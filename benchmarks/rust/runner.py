#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Runner de uma tentativa do piloto real: um run, um teto, sem acesso ao ouro.

Este arquivo é a parte do aceite de R2 que **não** depende de modelo nem de orçamento:
"o runner captura todas as chamadas, custos e patches sem acesso ao ouro". Ele existe para que
R3, quando P1/P2 forem decididos, comece com infraestrutura medida em vez de improvisada.

Quatro decisões que valem explicar, porque cada uma foi escolha contra algo mais fácil:

1. **`opened` vem de evento real de leitura.** O agente recebe um leitor sancionado
   (`atlas-read`) que registra cada leitura antes de imprimir. Se ele ler por outro caminho —
   `cat`, editor, `git show` —, o runner **não sabe**, e é isso que o número significa. Derivar
   `opened` de `delivered` é proibido pelo contrato §9 e invalidaria o cegamento; aqui não há
   nenhuma fórmula, só evento.
2. **`delivered` é medido, não relatado.** O shim `atlas` observa os bytes que passaram para o
   agente; o campo do envelope é registrado ao lado, para comparação, mas o número que decide é
   o que o runner viu.
3. **Teto primeiro, tentativa depois.** O runner acompanha parede e chamadas de ferramenta
   enquanto o executor roda e **mata o grupo de processos** no primeiro teto atingido, marcando
   a tentativa como falha. Continuar "só para terminar a etapa" é o que o protocolo §4 proíbe.
4. **Ouro inacessível é requisito, não promessa.** O runner recusa começar se o diretório do
   ouro estiver dentro do workspace (ou o contrário) e nunca escreve o caminho no ambiente do
   executor. Ele também **declara o que não cobre**: mesmo `.git`, mesmo usuário, sem container.
   O pré-registro §4 já avisa que worktree não é isolamento — o runner não finge que é.

5. **O que não é observável por fora vem por contrato, e não vira zero.** Identidade do modelo,
   tokens, latência, erro/retry, turnos, chamadas de ferramenta fora do shim e custo faturado
   são **declarados** pelo executor (`atlas-executor/1`, ver `executor_contract.py`) e ficam ao
   lado do que o runner viu, em campos próprios, conferidos contra o próprio stream dele. Sem
   result contract, a tentativa é `unverified`; com violação, `contract_violation` e nunca
   `real`. Tentativa real sem `provider`+`id`+`version`+`verified_by` do modelo é recusada como
   evidência, porque nome informal de modelo não substitui identidade verificável.

O executor `dry` existe para testar esta infraestrutura sem modelo. Todo run com ele sai marcado
`evidence_class: infrastructure_only`, e o runner se recusa a rodá-lo sem `--allow-dry`: um stub
nunca pode ser confundido com evidência de R3.

Uso:
    python benchmarks/rust/runner.py --tasks tarefas.json --task s01 --condition CTX-RS \\
        --workspace /caminho/worktree --out experiments/rust/siga/<run_id>/attempts \\
        --atlas-bin rust/archatlas/target/release/archatlas --atlas-index /tmp/idx.sqlite \\
        --executor-cmd 'meu-agente --enunciado {statement_file} --dir {workspace}' \\
        --gold /caminho/ouro

O executor recebe `ATLAS_EXECUTOR_TELEMETRY` (stream append-only, eventos com
`"source": "executor"`) e `ATLAS_EXECUTOR_RESULT` (result contract). Ver
[`research/rust/RUNNER_PILOTO.md`](../../research/rust/RUNNER_PILOTO.md) §§3–4b.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _bench import environment_manifest, write_json  # noqa: E402
from executor_contract import (  # noqa: E402
    CONTRACT_SCHEMA,
    EXTERNALLY_OBSERVED,
    RESULT_ENV,
    SHIM_SOURCE,
    STREAM_ENV,
    StreamAccounting,
    capability_manifest,
    coverage_report,
    load_result,
    reconcile,
    reconcile_violations,
    validate_result,
)

# `atlas-tasks/1` é o schema mínimo que bastou para ensaiar o runner; `/2` acrescenta o que a
# avaliação cega exige para checar escopo mecanicamente (`allowed_paths`, `immutable_paths`) e o
# que o protocolo §3 exige por tarefa (`origin`, `contamination_risk`). O runner aceita os dois —
# recusar `/1` quebraria tentativas já ensaiadas sem ganho —, mas `eval.py` só cega `/2`.
TASK_SCHEMA = "atlas-tasks/1"
TASK_SCHEMAS = ("atlas-tasks/1", "atlas-tasks/2")
RUN_SCHEMA = "atlas-run/1"
CONDITIONS = ("BASE", "LEX-RS", "CTX-RS")
# Tetos propostos no protocolo §4, iguais nos três braços. Não são dimensionamento; são tetos.
DEFAULT_LIMITS = {"wall_s": 1800, "turns": 40, "tool_calls": 100}
POLL_S = 0.05
# Conjunto fixo de ferramentas nos tres bracos: o loop tem de ser o mesmo e so a politica de
# contexto difere. `BASE` nao recebe o `atlas`, mas o loop registrado e identico — e
# `--expect-loop-sha` recusa iniciar quando a rodada nao esta no loop fixado.
FIXED_TOOLS = ("atlas", "atlas-read")

READ_SHIM = '''#!/usr/bin/env python3
"""Leitor sancionado: registra a leitura e só então imprime. Sem registro, `opened` não existe."""
import json, os, pathlib, sys, time

def log(event):
    p = os.environ.get("ATLAS_TELEMETRY")
    if p:
        with open(p, "a") as fh:
            fh.write(json.dumps(event) + "\\n")

def main() -> int:
    if len(sys.argv) < 2:
        print("uso: atlas-read <arquivo> [--line N] [--from A --to B]", file=sys.stderr)
        return 2
    target = pathlib.Path(sys.argv[1])
    root = pathlib.Path(os.environ["ATLAS_WORKSPACE"]).resolve()
    resolved = (root / target).resolve() if not target.is_absolute() else target.resolve()
    if root not in resolved.parents and resolved != root:
        log({"kind": "read_denied", "source": "shim", "file": str(target),
             "reason": "outside_workspace"})
        print("atlas-read: caminho fora do workspace", file=sys.stderr)
        return 4
    try:
        lines = resolved.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        log({"kind": "read_denied", "source": "shim", "file": str(target),
             "reason": f"io:{exc.__class__.__name__}"})
        print(f"atlas-read: {exc}", file=sys.stderr)
        return 4
    first, last = 1, len(lines)
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--line" and i + 1 < len(args):
            first = last = int(args[i + 1]); i += 2
        elif args[i] == "--from" and i + 1 < len(args):
            first = int(args[i + 1]); i += 2
        elif args[i] == "--to" and i + 1 < len(args):
            last = int(args[i + 1]); i += 2
        else:
            i += 1
    first = max(1, min(first, len(lines) or 1)); last = max(first, min(last, len(lines) or 1))
    body = "\\n".join(lines[first - 1:last])
    log({"kind": "opened", "source": "shim", "file": str(resolved.relative_to(root)),
         "from": first, "to": last, "lines": len(lines), "bytes": len(body), "ts": time.time()})
    print(body)
    return 0

raise SystemExit(main())
'''

