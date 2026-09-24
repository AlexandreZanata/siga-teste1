# SPDX-License-Identifier: Apache-2.0
"""P4/E26-02: mesmo ranking, só empacotamento varia — fixtures offline, sem LLM."""
from archatlas.capsule import build_capsule
from archatlas.lexical import rebuild_lexical
from archatlas.packing import pack_ranked
from archatlas.store import index_file, open_db

DISK = {"a.java": ["public class A {", "public void write() {}"],
        "b.java": ["public class B {", "public void read() {}"]}


def _ranked():
    mk = lambda f, ln, n, k="method": {"name": n, "kind": k, "file": f, "line": ln,
                                       "provenance": "t", "confidence": 0.9, "bm25": 0.0}
    return [mk("a.java", 2, "write"), mk("a.java", 1, "A", "class"), mk("b.java", 2, "read")]


def test_same_ranking_first_kept_and_dedupe():
    r = _ranked()
    m = pack_ranked(r, DISK, 2000, "multi")
    o = pack_ranked(r, DISK, 2000, "one_per_file")
    assert m["symbols"][0]["name"] == o["symbols"][0]["name"] == "write"
    dup = [r[0], dict(r[0]), r[2]]
    for pol in ("one_per_file", "multi", "expanded"):
        p = pack_ranked(dup, DISK, 2000, pol, decls={})
        assert len(p["symbols"]) == 2  # span idêntico nunca duplica


def test_one_per_file_caps_while_multi_keeps_both():
    r = _ranked()
    m = pack_ranked(r, DISK, 2000, "multi")
    o = pack_ranked(r, DISK, 2000, "one_per_file")
    assert len(m["symbols"]) == 3 and len(o["symbols"]) == 2
    assert len({s["file"] for s in o["symbols"]}) == len(o["symbols"])
    assert all(v <= 2000 for v in (m["used"], o["used"]))


def test_expanded_adds_decl_context_and_budget_holds():
    r = [{"name": "write", "kind": "method", "file": "a.java", "line": 2,
          "provenance": "t", "confidence": 0.9, "bm25": 0.0}]
    decls = {"a.java": [(1, "class", "A")]}
    m = pack_ranked(r, DISK, 2000, "multi")
    e = pack_ranked(r, DISK, 2000, "expanded", decls=decls)
    assert len(m["symbols"]) == 1 and len(e["symbols"]) == 2
    assert e["symbols"][1]["name"] == "A" and e["excerpts"][1]["id"] == "e0d"
    ids = {x["id"] for x in e["excerpts"]}
    assert all(c["excerpt_id"] in ids for c in e["citations"])
    assert e["used"] >= m["used"] and e["used"] <= 2000
    again = pack_ranked(r, DISK, 2000, "expanded", decls=decls)
    assert e["used"] == again["used"] and [s["name"] for s in e["symbols"]] == \
        [s["name"] for s in again["symbols"]]


def test_capsule_packing_param_backward_compat(tmp_path):
    f1 = tmp_path / "Foo.java"
    f1.write_bytes(b"public class Foo {\n public void write() {}\n public void read() {}\n}\n")
    con = open_db(tmp_path / "p.sqlite")
    index_file(con, f1, "test-sha")
    rebuild_lexical(con)
    default = build_capsule(con, "Foo write", 2000)
    multi = build_capsule(con, "Foo write", 2000, packing="multi")
    one = build_capsule(con, "Foo write", 2000, packing="one_per_file")
    exp = build_capsule(con, "Foo write", 2000, packing="expanded")
    assert [s["name"] for s in default["symbols"]] == [s["name"] for s in multi["symbols"]]
    assert len({s["file"] for s in one["symbols"]}) == len(one["symbols"]) or not one["symbols"]
    assert exp["telemetry"]["delivered"] >= multi["telemetry"]["delivered"]
    for c in (default, multi, one, exp):
        assert c["budget"]["used"] <= 2000
        ids = {e["id"] for e in c["excerpts"]}
        assert all(x["excerpt_id"] in ids for x in c["citations"])
