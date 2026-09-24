# SPDX-License-Identifier: Apache-2.0
"""F7: harness escreve JSONL válido com tempo/query e recall honesto."""
import json
import pathlib

from archatlas.harness import run

DEV = pathlib.Path("benchmarks/siga/queries_dev.json")


def test_harness_jsonl(tmp_path):
    rep = run(DEV, tmp_path / "h.sqlite", tmp_path / "r.jsonl", budget=2000)
    lines = (tmp_path / "r.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == rep["n"] == 153
    for ln in lines:
        r = json.loads(ln)
        assert {"id", "cat", "hit", "seconds", "used", "kept", "sha"} <= set(r)
        assert r["used"] <= 2000 and r["seconds"] >= 0
    assert 0.0 <= rep["recall"] <= 1.0
    assert rep["recall"] >= 0.90  # F10: 100Qs; freeze F8 (60Qs A/B/D) preservado abaixo
    import json as _json
    from collections import defaultdict as _dd
    per = _dd(lambda: [0, 0])
    for ln in lines:
        r = _json.loads(ln)
        per[r["cat"]][r["hit"]] += 1
    for cat in ("A", "B", "C", "D", "F"):
        assert per[cat][True] == sum(per[cat]), (cat, per[cat])  # escopo congelado: 100%
    print(f"\nF7 recall={rep['recall']:.3f} mean_query_s={rep['mean_query_s']} index_s={rep['index_seconds']}")
