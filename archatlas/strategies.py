# SPDX-License-Identifier: Apache-2.0
"""Bake-off F13: 4 metodologias comparáveis + roteador em cascata (sem LLM, sem chute)."""
from __future__ import annotations
import sqlite3

from archatlas.capsule import build_capsule
from archatlas.lexical import bm25_search
from archatlas.query import find_definition, find_symbol


def s_lexical(con: sqlite3.Connection, q: str) -> set[str]:
    return {h["file"] for h in bm25_search(con, q, 20)}


def s_structural(con: sqlite3.Connection, q: str) -> set[str]:
    out: set[str] = set()
    for tok in q.split():
        t = tok.strip("?,.")
        for s in find_symbol(con, t, exact=True)[:3]:
            out.add(s["file"])
        for s in find_definition(con, t):
            out.add(s["file"])
    return out


def s_hybrid(con: sqlite3.Connection, q: str) -> set[str]:
    return s_lexical(con, q) | s_structural(con, q)


def s_hybrid_refs(con: sqlite3.Connection, q: str, budget: int = 2000) -> set[str]:
    return set(build_capsule(con, q, budget)["files"])


def s_router(con: sqlite3.Connection, q: str, budget: int = 2000) -> set[str]:
    """Cascata: estrutural exato → +BM25 → +refs. Para no primeiro nível com ≥3 arquivos."""
    files = s_structural(con, q)
    if len(files) >= 3:
        return files
    files |= s_lexical(con, q)
    if len(files) >= 3:
        return files
    return s_hybrid_refs(con, q, budget)

STRATEGIES = {"lexical": s_lexical, "structural": s_structural, "hybrid": s_hybrid,
              "hybrid_refs": s_hybrid_refs, "router": s_router}
