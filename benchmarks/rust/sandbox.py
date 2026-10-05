#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Sandbox do executor (`atlas-sandbox/1`) — isolamento com prova de acesso negado.

NEXT-03 exige mais que "diretórios distintos": o executor roda num namespace de
usuário + montagem (+ rede, por padrão) via `bwrap`, com o sistema exposto
somente leitura, o workspace ligado leitura-escrita e tudo que é sensível
(custódia, pesquisa, outras tentativas, segredos) removido do mapa — por
tmpfs, não por promessa. Antes da carga útil, a prova tenta ler cada caminho
negado e inspeciona o ambiente; qualquer visibilidade bloqueia (saída 3) com
o laudo em `proof.json`. Sem `bwrap`, a resposta honesta é recusar (saída 2),
nunca fingir isolamento.

O runner não muda: este script compõe via `--executor-cmd`, então o modelo do
comando (com o sandbox dentro) entra no `loop_config_sha256` da rodada.

Uso (o orquestrador invoca; o executor nunca se auto-isola):
    python3 sandbox.py --workspace <ws> --out-dir <att>
        --deny /caminho/custodia --deny /repo/research
        --deny /exp/run/attempts --bind-rw /exp/run/attempts/att-a1
        --ro-bind /repo/benchmarks/rust/sandbox.py
        -- /usr/bin/python3 /ro/executor-sintetico.py ...

Limites declarados (não é container completo): mesmo kernel, sem seccomp
próprio; o `.git` do workspace continua visível (o nível por caminho do
runner já declara isso insuficiente para R5). Rede isolada por padrão; rodadas
reais com provedor precisam de `--share-net` + allowlist de egresso (gate da
NEXT-04, fora deste ensaio offline).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SCHEMA = "atlas-sandbox/1"

SYSTEM_RO = ("/usr", "/bin", "/lib", "/lib64")
SECRET_MARKERS = ("GOLD", "API_KEY", "APIKEY", "TOKEN", "SECRET", "PASSWORD", "CUSTODY",
                  "CUSTODIA", "PROBE_CANARY")
PASS_ENV = ("ATLAS_TELEMETRY", "ATLAS_EXECUTOR_TELEMETRY", "ATLAS_EXECUTOR_RESULT",
            "ATLAS_WORKSPACE", "ATLAS_CONDITION", "ATLAS_BIN", "ATLAS_REPO", "ATLAS_INDEX",
            "ATLAS_DRY_EXTRA_CALLS", "ATLAS_RESULT", "PATH", "HOME", "LANG", "LC_ALL",
            "TZ", "JAVA_BIN", "JAVAC_BIN", "M2_REPO")


def build_env() -> tuple[dict, list[str]]:
    """Ambiente limpo: allowlist + PATH mínimo + HOME isolado. Devolve (env, removidos)."""
    removed: list[str] = []
    env: dict[str, str] = {}
    for key, value in os.environ.items():
        upper = key.upper()
        if any(mark in upper for mark in SECRET_MARKERS):
            removed.append(key)
            continue
        if key in PASS_ENV:
            env[key] = value
    env["PATH"] = "/usr/bin:/bin"
    env.setdefault("HOME", "/tmp/sandbox-home")
    env.setdefault("LANG", "C.UTF-8")
    return env, removed


def path_map(workspace: str, out_dir: str) -> list[tuple[str, str]]:
    """Tradução de caminho do hospedeiro para dentro da sandbox (mais longo primeiro)."""
    pairs = [(str(Path(workspace).resolve()), "/workspace"),
             (str(Path(out_dir).resolve()), "/out")]
    return sorted(pairs, key=lambda kv: -len(kv[0]))


def translate(text: str, mapping: list[tuple[str, str]]) -> str:
    for host, target in mapping:
        text = text.replace(host, target)
    return text


def bwrap_argv(args, payload: list[str], home: Path) -> list[str]:
    bwrap = shutil.which("bwrap")
    if not bwrap:
        raise SystemExit("BLOQUEADO: `bwrap` ausente — sem mecanismo efetivo, sem ensaio (sair 2).")
    argv = [bwrap, "--unshare-all", "--die-with-parent", "--new-session"]
    if args.share_net:
        argv.append("--share-net")
    argv += ["--proc", "/proc", "--dev", "/dev"]
    for path in SYSTEM_RO:
        argv += ["--ro-bind", path, path]
    argv += ["--ro-bind", "/etc", "/etc"]
    # Pais negados primeiro (tmpfs), depois os filhos reexpostos por cima.
    for path in args.deny:
        argv += ["--tmpfs", path]
    argv += ["--tmpfs", "/home", "--tmpfs", "/root"]
    argv += ["--bind", str(Path(args.workspace).resolve()), "/workspace"]
    argv += ["--bind", str(Path(args.out_dir).resolve()), "/out"]
    argv += ["--bind", str(home), "/sandbox-home"]
    for spec in args.ro_bind:
        src, _, dst = spec.partition(":")
        argv += ["--ro-bind", src, dst or src]
    for path in args.ro:
        argv += ["--ro-bind", path, path]
    argv += ["--chdir", "/workspace", "--"]
    return argv + payload


