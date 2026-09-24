# SPDX-License-Identifier: Apache-2.0
"""Drill temporal BTC-P6 (sintético): t0 → t1 sem corpus real.

- `snapshot_facts(root)`: fatos-arquivo + fatos-`include` + Python-AST por arquivo,
  chaveados por caminho relativo (portável; sem absoluto versionado).
- `diff_snapshots(old, new)`: added/removed/changed/unchanged por `content_hash` +
  `invalidated` (arquivo alterado/removido + dependentes que o incluem pelo basename).
  Arquivos inalterados e não dependentes nunca entram em `invalidated` (sem retrabalho).
- `update_cost(diff, total)`: fração do corpus a reextrair. Puro e determinístico.
"""
from __future__ import annotations
import pathlib

from archatlas.bitcoin.cpp_lex import discover_cpp, extract_cpp_lexical
from archatlas.dataset import extract_py

CPP_EXTS = {".c", ".h", ".hpp", ".cpp"}


def snapshot_facts(root: pathlib.Path) -> dict:
    root = pathlib.Path(root)
    snap = {}
    for p in discover_cpp(root):
        rel = str(p.relative_to(root))
        snap[rel] = extract_cpp_lexical(p)["facts"]
    for p in sorted(root.rglob("*.py")):
        rel = str(p.relative_to(root))
        snap[rel] = extract_py(p)
    return snap


def _hashes(facts: list) -> str | None:
    for f in facts:
        if f.get("kind") == "file":
            return f["content_hash"]
    return facts[0]["content_hash"] if facts else None


def _includes_of(facts: list) -> set:
    return {f["name"].split("/")[-1] for f in facts if f.get("kind") == "include"}


def diff_snapshots(old: dict, new: dict) -> dict:
    old_files, new_files = set(old), set(new)
    added = sorted(new_files - old_files)
    removed = sorted(old_files - new_files)
    changed = sorted(f for f in old_files & new_files if _hashes(old[f]) != _hashes(new[f]))
    unchanged = sorted(f for f in old_files & new_files if _hashes(old[f]) == _hashes(new[f]))
    touched_names = {pathlib.Path(f).name for f in changed + removed}
    invalidated = sorted(set(changed + removed) | {
        f for f, facts in new.items()
        if f not in changed and touched_names & _includes_of(facts)})
    return {"added": added, "removed": removed, "changed": changed,
            "unchanged": unchanged, "invalidated": invalidated}


def update_cost(diff: dict, total: int) -> dict:
    n = len(diff["invalidated"])
    return {"reextract": n, "total": total,
            "fraction": (n / total) if total else 0.0}
