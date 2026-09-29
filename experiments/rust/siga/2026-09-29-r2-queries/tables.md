# R2 — tabelas geradas

Rodada: `2026-09-29-r2-queries`. Gerado por `benchmarks/rust/report.py`; nenhum número deste arquivo foi escrito à mão.

## Integridade da medição

- Execuções: **1800**, com código 0: **1800** (100.0%), não-zero: **0**.
- Rust: `used_bytes` igual ao stdout real em **900/900** execuções
- Consultas distintas: 36
- Políticas: CTX-RS, LEX-RS
- Combinações (política, orçamento) medidas:
  - `CTX-RS` orçamento 1000: 5 repetições por consulta/braço
  - `CTX-RS` orçamento 2000: 10 repetições por consulta/braço
  - `CTX-RS` orçamento 4000: 5 repetições por consulta/braço
  - `LEX-RS` orçamento 2000: 5 repetições por consulta/braço


## Política `CTX-RS`

### Tempo de parede (s), por orçamento

| grupo | impl | n | min | p50 | p95 | max | média |
|---|---|---|---|---|---|---|---|
| 1000 | python | 180 | 0.040 | 0.070 | 0.080 | 0.120 | 0.066 |
| 1000 | rust | 180 | 0.000 | 0.000 | 0.010 | 0.030 | 0.003 |
| 2000 | python | 360 | 0.040 | 0.070 | 0.100 | 0.170 | 0.071 |
| 2000 | rust | 360 | 0.000 | 0.000 | 0.010 | 0.030 | 0.003 |
| 4000 | python | 180 | 0.040 | 0.070 | 0.080 | 0.120 | 0.068 |
| 4000 | rust | 180 | 0.000 | 0.000 | 0.010 | 0.030 | 0.004 |

### CPU user+sistema (s), por orçamento

| grupo | impl | n | min | p50 | p95 | max | média |
|---|---|---|---|---|---|---|---|
| 1000 | python | 180 | 0.030 | 0.060 | 0.080 | 0.110 | 0.059 |
| 1000 | rust | 180 | 0 | 0.000 | 0.010 | 0.020 | 0.001 |
| 2000 | python | 360 | 0.030 | 0.070 | 0.090 | 0.140 | 0.066 |
| 2000 | rust | 360 | 0 | 0.000 | 0.010 | 0.020 | 0.001 |
| 4000 | python | 180 | 0.030 | 0.070 | 0.080 | 0.110 | 0.062 |
| 4000 | rust | 180 | 0 | 0.000 | 0.010 | 0.020 | 0.002 |

### Pico de RSS (kB), por orçamento

| grupo | impl | n | min | p50 | p95 | max | média |
|---|---|---|---|---|---|---|---|
| 1000 | python | 180 | 25900.000 | 26552.000 | 27972.000 | 28872.000 | 26825.311 |
| 1000 | rust | 180 | 5452.000 | 6570.000 | 8952.000 | 13504.000 | 7014.156 |
| 2000 | python | 360 | 25748.000 | 26572.000 | 27976.000 | 28796.000 | 26820.167 |
| 2000 | rust | 360 | 5396.000 | 6632.000 | 8924.000 | 13516.000 | 7007.556 |
| 4000 | python | 180 | 25808.000 | 26554.000 | 28032.000 | 28784.000 | 26825.978 |
| 4000 | rust | 180 | 5400.000 | 6662.000 | 8960.000 | 13564.000 | 7013.156 |

### Razão Rust/Python por consulta (medianas pareadas)

