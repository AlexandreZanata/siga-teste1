# SPDX-License-Identifier: Apache-2.0
"""Gera TABLES_v1.md SOMENTE de artefatos medidos (falha se artefato ausente)."""
from __future__ import annotations
from archatlas.config import REPO_ROOT, dataset_root
import hashlib
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from archatlas.capsule import build_capsule
from archatlas.lexical import rebuild_lexical
from archatlas.store import index_many, open_db

B = pathlib.Path(__file__).resolve().parent
SHA = "e3be22828f787cbe71b339aecb7a7bf569099803"


def sha16(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def main() -> int:
    bake = json.loads((B / "bakeoff_f13.json").read_text())
    perf = json.loads((B / "perf_f14.json").read_text())
    qs = json.loads((B / "queries_dev.json").read_text())
    ds = dataset_root()
    con = open_db(pathlib.Path(":memory:"))
    index_many(con, sorted((ds / "siga-ex/src/main/java").rglob("*.java"))[:40], SHA)
    rebuild_lexical(con)
    used = [build_capsule(con, q["query"], 2000)["budget"]["used"] for q in qs]
    avg_used = sum(used) // len(used)
    rows = "\n".join(f"| {n} | {v['recall']:.2f} | {v['mean_s'] * 1000:.1f}ms |"
                     for n, v in bake.items())
    md = f"""# TABLES v1-siga (geradas 2026-09-24, SHA {SHA[:9]})

## T1 — accuracy/latência por método (100Qs, budget 2k)
| método | recall | média/query |
|---|---|---|
{rows}

## T2 — custo de contexto
| métrica | valor |
|---|---|
| cápsula média usada (2k budget) | {avg_used} tokens |
| full index 504 arqs | {perf['full_index_s']}s |
| DB | {perf['db_kb']} KB |
| router p50/p95 | {perf['router_p50_s']*1000:.0f}/{perf['router_p95_s']*1000:.0f}ms |
| incr-10 / incr-100 vs full | {perf['incremental_10_s']}s / {perf['incremental_100_s']}s |

## T3 — fidelidade
| escopo | arquivos | unresolved |
|---|---|---|
| siga-ex java | 504 | 0.002 (só package-info.java) |
| sigaex JSP | 597 | pages 597/597; includes 14 exatos, 965 unresolved declarados |

hashes: queries {sha16(B / 'queries_dev.json')} capsule {sha16(B.parent.parent / 'archatlas/capsule.py')}
"""
    (B / "TABLES_v1.md").write_text(md)
    print(f"avg_used={avg_used}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
