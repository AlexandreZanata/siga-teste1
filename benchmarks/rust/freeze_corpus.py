#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Congela o corpus comum e **prova** que os dois índices cobrem o mesmo conjunto.

Resolve a pendência Q1 de `research/rust/R1_REPORT.md` §5. O problema era concreto: a
referência Python indexa `siga-ex/src/main/java/**/*.java` (504 arquivos), enquanto a
descoberta do Rust é genérica e cobre o repositório inteiro (6.916). Comparar os dois "como
estão" mediria tamanho de corpus, não implementação.

Aqui os dois lados são forçados ao mesmo conjunto, e a igualdade é **verificada em duas
camadas**: conjunto de caminhos e hash de conteúdo por arquivo. Sem as duas, um caminho
igual com bytes diferentes passaria batido.

Uso:
    python benchmarks/rust/freeze_corpus.py --out experiments/rust/siga/<run_id>
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _bench import environment_manifest, find_time_bin, write_json  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SUBTREE = "siga-ex/src/main/java"


def python_index(dataset: Path, index: Path, python_bin: str, subtree: str) -> dict:
    index.unlink(missing_ok=True)
    env = dict(os.environ, ARCHATLAS_DATASET=str(dataset))
    proc = subprocess.run(
        [python_bin, "-m", "archatlas.cli", "index", "--db", str(index),
         "--subtree", subtree],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise SystemExit(
            f"indice Python falhou ({proc.returncode}): {proc.stderr.decode()[-500:]}"
        )
    return {"stdout": proc.stdout.decode().strip()}


def rust_index(dataset: Path, index: Path, rust_bin: Path, subtree: str) -> dict:
    index.unlink(missing_ok=True)
    for extra in (Path(str(index) + "-wal"), Path(str(index) + "-shm")):
        extra.unlink(missing_ok=True)
    proc = subprocess.run(
        [
            str(rust_bin), "index",
            "--repo", str(dataset / subtree),
            "--index", str(index),
            # O filtro é o que torna o corpus idêntico ao da referência.
            "--include", "java",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise SystemExit(
            f"indice Rust falhou ({proc.returncode}): {proc.stderr.decode()[-500:]}"
        )
    import json

    return json.loads(proc.stdout.decode())["counts"]


def read_side(index: Path, root_prefix: Path | None) -> dict[str, str]:
    """Lê `(path relativo -> sha256)` de um índice. `root_prefix` remove o prefixo absoluto."""
    con = sqlite3.connect(f"file:{index}?mode=ro", uri=True)
    rows = con.execute("SELECT path, content_hash FROM files").fetchall()
    con.close()
    out: dict[str, str] = {}
    for path, chash in rows:
        p = Path(path)
        if root_prefix is not None:
            try:
                p = p.relative_to(root_prefix)
            except ValueError:
                p = Path(path)
        out[p.as_posix()] = chash.lower()
    return out


def fingerprint(files: dict[str, str]) -> str:
    h = hashlib.sha256()
    for rel in sorted(files):
        h.update(rel.encode())
        h.update(b"\0")
        h.update(files[rel].encode())
        h.update(b"\n")
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataset", default=os.environ.get("ARCHATLAS_DATASET") or str(REPO_ROOT.parent / "siga"))
    ap.add_argument("--out", required=True, help="diretorio da rodada (artefatos)")
    ap.add_argument("--rust-bin", default=str(REPO_ROOT / "rust/archatlas/target/release/archatlas"))
    ap.add_argument("--python-bin", default=sys.executable)
    ap.add_argument("--keep-indexes", action="store_true", help="manter os .sqlite na saida")
    ap.add_argument("--subtree", default=SUBTREE,
                    help="subarvore do dataset a congelar (default: corpus R2; Q8-real usa a raiz)")
    args = ap.parse_args()

    dataset = Path(args.dataset).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    find_time_bin()  # falha cedo se não houver medição confiável

    subtree = dataset / args.subtree
    if not subtree.is_dir():
        raise SystemExit(f"subarvore ausente: {subtree}")

    py_index = out / "index_python.sqlite"
    rs_index = out / "index_rust.sqlite"

    print(f"[1/3] indice Python ({args.subtree}, *.java)...")
    py_raw = python_index(dataset, py_index, args.python_bin, args.subtree)
    print(f"[2/3] indice Rust (mesma subarvore, --include java)...")
    rs_counts = rust_index(dataset, rs_index, Path(args.rust_bin), args.subtree)

    print("[3/3] conferindo igualdade de corpus...")
    py_files = read_side(py_index, subtree)
    rs_files = read_side(rs_index, None)

    only_py = sorted(set(py_files) - set(rs_files))
    only_rs = sorted(set(rs_files) - set(py_files))
    common = sorted(set(py_files) & set(rs_files))
    hash_divergent = [p for p in common if py_files[p] != rs_files[p]]

    same_set = not only_py and not only_rs
    same_bytes = not hash_divergent
    corpus_ok = same_set and same_bytes

    dataset_sha = subprocess.run(
        ["git", "-C", str(dataset), "rev-parse", "--short", "HEAD"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    ).stdout.decode().strip() or None

    manifest = {
        "schema": "atlas-corpus/1",
        "dataset": {"root_name": dataset.name, "sha": dataset_sha, "subtree": args.subtree},
        "corpus": {
            "files": len(common),
            "list_sha256": hashlib.sha256("\n".join(common).encode()).hexdigest(),
            "content_fingerprint_sha256": fingerprint({p: py_files[p] for p in common}),
            "paths": common,
        },
        "verification": {
            "same_path_set": same_set,
            "same_content_hashes": same_bytes,
            "corpus_equivalent": corpus_ok,
            "only_python": only_py[:20],
            "only_rust": only_rs[:20],
            "hash_divergent": hash_divergent[:20],
            "counts": {
                "python_files": len(py_files),
                "rust_files": len(rs_files),
                "common": len(common),
            },
        },
        "side_config": {
            "python": {"index": py_index.name, "stdout": py_raw["stdout"], "root_prefix": args.subtree},
            "rust": {"index": rs_index.name, "counts": rs_counts, "root_prefix": "(ja relativo)"},
        },
        "environment": environment_manifest(),
    }
    write_json(out / "corpus.json", manifest)

    print()
    print(f"  arquivos Python : {len(py_files)}")
    print(f"  arquivos Rust   : {len(rs_files)}")
    print(f"  comuns          : {len(common)}")
    print(f"  mesmo conjunto  : {same_set}")
    print(f"  mesmos bytes    : {same_bytes}")
    if only_py:
        print(f"  so no Python    : {only_py[:5]}")
    if only_rs:
        print(f"  so no Rust      : {only_rs[:5]}")
    if hash_divergent:
        print(f"  hash divergente : {hash_divergent[:5]}")
    print(f"  fingerprint     : {manifest['corpus']['content_fingerprint_sha256'][:16]}")
    print()
    print(f"corpus congelado em {out / 'corpus.json'}")

    if not args.keep_indexes:
        py_index.unlink(missing_ok=True)
        rs_index.unlink(missing_ok=True)
        for extra in ("-wal", "-shm"):
            Path(str(rs_index) + extra).unlink(missing_ok=True)

    if not corpus_ok:
        print("\nBLOQUEADO: corpus nao equivalente; a comparacao de R2 seria invalida.")
        return 1
    print("OK: corpus equivalente (caminhos e bytes).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
