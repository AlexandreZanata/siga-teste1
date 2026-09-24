# E26-01 com braço BM25 — REPORT (`btc-e2601-003`)

Pergunta: um ranker BM25 textual (top-10 arquivos) compete com busca/adapter no corpus?
Método: mesmas 34 tarefas × A/B/C + **D_bm25** × 2k/8k = **272** rodadas, seeds `7-{budget}`.
D usa `btc-bm25text/1`; A/B/C bit-idênticos às rodadas 001/002 (determinismo confirmado).
Sem modelo, sem custo faturado.

## Resultados @2000 (8k idêntico)

| braço | hit | recall | precisão | entregues med |
|---|---|---|---|---|
| A_busca | 0.962 | 0.942 | 0.0018 | 1208 |
| B_freq (top-4) | 0.385 | 0.231 | 0.1058 | 4 |
| C_adapter (CAP=25) | 0.731 | 0.673 | 0.0116 | 189 |
| D_bm25 (top-10) | 0.654 | 0.481 | 0.0962 | 10 |

D por tipo: edit2ripple 0.750, comment2context 0.400, trace2code 0.375, code2test 0.300
(queries descrevem mudança no código; arquivos de teste não ranqueiam). 9 misses/26.

## Leitura e decisão

D é o braço **precisão** (0.096, ~10 arquivos, barato, determinístico) e C o braço **recall**
(0.673, 189 arquivos); A segue recall inutilizável. D_bm25 `manter` como baseline lexical
real; dívidas: K=10 arbitrário, vocabulário (testes, `addrman`), sem abstenção. Nada sobre
patches ou custo faturado — **sem confirmação** de ganho em edição.
