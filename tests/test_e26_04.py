# SPDX-License-Identifier: Apache-2.0
"""E26-04: mesma entrega, poda determinística; foco errado degrada com sinal. Offline."""
import json
import pathlib

from archatlas.capsule import build_capsule
from archatlas.lexical import rebuild_lexical
from archatlas.packing import apply_focus, focus_terms
from archatlas.store import index_file, open_db

RUNS = pathlib.Path("experiments/e26_04/runs.jsonl")


def test_focus_terms_and_prune_preserve_skeleton(tmp_path):
    assert focus_terms("Assinar Movimentacao, com-senha?") == \
        ["assinar", "com", "movimentacao", "senha"]
    packed = {"symbols": [{"file": "a", "line": 1, "kind": "class", "name": "A"},
                          {"file": "a", "line": 2, "kind": "method", "name": "write"}],
              "excerpts": [{"id": "e0", "file": "a", "start_line": 1, "end_line": 1,
                            "tokens": 5, "truncated": False, "text": "public class A {",
                            "anchors": ["A"]},
                           {"id": "e1", "file": "a", "start_line": 2, "end_line": 2,
                            "tokens": 5, "truncated": False, "text": "void write() {}",
                            "anchors": ["write"]}],
              "citations": [{"excerpt_id": "e0", "file": "a", "line": 1, "symbol": "A"},
                            {"excerpt_id": "e1", "file": "a", "line": 2, "symbol": "write"}],
              "relations": [{"from": "a", "to": "A", "kind": "DEFINES",
                             "provenance": "t", "score": 1.0}],
              "truncation_log": [], "used": 10}
    out = apply_focus(packed, ["zzz"])
    assert out["omitted"] == 1 and out["pre_focus_kept"] == 2 and out["used"] == 5
    assert [e["id"] for e in out["excerpts"]] == ["e0"]  # esqueleto fica, método sai
    assert [r["dropped"] for r in out["truncation_log"] if r["rule"] == "focus-prune"] == ["e1"]
    keep = apply_focus(packed, ["write"])
    assert keep["omitted"] == 0  # termo casa o método; classe já era esqueleto


def test_capsule_focus_opt_in_and_wrong_fallback(tmp_path):
    f = tmp_path / "Foo.java"
    f.write_bytes(b"public class Foo {\n public void write() {}\n public void read() {}\n}\n")
    con = open_db(tmp_path / "f.sqlite")
    index_file(con, f, "t")
    rebuild_lexical(con)
    default = build_capsule(con, "Foo write", 2000)
    assert default["telemetry"]["focus_echo"] is None
    foc = build_capsule(con, "Foo write", 2000, focus="Foo write")
    assert foc["telemetry"]["focus_terms"] and foc["budget"]["used"] <= 2000
    assert foc["payload_tokens"] <= default["payload_tokens"]
    ids = {e["id"] for e in foc["excerpts"]}
    assert all(c["excerpt_id"] in ids for c in foc["citations"])
    wrong = build_capsule(con, "Foo write", 2000, focus="zxqvqw inexistente")
    assert wrong["telemetry"]["focus_omitted"] >= foc["telemetry"]["focus_omitted"]
    assert wrong["budget"]["used"] <= 2000  # fallback: mínimo + log, sem exceção


def test_runs_full_focus_wrong_and_report():
    runs = [json.loads(l) for l in RUNS.read_text(encoding="utf-8").splitlines()]
    assert len(runs) == 96
    assert {(r["case_id"], r["arm"]) for r in runs} == \
        {(r["case_id"], a) for r in runs for a in ("FULL", "FOCUS", "WRONG")}
    for suite in ("pilot", "e26_01pos"):
        full = [r for r in runs if r["suite"] == suite and r["arm"] == "FULL"]
        foc = [r for r in runs if r["suite"] == suite and r["arm"] == "FOCUS"]
        assert sum(r["hit"] for r in full) == sum(r["hit"] for r in foc)  # zero perda
        assert sum(r["payload_tokens"] for r in foc) <= sum(r["payload_tokens"] for r in full)
        assert all(r["patch_accepted"] is None and r["releituras"] is None for r in full + foc)
    rep = pathlib.Path("experiments/e26_04/REPORT.md").read_text(encoding="utf-8")
    assert "zero perda" in rep and "96" in rep and "neural" in rep
