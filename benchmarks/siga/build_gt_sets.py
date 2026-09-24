# SPDX-License-Identifier: Apache-2.0
"""GT-conjunto F11: E/G/D passam a aceitar QUALQUER referência verificada no escopo (não só 1 arquivo)."""
from __future__ import annotations
from archatlas.config import REPO_ROOT, as_rel, dataset_root
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from archatlas.query import find_references
from archatlas.store import index_many, open_db

DATASET = dataset_root()
SHA = "e3be22828f787cbe71b339aecb7a7bf569099803"
DEV = pathlib.Path(__file__).resolve().parent / "queries_dev.json"


def main() -> int:
    qs = json.loads(DEV.read_text(encoding="utf-8"))
    files = []
    for rel in ("siga-ex/src/main/java", "siga-cp/src/main/java", "siga-wf/src/main/java"):
        files += sorted((DATASET / rel).rglob("*.java"))
    scope = {str(f) for f in files}
    con = open_db(pathlib.Path(":memory:"))
    index_many(con, files, SHA)
    from archatlas.trace import build_call_index, trace as trace_path
    cidx = build_call_index(files)
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
                    rel = as_rel(r["file"])
                    if r["file"] in scope and rel not in got:
                        assert pathlib.Path(r["file"]).exists()
                        assert nm in pathlib.Path(r["file"]).read_text(
                            encoding="utf-8", errors="replace").splitlines()[r["line"] - 1]
                        got.append(rel)
            if got:
                q["gt"]["files"] = got
                q["gt"].pop("file", None)
                q["gt"].pop("line", None)
                n_sets += 1
        if q["category"] == "H":
            a, _, c = q["gt"]["chain"]
            paths: list[list[dict]] = []

            def dfs(node: str, path: list[dict], seen: set[str]) -> None:
                if node == c and path:
                    paths.append(list(path))
                    return
                if len(path) >= 3:
                    return
                for e in cidx.get(node, []):
                    if e["callee"] not in seen:
                        dfs(e["callee"], path + [e], seen | {e["callee"]})

            dfs(a, [], {a})
            pfiles = sorted({as_rel(e["file"]) for p in paths for e in p})
            if pfiles:
                q["gt"]["path_files"] = [as_rel(f) for f in pfiles]
                q["gt"]["n_paths"] = len(paths)
    json.dump(qs, open(DEV, "w"), indent=1, ensure_ascii=False)
    print(f"questões: {len(qs)}, com GT-conjunto: {n_sets}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
