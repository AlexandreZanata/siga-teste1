# SPDX-License-Identifier: Apache-2.0
"""Vocabulário mecânico Bitcoin (`btc-vocab/1`). Sem semântica, sem adivinhação.

`split_identifiers`: quebra tokens em `_`, `-` e fronteiras camelCase, mantendo os
originais (ordem preservada, sem duplicatas). Regra determinística sobre a forma da
string — não afirma que `mempool_accept` SIGNIFICA `mempool`, só permite o match
lexical das partes. Aliases de domínio (ex.: `address`→`addrman`, evidência
`src/addrman.h:59` "Stochastic address manager") vivem em `ALIASES` com evidência
obrigatória e entram só quando aplicados explicitamente.
"""
from __future__ import annotations
import re

ALIASES = {
    # alias: (tokens de código, evidência arquivo:linha@BTC_SHA)
    "address": (["addrman"], "src/addrman.h:59@9be056a8"),
}

_SPLIT_RE = re.compile(r"[A-Za-z0-9]+")


def _parts(token: str) -> list[str]:
    chunks = []
    for chunk in token.replace("-", "_").split("_"):
        chunks.extend(re.findall(r"[A-Z]?[a-z0-9]+|[A-Z]+(?![a-z])", chunk) or [chunk])
    return [c.lower() for c in chunks if c]


def split_identifiers(query: str) -> list[str]:
    """Tokens originais + partes, sem duplicatas, ordem estável."""
    out = []
    for tok in query.split():
        low = tok.lower()
        if low not in out:
            out.append(low)
        for p in _parts(tok):
            if p not in out:
                out.append(p)
    return out


def expand_query(query: str, aliases: dict | None = None) -> tuple[str, list[str]]:
    """Query expandida + tokens adicionados. `aliases=None` desliga aliases."""
    base = split_identifiers(query)
    added = [t for t in base if t not in query.lower().split()]
    if aliases:
        for alias, (targets, _evidence) in aliases.items():
            if alias in base:
                for tgt in targets:
                    if tgt not in base:
                        base.append(tgt)
                        added.append(tgt)
    return " ".join(base), added
