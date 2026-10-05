# R2 — tabelas geradas

Rodada: `2026-10-05-q8-realmeasure`. Gerado por `benchmarks/rust/report.py`; nenhum número deste arquivo foi escrito à mão.
Artefatos agregados: `runs_index.jsonl`, `runs_query_CTX-RS_b2000_r5.jsonl`.

## Integridade da medição

- Execuções: **360**, com código 0: **360** (100.0%), não-zero: **0**.
- Rust: `used_bytes` igual ao stdout real em **180/180** execuções
- Consultas distintas: 36
- Políticas: CTX-RS
- Combinações (política, orçamento) medidas:
  - `CTX-RS` orçamento 2000: 5 repetições por consulta/braço


## Política `CTX-RS`

### Tempo de parede (s), por orçamento

| grupo | impl | n | min | p50 | p95 | max | média |
|---|---|---|---|---|---|---|---|
| 2000 | python | 180 | 0.110 | 0.305 | 0.650 | 0.810 | 0.361 |
| 2000 | rust | 180 | 0.000 | 0.010 | 0.030 | 0.040 | 0.012 |

### CPU user+sistema (s), por orçamento

| grupo | impl | n | min | p50 | p95 | max | média |
|---|---|---|---|---|---|---|---|
| 2000 | python | 180 | 0.110 | 0.300 | 0.640 | 0.780 | 0.353 |
| 2000 | rust | 180 | 0 | 0.000 | 0.020 | 0.040 | 0.007 |

### Pico de RSS (kB), por orçamento

| grupo | impl | n | min | p50 | p95 | max | média |
|---|---|---|---|---|---|---|---|
| 2000 | python | 180 | 48996.000 | 49830.000 | 51292.000 | 51632.000 | 49980.867 |
| 2000 | rust | 180 | 6176.000 | 7272.000 | 12000.000 | 13584.000 | 8131.689 |

### Razão Rust/Python por consulta (medianas pareadas)

| consulta | estrato | py wall p50 | rs wall p50 | razão rs/py | py bytes | rs bytes |
|---|---|---|---|---|---|---|
| e01 `ZzqR2TokenInexistenteN` | zero_match | 0.130 | 0.000 | 0.00 | 295 | 466 |
| e02 `movimentação` | unicode | 0.250 | 0.030 | 0.12 | 11000 | 8000 |
| e03 `A04000 RESOURCE_BUNDLE` | multi_token | 0.200 | 0.000 | 0.00 | 1257 | 1996 |
| e04 `A04000 RESOURCE_BUNDLE` | long | 0.530 | 0.010 | 0.02 | 6786 | 7647 |
| e05 `getId();` | punctuation | 0.330 | 0.040 | 0.12 | 14239 | 7919 |
| e06 `id` | short | 0.400 | 0.040 | 0.10 | 10553 | 7946 |
| q01 `A04000` | 1 | 0.240 | 0.000 | 0.00 | 569 | 1059 |
| q02 `RESOURCE_BUNDLE` | 1 | 0.260 | 0.000 | 0.00 | 948 | 1340 |
| q03 `desc_tipo_mobil` | 1 | 0.230 | 0.000 | 0.00 | 592 | 1140 |
| q04 `imageQRCode` | 1 | 0.420 | 0.010 | 0.02 | 2025 | 2681 |
| q05 `redirecionaPaginaCasoO` | 1 | 0.350 | 0.000 | 0.00 | 2437 | 3884 |
| q06 `zone` | 1 | 0.440 | 0.000 | 0.00 | 3689 | 3500 |
| q07 `AAAA` | 2-5 | 0.390 | 0.010 | 0.03 | 3016 | 7819 |
| q08 `RecuperarMenuAbastecim` | 2-5 | 0.280 | 0.000 | 0.00 | 1016 | 2531 |
| q09 `daoId` | 2-5 | 0.440 | 0.000 | 0.00 | 3338 | 6412 |
| q10 `getTipoPermissaoSet` | 2-5 | 0.520 | 0.010 | 0.02 | 2283 | 3826 |
| q11 `protocolo_arq_transf` | 2-5 | 0.480 | 0.010 | 0.02 | 2364 | 4548 |
| q12 `zonedDateTime` | 2-5 | 0.640 | 0.010 | 0.02 | 2560 | 5017 |
| q13 `ABERTA` | 6-20 | 0.550 | 0.010 | 0.02 | 6536 | 7963 |
| q14 `NoSuchMethodException` | 6-20 | 0.720 | 0.020 | 0.03 | 8626 | 7927 |
| q15 `consultarCpServicoPorC` | 6-20 | 0.590 | 0.010 | 0.02 | 3134 | 6687 |
| q16 `getModelos` | 6-20 | 0.620 | 0.020 | 0.03 | 9449 | 7531 |
| q17 `pessoaObjetoSel` | 6-20 | 0.620 | 0.010 | 0.02 | 8467 | 7874 |
| q18 `zero` | 6-20 | 0.170 | 0.010 | 0.06 | 3392 | 7900 |
| q19 `ALERTA` | 21-100 | 0.280 | 0.010 | 0.04 | 11625 | 7906 |
| q20 `Revision` | 21-100 | 0.320 | 0.000 | 0.00 | 9494 | 7669 |
| q21 `containsKey` | 21-100 | 0.310 | 0.010 | 0.03 | 9590 | 7751 |
| q22 `getRequest` | 21-100 | 0.280 | 0.010 | 0.04 | 12311 | 7924 |
| q23 `permitida` | 21-100 | 0.260 | 0.010 | 0.04 | 11193 | 7858 |
| q24 `xpath` | 21-100 | 0.260 | 0.000 | 0.00 | 3652 | 7310 |
| q25 `AplicacaoException` | >100 | 0.260 | 0.020 | 0.08 | 10444 | 7900 |
| q26 `Retorna` | >100 | 0.280 | 0.010 | 0.04 | 15091 | 7933 |
| q27 `desta` | >100 | 0.290 | 0.010 | 0.03 | 3732 | 7979 |
| q28 `instanceof` | >100 | 0.260 | 0.020 | 0.08 | 9222 | 7974 |
| q29 `replace` | >100 | 0.120 | 0.030 | 0.25 | 2082 | 7421 |
| q30 `yyyy` | >100 | 0.210 | 0.020 | 0.10 | 3380 | 7892 |
| **resumo budget=2000** | — | — | — | p50 0.02 · máx 0.25 | | |

