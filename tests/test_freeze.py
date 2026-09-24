# SPDX-License-Identifier: Apache-2.0
"""F15: freeze — artefatos existem, números batem, tabelas regeneráveis."""
import json
import pathlib


def test_freeze_v1():
    b = pathlib.Path("benchmarks/siga")
    bake = json.loads((b / "bakeoff_f13.json").read_text())
    perf = json.loads((b / "perf_f14.json").read_text())
    assert bake["router"]["recall"] == 1.0
    assert perf["files"] == 504 and perf["db_kb"] < 5120
    assert (b / "TABLES_v1.md").read_text().count("1.00") >= 2
    sbom = json.loads(pathlib.Path("sbom/v1.json").read_text())
    assert sbom["metadata"]["component"]["name"] == "archatlas"
    assert "e3be22828" in json.dumps(sbom)
    assert (b / "FREEZE_V1.md").exists()
