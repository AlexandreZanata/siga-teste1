# SPDX-License-Identifier: Apache-2.0
"""BTC-E26-02 sintético: profundidade vs quantidade de arquivos, mesmo ranking/budget.

Fixtures próprias (repo sintético do dryrun); sem modelo, sem dataset, sem holdout.
"""
import pathlib
import tempfile

from archatlas.bitcoin.dryrun import FIXTURES, build_fixture_repo
from archatlas.bitcoin.packing import header_pairs, pack_candidates
from archatlas.bitcoin.cpp_lex import extract_cpp_lexical


def _setup():
    tmp = tempfile.TemporaryDirectory(prefix="btc-e2602-")
    root = build_fixture_repo(pathlib.Path(tmp.name))
    disk = {str(p.relative_to(root)): p.read_bytes().decode().splitlines()
            for p in root.rglob("*") if p.is_file()}
    facts = {}
    for rel in [f for f in disk if pathlib.Path(f).suffix in {".c", ".h", ".hpp", ".cpp"}]:
        facts[rel] = extract_cpp_lexical(root / rel)["facts"]
    pairs = header_pairs(facts)
    ranked = [
        {"file": "src/rpc/server.cpp", "line": 1, "kind": "include", "name": "server.h",
         "provenance": "lexical-verified", "confidence": 0.6},
        {"file": "src/rpc/server.cpp", "line": 2, "kind": "include", "name": "validation.h",
         "provenance": "lexical-verified", "confidence": 0.6},
        {"file": "src/rpc/server.cpp", "line": 3, "kind": "ref", "name": "GetState",
         "provenance": "text-match-verified", "confidence": 0.7},
        {"file": "src/rpc/server.cpp", "line": 1, "kind": "include", "name": "server.h",
         "provenance": "lexical-verified", "confidence": 0.6},  # span duplicado
        {"file": "src/validation.cpp", "line": 1, "kind": "include", "name": "validation.h",
         "provenance": "lexical-verified", "confidence": 0.6},
        {"file": "src/validation.cpp", "line": 3, "kind": "ref", "name": "CheckTransaction",
         "provenance": "text-match-verified", "confidence": 0.7},
        {"file": "src/net.cpp", "line": 2, "kind": "ref", "name": "SendMessage",
         "provenance": "text-match-verified", "confidence": 0.7},
        {"file": "src/gone.cpp", "line": 1, "kind": "ref", "name": "Missing",
         "provenance": "text-match-verified", "confidence": 0.7},  # ilegível
    ]
    return tmp, disk, pairs, ranked


def _pack_all(budget=120):
    tmp, disk, pairs, ranked = _setup()
    try:
        return {p: pack_candidates(ranked, disk, budget, p, pairs)
                for p in ("one_per_file", "multi", "expanded")}
    finally:
        tmp.cleanup()


def test_same_input_dedup_and_budget_in_all_three():
    res = _pack_all()
    for pol, out in res.items():
        assert out["used"] <= 120, pol
        rules = [e["rule"] for e in out["truncation_log"]]
        assert "duplicate-span" in rules, pol  # span duplicado dedup nas três
        kept = [(e["file"], e["start_line"]) for e in out["excerpts"]]
        assert len(kept) == len(set(kept)), pol
        again = _pack_all()[pol]
        assert again == out, f"determinismo {pol}"


def test_breadth_vs_depth():
    res = _pack_all()
    per_file = {}
    for e in res["one_per_file"]["excerpts"]:
        per_file.setdefault(e["file"], 0)
        per_file[e["file"]] += 1
    assert all(v == 1 for v in per_file.values())  # 1 trecho/arquivo
    assert any(e["rule"] == "one-per-file" for e in res["one_per_file"]["truncation_log"])
    multi_files = [e["file"] for e in res["multi"]["excerpts"]]
    assert len(multi_files) > len(set(multi_files))  # profundidade: repete arquivo
    assert len(res["multi"]["excerpts"]) >= len(res["one_per_file"]["excerpts"])


def test_expanded_preserves_pairs_at_comparable_cost():
    res = _pack_all()
    assert res["expanded"]["pairs_complete"] >= res["multi"]["pairs_complete"]
    assert res["expanded"]["used"] >= res["multi"]["used"]  # contexto custa
    assert res["expanded"]["used"] <= 120


def test_gates_loud_and_tiny_budget_enforced():
    res = _pack_all()
    rules = [e["rule"] for e in res["multi"]["truncation_log"]]
    assert "unreadable" in rules  # gone.cpp registrado, sem crash
    tiny = _pack_all(budget=5)
    for pol, out in tiny.items():
        assert out["used"] <= 5, pol
        assert any(e["rule"] == "over_budget" for e in out["truncation_log"]), pol
