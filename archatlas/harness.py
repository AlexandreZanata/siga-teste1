# SPDX-License-Identifier: Apache-2.0
"""Harness F7: indexa, roda queries_dev.json com tempo/query, escreve JSONL. Recall = GT presente na cápsula."""
from __future__ import annotations
import json
import pathlib
import sqlite3
import time

from archatlas.capsule import build_capsule
from archatlas.lexical import rebuild_lexical
from archatlas.store import index_many, open_db

SHA = "e3be22828f787cbe71b339aecb7a7bf569099803"


def run(dev_json: pathlib.Path, db: pathlib.Path, out_jsonl: pathlib.Path, budget: int = 2000) -> dict:
    qs = json.loads(dev_json.read_text(encoding="utf-8"))
    ds = pathlib.Path("/home/iiii/PESSOAL-PROJETOS-ALEXANDRE/siga")
    files = sorted((ds / "siga-ex/src/main/java").rglob("*.java"))[:40]
    con = open_db(db)
    t0 = time.perf_counter()
    counts = index_many(con, files, SHA)
    rebuild_lexical(con)
    index_s = time.perf_counter() - t0
    hits, total_s, dts = 0, 0.0, []
    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with open(out_jsonl, "w", encoding="utf-8") as fh:
        for q in qs:
            s = time.perf_counter()
            cap = build_capsule(con, q["query"], budget)
            dt = time.perf_counter() - s
            total_s += dt
            dts.append(dt)
            gt = q["gt"]
            files = set(cap["files"])
            if "files" in gt:
                ok = any(f in files for f in gt["files"])
            elif "edges" in gt:
                ok = any(e["file"] in files for e in gt["edges"])
            elif "package" in gt:
                ok = bool(gt.get("file") in files or any(f.startswith(gt["package"]) for f in files))
            else:
                ok = bool(gt.get("file")) and gt["file"] in files
            hits += ok
            fh.write(json.dumps({"id": q["id"], "cat": q["category"], "budget": budget,
                                 "hit": ok, "seconds": round(dt, 4), "used": cap["budget"]["used"],
                                 "kept": cap["stats"]["kept"], "sha": SHA}, ensure_ascii=False) + "\n")
    import statistics as _st
    dts.sort()
    p = lambda q: round(dts[min(len(dts) - 1, int(q * len(dts)))], 4)
    return {"n": len(qs), "recall": hits / len(qs), "index_seconds": round(index_s, 2),
            "mean_query_s": round(total_s / len(qs), 4), "p50_query_s": p(0.5),
            "p95_query_s": p(0.95), "counts": counts}
