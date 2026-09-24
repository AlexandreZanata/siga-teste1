# SPDX-License-Identifier: Apache-2.0
"""CLI v0.1 — verify dataset + extração com evidência."""
from __future__ import annotations
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))


def main() -> int:
    ap = argparse.ArgumentParser(prog="archatlas")
    ap.add_argument("cmd", choices=["verify"], help="verifica âncora real do dataset")
    ap.add_argument("--dataset", default="/home/iiii/PESSOAL-PROJETOS-ALEXANDRE/siga")
    args = ap.parse_args()
    from archatlas.extract import extract_java_symbols
    from archatlas.verify import verify_symbol
    anchor = pathlib.Path(args.dataset) / "siga-ex/src/main/java/br/gov/jfrj/siga/ex/ExMovimentacao.java"
    syms = extract_java_symbols(anchor)
    bad = [s for s in syms if not verify_symbol(s)[0]]
    print(f"símbolos: {len(syms)}, não-verificados: {len(bad)}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
