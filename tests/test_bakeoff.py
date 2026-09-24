# SPDX-License-Identifier: Apache-2.0
"""F13: bake-off mede recall+tempo das 5 condições nas 100Qs; roteador >= melhor isolada."""
import json
import pathlib
import time

from archatlas.lexical import rebuild_lexical
from archatlas.store import index_many, open_db
from archatlas.strategies import STRATEGIES

DEV = pathlib.Path("benchmarks/siga/queries_dev.json")
SHA = "e3be22828f787cbe71b339aecb7a7bf569099803"


def gt_match(q: dict, files: set[str]) -> bool:
    gt = q["gt"]
    if "files" in gt:
        return any(f in files for f in gt["files"])
    if "package" in gt:
        return bool(gt.get("file") in files or any(f.startswith(gt["package"]) for f in files))
    return bool(gt.get("file")) and gt["file"] in files


def test_bakeoff(tmp_path):
    ds = pathlib.Path("/home/iiii/PESSOAL-PROJETOS-ALEXANDRE/siga")
    roots = sorted((ds / "siga-ex/src/main/java").rglob("*.java"))[:40]
    con = open_db(tmp_path / "b.sqlite")
    index_many(con, roots, SHA)
    rebuild_lexical(con)
    qs = json.loads(DEV.read_text(encoding="utf-8"))
    rep: dict = {}
    for name, fn in STRATEGIES.items():
        hits, dt = 0, 0.0
        per: dict = {}
        for q in qs:
            s = time.perf_counter()
            files = fn(con, q["query"])
            dt += time.perf_counter() - s
            ok = gt_match(q, files)
            hits += ok
            per.setdefault(q["category"], [0, 0])
            per[q["category"]][ok] += 1
        rep[name] = {"recall": round(hits / len(qs), 3), "mean_s": round(dt / len(qs), 4),
                     "by_cat": {k: round(v[True] / sum(v), 3) for k, v in sorted(per.items())}}
    (tmp_path / "bakeoff.json").write_text(json.dumps(rep, indent=1))
    print("\n" + json.dumps(rep, indent=1))
    best_single = max(rep[n]["recall"] for n in ("lexical", "structural", "hybrid", "hybrid_refs"))
    assert rep["router"]["recall"] >= best_single
    assert rep["router"]["recall"] >= 0.99
