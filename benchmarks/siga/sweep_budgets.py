# SPDX-License-Identifier: Apache-2.0
"""Sweep F20: recall x budget (500-8k) nas 153Qs; indexa uma vez, reusa con."""
from __future__ import annotations
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from archatlas.capsule import build_capsule
from archatlas.config import dataset_root
from archatlas.lexical import rebuild_lexical
from archatlas.store import index_many, open_db

B = pathlib.Path(__file__).resolve().parent
BUDGETS = [500, 1000, 2000, 4000, 8000]


def gt_ok(q: dict, files: set[str]) -> bool:
    from archatlas.config import as_rel
    rel = {as_rel(f) for f in files}
    gt = q["gt"]
    if "files" in gt:
        return any(f in rel for f in gt["files"])
    if "edges" in gt:
        ok = any(e["file"] in rel for e in gt["edges"])
        return ok and (not gt.get("path_files") or any(f in rel for f in gt["path_files"]))
    if "package" in gt:
        return bool(gt.get("file") in rel or any(f.startswith(gt["package"]) for f in rel))
    return bool(gt.get("file")) and gt["file"] in rel


def main() -> int:
    ds = dataset_root()
    roots = []
    for rel in ("siga-ex/src/main/java", "siga-cp/src/main/java", "siga-wf/src/main/java"):
        roots += sorted((ds / rel).rglob("*.java"))
    con = open_db(pathlib.Path("/tmp/opencode/sweep.sqlite"))
    import os
    if os.path.exists("/tmp/opencode/sweep.sqlite"):
        os.remove("/tmp/opencode/sweep.sqlite")
        con = open_db(pathlib.Path("/tmp/opencode/sweep.sqlite"))
    index_many(con, roots, "e3be22828")
    rebuild_lexical(con)
    qs = json.loads((B / "queries_dev.json").read_text())
    curve = []
    for b in BUDGETS:
        hits, used, t0 = 0, 0, time.perf_counter()
        for q in qs:
            cap = build_capsule(con, q["query"], b)
            hits += gt_ok(q, set(cap["files"]))
            used += cap["budget"]["used"]
        curve.append({"budget": b, "recall": round(hits / len(qs), 4),
                      "avg_used": used // len(qs), "seconds": round(time.perf_counter() - t0, 1)})
    json.dump(curve, open(B / "curve_f20.json", "w"), indent=1)
    print(json.dumps(curve, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
