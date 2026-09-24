# SPDX-License-Identifier: Apache-2.0
"""Gera queries_dev.json SOMENTE de fatos lidos do disco (falha alto se não achar)."""
from __future__ import annotations
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from archatlas.extract import extract_java_symbols
from archatlas.query import find_references
from archatlas.store import index_many, open_db

DATASET = pathlib.Path("/home/iiii/PESSOAL-PROJETOS-ALEXANDRE/siga")
SHA = "e3be22828f787cbe71b339aecb7a7bf569099803"
OUT = pathlib.Path(__file__).resolve().parent / "queries_dev.json"


def main() -> int:
    java_files = sorted((DATASET / "siga-ex/src/main/java").rglob("*.java"))[:40]
    con = open_db(pathlib.Path(":memory:"))
    index_many(con, java_files, SHA)
    classes = [r for r in con.execute(
        "SELECT name, file, line FROM symbols WHERE kind='class' ORDER BY file").fetchall()]
    qs: list[dict] = []
    for i, (name, f, line) in enumerate(classes[:20]):
        assert pathlib.Path(f).exists(), f"GT inexistente: {f}"
        assert name in pathlib.Path(f).read_text(encoding="utf-8", errors="replace").splitlines()[line - 1]
        qs.append({"id": f"A-{i:03d}", "category": "A",
                   "query": f"Em qual arquivo está definida a classe {name}?",
                   "gt": {"file": f, "line": line}})
        qs.append({"id": f"B-{i:03d}", "category": "B",
                   "query": f"Qual módulo contém a classe {name}?",
                   "gt": {"module": "siga-ex", "file": f}})
        refs = find_references(con, name)
        if refs:
            qs.append({"id": f"D-{i:03d}", "category": "D",
                       "query": f"Cite um arquivo que referencia {name}.",
                       "gt": {"file": refs[0]["file"], "line": refs[0]["line"]}})
    cats = {q["category"] for q in qs}
    assert len(qs) >= 50, f"só {len(qs)} questões"
    assert {"A", "B", "D"} <= cats
    OUT.write_text(json.dumps(qs, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"questões: {len(qs)} categorias: {sorted(cats)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
