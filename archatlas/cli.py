# SPDX-License-Identifier: Apache-2.0
"""CLI v0.2 — verify + index + find (F4), tudo sobre o índice SQLite."""
from __future__ import annotations
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))


def main() -> int:
    ap = argparse.ArgumentParser(prog="archatlas")
    ap.add_argument("cmd", choices=["verify", "index", "find"], help="comando")
from archatlas.config import dataset_root
    ap.add_argument("--dataset", default=None, help="raiz do dataset (default: $ARCHATLAS_DATASET ou ../siga)")
    ap.add_argument("--db", default="/tmp/opencode/archatlas.sqlite")
    ap.add_argument("--name", default="ExMovimentacao")
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
    con = open_db(pathlib.Path(args.db))
    if args.cmd == "index":
        paths = sorted((ds / "siga-ex/src/main/java").rglob("*.java"))
        print(index_many(con, paths, "e3be22828"))
        return 0
    rows = find_symbol(con, args.name) or find_references(con, args.name)[:20]
    for r in rows:
        print(f"{r['file']}:{r['line']} {r.get('kind', 'ref')} {r['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
