# SPDX-License-Identifier: Apache-2.0
"""BTC-P3 dryrun: tarefas próprias + protocolo A/B/C pareado, sem modelo, sem dataset."""
import inspect
import json
import pathlib

from archatlas.telemetry import rescore_runs, score_delivery

TASKS = pathlib.Path("benchmarks/bitcoin/pilot_p3_dev.json")
RUNS = pathlib.Path("experiments/bitcoin/pilot_p3/btc-pilot-dryrun-001/runs.jsonl")
MANS = pathlib.Path("experiments/bitcoin/pilot_p3/btc-pilot-dryrun-001/manifest.jsonl")
REPORT = pathlib.Path("experiments/bitcoin/pilot_p3/btc-pilot-dryrun-001/REPORT.md")


def _load():
    tasks = json.loads(TASKS.read_text(encoding="utf-8"))
    runs = [json.loads(l) for l in RUNS.read_text(encoding="utf-8").splitlines()]
    mans = [json.loads(l) for l in MANS.read_text(encoding="utf-8").splitlines()]
    return tasks, runs, mans


def test_tasks_valid_and_without_solutions():
    tasks = json.loads(TASKS.read_text(encoding="utf-8"))
    assert len(tasks) == 12
    assert sorted(t["id"] for t in tasks) == [f"BTC-P3D-{i:03d}" for i in range(1, 13)]
    fams = [t["family"] for t in tasks]
    assert (fams.count("rpc"), fams.count("validation"), fams.count("wallet"),
            fams.count("network"), fams.count("tests")) == (3, 3, 2, 2, 2)
    scopes = [t["scope"] for t in tasks]
    assert "local" in scopes and "cross" in scopes
    for t in tasks:
        assert {"problema", "query", "snapshot_base", "snapshot_note", "expected_dev_files",
                "public_check", "hidden_criteria", "timeout_s", "budget_capsule"} <= set(t)
        assert t["snapshot_base"] is None and "BTC_SHA" in t["snapshot_note"]
        assert t["timeout_s"] >= 60 and t["budget_capsule"] == 2000
        assert len(t["expected_dev_files"]) >= 2 and t["hidden_criteria"].startswith("oculto:BTC-P3D-")
    blob = TASKS.read_text(encoding="utf-8")
    assert "@@" not in blob and "diff --git" not in blob  # sem solução embutida


def test_protocol_paired_budgeted_isolated_with_one_loud_error():
    tasks, runs, mans = _load()
    assert len(runs) == 72 and len(mans) == 72
    assert {(r["task_id"], r["condition"], r["repetition"]) for r in runs} == \
        {(t["id"], c, rep) for t in tasks for c in ("A_busca", "B_freq", "C_adapter") for rep in (1, 2)}
    assert sorted(r["order"] for r in runs) == list(range(1, 73))
    errs = [r for r in runs if r["error"]]
    assert len(errs) == 1
    assert (errs[0]["task_id"], errs[0]["condition"], errs[0]["repetition"]) == ("BTC-P3D-007", "B_freq", 2)
    assert "sintética injetada" in errs[0]["error"] and errs[0]["hit"] is False
    for r in runs:
        assert r["sha"] == "e6fde134f7da0d3616d90c40232d9ebe2ed9f033" and r["tokenizer"] == "chars//4"
        assert r["budget"] == 2000 and r["used"] <= 2000
        assert r["patch_accepted"] is None and "sem modelo" in r["patch_note"]
        assert r["cost_total"] is None and "sem telemetria" in r["cost_note"]
        if not r["error"]:
            assert r["payload_tokens"] is not None and r["payload_tokens"] >= r["used"]
    for m in mans:
        assert {"task_id", "condition", "repetition", "order", "budget", "sha", "tokenizer"} <= set(m)
    assert set(inspect.signature(score_delivery).parameters) == {"delivered", "gt"}


def test_replay_reproduces_and_report_honest():
    tasks, runs, _ = _load()
    gold = {t["id"]: t["expected_dev_files"] for t in tasks}
    for r in runs:
        sc = score_delivery(set(r["delivered"]), {"files": gold[r["task_id"]]})
        assert sc["hit"] == r["hit"] and sc["recall_set"] == r["recall_set"]
    ok = [r for r in runs if not r["error"]]
    mean = sum(r["recall_set"] for r in ok) / len(ok)
    rep = REPORT.read_text(encoding="utf-8")
    assert "72" in rep and "sem modelo" in rep and "sem confirmação" in rep
    assert "NÃO interpretável" in rep and f"{mean:.3f}" in rep
