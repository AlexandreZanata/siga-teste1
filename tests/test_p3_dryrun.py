# SPDX-License-Identifier: Apache-2.0
"""P3 dry-run: tarefas válidas + protocolo A/B/C pareado, sem modelo, sem holdout."""
import inspect
import json
import pathlib

from archatlas.config import dataset_root
from archatlas.telemetry import score_delivery

SHA = "e3be22828f787cbe71b339aecb7a7bf569099803"
TASKS = pathlib.Path("benchmarks/siga/pilot_p3_dev.json")
RUNS = pathlib.Path("experiments/pilot_p3/runs.jsonl")
MANS = pathlib.Path("experiments/pilot_p3/manifest.jsonl")
REPORT = pathlib.Path("experiments/pilot_p3/REPORT_DRYRUN.md")


def _load():
    tasks = json.loads(TASKS.read_text(encoding="utf-8"))
    runs = [json.loads(l) for l in RUNS.read_text(encoding="utf-8").splitlines()]
    mans = [json.loads(l) for l in MANS.read_text(encoding="utf-8").splitlines()]
    return tasks, runs, mans


def test_tasks_valid_and_grounded():
    tasks = json.loads(TASKS.read_text(encoding="utf-8"))
    assert len(tasks) == 12
    ids = [t["id"] for t in tasks]
    assert sorted(ids) == [f"P3D-{i:03d}" for i in range(1, 13)]
    fams = [t["family"] for t in tasks]
    assert fams.count("backend") == 5 and fams.count("frontend") == 3 and fams.count("cross") == 4
    ds = dataset_root()
    for t in tasks:
        assert {"problema", "query", "snapshot_base", "module", "expected_dev_files",
                "public_check", "hidden_criteria", "timeout_s", "budget_capsule"} <= set(t)
        assert t["snapshot_base"] == SHA and t["timeout_s"] >= 60 and t["budget_capsule"] == 2000
        assert len(t["expected_dev_files"]) >= 2 and t["hidden_criteria"].startswith("oculto:P3D-")
        assert "patch" not in t["problema"].lower() or "sem" in t["problema"].lower()
        for f in t["expected_dev_files"]:
            assert (ds / f).exists(), (t["id"], f)  # bytes reais no dataset pinado
    blob = TASKS.read_text(encoding="utf-8")
    assert "holdout final" not in blob and "@@" not in blob  # sem solução/gabarito final


def test_protocol_paired_budgeted_isolated():
    tasks, runs, mans = _load()
    assert len(runs) == 36 and len(mans) == 36
    assert {(r["task_id"], r["condition"]) for r in runs} == \
        {(t["id"], c) for t in tasks for c in ("A_lex", "B_cap", "C_router")}
    for r in runs:
        assert r["sha"] == SHA and r["tokenizer"] == "chars//4" and r["budget"] == 2000
        assert isinstance(r["hit"], bool) and 0.0 <= r["recall_set"] <= 1.0
        assert r["patch_accepted"] is None and r["cost_total"] is None  # sem modelo: nulo
        assert "sem modelo" in r["patch_note"] and "sem telemetria" in r["cost_note"]
        if r["condition"] == "B_cap":
            assert r["used"] <= 2000 and r["payload_tokens"] >= r["used"]
    for m in mans:
        assert {"task_id", "condition", "repetition", "order", "budget", "sha", "tokenizer"} <= set(m)
    assert inspect.signature(score_delivery).parameters.keys() == {"delivered", "gt"}


def test_replay_reproduces_and_report_honest():
    tasks, runs, _ = _load()
    gold = {t["id"]: t["expected_dev_files"] for t in tasks}
    for r in runs:
        sc = score_delivery(set(r["delivered"]), {"files": gold[r["task_id"]]})
        assert sc["hit"] == r["hit"] and sc["recall_set"] == r["recall_set"]
    rep = REPORT.read_text(encoding="utf-8")
    assert "sem modelo" in rep and "sem confirmação" in rep
    assert "fora do índice" in rep and "6461" in rep  # JSP + payload>=used registrados
    assert "0.750" in rep and "36" in rep
