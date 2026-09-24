# SPDX-License-Identifier: Apache-2.0
"""Gera categoria H (multi-hop 2 saltos) de cadeias calls reais; GT = 2 arestas verificadas."""
from __future__ import annotations
from archatlas.config import REPO_ROOT, as_rel, dataset_root
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from archatlas.trace import build_call_index

DATASET = dataset_root()
DEV = pathlib.Path(__file__).resolve().parent / "queries_dev.json"


def main() -> int:
    qs = json.loads(DEV.read_text(encoding="utf-8"))
    files = sorted((DATASET / "siga-ex/src/main/java").rglob("*.java"))[:40]
    idx = build_call_index(files)
    seen, n = set(), 0
    for a in sorted(idx):
        for e in sorted(idx[a], key=lambda x: (x["callee"], x["line"])):
            for e2 in sorted(idx.get(e["callee"], []), key=lambda x: (x["callee"], x["line"])):
                key = (a, e["callee"], e2["callee"])
                if key in seen or e2["callee"] == a:
                    continue
                for edge in (e, e2):
                    txt = pathlib.Path(edge["file"]).read_text(
                        encoding="utf-8", errors="replace").splitlines()[edge["line"] - 1]
                    assert edge["callee"] in txt, edge
                seen.add(key)
                qs.append({"id": f"H-{n:03d}", "category": "H",
                           "query": f"Qual caminho verificado liga {a} a {e2['callee']} via {e['callee']}?",
                           "gt": {"chain": [a, e["callee"], e2["callee"]],
                                  "edges": [{"file": as_rel(e["file"]), "line": e["line"]},
                                            {"file": as_rel(e2["file"]), "line": e2["line"]}]}})
                n += 1
                if n >= 8:
                    break
            if n >= 8:
                break
        if n >= 8:
            break
    assert n == 8, n
    json.dump(qs, open(DEV, "w"), indent=1, ensure_ascii=False)
    print("H:", n, "total:", len(qs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
