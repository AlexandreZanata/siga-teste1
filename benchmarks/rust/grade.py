#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Julgamento do avaliador: público + privado (`atlas-grade/1`, NEXT-03).

O runner mede o aceite público na tentativa; o avaliador decide. Este script é
o lado do avaliador: clona base nova por tentativa, aplica o patch candidato,
roda o comando público da tarefa E os casos privados da custódia, e persiste o
veredito final — inclusive em falha. A regra é pré-especificada e igual nos
três braços: **o verde público não basta**; sem o privado verde, não há aceite.

Regra (`GRADE_RULE`):
- patch vazio → `rejected` (`empty_patch`);
- público com timeout/erro ou saída 3 → `indeterminado` (`environmental`);
- público reprovado (outra saída ≠ 0) → `rejected` (`patch_fault`, `public_gate`);
- público verde + privado verde → `accepted`;
- público verde + privado reprovado → `rejected` (`patch_fault`, `private_gate`),
  com a ponderação de escopo reservada ao revisor cego (o gate privado do lote
  roda casos de todas as tarefas; só contagens `N/M` entram no `grade.json`,
  nunca conteúdo de caso — o log bruto com casos fica fora do git);
- público verde + privado bloqueado (saída 3) → `indeterminado` (`environmental`).

Quem roda: o operador da custódia, com `--private-java` apontando para a
custódia (fora do git) e `--private-runner` para o script do lote. O executor
nunca vê nenhum dos dois. A base do operador sai intocada: o trabalho ocorre
num clone descartável. Saída 0 = julgamento persistido (mesmo `rejected`);
≠ 0 só em falha de infraestrutura do próprio julgamento.

Uso:
    python benchmarks/rust/grade.py --attempt <att> --tasks <tarefas.json>
        --acceptance-repo <base> --acceptance-scripts benchmarks/siga/rust/acceptance
        --private-java /custodia/Privado.java
        --private-runner benchmarks/siga/rust/acceptance/run-private3.sh
        --out <att>/grade.json

O pacote público (`--acceptance-scripts`, ex. o diretório `acceptance/` versionado
deste repo) é instalado pelo avaliador em `<clone>/atlas-accept/`, como manda a
instalação documentada no cabeçalho do runner público — o clone fresco nunca
traz o harness sozinho. O sha256 do pacote instalado entra no `grade.json`.
Se o comando da tarefa referencia um script relativo ausente no clone (mesmo
após a instalação), o gate público é registrado como erro de harness e o
veredito é `indeterminado` (`environmental`): harness mal instalado é falha do
avaliador, nunca regressão do patch.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SCHEMA = "atlas-grade/1"
ENV_EXIT = 3
GRADE_RULE = ("publico verde E privado verde => accepted; "
              "verde publico sozinho nunca aceita; "
              "bloqueio ambiental => indeterminado; resto => rejected")


def load_tasks(path: Path) -> dict:
    doc = json.loads(path.read_text())
    if doc.get("schema") not in ("atlas-tasks/1", "atlas-tasks/2"):
        raise SystemExit(f"schema de tarefas desconhecido: {doc.get('schema')!r}")
    return doc


def run(cmd: list[str], cwd: Path, timeout: float, extra_env: dict | None = None,
        log: Path | None = None) -> dict:
    env = dict(os.environ)
    if extra_env:
        env.update(extra_env)
    started = time.time()
    try:
        proc = subprocess.run(cmd, cwd=str(cwd), stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=timeout, env=env)
        seconds = time.time() - started
        if log:
            log.write_bytes(proc.stdout)
        return {"exit_code": proc.returncode, "seconds": round(seconds, 3),
                "timeout": False, "error": None}
    except subprocess.TimeoutExpired as exc:
        seconds = time.time() - started
        partial = exc.stdout or b""
        if log:
            log.write_bytes(partial if isinstance(partial, bytes) else str(partial).encode())
        return {"exit_code": None, "seconds": round(seconds, 3),
                "timeout": True, "error": None}
    except Exception as exc:  # noqa: BLE001
        return {"exit_code": None, "seconds": round(time.time() - started, 3),
                "timeout": False, "error": f"{exc.__class__.__name__}: {exc}"}


