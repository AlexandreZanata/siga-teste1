# E26-01 com split de identificadores — REPORT (`btc-e2601-004`)

Pergunta: quebrar identificadores (`_`, `-`, camel) recupera trace2code sem semântica?
Método: mesmas 34 tarefas × 4 braços × 2k/8k = **272** rodadas; único fator vs 003 é
`split_ids=True` (`btc-vocab/1`, mecânico; aliases desligados). Sem modelo.

## Medições @2000 (003 → 004)

| braço | hit | recall | precisão |
|---|---|---|---|
| A_busca | 0.962 → **1.000** | 0.942 → **1.000** | 0.0018 |
| B_freq | 0.385 → 0.423 | 0.231 → 0.269 | 0.1058 → 0.1250 |
| C_adapter | 0.731 → **0.808** | 0.673 → **0.750** | 0.0116 → 0.0129 |
| D_bm25 | 0.654 → 0.654 | 0.481 → 0.481 | 0.0962 → 0.1051 |

Ganhos: R17 + R18 (trace2code 0.375 → **0.625**); perdas: zero. D inalterado (porter já
cobre; split nada acrescenta ao BM25). R12 (`addrman`) segue miss — split não cria
vocabulário: aliases com evidência ficam para o próximo.

## Decisão

Split mecânico `manter` (ganho sem perda, custo zero, determinístico). R12 exige alias
verdadeiro (`address`→`addrman`, evidência `src/addrman.h:59`) — próximo fator isolado.
Nada sobre patches ou custo faturado — **sem confirmação** de ganho em edição.