| consulta | estrato | py wall p50 | rs wall p50 | razão rs/py | py bytes | rs bytes |
|---|---|---|---|---|---|---|
| e01 `ZzqR2TokenInexistenteN` | zero_match | 0.050 | 0.000 | 0.00 | 295 | 466 |
| e02 `movimentação` | unicode | 0.080 | 0.020 | 0.25 | 8440 | 668 |
| e03 `ABCDEFGHIJLMNOPQRSTUZ ` | multi_token | 0.080 | 0.000 | 0.00 | 3839 | 3895 |
| e04 `ABCDEFGHIJLMNOPQRSTUZ ` | long | 0.110 | 0.010 | 0.09 | 8130 | 3859 |
| e05 `getId();` | punctuation | 0.070 | 0.010 | 0.14 | 8858 | 3978 |
| e06 `id` | short | 0.080 | 0.010 | 0.12 | 3979 | 1969 |
| q01 `ABCDEFGHIJLMNOPQRSTUZ` | 1 | 0.050 | 0.000 | 0.00 | 1398 | 2855 |
| q02 `Reiniciar` | 1 | 0.060 | 0.000 | 0.00 | 2705 | 3919 |
| q03 `designar` | 1 | 0.050 | 0.000 | 0.00 | 694 | 1489 |
| q04 `htmlImage` | 1 | 0.070 | 0.000 | 0.00 | 3362 | 1795 |
| q05 `predicateMobilRefComoM` | 1 | 0.050 | 0.000 | 0.00 | 1751 | 2036 |
| q06 `zone` | 1 | 0.050 | 0.000 | 0.00 | 960 | 1105 |
| q07 `ACESSAR` | 2-5 | 0.050 | 0.000 | 0.00 | 1529 | 3848 |
| q08 `LocalDate` | 2-5 | 0.070 | 0.000 | 0.00 | 8489 | 3817 |
| q09 `consultarQuantidadePar` | 2-5 | 0.050 | 0.000 | 0.00 | 1231 | 2878 |
| q10 `getNrInicial` | 2-5 | 0.050 | 0.000 | 0.00 | 988 | 1426 |
| q11 `possuiAssinaturaCossig` | 2-5 | 0.050 | 0.000 | 0.00 | 1218 | 2168 |
| q12 `zero` | 2-5 | 0.040 | 0.000 | 0.00 | 634 | 3888 |
| q13 `AGENDAMENTO_DE_PUBLICA` | 6-20 | 0.070 | 0.000 | 0.00 | 7906 | 3870 |
| q14 `Math` | 6-20 | 0.070 | 0.000 | 0.00 | 8252 | 3826 |
| q15 `converter` | 6-20 | 0.070 | 0.000 | 0.00 | 8715 | 3925 |
| q16 `getJuntados` | 6-20 | 0.070 | 0.000 | 0.00 | 4954 | 3922 |
| q17 `openoffice` | 6-20 | 0.070 | 0.000 | 0.00 | 8768 | 3940 |
| q18 `yyyy` | 6-20 | 0.060 | 0.000 | 0.00 | 4131 | 3933 |
| q19 `AplicacaoException` | 21-100 | 0.070 | 0.000 | 0.00 | 8446 | 3682 |
| q20 `Problem` | 21-100 | 0.070 | 0.000 | 0.00 | 7966 | 3801 |
| q21 `contains` | 21-100 | 0.040 | 0.000 | 0.00 | 2403 | 3969 |
| q22 `getTitular` | 21-100 | 0.070 | 0.000 | 0.00 | 8338 | 3959 |
| q23 `podeMovimentar` | 21-100 | 0.070 | 0.000 | 0.00 | 7919 | 3796 |
| q24 `write` | 21-100 | 0.070 | 0.000 | 0.00 | 3799 | 3894 |
| q25 `CompositeExpressionSup` | >100 | 0.070 | 0.000 | 0.00 | 8195 | 3711 |
| q26 `MERCHANTABILITY` | >100 | 0.070 | 0.010 | 0.14 | 8311 | 3716 |
| q27 `distributed` | >100 | 0.070 | 0.010 | 0.14 | 8501 | 3951 |
| q28 `later` | >100 | 0.080 | 0.010 | 0.12 | 3850 | 3843 |
| q29 `result` | >100 | 0.080 | 0.010 | 0.12 | 3825 | 3974 |
| q30 `your` | >100 | 0.080 | 0.010 | 0.12 | 3839 | 3834 |
| **resumo budget=1000** | — | — | — | p50 0.00 · máx 0.25 | | |
| e01 `ZzqR2TokenInexistenteN` | zero_match | 0.040 | 0.000 | 0.00 | 295 | 466 |
| e02 `movimentação` | unicode | 0.080 | 0.020 | 0.25 | 11884 | 5961 |
| e03 `ABCDEFGHIJLMNOPQRSTUZ ` | multi_token | 0.080 | 0.000 | 0.00 | 3839 | 7821 |
| e04 `ABCDEFGHIJLMNOPQRSTUZ ` | long | 0.110 | 0.010 | 0.09 | 10990 | 7689 |
| e05 `getId();` | punctuation | 0.070 | 0.010 | 0.14 | 17810 | 7810 |
| e06 `id` | short | 0.090 | 0.010 | 0.11 | 3979 | 6936 |
| q01 `ABCDEFGHIJLMNOPQRSTUZ` | 1 | 0.050 | 0.000 | 0.00 | 1398 | 2855 |
| q02 `Reiniciar` | 1 | 0.060 | 0.000 | 0.00 | 2705 | 6830 |
| q03 `designar` | 1 | 0.050 | 0.000 | 0.00 | 694 | 1489 |
| q04 `htmlImage` | 1 | 0.070 | 0.000 | 0.00 | 3362 | 1795 |
| q05 `predicateMobilRefComoM` | 1 | 0.060 | 0.000 | 0.00 | 1751 | 2036 |
| q06 `zone` | 1 | 0.060 | 0.000 | 0.00 | 960 | 1105 |
| q07 `ACESSAR` | 2-5 | 0.055 | 0.000 | 0.00 | 1529 | 7942 |
| q08 `LocalDate` | 2-5 | 0.080 | 0.000 | 0.00 | 12014 | 7861 |
| q09 `consultarQuantidadePar` | 2-5 | 0.050 | 0.000 | 0.00 | 1231 | 2878 |
| q10 `getNrInicial` | 2-5 | 0.050 | 0.000 | 0.00 | 988 | 1426 |
| q11 `possuiAssinaturaCossig` | 2-5 | 0.050 | 0.000 | 0.00 | 1218 | 2168 |
| q12 `zero` | 2-5 | 0.050 | 0.000 | 0.00 | 634 | 4894 |
| q13 `AGENDAMENTO_DE_PUBLICA` | 6-20 | 0.070 | 0.000 | 0.00 | 8313 | 7881 |
| q14 `Math` | 6-20 | 0.085 | 0.000 | 0.00 | 9375 | 7925 |
| q15 `converter` | 6-20 | 0.080 | 0.000 | 0.00 | 13557 | 7733 |
| q16 `getJuntados` | 6-20 | 0.080 | 0.000 | 0.00 | 4954 | 6389 |
| q17 `openoffice` | 6-20 | 0.070 | 0.000 | 0.00 | 11623 | 7944 |
| q18 `yyyy` | 6-20 | 0.070 | 0.000 | 0.00 | 4131 | 7920 |
| q19 `AplicacaoException` | 21-100 | 0.080 | 0.010 | 0.12 | 11938 | 7881 |
| q20 `Problem` | 21-100 | 0.080 | 0.000 | 0.00 | 12411 | 7634 |
| q21 `contains` | 21-100 | 0.065 | 0.010 | 0.15 | 2403 | 7897 |
| q22 `getTitular` | 21-100 | 0.080 | 0.000 | 0.00 | 12107 | 7853 |
| q23 `podeMovimentar` | 21-100 | 0.080 | 0.000 | 0.00 | 13052 | 7704 |
| q24 `write` | 21-100 | 0.080 | 0.000 | 0.00 | 3799 | 7518 |
| q25 `CompositeExpressionSup` | >100 | 0.070 | 0.000 | 0.00 | 13421 | 7979 |
| q26 `MERCHANTABILITY` | >100 | 0.070 | 0.010 | 0.14 | 12330 | 7713 |
| q27 `distributed` | >100 | 0.080 | 0.010 | 0.12 | 12026 | 7885 |
| q28 `later` | >100 | 0.080 | 0.010 | 0.12 | 3850 | 7946 |
| q29 `result` | >100 | 0.080 | 0.010 | 0.12 | 3825 | 7738 |
| q30 `your` | >100 | 0.070 | 0.010 | 0.14 | 3839 | 7930 |
| **resumo budget=2000** | — | — | — | p50 0.00 · máx 0.25 | | |
| e01 `ZzqR2TokenInexistenteN` | zero_match | 0.050 | 0.000 | 0.00 | 295 | 467 |
| e02 `movimentação` | unicode | 0.080 | 0.030 | 0.38 | 11884 | 14100 |
| e03 `ABCDEFGHIJLMNOPQRSTUZ ` | multi_token | 0.080 | 0.000 | 0.00 | 3839 | 9283 |
| e04 `ABCDEFGHIJLMNOPQRSTUZ ` | long | 0.110 | 0.010 | 0.09 | 10990 | 15922 |
| e05 `getId();` | punctuation | 0.070 | 0.010 | 0.14 | 18155 | 15948 |
| e06 `id` | short | 0.080 | 0.010 | 0.12 | 3979 | 15967 |
| q01 `ABCDEFGHIJLMNOPQRSTUZ` | 1 | 0.060 | 0.000 | 0.00 | 1398 | 2856 |
| q02 `Reiniciar` | 1 | 0.070 | 0.000 | 0.00 | 2705 | 6831 |
| q03 `designar` | 1 | 0.050 | 0.000 | 0.00 | 694 | 1490 |
| q04 `htmlImage` | 1 | 0.070 | 0.000 | 0.00 | 3362 | 1796 |
| q05 `predicateMobilRefComoM` | 1 | 0.050 | 0.000 | 0.00 | 1751 | 2037 |
| q06 `zone` | 1 | 0.050 | 0.000 | 0.00 | 960 | 1106 |
| q07 `ACESSAR` | 2-5 | 0.050 | 0.000 | 0.00 | 1529 | 15713 |
| q08 `LocalDate` | 2-5 | 0.070 | 0.000 | 0.00 | 12014 | 10327 |
| q09 `consultarQuantidadePar` | 2-5 | 0.050 | 0.000 | 0.00 | 1231 | 2879 |
| q10 `getNrInicial` | 2-5 | 0.050 | 0.000 | 0.00 | 988 | 1427 |
| q11 `possuiAssinaturaCossig` | 2-5 | 0.050 | 0.000 | 0.00 | 1218 | 2169 |
| q12 `zero` | 2-5 | 0.040 | 0.000 | 0.00 | 634 | 4895 |
| q13 `AGENDAMENTO_DE_PUBLICA` | 6-20 | 0.070 | 0.000 | 0.00 | 8313 | 13865 |
| q14 `Math` | 6-20 | 0.070 | 0.000 | 0.00 | 9375 | 14135 |
| q15 `converter` | 6-20 | 0.080 | 0.000 | 0.00 | 13557 | 15900 |
| q16 `getJuntados` | 6-20 | 0.080 | 0.000 | 0.00 | 4954 | 6390 |
| q17 `openoffice` | 6-20 | 0.070 | 0.000 | 0.00 | 11623 | 11675 |
| q18 `yyyy` | 6-20 | 0.070 | 0.000 | 0.00 | 4131 | 15881 |
| q19 `AplicacaoException` | 21-100 | 0.070 | 0.010 | 0.14 | 11938 | 15990 |
| q20 `Problem` | 21-100 | 0.070 | 0.000 | 0.00 | 12411 | 15858 |
| q21 `contains` | 21-100 | 0.040 | 0.010 | 0.25 | 2403 | 15785 |
| q22 `getTitular` | 21-100 | 0.080 | 0.000 | 0.00 | 12107 | 15972 |
| q23 `podeMovimentar` | 21-100 | 0.070 | 0.000 | 0.00 | 13052 | 15696 |
| q24 `write` | 21-100 | 0.070 | 0.000 | 0.00 | 3799 | 15956 |
| q25 `CompositeExpressionSup` | >100 | 0.070 | 0.000 | 0.00 | 13421 | 15926 |
| q26 `MERCHANTABILITY` | >100 | 0.070 | 0.010 | 0.14 | 12330 | 15667 |
| q27 `distributed` | >100 | 0.080 | 0.010 | 0.12 | 12026 | 15923 |
| q28 `later` | >100 | 0.070 | 0.010 | 0.14 | 3850 | 15858 |
| q29 `result` | >100 | 0.080 | 0.010 | 0.12 | 3825 | 15992 |
| q30 `your` | >100 | 0.070 | 0.010 | 0.14 | 3839 | 15831 |
| **resumo budget=4000** | — | — | — | p50 0.00 · máx 0.38 | | |

