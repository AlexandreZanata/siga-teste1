#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Executa uma rodada inteira de R2 com um comando — e para no primeiro passo inválido.

O aceite de R2 pede "scripts reproduzíveis". Cinco scripts corretos invocados à mão em ordem
certa não são reproduzíveis: quem tenta de novo escolhe outra ordem, outro conjunto de
orçamentos e outra flag, e os números deixam de ser comparáveis. Este driver é a ordem, e o
`manifest_round.json` que ele grava é a prova de qual ordem foi usada.

A sequência é deliberada:

1. **corpus** — se os dois índices não cobrirem caminhos *e* bytes idênticos, o driver
   **aborta** e não gera tabela nenhuma. Uma comparação sobre corpus diferente mediria
   tamanho de corpus, não implementação.
2. **consultas** — geradas do corpus congelado, deterministicamente.
3. **`index`** — disparão de build em diretórios exclusivos, nada reaproveitado.
4. **consultas medidas** — cada especificação `POLÍTICA:ORÇAMENTOS:REPETIÇÕES` vira um
   arquivo `runs_query_*.jsonl` próprio; nada é sobrescrito.
5. **`doctor`** — processo novo, cache aquecido.
6. **tabelas** — agregadas dos `.jsonl`, nunca escritas à mão.

Os `.sqlite` ficam na pasta da rodada (gitignored) para que quem audita possa rodar `verify`
e `expand` sobre o mesmo índice; eles não são commitados.

Uso:
    python benchmarks/rust/run_round.py --run-id 2026-09-29-r2-queries
