# BTC-E26-02 sintético — REPORT (`btc-e2602-synth-001`)

Pergunta: sob mesmo ranking e mesmo budget, profundidade/profundidade-com-pares supera
dispersar 1 trecho por arquivo? Método: 8 candidatos (com span duplicado e arquivo ilegível)
sobre o repo sintético, budget diagnóstico 120, `btc-pack/1` nas três políticas.
Comando: `pytest -q tests/bitcoin/test_btc_packing.py` → **4 passed**.

## Medições (fixtures sintéticas; sem valor de produto)

| política | used | trechos | arquivos | pares completos | descartes (log) |
|---|---|---|---|---|---|
| one_per_file | 48 | 3 | 3 | 0 | 5 |
| multi | 108 | 6 | 3 | 0 | 2 |
| expanded | 113 | 7 | 5 | 2 | 4 |

Dedup de span idêntico nas três; gates `one-per-file`/`unreadable`/`over_budget` ruidosos;
determinismo repetido; `used ≤ budget` inclusive com budget 5.

## Decisão

`expanded` promovido a **candidato** (2 pares header/impl preservados por +5 tokens, +4,6%
sobre `multi`; `one_per_file` perde profundidade sem economia relevante aqui). Decisão final
de produto exige piloto real — até lá, `evidência insuficiente` para qualidade/custo em edição.
Limites: repo minúsculo, sem modelo, sem latência; pares só textuais (mesmo radical).
