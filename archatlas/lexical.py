# SPDX-License-Identifier: Apache-2.0
"""Léxico BM25 via SQLite FTS5 (F5)."""
from __future__ import annotations
import re
import sqlite3

LEX_SCHEMA = "CREATE VIRTUAL TABLE IF NOT EXISTS lex_docs USING fts5(name, kind, file, tokenize='porter');"


def rebuild_lexical(con: sqlite3.Connection) -> int:
    con.execute("DROP TABLE IF EXISTS lex_docs")
    con.execute(LEX_SCHEMA)
    rows = con.execute("SELECT name, kind, file FROM symbols").fetchall()
    con.executemany("INSERT INTO lex_docs(name, kind, file) VALUES (?,?,?)", rows)
    con.commit()
    return len(rows)


def _fts_query(q: str) -> str:
    toks = re.findall(r"[A-Za-z0-9_]+", q)
    return " OR ".join(f'"{t}"' for t in toks) or '""'


def bm25_search(con: sqlite3.Connection, query: str, k: int = 20) -> list[dict]:
    fq = _fts_query(query)
    rows = con.execute(
        """SELECT s.name, s.kind, s.file, s.line, s.provenance, s.confidence, bm25(lex_docs) AS b
           FROM lex_docs JOIN symbols s ON s.name=lex_docs.name AND s.file=lex_docs.file
           WHERE lex_docs MATCH ? ORDER BY b LIMIT ?""",
        (fq, k),
    ).fetchall()
    seen, out = set(), []
    for r in rows:
        key = (r[0], r[2], r[3])
        if key in seen:
            continue
        seen.add(key)
        out.append({"name": r[0], "kind": r[1], "file": r[2], "line": r[3],
                    "provenance": r[4], "confidence": r[5], "bm25": r[6]})
    return out