def dir_sha256(root: Path) -> str:
    """Hash do pacote do avaliador: caminhos relativos ordenados + conteúdo."""
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file() and ".git" not in p.parts:
            h.update(p.relative_to(root).as_posix().encode())
            h.update(b"\0")
            h.update(hashlib.sha256(p.read_bytes()).digest())
    return "sha256:" + h.hexdigest()


def gate_ready(command: list, base: Path) -> str | None:
    """Confere o harness ANTES de culpar o patch. Devolve motivo ou None (pronto).

    Só partes com separador de caminho são tratadas como arquivo (o id da tarefa,
ex. `SIGA-REAL-17`, passa direto). Binário relativo vale na base ou no PATH.
    """
    if not command:
        return "test_command ausente na tarefa"
    binary = command[0]
    if Path(binary).is_absolute():
        if not Path(binary).exists():
            return f"binário do aceite ausente: {binary}"
    elif not (base / binary).exists():
        import shutil as _sh
        if _sh.which(binary) is None:
            return f"binário do aceite ausente: {binary} (nem na base, nem no PATH)"
    for part in command[1:]:
        if ("/" in part or os.sep in part) and not Path(part).is_absolute() \
                and not (base / part).exists():
            return (f"harness ausente no clone do avaliador: {part} "
                    "(atlas-accept não instalado; falha do avaliador, não do patch)")
    return None


def parse_case_counts(log: Path | None) -> tuple[int | None, int | None]:
    """Extrai `N/M passed` da cauda do log do gate (convenção dos harnesses).

    Só contagens — nenhum conteúdo de caso entra no `grade.json`, que é
    publicável. Sem linha de contagem, devolve (None, None).
    """
    import re as _re
    if log is None or not log.exists():
        return None, None
    hits = _re.findall(r"(\d+)\s*/\s*(\d+)\s+passed", log.read_text(errors="replace"))
    if not hits:
        return None, None
    passed, total = (int(x) for x in hits[-1])
    return passed, total