ATLAS_SHIM = '''#!/usr/bin/env python3
"""Envelope do binário real: observa os bytes que passaram ao agente e repassa o stdout intacto."""
import json, os, subprocess, sys, time

def main() -> int:
    binary = os.environ["ATLAS_BIN"]
    proc = subprocess.run([binary, *sys.argv[1:]], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout = proc.stdout
    declared = {}
    try:
        env = json.loads(stdout.decode())
        budget = env.get("budget") or {}
        declared = {"schema": env.get("schema"), "state": env.get("state"),
                    "declared_bytes": budget.get("used_bytes"),
                    "declared_tokens": budget.get("used_tokens"),
                    "units": len(env.get("units") or []),
                    "omitted": (env.get("omitted") or {}).get("n")}
    except Exception:
        declared = {"parse_ok": False}
    p = os.environ.get("ATLAS_TELEMETRY")
    if p:
        with open(p, "a") as fh:
            fh.write(json.dumps({"kind": "tool_call", "source": "shim",
                                 "tool": "atlas", "argv": sys.argv[1:],
                                 "stdout_bytes": len(stdout), "exit_code": proc.returncode,
                                 "declared": declared, "ts": time.time()}) + "\\n")
    sys.stdout.write(stdout.decode("utf-8", errors="replace"))
    sys.stderr.write(proc.stderr.decode("utf-8", errors="replace"))
    return proc.returncode

raise SystemExit(main())
'''


def sha256_file(path: Path) -> str | None:
    if not path or not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def loop_fingerprint(executor_kind: str, cmd: list[str], limits: dict,
                     statement_sha: str | None) -> str:
    """Hash da tentativa: executor, comando efetivo, tetos e enunciado (legado, instável).

    Mantido por compatibilidade com manifestos e com `--expect-loop-sha`. Ele mistura a
    identidade da tentativa — comando com caminhos absolutos temporários + enunciado — e
    por isso muda quando só o diretório muda (probe da auditoria 2026-10-05 §1.2). A
    identidade da **rodada** é `loop_config_sha256` (NEXT-01); este aqui identifica a
    tentativa, com caminhos e enunciado em campos próprios.
    """
    doc = {"executor": {"kind": executor_kind, "cmd": cmd}, "tools": sorted(FIXED_TOOLS),
           "limits": limits, "statement_sha256": statement_sha}
    return "sha256:" + hashlib.sha256(json.dumps(doc, sort_keys=True).encode()).hexdigest()


# --- NEXT-01: hash de configuração estável ----------------------------------------
# O probe da auditoria mostrou `loop_fingerprint` mudando só porque os caminhos
# temporários mudaram. A identidade da rodada exclui tudo que é da tentativa: sem
# caminhos, sem enunciado. Mesmo loop em caminhos distintos => mesmo hash; mudança de
# código do executor, ferramenta ou teto => hash diferente. A conferência de "mesma
# tarefa entre braços" continua separada (tarefa + `statement_sha256`, não loop).
LOOP_CONFIG_SCHEMA = "atlas-loop-config/1"
TOOL_PROTOCOL = "atlas-tools/1"
RUNNER_CODE_FILES = ("runner.py", "executor_contract.py", "real_executor.py")
# Código de saída que os aceites reservam para falha de ambiente (harness, não patch).
ENV_EXIT_CODE = 3
ACCEPTANCE_STATES = ("no_base", "empty_patch", "deps_missing", "apply_failed", "passed",
                     "patch_regression", "env_blocked", "acceptance_timeout",
                     "acceptance_error")
# Regra pré-especificada e igual nos três braços: só estes estados bloqueiam o
# julgamento sem culpar o patch (o avaliador os marca `indeterminado`, nunca sucesso).
# Todo o resto que não passa é `rejeitado` — inclusive saída 3 pós-patch sem falta
# comprovada pré-patch não vira ambiente sozinha: a classificação vem do código de
# saída do harness e da checagem de dependências, nunca de declaração do executor.
ENV_INDETERMINATE_STATES = ("env_blocked", "acceptance_timeout", "deps_missing", "no_base")


def executor_code_sha() -> dict:
    """Hash do código do executor (runner + contrato + loop real). Muda se o código mudar."""
    base = Path(__file__).resolve().parent
    files: dict[str, str] = {}
    for name in RUNNER_CODE_FILES:
        h = sha256_file(base / name)
        if h:
            files[name] = "sha256:" + h
    if len(files) < len(RUNNER_CODE_FILES):
        missing = sorted(set(RUNNER_CODE_FILES) - set(files))
        return {"sha256": None, "files": files,
                "reason": f"código do executor sem hash: ausente {missing}"}
    combined = hashlib.sha256()
    for name in sorted(files):
        combined.update(name.encode())
        combined.update(b"\0")
        combined.update(files[name].encode())
    return {"sha256": "sha256:" + combined.hexdigest(), "files": files, "reason": None}


def tool_spec_digest() -> dict:
    """Protocolo de ferramentas do loop: shims do runner + ferramentas fixas do executor."""
    try:
        from real_executor import FIXED_EXECUTOR_TOOLS, TOOLS_SPEC  # type: ignore
        exec_tools = sorted(tuple(FIXED_EXECUTOR_TOOLS))
        spec = TOOLS_SPEC
    except Exception as exc:  # noqa: BLE001 - sem o módulo, o protocolo fica sem hash
        return {"sha256": None, "protocol": TOOL_PROTOCOL,
                "runner_tools": sorted(FIXED_TOOLS), "executor_tools": None,
                "reason": f"TOOLS_SPEC indisponível: {exc.__class__.__name__}"}
    doc = {"protocol": TOOL_PROTOCOL, "runner_tools": sorted(FIXED_TOOLS),
           "executor_tools": exec_tools, "spec": spec}
    return {"sha256": "sha256:" + hashlib.sha256(
        json.dumps(doc, sort_keys=True).encode()).hexdigest(),
        "protocol": TOOL_PROTOCOL, "runner_tools": sorted(FIXED_TOOLS),
        "executor_tools": exec_tools, "reason": None}


def loop_config_doc(executor_kind: str, cmd_template: str | None, limits: dict) -> dict:
    """Documento da configuração do loop: só o que é da rodada, nada da tentativa."""
    code = executor_code_sha()
    tools = tool_spec_digest()
    template_sha = ("sha256:" + hashlib.sha256(cmd_template.encode()).hexdigest()
                    if cmd_template else None)
    return {
        "schema": LOOP_CONFIG_SCHEMA,
        "executor": {"kind": executor_kind, "code_sha256": code["sha256"],
                     "code_files": code["files"], "code_reason": code["reason"]},
        "tools": {"protocol": tools["protocol"], "runner_tools": tools["runner_tools"],
                  "executor_tools": tools["executor_tools"],
                  "spec_sha256": tools["sha256"], "spec_reason": tools.get("reason")},
        "limits": limits,
        "cmd_template_sha256": template_sha,
        "cmd_template_note": ("modelo do comando antes de substituir {statement_file}, "
                              "{workspace}, {tool_dir}, {out_dir}; os caminhos efetivos ficam "
                              "em executor.cmd, fora deste hash"),
    }


