# Sondas dev executadas — `transfer-probes-001` (20 sondas, sem tarefas)

Data: 2026-09-24. ID: P6-exec-c2. Método: índices T1/T2 da linha de base
(`t1-base.sqlite`, `t2-base.sqlite`), 10 sondas/alvo × LEX/CÁPSULA-2k = 40 rodadas.
Ouro dev (localização, sem holdout); patch nulo. Saídas: `manifest.jsonl` + `runs.jsonl`.

## Resultados (hit = arquivo esperado entregue)

| alvo | LEX | CÁPSULA | payload med (cápsula) |
|---|---|---|---|
| T1 cucumber | 0.90 | 0.90 | 6564 |
| T2 pytest | 0.80 | 1.00 | 7210 |

Misses: T1-005/CÁPSULA (`Status` ambíguo entre módulos — refs lotaram o budget com
candidatos errados); T1-006/LEX, T2-003/LEX, T2-004/LEX (BM25 puro perde; cápsula
com símbolos+refs resgata os 3). Cápsula ≥ lexical nos dois alvos; T2 perfeita
(AST + nomes distintos ajudam).

## Leitura

Localização dev funciona fora do SIGA sem ajuste (índice + mesma cápsula); ambiguidade
de nomes (T1-005) é o modo de falha a tratar com desambiguação explícita, não com
mais budget. Nenhuma tarefa de edição, nenhum holdout, nenhuma transferência provada —
próximo: tarefas executáveis por alvo (P6-exec-d) com teste cego próprio.
