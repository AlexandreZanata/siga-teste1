# SPDX-License-Identifier: Apache-2.0
"""Teto de fan-in: hubs pulados, ouro preservado; A/B idênticos entre 001/002. Sem modelo."""
import json
import pathlib

from archatlas.bitcoin.realretrieval import ARMS, exec_arm

R1 = pathlib.Path("experiments/bitcoin/e26_01_real/btc-e26-01-real-001/runs.jsonl")
R2 = pathlib.Path("experiments/bitcoin/e26_01_real/btc-e26-01-real-002/runs.jsonl")


def _mini(tmp_path):
    root = tmp_path / "mini"
    (root / "src").mkdir(parents=True)
    (root / "src" / "hub.h").write_bytes(b"#pragma once\n// hub onipresente\n")
    (root / "src" / "leaf.h").write_bytes(b"#pragma once\n// leaf alpha\n")
    (root / "src" / "alpha.cpp").write_bytes(b'#include "hub.h"\n#include "leaf.h"\n// alpha\n')
    (root / "src" / "beta.cpp").write_bytes(b'#include "hub.h"\n// beta\n')
    return root


def _texts(root):
    from archatlas.bitcoin.realretrieval import corpus_texts
    return corpus_texts(root)


def test_hub_skipped_leaf_kept_and_legacy_uncapped(tmp_path):
    from archatlas.bitcoin.realretrieval import build_fanin
    root = _mini(tmp_path)
    texts = _texts(root)
    assert set(texts) == {"src/hub.h", "src/leaf.h", "src/alpha.cpp", "src/beta.cpp"}
    fanin = build_fanin(root)
    assert fanin.get("hub.h", 0) == 2 and fanin.get("leaf.h", 0) == 1
    hit_cap, note = exec_arm("C_adapter", root, texts, "alpha beta", fanin, cap=1)
    assert "src/hub.h" not in hit_cap  # hub (fan-in 2 > 1) pulado...
    assert "src/leaf.h" in hit_cap  # ...folha (fan-in 1) mantida
    assert "hubs_skipped=" in note
    hit_full, _ = exec_arm("C_adapter", root, texts, "alpha beta", None)
    hit_none, _ = exec_arm("C_adapter", root, texts, "alpha beta", fanin, cap=10 ** 9)
    assert hit_full == hit_none and "src/hub.h" in hit_full  # legado sem teto
    again, _ = exec_arm("C_adapter", root, texts, "alpha beta", fanin, cap=1)
    assert again == hit_cap  # determinístico


def test_repeat_002_preserves_hits_and_ab_identical():
    r1 = [json.loads(l) for l in R1.read_text(encoding="utf-8").splitlines()]
    r2 = [json.loads(l) for l in R2.read_text(encoding="utf-8").splitlines()]
    assert len(r2) == 72
    assert {(r["task_id"], r["condition"]) for r in r2} == \
        {(r["task_id"], r["condition"]) for r in r1}
    for arm in ("A_busca", "B_freq"):  # fator isolado no C: A/B bit-idênticos
        for a, b in zip(sorted(r1, key=lambda r: (r["task_id"], r["condition"], r["repetition"])),
                        sorted(r2, key=lambda r: (r["task_id"], r["condition"], r["repetition"]))):
            if a["condition"] == arm:
                assert a["delivered"] == b["delivered"] and a["hit"] == b["hit"]
    c1 = [r for r in r1 if r["condition"] == "C_adapter"]
    c2 = [r for r in r2 if r["condition"] == "C_adapter"]
    assert sum(r["hit"] for r in c2) == sum(r["hit"] for r in c1)  # zero perda
    assert sum(len(r["delivered"]) for r in c2) < sum(len(r["delivered"]) for r in c1)
    assert all(r["fanin_cap"] == 100 and r["patch_accepted"] is None for r in c2)
    assert all(r["recall_set"] is None or 0.0 <= r["recall_set"] <= 1.0 for r in r2)