PROOF_SCRIPT = r"""
import json, os, sys

def disclosed(path):
    # Negado com sucesso = inexistente ou tmpfs vazio (a propria negacao cria o
    # ponto de montagem). Vazamento = arquivo ou diretorio COM conteudo.
    # (Diretorio vazio no hospedeiro e indistinguivel do tmpfs — e nao vaza nada.)
    if not os.path.exists(path):
        return False, "ausente"
    if os.path.isfile(path):
        return True, "arquivo visivel"
    try:
        entries = os.listdir(path)
    except OSError as exc:
        return True, f"ilegivel: {exc.__class__.__name__}"
    return (False, "tmpfs vazio") if not entries else (True, f"{len(entries)} entradas visiveis")

denied = sys.argv[1].split("\n") if len(sys.argv) > 1 and sys.argv[1] else []
markers = sys.argv[2].split(",") if len(sys.argv) > 2 and sys.argv[2] else []
rows = []
for p in denied:
    vis, how = disclosed(p)
    rows.append({"path": p, "visible": vis, "how": how})
leaked = [k for k in os.environ if any(m in k.upper() for m in markers)]
proof = {"schema": "atlas-sandbox-proof/1", "denied": rows,
         "env_leaked": leaked, "ok": not any(r["visible"] for r in rows) and not leaked}
with open("/out/sandbox_proof.json", "w") as fh:
    json.dump(proof, fh, ensure_ascii=False, indent=1)
sys.exit(0 if proof["ok"] else 3)
"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace", required=True, help="dataset da tentativa (rw na sandbox)")
    ap.add_argument("--out-dir", required=True, help="diretório da tentativa (rw; recebe proof.json)")
    ap.add_argument("--deny", action="append", default=[],
                    help="DIRETORIO sensível removido do mapa via tmpfs (pode repetir)")
    ap.add_argument("--ro-bind", action="append", default=[],
                    help="SRC[:DST] exposto somente-leitura (ferramentas, scripts)")
    ap.add_argument("--ro", action="append", default=[],
                    help="caminho exposto somente-leitura no mesmo lugar")
    ap.add_argument("--share-net", action="store_true",
                    help="NÃO isola a rede (só rodadas reais com provedor; ensaio usa rede isolada)")
    ap.add_argument("--proof-only", action="store_true",
                    help="só roda a prova, sem carga útil")
    ap.add_argument("payload", nargs=argparse.REMAINDER,
                    help="carga útil após `--`")
    args = ap.parse_args(argv)
    if args.payload and args.payload[0] == "--":
        args.payload = args.payload[1:]
    if not args.proof_only and not args.payload:
        raise SystemExit("sandbox sem carga útil (use --proof-only para só provar)")

    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    home = out / "sandbox-home"
    home.mkdir(exist_ok=True)
    env, removed = build_env()
    env["HOME"] = "/sandbox-home"
    # O chamador (runner) usa caminhos do hospedeiro; dentro da sandbox eles não
    # existem. Traduzir é parte do isolamento: o executor recebe /workspace e /out,
    # nunca o caminho real da tentativa (que poderia revelar irmãos/vizinhos).
    mapping = path_map(args.workspace, args.out_dir)
    for key in list(env):
        env[key] = translate(env[key], mapping)
    args.payload = [translate(arg, mapping) for arg in args.payload]

    denied = [str(Path(p)) for p in args.deny]
    base = bwrap_argv(args, [], home)
    python = "/usr/bin/python3"
    proof_cmd = [python, "-c", PROOF_SCRIPT, "\n".join(denied), ",".join(SECRET_MARKERS)]
    proc = subprocess.run(base + proof_cmd, env=env, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    (out / "sandbox_proof_stdout.txt").write_bytes(proc.stdout)
    proof_path = out / "sandbox_proof.json"
    if proc.returncode != 0 or not proof_path.exists():
        print(f"BLOQUEADO: prova de isolamento falhou (exit {proc.returncode}); "
              "ver sandbox_proof.json. Carga útil NÃO executada.", flush=True)
        return 3
    proof = json.loads(proof_path.read_text())
    manifest = {"schema": SCHEMA, "denied": denied,
                "env_removed": sorted(removed), "network_isolated": not args.share_net,
                "path_map": [{"host": h, "sandbox": t} for h, t in mapping],
                "proof": proof, "payload": args.payload if not args.proof_only else None}
    (out / "sandbox_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1) + "\n")
    print(f"sandbox ok: {len(denied)} caminhos negados, {len(removed)} vars removidas, "
          f"rede {'compartilhada' if args.share_net else 'isolada'}", flush=True)
    if args.proof_only:
        return 0
    proc = subprocess.run(base + args.payload, env=env)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
