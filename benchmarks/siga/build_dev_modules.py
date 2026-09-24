# SPDX-License-Identifier: Apache-2.0
"""Questões A/B/D de siga-cp + siga-wf (GT verificado; ids com sufixo de módulo)."""
from __future__ import annotations
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from archatlas.query import find_references
from archatlas.store import index_many, open_db

DATASET = pathlib.Path("/home/iiii/PESSOAL-PROJETOS-ALEXANDRE/siga")
SHA = "e3be22828f787cbe71b339aecb7a7bf569099803"
DEV = pathlib.Path(__file__).resolve().parent / "queries_dev.json"
MODS = {"siga-cp": "siga-cp/src/main/java", "siga-wf": "siga-wf/src/main/java"}


def main() -> int:
    qs = json.loads(DEV.read_text(encoding="utf-8"))
    n = 0
    for mod, rel in MODS.items():
        files = sorted((DATASET / rel).rglob("*.java"))
        con = open_db(pathlib.Path(":memory:"))
        index_many(con, files, SHA)
        classes = [r for r in con.execute(
            "SELECT name, file, line FROM symbols WHERE kind='class' ORDER BY file").fetchall()][:8]
        for name, f, line in classes:
            assert pathlib.Path(f).exists()
            assert name in pathlib.Path(f).read_text(encoding="utf-8", errors="replace").splitlines()[line - 1]
            tag = f"{mod.replace('siga-', '')}-{n:03d}"
            qs.append({"id": f"A-{tag}", "category": "A",
                       "query": f"Em qual arquivo está definida a classe {name}?",
                       "gt": {"file": f, "line": line}})
            qs.append({"id": f"B-{tag}", "category": "B",
                       "query": f"Qual módulo contém a classe {name}?",
                       "gt": {"module": mod, "file": f}})
            refs = [r for r in find_references(con, name) if r["file"] != f][:3]
            if refs:
                qs.append({"id": f"D-{tag}", "category": "D",
                           "query": f"Cite um arquivo que referencia {name}.",
                           "gt": {"files": [r["file"] for r in refs]}})
            n += 1
    from collections import Counter
    print(Counter(x["category"] for x in qs), len(qs))
    json.dump(qs, open(DEV, "w"), indent=1, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
