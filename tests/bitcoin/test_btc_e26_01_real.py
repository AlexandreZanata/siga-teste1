# SPDX-License-Identifier: Apache-2.0
"""BTC-E26-01-real: sondas válidas + replay puro + braços herméticos. Sem holdout."""
import json
import pathlib

import pytest

from archatlas.bitcoin.realretrieval import (ARMS, BUDGET, corpus_texts,
                                             exec_arm, used_tokens)
from archatlas.telemetry import score_delivery

TASKS = pathlib.Path("benchmarks/bitcoin/e26_01_real.json")
RUNDIR = pathlib.Path("experiments/bitcoin/e26_01_real/btc-e26-01-real-001")
CORPUS = pathlib.Path("/tmp/btc-readonly")
corpus_here = CORPUS.is_dir()


def _mini(tmp_path):
    root = tmp_path / "mini"
    (root / "src").mkdir(parents=True)
    (root / "src" / "validation.cpp").write_bytes(
        b'#include "validation.h"\n// CheckTransaction mempool accept\n')
    (root / "src" / "validation.h").write_bytes(b"#pragma once\n// validation spent\n")
    (root / "src" / "txmempool.h").write_bytes(b"#pragma once\n// mempool limit size\n")
    return root


def test_tasks_schema_and_replay_without_corpus():
    tasks = json.loads(TASKS.read_text(encoding="utf-8"))
    assert len(tasks) == 12
    from collections import Counter
    assert Counter(t["family"] for t in tasks) == \
        {"mempool": 3, "rpc": 3, "wallet": 3, "net": 3}
    assert len({t["id"] for t in tasks}) == 12
    for t in tasks:
        assert len(t["expected_dev_files"]) == 2 and "holdout final" not in json.dumps(t)
    runs = [json.loads(l) for l in (RUNDIR / "runs.jsonl").read_text(encoding="utf-8").splitlines()]
    mans = [json.loads(l) for l in (RUNDIR / "manifest.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(runs) == 72 and len(mans) == 72  # 12 x 3 x 2
    assert {(r["task_id"], r["condition"]) for r in runs} == \
        {(t["id"], a) for t in tasks for a in ARMS}
    for r in runs:  # replay puro: re-escora (delivered, ouro), sem corpus
        sc = score_delivery(r["delivered"], {"files": next(
            t["expected_dev_files"] for t in tasks if t["id"] == r["task_id"])})
        assert sc["hit"] == r["hit"] and sc["recall_set"] == r["recall_set"]
        assert r["patch_accepted"] is None and r["cost_total"] is None
    rep = (RUNDIR / "REPORT.md").read_text(encoding="utf-8")
    assert "0.833" in rep and "72" in rep and "sem modelo" in rep and "addrman" in rep


def test_arms_hermetic_on_mini_repo(tmp_path):
    root = _mini(tmp_path)
    texts = corpus_texts(root)
    assert set(texts) == {"src/validation.cpp", "src/validation.h", "src/txmempool.h"}
    hit, _ = exec_arm("C_adapter", root, texts, "where is validation CheckTransaction")
    assert "src/validation.cpp" in hit and "src/validation.h" in hit  # salto #include real
    assert exec_arm("B_freq", root, texts, "mempool")[0] <= set(texts)
    assert len(exec_arm("B_freq", root, texts, "mempool")[0]) <= 4
    with pytest.raises(ValueError):
        exec_arm("Z_stub", root, texts, "x")
    assert used_tokens(root, {"src/validation.cpp"}, BUDGET) >= 1


@pytest.mark.skipif(not corpus_here, reason="corpus v31.1 ausente: só replay hermético")
def test_gold_files_exist_in_pinned_corpus():
    tasks = json.loads(TASKS.read_text(encoding="utf-8"))
    missing = [f for t in tasks for f in t["expected_dev_files"]
               if not (CORPUS / f).exists()]
    assert missing == []