### Divergência semântica: declarado vs entregue

| orçamento | impl | estado (contagem) | bytes entregues (p50) | tokens declarados (p50) | bytes declarados (p50) | refs (p50) | trechos (p50) | arquivos (p50) | `tokenizer_is_exact` |
|---|---|---|---|---|---|---|---|---|---|
| 1000 | python | ok=105, partial=75 | 3914 | 438 | nao medido | 10 | 10 | 4 | False |
| 1000 | rust | ok=45, partial=135 | 3830 | 957 | 3829 | 3 | 3 | 3 | False |
| 2000 | python | ok=350, partial=10 | 3914 | 438 | nao medido | 10 | 10 | 4 | False |
| 2000 | rust | ok=110, partial=250 | 7708 | 1926 | 7708 | 7 | 7 | 6 | False |
| 4000 | python | ok=180 | 3914 | 438 | nao medido | 10 | 10 | 4 | False |
| 4000 | rust | ok=65, partial=115 | 14901 | 3724 | 14900 | 14 | 14 | 10 | False |

## Política `LEX-RS`

### Tempo de parede (s), por orçamento

| grupo | impl | n | min | p50 | p95 | max | média |
|---|---|---|---|---|---|---|---|
| 2000 | python | 180 | 0.040 | 0.070 | 0.130 | 0.180 | 0.074 |
| 2000 | rust | 180 | 0.000 | 0.000 | 0.010 | 0.010 | 0.002 |

