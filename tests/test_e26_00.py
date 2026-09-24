# SPDX-License-Identifier: Apache-2.0
"""P2/E26-00: medir contexto de verdade — fixtures offline, sem LLM, sem holdout."""
import inspect

from archatlas.capsule import build_capsule
from archatlas.lexical import rebuild_lexical
from archatlas.store import index_file, open_db
from archatlas.telemetry import (build_manifest, payload_tokens_for_capsule,
                                 rescore_runs, score_delivery, verify_replay)
from archatlas.verify import verify_symbol


def test_partial_single_member_not_100():
    sc = score_delivery({"a.java"}, {"files": ["a.java", "b.java", "c.java", "d.java"]})
    assert sc["hit"] is True
    assert sc["recall_set"] == 0.25
    assert sc["recall_set"] < 1.0


def test_precision_with_extra_and_path_coverage():
    sc = score_delivery({"a.java", "b.java", "x.java", "y.java"},
                        {"files": ["a.java", "b.java"]})
    assert sc["recall_set"] == 1.0 and sc["precision_set"] == 0.5
    pc = score_delivery({"p1.java"}, {"path_files": ["p1.java", "p2.java", "p3.java"]})
    assert pc["hit"] is True and pc["recall_set"] == 1 / 3


def test_package_never_claims_complete_and_empty_no_crash():
    sc = score_delivery({"m/Foo.java"}, {"package": "m/", "file": "m/Foo.java"})
    assert sc["hit"] is True
    assert sc["recall_set"] is None and sc["precision_set"] is None
    e1 = score_delivery(set(), {"files": ["a.java", "b.java"]})
    assert e1 == {**e1, "hit": False} and e1["recall_set"] == 0.0 and e1["precision_set"] == 0.0
    e2 = score_delivery({"a.java"}, {"files": []})
    assert e2["hit"] is False and e2["error"] == "gt-vazio"
    e3 = score_delivery({"a.java"}, {})
    assert e3["hit"] is False and e3["error"] == "gt-vazio"


def _tiny_db(tmp_path):
    f1 = tmp_path / "Foo.java"
    f1.write_bytes(b"public class Foo {\n public void write() {}\n}\n")
    f2 = tmp_path / "Bar.java"
    f2.write_bytes(b"public class Bar {\n public void read() {}\n}\n")
    con = open_db(tmp_path / "t.sqlite")
    index_file(con, f1, "test-sha")
    index_file(con, f2, "test-sha")
    rebuild_lexical(con)
    return con, f1, f2


def test_payload_full_serialization_replay_and_history_separation(tmp_path):
    con, _, _ = _tiny_db(tmp_path)
    c1 = build_capsule(con, "Foo", 2000)
    c2 = build_capsule(con, "Foo", 2000)
    assert c1["payload_tokens"] == c2["payload_tokens"] == payload_tokens_for_capsule(c1)
    assert c1["payload_tokens"] >= c1["budget"]["used"]  # serialização inteira >= soma itens
    assert c1["telemetry"]["retrieved"] >= c1["telemetry"]["delivered"] >= 1
    assert c1["telemetry"]["opened"] == 0
    assert c1["telemetry"]["declared_relevant"] is None
    assert c1["telemetry"]["history_tokens"] is None
    assert "history" not in c1["telemetry"].get("history_note", "history")
    runs = [{"delivered": set(c1["telemetry"]["delivered_files"]),
             "gt": {"files": list(c1["telemetry"]["delivered_files"])[:1] + ["missing.java"]}}]
    stored = rescore_runs(runs)
    assert stored[0]["hit"] is True and stored[0]["recall_set"] < 1.0
    assert verify_replay(runs, stored) is True
    assert verify_replay(runs, [{**stored[0], "recall_set": 1.0}]) is False


def test_stale_trecho_detected_and_missing_file_no_crash(tmp_path):
    con, f1, _ = _tiny_db(tmp_path)
    row = con.execute("SELECT name, file, line, content_hash FROM symbols WHERE name='Foo'").fetchone()
    sym = {"name": row[0], "file": row[1], "line": row[2], "content_hash": row[3]}
    assert verify_symbol(sym) == (True, "ok")  # bytes reais lidos do disco
    f1.write_bytes(f1.read_bytes() + b"\n// touch\n")
    ok, msg = verify_symbol(sym)
    assert ok is False and "divergiu" in msg  # trecho alterado pós-index detectado
    f1.unlink()  # arquivo some: cápsula registra e segue, sem exceção
    cap = build_capsule(con, "Foo", 2000)
    assert isinstance(cap, dict) and cap["budget"]["used"] <= 2000
    sc = score_delivery(set(), {"file": "gone.java"})
    assert sc["hit"] is False


def test_manifest_pairing_deterministic_and_evaluator_isolated():
    m1 = build_manifest("t1", "C", 1, 0, 2000, "e3be22828")
    m2 = build_manifest("t1", "C", 1, 0, 2000, "e3be22828")
    m3 = build_manifest("t1", "C", 1, 1, 2000, "e3be22828")
    assert m1 == m2 and m1 != m3
    assert inspect.signature(score_delivery).parameters.keys() == {"delivered", "gt"}
