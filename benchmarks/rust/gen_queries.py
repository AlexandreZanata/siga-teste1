#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Gera o conjunto de consultas de R2: 30 estratificadas, deterministicamente.

Estratificar por frequência de documento é o ponto: uma consulta que casa em 1 arquivo e
outra que casa em 200 custam coisas diferentes, e uma média sobre consultas escolhidas só
numa faixa esconderia isso. São cinco estratos × seis consultas.

A seleção é **reprodutível**, não amostrada: dentro de cada estrato os nomes são ordenados e
seis são tomados em posições igualmente espaçadas. Rodar de novo sobre o mesmo corpus
devolve exatamente as mesmas consultas — sem isso, duas rodadas não seriam comparáveis.

Consultas de borda (zero correspondência, Unicode, multi-token, longa, pontuação) ficam em
lista separada: o protocolo §7 pede que sejam reportadas separadamente, não diluídas na
média.

Uso:
    python benchmarks/rust/gen_queries.py --corpus experiments/rust/siga/<run_id>/corpus.json \
        --out experiments/rust/siga/<run_id>
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

SUBTREE = "siga-ex/src/main/java"
TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{3,}")

# Palavras da linguagem e ruído de sintaxe: casariam em quase todo arquivo e não
# distinguiriam nada além do estrato ">100", que já é coberto de propósito.
STOPWORDS = {
    "public", "private", "protected", "static", "final", "class", "interface", "enum",
    "import", "package", "return", "throws", "extends", "implements", "void", "this",
    "null", "true", "false", "new", "super", "abstract", "synchronized", "native",
    "String", "Object", "Integer", "Long", "Boolean", "List", "Map", "Set", "Override",
    "override", "serialVersionUID", "void", "int", "long", "double", "boolean", "char",
    "float", "byte", "short", "Exception", "throws", "catch", "finally", "while",
}

# (rotulo, minimo, maximo) — limites inclusivos; `None` = sem teto.
STRATA = [
    ("1", 1, 1),
    ("2-5", 2, 5),
    ("6-20", 6, 20),
    ("21-100", 21, 100),
    (">100", 101, None),
]
PER_STRATUM = 6


def tokenize(text: str) -> set[str]:
    return {t for t in TOKEN_RE.findall(text) if t not in STOPWORDS}


def evenly_spaced(names: list[str], k: int) -> list[str]:
    """k nomes em posições igualmente espaçadas de uma lista já ordenada."""
    if not names:
        return []
    if len(names) <= k:
        return list(names)
    step = (len(names) - 1) / (k - 1) if k > 1 else 0
    picked = []
    for i in range(k):
        idx = round(i * step)
        if names[idx] not in picked:
            picked.append(names[idx])
    return picked


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", required=True, help="corpus.json produzido por freeze_corpus.py")
    ap.add_argument("--dataset", default=None)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    corpus = json.loads(Path(args.corpus).read_text())
    dataset = Path(args.dataset or (Path(args.corpus).resolve().parent / ".." / ".." / ".." / ".." / ".." / "siga")).resolve()
    if not (dataset / SUBTREE).is_dir():
        # Fallback: descobrir pela raiz declarada no manifesto do ambiente, se existir.
        candidate = Path(corpus.get("environment", {}).get("git_head") or ".").resolve()
        dataset = candidate.parent
    root = dataset / SUBTREE
    if not root.is_dir():
        raise SystemExit(f"subarvore ausente: {root}; passe --dataset explicitamente")

    paths: list[str] = corpus["corpus"]["paths"]
    df: Counter = Counter()
    for rel in paths:
        try:
            text = (root / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for tok in tokenize(text):
            df[tok] += 1

    by_stratum: dict[str, list[str]] = defaultdict(list)
    for name, count in df.items():
        for label, lo, hi in STRATA:
            if count >= lo and (hi is None or count <= hi):
                by_stratum[label].append(name)
                break
    for label in by_stratum:
        by_stratum[label].sort()

    queries = []
    n = 0
    for label, _, _ in STRATA:
        for name in evenly_spaced(by_stratum[label], PER_STRATUM):
            n += 1
            queries.append(
                {
                    "id": f"q{n:02d}",
                    "text": name,
                    "stratum": label,
                    "doc_freq": df[name],
                }
            )

    # Borda, reportadas à parte. A consulta de zero correspondência é verificada contra o
    # próprio vocabulário do corpus: se um dia existir, o rótulo deixa de ser verdade.
    zero = "ZzqR2TokenInexistenteNoCorpus"
    while zero in df:
        zero += "X"
    multi = [q["text"] for q in queries if q["stratum"] == "1"][:2]
    edge = [
        {"id": "e01", "kind": "zero_match", "text": zero, "note": "ausente do vocabario"},
        {"id": "e02", "kind": "unicode", "text": "movimentação", "note": "acento nao-ASCII"},
        {"id": "e03", "kind": "multi_token", "text": " ".join(multi) if multi else "getId setId",
         "note": "dois tokens"},
        {"id": "e04", "kind": "long", "text": " ".join(q["text"] for q in queries[:12]),
         "note": "12 tokens"},
        {"id": "e05", "kind": "punctuation", "text": "getId();", "note": "pontuacao de codigo"},
        {"id": "e06", "kind": "short", "text": "id", "note": "token curto e comum"},
    ]

    out = Path(args.out)
    payload = {
        "schema": "atlas-queries/1",
        "generator": "benchmarks/rust/gen_queries.py",
        "source_corpus": {
            "files": corpus["corpus"]["files"],
            "fingerprint": corpus["corpus"]["content_fingerprint_sha256"],
        },
        "strata_definition": {label: {"min": lo, "max": hi} for label, lo, hi in STRATA},
        "per_stratum": PER_STRATUM,
        "queries": queries,
        "edge": edge,
        "vocabulary_size": len(df),
        "counts_by_stratum": {label: len(by_stratum[label]) for label, _, _ in STRATA},
    }
    from _bench import write_json  # noqa: E402

    write_json(out / "queries.json", payload)

    print(f"vocabulario: {len(df)} tokens; {len(queries)} consultas estratificadas")
    for label, _, _ in STRATA:
        picked = [q["text"] for q in queries if q["stratum"] == label]
        print(f"  {label:>6} (df disponiveis {len(by_stratum[label]):5}): {picked}")
    print(f"  borda: {[e['text'] for e in edge]}")
    print(f"escrito em {out / 'queries.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
