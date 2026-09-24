from archatlas.config import REPO_ROOT, dataset_root
# SPDX-License-Identifier: Apache-2.0
"""F16: trace encontra as 8 cadeias GT; cada aresta re-verificada no disco."""
import json
import pathlib

from archatlas.trace import build_call_index, trace

DS = dataset_root()
DEV = pathlib.Path("benchmarks/siga/queries_dev.json")


def test_trace_finds_gt_chains():
    files = sorted((DS / "siga-ex/src/main/java").rglob("*.java"))[:40]
    idx = build_call_index(files)
    hs = [q for q in json.loads(DEV.read_text(encoding="utf-8")) if q["category"] == "H"]
    assert len(hs) == 8
    for q in hs:
        a, _, c = q["gt"]["chain"]
        path = trace(idx, a, c)
        assert path, q["id"]
        assert path[0]["caller"] == a and path[-1]["callee"] == c
        for e in path:
            line = pathlib.Path(e["file"]).read_text(
                encoding="utf-8", errors="replace").splitlines()[e["line"] - 1]
            assert e["callee"] in line
