# SPDX-License-Identifier: Apache-2.0
"""Estende queries_dev.json com C/E/F/G — GT só de arestas/linhas lidas (falha alto se ausente)."""
from __future__ import annotations
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from archatlas.calls import extract_calls
from archatlas.query import find_references
from archatlas.store import index_many, open_db

DATASET = pathlib.Path("/home/iiii/PESSOAL-PROJETOS-ALEXANDRE/siga")
SHA = "e3be22828f787cbe71b339aecb7a7bf569099803"
OUT = pathlib.Path(__file__).resolve().parent / "queries_dev.json"


def main() -> int:
    qs = json.loads(OUT.read_text(encoding="utf-8"))
    have = {q["id"] for q in qs}
    files = sorted((DATASET / "siga-ex/src/main/java").rglob("*.java"))[:40]
    con = open_db(pathlib.Path(":memory:"))
    index_many(con, files, SHA)
    edges = []
    for f in files:
        edges += [(c["caller"], c["callee"], c["file"], c["line"]) for c in extract_calls(f)]
    edges.sort(key=lambda e: (e[0], e[1], e[2], e[3]))
    n_c = n_e = n_f = n_g = 0
    for caller, callee, f, line in edges:
        if n_c >= 10 and n_e >= 10 and n_f >= 10 and n_g >= 10:
            break
        txt = pathlib.Path(f).read_text(encoding="utf-8", errors="replace").splitlines()[line - 1]
        assert callee in txt, (callee, f, line)
        if n_c < 10:
            qs.append({"id": f"C-{n_c:03d}", "category": "C",
                       "query": f"Em qual arquivo/linha o método {caller} chama {callee}?",
                       "gt": {"file": f, "line": line, "caller": caller, "callee": callee}})
            n_c += 1
        refs = [r for r in find_references(con, callee) if r["file"] != f][:2]
        if refs and n_e < 10:
            qs.append({"id": f"E-{n_e:03d}", "category": "E",
                       "query": f"Cite um caller de {callee} (quem o chama e onde).",
                       "gt": {"file": refs[0]["file"], "line": refs[0]["line"], "callee": callee}})
            n_e += 1
        if refs and n_g < 10:
            qs.append({"id": f"G-{n_g:03d}", "category": "G",
                       "query": f"Se {callee} mudar, cite um arquivo que precisaria revisão.",
                       "gt": {"files": [r["file"] for r in refs], "callee": callee}})
            n_g += 1
        pkg = str(pathlib.Path(f).parent).replace(str(DATASET) + "/", "")
        if n_f < 10:
            qs.append({"id": f"F-{n_f:03d}", "category": "F",
                       "query": f"Em qual pacote (diretório) está o método {caller}?",
                       "gt": {"package": pkg, "file": f}})
            n_f += 1
    cats = {q["category"] for q in qs}
    assert {"A", "B", "C", "D", "E", "F", "G"} <= cats, cats
    assert len(qs) >= 100, len(qs)
    OUT.write_text(json.dumps(qs, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"questões: {len(qs)} categorias: {sorted(cats)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
