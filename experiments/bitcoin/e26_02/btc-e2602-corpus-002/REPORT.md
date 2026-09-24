# E26-02 ranqueado no corpus — REPORT (`btc-e2602-corpus-002`)

Pergunta: com ranking por relevância, qual empacotamento preserva pares e ouro?
Método: mesmas 26 tarefas; candidatos = top-200 linhas BM25 (`btc-bm25text/1`: 1773 arqs,
404.724 linhas indexadas em 2s, DB 118MB em `/tmp`, trechos ranqueados); `btc-pack/1` × 3,
budget 2000. Corrige o confound alfabético de `btc-e2602-corpus-001`. Sem modelo.

## Medições (médias/26)

| política | used | trechos | pares | gt_all | gt_file_recall |
|---|---|---|---|---|---|
| one_per_file | 1285 | 35.1 | 73 | 16/26 | 0.673 |
| multi | 1994 | 68.8 | 36 | 11/26 | 0.558 |
| expanded | 1995 | 69.2 | 65 | 13/26 | 0.596 |

## Leitura e decisão

Ranking estreita a disputa: `expanded` supera `multi` (13 vs 11 gt_all, +29 pares) e
`one_per_file` lidera cobertura por token (16/26 a 1285 tok). Largura ainda vence em
cobertura de arquivos — mas cobertura ≠ patch correto; promoção de produto exige tarefa
real de edição (piloto). Técnica E26-02: comparação completa nas duas condições
(alfabética + ranqueada); `btc-bm25text/1` `manter` como ranker lexical (hits relevantes,
determinístico, barato). Vocabulário (`addrman`) e edição seguem pendentes.