### CPU user+sistema (s), por orçamento

| grupo | impl | n | min | p50 | p95 | max | média |
|---|---|---|---|---|---|---|---|
| 2000 | python | 180 | 0.030 | 0.060 | 0.130 | 0.170 | 0.069 |
| 2000 | rust | 180 | 0 | 0.000 | 0.000 | 0.010 | 0.000 |

### Pico de RSS (kB), por orçamento

| grupo | impl | n | min | p50 | p95 | max | média |
|---|---|---|---|---|---|---|---|
| 2000 | python | 180 | 25804.000 | 26564.000 | 28016.000 | 28732.000 | 26820.333 |
| 2000 | rust | 180 | 5368.000 | 6480.000 | 8664.000 | 9160.000 | 6648.689 |

### Razão Rust/Python por consulta (medianas pareadas)

| consulta | estrato | py wall p50 | rs wall p50 | razão rs/py | py bytes | rs bytes |
|---|---|---|---|---|---|---|
| e01 `ZzqR2TokenInexistenteN` | zero_match | 0.040 | 0.000 | 0.00 | 295 | 466 |
| e02 `movimentação` | unicode | 0.070 | 0.010 | 0.14 | 11884 | 7943 |
| e03 `ABCDEFGHIJLMNOPQRSTUZ ` | multi_token | 0.070 | 0.000 | 0.00 | 3839 | 3738 |
| e04 `ABCDEFGHIJLMNOPQRSTUZ ` | long | 0.100 | 0.010 | 0.10 | 10990 | 7967 |
| e05 `getId();` | punctuation | 0.060 | 0.000 | 0.00 | 17810 | 7914 |
| e06 `id` | short | 0.070 | 0.000 | 0.00 | 3979 | 7986 |
| q01 `ABCDEFGHIJLMNOPQRSTUZ` | 1 | 0.100 | 0.000 | 0.00 | 1398 | 913 |
| q02 `Reiniciar` | 1 | 0.160 | 0.010 | 0.06 | 2705 | 3227 |
| q03 `designar` | 1 | 0.110 | 0.000 | 0.00 | 694 | 1027 |
| q04 `htmlImage` | 1 | 0.140 | 0.000 | 0.00 | 3362 | 889 |
| q05 `predicateMobilRefComoM` | 1 | 0.100 | 0.000 | 0.00 | 1751 | 1082 |
| q06 `zone` | 1 | 0.110 | 0.000 | 0.00 | 960 | 806 |
| q07 `ACESSAR` | 2-5 | 0.060 | 0.000 | 0.00 | 1529 | 7909 |
| q08 `LocalDate` | 2-5 | 0.070 | 0.000 | 0.00 | 12014 | 2059 |
| q09 `consultarQuantidadePar` | 2-5 | 0.050 | 0.000 | 0.00 | 1231 | 1775 |
| q10 `getNrInicial` | 2-5 | 0.050 | 0.000 | 0.00 | 988 | 1090 |
| q11 `possuiAssinaturaCossig` | 2-5 | 0.050 | 0.000 | 0.00 | 1218 | 1606 |
| q12 `zero` | 2-5 | 0.040 | 0.000 | 0.00 | 634 | 3292 |
| q13 `AGENDAMENTO_DE_PUBLICA` | 6-20 | 0.060 | 0.000 | 0.00 | 8313 | 6082 |
| q14 `Math` | 6-20 | 0.060 | 0.000 | 0.00 | 9375 | 4607 |
| q15 `converter` | 6-20 | 0.060 | 0.000 | 0.00 | 13557 | 7961 |
| q16 `getJuntados` | 6-20 | 0.060 | 0.000 | 0.00 | 4954 | 3168 |
| q17 `openoffice` | 6-20 | 0.060 | 0.000 | 0.00 | 11623 | 4446 |
| q18 `yyyy` | 6-20 | 0.060 | 0.000 | 0.00 | 4131 | 7290 |
| q19 `AplicacaoException` | 21-100 | 0.070 | 0.000 | 0.00 | 11938 | 7984 |
| q20 `Problem` | 21-100 | 0.070 | 0.000 | 0.00 | 12411 | 7988 |
| q21 `contains` | 21-100 | 0.040 | 0.000 | 0.00 | 2403 | 7833 |
| q22 `getTitular` | 21-100 | 0.080 | 0.000 | 0.00 | 12107 | 7899 |
| q23 `podeMovimentar` | 21-100 | 0.070 | 0.000 | 0.00 | 13052 | 7893 |
| q24 `write` | 21-100 | 0.070 | 0.000 | 0.00 | 3799 | 7950 |
| q25 `CompositeExpressionSup` | >100 | 0.070 | 0.000 | 0.00 | 13421 | 7887 |
| q26 `MERCHANTABILITY` | >100 | 0.070 | 0.010 | 0.14 | 12330 | 7974 |
| q27 `distributed` | >100 | 0.070 | 0.010 | 0.14 | 12026 | 7981 |
| q28 `later` | >100 | 0.070 | 0.010 | 0.14 | 3850 | 7963 |
| q29 `result` | >100 | 0.070 | 0.000 | 0.00 | 3825 | 7958 |
| q30 `your` | >100 | 0.100 | 0.010 | 0.10 | 3839 | 7952 |
| **resumo budget=2000** | — | — | — | p50 0.00 · máx 0.14 | | |

