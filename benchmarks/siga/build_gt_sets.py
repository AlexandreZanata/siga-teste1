# SPDX-License-Identifier: Apache-2.0
"""GT-conjunto F11: E/G/D passam a aceitar QUALQUER referência verificada no escopo (não só 1 arquivo)."""
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


def main() -> int:
    qs = json.loads(DEV.read_text(encoding="utf-8"))
    files = sorted((DATASET / "siga-ex/src/main/java").rglob("*.java"))[:40]
    scope = {str(f) for f in files}
    con = open_db(pathlib.Path(":memory:"))
    index_many(con, files, SHA)
    n_sets = 0
    for q in qs:
        if q["category"] in ("E", "G", "D"):
            key = q["gt"].get("callee") or q["query"].split()[-1].strip("?.")
            names = [key]
            if q["category"] == "D":
                names = [q["query"].split("referencia ")[-1].strip("?.")]
            got: list[str] = []
            for nm in names:
                for r in find_references(con, nm):
                    if r["file"] in scope and r["file"] not in got:
                        assert pathlib.Path(r["file"]).exists()
                        assert nm in pathlib.Path(r["file"]).read_text(
                            encoding="utf-8", errors="replace").splitlines()[r["line"] - 1]
                        got.append(r["file"])
            if got:
                q["gt"]["files"] = got
                q["gt"].pop("file", None)
                q["gt"].pop("line", None)
                n_sets += 1
    json.dump(qs, open(DEV, "w"), indent=1, ensure_ascii=False)
    print(f"questões: {len(qs)}, com GT-conjunto: {n_sets}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
