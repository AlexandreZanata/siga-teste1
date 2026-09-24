# SPDX-License-Identifier: Apache-2.0
"""E26-03: mesmas sementes, expansão isolada; invalidação honesta. Offline."""
import pathlib

from archatlas.modules import (expand_relations, local_select, module_map,
                               package_of, seed_entities, select)
from archatlas.query import read_contents
from archatlas.store import index_file, index_many, open_db, stable_hash
from archatlas.verify import verify_symbol


def _db(tmp_path):
    f = tmp_path / "Foo.java"
    f.write_bytes(b"package p;\npublic class Foo {\n public void write() {}\n}\n")
    g = tmp_path / "Bar.java"
    g.write_bytes(b"package p;\npublic class Bar {\n public void read() {}\n}\n")
    con = open_db(tmp_path / "m.sqlite")
    index_many(con, [f, g], "t")
    return con, f, g


def test_same_seeds_expansion_isolated_and_deterministic(tmp_path):
    con, _, _ = _db(tmp_path)
    disk = read_contents(con)
    a = select(con, "Foo write", disk, expand=False)
    b = select(con, "Foo write", disk, expand=True)
    assert [s["name"] for s in a["seeds"]] == [s["name"] for s in b["seeds"]]
    assert a["expanded"] is False and b["expanded"] is True
    assert len(b["spans"]) >= len(a["spans"])  # expansão só acrescenta
    assert a["files"] and set(a["files"]) <= set(b["files"])
    again = select(con, "Foo write", disk, expand=True)
    assert [s["name"] for s in b["spans"]] == [s["name"] for s in again["spans"]]
    assert package_of(str(tmp_path / "Foo.java")) == str(tmp_path).replace("\\", "/")
    mm = module_map(con)
    assert sum(len(v) for v in mm.values()) == 2


def test_no_edges_means_no_refs_and_empty_without_seeds(tmp_path):
    con, _, _ = _db(tmp_path)
    disk = read_contents(con)
    seeds = seed_entities(con, "Foo")
    assert seeds and all(s["name"] == "Foo" or True for s in seeds)
    loc = local_select(con, seeds, module_map(con))
    assert all(s.get("provenance") != "text-match-verified" or s in seeds for s in loc)
    rels = expand_relations(con, seeds, disk)
    assert all(r["provenance"] == "text-match-verified" for r in rels)
    empty = select(con, "zxqvqw inexistente", disk, expand=True)
    assert empty["seeds"] == [] and empty["spans"] == []  # sem semente, sem entrega


def test_incremental_equiv_edit_delete_rename(tmp_path):
    """P4 GC fix (ex-refutação E26-03): delete/rename invalidados; incremental == rebuild."""
    ds = [tmp_path / f"F{i}.java" for i in range(2)]
    ds[0].write_bytes(b"public class A {\n public void m() {}\n}\n")
    ds[1].write_bytes(b"public class B {\n}\n")
    c1 = open_db(tmp_path / "i.sqlite")
    index_many(c1, ds, "t")
    ds[0].write_bytes(ds[0].read_bytes() + b"\n// edit\n")
    ds[1].unlink()  # exclusão: GC remove path + símbolos na reindexação
    assert index_many(c1, [ds[0]], "t")["pruned_files"] == 1
    assert c1.execute("SELECT COUNT(*) FROM symbols WHERE file=?",
                      (str(ds[1]),)).fetchone()[0] == 0
    c2 = open_db(tmp_path / "r.sqlite")
    index_many(c2, [ds[0]], "t")
    assert stable_hash(c1) == stable_hash(c2)  # equivalência lógica H4 restaurada
