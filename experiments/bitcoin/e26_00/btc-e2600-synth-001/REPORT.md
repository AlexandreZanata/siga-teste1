# BTC-E26-00 sintético — REPORT (`btc-e2600-synth-001`)

Pergunta: a instrumentação espelho (hit vs recall de conjunto, payload inteiro, replay, stale)
funciona sobre fatos do adaptador Bitcoin antes de qualquer dataset real?
Método: 5 casos sintéticos C++/Python em `tests/bitcoin/test_btc_e26_00.py` (ouro independente,
sem LLM, sem holdout). Manifesto: `manifest.json`. Comando:
`PYTHONPATH=<worktree> pytest -q tests/bitcoin/` → **10 passed** (5 E26-00 + 5 adaptador).

## Medições

- Parcial: `delivered={src/validation.cpp}` em 3 esperados → `hit=True`, `recall_set=1/3` (não 100%).
- Alternativas: 1 de 2 → 0.5; 2 de 2 → 1.0 (sem passe livre por alternativa).
- Caminho: nós sem o arquivo da aresta → `hit=False` (aresta exigida).
- Stale: mudança pós-índice e remoção detectadas por `verify_fact`; scoring vazio sem crash.
- Payload: `payload_tokens_for_capsule` determinístico e positivo; `verify_replay` True no original,
  False no adulterado; `score_delivery(delivered, gt)` isolado do índice/disco.
- `opened`/`declared_relevant`/`history_tokens`: nulos com motivo (sem canal de entrega/rodada viva
  nesta etapa; ver `CONTRACTS_P2.md` §5).

## Falhas e limites

Nenhuma falha. Limites: fixtures sintéticas, não corpus; sem budgets 2k/8k reais, sem latência,
sem variância de modelo. Não é experimento de superioridade e não autoriza conclusões de economia.

## Decisão

`manter` a instrumentação E26-00 espelho para a rodada real pós-PIN; `evidência insuficiente`
para qualquer outra conclusão. Próximo: manifesto de build/índice do corpus após `BTC_SHA`.