### Divergência semântica: declarado vs entregue

| orçamento | impl | estado (contagem) | bytes entregues (p50) | tokens declarados (p50) | bytes declarados (p50) | refs (p50) | trechos (p50) | arquivos (p50) | `tokenizer_is_exact` |
|---|---|---|---|---|---|---|---|---|---|
| 2000 | python | ok=175, partial=5 | 3914 | 438 | nao medido | 10 | 10 | 4 | False |
| 2000 | rust | ok=85, partial=95 | 7562 | 1890 | 7560 | 12 | 12 | 12 | False |

## Fidelidade do orçamento declarado (todas as políticas)

| impl | n | bytes entregues (p50) | tokens estimados `chars//4` (p50) | tokens declarados (p50) | razão declarado/entregue (p50 · máx) | declara bytes entregues? | execuções acima de `max_bytes` | declarado acima de `budget_tokens` |
|---|---|---|---|---|---|---|---|---|
| python | 900 | 3914 | 978 | 438 | 0.45 · 0.50 | não | 315/900 | 0/900 |
| rust | 900 | 6830 | 1707 | 1707 | 1.00 · 1.00 | sim | 0/900 | 0/900 |

`ratio` é a mediana das razões **por execução** (declarado ÷ bytes entregues ÷ 4), não a razão de duas medianas: agregar antes de dividir esconderia justamente as execuções em que a declaração diverge.

