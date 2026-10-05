# SPDX-License-Identifier: Apache-2.0
"""Q8-real: escopo `--subtree` aditivo com prova de não-regressão.

O default reproduz o corpus R2 publicado byte a byte (fingerprint pinado);
o walker Python pula repos aninhados como o walker Rust (fixtures externas
vendoredadas com `.git` aninhado), e a raiz congela equivalente (2278).
Pula se dataset ou binário Rust ausentes (dependência externa).
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
ROOT_FINGERPRINT = "34eb6630709f24c5d96941b97e9b7f9e9bf986dfe488bf19c4c05f07e9dd173d"
PUBLISHED_QUERIES = REPO / "experiments/rust/siga/2026-09-29-r2-queries/queries.json"
PUBLISHED_CORPUS = REPO / "experiments/rust/siga/2026-09-29-r2-queries/corpus.json"

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


def test_walker_pula_repos_aninhados_sem_pular_a_raiz(tmp_path):
    from archatlas.cli import _under_nested_repo
    scope = tmp_path / "proj"
    (scope / "a").mkdir(parents=True)
    (scope / "vend" / "ext").mkdir(parents=True)
    (scope / "vend" / ".git").mkdir()
    (scope / ".git").mkdir()  # a raiz pode ser repo: nunca excluída
    f_ok = scope / "a" / "A.java"
    f_ok.touch()
    f_ext = scope / "vend" / "ext" / "E.java"
    f_ext.touch()
    f_root = scope / "R.java"
    f_root.touch()
    assert _under_nested_repo(f_ok, scope) is False
    assert _under_nested_repo(f_root, scope) is False
    assert _under_nested_repo(f_ext, scope) is True
    assert _under_nested_repo(scope / "fora" / "X.java", scope) is False


@needs_env
def test_raiz_congela_equivalente_apos_alinhar_walker(tmp_path):
    proc = run_freeze(tmp_path, "--subtree", ".")
    assert proc.returncode == 0, proc.stdout.decode()[-2000:]
    doc = json.loads((tmp_path / "corpus.json").read_text())
    assert doc["corpus"]["files"] == 2278
    assert doc["corpus"]["content_fingerprint_sha256"] == ROOT_FINGERPRINT
    assert doc["dataset"]["subtree"] == "."
    assert doc["verification"]["corpus_equivalent"] is True


@needs_env
def test_gen_queries_regenera_identino_no_default(tmp_path):
    proc = subprocess.run(
        [sys.executable, str(REPO / "benchmarks/rust/gen_queries.py"),
         "--corpus", str(PUBLISHED_CORPUS), "--out", str(tmp_path),
         "--dataset", str(DATASET)],
        cwd=str(REPO), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        timeout=300,
    )
    assert proc.returncode == 0, proc.stdout.decode()[-2000:]
    new = json.loads((tmp_path / "queries.json").read_text())
    old = json.loads(PUBLISHED_QUERIES.read_text())
    assert new["queries"] == old["queries"]
    assert new["edge"] == old["edge"]
