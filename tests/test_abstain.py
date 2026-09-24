# SPDX-License-Identifier: Apache-2.0
"""P4-infra(c): gate dev-calibrado (mesma-amostra, otimista) + integração. Offline."""
import json
import pathlib

from archatlas.abstain import CALIBRATION, WEAK_TOP, decide, features
from archatlas.capsule import build_capsule
from archatlas.lexical import rebuild_lexical
from archatlas.store import index_file, open_db

RUNS = pathlib.Path("experiments/e26_01/runs_r3.jsonl")
MANS = pathlib.Path("experiments/e26_01/manifest_r3.jsonl")


def test_gate_unit_frozen_rule():
    assert WEAK_TOP == -1.0 and "holdout pendente" in CALIBRATION
    assert decide(features(0, 0, None)) == \
        {"abstain": True, "reason": "no-local-evidence", "uncertain": False}
    assert decide(features(0, 18, -0.0))["uncertain"] is True  # WR-03: bandeira, sem reter
    assert decide(features(2, 20, -15.0)) == \
        {"abstain": False, "reason": None, "uncertain": False}
    assert decide(features(0, 20, -4.5))["uncertain"] is True


def test_capsule_integration_opt_in(tmp_path):
    f = tmp_path / "Foo.java"
    f.write_bytes(b"public class Foo {\n public void write() {}\n}\n")
    con = open_db(tmp_path / "g.sqlite")
    index_file(con, f, "t")
    rebuild_lexical(con)
    default = build_capsule(con, "Foo", 2000)  # default: gate desligado, legado intacto
    assert default["telemetry"]["abstained"] is False
    assert default["telemetry"]["uncertain"] is None
    assert default["budget"]["used"] <= 2000
    empty = build_capsule(con, "zxqvqw inexistente", 2000, abstain=True)
    assert empty["telemetry"]["abstained"] is True
    assert empty["telemetry"]["abstain_reason"] == "no-local-evidence"
    assert empty["files"] == [] and empty["budget"]["used"] == 0
    assert empty["payload_tokens"] == 1
    full = build_capsule(con, "Foo", 2000, abstain=True)
    assert full["telemetry"]["abstained"] is False
    assert full["files"] == default["files"]  # gate não muda entrega confiante


def test_r3_artifacts_discovery_delta_and_flags():
    runs = [json.loads(l) for l in RUNS.read_text(encoding="utf-8").splitlines()]
    mans = [json.loads(l) for l in MANS.read_text(encoding="utf-8").splitlines()]
    assert len(runs) == 84 and len(mans) == 84
    assert {(r["case_id"], r["condition"]) for r in runs} == \
        {(c, k) for c in {r["case_id"] for r in runs}
         for k in ("LEX", "ATLAS-multi-2k-gate", "ATLAS-one_per_file-2k-gate")}
    pos = [r for r in runs if r["expected_count"] > 0]
    neg = [r for r in runs if r["expected_count"] == 0]
    multi = [r for r in pos if r["condition"] == "ATLAS-multi-2k-gate"]
    assert sum(r["gate_abstained"] for r in multi) == 5
    assert sum(r["gate_abstained"] for r in neg
               if r["condition"] == "ATLAS-multi-2k-gate") == 7
    lost = [r["case_id"] for r in multi if r["case_id"] == "E01-C2C-02"]
    assert lost and all(r["hit"] is False for r in
                        [x for x in multi if x["case_id"] == "E01-C2C-02"])
    assert all(r["recall_set"] is None for r in neg)  # sem recall em denominador zero
    rep = pathlib.Path("experiments/e26_01/REPEAT_R3.md").read_text(encoding="utf-8")
    assert "descartado como default" in rep and "C2C-02" in rep
