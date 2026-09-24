# SPDX-License-Identifier: Apache-2.0
"""Context Capsule sob budget hard (F5). Sem LLM; só índice + disco."""
from __future__ import annotations
import pathlib
import sqlite3

from archatlas.lexical import bm25_search
from archatlas.query import find_references, find_symbol, read_contents


def count_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def build_capsule(con: sqlite3.Connection, query: str, budget: int, k: int = 20) -> dict:
    import re as _re
    disk = read_contents(con)  # F19: lê cada arquivo UMA vez; verificação por linha mantida
    cands = bm25_search(con, query, k)
    for c in cands:
        c["tier"] = 1
    codetoks = {t for tok in query.split() for t in [tok.strip("?,.")]
                if _re.search(r"[A-Z_]", t) or len(t) > 8}
    for t in {tok.strip("?,.") for tok in query.split()}:
        for s in find_symbol(con, t, exact=True)[:3]:
            if (s["name"], s["file"], s["line"]) not in {(c["name"], c["file"], c["line"]) for c in cands}:
                cands.append({**s, "bm25": -1.0, "tier": 0})
    for t in codetoks:  # token code-like → refs verificadas, tier 0, com co-ocorrência ≥2
        for r in find_references(con, t, disk)[:30]:
            key = (r["name"], r["file"], r["line"])
            if key in {(c["name"], c["file"], c["line"]) for c in cands}:
                continue
            others = [u for u in codetoks if u != t]
            blob = "\n".join(disk.get(r["file"], []))
            if others and not any(u in blob for u in others):
                continue
            cands.append({"name": r["name"], "kind": "ref", "file": r["file"], "line": r["line"],
                          "provenance": "text-match-verified", "confidence": 0.7, "bm25": 0.0, "tier": 0})
    if not cands:  # F10: nada indexado p/ query → refs verificadas de todos os tokens
        for tok in query.split():
            for r in find_references(con, tok.strip("?,."), disk)[:10]:
                key = (r["name"], r["file"], r["line"])
                if key not in {(c["name"], c["file"], c["line"]) for c in cands}:
                    cands.append({"name": r["name"], "kind": "ref", "file": r["file"], "line": r["line"],
                                  "provenance": "text-match-verified", "confidence": 0.7, "bm25": 0.0, "tier": 0})
    ranked = sorted(cands, key=lambda c: (c.get("tier", 1), c.get("bm25", 0), c["file"], c["line"]))
    seen = {(c["name"], c["file"], c["line"]) for c in ranked}
    for c in ranked[:8]:  # expansão 1-hop p/ qualquer símbolo (métodos incluídos)
        for r in find_references(con, c["name"], disk)[:5]:
            key = (r["name"], r["file"], r["line"])
            if key not in seen:
                seen.add(key)
                ranked.append({"name": r["name"], "kind": "ref", "file": r["file"], "line": r["line"],
                               "provenance": "text-match-verified", "confidence": 0.7, "bm25": 0.0, "tier": 1,
                               "excerpt": r["excerpt"]})
    ranked = sorted(ranked, key=lambda c: (c.get("tier", 1), c.get("bm25", 0), c["file"], c["line"]))
    symbols, excerpts, citations, relations, log = [], [], [], [], []
    used = 0
    for i, c in enumerate(ranked):
        lines = disk.get(c["file"])
        try:
            line_text = lines[c["line"] - 1].strip()[:200]
        except (TypeError, IndexError):
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
        rel_kind = "REFERENCES" if c.get("kind") == "ref" else "DEFINES"
        relations.append({"from": c["file"], "to": c["name"], "kind": rel_kind,
                          "provenance": c["provenance"], "score": 1.0})
        used += cost
    files = sorted({s["file"] for s in symbols})
    return {"capsule_version": "1.0", "query": query,
            "budget": {"requested": budget, "used": used, "tokenizer": "chars//4", "hard_enforced": True},
            "symbols": symbols, "files": files, "relations": relations, "call_paths": [],
            "tests": [], "docs": [], "excerpts": excerpts, "citations": citations,
            "truncation_log": log, "stats": {"candidates": len(ranked), "kept": len(symbols)}}
