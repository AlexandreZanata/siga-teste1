# SPDX-License-Identifier: Apache-2.0
"""Store SQLite + incremental por content-hash (F3)."""
from __future__ import annotations
import hashlib
import pathlib
import sqlite3

from archatlas.extract import extract_java_symbols

SCHEMA = """
CREATE TABLE IF NOT EXISTS files(path TEXT PRIMARY KEY, content_hash TEXT NOT NULL, commit_sha TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS symbols(name TEXT NOT NULL, kind TEXT NOT NULL, file TEXT NOT NULL,
  line INTEGER NOT NULL, content_hash TEXT NOT NULL, provenance TEXT NOT NULL, confidence REAL NOT NULL);
CREATE INDEX IF NOT EXISTS idx_sym_file ON symbols(file);
"""


def open_db(db: pathlib.Path) -> sqlite3.Connection:
    con = sqlite3.connect(db)
    con.executescript(SCHEMA)
    return con


def index_file(con: sqlite3.Connection, path: pathlib.Path, commit_sha: str) -> str:
    raw = pathlib.Path(path).read_bytes()
    chash = hashlib.sha256(raw).hexdigest()
    row = con.execute("SELECT content_hash FROM files WHERE path=?", (str(path),)).fetchone()
    if row and row[0] == chash:
        return "skipped"
    syms = extract_java_symbols(pathlib.Path(path))
    con.execute("DELETE FROM symbols WHERE file=?", (str(path),))
    con.execute("REPLACE INTO files(path, content_hash, commit_sha) VALUES (?,?,?)", (str(path), chash, commit_sha))
    con.executemany(
        "INSERT INTO symbols(name, kind, file, line, content_hash, provenance, confidence) VALUES (?,?,?,?,?,?,?)",
        [(s["name"], s["kind"], s["file"], s["line"], s["content_hash"], s["provenance"], s["confidence"]) for s in syms],
    )
    con.commit()
    return "indexed"


def index_any(con: sqlite3.Connection, path: pathlib.Path, lang: str, commit_sha: str) -> str:
    from archatlas.dataset import extract_any
    raw = pathlib.Path(path).read_bytes()
    chash = hashlib.sha256(raw).hexdigest()
    row = con.execute("SELECT content_hash FROM files WHERE path=?", (str(path),)).fetchone()
    if row and row[0] == chash:
        return "skipped"
    syms = extract_any(pathlib.Path(path), lang)
    con.execute("DELETE FROM symbols WHERE file=?", (str(path),))
    con.execute("REPLACE INTO files(path, content_hash, commit_sha) VALUES (?,?,?)", (str(path), chash, commit_sha))
    con.executemany(
        "INSERT INTO symbols(name, kind, file, line, content_hash, provenance, confidence) VALUES (?,?,?,?,?,?,?)",
        [(s["name"], s["kind"], s["file"], s["line"], s["content_hash"], s["provenance"], s["confidence"]) for s in syms],
    )
    con.commit()
    return "indexed"


def index_discovered(con: sqlite3.Connection, root: pathlib.Path, commit_sha: str,
                     limit: int = 0) -> dict:
    from archatlas.dataset import discover
    counts: dict = {"indexed": 0, "skipped": 0, "langs": {}}
    items = discover(root)
    if limit:
        items = items[:limit]
    for p, lang in items:
        counts[index_any(con, p, lang, commit_sha)] += 1
        counts["langs"][lang] = counts["langs"].get(lang, 0) + 1
    return counts


def index_many(con: sqlite3.Connection, paths: list[pathlib.Path], commit_sha: str) -> dict:
    counts = {"indexed": 0, "skipped": 0}
    for p in paths:
        counts[index_file(con, p, commit_sha)] += 1
    return counts


def stable_hash(con: sqlite3.Connection) -> str:
    rows = con.execute("SELECT name, kind, file, line, content_hash FROM symbols ORDER BY file, line, name").fetchall()
    h = hashlib.sha256()
    for r in rows:
        h.update(("|".join(map(str, r))).encode())
    return h.hexdigest()
