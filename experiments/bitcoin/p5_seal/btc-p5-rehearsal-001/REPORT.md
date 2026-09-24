# BTC-P5 ensaio de selamento — REPORT (`btc-p5-rehearsal-001`)

**ENSAIO — VOID PARA A RODADA REAL.** Sem custodiante, sem ouro, sem amostra dimensionada.
O selo real ocorre uma única vez antes da rodada, com tarefas finais, testes ocultos e chave
sob custódia segregada; este ensaio jamais será apresentado como selo.

## O que foi ensaiado

- `sealed.json`: 12 tarefas estruturais (`BTC-P3D-001–012`, sem soluções) × 3 condições × 2 reps,
  seed 7, versões (`core_sha`, `btc-cpp-lex/1`, `btc-pack/1+expanded`, budget 2000, `chars//4`).
- Selo `a6c5be5a…2903322c` (64 hex); `verify_seal` True no original, False em cópias com
  `repetitions` ou `family` adulterados e sem campo `schema`.
- Cegamento: bijeção determinística por seed (`patch-…` → `Blind-001…`); `unblind` exige chave
  (`PermissionError` sem ela; `KeyError` em ID desconhecido); pacote do avaliador só com
  tarefa/snapshot/patch/rubrica (sem condição, modelo, custo ou ordem).
- Comando: `pytest -q tests/bitcoin/test_btc_seal.py` → **3 passed**.

## Decisão

Maquinaria `manter` para a rodada real; ensaio `evidência insuficiente` para qualquer conclusão
de produto. Próximo (pré-rodada, com piloto e custodiante): amostra dimensionada, selo real único,
avaliação cega independente, publicação positivo/negativo/inconclusivo.
