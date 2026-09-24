# SPDX-License-Identifier: Apache-2.0
"""btc-bm25text/1: índice FTS5 de linhas + ranking BM25. Sem corpus, sem modelo."""
import pathlib
import sqlite3

from archatlas.bitcoin.bm25text import bm25_lines, build_text_index


def _tiny(tmp_path):
    (tmp_path / "a.cpp").write_bytes(b'#include "a.h"\nCheckTransaction validation here\n')
    (tmp_path / "a.h").write_bytes(b"#pragma once\n")
    (tmp_path / "b.cpp").write_bytes(b"nothing relevant xyzzy\n")
    return tmp_path


def test_build_and_rank(tmp_path):
    db = tmp_path / "t.sqlite"
    info = build_text_index(db, _tiny(tmp_path))
    assert info["files"] == 3 and info["lines"] > 0 and info["db_bytes"] > 0
    con = sqlite3.connect(db)
    hits = bm25_lines(con, "CheckTransaction validation", k=10)
    assert hits and hits[0]["file"] == "a.cpp"
    scores = [h["bm25"] for h in hits]
    assert scores == sorted(scores)  # rankeado
    assert bm25_lines(con, "CheckTransaction validation", k=10) == hits  # determinismo
    assert bm25_lines(con, "a b", k=10) == []  # sem tokens: sem crash
    assert len(bm25_lines(con, "CheckTransaction validation nothing", k=1)) <= 1
    con.close()


def test_empty_root_builds_empty_index(tmp_path):
    db = tmp_path / "e.sqlite"
    info = build_text_index(db, tmp_path)
    con = sqlite3.connect(db)
    assert bm25_lines(con, "zzzznada", k=5) == []
    con.close()
