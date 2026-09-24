# SPDX-License-Identifier: Apache-2.0
"""BM25 textual Bitcoin (`btc-bm25text/1`). Variante local, não fork do core.

Motivo: `archatlas.lexical` indexa a tabela `symbols`, que no corpus Bitcoin só tem
Python-AST (C++ rende zero símbolos — AUDIT A2 em escala). Este módulo indexa LINHAS
de texto (C++/Python) em FTS5 e devolve trechos ranqueados por BM25, sem afirmar
semântica. Puro e determinístico (stdlib-only + SQLite do ambiente).
"""
from __future__ import annotations
import pathlib
import re
import sqlite3

from archatlas.dataset import EXCLUDE_DIRS

SCHEMA = ("CREATE TABLE IF NOT EXISTS btc_lines(file TEXT NOT NULL, line INTEGER NOT NULL, "
          "text TEXT NOT NULL, PRIMARY KEY (file, line));"
          "CREATE VIRTUAL TABLE IF NOT EXISTS btc_fts USING fts5(file, line, text, "
          "tokenize='porter');")
SUFFIXES = {".c", ".h", ".hpp", ".cpp", ".py"}


def build_text_index(db: pathlib.Path, root: pathlib.Path) -> dict:
    """Indexa linhas de C++/Python sob `root` explícito. Retorna contagens."""
    root = pathlib.Path(root)
    db = pathlib.Path(db)
    con = sqlite3.connect(db)
    con.executescript("DROP TABLE IF EXISTS btc_lines; DROP TABLE IF EXISTS btc_fts;" + SCHEMA)
    files, lines = 0, 0
    batch = []
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix not in SUFFIXES:
            continue
        if EXCLUDE_DIRS & set(p.parts):
            continue
        rel = str(p.relative_to(root))
        files += 1
        for i, text in enumerate(p.read_bytes().decode("utf-8", errors="replace").splitlines(), 1):
            if text.strip():
                batch.append((rel, i, text.strip()[:500]))
                lines += 1
        if len(batch) >= 20000:
            con.executemany("INSERT INTO btc_lines VALUES (?,?,?)", batch)
            con.executemany("INSERT INTO btc_fts(file, line, text) VALUES (?,?,?)", batch)
            batch = []
    if batch:
        con.executemany("INSERT INTO btc_lines VALUES (?,?,?)", batch)
        con.executemany("INSERT INTO btc_fts(file, line, text) VALUES (?,?,?)", batch)
    con.commit()
    size = db.stat().st_size
    con.close()
    return {"files": files, "lines": lines, "db_bytes": size}


def _fts_query(query: str) -> str | None:
    toks = re.findall(r"[A-Za-z0-9_]+", query.lower())
    toks = [t for t in toks if len(t) > 2 or t in {"qt", "ui", "tx", "rx"}]
    return " OR ".join(f'"{t}"' for t in toks) or None


def bm25_lines(con: sqlite3.Connection, query: str, k: int = 200) -> list[dict]:
    """Top-k linhas por BM25 (rankeadas). Query sem tokens → []. Sem crash."""
    fq = _fts_query(query)
    if fq is None:
        return []
    rows = con.execute(
        """SELECT file, line, text, bm25(btc_fts) AS b FROM btc_fts
           WHERE btc_fts MATCH ? ORDER BY b LIMIT ?""", (fq, k)).fetchall()
    seen, out = set(), []
    for f, line, text, b in rows:
        if (f, line) in seen:
            continue
        seen.add((f, line))
        out.append({"file": f, "line": line, "text": text, "bm25": b})
    return out
