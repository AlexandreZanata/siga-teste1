# SPDX-License-Identifier: Apache-2.0
"""E26-06: doctor/context com diagnóstico honesto; legados preservados. Offline."""
import json
import pathlib
import sqlite3
import sys

import pytest

from archatlas.cli import main as cli_main
from archatlas.doctor import (check_env, index_state, language_support,
                              uninstall)
from archatlas.store import index_many, open_db, stable_hash
from archatlas.verify import verify_symbol


@pytest.fixture()
def proj(tmp_path):
    d = tmp_path / "proj"
    d.mkdir()
    (d / "A.java").write_bytes(b"public class A {\n public void m() {}\n}\n")
    db = tmp_path / "i.sqlite"
    con = open_db(db)
    index_many(con, sorted(d.rglob("*.java")), "t")
    con.close()
    return d, db


def _run(monkeypatch, capsys, *argv):
    monkeypatch.setattr(sys, "argv", ["archatlas", *argv])
    rc = cli_main()
    out = capsys.readouterr().out
    return rc, (json.loads(out) if out.strip() else None)


def test_doctor_states_and_support(tmp_path, proj):
    _, db = proj
    assert index_state(tmp_path / "nope.sqlite")["state"] == "missing"
    assert index_state(db)["state"] == "ok"
    bad = tmp_path / "bad.sqlite"
    bad.write_bytes(b"nao-sqlite")
    assert index_state(bad)["state"] == "corrupt"
    inc = tmp_path / "inc.sqlite"
    con = open_db(inc)
    con.execute("PRAGMA user_version=99")
    con.commit()
    con.close()
    assert index_state(inc)["state"] == "incompatible"
    assert language_support("java")["level"] == "structural"
    assert language_support("jsp")["level"] == "lexical-fallback"
    assert check_env()["needs_gpu"] is False


def test_context_schema_cost_and_fallback(tmp_path, monkeypatch, capsys, proj):
    _, db = proj
    rc, d = _run(monkeypatch, capsys, "context", "--db", str(db),
                 "--query", "classe A", "--budget", "2000")
    assert rc == 0 and d["schema"] == "atlas-context/1"
    assert d["refs"] and d["schema_overhead_tokens"] >= 1
    assert d["budget"]["used"] <= 2000 and d["state"] in ("ok", "partial")
    r0 = d["refs"][0]
    raw = pathlib.Path(r0["file"]).read_bytes()
    import hashlib
    assert verify_symbol({"name": r0["symbol"], "file": r0["file"],
                          "line": r0["line"],
                          "content_hash": hashlib.sha256(raw).hexdigest()})[0] is True
    rc, d = _run(monkeypatch, capsys, "context", "--db",
                 str(tmp_path / "nope.sqlite"), "--query", "x")
    assert rc == 2 and d["state"] == "missing" and d["refs"] == []
    assert not (tmp_path / "nope.sqlite").exists()  # sem resíduo enganoso


def test_uninstall_cleans_only_index_and_legados_kept(tmp_path, monkeypatch, capsys, proj):
    d, db = proj
    h0 = stable_hash(open_db(db))
    idx = tmp_path / "idx"
    idx.mkdir()
    (idx / "x.sqlite").write_bytes(b"z")
    assert uninstall(str(idx))["removed"] is True and not idx.exists()
    assert stable_hash(open_db(db)) == h0  # código intocado
    monkeypatch.setattr(sys, "argv", ["archatlas", "find", "--db", str(db), "--name", "A"])
    assert cli_main() == 0
    assert "A.java" in capsys.readouterr().out  # legado preservado
