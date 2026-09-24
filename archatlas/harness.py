# SPDX-License-Identifier: Apache-2.0
"""Harness F7+P2: indexa, roda queries_dev.json com tempo/query, escreve JSONL. `hit` legado = algum esperado; `recall_set`/`precision_set` (telemetry) = métricas completas."""
from __future__ import annotations
from archatlas.config import REPO_ROOT, dataset_root
import json
import pathlib
import sqlite3
import time

from archatlas.capsule import build_capsule
from archatlas.config import as_rel
from archatlas.lexical import rebuild_lexical
from archatlas.store import index_many, open_db
from archatlas.telemetry import score_delivery

SHA = "e3be22828f787cbe71b339aecb7a7bf569099803"


def run(dev_json: pathlib.Path, db: pathlib.Path, out_jsonl: pathlib.Path, budget: int = 2000) -> dict:
    qs = json.loads(dev_json.read_text(encoding="utf-8"))
    ds = dataset_root()
    files = []
    # P4-infra(b): main + test como fontes recuperáveis (E26-01 achado 1).
    # Limite declarado: mesmo extrator/kinds, sem distinção main-vs-test no ranking.
    for rel in ("siga-ex/src/main/java", "siga-cp/src/main/java", "siga-wf/src/main/java",
                "siga-ex/src/test/java", "siga-cp/src/test"):
        d = ds / rel
        if d.is_dir():
            files += sorted(d.rglob("*.java"))
    con = open_db(db)
    t0 = time.perf_counter()
    counts = index_many(con, files, SHA)
    rebuild_lexical(con)
    index_s = time.perf_counter() - t0
    hits, total_s, dts = 0, 0.0, []
    rs_sum, rs_n, ps_sum, ps_n, errors = 0.0, 0, 0.0, 0, []
    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with open(out_jsonl, "w", encoding="utf-8") as fh:
        for q in qs:
            try:
                s = time.perf_counter()
                cap = build_capsule(con, q["query"], budget)
                dt = time.perf_counter() - s
                total_s += dt
                dts.append(dt)
                gt = q["gt"]
                # Executor: só índice+disco via build_capsule. Avaliador abaixo
                # recebe só (delivered, gt) — nunca `con` (isolamento P2).
                delivered = {as_rel(f) for f in cap["files"]}
                sc = score_delivery(delivered, gt)
                ok = bool(sc["hit"])
                hits += ok
                if sc["recall_set"] is not None:
                    rs_sum += sc["recall_set"]
                    rs_n += 1
                if sc["precision_set"] is not None:
                    ps_sum += sc["precision_set"]
                    ps_n += 1
                tel = cap.get("telemetry", {})
                fh.write(json.dumps({"id": q["id"], "cat": q["category"], "budget": budget,
                                     "hit": ok, "recall_set": sc["recall_set"],
                                     "precision_set": sc["precision_set"],
                                     "seconds": round(dt, 4), "used": cap["budget"]["used"],
                                     "payload_tokens": tel.get("payload_tokens"),
                                     "delivered": tel.get("delivered", cap["stats"]["kept"]),
                                     "kept": cap["stats"]["kept"], "sha": SHA},
                                    ensure_ascii=False) + "\n")
            except Exception as e:  # P2: registra erro, nunca aborta o lote
                errors.append({"id": q.get("id"), "error": f"{type(e).__name__}: {e}"})
                fh.write(json.dumps({"id": q.get("id"), "cat": q.get("category"),
                                     "budget": budget, "hit": False, "recall_set": 0.0,
                                     "precision_set": 0.0, "seconds": -1.0, "used": 0,
                                     "payload_tokens": None, "delivered": 0,
                                     "kept": 0, "sha": SHA, "error": "harness-catch"},
                                    ensure_ascii=False) + "\n")
    import statistics as _st
    dts.sort()
    p = lambda q: round(dts[min(len(dts) - 1, int(q * len(dts)))], 4)
    return {"n": len(qs), "recall": hits / len(qs), "hit_rate": hits / len(qs),
            "recall_set_mean": (rs_sum / rs_n if rs_n else None),
            "precision_set_mean": (ps_sum / ps_n if ps_n else None),
            "errors": errors,
            "manifest": {"sha": SHA, "budget": budget, "tokenizer": "chars//4",
                         "executor": "archatlas.capsule.build_capsule",
                         "evaluator": "archatlas.telemetry.score_delivery"},
            "index_seconds": round(index_s, 2),
            "mean_query_s": round(total_s / len(qs), 4), "p50_query_s": p(0.5),
            "p95_query_s": p(0.95), "counts": counts}
