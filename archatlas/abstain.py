# SPDX-License-Identifier: Apache-2.0
"""P4-infra(c): abstenção e incerteza explícitas, calibradas no dev E26-01.

Regra congelada (dev 28 casos; calibrada E avaliada no mesmo dev — otimista;
validação em holdout pendente, sem promessa de generalização):
- ABSTAIN sse `seeds == 0 AND lex == 0` (motivo `no-local-evidence`): no dev,
  7/8 negativos e 5/20 positivos (dos quais 1 hit real via fallback: E01-C2C-02).
- UNCERTAIN (entrega com bandeira, sem reter) sse entregue e
  (`seeds == 0 OR lex == 0 OR top_score > WEAK_TOP`) com `WEAK_TOP = -1.0`
  (no dev, separa WR-03 `-0.0` de todos os positivos ≤ `-3.6`; 1 ponto —
  frágil, só p/ bandeira, nunca p/ reter).

Puro e determinístico (sem `con` além das listas já computadas pelo executor).
"""
from __future__ import annotations

WEAK_TOP = -1.0
CALIBRATION = "E26-01 dev 28 casos (20pos+8neg), mesma-amostra; holdout pendente"


def features(seeds_n: int, lex_n: int, top_score: float | None) -> dict:
    """Evidência observável da consulta (executor fornece, avaliador consome)."""
    return {"seeds_n": seeds_n, "lex_n": lex_n, "top_score": top_score}


def decide(feat: dict) -> dict:
    """`{abstain, reason, uncertain}` — reter só no vazio duplo; resto é bandeira."""
    seeds_empty = feat["seeds_n"] == 0
    lex_empty = feat["lex_n"] == 0
    if seeds_empty and lex_empty:
        return {"abstain": True, "reason": "no-local-evidence", "uncertain": False}
    top = feat.get("top_score")
    weak = seeds_empty or lex_empty or (top is not None and top > WEAK_TOP)
    return {"abstain": False, "reason": None, "uncertain": bool(weak)}
