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

O executor `dry` existe para testar esta infraestrutura sem modelo. Todo run com ele sai marcado
`evidence_class: infrastructure_only`, e o runner se recusa a rodá-lo sem `--allow-dry`: um stub
nunca pode ser confundido com evidência de R3.

Uso:
    python benchmarks/rust/runner.py --tasks tarefas.json --task s01 --condition CTX-RS \\
        --workspace /caminho/worktree --out experiments/rust/siga/<run_id>/attempts \\
        --atlas-bin rust/archatlas/target/release/archatlas --atlas-index /tmp/idx.sqlite \\
        --executor-cmd 'meu-agente --enunciado {statement_file} --dir {workspace}' \\
        --gold /caminho/ouro
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
        log({"kind": "read_denied", "file": str(target), "reason": "outside_workspace"})
        print("atlas-read: caminho fora do workspace", file=sys.stderr)
        return 4
    try:
        lines = resolved.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        log({"kind": "read_denied", "file": str(target), "reason": f"io:{exc.__class__.__name__}"})
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
    log({"kind": "opened", "file": str(resolved.relative_to(root)), "from": first, "to": last,
         "lines": len(lines), "bytes": len(body), "ts": time.time()})
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
            fh.write(json.dumps({"kind": "tool_call", "tool": "atlas", "argv": sys.argv[1:],
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
    """Teto primeiro. Cada evento passa por aqui; o primeiro teto atingido para a tentativa."""

    def __init__(self, limits: dict):
        self.limits = limits
        self.started = time.time()
        self.tool_calls = 0
        self.opened = 0
        self.delivered_bytes = 0
        self.turns: int | None = None
        self._saw_turn_event = False

    def absorb(self, path: Path) -> None:
        """Lê o stream de telemetria (append-only) e atualiza a contabilidade."""
        if not path.exists():
            return
        for line in path.read_text().splitlines():
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
        if kind == "tool_call":
            self.tool_calls += 1
            self.delivered_bytes += int(ev.get("stdout_bytes") or 0)
        elif kind == "opened":
            # Leitura sancionada **conta como chamada de ferramenta**: o teto do protocolo §4 é de
            # "chamadas de ferramenta por tentativa", e ler um arquivo por uma ferramenta é uma.
            # Contar só o `atlas` deixaria o braço BASE sem teto nenhum de chamadas.
            self.tool_calls += 1
            self.opened += 1
        elif kind == "turn":
            self._saw_turn_event = True
            self.turns = (self.turns or 0) + 1

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
        out = {
            "wall_s": round(self.wall_s, 3),
            "tool_calls": self.tool_calls,
            "opened": self.opened,
            "delivered_bytes": self.delivered_bytes,
            "turns": self.turns,
            "turns_reason": None if self._saw_turn_event else
                            "executor nao emitiu evento de turno; teto de turnos nao fiscalizavel",
            "retrieved_candidates": None,
            "retrieved_reason": "o envelope do `context` nao expoe a contagem interna de candidatos",
        }
        return out


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
                 output_path: Path) -> tuple[int | None, str | None, bool, float, int]:
    """Roda o executor medindo-o por fora e mata no primeiro teto.

    A saída vai para **arquivo**, não para um pipe: um executor que escreve mais do que o buffer
    do pipe encheria e travaria sozinho, e o `Popen` com `poll()` não estaria consumindo. Com
    arquivo não existe esse ponto morto, e o log fica auditável.
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
    return proc.returncode, stopped, killed, time.time() - started, peak_rss


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


def run_acceptance(args, task: dict, patch: Path) -> dict:
    """Patch candidato aplicado a base limpa, testado com comando imutável do avaliador."""
    if not args.acceptance_repo:
        return {"applied": None, "exit_code": None, "seconds": None,
                "reason": "sem --acceptance-repo: nenhuma base limpa fornecida nesta tentativa"}
    if patch.read_bytes() == b"":
        return {"applied": None, "exit_code": None, "seconds": None,
                "reason": "patch vazio; nada a aplicar"}
    base = Path(args.acceptance_repo).resolve()
    apply_proc = subprocess.run(["git", "-C", str(base), "apply", "--check", str(patch)],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if apply_proc.returncode != 0:
        return {"applied": False, "exit_code": None, "seconds": None,
                "reason": apply_proc.stdout.decode("utf-8", errors="replace")[-400:]}
    subprocess.run(["git", "-C", str(base), "apply", str(patch)], check=True)
    command = task["test_command"]
    started = time.time()
    proc = subprocess.run(command, cwd=str(base), stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, timeout=task.get("timeout_s", 600))
    seconds = time.time() - started
    (Path(args.out).resolve() / "acceptance_output.txt").write_bytes(proc.stdout)
    return {"applied": True, "command": command, "exit_code": proc.returncode,
            "seconds": round(seconds, 3), "reason": None}


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

    base_sha = subprocess.run(["git", "-C", str(workspace), "rev-parse", "HEAD"],
                              stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
                              ).stdout.decode().strip() or None
    if task.get("base_sha") and base_sha and not base_sha.startswith(task["base_sha"][:8]):
        raise SystemExit(f"workspace nao esta no snapshot pedido: {base_sha} vs {task['base_sha']}")

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
    started_iso = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    exit_code, stopped_by, killed, seconds, peak_rss = run_executor(
        cmd, env, workspace, telemetry, limits, out / "executor_output.txt")
    patch_info = capture_patch(workspace, out)
    acceptance = run_acceptance(args, task, out / patch_info["file"])
    usage = Accounting(limits)
    usage.absorb(telemetry)

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
        "model": {"provider": None, "id": None, "version": None,
                  "reason": "P1 pendente: modelo efetivo e decisao do usuario"},
        "tokenizer": {"id": None, "reason": "P3 pendente: tokenizer do modelo nao definido"},
        "prompt": {"statement_sha256": sha256_file(statement_file),
                   "tool_specs_sha256": None,
                   "tool_specs_reason": "as descricoes das ferramentas sao do executor, nao deste runner"},
        "limits": limits,
        "usage": usage.report(),
        "cost": {
            "provider_billed": None, "currency": None,
            "reason": "P2 pendente: sem teto financeiro e sem telemetria de provedor",
            "local_cpu_s": None,
            "local_cpu_reason": "medido no nivel do processo externo pelo harness de microbenchmark, nao aqui",
            "local_peak_rss_kb": peak_rss or None,
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
        "evidence_class": ("infrastructure_only" if args.executor == "dry" else "real"),
        "evidence_class_reason": ("executor dry: valida a infraestrutura, nao responde a pergunta "
                                  "de utilidade" if args.executor == "dry"
                                  else "executor externo; utilidade ainda depende de modelo e rubrica"),
        "gold_isolation": gold_check,
        "executor_seconds": round(seconds, 3),
        "environment": environment_manifest(),
    }
    write_json(out / "manifest.json", manifest)

    print(f"tentativa {task['id']} [{args.condition}] -> {manifest['outcome']} "
          f"({manifest['evidence_class']})")
    print(f"  parede {seconds:.1f}s | tool_calls {usage.tool_calls} | opened {usage.opened} | "
          f"delivered {usage.delivered_bytes}B | patch {patch_info['bytes']}B")
    if stopped_by:
        print(f"  PARADO por teto: {stopped_by}")
    return 0 if manifest["outcome"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
