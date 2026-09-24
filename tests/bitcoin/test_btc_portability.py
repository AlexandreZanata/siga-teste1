# SPDX-License-Identifier: Apache-2.0
"""BTC-P6 drill temporal: t0 → t1 sintéticos (mudança de header, arquivo novo, remoção)."""
import pathlib

from archatlas.bitcoin.dryrun import FIXTURES
from archatlas.bitcoin.temporal import diff_snapshots, snapshot_facts, update_cost


def _repos(tmp_path):
    t0 = tmp_path / "t0"
    for rel, blob in FIXTURES.items():
        p = t0 / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(blob)
    t1 = tmp_path / "t1"
    for rel, blob in FIXTURES.items():
        if rel == "test/wallet_tests.py":  # remoção em t1
            continue
        p = t1 / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(blob)
    (t1 / "src/validation.h").write_bytes(  # header alterado em t1
        b"#pragma once\n// validation spent CheckTransaction fee\n")
    (t1 / "src/policy.cpp").write_bytes(b'#include "policy.h"\n// policy fee\n')
    (t1 / "src/policy.h").write_bytes(b"#pragma once\n// policy\n")
    return t0, t1


def test_diff_classifies_and_invalidates_dependents(tmp_path):
    t0, t1 = _repos(tmp_path)
    d = diff_snapshots(snapshot_facts(t0), snapshot_facts(t1))
    assert d["added"] == ["src/policy.cpp", "src/policy.h"]
    assert d["removed"] == ["test/wallet_tests.py"]
    assert d["changed"] == ["src/validation.h"]
    assert "src/validation.cpp" in d["invalidated"]  # inclui validation.h
    assert "src/wallet/wallet.cpp" in d["invalidated"]  # inclui validation.h
    assert "src/rpc/server.cpp" in d["invalidated"]  # inclui validation.h
    assert "src/net.cpp" not in d["invalidated"]  # sem dependência: sem retrabalho
    assert "src/mempool.cpp" not in d["invalidated"]
    cost = update_cost(d, 13)
    assert cost["reextract"] == len(d["invalidated"]) and cost["total"] == 13
    assert 0.0 < cost["fraction"] < 1.0  # incremental < rebuild, ambos registrados


def test_no_change_no_rework_and_deterministic(tmp_path):
    t0, _ = _repos(tmp_path)
    a = snapshot_facts(t0)
    d = diff_snapshots(a, snapshot_facts(t0))
    assert d["added"] == d["removed"] == d["changed"] == d["invalidated"] == []
    assert len(d["unchanged"]) == 12
    assert diff_snapshots(a, snapshot_facts(t0)) == d
