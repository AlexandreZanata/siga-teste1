# SPDX-License-Identifier: Apache-2.0
"""BTC-E26-06 ensaiado: jornada dev completa sobre repo sintético (sem humano, sem dataset)."""
import hashlib
import pathlib

from archatlas.bitcoin import devflow
from archatlas.bitcoin.dryrun import FIXTURES
from archatlas.bitcoin.temporal import snapshot_facts


def _repo(tmp_path):
    root = tmp_path / "repo"
    for rel, blob in FIXTURES.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(blob)
    (root / "notes.rs").write_bytes(b"// sem suporte declarado\n")
    return root


def test_journey_doctor_to_uninstall(tmp_path):
    root, work = _repo(tmp_path), tmp_path / "work"
    work.mkdir()
    doc = devflow.doctor(root)
    assert doc["state"] == "partial"  # .rs sem suporte: diagnóstico, não silêncio
    assert any(".rs" in d for d in doc["diagnostics"])
    idx = devflow.index_repo(root)
    assert idx["state"] == "ok" and idx["files"] == 12
    ctx = devflow.context_query(root, idx, "CheckTransaction validation")
    assert ctx["state"] == "ok" and ctx["out"]["excerpts"]
    assert ctx["out"]["used"] <= 2000
    first = ctx["out"]["citations"][0]
    opened = devflow.expand_evidence(root, first["file"], first["line"])
    assert opened["state"] == "ok" and first["symbol"] in opened["text"]
    ed = devflow.edit_task(root, work, "src/validation.cpp", b"\n// fix sintatico\n")
    assert ed["original_untouched"] is True
    assert (root / "src/validation.cpp").read_bytes() == FIXTURES["src/validation.cpp"]
    val = devflow.validate_checkout(ed["checkout"])
    assert val["state"] == "ok"
    old = snapshot_facts(root)
    (root / "src/mempool.h").write_bytes(b"#pragma once\n// mempool limit size strict\n")
    upd = devflow.update_index(old, root)
    assert upd["changed"] == ["src/mempool.h"] and upd["cost"]["reextract"] >= 1
    un = devflow.uninstall(work)
    assert un == {"state": "ok", "removed": True}
    assert not (tmp_path / "work").exists()


def test_stale_and_unsupported_are_states_not_crashes(tmp_path):
    root = _repo(tmp_path)
    assert devflow.doctor(tmp_path / "nope")["state"] == "stale"
    assert devflow.expand_evidence(root, "src/gone.cpp", 1)["state"] == "stale"
    assert devflow.expand_evidence(root, "src/net.cpp", 999)["state"] == "stale"
    bad = tmp_path / "bad.py"
    bad.write_bytes(b"def broken(:\n")
    val = devflow.validate_checkout(str(bad))
    assert val["state"] == "partial"
    assert any(c["check"] == "sintaxe-python" and not c["ok"] for c in val["checks"])
    h = hashlib.sha256((root / "src/net.cpp").read_bytes()).hexdigest()
    assert devflow.edit_task(root, tmp_path / "w2", "src/net.cpp", b"")["original_untouched"]
    assert hashlib.sha256((root / "src/net.cpp").read_bytes()).hexdigest() == h
