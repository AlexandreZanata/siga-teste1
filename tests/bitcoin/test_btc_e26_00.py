# SPDX-License-Identifier: Apache-2.0
"""BTC-E26-00 sintético: medir contexto de verdade em fixtures próprias.

Espelho do método E26-00 (hit vs recall_set, payload inteiro, replay, stale)
com dados sintéticos C++/Python independentes. Sem LLM, sem holdout, sem dataset.
"""
import inspect

from archatlas.bitcoin.cpp_lex import extract_cpp_lexical, verify_fact
from archatlas.telemetry import (payload_tokens_for_capsule, rescore_runs,
                                 score_delivery, verify_replay)


def test_partial_single_member_not_100():
    sc = score_delivery({"src/validation.cpp"},
                        {"files": ["src/validation.cpp", "src/validation.h",
                                   "test/validation_tests.cpp"]})
    assert sc["hit"] is True
    assert sc["recall_set"] == 1 / 3 < 1.0


def test_alternatives_require_full_set_for_full_recall():
    gt = {"files": ["src/net.h", "src/net.cpp"]}
    assert score_delivery({"src/net.cpp"}, gt)["recall_set"] == 0.5
    assert score_delivery({"src/net.h", "src/net.cpp"}, gt)["recall_set"] == 1.0


def test_path_complete_requires_edge_files():
    gt = {"path_files": ["src/init.cpp", "src/validation.cpp", "src/mempool.cpp"],
          "edges": [{"file": "src/validation.cpp"}]}
    full = score_delivery(set(gt["path_files"]), gt)
    assert full["hit"] is True and full["recall_set"] == 1.0
    no_edge = score_delivery({"src/init.cpp", "src/mempool.cpp"}, gt)
    assert no_edge["hit"] is False  # nós sem o arquivo da aresta não bastam


def test_stale_and_removed_detected_no_crash(tmp_path):
    p = tmp_path / "chain.cpp"
    p.write_bytes(b'#include "chain.h"\n')
    facts = extract_cpp_lexical(p)["facts"]
    assert all(verify_fact(f) == (True, "ok") for f in facts)
    p.write_bytes(b'#include "chain.h"\n#include <vector>\n')
    assert verify_fact(facts[1])[0] is False  # mudança pós-índice detectada
    p.unlink()
    assert verify_fact(facts[0]) == (False, "arquivo inexistente")
    sc = score_delivery(set(), {"file": "chain.cpp"})
    assert sc["hit"] is False


def test_payload_whole_serialization_replay_and_evaluator_isolated():
    cap = {"excerpts": [{"file": "src/validation.cpp", "lines": "1-7"}],
           "citations": ["src/validation.cpp:1"],
           "symbols": [{"file": "src/validation.cpp", "line": 1,
                        "kind": "file", "name": "validation.cpp"}]}
    assert payload_tokens_for_capsule(cap) == payload_tokens_for_capsule(cap) > 0
    runs = [{"delivered": {"src/validation.cpp"},
             "gt": {"files": ["src/validation.cpp", "src/validation.h"]}}]
    stored = rescore_runs(runs)
    assert stored[0]["hit"] is True and stored[0]["recall_set"] == 0.5
    assert verify_replay(runs, stored) is True
    assert verify_replay(runs, [{**stored[0], "recall_set": 1.0}]) is False
    assert set(inspect.signature(score_delivery).parameters) == {"delivered", "gt"}
