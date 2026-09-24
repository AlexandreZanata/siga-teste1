# E26-02 no corpus — REPORT (`btc-e2602-corpus-001`)

Pergunta: sob mesmo ranking/budget, qual empacotamento preserva pares e ouro no corpus?
Método: 26 tarefas; candidatos = linhas com tokens da query nos arquivos C@2000
(~610/tarefa, ordem **alfabética**); `btc-pack/1` × 3 políticas, budget 2000. Sem modelo.

## Medições (médias/26; budget limita ~71 trechos)

| política | used | trechos | pares | gt_all | gt_file_recall | descartes |
|---|---|---|---|---|---|---|
| one_per_file | 1673 | 71.5 | 143 | 7/26 | 0.340 | ~538 |
| multi | 1706 | 71.0 | 26 | 1/26 | 0.038 | ~539 |
| expanded | 1706 | 70.5 | 60 | 1/26 | 0.051 | ~542 |

## Leitura e decisão

Largura vence cobertura aqui — mas o ranking é alfabético (conjuntos sem score), então o
experimento mede **robustez a orçamento sob ordem arbitrária**, não qualidade de ranking:
`evidência insuficiente` para produto. `expanded` gasta budget com contexto de par sem ganho
de cobertura nestas condições; o sintético (mesmo ranking) dizia o oposto — contradição que
só se resolve com candidatos ranqueados por score. Próximo: ranking BM25/score + repetir;
só então promover política. Nada sobre patches ou custo faturado.
