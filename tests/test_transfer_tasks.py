# SPDX-License-Identifier: Apache-2.0
"""P6 tarefas dev: 6 válidas (3T1+3T2), testes existem, sem holdout/patch."""
import json
import pathlib

import pytest

TASKS = pathlib.Path("benchmarks/transfer/edit_tasks_dev.json")
T1 = pathlib.Path("/tmp/opencode-p6/t1")
T2 = pathlib.Path("/tmp/opencode-p6/t2")
clones_here = T1.is_dir() and T2.is_dir()
ROOTS = {"T1": T1, "T2": T2}
SHAS = {"T1": "ae2ceeb5a79f9459f54ecaa9f4b2f8e095a2277b",
        "T2": "8721173580390a9d297e5af06cac3f0b6841f425"}


def test_tasks_schema_no_holdout_no_patch():
    tasks = json.loads(TASKS.read_text(encoding="utf-8"))
    assert len(tasks) == 6
    assert sorted(t["id"] for t in tasks) == \
        ["T1-E1", "T1-E2", "T1-E3", "T2-E1", "T2-E2", "T2-E3"]
    blob = TASKS.read_text(encoding="utf-8")
    assert "holdout final" not in blob and "@@" not in blob and "diff --git" not in blob
    for t in tasks:
        assert {"id", "target", "snapshot_base", "problema", "public_test",
                "hidden_criteria", "timeout_s", "difficulty", "test_files"} <= set(t)
        assert t["snapshot_base"] == SHAS[t["target"]] and t["timeout_s"] >= 60
        assert t["hidden_criteria"].startswith("oculto:" + t["id"])
        assert "fail-before a demonstrar" in t["hidden_criteria"]  # proposto, não provado


@pytest.mark.skipif(not clones_here, reason="clones /tmp/opencode-p6 ausentes: só schema")
def test_public_tests_exist_in_pinned_checkouts():
    tasks = json.loads(TASKS.read_text(encoding="utf-8"))
    for t in tasks:
        for f in t["test_files"]:
            assert (ROOTS[t["target"]] / f).exists(), (t["id"], f)
