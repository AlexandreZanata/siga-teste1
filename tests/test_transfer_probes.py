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
