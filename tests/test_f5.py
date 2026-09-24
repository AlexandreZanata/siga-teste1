# SPDX-License-Identifier: Apache-2.0
"""F5: BM25 encontra a classe âncora; cápsula respeita budget hard; GT 100% verificado."""
import json
import pathlib
import shutil

from archatlas.capsule import build_capsule
from archatlas.lexical import bm25_search, rebuild_lexical
from archatlas.store import index_many, open_db

A = pathlib.Path("/home/iiii/PESSOAL-PROJETOS-ALEXANDRE/siga/siga-ex/src/main/java/br/gov/jfrj/siga/ex/ExMovimentacao.java")
B = pathlib.Path("/home/iiii/PESSOAL-PROJETOS-ALEXANDRE/siga/siga-ex/src/main/java/br/gov/jfrj/siga/ex/vo/ExMobilVO.java")
SHA = "e3be22828f787cbe71b339aecb7a7bf569099803"
DEV = pathlib.Path("benchmarks/siga/queries_dev.json")


def _db(tmp_path):
    d = tmp_path / "w"
    d.mkdir()
    files = []
    for i, src in enumerate([A, B]):
        dst = d / f"F{i}.java"
        shutil.copy(src, dst)
        files.append(dst)
    con = open_db(tmp_path / "l.sqlite")
    index_many(con, files, SHA)
    rebuild_lexical(con)
    return con


def test_bm25_finds_anchor(tmp_path):
    con = _db(tmp_path)
    hits = bm25_search(con, "ExMovimentacao", k=10)
    assert hits and hits[0]["name"] == "ExMovimentacao"


def test_capsule_budget_hard_and_citations_closed(tmp_path):
    con = _db(tmp_path)
    kept = {}
    for budget in (500, 2000, 32000):
        cap = build_capsule(con, "onde está ExMovimentacao", budget)
        assert cap["budget"]["used"] <= budget
        for s in cap["symbols"]:
            assert {"provenance", "reason", "score"} <= set(s)
        ids = {e["id"] for e in cap["excerpts"]}
        for c in cap["citations"]:
            assert c["excerpt_id"] in ids
        kept[budget] = cap["stats"]["kept"]
    assert kept[500] <= kept[32000]


def test_benchmark_gt_verified():
    qs = json.loads(DEV.read_text(encoding="utf-8"))
    assert len(qs) >= 100
    assert {"A", "B", "C", "D", "E", "F", "G"} <= {q["category"] for q in qs}
    for q in qs:
        gt = q["gt"]
        files = gt.get("files", [gt["file"]] if "file" in gt else [])
        assert files, q["id"]
        for f in files:
            assert pathlib.Path(f).exists(), (q["id"], f)
