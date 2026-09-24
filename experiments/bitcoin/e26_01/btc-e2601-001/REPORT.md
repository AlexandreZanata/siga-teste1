# BTC-E26-01 no corpus — REPORT (`btc-e2601-001`)

Pergunta: os braços recuperam a próxima evidência no corpus v31.1 com custo conhecido?
Método: 26 positivas (code2test 5, trace2code 8, comment2context 5, edit2ripple 8; 12 adotadas
de rascunho não-identificado após auditoria item a item, resto ouro próprio — todos os paths
verificados no tag) + 8 negativas × A/B/C × budgets 2k/8k = **204** rodadas, seeds `7-{budget}`.
Checkout `--detach BTC_SHA` somente leitura. Sem modelo (patch nulo), sem custo faturado.

## Resultados @2000 (8k idêntico em conjuntos; só `used` muda)

| braço | hit | recall | precisão | abstenção | entregues med | used med |
|---|---|---|---|---|---|---|
| A_busca | 0.962 | 0.942 | 0.0018 | 0.000 | 1427 | 1730 |
| B_freq (top-4) | 0.385 | 0.231 | 0.1058 | 0.000 | 4 | 0† |
| C_adapter | 0.808 | 0.731 | 0.0071 | 0.125 | 238 | 776 |

†`used` 0 quando o 1º arquivo excede o budget — artefato da conta por arquivo inteiro.
C por tipo: code2test 1.000, edit2ripple 1.000, comment2context 0.700, trace2code **0.312**.
Misses C: R17/R18/R19/R20 (falha funcional aponta impl sem vocabulário comum) + R12
(`addrman` ≠ `address`, afogado pelo fan-in de hubs). Único miss A: R17. Única abstenção:
N05/siga-ex sob C (zero matches); A/B jamais se abstêm — sem limiar calibrado.

## Leitura e decisão

A tem recall alto e inutilizável (1427 arquivos); B é barato e perdedor; C é o candidato
(recall 0.731, 6× menos arquivos que A) com dívidas: teto de fan-in em hubs + vocabulário
de domínio + trace2code fraco. Nada sobre patches, custo faturado ou superioridade:
1 snapshot, sem modelo — **sem confirmação** de ganho em edição. Política dev: C_adapter;
E26-02 (empacotamento por spans, não arquivos inteiros) é o próximo gargalo medido.
