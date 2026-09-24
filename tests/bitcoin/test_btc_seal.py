# SPDX-License-Identifier: Apache-2.0
"""BTC-P5: selamento e cegamento — ensaio com tarefas estruturais próprias, sem ouro real."""
import json
import pathlib

import pytest

from archatlas.bitcoin.seal import (FORBIDDEN_IN_BLIND, blind_map, blind_package,
                                    seal_manifest, unblind, verify_seal)

TASKS = json.loads(pathlib.Path("benchmarks/bitcoin/pilot_p3_dev.json").read_text(encoding="utf-8"))
STRUCT = [{"id": t["id"], "family": t["family"], "scope": t["scope"]} for t in TASKS]
VERSIONS = {"core_sha": "e6fde134f7da0d3616d90c40232d9ebe2ed9f033",
            "adapter": "btc-cpp-lex/1", "policy": "btc-pack/1+expanded",
            "budget": 2000, "tokenizer": "chars//4"}


def test_seal_deterministic_and_tamper_detected():
    s1 = seal_manifest(STRUCT, ["A_busca", "B_freq", "C_adapter"], 2, 7, VERSIONS)
    s2 = seal_manifest(STRUCT, ["A_busca", "B_freq", "C_adapter"], 2, 7, VERSIONS)
    assert s1 == s2 and verify_seal(s1) is True
    assert len(s1["seal"]) == 64
    bad = json.loads(json.dumps(s1))
    bad["manifest"]["repetitions"] = 3
    assert verify_seal(bad) is False
    bad2 = json.loads(json.dumps(s1))
    bad2["manifest"]["tasks"][0]["family"] = "wallet"  # original é "rpc"
    assert verify_seal(bad2) is False
    assert verify_seal({"manifest": s1["manifest"], "seal": s1["seal"]}) is False  # schema exigido


def test_blind_bijection_seeded_and_key_gated():
    ids = [f"patch-{t['id']}-{c}" for t in STRUCT[:4] for c in ("A", "B")]
    m1, key = blind_map(ids, 7)
    m2, _ = blind_map(ids, 7)
    assert m1 == m2 and sorted(m1.values()) == [f"Blind-{i:03d}" for i in range(1, 9)]
    assert unblind(m1[ids[0]], key) == ids[0]
    with pytest.raises(PermissionError):
        unblind(m1[ids[0]], None)
    with pytest.raises(PermissionError):
        unblind(m1[ids[0]], {})
    with pytest.raises(KeyError):
        unblind("Blind-999", key)


def test_blind_package_hides_conditions():
    pkg = blind_package(TASKS[0], "BTC_SHA-pendente", "diff-sintetico", {"aceitacao": "pass"})
    assert set(pkg) == {"task", "snapshot_ref", "patch", "rubric"}
    assert set(pkg["task"]) <= {"id", "family", "scope", "problema"}
    assert not (set(pkg) & FORBIDDEN_IN_BLIND)
    blob = json.dumps(pkg)
    assert "A_busca" not in blob and "e6fde13" not in blob
