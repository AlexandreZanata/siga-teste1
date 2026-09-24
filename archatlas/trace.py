# SPDX-License-Identifier: Apache-2.0
"""Trace multi-hop F16: BFS sobre arestas calls verificadas (candidate 0.6, nunca inventado)."""
from __future__ import annotations
import pathlib
from collections import deque

from archatlas.calls import extract_calls


def build_call_index(files: list[pathlib.Path]) -> dict[str, list[dict]]:
    idx: dict[str, list[dict]] = {}
    for f in files:
        for c in extract_calls(f):
            idx.setdefault(c["caller"], []).append(c)
    return idx


def trace(idx: dict[str, list[dict]], src: str, dst: str, depth: int = 4) -> list[dict] | None:
    seen = {src}
    q: deque = deque([(src, [])])
    while q:
        node, path = q.popleft()
        if node == dst and path:
            return path
        if len(path) >= depth:
            continue
        for e in idx.get(node, []):
            if e["callee"] not in seen:
                seen.add(e["callee"])
                q.append((e["callee"], path + [e]))
    return None
