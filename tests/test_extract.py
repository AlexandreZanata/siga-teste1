from archatlas.config import REPO_ROOT, dataset_root
# SPDX-License-Identifier: Apache-2.0
"""F2: extração+verificação sobre código real (ExMovimentacao.java)."""
import pathlib

from archatlas.extract import extract_java_symbols
from archatlas.verify import verify_symbol

ANCHOR = dataset_root() / "siga-ex/src/main/java/br/gov/jfrj/siga/ex/ExMovimentacao.java"


def test_extract_anchor_has_class():
    syms = extract_java_symbols(ANCHOR)
    classes = [s for s in syms if s["kind"] == "class" and s["name"] == "ExMovimentacao"]
    assert len(classes) == 1
    assert classes[0]["line"] >= 1


def test_zero_false_positive_all_verified():
    syms = extract_java_symbols(ANCHOR)
    assert len(syms) > 0
    for s in syms:
        ok, reason = verify_symbol(s)
        assert ok, f"falso positivo: {s} ({reason})"
