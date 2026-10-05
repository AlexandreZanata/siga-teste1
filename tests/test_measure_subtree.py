# SPDX-License-Identifier: Apache-2.0
"""Q8-real, passo 3: `measure.py --subtree` nos modos index/query.

Prova a rosca sem afirmar desempenho: default registra o corpus R2 e a raiz
registra `.`, com exit 0 nos dois lados. Pula sem dataset ou binário Rust.
"""
import json
import pathlib
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent
DATASET = REPO.parent / "siga"
RUST_BIN = REPO / "rust/archatlas/target/release/archatlas"
MEASURE = REPO / "benchmarks/rust/measure.py"

needs_env = pytest.mark.skipif(
    not DATASET.is_dir() or not RUST_BIN.exists(),
    reason="requer dataset ../siga e binário Rust compilado",
)


def run_index(out_dir: pathlib.Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(MEASURE), "--mode", "index", "--out", str(out_dir),
         "--reps", "1", "--dataset", str(DATASET),
         "--rust-bin", str(RUST_BIN), "--python-bin", sys.executable, *extra],
        cwd=str(REPO), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        timeout=300,
    )


@needs_env
def test_index_default_registra_corpus_r2(tmp_path):
    proc = run_index(tmp_path)
    assert proc.returncode == 0, proc.stdout.decode()[-2000:]
    manifest = json.loads((tmp_path / "manifest_index.json").read_text())
    assert manifest["inputs"]["corpus"] == "siga-ex/src/main/java"
    rows = [json.loads(ln) for ln in
            (tmp_path / "runs_index.jsonl").read_text().strip().splitlines()]
    assert len(rows) == 2 and all(r["exit_code"] == 0 for r in rows)


@needs_env
def test_index_raiz_registra_ponto(tmp_path):
    proc = run_index(tmp_path, "--subtree", ".")
    assert proc.returncode == 0, proc.stdout.decode()[-2000:]
    manifest = json.loads((tmp_path / "manifest_index.json").read_text())
    assert manifest["inputs"]["corpus"] == "."
    rows = [json.loads(ln) for ln in
            (tmp_path / "runs_index.jsonl").read_text().strip().splitlines()]
    assert len(rows) == 2 and all(r["exit_code"] == 0 for r in rows)
