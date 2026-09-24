# SPDX-License-Identifier: Apache-2.0
"""CLI v0.2 — verify + index + find (F4), tudo sobre o índice SQLite."""
from __future__ import annotations
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))


def main() -> int:
    ap = argparse.ArgumentParser(prog="archatlas")
    ap.add_argument("cmd", choices=["verify", "index", "find", "doctor", "context"],
                    help="comando")
    from archatlas.config import dataset_root
    ap.add_argument("--dataset", default=None, help="raiz do dataset (default: $ARCHATLAS_DATASET ou ../siga)")
    ap.add_argument("--db", default="/tmp/opencode/archatlas.sqlite")
    ap.add_argument("--name", default="ExMovimentacao")
    ap.add_argument("--query", default="")
    ap.add_argument("--budget", type=int, default=2000)
    args = ap.parse_args()
    ds = pathlib.Path(args.dataset) if args.dataset else dataset_root()
    if args.cmd == "verify":
        from archatlas.extract import extract_java_symbols
        from archatlas.verify import verify_symbol
        anchor = ds / "siga-ex/src/main/java/br/gov/jfrj/siga/ex/ExMovimentacao.java"
        syms = extract_java_symbols(anchor)
        bad = [s for s in syms if not verify_symbol(s)[0]]
        print(f"símbolos: {len(syms)}, não-verificados: {len(bad)}")
        return 1 if bad else 0
    from archatlas.query import find_references, find_symbol
    from archatlas.store import index_many, open_db
    import sqlite3 as _sqlite3
    db_path = pathlib.Path(args.db)
    db_preexisted = db_path.exists()  # open_db cria arquivo vazio: registrar antes
    if args.cmd in ("doctor", "context") and not db_preexisted:
        import json as _json
        from archatlas.doctor import check_env
        advice = "rode archatlas index; ou use leitura/busca direta"
        if args.cmd == "doctor":
            print(_json.dumps({"env": check_env(),
                               "index": {"state": "missing", "db": str(db_path),
                                         "advice": advice}}, ensure_ascii=False))
        else:
            print(_json.dumps({"state": "missing", "advice": advice,
                               "refs": [], "omitted": "diagnostico, sem resultado"},
                              ensure_ascii=False))
        return 2
    try:
        con = open_db(db_path)
    except _sqlite3.DatabaseError:
        import json as _json
        if args.cmd in ("doctor", "context"):
            if args.cmd == "doctor":
                from archatlas.doctor import check_env
                print(_json.dumps({"env": check_env(),
                                   "index": {"state": "corrupt", "db": str(db_path),
                                             "advice": "arquivo não é SQLite válido; apague e reindexe, ou use busca direta"}},
                                  ensure_ascii=False))
            else:
                print(_json.dumps({"state": "corrupt",
                                   "advice": "arquivo não é SQLite válido; apague e reindexe, ou use busca direta",
                                   "refs": [], "omitted": "diagnostico, sem resultado"},
                                  ensure_ascii=False))
            return 2
        raise
    if args.cmd == "index":
        paths = sorted((ds / "siga-ex/src/main/java").rglob("*.java"))
        print(index_many(con, paths, "e3be22828"))
        return 0
    if args.cmd == "find":
        rows = find_symbol(con, args.name) or find_references(con, args.name)[:20]
        for r in rows:
            print(f"{r['file']}:{r['line']} {r.get('kind', 'ref')} {r['name']}")
        return 0
    if args.cmd == "doctor":
        import json as _json
        from archatlas.doctor import check_env, index_state
        st = index_state(db_path)
        print(_json.dumps({"env": check_env(), "index": st}, indent=1,
                          ensure_ascii=False))
        return 0 if st["state"] == "ok" else 2
    if args.cmd == "context":
        import json as _json
        from archatlas.capsule import build_capsule
        from archatlas.doctor import index_state as _st
        st = _st(db_path)
        if st.get("state") == "ok" and st.get("files", 0) == 0:
            st = {"state": "empty",
                  "advice": "índice vazio; indexe arquivos ou use busca direta"}
        if st["state"] != "ok":
            print(_json.dumps({"state": st["state"], "advice": st.get("advice"),
                               "refs": [], "omitted": "diagnostico, sem resultado"},
                              ensure_ascii=False))
            return 2  # fallback: diagnóstico, nunca lista vazia fingida
        cap = None
        healed = False
        try:
            cap = build_capsule(con, args.query, args.budget)
        except _sqlite3.OperationalError:
            from archatlas.lexical import rebuild_lexical as _relex
            tables = {r[0] for r in con.execute(
                "SELECT name FROM sqlite_master").fetchall()}
            if "lex_docs" not in tables:
                _relex(con)  # auto-reparo: índice sem tabela lexical
                healed = True
                cap = build_capsule(con, args.query, args.budget)
            else:
                raise
        snaps = sorted({r[0] for r in con.execute(
            "SELECT DISTINCT commit_sha FROM files").fetchall()})
        refs = [{"file": s["file"], "line": s["line"], "symbol": s["name"],
                 "reason": s.get("reason")} for s in cap["symbols"]]
        texts = [{"file": e["file"], "line": e["start_line"], "text": e["text"]}
                 for e in cap["excerpts"]]
        drops = cap["truncation_log"]
        envelope = {"schema": "atlas-context/1",
                    "snapshot": snaps, "query": args.query,
                    "budget": {"requested": args.budget, "used": cap["budget"]["used"],
                               "tokenizer": "chars//4"},
                    "refs": refs, "texts": texts,
                    "omitted": {"n": len(drops),
                                "rules": sorted({d.get("rule", "?") for d in drops})},
                    "state": "ok" if not drops else "partial",
                    "lexical_healed": healed}
        overhead = max(1, len(_json.dumps({"schema": envelope["schema"],
                                           "snapshot": snaps,
                                           "refs": refs}, ensure_ascii=False)) // 4)
        envelope["schema_overhead_tokens"] = overhead  # custo do schema, contabilizado
        print(_json.dumps(envelope, ensure_ascii=False))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
