# SPDX-License-Identifier: Apache-2.0
"""P6-exec (c): adaptadores por linguagem + linha de base documentada. Sem tarefas."""
import pathlib

import pytest

from archatlas.dataset import EXT_MAP, discover, extract_any

T1 = pathlib.Path("/tmp/opencode-p6/t1")
T2 = pathlib.Path("/tmp/opencode-p6/t2")
clones_here = T1.is_dir() and T2.is_dir()


def test_adapters_dispatch_and_levels():
    assert EXT_MAP[".java"] == "java" and EXT_MAP[".py"] == "python"
    assert ".feature" not in EXT_MAP and ".rst" not in EXT_MAP  # lacuna declarada
    assert extract_any(pathlib.Path("x.md"), "md") == []  # sem extrator → vazio honesto
    assert extract_any(pathlib.Path("x.cpp"), "cpp") == []


def test_synthetic_java_python_jsp(tmp_path):
    j = tmp_path / "A.java"
    j.write_bytes(b"public class A {\n public void m() {}\n}\n")
    p = tmp_path / "b.py"
    p.write_bytes(b"class B:\n    def f(self):\n        pass\n")
    assert [s["name"] for s in extract_any(j, "java")] == ["A", "m"]
    assert [s["name"] for s in extract_any(p, "python")] == ["B", "f"]
    assert all(s["confidence"] == 1.0 for s in extract_any(p, "python"))
    found = {f.name for f, _ in discover(tmp_path)}
    assert {"A.java", "b.py"} <= found


@pytest.mark.skipif(not clones_here, reason="clones /tmp/opencode-p6 ausentes: só sintético")
def test_baseline_counts_match_checkouts():
    t1 = [(f, l) for f, l in discover(T1)]
    t2 = [(f, l) for f, l in discover(T2)]
    assert sum(1 for _, l in t1 if l == "java") == 842
    assert sum(1 for _, l in t1 if l == "js") == 4
    assert sum(1 for _, l in t2 if l == "python") == 274
    rep = pathlib.Path("experiments/transfer/BASELINE.md").read_text(encoding="utf-8")
    assert "3411" in rep and "7328" in rep and "300/300" in rep
