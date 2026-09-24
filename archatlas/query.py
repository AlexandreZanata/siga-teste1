# SPDX-License-Identifier: Apache-2.0
"""Query API mínima F4 — só retorna o que o índice + disco confirmam."""
from __future__ import annotations
import pathlib
import sqlite3


def find_symbol(con: sqlite3.Connection, name: str, exact: bool = True) -> list[dict]:
    if exact:
        rows = con.execute(
            "SELECT name, kind, file, line, provenance, confidence FROM symbols WHERE name=? ORDER BY file, line",
            (name,),
        ).fetchall()
    else:
        rows = con.execute(
            "SELECT name, kind, file, line, provenance, confidence FROM symbols WHERE name LIKE ? ORDER BY file, line",
            (f"%{name}%",),
        ).fetchall()
    return [{"name": r[0], "kind": r[1], "file": r[2], "line": r[3], "provenance": r[4], "confidence": r[5]} for r in rows]


def find_definition(con: sqlite3.Connection, name: str) -> list[dict]:
    rows = con.execute(
        """SELECT name, kind, file, line, provenance, confidence FROM symbols
           WHERE name=? AND kind IN ('class','interface','enum') ORDER BY file, line""",
        (name,),
    ).fetchall()
    if rows:
        return [{"name": r[0], "kind": r[1], "file": r[2], "line": r[3], "provenance": r[4], "confidence": r[5]} for r in rows]
    return find_symbol(con, name, exact=True)


def find_references(con: sqlite3.Connection, name: str) -> list[dict]:
    """Referências textuais verificadas: cada hit exige nome literal na linha lida do disco."""
    files = [r[0] for r in con.execute("SELECT path FROM files ORDER BY path").fetchall()]
    out: list[dict] = []
    for f in files:
        p = pathlib.Path(f)
        if not p.exists():
            continue
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines, 1):
            if name in line:
                out.append({"name": name, "file": f, "line": i,
                            "provenance": "text-match-verified", "confidence": 0.7,
                            "excerpt": line.strip()[:200]})
    return out
