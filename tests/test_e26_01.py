# SPDX-License-Identifier: Apache-2.0
"""E26-01: ouro dev válido + protocolo 28x5 + replay puro. Offline, sem holdout."""
import json
import pathlib

from archatlas.config import dataset_root
from archatlas.telemetry import score_additional

SHA = "e3be22828f787cbe71b339aecb7a7bf569099803"
CASES = pathlib.Path("benchmarks/siga/e26_01_dev.json")
RUNS = pathlib.Path("experiments/e26_01/runs.jsonl")
MANS = pathlib.Path("experiments/e26_01/manifest.jsonl")
REPORT = pathlib.Path("experiments/e26_01/REPORT.md")
CONDS = {"LEX", "ATLAS-multi-2000", "ATLAS-multi-8000",
         "ATLAS-one_per_file-2000", "ATLAS-one_per_file-8000"}


def _load():
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    runs = [json.loads(l) for l in RUNS.read_text(encoding="utf-8").splitlines()]
    mans = [json.loads(l) for l in MANS.read_text(encoding="utf-8").splitlines()]
    return cases, runs, mans


def test_cases_gold_valid():
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    assert len(cases) == 28
    from collections import Counter
    assert Counter(c["type"] for c in cases) == \
        {"code2test": 5, "trace2code": 5, "comment2context": 5,
         "edit2ripple": 5, "negative": 8}
    assert len({c["id"] for c in cases}) == 28
    ds = dataset_root()
    for c in cases:
        assert c["snapshot_base"] == SHA
        assert "holdout final" not in json.dumps(c) and "@@" not in json.dumps(c)
        if c["type"] == "negative":
            assert c["expected_additional"] == [] and c["negative_reason"] in \
                ("no-local-evidence", "wrong-repo")
        else:
            assert len(c["expected_additional"]) >= 1 and c["negative_reason"] is None
            for f in c["given_files"] + c["expected_additional"]:
                assert (ds / f).exists(), (c["id"], f)  # bytes reais no PIN
            stem = [f.split("/")[-1].replace(".java", "") for f in c["expected_additional"]]
            assert not any(s in c["query"] for s in stem)  # consulta não nomeia o ouro


def test_protocol_28x5_and_no_recall_on_zero_denominator():
    cases, runs, mans = _load()
    assert len(runs) == 140 and len(mans) == 140
    assert {(r["case_id"], r["condition"]) for r in runs} == \
        {(c["id"], k) for c in cases for k in CONDS}
    for r in runs:
        assert r["sha"] == SHA and r["patch_accepted"] is None
        if r["expected_count"] == 0:
            assert r["recall_set"] is None  # jamais recall convencional c/ denominador zero
        else:
            assert 0.0 <= r["recall_set"] <= 1.0
        if r["condition"].startswith("ATLAS-"):
            assert r["used"] <= r["budget"]
    for m in mans:
        assert {"task_id", "condition", "budget", "sha"} <= set(m)


def test_replay_and_additional_unit():
    cases, runs, _ = _load()
    gold = {c["id"]: (c["expected_additional"], c["given_files"]) for c in cases}
    for r in runs[:40]:  # amostra do replay puro (sem índice/disco)
        exp, giv = gold[r["case_id"]]
        sc = score_additional(set(r["delivered"]), exp, giv)
        assert sc["hit"] == r["hit"] and sc["recall_set"] == r["recall_set"] \
            and sc["abstained"] == r["abstained"]
    sc = score_additional({"g.java", "a.java"}, {"a.java"}, {"g.java"})
    assert sc["recall_set"] == 1.0 and sc["novel_count"] == 1  # dado é excluído
    neg = score_additional({"x.java"}, [], [])
    assert neg["recall_set"] is None and neg["abstained"] is False
    assert score_additional(set(), [], [])["abstained"] is True


def test_report_withholds_promotion():
    rep = REPORT.read_text(encoding="utf-8")
    assert "Sem promoção" in rep and "abstenção" in rep
    assert "code2test 0/5" in rep and "140" in rep