## Construção do índice (dispersão, diretórios exclusivos)

### Tempo de parede (s)

| grupo | impl | n | min | p50 | p95 | max | média |
|---|---|---|---|---|---|---|---|
| index | python | 10 | 1.270 | 3.140 | 6.460 | 6.460 | 3.326 |
| index | rust | 10 | 0.050 | 0.050 | 0.150 | 0.150 | 0.066 |

### Pico de RSS (kB)

| grupo | impl | n | min | p50 | p95 | max | média |
|---|---|---|---|---|---|---|---|
| index | python | 10 | 21380.000 | 21738.000 | 22016.000 | 22016.000 | 21739.600 |
| index | rust | 10 | 9940.000 | 10542.000 | 10644.000 | 10644.000 | 10468.400 |

| impl | walls (todas as repetições) | índice (B) p50 | WAL (B) p50 |
|---|---|---|---|
| python | 5.520, 1.560, 5.790, 3.480, 1.530, 1.370, 6.460, 2.910, 1.270, 3.370 | 1781760 | 0 |
| rust | 0.050, 0.050, 0.060, 0.150, 0.050, 0.050, 0.080, 0.070, 0.050, 0.050 | 3727360 | 0 |

## Ciclo editar/testar: reindexar depois de uma mutação

A primeira indexação de cada cópia é *setup*, não medida: o número é o da passada seguinte à mutação, que é o que o agente paga a cada edição.

