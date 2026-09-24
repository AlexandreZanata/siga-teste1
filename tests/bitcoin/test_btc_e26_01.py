# SPDX-License-Identifier: Apache-2.0
"""BTC-E26-01 no corpus: ouro próprio verificado, 3 braços, replay exato. Sem modelo."""
import inspect
import json
import pathlib

from archatlas.bitcoin.realretrieval import (ARMS, FANIN_CAP, build_fanin, exec_arm,
                                              run_all, verify_gold)
from archatlas.telemetry import score_delivery

TASKS = pathlib.Path("benchmarks/bitcoin/e26_01_dev.json")
RUNS = pathlib.Path("experiments/bitcoin/e26_01/btc-e2601-001/runs.jsonl")
MANS = pathlib.Path("experiments/bitcoin/e26_01/btc-e2601-001/manifest.jsonl")
REPORT = pathlib.Path("experiments/bitcoin/e26_01/btc-e2601-001/REPORT.md")


def _load():
    tasks = json.loads(TASKS.read_text(encoding="utf-8"))
    runs = [json.loads(l) for l in RUNS.read_text(encoding="utf-8").splitlines()]
    mans = [json.loads(l) for l in MANS.read_text(encoding="utf-8").splitlines()]
    return tasks, runs, mans


def test_gold_valid_and_without_solutions():
    tasks = json.loads(TASKS.read_text(encoding="utf-8"))
    pos = [t for t in tasks if t["type"] != "negative"]
    neg = [t for t in tasks if t["type"] == "negative"]
    assert len(tasks) == 34 and len(pos) == 26 and len(neg) == 8
    assert len({t["id"] for t in tasks}) == 34
    kinds = {t["kind"] for t in neg}
    assert kinds == {"natural", "wrong-repo"}
    for t in pos:
        assert t["expected_dev_files"], t["id"]
        for f in t["given_files"] + t["expected_dev_files"]:
            assert not f.startswith("/") and ".." not in f, (t["id"], f)
    for t in neg:
        assert t["expected_dev_files"] == [] and t["reason"], t["id"]
    blob = TASKS.read_text(encoding="utf-8")
    assert "@@" not in blob and "diff --git" not in blob


def test_verify_gold_loud_on_missing_file(tmp_path):
    (tmp_path / "a.cpp").write_bytes(b"int x;\n")
    try:
        verify_gold([{"id": "T", "given_files": [], "expected_dev_files": ["nope.cpp"]}],
                    {"a.cpp": "int x;"})
    except FileNotFoundError as e:
        assert "nope.cpp" in str(e)
    else:
        raise AssertionError("ouro fora do corpus deveria falhar ruidoso")


def test_arms_deterministic_and_evaluator_isolated(tmp_path):
    (tmp_path / "a.cpp").write_bytes(b"#include \"a.h\"\nfoo bar\n")
    (tmp_path / "a.h").write_bytes(b"foo\n")
    from archatlas.bitcoin.realretrieval import corpus_texts
    texts = corpus_texts(tmp_path)
    for arm in ARMS:
        assert exec_arm(arm, tmp_path, texts, "foo") == exec_arm(arm, tmp_path, texts, "foo")
    assert set(inspect.signature(score_delivery).parameters) == {"delivered", "gt"}


def test_protocol_paired_and_nulls_honest():
    tasks, runs, mans = _load()
    assert len(runs) == 34 * 3 * 2 and len(mans) == 34 * 3 * 2
    assert {(r["task_id"], r["condition"], r["budget"]) for r in runs} == \
        {(t["id"], c, b) for t in tasks for c in ARMS for b in (2000, 8000)}
    for r in runs:
        assert r["sha"] == "e6fde134f7da0d3616d90c40232d9ebe2ed9f033"
        assert r["patch_accepted"] is None and r["cost_total"] is None
        assert "sem modelo" in r["patch_note"] and "sem telemetria" in r["cost_note"]


def test_fanin_cap_skips_hubs_and_preserves_pairs(tmp_path):
    for name, blob in {
            "hub.h": b"#pragma once\n",
            "a.cpp": b'#include "hub.h"\n#include "solo.h"\nquerytoken\n',
            "b.cpp": b'#include "hub.h"\n',
            "c.cpp": b'#include "hub.h"\n',
            "solo.h": b"// solo\n"}.items():
        (tmp_path / name).write_bytes(blob)
    from archatlas.bitcoin.realretrieval import corpus_texts
    texts = corpus_texts(tmp_path)
    fanin = build_fanin(tmp_path)
    assert fanin["hub.h"] == 3 and fanin["solo.h"] == 1
    capped, note = exec_arm("C_adapter", tmp_path, texts, "querytoken a", fanin, cap=1)
    assert "hub.h" not in {f.split("/")[-1] for f in capped}
    assert "solo.h" in {f.split("/")[-1] for f in capped}
    assert "hubs_skipped=1" in note and "fanin_cap=1" in note
    free, note2 = exec_arm("C_adapter", tmp_path, texts, "querytoken a")
    assert "hub.h" in {f.split("/")[-1] for f in free}
    assert "fanin_cap=off" in note2
    assert FANIN_CAP == 25


RUNS2 = pathlib.Path("experiments/bitcoin/e26_01/btc-e2601-002/runs.jsonl")


def test_repeat_carries_fanin_fields_and_replays():
    tasks = {t["id"]: [f for f in t["expected_dev_files"] if f not in t.get("given_files", [])]
             for t in json.loads(TASKS.read_text(encoding="utf-8"))
             if t["type"] != "negative"}
    runs = [json.loads(l) for l in RUNS2.read_text(encoding="utf-8").splitlines()]
    assert len(runs) == 204
    assert all(r["fanin_cap"] == 25 and isinstance(r["hubs_skipped"], int) for r in runs)
    assert sum(r["hubs_skipped"] for r in runs if r["condition"] == "C_adapter") > 0
    for r in runs:
        if r["type"] == "negative":
            continue
        sc = score_delivery(set(r["delivered"]), {"files": tasks[r["task_id"]]})
        assert sc["hit"] == r["hit"] and sc["recall_set"] == r["recall_set"]


def test_replay_reproduces_and_report_honest():
    tasks, runs, _ = _load()
    gold = {t["id"]: [f for f in t["expected_dev_files"] if f not in t.get("given_files", [])]
            for t in tasks if t["type"] != "negative"}
    for r in runs:
        if r["type"] == "negative":
            assert r["hit"] is False
            continue
        sc = score_delivery(set(r["delivered"]), {"files": gold[r["task_id"]]})
        assert sc["hit"] == r["hit"] and sc["recall_set"] == r["recall_set"], r["task_id"]
    rep = REPORT.read_text(encoding="utf-8")
    assert "sem modelo" in rep and "sem confirmação" in rep
    assert "204" in rep
