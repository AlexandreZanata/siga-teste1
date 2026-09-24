# E26-01 repetição com teto de fan-in — REPORT (`btc-e2601-002`)

Pergunta: o teto de fan-in (CAP=25, p90≈27, 970 headers) corta o ruído sem perder ouro?
Método: mesmas 34 tarefas, mesmos seeds/pares, C com `fanin.get(base,0) > 25` pulado e contado;
A/B rerodados (idênticos, determinismo confirmado). 204 rodadas, 106s. Comparado: `btc-e2601-001`.

## Medições @2000 (C_adapter; A/B inalterados)

| rodada | hit | recall | precisão | entregues med | hubs pulados |
|---|---|---|---|---|---|
| 001 sem teto | 0.808 | 0.731 | 0.0071 | 238 | — |
| 002 CAP=25 | 0.731 | 0.673 | 0.0116 | 189 | 14373 |

Perdas: R04 (server.h é hub) e R10 (net.h é hub) — o teto global derruba justamente respostas-hub.
Ganhos: zero. Por tipo (002): code2test 1.0, edit2ripple 1.0, comment2context 0.6, trace2code 0.188.

## Decisão

Teto global **não adotado**: −21% arquivos e +63% precisão relativa não compensam −0.058 recall
quando o ouro mora em hubs. Alternativa registrada (não executada): teto só além das sementes
(seeds nunca caem) ou ranking por co-ocorrência em vez de corte — E26-02 com spans é o palco
correto, não arquivo inteiro. R12 (`addrman`) segue miss nas duas rodadas: vocabulário pendente.
Nada sobre patches ou custo faturado — **sem confirmação** de ganho em edição.