### Tempo de parede (s), por cenário

| cenário | impl | n | min | p50 | p95 | max | média |
|---|---|---|---|---|---|---|---|
| unchanged | python | 3 | 0.030 | 0.030 | 0.030 | 0.030 | 0.030 |
| unchanged | rust | 3 | 0.010 | 0.020 | 0.050 | 0.050 | 0.027 |
| edit_1 | python | 3 | 0.050 | 0.050 | 0.060 | 0.060 | 0.053 |
| edit_1 | rust | 3 | 0.020 | 0.020 | 0.040 | 0.040 | 0.027 |
| edit_10 | python | 3 | 0.060 | 0.140 | 0.220 | 0.220 | 0.140 |
| edit_10 | rust | 3 | 0.030 | 0.030 | 0.040 | 0.040 | 0.033 |
| edit_100 | python | 3 | 0.270 | 0.490 | 1.000 | 1.000 | 0.587 |
| edit_100 | rust | 3 | 0.070 | 0.100 | 0.110 | 0.110 | 0.093 |
| delete_1 | python | 3 | 0.030 | 0.040 | 0.050 | 0.050 | 0.040 |
| delete_1 | rust | 3 | 0.010 | 0.020 | 0.020 | 0.020 | 0.017 |
| rename_1 | python | 3 | 0.040 | 0.050 | 0.100 | 0.100 | 0.063 |
| rename_1 | rust | 3 | 0.020 | 0.020 | 0.030 | 0.030 | 0.023 |

### Pico de RSS (kB), por cenário

