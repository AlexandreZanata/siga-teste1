# Repeat com teto de fan-in — REPORT (`btc-e26-01-real-002`)

Pergunta: o teto no salto por `#include` corta o ruído sem perder o ouro?
Método: mesmas 12 sondas, braços, budgets, seeds de embaralhamento e corpus
somente-leitura de 001; único fator variado: `fanin_cap=100` no braço C
(headers incluídos por >100 arquivos pulados com registro). 72 rodadas, 0 erros.
Calibração (dev, mesma-amostra — otimista; holdout pendente): cap ≤50 perde 1 hit
(0.917→0.833); cap 100 preserva tudo (301→265 arqs no sweep; 271 medidos aqui).

## 001 → 002 (24 rodadas/braço)

| braço | hit | recall | entregues med | hubs pulados |
|---|---|---|---|---|
| A_busca | 1.000 → 1.000 | 1.000 → 1.000 | 1431.9 → 1431.9 | — |
| B_freq | 0.500 → 0.500 | 0.292 → 0.292 | 4.0 → 4.0 | — |
| C_adapter | 0.917 → 0.917 | 0.833 → 0.833 | 300.9 → 270.9 | 7452 |

A/B bit-idênticos (fator isolado no C). R12 segue miss (vocabulário `addrman`,
não hubs). Divergência registrada como evidência (sem reescrita alheia): o default
commitado é `FANIN_CAP=25` (p90≈27, sem calibração por resultado); esta repetição usa
`cap=100` explícito por rodada — 25 perderia 1 hit no dev (sweep acima). Decisão do
default fica para integração (A/orquestrador), não para overwrite silencioso.

## Leitura e decisão

Teto de fan-in: −10% entregues, zero perda de hit/recall no dev — `manter` como
variante registrada (`cap` por rodada), não como default imposto. Vocabulário
(`addrman`) é a próxima dívida (mapa de domínio, sem adivinhação semântica).
Patch/custo nulos; sem confirmação de edição.
