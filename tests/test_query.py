from archatlas.config import REPO_ROOT, dataset_root
# SPDX-License-Identifier: Apache-2.0
"""F4: Query API sobre índice real (âncoras ExMovimentacao / ExMobilVO)."""
import pathlib
import shutil

from archatlas.query import find_definition, find_references, find_symbol
from archatlas.store import index_many, open_db

A = dataset_root() / "siga-ex/src/main/java/br/gov/jfrj/siga/ex/ExMovimentacao.java"
B = dataset_root() / "siga-ex/src/main/java/br/gov/jfrj/siga/ex/vo/ExMobilVO.java"
SHA = "e3be22828f787cbe71b339aecb7a7bf569099803"


def _db(tmp_path):
    d = tmp_path / "w"
    d.mkdir()
    files = []
    for i, src in enumerate([A, B]):
        dst = d / f"F{i}.java"
        shutil.copy(src, dst)
        files.append(dst)
    con = open_db(tmp_path / "q.sqlite")
    index_many(con, files, SHA)
    return con, files


def test_find_symbol_exact(tmp_path):
    con, files = _db(tmp_path)
    hits = find_symbol(con, "ExMovimentacao", exact=True)
    classes = [h for h in hits if h["kind"] == "class"]
    assert len(classes) == 1
    assert classes[0]["file"] == str(files[0])
    for h in hits:
        line = pathlib.Path(h["file"]).read_text(encoding="utf-8", errors="replace").splitlines()[h["line"] - 1]
        assert "ExMovimentacao" in line


def test_find_definition_prefers_class(tmp_path):
    con, _ = _db(tmp_path)
    defs = find_definition(con, "ExMovimentacao")
    assert len(defs) == 1 and defs[0]["kind"] == "class"


def test_find_references_verified(tmp_path):
    con, _ = _db(tmp_path)
    refs = find_references(con, "ExMobilVO")
    assert len(refs) >= 1
    for r in refs:
        text = pathlib.Path(r["file"]).read_text(encoding="utf-8", errors="replace").splitlines()[r["line"] - 1]
        assert "ExMobilVO" in text
