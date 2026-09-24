# SPDX-License-Identifier: Apache-2.0
"""E26-02 no corpus: empacotamento por spans sobre conjuntos entregues (sem modelo).

Para cada tarefa, os arquivos entregues pelo braço C viram candidatos de linha
(ocorrências dos tokens da query, até `per_file` por arquivo); as 3 políticas
`btc-pack/1` competem sob mesmo ranking/budget. Pares header/impl via `header_pairs`
sobre fatos-`include` dos entregues. Puro e determinístico (stdlib-only).
"""
from __future__ import annotations
import pathlib
import re

from archatlas.bitcoin.cpp_lex import INCLUDE_RE, extract_cpp_lexical
from archatlas.bitcoin.packing import header_pairs, pack_candidates

POLICIES = ("one_per_file", "multi", "expanded")


def candidates_for_task(root: pathlib.Path, delivered: list, query: str,
                        per_file: int = 3) -> list[dict]:
    """Candidatos ordenados (ordem dos entregues preservada). Só lê bytes."""
    root = pathlib.Path(root)
    toks = [t.lower() for t in query.split()]
    ranked = []
    for rel in delivered:
        p = root / rel
        if not p.is_file():
            continue
        lines = p.read_bytes().decode("utf-8", errors="replace").splitlines()
        kept = 0
        for i, text in enumerate(lines, start=1):
            if kept >= per_file:
                break
            low = text.lower()
            hit = next((t for t in toks if t in low), None)
            if hit is None:
                continue
            m = INCLUDE_RE.search(text)
            if m and m.group(2) in text:
                ranked.append({"file": rel, "line": i, "kind": "include",
                               "name": m.group(2), "provenance": "lexical-verified",
                               "confidence": 0.6})
            else:
                at = low.find(hit)
                name = text[at:at + len(hit)]
                ranked.append({"file": rel, "line": i, "kind": "ref", "name": name,
                               "provenance": "text-match-verified", "confidence": 0.7})
            kept += 1
    return ranked


def run_packing(root: pathlib.Path, tasks: list, delivered_by_task: dict,
                budget: int = 2000) -> list[dict]:
    """Uma linha por (tarefa, política) com cobertura do ouro em nível de arquivo."""
    root = pathlib.Path(root)
    rows = []
    for task in tasks:
        if task.get("type") == "negative":
            continue
        tid = task["id"]
        gt = [f for f in task["expected_dev_files"] if f not in task.get("given_files", [])]
        ranked = candidates_for_task(root, delivered_by_task.get(tid, []), task["query"])
        disk = {}
        for rel in {c["file"] for c in ranked}:
            p = root / rel
            if p.is_file():
                disk[rel] = p.read_bytes().decode("utf-8", errors="replace").splitlines()
        facts = {}
        for rel in disk:
            if pathlib.Path(rel).suffix in {".c", ".h", ".hpp", ".cpp"}:
                facts[rel] = extract_cpp_lexical(root / rel)["facts"]
        pairs = header_pairs(facts)
        for pol in POLICIES:
            out = pack_candidates(ranked, disk, budget, pol, pairs)
            covered = sorted({e["file"] for e in out["excerpts"]} & set(gt))
            rows.append({"task_id": tid, "policy": pol, "budget": budget,
                         "candidates": len(ranked), "used": out["used"],
                         "excerpts": len(out["excerpts"]), "files": len(out["files"]),
                         "pairs_complete": out["pairs_complete"], "dropped": out["dropped"],
                         "gt_covered": covered,
                         "gt_all": sorted(covered) == sorted(gt) and bool(gt)})
    return rows
