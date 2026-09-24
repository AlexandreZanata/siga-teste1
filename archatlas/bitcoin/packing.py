# SPDX-License-Identifier: Apache-2.0
"""Empacotamento experimental Bitcoin (`btc-pack/1`). Variante local, não fork do core.

Três políticas sobre a MESMA lista ranqueada e o MESMO budget (E26-02 espelho):
- `one_per_file`: no máximo um trecho por arquivo.
- `multi`: múltiplos trechos não redundantes do mesmo arquivo.
- `expanded`: multi + contraparte do par header/implementação como contexto
  (par derivado de fatos-`include` do adaptador; sem resolução semântica).

Regras comuns: deduplicação de spans idênticos nas três; gates `unreadable`,
`name-absent` e `over_budget` com log; tokenizer `chars//4`; ids `b{i}` e
contexto de par `b{i}p`; função pura (sem índice/disco além dos args).
"""
from __future__ import annotations
import pathlib


def _count(text: str) -> int:
    return max(1, len(text) // 4)


def header_pairs(facts_by_file: dict) -> dict:
    """Pares header/implementação a partir de fatos-`include` (mesmo radical).

    `facts_by_file`: {arquivo: [fatos]}. Retorna {arquivo: contraparte}.
    Só afirma correspondência textual de nomes, nunca vínculo semântico.
    """
    by_name = {}
    for f, facts in facts_by_file.items():
        by_name.setdefault(pathlib.Path(f).name, f)
    pairs = {}
    for f, facts in facts_by_file.items():
        stem = pathlib.Path(f).stem
        for fact in facts:
            if fact.get("kind") != "include":
                continue
            target = fact["name"].split("/")[-1]
            if pathlib.Path(target).stem == stem and target in by_name:
                mate = by_name[target]
                if mate != f:
                    pairs[f] = mate
    for f, mate in list(pairs.items()):
        pairs.setdefault(mate, f)
    return pairs


def pack_candidates(ranked: list[dict], disk: dict, budget: int, policy: str = "multi",
                    pairs: dict | None = None) -> dict:
    assert policy in ("one_per_file", "multi", "expanded")
    pairs = pairs or {}
    excerpts, citations, log = [], [], []
    kept_spans, kept_files, used = set(), set(), 0

    def _keep(c: dict, line_text: str, eid: str) -> bool:
        nonlocal used
        item = f"{c['file']}:{c['line']} {c['kind']} {c['name']} :: {line_text}"
        cost = _count(item)
        if used + cost > budget:
            log.append({"stage": "pack", "rule": "over_budget", "dropped": c["name"],
                        "reason": f"+{cost} > {budget - used}"})
            return False
        excerpts.append({"id": eid, "file": c["file"], "start_line": c["line"],
                         "end_line": c["line"], "tokens": cost, "truncated": False,
                         "text": line_text, "anchors": [c["name"]]})
        citations.append({"excerpt_id": eid, "file": c["file"], "line": c["line"],
                          "symbol": c["name"]})
        used += cost
        kept_spans.add((c["file"], c["line"]))
        kept_files.add(c["file"])
        return True

    for i, c in enumerate(ranked):
        if (c["file"], c["line"]) in kept_spans:
            log.append({"stage": "pack", "rule": "duplicate-span", "dropped": c["name"],
                        "reason": c["file"]})
            continue
        if policy == "one_per_file" and c["file"] in kept_files:
            log.append({"stage": "pack", "rule": "one-per-file", "dropped": c["name"],
                        "reason": c["file"]})
            continue
        lines = disk.get(c["file"])
        try:
            line_text = lines[c["line"] - 1].strip()[:200]
        except (TypeError, IndexError):
            log.append({"stage": "select", "rule": "unreadable", "dropped": c["name"],
                        "reason": c["file"]})
            continue
        if not line_text or (c["kind"] == "include" and c["name"] not in line_text):
            log.append({"stage": "select", "rule": "name-absent", "dropped": c["name"],
                        "reason": c["file"]})
            continue
        if not _keep(c, line_text, f"b{i}"):
            continue
        if policy == "expanded":
            mate = pairs.get(c["file"])
            if mate and mate not in kept_files:
                mlines = disk.get(mate, [])
                if mlines and (mate, 1) not in kept_spans:
                    mtxt = mlines[0].strip()[:200]
                    if mtxt:
                        _keep({"name": pathlib.Path(mate).name, "kind": "pair-context",
                               "file": mate, "line": 1, "provenance": "pair-context",
                               "confidence": 0.5}, mtxt, f"b{i}p")
    files = sorted(kept_files)
    pair_hits = sum(1 for f, m in pairs.items() if f in kept_files and m in kept_files) // 2
    return {"policy": "btc-pack/1+" + policy, "excerpts": excerpts, "citations": citations,
            "truncation_log": log, "used": used, "files": files,
            "pairs_complete": pair_hits,
            "dropped": len(log)}
