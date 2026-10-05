# R2 — tabelas geradas

Rodada: `2026-10-05-r2-scale-q8`. Gerado por `benchmarks/rust/report.py`; nenhum número deste arquivo foi escrito à mão.
Artefatos agregados: `runs_scale.jsonl`.

## Escala: o que acontece quando o corpus cresce

| × | arquivos | MiB de texto |
|---|---|---|
| ×30 | 15120 | 71.6 |
| ×100 | 50400 | 238.7 |

O corpus é uma **cópia** do mesmo conjunto: cada arquivo aparece N vezes, então `doc_freq` e ranking não são os de um projeto real. Interpretar **custo** (tempo, RSS, bytes de índice), não qualidade de resultado.

### Indexação

| × | arquivos | impl | n | wall p50 | wall p95 | wall máx | RSS p50 (kB) | RSS máx (kB) | CPU p50 |
|---|---|---|---|---|---|---|---|---|---|
| ×30 | 15120 | python | 4 | 196.725 | 295.050 | 295.050 | 47694 | 47912 | 9.305 |
| ×30 | 15120 | rust | 4 | 2.280 | 6.680 | 6.680 | 23332 | 23500 | 1.395 |
| ×100 | 50400 | python | 3 | 435.380 | 493.730 | 493.730 | 110656 | 111196 | 61.030 |
| ×100 | 50400 | rust | 3 | 12.670 | 13.570 | 13.570 | 54556 | 54592 | 11.040 |

### Consulta (`context`, orçamento 2 000)

| × | arquivos | impl | n | wall p50 | wall p95 | wall máx | RSS p50 (kB) | RSS máx (kB) | CPU p50 |
|---|---|---|---|---|---|---|---|---|---|
| ×30 | 15120 | python | 10 | 1.270 | 2.330 | 2.330 | 208404 | 394336 | 1.270 |
| ×30 | 15120 | rust | 10 | 0.020 | 0.080 | 0.080 | 12584 | 13536 | 0.010 |
| ×100 | 50400 | python | 10 | 4.280 | 7.280 | 7.280 | 646100 | 1264056 | 4.275 |
| ×100 | 50400 | rust | 10 | 0.065 | 0.350 | 0.350 | 22628 | 26240 | 0.045 |

### Custo normalizado

| impl | × | wall p50 por 1 000 arquivos | RSS p50 por 1 000 arquivos (kB) | índice (B) | índice por arquivo (B) | `context` bytes p50 |
|---|---|---|---|---|---|---|
| python | ×30 | 13.011 | 3154.4 | 50257920 | 3323.9 | nao medido |
| rust | ×30 | 0.151 | 1543.1 | 108802048 | 7195.9 | 7928 |
| python | ×100 | 8.638 | 2195.6 | 168869888 | 3350.6 | nao medido |
| rust | ×100 | 0.251 | 1082.5 | 359108608 | 7125.2 | 7928 |

## Convenções

- Quantis por **posto mais próximo** em amostra ordenada; p50 = mediana (média dos dois centrais quando n é par).
- Tempo medido do **spawn até consumir todo o stdout**, com GNU time. Nenhuma medição é de função interna.
- Cache de filesystem **aquecido**. Frio não foi medido: exigiria `drop_caches` com root numa máquina dedicada.
- Ordem **alternada por repetição**: cada braço ocupa cada posição metade das vezes.

