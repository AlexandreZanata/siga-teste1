# SPDX-License-Identifier: Apache-2.0
"""E26-05: replay valida instruções/protocolo/contagem; vivo fica N/A. Offline."""
import json
import pathlib

from archatlas.history import cliff, drop_old, keep, replay, total_tokens

RUNS = pathlib.Path("experiments/e26_05/runs.jsonl")


def _session(n_pairs=30, needle=True):
    instr = [{"role": "system", "content": "siga o protocolo"},
             {"role": "system", "content": "formato arquivo:linha"}]
    msgs = list(instr)
    if needle:
        msgs.append({"role": "assistant", "content": "DECISAO: estrategia B"})
    for i in range(n_pairs):
        msgs.append({"role": "assistant", "content": f"call {i}",
                     "tool_call": True, "call_id": f"k{i}"})
        msgs.append({"role": "tool", "content": f"resp {i} " + "y" * 120,
                     "tool_response": True, "call_id": f"k{i}"})
    return msgs


def test_replay_validates_and_windows_keep_pairs():
    S = _session(60)
    assert total_tokens(S) > 2000  # pressão real sobre o budget
    for fn in (keep, drop_old, cliff):
        r = fn(S, 2000)
        rp = replay(r["effective"])
        assert rp["instructions_n"] == 2 and rp["protocol_intact"] is True
        assert rp["total_tokens"] == total_tokens(r["effective"])  # contagem exata
    k = keep(S, 2000)
    assert k["overflow"] is True and k["dropped"] == 0  # sem compactação, estouro honesto
    d = drop_old(S, 2000)
    assert d["overflow"] is False  # mais barato...
    assert not any("estrategia B" in m.get("content", "") for m in d["effective"])  # ...mas perde
    c = cliff(S, 2000)
    assert c["overflow"] is False and c["markers"]  # marcador literal, sem reescrita
    assert any("estrategia B" in m.get("content", "") for m in c["effective"])
    assert replay([{"role": "assistant", "content": "x", "tool_call": True,
                    "call_id": "solo"}])["protocol_intact"] is False  # órfão detectado


def test_runs_artifacts_and_live_marked_na():
    runs = [json.loads(l) for l in RUNS.read_text(encoding="utf-8").splitlines()]
    assert len(runs) == 6
    assert {(r["session"], r["policy"]) for r in runs} == \
        {(s, p) for s in ("S1-longa", "S2-decisao-antiga") for p in ("KEEP", "DROP-OLD", "CLIFF")}
    for r in runs:
        assert r["instructions_intact"] is True and r["protocol_intact"] is True
        assert r["success"] is None  # vivo N/A: nulo com motivo, nunca zero
    s2 = {r["policy"]: r for r in runs if r["session"] == "S2-decisao-antiga"}
    assert s2["KEEP"]["decision_found"] is True
    assert s2["DROP-OLD"]["decision_found"] is False
    assert s2["CLIFF"]["decision_found"] is True
    rep = pathlib.Path("experiments/e26_05/REPORT.md").read_text(encoding="utf-8")
    assert "N/A" in rep and "6" in rep and "sem" in rep
