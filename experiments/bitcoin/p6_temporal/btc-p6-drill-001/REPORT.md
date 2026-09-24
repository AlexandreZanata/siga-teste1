# BTC-P6 drill temporal — REPORT (`btc-p6-drill-001`)

Pergunta: a maquinaria de atualização classifica t0 → t1 e limita o retrabalho sem corpus real?
Método: `archatlas/bitcoin/temporal.py` sobre repos sintéticos (header alterado, par novo,
1 remoção). Comando: `pytest -q tests/bitcoin/test_btc_portability.py` → **2 passed**.

## Medições (sintéticas; sem valor de produto)

- `added`: policy.cpp, policy.h. `removed`: test/wallet_tests.py. `changed`: validation.h.
- `invalidated` (5/13, fração 0.385): validation.h + dependentes (validation.cpp, wallet.cpp,
  server.cpp via `#include`) + remoção registrada. `net.cpp`/`mempool.cpp` sem retrabalho.
- Sem mudança → zero invalidação (12 inalterados); determinismo repetido.

## Decisão

Maquinaria `manter` para a rodada temporal real (t0/t1 pinados por SHA); custo e cobertura
reais `evidência insuficiente` até snapshots Bitcoin. Limites: minúsculo, sem build, sem
`compile_commands.json`; invalidação só textual (basename de include).