def loop_config_sha(doc: dict) -> str:
    """Hash estável da configuração: igual entre tentativas do mesmo loop."""
    return "sha256:" + hashlib.sha256(json.dumps(doc, sort_keys=True).encode()).hexdigest()


def assess_contract(executor_kind: str, result_path: Path, stream_report: dict) -> dict:
    """Estado do contrato do executor. Fail-closed: o rótulo `real` exige contrato fechado."""
    if executor_kind == "dry":
        return {
            "state": "not_applicable",
            "reason": "executor dry: contrato de modelo nao se aplica a ensaio de infraestrutura",
            "violations": [], "missing": [], "result": None, "result_error": None,
            "reconciliation": [],
            "coverage": coverage_report(None, stream_report, []),
        }
    result_doc, result_error = load_result(result_path)
    # Violacao do stream conta como violacao do contrato mesmo sem result: fabricar evento
    # reservado e pior que nao entregar resumo, nao melhor.
    stream_violations = list(stream_report.get("stream_violations") or [])
    violations = (validate_result(result_doc) if result_doc is not None else [])
    violations.extend(stream_violations)
    missing: list[str] = []
    if result_doc is None:
        state = "violation" if stream_violations else "missing"
        missing.append(f"result_contract:{result_error}")
    else:
        state = "violation" if violations else "ok"
    rows = reconcile(stream_report, result_doc)
    mismatches = reconcile_violations(rows)
    if mismatches:
        # Stream e resumo discordando e violacao, nao empate: um dos dois lados declara errado.
        violations.extend(mismatches)
        state = "violation"
    coverage = coverage_report(result_doc, stream_report, violations)
    if state == "ok" and any(not entry["observed"] for entry in coverage.values()):
        state = "partial"
    return {"state": state, "reason": None, "violations": violations, "missing": missing,
            "result": result_doc, "result_error": result_error, "reconciliation": rows,
            "coverage": coverage}


def tree_hash(root: Path) -> str:
    """Hash do conteúdo do workspace por caminho+bytes: prova qual snapshot foi usado."""
    h = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts):
        h.update(path.relative_to(root).as_posix().encode())
        h.update(b"\0")
        h.update(hashlib.sha256(path.read_bytes()).digest())
    return h.hexdigest()


def load_tasks(path: Path) -> dict:
    doc = json.loads(path.read_text())
    if doc.get("schema") not in TASK_SCHEMAS:
        raise SystemExit(f"schema de tarefas desconhecido: {doc.get('schema')!r} "
                         f"(esperado um de {', '.join(TASK_SCHEMAS)})")
    return doc


def pick_task(doc: dict, task_id: str) -> dict:
    for t in doc["tasks"]:
        if t["id"] == task_id:
            return t
    raise SystemExit(f"tarefa ausente no conjunto: {task_id}")


def check_gold_separation(gold: Path | None, workspace: Path) -> dict:
    """Ouro fora do alcance do executor — e o que esta checagem **não** garante, declarado."""
    # O caminho do ouro **não** entra no manifesto: o manifesto é escrito no mesmo diretório
    # que o executor recebe como `ATLAS_TELEMETRY`, então registrá-lo seria publicar o mapa do
    # ouro para quem tem acesso a artefatos de tentativa — inclusive uma tentativa seguinte.
    # Fica um identificador curto o suficiente para conferir que o diretório é o mesmo, sem
    # entregar o caminho.
    record = {
        "declared_dir_ref": ("sha256:" + hashlib.sha256(str(gold).encode()).hexdigest()[:12])
        if gold else None,
        "path_recorded": False,
        "path_recorded_reason": "manifesto e artefato de tentativa; o caminho do ouro nao entra nele",
        "in_executor_env": False,
        "checks": ["gold fora do workspace", "gold fora do checkout do repo",
                   "caminho do ouro nao entra no ambiente do executor",
                   "caminho do ouro nao entra no manifesto"],
        "not_covered": ["mesmo usuario do sistema", "mesmo .git e historico do checkout",
                        "sem container/namespace: o executor pode ler o disco se souber o caminho"],
        "level": "checagem_por_caminho; insuficiente para R5",
    }
    if gold is None:
        record["state"] = "ausente"
        record["note"] = "sem --gold nesta tentativa; nenhum ouro foi lido nem referenciado"
        return record
    g = gold.resolve()
    ws = workspace.resolve()
    if g == ws or ws in g.parents or g in ws.parents:
        raise SystemExit(
            "BLOQUEADO: o diretorio do ouro e alcancavel a partir do workspace "
            f"({g} vs {ws}). Separacao de diretorio nao e isolamento — mova o ouro para fora."
        )
    record["state"] = "verificado_por_caminho"
    return record


