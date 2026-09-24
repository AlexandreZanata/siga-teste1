# SPDX-License-Identifier: Apache-2.0
"""Context Capsule sob budget hard (F5). Sem LLM; só índice + disco."""
from __future__ import annotations
import pathlib
import sqlite3

from archatlas.lexical import bm25_search
from archatlas.packing import apply_focus, focus_terms, pack_ranked
from archatlas.query import find_references, find_symbol, read_contents
from archatlas.telemetry import payload_tokens_for_capsule


def count_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _rank_candidates(con: sqlite3.Connection, query: str, k: int,
                     disk: dict) -> list[dict]:
    """Ranking F5–F19 verbatim (E26-02 congela aqui; só packing varia)."""
    import re as _re
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
    return ranked


def build_capsule(con: sqlite3.Connection, query: str, budget: int, k: int = 20,
                  packing: str = "multi", abstain: bool = False,
                  focus: str | None = None) -> dict:
    """Monta a cápsula; `packing` ∈ {one_per_file, multi, expanded} (E26-02).

    Default `multi` reproduz o comportamento F5–F19 byte a byte nos campos
    legados (mesmo ranking, mesmos gates, mesmos ids `e{i}`). Chamadores
    antigos (harness, strategies, testes) seguem funcionando sem mudanças.
    `abstain=True` (P4-infra(c), default False) aplica o gate dev-calibrado de
    `archatlas/abstain.py`: vazio duplo → entrega vazia + motivo explícito.
    `focus=None` (E26-04, default) desliga a poda; com texto, aplica seleção
    determinística pós-montagem (originais contados, omissões no log).
    """
    disk = read_contents(con)  # F19: lê cada arquivo UMA vez; verificação por linha mantida
    ranked = _rank_candidates(con, query, k, disk)
    gate = {"abstain": False, "reason": None, "uncertain": None,
            "note": "gate desligado (default); sem retenção"}
    if abstain:
        from archatlas.abstain import decide, features
        from archatlas.lexical import bm25_search as _bm25
        from archatlas.modules import seed_entities as _seeds
        _seeds_n = _seeds(con, query)
        _lex = _bm25(con, query, k)
        _top = min((h["bm25"] for h in _lex), default=None)
        dec = decide(features(len(_seeds_n), len(_lex), _top))
        gate = {"abstain": dec["abstain"], "reason": dec["reason"],
                "uncertain": dec["uncertain"], "note": "gate dev-calibrado E26-01"}
        if dec["abstain"]:
            out = {"capsule_version": "1.0", "query": query,
                   "budget": {"requested": budget, "used": 0, "tokenizer": "chars//4",
                              "hard_enforced": True},
                   "symbols": [], "files": [], "relations": [], "call_paths": [],
                   "tests": [], "docs": [], "excerpts": [], "citations": [],
                   "truncation_log": [{"stage": "gate", "rule": "abstain",
                                       "dropped": "delivery", "reason": dec["reason"]}],
                   "stats": {"candidates": len(ranked), "kept": 0,
                             "retrieved": len(ranked), "packing": packing}}
            out["payload_tokens"] = 1
            out["telemetry"] = {"retrieved": len(ranked), "delivered": 0,
                                "packing": packing, "delivered_files": [],
                                "payload_chars": 2, "payload_tokens": 1, "opened": 0,
                                "declared_relevant": None, "history_tokens": None,
                                "history_note": "historico/instrucoes nao incluidos",
                                "abstained": True, "abstain_reason": dec["reason"],
                                "uncertain": False}
            return out
    decls = None
    if packing == "expanded":
        decls = {}
        for (name, kind, f, line) in con.execute(
                "SELECT name, kind, file, line FROM symbols WHERE kind IN "
                "('class','interface','enum','method') ORDER BY file, line").fetchall():
            decls.setdefault(f, []).append((line, kind, name))
    packed = pack_ranked(ranked, disk, budget, policy=packing, decls=decls)
    focus_meta = {"focus_echo": None, "focus_terms": [], "omitted": 0, "pre_focus_kept": None}
    if focus:
        terms = focus_terms(focus)
        packed = apply_focus({**packed, "focus_terms": terms}, terms)
        focus_meta = {"focus_echo": focus, "focus_terms": terms,
                      "omitted": packed["omitted"], "pre_focus_kept": packed["pre_focus_kept"]}
    symbols, excerpts, citations, relations, log = (
        packed["symbols"], packed["excerpts"], packed["citations"],
        packed["relations"], packed["truncation_log"])
    used = packed["used"]
    files = sorted({s["file"] for s in symbols})
    out = {"capsule_version": "1.0", "query": query,
            "budget": {"requested": budget, "used": used, "tokenizer": "chars//4", "hard_enforced": True},
            "symbols": symbols, "files": files, "relations": relations, "call_paths": [],
            "tests": [], "docs": [], "excerpts": excerpts, "citations": citations,
            "truncation_log": log, "stats": {"candidates": len(ranked), "kept": len(symbols),
                                            "retrieved": len(ranked), "packing": packing}}
    # P2/E26-00: telemetria da fronteira de entrega (sem mudar ranking/seleção).
    # `used` segue soma de itens (compat); `payload_tokens` mede a serialização
    # inteira entregue. `opened`=leituras explícitas fora da cápsula (0 aqui);
    # histórico/instruções não entram neste número (nulos com motivo).
    blob_chars = len(__import__("json").dumps(
        {"excerpts": excerpts, "citations": citations,
         "symbols": [{"file": s.get("file"), "line": s.get("line"),
                      "kind": s.get("kind"), "name": s.get("name")} for s in symbols]},
        sort_keys=True, ensure_ascii=False))
    out["payload_tokens"] = payload_tokens_for_capsule(out)
    out["telemetry"] = {"retrieved": len(ranked), "delivered": len(symbols),
                        "packing": packing,
                        "delivered_files": files, "payload_chars": blob_chars,
                        "payload_tokens": out["payload_tokens"], "opened": 0,
                        "declared_relevant": None, "history_tokens": None,
                        "history_note": "historico/instrucoes nao incluidos; P3 medira custo total",
                        "abstained": False, "abstain_reason": gate["reason"],
                        "uncertain": gate["uncertain"],
                        "focus_echo": focus_meta["focus_echo"],
                        "focus_terms": focus_meta["focus_terms"],
                        "focus_omitted": focus_meta["omitted"],
                        "pre_focus_kept": focus_meta["pre_focus_kept"]}
    return out
