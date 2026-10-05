# SPDX-License-Identifier: Apache-2.0
"""Q8-real, passo 1: `freeze_corpus.py --subtree` aditivo com prova de não-regressão.

O default reproduz o corpus R2 publicado byte a byte (fingerprint pinado);
a sonda da raiz documenta a única divergência conhecida (fixtures externas
vendoredadas com `.git` aninhado, que o walker Rust ignora e o `rglob`
Python não). Pula se dataset ou binário Rust ausentes (dependência externa).
"""
import json
import pathlib
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent
DATASET = REPO.parent / "siga"
RUST_BIN = REPO / "rust/archatlas/target/release/archatlas"
FREEZE = REPO / "benchmarks/rust/freeze_corpus.py"
PUBLISHED_FINGERPRINT = "bb7a99fbe4582c972b0c0263665156a26c15e0541e237722b27928fdcf13caba"

needs_env = pytest.mark.skipif(
    not DATASET.is_dir() or not RUST_BIN.exists(),
    reason="requer dataset ../siga e binário Rust compilado",
)


def run_freeze(out_dir: pathlib.Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(FREEZE), "--out", str(out_dir),
         "--dataset", str(DATASET), "--rust-bin", str(RUST_BIN),
         "--python-bin", sys.executable, *extra],
        cwd=str(REPO), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        timeout=300,
    )


@needs_env
def test_default_reproduz_fingerprint_publicado(tmp_path):
    proc = run_freeze(tmp_path)
    assert proc.returncode == 0, proc.stdout.decode()[-2000:]
    doc = json.loads((tmp_path / "corpus.json").read_text())
    assert doc["corpus"]["files"] == 504
    assert doc["corpus"]["content_fingerprint_sha256"] == PUBLISHED_FINGERPRINT
    assert doc["dataset"]["subtree"] == "siga-ex/src/main/java"
    assert doc["verification"]["corpus_equivalent"] is True


@needs_env
def test_subtree_explicito_igual_ao_default_e_noop(tmp_path):
    proc = run_freeze(tmp_path, "--subtree", "siga-ex/src/main/java")
    assert proc.returncode == 0, proc.stdout.decode()[-2000:]
    doc = json.loads((tmp_path / "corpus.json").read_text())
    assert doc["corpus"]["content_fingerprint_sha256"] == PUBLISHED_FINGERPRINT
    assert doc["verification"]["corpus_equivalent"] is True


@needs_env
def test_sonda_da_raiz_bloqueia_so_por_fixtures_externas(tmp_path):
    proc = run_freeze(tmp_path, "--subtree", ".")
    assert proc.returncode == 1, proc.stdout.decode()[-2000:]
    doc = json.loads((tmp_path / "corpus.json").read_text())
    ver = doc["verification"]
    assert ver["same_path_set"] is False
    assert ver["same_content_hashes"] is True  # resto idêntico: só cobertura diverge
    assert ver["counts"]["rust_files"] == 2278
    # 50 arquivos só-Python; a amostra do manifesto (truncada em 20) é toda externa.
    assert ver["counts"]["python_files"] - ver["counts"]["common"] == 50
    assert ver["only_python"] and all(
        p.startswith("siga-teste/data/external_repos/") for p in ver["only_python"])