### Divergência semântica: declarado vs entregue

| orçamento | impl | estado (contagem) | bytes entregues (p50) | tokens declarados (p50) | bytes declarados (p50) | refs (p50) | trechos (p50) | arquivos (p50) | `tokenizer_is_exact` |
|---|---|---|---|---|---|---|---|---|---|
| 2000 | python | ok=170, partial=10 | 3670 | 392 | nao medido | 10 | 10 | 5 | False |
| 2000 | rust | ok=60, partial=120 | 7658 | 1914 | 7657 | 5 | 5 | 4 | False |

## Fidelidade do orçamento declarado (todas as políticas)

| impl | n | bytes entregues (p50) | tokens estimados `chars//4` (p50) | tokens declarados (p50) | razão declarado/entregue (p50 · máx) | declara bytes entregues? | execuções acima de `max_bytes` | declarado acima de `budget_tokens` |
|---|---|---|---|---|---|---|---|---|
| python | 180 | 3670 | 918 | 392 | 0.45 · 0.53 | não | 70/180 | 0/180 |
| rust | 180 | 7658 | 1914 | 1914 | 1.00 · 1.00 | sim | 0/180 | 0/180 |

`ratio` é a mediana das razões **por execução** (declarado ÷ bytes entregues ÷ 4), não a razão de duas medianas: agregar antes de dividir esconderia justamente as execuções em que a declaração diverge.

## Construção do índice (dispersão, diretórios exclusivos)

### Tempo de parede (s)

| grupo | impl | n | min | p50 | p95 | max | média |
|---|---|---|---|---|---|---|---|
| index | python | 3 | 12.440 | 17.810 | 22.990 | 22.990 | 17.747 |
| index | rust | 3 | 0.590 | 0.610 | 0.640 | 0.640 | 0.613 |

### Pico de RSS (kB)

| grupo | impl | n | min | p50 | p95 | max | média |
|---|---|---|---|---|---|---|---|
| index | python | 3 | 26596.000 | 26692.000 | 26768.000 | 26768.000 | 26685.333 |
| index | rust | 3 | 12844.000 | 13176.000 | 13268.000 | 13268.000 | 13096.000 |

| impl | walls (todas as repetições) | índice (B) p50 | WAL (B) p50 |
|---|---|---|---|
| python | 12.440, 17.810, 22.990 | 9457664 | 0 |
| rust | 0.640, 0.590, 0.610 | 17231872 | 0 |

## Convenções

- Quantis por **posto mais próximo** em amostra ordenada; p50 = mediana (média dos dois centrais quando n é par).
- Tempo medido do **spawn até consumir todo o stdout**, com GNU time. Nenhuma medição é de função interna.
- Cache de filesystem **aquecido**. Frio não foi medido: exigiria `drop_caches` com root numa máquina dedicada.
- Ordem **alternada por repetição**: cada braço ocupa cada posição metade das vezes.

