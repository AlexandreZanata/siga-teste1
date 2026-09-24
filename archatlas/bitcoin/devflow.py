# SPDX-License-Identifier: Apache-2.0
"""Jornada do desenvolvedor BTC-E26-06 (ensaio offline sobre repo sintético).

Fluxo: doctor → index → context → expand → edit (checkout isolado) → validate →
update → uninstall. Tudo sob diretório de trabalho explícito (tmp); o repo original
nunca é modificado. Estados: `ok`, `partial`, `stale`, `unsupported`.
Reuso (só leitura): `cpp_lex`, `packing`, `temporal`, `extract_py`, `verify_fact`.
"""
from __future__ import annotations
import ast
import hashlib
import pathlib
import shutil

from archatlas.bitcoin.cpp_lex import file_record, verify_fact
from archatlas.bitcoin.packing import header_pairs, pack_candidates
from archatlas.bitcoin.temporal import diff_snapshots, snapshot_facts, update_cost

SUPPORTED = {".c", ".h", ".hpp", ".cpp", ".py"}


def doctor(root: pathlib.Path) -> dict:
    root = pathlib.Path(root)
    if not root.is_dir():
        return {"state": "stale", "reason": "raiz inexistente"}
    other = sorted({p.suffix for p in root.rglob("*") if p.is_file()} - SUPPORTED - {""})
    diags = [f"extensão sem suporte declarado: {s} (diagnóstico, sem resultado vazio enganoso)"
             for s in other]
    return {"state": "partial" if diags else "ok", "root": str(root),
            "support": {"cpp": "lexical (includes)", "python": "ast", "outras": "unsupported"},
            "diagnostics": diags,
            "limitations": ["sem resolução semântica C++", "sem build/index do corpus"]}


def index_repo(root: pathlib.Path) -> dict:
    snap = snapshot_facts(root)
    return {"state": "ok", "files": len(snap),
            "facts": sum(len(v) for v in snap.values()), "index": snap}


def context_query(root: pathlib.Path, index: dict, query: str, budget: int = 2000) -> dict:
    root = pathlib.Path(root)
    toks = [t.lower() for t in query.split()]
    ranked = []
    for f, facts in index["index"].items():
        for fact in facts:
            if fact.get("kind") == "file":
                continue
            if any(tok in fact["name"].lower() for tok in toks):
                ranked.append({"file": f, "line": fact["line"], "kind": fact["kind"],
                               "name": fact["name"],
                               "provenance": fact.get("provenance", "?"),
                               "confidence": fact.get("confidence", 0.0)})
    disk = {}
    for f in index["index"]:
        p = root / f
        if p.is_file():
            disk[f] = p.read_bytes().decode("utf-8", errors="replace").splitlines()
    out = pack_candidates(ranked, disk, budget, "expanded", header_pairs(index["index"]))
    gaps = [t for t in toks if not any(t in (e["text"] + e["file"]).lower()
                                       for e in out["excerpts"])]
    return {"state": "ok" if out["excerpts"] else "partial", "ranked": len(ranked),
            "out": out, "gaps": gaps}


def expand_evidence(root: pathlib.Path, file: str, line: int, window: int = 3) -> dict:
    p = pathlib.Path(root) / file
    if not p.exists():
        return {"state": "stale", "reason": f"fonte ausente: {file}"}
    raw = p.read_bytes()
    lines = raw.decode("utf-8", errors="replace").splitlines()
    if not (1 <= line <= len(lines)):
        return {"state": "stale", "reason": f"linha fora do intervalo: {file}:{line}"}
    lo, hi = max(1, line - window), min(len(lines), line + window)
    return {"state": "ok", "file": file, "span": [lo, hi],
            "text": "\n".join(lines[lo - 1:hi]),
            "content_hash": hashlib.sha256(raw).hexdigest()}


def edit_task(root: pathlib.Path, work: pathlib.Path, rel: str, new_bytes: bytes) -> dict:
    src = pathlib.Path(root) / rel
    before = hashlib.sha256(src.read_bytes()).hexdigest()
    co = pathlib.Path(work) / "task-checkout" / rel
    co.parent.mkdir(parents=True, exist_ok=True)
    co.write_bytes(src.read_bytes() + new_bytes)  # edição só na cópia isolada
    after = hashlib.sha256(src.read_bytes()).hexdigest()
    assert before == after, "original jamais é modificado"
    return {"state": "ok", "checkout": str(co), "original_untouched": before == after}


def validate_checkout(path: str) -> dict:
    p = pathlib.Path(path)
    checks = []
    rec = file_record(p)
    ok, msg = verify_fact(rec)
    checks.append({"check": "integridade", "ok": ok, "msg": msg})
    if p.suffix == ".py":
        try:
            ast.parse(p.read_bytes().decode("utf-8", errors="replace"))
            checks.append({"check": "sintaxe-python", "ok": True, "msg": "ast.parse ok"})
        except SyntaxError as e:
            checks.append({"check": "sintaxe-python", "ok": False, "msg": str(e)})
    else:
        checks.append({"check": "sintaxe-cpp", "ok": None,
                       "msg": "sem parser C++; revisão humana/build exigidos"})
    state = "ok" if all(c["ok"] for c in checks if c["ok"] is not None) else "partial"
    return {"state": state, "checks": checks}


def update_index(old_snap: dict, root: pathlib.Path) -> dict:
    new_snap = snapshot_facts(root)
    diff = diff_snapshots(old_snap, new_snap)
    cost = update_cost(diff, len(new_snap))
    return {"state": "ok", "added": diff["added"], "removed": diff["removed"],
            "changed": diff["changed"], "invalidated": diff["invalidated"],
            "cost": cost}


def uninstall(work: pathlib.Path) -> dict:
    work = pathlib.Path(work)
    shutil.rmtree(work, ignore_errors=True)
    return {"state": "ok" if not work.exists() else "stale", "removed": not work.exists()}