def merge(public: dict, private: dict | None) -> tuple[str, str | None, str]:
    """Aplica a regra. Devolve (final, failure_class, reason)."""
    if public.get("empty"):
        return "rejected", "patch_fault", "patch vazio: nada a julgar (M3)"
    if public.get("timeout"):
        return "indeterminado", "environmental", "aceite público excedeu o teto"
    if public.get("error"):
        return "indeterminado", "environmental", f"aceite público não executou: {public['error']}"
    if public.get("exit_code") == ENV_EXIT:
        return "indeterminado", "environmental", "aceite público saiu 3 (ambiente)"
    if public.get("exit_code") != 0:
        return "rejected", "patch_fault", \
            f"aceite público reprovou (exit {public.get('exit_code')}; gate público)"
    if private is None:
        return "indeterminado", "environmental", \
            "sem casos privados nesta chamada: o verde público sozinho nunca aceita"
    if private.get("timeout"):
        return "indeterminado", "environmental", "aceite privado excedeu o teto"
    if private.get("error"):
        return "indeterminado", "environmental", f"aceite privado não executou: {private['error']}"
    if private.get("exit_code") == ENV_EXIT:
        return "indeterminado", "environmental", "aceite privado saiu 3 (ambiente)"
    if private.get("exit_code") != 0:
        return "rejected", "patch_fault", \
            f"aceite privado reprovou (exit {private.get('exit_code')}; gate privado; " \
            "a ponderação de escopo — casos de outras tarefas do lote — cabe ao revisor " \
            "cego, não a este registro)"
    return "accepted", None, "público e privado verdes"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--attempt", required=True)
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--acceptance-repo", required=True, help="base pristina (não é modificada)")
    ap.add_argument("--acceptance-scripts", default=None,
                    help="pacote público versionado instalado em <clone>/atlas-accept/")
    ap.add_argument("--private-java", default=None,
                    help="casos privados na custódia (ausente => sem gate privado)")
    ap.add_argument("--private-runner", default=None, help="script do lote (ex.: run-private3.sh)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--timeout-scale", type=float, default=1.0)
    args = ap.parse_args(argv)

    attempt = Path(args.attempt).resolve()
    man = json.loads((attempt / "manifest.json").read_text())
    task_id = man["task"]["id"]
    doc = load_tasks(Path(args.tasks))
    task = next((t for t in doc["tasks"] if t["id"] == task_id), None)
    if task is None:
        raise SystemExit(f"tarefa {task_id!r} ausente do conjunto")
    patch_file = attempt / man["patch"]["file"]
    patch_bytes = patch_file.read_bytes() if patch_file.exists() else b""

    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    timeout_s = float(task.get("timeout_s", 600)) * args.timeout_scale

    grade: dict = {"schema": SCHEMA, "attempt": attempt.name, "task_id": task_id,
                   "rule": GRADE_RULE, "timeout_s": timeout_s}
    if patch_bytes == b"":
        public = {"empty": True, "exit_code": None, "seconds": 0.0,
                  "timeout": False, "error": None}
        private = None
    else:
        scratch = Path(tempfile.mkdtemp(prefix="atlas-grade-"))
        try:
            clone = subprocess.run(["git", "clone", "-q", str(Path(args.acceptance_repo).resolve()),
                                    str(scratch / "base")], stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
            if clone.returncode != 0:
                raise SystemExit(f"clone da base falhou: {clone.stdout.decode()[-300:]}")
            base = scratch / "base"
            (scratch / "candidate.patch").write_bytes(patch_bytes)
            chk = subprocess.run(["git", "-C", str(base), "apply", "--check",
                                  str(scratch / "candidate.patch")],
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if chk.returncode != 0:
                public = {"empty": False, "applied": False, "exit_code": None,
                          "seconds": 0.0, "timeout": False, "error": None,
                          "reason": chk.stdout.decode("utf-8", errors="replace")[-400:]}
                private = None
            else:
                subprocess.run(["git", "-C", str(base), "apply",
                                str(scratch / "candidate.patch")], check=True)
                scripts_sha = None
                if args.acceptance_scripts:
                    src = Path(args.acceptance_scripts).resolve()
                    if not src.is_dir():
                        raise SystemExit(f"--acceptance-scripts não é diretório: {src}")
                    shutil.copytree(src, base / "atlas-accept", dirs_exist_ok=True)
                    scripts_sha = dir_sha256(src)
                blocked = gate_ready(task["test_command"], base)
                if blocked is not None:
                    public = {"empty": False, "applied": True,
                              "acceptance_scripts_sha256": scripts_sha,
                              "exit_code": None, "seconds": 0.0,
                              "timeout": False, "error": blocked}
                else:
                    public_log = out.parent / f"{attempt.name}.public.log"
                    public = {"empty": False, "applied": True,
                              "acceptance_scripts_sha256": scripts_sha,
                              **run(task["test_command"], base, timeout_s, log=public_log)}
                    passed, total = parse_case_counts(public_log)
                    public["cases_passed"] = passed
                    public["cases_total"] = total
                if args.private_java and args.private_runner:
                    priv_build = scratch / "priv-build"
                    priv_build.mkdir()
                    private_log = out.parent / f"{attempt.name}.private.log"
                    private = run(["bash", str(Path(args.private_runner).resolve()),
                                   task_id], base, timeout_s,
                                  extra_env={"PRIVATE_JAVA": str(Path(args.private_java).resolve()),
                                             "PRIVATE_BUILD": str(priv_build)},
                                  log=private_log)
                    passed, total = parse_case_counts(private_log)
                    private["cases_passed"] = passed
                    private["cases_total"] = total
                else:
                    private = None
        finally:
            shutil.rmtree(scratch, ignore_errors=True)

    final, failure_class, reason = merge(public, private)
    # `apply_failed` do avaliador também é rejeição do patch, com motivo próprio.
    if public.get("applied") is False and final == "rejected":
        reason = "patch não aplica em base limpa (M1)"
    grade.update({"patch_bytes": len(patch_bytes), "public": public, "private": private,
                  "final": final, "failure_class": failure_class, "reason": reason,
                  "private_source": ("custodia (caminho não publicado)"
                                     if args.private_java else None)})
    out.write_text(json.dumps(grade, ensure_ascii=False, indent=1) + "\n")
    print(f"{attempt.name} [{task_id}] -> {final}"
          + (f" ({failure_class})" if failure_class else "") + f": {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
