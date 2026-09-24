# SPDX-License-Identifier: Apache-2.0
"""F14: escala real — full 504 arqs, p50/p95, tamanho, incremental 10/100 vs rebuild (cópias tmp, dataset intacto)."""
import json
import pathlib
import shutil
import sqlite3
import time

from archatlas.lexical import rebuild_lexical
from archatlas.store import index_many, open_db
from archatlas.strategies import s_router

DS = pathlib.Path("/home/iiii/PESSOAL-PROJETOS-ALEXANDRE/siga/siga-ex/src/main/java")
SHA = "e3be22828f787cbe71b339aecb7a7bf569099803"
DEV = pathlib.Path("benchmarks/siga/queries_dev.json")


def _mirror(tmp_path: pathlib.Path, n: int) -> list[pathlib.Path]:
    src = sorted(DS.rglob("*.java"))[:n]
    d = tmp_path / f"m{n}"
    d.mkdir(exist_ok=True)
    return [shutil.copy(f, d / f.name) for f in src]


def test_full_scale_and_incremental(tmp_path):
    files = _mirror(tmp_path, 504)
    assert len(files) == 504
    db = tmp_path / "full.sqlite"
    con = open_db(db)
    t0 = time.perf_counter()
    counts = index_many(con, files, SHA)
    rebuild_lexical(con)
    full_s = time.perf_counter() - t0
    size_kb = db.stat().st_size // 1024
    assert counts["indexed"] == 504
    qs = json.loads(DEV.read_text(encoding="utf-8"))
    dts = []
    for q in qs:
        s = time.perf_counter()
        s_router(con, q["query"])
        dts.append(time.perf_counter() - s)
    dts.sort()
    p50, p95 = dts[len(dts) // 2], dts[int(0.95 * len(dts))]
    rep = {"files": 504, "full_index_s": round(full_s, 2), "db_kb": size_kb,
           "router_p50_s": round(p50, 4), "router_p95_s": round(p95, 4)}
    (tmp_path / "perf.json").write_text(json.dumps(rep, indent=1))
    print("\n" + json.dumps(rep, indent=1))
    assert full_s < 60 and p95 < 0.5
    for n in (10, 100):
        for f in files[:n]:
            f.write_bytes(f.read_bytes() + b"\n// touch\n")
        s = time.perf_counter()
        c = index_many(con, files, SHA)
        dt = time.perf_counter() - s
        assert c["indexed"] == n and c["skipped"] == 504 - n
        print(f"incremental-{n}: {dt:.2f}s vs full {full_s:.2f}s")
        assert dt < full_s
