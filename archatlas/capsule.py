# SPDX-License-Identifier: Apache-2.0
"""Context Capsule sob budget hard (F5). Sem LLM; só índice + disco."""
from __future__ import annotations
import pathlib
import sqlite3

from archatlas.lexical import bm25_search
from archatlas.query import find_references, find_symbol


def count_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def build_capsule(con: sqlite3.Connection, query: str, budget: int, k: int = 20) -> dict:
    cands = bm25_search(con, query, k)
    for tok in query.split():
        for s in find_symbol(con, tok.strip("?,."), exact=True)[:3]:
            if (s["name"], s["file"], s["line"]) not in {(c["name"], c["file"], c["line"]) for c in cands}:
                cands.append({**s, "bm25": -1.0})
    ranked = sorted(cands, key=lambda c: (c.get("bm25", 0), c["file"], c["line"]))
    symbols, excerpts, citations, relations, log = [], [], [], [], []
    used = 0
    for i, c in enumerate(ranked):
        p = pathlib.Path(c["file"])
        try:
            line_text = p.read_text(encoding="utf-8", errors="replace").splitlines()[c["line"] - 1].strip()[:200]
        except (OSError, IndexError):
            log.append({"stage": "select", "rule": "unreadable", "dropped": c["name"], "reason": c["file"]})
            continue
        if c["name"] not in line_text and c["kind"] in ("class", "interface", "enum"):
            log.append({"stage": "select", "rule": "name-absent", "dropped": c["name"], "reason": c["file"]})
            continue
        item = f"{c['file']}:{c['line']} {c['kind']} {c['name']} :: {line_text}"
        cost = count_tokens(item)
        if used + cost > budget:
            log.append({"stage": "pack", "rule": "over_budget", "dropped": c["name"], "reason": f"+{cost} > {budget - used}"})
            continue
        symbols.append({**c, "reason": f"bm25 rank {i}", "score": round(float(-c.get('bm25', 0)), 4)})
        excerpts.append({"id": f"e{i}", "file": c["file"], "start_line": c["line"], "end_line": c["line"],
                         "tokens": cost, "truncated": False, "text": line_text, "anchors": [c["name"]]})
        citations.append({"excerpt_id": f"e{i}", "file": c["file"], "line": c["line"], "symbol": c["name"]})
        relations.append({"from": c["file"], "to": c["name"], "kind": "DEFINES",
                          "provenance": c["provenance"], "score": 1.0})
        used += cost
    files = sorted({s["file"] for s in symbols})
    return {"capsule_version": "1.0", "query": query,
            "budget": {"requested": budget, "used": used, "tokenizer": "chars//4", "hard_enforced": True},
            "symbols": symbols, "files": files, "relations": relations, "call_paths": [],
            "tests": [], "docs": [], "excerpts": excerpts, "citations": citations,
            "truncation_log": log, "stats": {"candidates": len(ranked), "kept": len(symbols)}}