"""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _bench import environment_manifest, write_json  # noqa: E402

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent

# (política, orçamentos, repetições por consulta/braço). A mesma política aparece com dois
# regimes de orçamento porque "cabe mais" e "cabe menos" são perguntas diferentes.
DEFAULT_SPECS = [
    "CTX-RS:1000,4000:5",
    "CTX-RS:2000:10",
    "LEX-RS:2000:5",
]


STEPS: list[dict] = []


def run(step: str, argv: list[str], *, allow_fail: bool = False) -> int:
    print(f"\n=== {step}")
    print("    " + " ".join(argv))
    started = time.perf_counter()
    proc = subprocess.run(argv, cwd=str(REPO_ROOT))
    dt = time.perf_counter() - started
    print(f"    -> exit {proc.returncode} em {dt:.1f}s")
    STEPS.append({
        "step": step,
        "argv": [str(a) for a in argv],
        "exit_code": proc.returncode,
        "seconds": round(dt, 3),
    })
    if proc.returncode != 0 and not allow_fail:
        raise SystemExit(f"passo '{step}' falhou com exit {proc.returncode}; rodada abortada")
    return proc.returncode


def sha256_file(path: Path) -> str | None:
    """Hash do binário medido: sem ele, dois relatórios de R2 não sabem se mediram o mesmo."""
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_spec(spec: str) -> tuple[str, str, int]:
    try:
        policy, budgets, reps = spec.split(":")
        int(reps)
        [int(b) for b in budgets.split(",")]
    except ValueError:
        raise SystemExit(f"especificação inválida: {spec!r}; use POLITICA:orcamentos:reps")
    return policy, budgets, int(reps)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-id", required=True, help="nome da rodada, ex. 2026-09-29-r2-queries")
    ap.add_argument("--out-root", default=str(REPO_ROOT / "experiments/rust/siga"))
    ap.add_argument("--dataset", default=os.environ.get("ARCHATLAS_DATASET")
                    or str(REPO_ROOT.parent / "siga"))
    ap.add_argument("--rust-bin", default=str(REPO_ROOT / "rust/archatlas/target/release/archatlas"))
    ap.add_argument("--python-bin", default=None,
                    help="padrão: .venv/bin/python do repo, se existir; senão o interpretador atual")
    ap.add_argument("--spec", action="append", default=None,
                    help="POLITICA:orcamentos:reps (repetível); padrão = as três combinações de R2")
    ap.add_argument("--index-reps", type=int, default=10)
    ap.add_argument("--update-reps", type=int, default=3)
    ap.add_argument("--doctor-reps", type=int, default=10)
    ap.add_argument("--no-edge", action="store_true",
                    help="mede só as 30 estratificadas, sem as 6 de borda")
    ap.add_argument("--skip-index", action="store_true", help="reaproveita .sqlite já na pasta")
    ap.add_argument("--skip-update", action="store_true")
    ap.add_argument("--skip-doctor", action="store_true")
    args = ap.parse_args()

    python_bin = args.python_bin
    if python_bin is None:
        candidate = REPO_ROOT / ".venv/bin/python"
        python_bin = str(candidate) if candidate.exists() else sys.executable

    rust_bin = Path(args.rust_bin).resolve()
    if not rust_bin.exists():
        raise SystemExit(f"binário Rust ausente: {rust_bin}\n"
                         "construa com: cargo build --release --manifest-path rust/archatlas/Cargo.toml")

    out = Path(args.out_root).resolve() / args.run_id
    out.mkdir(parents=True, exist_ok=True)
    specs = [parse_spec(s) for s in (args.spec or DEFAULT_SPECS)]
    py = [python_bin]

    print(f"rodada  : {args.run_id}")
    print(f"saída   : {out}")
    print(f"dataset : {args.dataset}")
    print(f"rust    : {rust_bin}")
    print(f"python  : {python_bin}")
    print(f"specs   : {', '.join(args.spec or DEFAULT_SPECS)}")

    # 1. Corpus comum, verificado em caminhos e bytes. Aborta se não for equivalente.
    run("corpus", [*py, str(HERE / "freeze_corpus.py"), "--out", str(out),
                   "--dataset", str(args.dataset), "--rust-bin", str(rust_bin),
                   "--python-bin", python_bin, "--keep-indexes"])

    # 2. Consultas derivadas do corpus congelado.
    run("consultas", [*py, str(HERE / "gen_queries.py"),
                      "--corpus", str(out / "corpus.json"), "--out", str(out),
                      "--dataset", str(args.dataset)])

    rust_index = out / "index_rust.sqlite"
    py_index = out / "index_python.sqlite"

    # 3. Dispersão de build. Roda mesmo sem `--skip-index` reaproveitar: os índices do passo 1
    #    foram construídos uma vez cada; com `--skip-index` eles são a única fonte.
    if not args.skip_index:
        run("índice", [*py, str(HERE / "measure.py"), "--mode", "index", "--out", str(out),
                       "--reps", str(args.index_reps), "--dataset", str(args.dataset),
                       "--rust-bin", str(rust_bin), "--python-bin", python_bin])

    # 3b. Ciclo editar/testar. Trabalha sobre cópias da árvore, nunca sobre o dataset.
    if not args.skip_update:
        run("ciclo editar/testar", [*py, str(HERE / "measure.py"), "--mode", "update",
                                    "--out", str(out), "--reps", str(args.update_reps),
                                    "--dataset", str(args.dataset), "--rust-bin", str(rust_bin),
                                    "--python-bin", python_bin,
                                    "--corpus", str(out / "corpus.json")])

    # 4. Consultas medidas, uma especificação por arquivo.
    edge = [] if args.no_edge else ["--include-edge"]
    for policy, budgets, reps in specs:
        label = f"{policy}_b{budgets.replace(',', '-')}_r{reps}"
        run(f"consultas {label}",
            [*py, str(HERE / "measure.py"), "--mode", "query", "--out", str(out),
             "--policy", policy, "--budgets", budgets, "--reps", str(reps),
             "--queries", str(out / "queries.json"), "--dataset", str(args.dataset),
             "--rust-bin", str(rust_bin), "--python-bin", python_bin,
             "--rust-index", str(rust_index), "--python-index", str(py_index), *edge])

    # 5. `doctor`: só faz sentido com os dois índices presentes.
    if not args.skip_doctor:
        run("doctor", [*py, str(HERE / "measure.py"), "--mode", "doctor", "--out", str(out),
                       "--reps", str(args.doctor_reps), "--dataset", str(args.dataset),
                       "--rust-bin", str(rust_bin), "--python-bin", python_bin,
                       "--rust-index", str(rust_index), "--python-index", str(py_index)])

    # 6. Tabelas: só agregam o que está nos jsonl.
    run("tabelas", [*py, str(HERE / "report.py"), "--run", str(out)])

    write_json(out / "manifest_round.json", {
        "schema": "atlas-round/1",
        "run_id": args.run_id,
        "invocation": ["python", "benchmarks/rust/run_round.py", *sys.argv[1:]],
        "specs": [{"policy": p, "budgets": b, "reps": r} for p, b, r in specs],
        "edge_queries": not args.no_edge,
        "index_reps": args.index_reps,
        "update_reps": args.update_reps,
        "doctor_reps": args.doctor_reps,
        "inputs": {
            "dataset": str(Path(args.dataset).resolve()),
            "rust_bin": str(rust_bin),
            "rust_bin_sha256": sha256_file(rust_bin),
            "python_bin": python_bin,
        },
        "steps": STEPS,
        "environment": environment_manifest(),
    })

    print(f"\nrodada completa em {out}")
    print("versionar: corpus.json, queries.json, runs_*.jsonl, manifest_*.json, tables.md")
    print("não versionar: *.sqlite* (gitignored)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