| grupo | impl | n | min | p50 | p95 | max | média |
|---|---|---|---|---|---|---|---|
| delete_1 | python | 3 | 19476.000 | 19512.000 | 19584.000 | 19584.000 | 19524.000 |
| delete_1 | rust | 3 | 7520.000 | 7556.000 | 7560.000 | 7560.000 | 7545.333 |
| edit_1 | python | 3 | 19716.000 | 19728.000 | 19876.000 | 19876.000 | 19773.333 |
| edit_1 | rust | 3 | 7884.000 | 8108.000 | 8164.000 | 8164.000 | 8052.000 |
| edit_10 | python | 3 | 19852.000 | 19888.000 | 19972.000 | 19972.000 | 19904.000 |
| edit_10 | rust | 3 | 8752.000 | 9032.000 | 9052.000 | 9052.000 | 8945.333 |
| edit_100 | python | 3 | 19972.000 | 20504.000 | 20520.000 | 20520.000 | 20332.000 |
| edit_100 | rust | 3 | 8788.000 | 8920.000 | 9068.000 | 9068.000 | 8925.333 |
| rename_1 | python | 3 | 19264.000 | 19384.000 | 19508.000 | 19508.000 | 19385.333 |
| rename_1 | rust | 3 | 7516.000 | 7632.000 | 7740.000 | 7740.000 | 7629.333 |
| unchanged | python | 3 | 19188.000 | 19372.000 | 19384.000 | 19384.000 | 19314.667 |
| unchanged | rust | 3 | 6108.000 | 6224.000 | 6320.000 | 6320.000 | 6217.333 |

### O que cada lado declara ter reindexado, e a checagem independente

| cenário | impl | arquivos mutados | reindexados (p50) | pulados (p50) | removidos (p50) | equivale a rebuild |
|---|---|---|---|---|---|---|
| unchanged | python | 0 | 0 | 504 | 0 | sim (3/3) |
| unchanged | rust | 0 | 0 | 504 | 0 | sim (3/3) |
| edit_1 | python | 1 | 1 | 503 | 0 | sim (3/3) |
| edit_1 | rust | 1 | 1 | 503 | 0 | sim (3/3) |
| edit_10 | python | 10 | 10 | 494 | 0 | sim (3/3) |
| edit_10 | rust | 10 | 10 | 494 | 0 | sim (3/3) |
| edit_100 | python | 100 | 100 | 404 | 0 | sim (3/3) |
| edit_100 | rust | 100 | 100 | 404 | 0 | sim (3/3) |
| delete_1 | python | 1 | 0 | 503 | 1 | sim (3/3) |
| delete_1 | rust | 1 | 0 | 503 | 1 | sim (3/3) |
| rename_1 | python | 1 | 1 | 503 | 1 | sim (3/3) |
| rename_1 | rust | 1 | 1 | 503 | 1 | sim (3/3) |

`equivale a rebuild` é checagem independente do que o comando declara: para o Rust, uma reindexação do zero (com `--force`) na mesma árvore mutada tem de produzir a **mesma geração**; para a referência Python, que não publica geração, o conjunto de arquivos dentro do índice tem de ser exatamente o do disco.

## `doctor` (processo novo, cache aquecido)

### Tempo de parede (s)

| grupo | impl | n | min | p50 | p95 | max | média |
|---|---|---|---|---|---|---|---|
| doctor | python | 10 | 0.020 | 0.020 | 0.030 | 0.030 | 0.021 |
| doctor | rust | 10 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

### Pico de RSS (kB)

| grupo | impl | n | min | p50 | p95 | max | média |
|---|---|---|---|---|---|---|---|
| doctor | python | 10 | 18440.000 | 18876.000 | 18992.000 | 18992.000 | 18802.800 |
| doctor | rust | 10 | 5044.000 | 5082.000 | 5192.000 | 5192.000 | 5089.600 |

| impl | walls |
|---|---|
| python | 0.020, 0.020, 0.020, 0.020, 0.020, 0.020, 0.020, 0.030, 0.020, 0.020 |
| rust | 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000 |

## Convenções

- Quantis por **posto mais próximo** em amostra ordenada; p50 = mediana (média dos dois centrais quando n é par).
- Tempo medido do **spawn até consumir todo o stdout**, com GNU time. Nenhuma medição é de função interna.
- Cache de filesystem **aquecido**. Frio não foi medido: exigiria `drop_caches` com root numa máquina dedicada.
- Ordem **alternada por repetição**: cada braço ocupa cada posição metade das vezes.

