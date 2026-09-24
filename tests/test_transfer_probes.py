# SPDX-License-Identifier: Apache-2.0
"""P6 fixtures dev: 20 sondas localização, ouro em bytes, sem tarefas/holdout."""
import json
import pathlib

import pytest

PROBES = pathlib.Path("benchmarks/transfer/dev_probes.json")
T1 = pathlib.Path("/tmp/opencode-p6/t1")
T2 = pathlib.Path("/tmp/opencode-p6/t2")
clones_here = T1.is_dir() and T2.is_dir()
ROOTS = {"T1": T1, "T2": T2}


def test_probes_schema_no_tasks_no_holdout():
    probes = json.loads(PROBES.read_text(encoding="utf-8"))
    assert len(probes) == 20
    ids = [p["id"] for p in probes]
    assert sorted(ids) == [f"T1-{i:03d}" for i in range(1, 11)] + \
        [f"T2-{i:03d}" for i in range(1, 11)]
    blob = PROBES.read_text(encoding="utf-8")
    assert "holdout final" not in blob and "@@" not in blob
    for p in probes:
        assert {"id", "target", "query", "symbol", "file"} <= set(p)
        assert p["symbol"] in p["query"]  # localização: símbolo nomeado...
        assert p["file"].split("/")[-1] not in p["query"]  # ...arquivo, nunca


@pytest.mark.skipif(not clones_here, reason="clones /tmp/opencode-p6 ausentes: só schema")
def test_gold_bytes_in_pinned_checkouts():
    probes = json.loads(PROBES.read_text(encoding="utf-8"))
    for p in probes:
        raw = (ROOTS[p["target"]] / p["file"]).read_bytes()
        assert p["symbol"] in raw.decode("utf-8", errors="replace"), p["id"]


def test_probes_run_replay():
    """Replay puro da rodada commitada (sem clones, sem índice)."""
    from archatlas.telemetry import score_delivery
    probes = {p["id"]: p["file"] for p in json.loads(PROBES.read_text(encoding="utf-8"))}
    runs = [json.loads(l) for l in
            pathlib.Path("experiments/transfer/probes_001/runs.jsonl").read_text(encoding="utf-8").splitlines()]
    mans = [json.loads(l) for l in
            pathlib.Path("experiments/transfer/probes_001/manifest.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(runs) == 40 and len(mans) == 40
    assert {(r["case_id"], r["condition"]) for r in runs} == \
        {(p["id"], a) for p in json.loads(PROBES.read_text(encoding="utf-8")) for a in ("LEX", "CAPSULE")}
    t2cap = [r for r in runs if r["target"] == "T2" and r["condition"] == "CAPSULE"]
    assert sum(r["hit"] for r in t2cap) == 10  # T2 perfeita com cápsula
    for r in runs:
        sc = score_delivery(set(r["delivered"]), {"file": probes[r["case_id"]]})
        assert sc["hit"] == r["hit"] and sc["recall_set"] == r["recall_set"]
        assert r["patch_accepted"] is None