class Accounting:
    """Teto primeiro. Cada evento passa por aqui; o primeiro teto atingido para a tentativa.

    Duas correções que valem explicação:

    - O stream é lido **por offset**, só o que foi apensado desde a última passada. Reabsorver o
      arquivo inteiro a cada poll multiplicava o teto pelo número de polls: a tentativa morria
      por "chamadas de ferramenta" que nunca existiram.
    - O teto de chamadas conta **todas as ferramentas**: as do shim, que o runner observa, e as
      que o executor declara (shell, editor, outras). Contar só `atlas`/`atlas-read` deixaria a
      maior parte das chamadas de fora do teto — inclusive no braço `BASE`, onde o `atlas` não
      existe. Os bytes entregues, porém, continuam vindo só do shim: os declarados ficam ao
      lado, em campo próprio, para conferência.
    """

    def __init__(self, limits: dict):
        self.limits = limits
        self.started = time.time()
        self.tool_calls = 0
        self.tool_calls_observed = 0
        self.tool_calls_rejected = 0
        self.opened = 0
        self.delivered_bytes = 0
        self.turns: int | None = None
        self._saw_turn_event = False
        self._offset = 0
        self.stream = StreamAccounting()

    def absorb(self, path: Path) -> None:
        """Lê o que foi apensado ao stream (append-only) desde a última chamada."""
        if not path.exists():
            return
        with path.open("rb") as fh:
            fh.seek(self._offset)
            chunk = fh.read()
        if not chunk:
            return
        cut = chunk.rfind(b"\n") + 1
        if cut <= 0:
            return  # linha em construcao: so completa e absorvida na proxima passada
        self._offset += cut
        for line in chunk[:cut].decode("utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except Exception:
                continue
            self._absorb_event(ev)

    def _absorb_event(self, ev: dict) -> None:
        kind = ev.get("kind")
        # `source` decide a origem: shim (observado) ou executor (declarado). Evento reservado
        # sem `source: shim` nunca e contado como leitura — vira violacao no stream.
        before = len(self.stream.violations)
        source = self.stream.absorb(ev)
        rejected = len(self.stream.violations) > before
        if source == SHIM_SOURCE:
            if kind == "tool_call":
                self.tool_calls += 1
                self.tool_calls_observed += 1
                self.delivered_bytes += int(ev.get("stdout_bytes") or 0)
            elif kind == "opened":
                # Leitura sancionada **conta como chamada de ferramenta**: o teto do protocolo §4
                # é de "chamadas de ferramenta por tentativa", e ler um arquivo é uma delas.
                self.tool_calls += 1
                self.tool_calls_observed += 1
                self.opened += 1
            # `read_denied` e tentativa de leitura fora do workspace: nao e leitura entregue.
            return
        if kind == "tool_call":
            # Declarada pelo executor — inclusive a que violou o contrato (nome reservado):
            # entra no teto de qualquer forma, porque subdeclarar nao pode render chamada extra.
            self.tool_calls += 1
            if rejected:
                self.tool_calls_rejected += 1
        elif kind == "turn":
            self._saw_turn_event = True
            self.turns = self.stream.turns

    @property
    def wall_s(self) -> float:
        return time.time() - self.started

    def ceiling_hit(self) -> str | None:
        if self.wall_s > self.limits["wall_s"]:
            return "wall_s"
        if self.tool_calls > self.limits["tool_calls"]:
            return "tool_calls"
        if self.turns is not None and self.turns > self.limits["turns"]:
            return "turns"
        return None

    def report(self) -> dict:
        declared = self.stream.report()
        return {
            "wall_s": round(self.wall_s, 3),
            # `tool_calls` e o total que fiscaliza o teto; `observed` e `declared` mostram a
            # cobertura, sem somar declarado dentro de medido.
            "tool_calls": self.tool_calls,
            "tool_calls_observed": self.tool_calls_observed,
            "tool_calls_declared": declared["tool_calls_declared"],
            "tool_calls_rejected": self.tool_calls_rejected,
            "tool_calls_by_tool": declared["tool_calls_by_tool"],
            "opened": self.opened,
            "delivered_bytes": self.delivered_bytes,
            "declared_delivered_bytes": declared["declared_delivered_bytes"],
            "turns": self.turns,
            "turns_reason": None if self._saw_turn_event else
                            "executor nao emitiu evento de turno; teto de turnos nao fiscalizavel",
            "model_calls": declared["model_calls"],
            "calls_ok": declared["calls_ok"],
            "calls_error": declared["calls_error"],
            "tokens": declared["tokens"],
            "latency_ms": declared["latency_ms"],
            "errors": declared["errors"],
            "retries": declared["retries"],
            "declared_cost": declared["cost"],
            "declared_stop": declared["stop"],
            "duplicate_request_ids": declared["duplicate_request_ids"],
            "unattributed_events": declared["unattributed_events"],
            "stream_violations": declared["violations"],
            "retrieved_candidates": None,
            "retrieved_reason": "o envelope do `context` nao expoe a contagem interna de candidatos",
        }


def write_shims(tools: Path) -> None:
    tools.mkdir(parents=True, exist_ok=True)
    for name, body in (("atlas-read", READ_SHIM), ("atlas", ATLAS_SHIM)):
        p = tools / name
        p.write_text(body)
        p.chmod(0o755)


def executor_env(workspace: Path, tools: Path, telemetry: Path, atlas_bin: Path | None,
                 atlas_repo: Path | None, atlas_index: Path | None, condition: str) -> dict:
    """Ambiente do executor. O ouro não aparece aqui — é o que o teste guarda."""
    env = dict(os.environ)
    env["PATH"] = f"{tools}{os.pathsep}{env.get('PATH', '')}"
    env["ATLAS_TELEMETRY"] = str(telemetry)
    env["ATLAS_WORKSPACE"] = str(workspace)
    if condition != "BASE":
        env["ATLAS_BIN"] = str(atlas_bin)
        env["ATLAS_REPO"] = str(atlas_repo)
        env["ATLAS_INDEX"] = str(atlas_index)
    env.pop("ATLAS_GOLD", None)
    return env


def run_executor(cmd: list[str], env: dict, workspace: Path, telem: Path, limits: dict,
                 output_path: Path) -> tuple[int | None, str | None, bool, float, int, Accounting]:
    """Roda o executor medindo-o por fora e mata no primeiro teto.

    A saída vai para **arquivo**, não para um pipe: um executor que escreve mais do que o buffer
    do pipe encheria e travaria sozinho, e o `Popen` com `poll()` não estaria consumindo. Com
    arquivo não existe esse ponto morto, e o log fica auditável.

    Devolve a contabilidade **viva** da tentativa: o mesmo objeto que fiscalizou o teto é o que
    relata o uso, para que contagem e fiscalização não possam divergir por releitura.
    """
    acct = Accounting(limits)
    started = time.time()
    stopped: str | None = None
    killed = False
    peak_rss = 0
    with output_path.open("wb") as sink:
        proc = subprocess.Popen(cmd, cwd=str(workspace), env=env, stdout=sink,
                                stderr=subprocess.STDOUT, start_new_session=True)
        while proc.poll() is None:
            acct.absorb(telem)
            peak_rss = max(peak_rss, peak_rss_kb(proc.pid))
            stopped = acct.ceiling_hit()
            if stopped:
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                    killed = True
                except ProcessLookupError:
                    pass
                break
            time.sleep(POLL_S)
    acct.absorb(telem)
    if stopped is None:
        # Executor rápido demais para ser interrompido no meio: o teto continua valendo. A
        # tentativa que estourou é **falha registrada**, não sucesso que escapou da fiscalização
        # por velocidade — e o manifesto diz se houve kill ou só detecção posterior.
        stopped = acct.ceiling_hit()
    return proc.returncode, stopped, killed, time.time() - started, peak_rss, acct


def peak_rss_kb(pid: int) -> int:
    try:
        with open(f"/proc/{pid}/status") as fh:
            for line in fh:
                if line.startswith("VmHWM:"):
                    return int(line.split()[1])
    except OSError:
        return 0
    return 0


def capture_patch(workspace: Path, out: Path) -> dict:
    """Diff do workspace após a tentativa, incluindo arquivos novos. O índice é restaurado."""
    subprocess.run(["git", "-C", str(workspace), "add", "-A"], check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    diff = subprocess.run(["git", "-C", str(workspace), "diff", "--cached", "--binary"],
                          stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "-C", str(workspace), "reset", "-q"], check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    patch = out / "attempt.patch"
    patch.write_bytes(diff.stdout)
    return {"file": patch.name, "bytes": len(diff.stdout), "empty": not diff.stdout}


def git_head(repo: Path) -> str | None:
    """HEAD completo (40 hex) ou None quando ausente."""
    proc = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                          stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    head = proc.stdout.decode().strip()
    return head if proc.returncode == 0 and head else None


def git_tracked_clean(repo: Path) -> bool:
    """Árvore rastreada limpa: sem modificação em staged nem unstaged. Não-trackeados ok."""
    for extra in (["--cached"], []):
        proc = subprocess.run(["git", "-C", str(repo), "diff", "--quiet", *extra],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if proc.returncode != 0:
            return False
    return True


def preflight_workspace(workspace: Path, expected_sha: str | None) -> dict:
    """Preflight fechado do workspace, antes do executor: SHA completo, HEAD, limpeza.

    Falha aqui é BLOQUEIO (SystemExit, sem manifesto): nada rodou ainda, então recusar
    é barato e não esconde custo. O overlay imutável (`immutable_paths`) é registrado
    no manifesto, não bloqueia aqui — quem o fiscaliza é M5, no avaliador.
    """
    head = git_head(workspace)
    if not head:
        raise SystemExit(f"BLOQUEADO: workspace sem HEAD legível ({workspace}). "
                         "Base sem commit não é base fixada.")
    if expected_sha:
        if len(expected_sha) < 40 or any(c not in "0123456789abcdef" for c in expected_sha.lower()):
            raise SystemExit(
                f"BLOQUEADO: base_sha da tarefa não é SHA completo (40 hex): "
                f"{expected_sha!r}. Prefixo de 8 caracteres não fixa base.")
        if head.lower() != expected_sha.lower():
            raise SystemExit(f"BLOQUEADO: workspace fora do snapshot pedido: {head} vs "
                             f"{expected_sha} (comparação exata, sem prefixo).")
    if not git_tracked_clean(workspace):
        raise SystemExit(f"BLOQUEADO: workspace com árvore rastreada suja ({workspace}). "
                         "Uma tentativa por workspace novo e limpo.")
    return {"base_sha_full": head, "head_present": True, "tracked_clean": True,
            "tree_sha256": tree_hash(workspace),
            "expected_sha": expected_sha,
            "expected_reason": None if expected_sha else
                               "tarefa sem base_sha fixado; HEAD registrado sem conferência"}


def check_test_deps(task: dict, base: Path) -> dict:
    """Dependências do aceite **antes** do patch: falta comprovada não culpa o patch.

    Mesma regra nos três braços: só o binário/arquivo do comando é checado aqui (sem
    executar nada). Se faltar, o patch nem é aplicado (`applied: None`) e o estado é
    `deps_missing` — não sucesso, nem rejeição do patch.
    """
    command = task.get("test_command") or []
    if not command:
        return {"ok": False, "reason": "test_command ausente na tarefa"}
    binary = str(command[0])
    candidate = Path(binary)
    if candidate.is_absolute():
        ok = candidate.exists()
        return {"ok": ok, "binary": binary,
                "reason": None if ok else f"binário do aceite ausente: {binary}"}
    if (base / binary).exists():
        return {"ok": True, "binary": binary, "reason": None,
                "note": "binário relativo resolvido dentro da base de aceitação"}
    which = shutil.which(binary)
    return {"ok": which is not None, "binary": binary,
            "reason": None if which else f"dependência do aceite não encontrada: {binary!r} "
                                          f"(nem em {base}, nem no PATH)"}


def _patch_paths(text: str) -> list[str]:
    """Caminhos tocados pelo patch (para desfazer só o patch na restauração da base)."""
    out: list[str] = []
    for line in text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                p = parts[3]
                out.append(p[2:] if p.startswith("b/") else p)
        elif line.startswith("rename to "):
            p = line[len("rename to "):].strip()
            if p and p not in out:
                out.append(p)
    return out


def restore_acceptance_base(base: Path, patch_text: str) -> dict:
    """Devolve a base ao HEAD e remove arquivos novos vindos do patch. Nunca reutilizar
    base modificada: a tentativa seguinte exige base limpa no preflight."""
    subprocess.run(["git", "-C", str(base), "reset", "--hard", "-q", "HEAD"],
                   check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    removed: list[str] = []
    for rel in _patch_paths(patch_text):
        proc = subprocess.run(["git", "-C", str(base), "clean", "-fdq", "--", rel],
                              check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if proc.returncode == 0:
            removed.append(rel)
    clean = git_tracked_clean(base)
    return {"reset_hard": True, "patch_paths_removed": removed, "tracked_clean_after": clean,
            "reason": None if clean else "base segue suja após restauração; orquestrador deve "
                              "fornecer base nova (nunca reutilizar base modificada)"}


def run_acceptance(args, task: dict, patch: Path) -> dict:
    """Patch candidato aplicado a base limpa, testado com comando imutável do avaliador.

    Estados distintos (NEXT-01), mesma regra nos três braços: `no_base` (sem base),
    `empty_patch`, `deps_missing` (falta comprovada **antes** do patch, sem aplicar),
    `apply_failed`, `passed`, `patch_regression` (exit != 0 e != 3), `env_blocked`
    (exit 3, reservado ao harness para ambiente), `acceptance_timeout` e
    `acceptance_error`. Timeout e erro escrevem manifesto + log parcial e restauram a
    base — nunca travam o runner sem rastro. Custos/retries do executor já estão no
    manifesto; a falha do aceite não os apaga.
    """
    outdir = Path(args.out).resolve()
    log_path = outdir / "acceptance_output.txt"
    command = task.get("test_command")
    command_sha = ("sha256:" + hashlib.sha256(
        json.dumps(command, sort_keys=True).encode()).hexdigest() if command else None)
    if not args.acceptance_repo:
        return {"state": "no_base", "applied": None, "exit_code": None, "seconds": None,
                "command": command, "test_command_sha256": command_sha,
                "reason": "sem --acceptance-repo: nenhuma base limpa fornecida nesta tentativa"}
    patch_bytes = patch.read_bytes()
    patch_text = patch_bytes.decode("utf-8", errors="replace")
    if patch_bytes == b"":
        return {"state": "empty_patch", "applied": None, "exit_code": None, "seconds": None,
                "command": command, "test_command_sha256": command_sha,
                "reason": "patch vazio; nada a aplicar"}
    base = Path(args.acceptance_repo).resolve()
    base_head_before = git_head(base)
    if not base_head_before:
        return {"state": "env_blocked", "applied": None, "exit_code": None, "seconds": None,
                "command": command, "test_command_sha256": command_sha,
                "base_head_before": None, "reason": "base de aceitação sem HEAD legível; "
                "julgamento bloqueado sem culpar o patch"}
    if not git_tracked_clean(base):
        return {"state": "env_blocked", "applied": None, "exit_code": None, "seconds": None,
                "command": command, "test_command_sha256": command_sha,
                "base_head_before": base_head_before,
                "reason": "base de aceitação suja: nunca reutilizar base modificada pela "
                          "tentativa anterior; julgamento bloqueado sem culpar o patch"}
    deps = check_test_deps(task, base)
    if not deps["ok"]:
        return {"state": "deps_missing", "applied": None, "exit_code": None, "seconds": None,
                "command": command, "test_command_sha256": command_sha,
                "base_head_before": base_head_before, "deps": deps,
                "reason": f"dependência do aceite ausente antes do patch ({deps['reason']}): "
                          "falta comprovada não é sucesso nem rejeição do patch; patch não aplicado"}
    apply_proc = subprocess.run(["git", "-C", str(base), "apply", "--check", str(patch)],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if apply_proc.returncode != 0:
        return {"state": "apply_failed", "applied": False, "exit_code": None, "seconds": None,
                "command": command, "test_command_sha256": command_sha,
                "base_head_before": base_head_before, "deps": deps,
                "reason": apply_proc.stdout.decode("utf-8", errors="replace")[-400:] or
                          "git apply --check reprovou o patch"}
    subprocess.run(["git", "-C", str(base), "apply", str(patch)], check=True)
    timeout_s = task.get("timeout_s", 600)
    started = time.time()
    try:
        proc = subprocess.run(command, cwd=str(base), stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=timeout_s)
    except subprocess.TimeoutExpired as exc:
        seconds = time.time() - started
        partial = exc.stdout or b""
        log_path.write_bytes(partial if isinstance(partial, bytes) else str(partial).encode())
        restored = restore_acceptance_base(base, patch_text)
        return {"state": "acceptance_timeout", "applied": True, "command": command,
                "test_command_sha256": command_sha, "exit_code": None,
                "seconds": round(seconds, 3), "timeout_s": timeout_s,
                "base_head_before": base_head_before, "base_head_after": git_head(base),
                "deps": deps, "restored": restored, "log_file": log_path.name,
                "reason": f"aceite excedeu o teto de {timeout_s}s; saída parcial em "
                          f"{log_path.name}; base restaurada"}
    except Exception as exc:  # noqa: BLE001 - aceite que nem executa e bloqueio, não patch
        seconds = time.time() - started
        restored = restore_acceptance_base(base, patch_text)
        return {"state": "acceptance_error", "applied": True, "command": command,
                "test_command_sha256": command_sha, "exit_code": None,
                "seconds": round(seconds, 3),
                "base_head_before": base_head_before, "base_head_after": git_head(base),
                "deps": deps, "restored": restored, "log_file": None,
                "reason": f"aceite não executou ({exc.__class__.__name__}: {exc}); base restaurada"}
    seconds = time.time() - started
    log_path.write_bytes(proc.stdout)
    restored = restore_acceptance_base(base, patch_text)
    if proc.returncode == 0:
        return {"state": "passed", "applied": True, "command": command,
                "test_command_sha256": command_sha, "exit_code": 0,
                "seconds": round(seconds, 3),
                "base_head_before": base_head_before, "base_head_after": git_head(base),
                "deps": deps, "restored": restored, "log_file": log_path.name, "reason": None}
    if proc.returncode == ENV_EXIT_CODE:
        return {"state": "env_blocked", "applied": True, "command": command,
                "test_command_sha256": command_sha, "exit_code": proc.returncode,
                "seconds": round(seconds, 3),
                "base_head_before": base_head_before, "base_head_after": git_head(base),
                "deps": deps, "restored": restored, "log_file": log_path.name,
                "reason": "aceite saiu com código 3 (ambiente, reservado ao harness): "
                          "julgamento bloqueado; saída preservada em acceptance_output.txt para "
                          "auditoria; não conta como sucesso nem como regressão do patch"}
    return {"state": "patch_regression", "applied": True, "command": command,
            "test_command_sha256": command_sha, "exit_code": proc.returncode,
            "seconds": round(seconds, 3),
            "base_head_before": base_head_before, "base_head_after": git_head(base),
            "deps": deps, "restored": restored, "log_file": log_path.name,
            "reason": f"aceite reprovou o patch (exit {proc.returncode})"}


DRY_SCRIPT = '''#!/usr/bin/env python3
"""Executor de infraestrutura: usa as ferramentas e edita, sem modelo. Nunca e evidencia de R3."""
import json, os, pathlib, subprocess, sys

ws = pathlib.Path(os.environ["ATLAS_WORKSPACE"])
condition = os.environ.get("ATLAS_CONDITION", "CTX-RS")
report = {"condition": condition, "steps": []}

if condition != "BASE" and os.environ.get("ATLAS_BIN"):
    import tempfile
    req = pathlib.Path(tempfile.mkdtemp(prefix="atlas-dry-req-")) / "request.json"
    req.write_text(json.dumps({"schema_version": 1, "intent": "localizar", "query": "getTitular",
                               "budget_tokens": 2000, "max_bytes": 8000, "policy": "CTX-RS"}))
    out = subprocess.run(["atlas", "context", "--repo", os.environ["ATLAS_REPO"],
                          "--index", os.environ["ATLAS_INDEX"], "--request", str(req)],
                         stdout=subprocess.PIPE)
    report["steps"].append({"tool": "atlas", "exit": out.returncode})
    try:
        env = json.loads(out.stdout.decode())
        units = env.get("units") or []
    except Exception:
        units = []
    if units:
        target = units[0]["file"]
        line = units[0]["line"]
        read = subprocess.run(["atlas-read", target, "--line", str(line)],
                              stdout=subprocess.PIPE)
        report["steps"].append({"tool": "atlas-read", "exit": read.returncode, "file": target})

for extra in json.loads(os.environ.get("ATLAS_DRY_EXTRA_CALLS", "[]")):
    subprocess.run(extra, cwd=str(ws), stdout=subprocess.PIPE)

edited = ws / "dry_edit.txt"
edited.write_text(edited.read_text() + "linha adicionada pelo executor dry\\n"
                  if edited.exists() else "linha adicionada pelo executor dry\\n")
report["declared_relevant"] = [str(edited.relative_to(ws))]
# Evento de parada pelo contrato do executor: o dry nao tem modelo, mas exercita o caminho
# do stream declarado — e por isso continua marcado `infrastructure_only`.
stream = os.environ.get("ATLAS_EXECUTOR_TELEMETRY")
if stream:
    with open(stream, "a") as fh:
        fh.write(json.dumps({"kind": "stop", "source": "executor",
                             "reason": "dry_infrastructure"}) + "\\n")
print(json.dumps(report))
'''

SLEEP_SCRIPT = '''#!/usr/bin/env python3
"""Executor de infraestrutura que so dorme, para testar o teto de parede."""
import time
time.sleep(600)
'''


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--task", required=True)
    ap.add_argument("--condition", required=True, choices=CONDITIONS)
    ap.add_argument("--workspace", required=True,
                    help="checkout de base limpa por tentativa (workspace novo)")
    ap.add_argument("--out", required=True, help="diretório da tentativa (artefatos)")
    ap.add_argument("--executor", choices=["dry", "cmd"], default="dry")
    ap.add_argument("--executor-cmd", default=None,
                    help="template com {statement_file}, {workspace}, {tool_dir}, {out_dir}")
    ap.add_argument("--allow-dry", action="store_true",
                    help="obrigatório para o executor dry: stub não é evidência")
    ap.add_argument("--atlas-bin", default=str(REPO_ROOT / "rust/archatlas/target/release/archatlas"))
    ap.add_argument("--atlas-repo", default=None, help="raiz indexada (padrão: workspace)")
    ap.add_argument("--atlas-index", default=None)
    ap.add_argument("--gold", default=None, help="diretório do ouro, fora do workspace")
    ap.add_argument("--acceptance-repo", default=None, help="base limpa para aplicar o patch")
    ap.add_argument("--phase", choices=["smoke", "piloto"], default="smoke")
    ap.add_argument("--repetition", type=int, default=0)
    ap.add_argument("--position", type=int, default=0)
    ap.add_argument("--wall-limit", type=float, default=DEFAULT_LIMITS["wall_s"])
    ap.add_argument("--turn-limit", type=int, default=DEFAULT_LIMITS["turns"])
    ap.add_argument("--tool-call-limit", type=int, default=DEFAULT_LIMITS["tool_calls"])
    ap.add_argument("--dry-extra-calls", default="[]",
                    help="JSON com comandos extras para o dry (teste de teto)")
    ap.add_argument("--executor-result", default=None,
                    help="result contract do executor (padrao: <out>/executor_result.json)")
    ap.add_argument("--expect-loop-sha", default=None,
                    help="legado: recusa iniciar se o hash da tentativa "
                    "(executor+comando+tetos+enunciado) divergir")
    ap.add_argument("--expect-loop-config-sha", default=None,
                    help="recusa iniciar se a configuração do loop (código do executor + "
                    "protocolo de ferramentas + tetos, sem caminhos nem enunciado) divergir "
                    "da fixada para a rodada")
    args = ap.parse_args()

    if args.executor == "dry" and not args.allow_dry:
        raise SystemExit("BLOQUEADO: executor `dry` sem --allow-dry. Stub nao e evidencia de R3.")
    if args.executor == "cmd" and not args.executor_cmd:
        raise SystemExit("--executor cmd exige --executor-cmd")

    workspace = Path(args.workspace).resolve()
    out = Path(args.out).resolve()
    gold = Path(args.gold).resolve() if args.gold else None
    doc = load_tasks(Path(args.tasks))
    task = pick_task(doc, args.task)

    if not workspace.is_dir():
        raise SystemExit(f"workspace ausente: {workspace}")
    out.mkdir(parents=True, exist_ok=True)
    gold_check = check_gold_separation(gold, workspace)

    # Preflight fechado do workspace (NEXT-01): SHA completo, HEAD presente e árvore
    # rastreada limpa — antes do executor, sem manifesto em caso de recusa.
    wf_preflight = preflight_workspace(workspace, task.get("base_sha"))
    base_sha = wf_preflight["base_sha_full"]

    statement_file = out / "statement.txt"
    statement_file.write_text(task["statement"])
    tools = out / "tools"
    write_shims(tools)
    telemetry = out / "telemetry.jsonl"
    telemetry.write_text("")

    atlas_index = Path(args.atlas_index).resolve() if args.atlas_index else None
    atlas_repo = Path(args.atlas_repo).resolve() if args.atlas_repo else workspace
    env = executor_env(workspace, tools, telemetry, Path(args.atlas_bin), atlas_repo,
                       atlas_index, args.condition)
    env["ATLAS_CONDITION"] = args.condition
    env["ATLAS_DRY_EXTRA_CALLS"] = args.dry_extra_calls
    result_path = Path(args.executor_result).resolve() if args.executor_result \
        else out / "executor_result.json"
    # Stream declarado e result contract: caminhos explicitos, para o executor nao adivinhar.
    env[STREAM_ENV] = str(telemetry)
    env[RESULT_ENV] = str(result_path)

    if args.executor == "dry":
        script = out / "dry_executor.py"
        script.write_text(SLEEP_SCRIPT if args.dry_extra_calls == "SLEEP" else DRY_SCRIPT)
        script.chmod(0o755)
        cmd = [sys.executable, str(script)]
    else:
        template = args.executor_cmd
        for key, value in (("{statement_file}", statement_file), ("{workspace}", workspace),
                           ("{tool_dir}", tools), ("{out_dir}", out)):
            template = template.replace(key, str(value))
        cmd = ["bash", "-lc", template]

    limits = {"wall_s": args.wall_limit, "turns": args.turn_limit,
              "tool_calls": args.tool_call_limit}
    statement_sha = sha256_file(statement_file)
    loop_sha = loop_fingerprint(args.executor, cmd, limits, statement_sha)
    # Configuração estável da rodada (NEXT-01): modelo do comando antes de substituir
    # caminhos — caminhos efetivos e enunciado ficam fora deste hash, em campos próprios.
    cmd_template = args.executor_cmd if args.executor == "cmd" else None
    config_doc = loop_config_doc(args.executor, cmd_template, limits)
    config_sha = loop_config_sha(config_doc)
    if args.expect_loop_sha and args.expect_loop_sha != loop_sha:
        raise SystemExit(
            f"BLOQUEADO: tentativa fora do loop fixado ({loop_sha} != "
            f"{args.expect_loop_sha}). Os tres bracos rodam o mesmo loop; mudar executor, "
            "ferramenta ou teto exige configuracao nova registrada, nao edicao silenciosa."
        )
    if args.expect_loop_config_sha and args.expect_loop_config_sha != config_sha:
        raise SystemExit(
            f"BLOQUEADO: configuração do loop diferente da fixada para a rodada "
            f"({config_sha} != {args.expect_loop_config_sha}). Mesmo loop em caminhos "
            "distintos produz o mesmo hash; divergência aqui significa mudança de código, "
            "ferramenta ou teto — exige configuração nova registrada."
        )
    started_iso = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    exit_code, stopped_by, killed, seconds, peak_rss, acct = run_executor(
        cmd, env, workspace, telemetry, limits, out / "executor_output.txt")
    patch_info = capture_patch(workspace, out)
    acceptance = run_acceptance(args, task, out / patch_info["file"])
    # A contabilidade viva (a mesma que fiscalizou o teto) e o uso relatado: contagem e
    # fiscalizacao nao podem divergir por releitura do stream.
    usage = acct.report()
    contract = assess_contract(args.executor, result_path, usage)
    coverage = contract["coverage"]
    result_doc = contract["result"]

    declared_model = (result_doc or {}).get("model") or {}
    identity_verified = coverage["model_identity"]["observed"]
    model_block = {
        "provider": declared_model.get("provider"),
        "id": declared_model.get("id"),
        "version": declared_model.get("version"),
        "verified_by": declared_model.get("verified_by"),
        "identity_verified": identity_verified,
        # Nome informal de modelo nao substitui identidade verificavel: sem o trio completo e
        # sem `verified_by`, o campo fica nulo **com motivo** e a tentativa nao e `real`.
        "reason": None if identity_verified else (contract["reason"]
                                                  or coverage["model_identity"]["reason"]),
    }
    declared_tokenizer = (result_doc or {}).get("tokenizer") or {}
    tokenizer_block = {
        "id": declared_tokenizer.get("id"),
        "is_exact": declared_tokenizer.get("is_exact"),
        "reason": None if declared_tokenizer.get("id") else (
            "P3 pendente: nenhum executor declarou tokenizer" if result_doc is None
            else "result contract sem tokenizer; sem ele a contagem fica em modo bytes"),
    }
    declared_cost = (result_doc or {}).get("cost") or {}
    cost_block = {
        "provider_billed": declared_cost.get("provider_billed"),
        "currency": declared_cost.get("currency"),
        "source": declared_cost.get("source"),
        "coverage": coverage["cost"],
        "stream_declared": usage.get("declared_cost"),
        "reason": None if declared_cost.get("provider_billed") is not None else
                  "P2 pendente: sem teto financeiro e sem custo faturado declarado",
        "local_cpu_s": None,
        "local_cpu_reason": "medido no nivel do processo externo pelo harness de microbenchmark, nao aqui",
        "local_peak_rss_kb": peak_rss or None,
    }
    if args.executor == "dry":
        evidence_class = "infrastructure_only"
        evidence_class_reason = ("executor dry: valida a infraestrutura, nao responde a pergunta "
                                 "de utilidade")
    elif contract["state"] == "ok":
        evidence_class = "real"
        evidence_class_reason = ("executor externo com contrato fechado: identidade de modelo, "
                                 "tokens, chamadas, turnos e custo declarados e reconciliados "
                                 "com o stream")
    elif contract["state"] == "partial":
        evidence_class = "real"
        evidence_class_reason = ("executor externo com cobertura parcial declarada; afirmacao "
                                 "sem cobertura fica bloqueada no manifesto de capacidade")
    elif contract["state"] == "missing":
        evidence_class = "unverified"
        evidence_class_reason = ("executor externo sem result contract: identidade de modelo, "
                                 "tokens, custo e motivo de parada nao verificaveis")
    else:
        evidence_class = "contract_violation"
        evidence_class_reason = ("contrato do executor violado; a tentativa nao vale como "
                                 "evidencia real (ver contract.violations)")
    capability = capability_manifest(out.name, args.condition, evidence_class,
                                     contract["state"], coverage, usage, cost_block,
                                     patch_info, gold_check)
    write_json(out / "capability_manifest.json", capability)

    manifest = {
        "schema": RUN_SCHEMA,
        "run_id": out.name,
        "platform": doc.get("platform"),
        "phase": args.phase,
        "task": {"id": task["id"], "split": task.get("split"), "category": task.get("category"),
                 "base_sha": task.get("base_sha"), "test_command": task.get("test_command"),
                 # Cópia do escopo declarado, para que o manifesto registre com que escopo a
                 # tentativa correu. `eval.py` recusa se isto divergir do conjunto de tarefas.
                 "allowed_paths": task.get("allowed_paths"),
                 "immutable_paths": task.get("immutable_paths"),
                 "origin": task.get("origin"),
                 "contamination_risk": task.get("contamination_risk")},
        "condition": args.condition,
        "snapshot": {"base_sha": base_sha, "tree_sha256": tree_hash(workspace),
                     "workspace": str(workspace),
                     "source": "workspace fornecido pelo chamador (nao criado por este runner)"},
        "tool": {
            "contract": "CLI_CONTRACT/1",
            "binary": str(args.atlas_bin) if args.condition != "BASE" else None,
            "binary_sha256": sha256_file(Path(args.atlas_bin)) if args.condition != "BASE" else None,
            "policy": {"LEX-RS": "LEX-RS", "CTX-RS": "CTX-RS"}.get(args.condition),
            "index": str(atlas_index) if atlas_index else None,
            "index_generation": None,
            "index_generation_reason": "o runner nao abre o indice; o campo vem do envelope quando houver",
            "absent_in_base": args.condition == "BASE",
        },
        "executor": {"kind": args.executor, "cmd": cmd,
                     "cmd_sha256": "sha256:" + hashlib.sha256(
                         json.dumps(cmd, sort_keys=True).encode()).hexdigest(),
                     "cmd_template": cmd_template,
                     "loop_sha256": loop_sha, "expected_loop_sha256": args.expect_loop_sha,
                     "loop_config_sha256": config_sha, "loop_config": config_doc,
                     "expected_loop_config_sha256": args.expect_loop_config_sha,
                     "task_identity": {"id": task["id"],
                                      "statement_sha256": statement_sha,
                                      "note": "mesma tarefa entre braços se confere por "
                                              "tarefa+enunciado, nunca pelo hash do loop"},
                     "tools_registered": list(FIXED_TOOLS),
                     "result_path": str(result_path),
                     "result_received": result_doc is not None},
        "model": model_block,
        "tokenizer": tokenizer_block,
        "preflight": {
            "workspace": wf_preflight,
            "overlay": {"immutable_paths": task.get("immutable_paths"),
                        "note": "overlay imutável identificado por lista declarada da tarefa; "
                                "a fiscalização é M5 no avaliador"},
            "note": "preflight fechado (NEXT-01): SHA completo, HEAD presente, árvore "
                      "rastreada limpa; base de aceitação tem preflight próprio em "
                      "acceptance.* e é restaurada após o teste (nunca reutilizar base "
                      "modificada)",
        },
        "prompt": {"statement_sha256": statement_sha,
                   "tool_specs_sha256": None,
                   "tool_specs_reason": "as descricoes das ferramentas sao do executor, nao deste runner"},
        "limits": limits,
        "usage": usage,
        "cost": cost_block,
        "contract": {
            "schema": CONTRACT_SCHEMA,
            "state": contract["state"],
            "reason": contract["reason"],
            "violations": contract["violations"],
            "missing": contract["missing"],
            "reconciliation": contract["reconciliation"],
            "coverage": coverage,
            "result_schema": (result_doc or {}).get("schema"),
            "result_error": contract["result_error"],
            # Declarado nunca se mistura com observado: os totais vem do executor e sao
            # conferidos contra o proprio stream dele — consistencia interna nao e prova.
            "provenance": {
                "totals": "declarados pelo executor e conferidos contra o proprio stream",
                "externally_observed": list(EXTERNALLY_OBSERVED),
            },
        },
        "capability": {
            "manifest": "capability_manifest.json",
            "supported_claims": [c["claim"] for c in capability["claims"] if c["supported"]],
            "unsupported_claims": [c["claim"] for c in capability["claims"]
                                  if not c["supported"]],
        },
        "cache": {"index": "indice da rodada, aquecido",
                  "filesystem": "aquecido (nao foi possivel derrubar sem maquina dedicada)"},
        "order": {"repetition": args.repetition, "position": args.position},
        "timestamps": {"started": started_iso,
                       "finished": time.strftime("%Y-%m-%dT%H:%M:%S%z")},
        "processes": [{"argv": cmd, "exit_code": exit_code}],
        "patch": patch_info,
        "acceptance": acceptance,
        "stopped_by": stopped_by,
        "stopped_killed": killed,
        "stopped_note": ("processo interrompido no teto" if killed else
                         "teto detectado depois do fim do executor" if stopped_by else None),
        "outcome": ("stopped" if stopped_by else
                    "completed" if exit_code == 0 else "failed"),
        "evidence_class": evidence_class,
        "evidence_class_reason": evidence_class_reason,
        "gold_isolation": gold_check,
        "executor_seconds": round(seconds, 3),
        "environment": environment_manifest(),
    }
    write_json(out / "manifest.json", manifest)

    print(f"tentativa {task['id']} [{args.condition}] -> {manifest['outcome']} "
          f"({manifest['evidence_class']})")
    print(f"  parede {seconds:.1f}s | tool_calls {usage['tool_calls']} "
          f"(observadas {usage['tool_calls_observed']}, declaradas {usage['tool_calls_declared']}) | "
          f"opened {usage['opened']} | delivered {usage['delivered_bytes']}B | "
          f"patch {patch_info['bytes']}B")
    print(f"  contrato {contract['state']} | modelo {model_block['id'] or 'nao verificado'} | "
          f"chamadas {usage['model_calls']} | turnos {usage['turns']} | "
          f"custo {cost_block['provider_billed']}")
    if stopped_by:
        print(f"  PARADO por teto: {stopped_by}")
    return 0 if manifest["outcome"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
