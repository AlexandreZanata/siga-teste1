# SPDX-License-Identifier: Apache-2.0
"""P4/E26-02: políticas de empacotamento (mesmo ranking, só packing varia).

Três políticas sobre a MESMA lista ranqueada (ordem preservada):
- `one_per_file`: no máximo um trecho por arquivo.
- `multi`: múltiplos trechos não redundantes (comportamento F5 atual).
- `expanded`: multi + linha de declaração englobante (aproximação da unidade
  de código/contrato: declaração + uso; NÃO é extração de unidade completa —
  sem parser novo; ver limite abaixo).

Regras comuns (E26-02): deduplicação de spans idênticos nas três; mesmos
gates da cápsula (ilegível / nome-ausente p/ classe / over_budget com log);
mesmo budget e mesma contagem `chars//4`; ids determinísticos (`e{i}`,
decl-contexto `e{i}d`); sem acesso a índice/disco além dos args (puro).

Limite honesto: `expanded` usa declarações da tabela `symbols`
(class/interface/enum/method) + texto do disco; não resolve overloads, DI,
macros ou unidades multi-bloco. Efeito medido só no recuperador da cápsula;
BM25/estrutural puros ficam para repetição futura (sem presunção).
"""
from __future__ import annotations


def _count(text: str) -> int:
    return max(1, len(text) // 4)  # mesmo tokenizer chars//4 da cápsula


def pack_ranked(ranked: list[dict], disk: dict[str, list[str]], budget: int,
                policy: str = "multi",
                decls: dict[str, list[tuple]] | None = None) -> dict:
    assert policy in ("one_per_file", "multi", "expanded")
    symbols, excerpts, citations, relations, log = [], [], [], [], []
    kept_keys, kept_files, used = set(), set(), 0

    def _keep(c: dict, i: int, line_text: str, reason: str, eid: str) -> None:
        nonlocal used
        item = f"{c['file']}:{c['line']} {c['kind']} {c['name']} :: {line_text}"
        cost = _count(item)
        if used + cost > budget:
            log.append({"stage": "pack", "rule": "over_budget", "dropped": c["name"],
                        "reason": f"+{cost} > {budget - used}"})
            return False
        symbols.append({**c, "reason": reason, "score": round(float(-c.get("bm25", 0)), 4)})
        excerpts.append({"id": eid, "file": c["file"], "start_line": c["line"],
                         "end_line": c["line"], "tokens": cost, "truncated": False,
                         "text": line_text, "anchors": [c["name"]]})
        citations.append({"excerpt_id": eid, "file": c["file"], "line": c["line"],
                          "symbol": c["name"]})
        rel_kind = "REFERENCES" if c.get("kind") == "ref" else "DEFINES"
        relations.append({"from": c["file"], "to": c["name"], "kind": rel_kind,
                          "provenance": c["provenance"], "score": 1.0})
        used += cost
        kept_keys.add((c["file"], c["line"]))
        kept_files.add(c["file"])
        return True

    for i, c in enumerate(ranked):
        if (c["file"], c["line"]) in kept_keys:
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
        if c["name"] not in line_text and c["kind"] in ("class", "interface", "enum"):
            log.append({"stage": "select", "rule": "name-absent", "dropped": c["name"],
                        "reason": c["file"]})
            continue
        if not _keep(c, i, line_text, f"bm25 rank {i}", f"e{i}"):
            continue
        if policy == "expanded" and decls:
            d = _enclosing_decl(decls.get(c["file"], []), c["line"])
            if d and (c["file"], d[0]) not in kept_keys:
                dl = disk.get(c["file"], [])
                if 1 <= d[0] <= len(dl):
                    dtxt = dl[d[0] - 1].strip()[:200]
                    if d[2] in dtxt:
                        _keep({"name": d[2], "kind": d[1], "file": c["file"],
                               "line": d[0], "provenance": "decl-context",
                               "confidence": 0.9, "bm25": c.get("bm25", 0)},
                              i, dtxt, f"decl-context rank {i}", f"e{i}d")
    return {"symbols": symbols, "excerpts": excerpts, "citations": citations,
            "relations": relations, "truncation_log": log, "used": used}


def _enclosing_decl(decl_list: list[tuple], line: int) -> tuple | None:
    """Maior declaração com `decl_line <= line` (aproximação, sem parser)."""
    best = None
    for (dl, kind, name) in decl_list:
        if dl <= line and (best is None or dl > best[0]):
            best = (dl, kind, name)
    return best


def focus_terms(focus: str) -> list[str]:
    """Termos do foco: alfanuméricos len>2, minúsculos, ordenados. Determinístico."""
    import re as _re
    return sorted({t.lower() for t in _re.findall(r"[A-Za-z0-9_]+", focus or "") if len(t) > 2})


def apply_focus(packed: dict, terms: list[str]) -> dict:
    """E26-04: poda determinística pós-montagem (mesmos candidatos, só seleção varia).

    Mantém trecho sse casa algum termo (nome/texto, case-insensitive) OU é
    esqueleto estrutural (class/interface/enum) — contratos nunca somem sem
    registro. O restante vira `truncation_log` (`focus-prune`) + contadores;
    originais preservados na contagem `pre_focus_kept`; excerto podado jamais
    se apresenta como arquivo integral (spans com file/line intactos).
    """
    keep_ex, keep_ids = [], set()
    for e in packed["excerpts"]:
        txt = f"{e.get('text', '')} {' '.join(e.get('anchors', []))}".lower()
        sym = next((s for s in packed["symbols"]
                    if s["file"] == e["file"] and s["line"] == e["start_line"]), {})
        if any(t in txt for t in terms) or sym.get("kind") in ("class", "interface", "enum"):
            keep_ex.append(e)
            keep_ids.add(e["id"])
    kept_names = {(s["file"], s["line"]) for s in packed["symbols"]
                  if any(e["id"] in keep_ids and e["file"] == s["file"]
                         and e["start_line"] == s["line"] for e in keep_ex)}
    symbols = [s for s in packed["symbols"] if (s["file"], s["line"]) in kept_names]
    citations = [c for c in packed["citations"] if c["excerpt_id"] in keep_ids]
    names = {s["name"] for s in symbols}
    relations = [r for r in packed["relations"] if r["to"] in names]
    log = list(packed["truncation_log"]) + [
        {"stage": "focus", "rule": "focus-prune", "dropped": e["id"],
         "reason": f"termos={','.join(terms) or '-'} {e['file']}:{e['start_line']}"}
        for e in packed["excerpts"] if e["id"] not in keep_ids]
    used = sum(e["tokens"] for e in keep_ex)
    return {"symbols": symbols, "excerpts": keep_ex, "citations": citations,
            "relations": relations, "truncation_log": log, "used": used,
            "omitted": len(packed["excerpts"]) - len(keep_ex),
            "pre_focus_kept": len(packed["excerpts"]), "focus_terms": terms}
