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
| 1000 | python | 180 | 0.050 | 0.120 | 0.190 | 0.280 | 0.122 |
| 1000 | rust | 180 | 0.000 | 0.010 | 0.020 | 0.050 | 0.008 |
| 2000 | python | 360 | 0.040 | 0.110 | 0.200 | 0.380 | 0.119 |
| 2000 | rust | 360 | 0.000 | 0.010 | 0.030 | 0.060 | 0.008 |
| 4000 | python | 180 | 0.050 | 0.090 | 0.180 | 0.240 | 0.103 |
| 4000 | rust | 180 | 0.000 | 0.000 | 0.020 | 0.070 | 0.008 |

### CPU user+sistema (s), por orçamento

| grupo | impl | n | min | p50 | p95 | max | média |
|---|---|---|---|---|---|---|---|
| 1000 | python | 180 | 0.050 | 0.110 | 0.180 | 0.260 | 0.114 |
| 1000 | rust | 180 | 0 | 0.000 | 0.020 | 0.040 | 0.004 |
| 2000 | python | 360 | 0.040 | 0.100 | 0.170 | 0.320 | 0.107 |
| 2000 | rust | 360 | 0 | 0.000 | 0.020 | 0.050 | 0.004 |
| 4000 | python | 180 | 0.040 | 0.090 | 0.160 | 0.240 | 0.096 |
| 4000 | rust | 180 | 0 | 0.000 | 0.010 | 0.070 | 0.004 |

### Pico de RSS (kB), por orçamento

| grupo | impl | n | min | p50 | p95 | max | média |
|---|---|---|---|---|---|---|---|
| 1000 | python | 180 | 25856.000 | 26592.000 | 28132.000 | 28684.000 | 26859.889 |
| 1000 | rust | 180 | 5364.000 | 6630.000 | 8968.000 | 13604.000 | 7023.756 |
| 2000 | python | 360 | 26004.000 | 26684.000 | 28148.000 | 28888.000 | 26954.700 |
| 2000 | rust | 360 | 5372.000 | 6672.000 | 8936.000 | 13676.000 | 7056.011 |
| 4000 | python | 180 | 25904.000 | 26598.000 | 28108.000 | 28732.000 | 26919.889 |
| 4000 | rust | 180 | 5384.000 | 6692.000 | 8964.000 | 13616.000 | 7037.844 |

### Razão Rust/Python por consulta (medianas pareadas)

| consulta | estrato | py wall p50 | rs wall p50 | razão rs/py | py bytes | rs bytes |
|---|---|---|---|---|---|---|
| e01 `ZzqR2TokenInexistenteN` | zero_match | 0.070 | 0.000 | 0.00 | 295 | 466 |
| e02 `movimentação` | unicode | 0.120 | 0.040 | 0.33 | 8440 | 668 |
| e03 `ABCDEFGHIJLMNOPQRSTUZ ` | multi_token | 0.130 | 0.000 | 0.00 | 3839 | 3895 |
| e04 `ABCDEFGHIJLMNOPQRSTUZ ` | long | 0.120 | 0.010 | 0.08 | 8130 | 3859 |
| e05 `getId();` | punctuation | 0.090 | 0.010 | 0.11 | 8858 | 3978 |
| e06 `id` | short | 0.140 | 0.020 | 0.14 | 3979 | 1969 |
| q01 `ABCDEFGHIJLMNOPQRSTUZ` | 1 | 0.080 | 0.000 | 0.00 | 1398 | 2855 |
| q02 `Reiniciar` | 1 | 0.090 | 0.000 | 0.00 | 2705 | 3919 |
| q03 `designar` | 1 | 0.120 | 0.000 | 0.00 | 694 | 1489 |
| q04 `htmlImage` | 1 | 0.120 | 0.000 | 0.00 | 3362 | 1795 |
| q05 `predicateMobilRefComoM` | 1 | 0.150 | 0.000 | 0.00 | 1751 | 2036 |
| q06 `zone` | 1 | 0.130 | 0.000 | 0.00 | 960 | 1105 |
| q07 `ACESSAR` | 2-5 | 0.130 | 0.010 | 0.08 | 1529 | 3848 |
| q08 `LocalDate` | 2-5 | 0.230 | 0.010 | 0.04 | 8489 | 3817 |
| q09 `consultarQuantidadePar` | 2-5 | 0.210 | 0.010 | 0.05 | 1231 | 2878 |
| q10 `getNrInicial` | 2-5 | 0.170 | 0.000 | 0.00 | 988 | 1426 |
| q11 `possuiAssinaturaCossig` | 2-5 | 0.120 | 0.010 | 0.08 | 1218 | 2168 |
| q12 `zero` | 2-5 | 0.090 | 0.000 | 0.00 | 634 | 3888 |
| q13 `AGENDAMENTO_DE_PUBLICA` | 6-20 | 0.120 | 0.000 | 0.00 | 7906 | 3870 |
| q14 `Math` | 6-20 | 0.100 | 0.000 | 0.00 | 8252 | 3826 |
| q15 `converter` | 6-20 | 0.100 | 0.000 | 0.00 | 8715 | 3925 |
| q16 `getJuntados` | 6-20 | 0.090 | 0.000 | 0.00 | 4954 | 3922 |
| q17 `openoffice` | 6-20 | 0.120 | 0.000 | 0.00 | 8768 | 3940 |
| q18 `yyyy` | 6-20 | 0.110 | 0.010 | 0.09 | 4131 | 3933 |
| q19 `AplicacaoException` | 21-100 | 0.110 | 0.010 | 0.09 | 8446 | 3682 |
| q20 `Problem` | 21-100 | 0.090 | 0.000 | 0.00 | 7966 | 3801 |
| q21 `contains` | 21-100 | 0.070 | 0.010 | 0.14 | 2403 | 3969 |
| q22 `getTitular` | 21-100 | 0.150 | 0.010 | 0.07 | 8338 | 3959 |
| q23 `podeMovimentar` | 21-100 | 0.140 | 0.000 | 0.00 | 7919 | 3796 |
| q24 `write` | 21-100 | 0.160 | 0.010 | 0.06 | 3799 | 3894 |
| q25 `CompositeExpressionSup` | >100 | 0.100 | 0.010 | 0.10 | 8195 | 3711 |
| q26 `MERCHANTABILITY` | >100 | 0.130 | 0.020 | 0.15 | 8311 | 3716 |
| q27 `distributed` | >100 | 0.130 | 0.020 | 0.15 | 8501 | 3951 |
| q28 `later` | >100 | 0.130 | 0.020 | 0.15 | 3850 | 3843 |
| q29 `result` | >100 | 0.080 | 0.010 | 0.12 | 3825 | 3974 |
| q30 `your` | >100 | 0.120 | 0.020 | 0.17 | 3839 | 3834 |
| **resumo budget=1000** | — | — | — | p50 0.05 · máx 0.33 | | |
| e01 `ZzqR2TokenInexistenteN` | zero_match | 0.110 | 0.000 | 0.00 | 295 | 466 |
| e02 `movimentação` | unicode | 0.155 | 0.050 | 0.32 | 11884 | 5961 |
| e03 `ABCDEFGHIJLMNOPQRSTUZ ` | multi_token | 0.220 | 0.010 | 0.05 | 3839 | 7821 |
| e04 `ABCDEFGHIJLMNOPQRSTUZ ` | long | 0.190 | 0.020 | 0.11 | 10990 | 7689 |
| e05 `getId();` | punctuation | 0.135 | 0.010 | 0.07 | 17810 | 7810 |
| e06 `id` | short | 0.100 | 0.010 | 0.10 | 3979 | 6936 |
| q01 `ABCDEFGHIJLMNOPQRSTUZ` | 1 | 0.095 | 0.000 | 0.00 | 1398 | 2855 |
| q02 `Reiniciar` | 1 | 0.090 | 0.000 | 0.00 | 2705 | 6830 |
| q03 `designar` | 1 | 0.085 | 0.000 | 0.00 | 694 | 1489 |
| q04 `htmlImage` | 1 | 0.090 | 0.000 | 0.00 | 3362 | 1795 |
| q05 `predicateMobilRefComoM` | 1 | 0.095 | 0.000 | 0.00 | 1751 | 2036 |
| q06 `zone` | 1 | 0.075 | 0.000 | 0.00 | 960 | 1105 |
| q07 `ACESSAR` | 2-5 | 0.085 | 0.010 | 0.12 | 1529 | 7942 |
| q08 `LocalDate` | 2-5 | 0.105 | 0.000 | 0.00 | 12014 | 7861 |
| q09 `consultarQuantidadePar` | 2-5 | 0.095 | 0.000 | 0.00 | 1231 | 2878 |
| q10 `getNrInicial` | 2-5 | 0.100 | 0.000 | 0.00 | 988 | 1426 |
| q11 `possuiAssinaturaCossig` | 2-5 | 0.090 | 0.005 | 0.06 | 1218 | 2168 |
| q12 `zero` | 2-5 | 0.075 | 0.000 | 0.00 | 634 | 4894 |
| q13 `AGENDAMENTO_DE_PUBLICA` | 6-20 | 0.090 | 0.000 | 0.00 | 8313 | 7881 |
| q14 `Math` | 6-20 | 0.120 | 0.005 | 0.04 | 9375 | 7925 |
| q15 `converter` | 6-20 | 0.125 | 0.010 | 0.08 | 13557 | 7733 |
| q16 `getJuntados` | 6-20 | 0.160 | 0.010 | 0.06 | 4954 | 6389 |
| q17 `openoffice` | 6-20 | 0.140 | 0.000 | 0.00 | 11623 | 7944 |
| q18 `yyyy` | 6-20 | 0.115 | 0.010 | 0.09 | 4131 | 7920 |
| q19 `AplicacaoException` | 21-100 | 0.110 | 0.010 | 0.09 | 11938 | 7881 |
| q20 `Problem` | 21-100 | 0.105 | 0.000 | 0.00 | 12411 | 7634 |
| q21 `contains` | 21-100 | 0.070 | 0.010 | 0.14 | 2403 | 7897 |
| q22 `getTitular` | 21-100 | 0.125 | 0.005 | 0.04 | 12107 | 7853 |
| q23 `podeMovimentar` | 21-100 | 0.095 | 0.000 | 0.00 | 13052 | 7704 |
| q24 `write` | 21-100 | 0.120 | 0.010 | 0.08 | 3799 | 7518 |
| q25 `CompositeExpressionSup` | >100 | 0.130 | 0.010 | 0.08 | 13421 | 7979 |
| q26 `MERCHANTABILITY` | >100 | 0.130 | 0.020 | 0.15 | 12330 | 7713 |
| q27 `distributed` | >100 | 0.130 | 0.020 | 0.15 | 12026 | 7885 |
| q28 `later` | >100 | 0.120 | 0.020 | 0.17 | 3850 | 7946 |
| q29 `result` | >100 | 0.135 | 0.015 | 0.11 | 3825 | 7738 |
| q30 `your` | >100 | 0.135 | 0.020 | 0.15 | 3839 | 7930 |
| **resumo budget=2000** | — | — | — | p50 0.05 · máx 0.32 | | |
| e01 `ZzqR2TokenInexistenteN` | zero_match | 0.130 | 0.000 | 0.00 | 295 | 467 |
| e02 `movimentação` | unicode | 0.220 | 0.060 | 0.27 | 11884 | 14100 |
| e03 `ABCDEFGHIJLMNOPQRSTUZ ` | multi_token | 0.210 | 0.000 | 0.00 | 3839 | 9283 |
| e04 `ABCDEFGHIJLMNOPQRSTUZ ` | long | 0.140 | 0.010 | 0.07 | 10990 | 15922 |
| e05 `getId();` | punctuation | 0.080 | 0.010 | 0.12 | 18155 | 15948 |
| e06 `id` | short | 0.080 | 0.010 | 0.12 | 3979 | 15967 |
| q01 `ABCDEFGHIJLMNOPQRSTUZ` | 1 | 0.160 | 0.010 | 0.06 | 1398 | 2856 |
| q02 `Reiniciar` | 1 | 0.120 | 0.010 | 0.08 | 2705 | 6831 |
| q03 `designar` | 1 | 0.080 | 0.000 | 0.00 | 694 | 1490 |
| q04 `htmlImage` | 1 | 0.120 | 0.000 | 0.00 | 3362 | 1796 |
| q05 `predicateMobilRefComoM` | 1 | 0.060 | 0.000 | 0.00 | 1751 | 2037 |
| q06 `zone` | 1 | 0.060 | 0.000 | 0.00 | 960 | 1106 |
| q07 `ACESSAR` | 2-5 | 0.060 | 0.000 | 0.00 | 1529 | 15713 |
| q08 `LocalDate` | 2-5 | 0.120 | 0.000 | 0.00 | 12014 | 10327 |
| q09 `consultarQuantidadePar` | 2-5 | 0.070 | 0.000 | 0.00 | 1231 | 2879 |
| q10 `getNrInicial` | 2-5 | 0.060 | 0.000 | 0.00 | 988 | 1427 |
| q11 `possuiAssinaturaCossig` | 2-5 | 0.060 | 0.000 | 0.00 | 1218 | 2169 |
| q12 `zero` | 2-5 | 0.070 | 0.000 | 0.00 | 634 | 4895 |
| q13 `AGENDAMENTO_DE_PUBLICA` | 6-20 | 0.100 | 0.010 | 0.10 | 8313 | 13865 |
| q14 `Math` | 6-20 | 0.080 | 0.000 | 0.00 | 9375 | 14135 |
| q15 `converter` | 6-20 | 0.090 | 0.000 | 0.00 | 13557 | 15900 |
| q16 `getJuntados` | 6-20 | 0.100 | 0.000 | 0.00 | 4954 | 6390 |
| q17 `openoffice` | 6-20 | 0.120 | 0.000 | 0.00 | 11623 | 11675 |
| q18 `yyyy` | 6-20 | 0.080 | 0.010 | 0.12 | 4131 | 15881 |
| q19 `AplicacaoException` | 21-100 | 0.100 | 0.010 | 0.10 | 11938 | 15990 |
| q20 `Problem` | 21-100 | 0.080 | 0.000 | 0.00 | 12411 | 15858 |
| q21 `contains` | 21-100 | 0.050 | 0.010 | 0.20 | 2403 | 15785 |
| q22 `getTitular` | 21-100 | 0.140 | 0.010 | 0.07 | 12107 | 15972 |
| q23 `podeMovimentar` | 21-100 | 0.130 | 0.000 | 0.00 | 13052 | 15696 |
| q24 `write` | 21-100 | 0.100 | 0.010 | 0.10 | 3799 | 15956 |
| q25 `CompositeExpressionSup` | >100 | 0.090 | 0.000 | 0.00 | 13421 | 15926 |
| q26 `MERCHANTABILITY` | >100 | 0.090 | 0.010 | 0.11 | 12330 | 15667 |
| q27 `distributed` | >100 | 0.160 | 0.030 | 0.19 | 12026 | 15923 |
| q28 `later` | >100 | 0.100 | 0.010 | 0.10 | 3850 | 15858 |
| q29 `result` | >100 | 0.090 | 0.010 | 0.11 | 3825 | 15992 |
| q30 `your` | >100 | 0.110 | 0.020 | 0.18 | 3839 | 15831 |
| **resumo budget=4000** | — | — | — | p50 0.00 · máx 0.27 | | |

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
| 2000 | python | 180 | 0.050 | 0.130 | 0.250 | 0.300 | 0.133 |
| 2000 | rust | 180 | 0.000 | 0.010 | 0.030 | 0.050 | 0.009 |

### CPU user+sistema (s), por orçamento

| grupo | impl | n | min | p50 | p95 | max | média |
|---|---|---|---|---|---|---|---|
| 2000 | python | 180 | 0.050 | 0.110 | 0.200 | 0.260 | 0.116 |
| 2000 | rust | 180 | 0 | 0.000 | 0.010 | 0.020 | 0.002 |

### Pico de RSS (kB), por orçamento

| grupo | impl | n | min | p50 | p95 | max | média |
|---|---|---|---|---|---|---|---|
| 2000 | python | 180 | 26040.000 | 26698.000 | 28196.000 | 28804.000 | 26987.933 |
| 2000 | rust | 180 | 5296.000 | 6500.000 | 8756.000 | 9204.000 | 6707.400 |

### Razão Rust/Python por consulta (medianas pareadas)

| consulta | estrato | py wall p50 | rs wall p50 | razão rs/py | py bytes | rs bytes |
|---|---|---|---|---|---|---|
| e01 `ZzqR2TokenInexistenteN` | zero_match | 0.090 | 0.000 | 0.00 | 295 | 466 |
| e02 `movimentação` | unicode | 0.120 | 0.020 | 0.17 | 11884 | 7943 |
| e03 `ABCDEFGHIJLMNOPQRSTUZ ` | multi_token | 0.140 | 0.000 | 0.00 | 3839 | 3738 |
| e04 `ABCDEFGHIJLMNOPQRSTUZ ` | long | 0.130 | 0.010 | 0.08 | 10990 | 7967 |
| e05 `getId();` | punctuation | 0.090 | 0.010 | 0.11 | 17810 | 7914 |
| e06 `id` | short | 0.100 | 0.010 | 0.10 | 3979 | 7986 |
| q01 `ABCDEFGHIJLMNOPQRSTUZ` | 1 | 0.070 | 0.000 | 0.00 | 1398 | 913 |
| q02 `Reiniciar` | 1 | 0.070 | 0.000 | 0.00 | 2705 | 3227 |
| q03 `designar` | 1 | 0.100 | 0.000 | 0.00 | 694 | 1027 |
| q04 `htmlImage` | 1 | 0.130 | 0.000 | 0.00 | 3362 | 889 |
| q05 `predicateMobilRefComoM` | 1 | 0.060 | 0.000 | 0.00 | 1751 | 1082 |
| q06 `zone` | 1 | 0.080 | 0.000 | 0.00 | 960 | 806 |
| q07 `ACESSAR` | 2-5 | 0.100 | 0.010 | 0.10 | 1529 | 7909 |
| q08 `LocalDate` | 2-5 | 0.120 | 0.000 | 0.00 | 12014 | 2059 |
| q09 `consultarQuantidadePar` | 2-5 | 0.060 | 0.000 | 0.00 | 1231 | 1775 |
| q10 `getNrInicial` | 2-5 | 0.090 | 0.000 | 0.00 | 988 | 1090 |
| q11 `possuiAssinaturaCossig` | 2-5 | 0.110 | 0.000 | 0.00 | 1218 | 1606 |
| q12 `zero` | 2-5 | 0.080 | 0.000 | 0.00 | 634 | 3292 |
| q13 `AGENDAMENTO_DE_PUBLICA` | 6-20 | 0.110 | 0.010 | 0.09 | 8313 | 6082 |
| q14 `Math` | 6-20 | 0.120 | 0.010 | 0.08 | 9375 | 4607 |
| q15 `converter` | 6-20 | 0.140 | 0.010 | 0.07 | 13557 | 7961 |
| q16 `getJuntados` | 6-20 | 0.160 | 0.000 | 0.00 | 4954 | 3168 |
| q17 `openoffice` | 6-20 | 0.150 | 0.000 | 0.00 | 11623 | 4446 |
| q18 `yyyy` | 6-20 | 0.120 | 0.010 | 0.08 | 4131 | 7290 |
| q19 `AplicacaoException` | 21-100 | 0.150 | 0.010 | 0.07 | 11938 | 7984 |
| q20 `Problem` | 21-100 | 0.190 | 0.010 | 0.05 | 12411 | 7988 |
| q21 `contains` | 21-100 | 0.160 | 0.020 | 0.12 | 2403 | 7833 |
| q22 `getTitular` | 21-100 | 0.220 | 0.020 | 0.09 | 12107 | 7899 |
| q23 `podeMovimentar` | 21-100 | 0.200 | 0.010 | 0.05 | 13052 | 7893 |
| q24 `write` | 21-100 | 0.260 | 0.040 | 0.15 | 3799 | 7950 |
| q25 `CompositeExpressionSup` | >100 | 0.200 | 0.010 | 0.05 | 13421 | 7887 |
| q26 `MERCHANTABILITY` | >100 | 0.130 | 0.010 | 0.08 | 12330 | 7974 |
| q27 `distributed` | >100 | 0.130 | 0.020 | 0.15 | 12026 | 7981 |
| q28 `later` | >100 | 0.130 | 0.020 | 0.15 | 3850 | 7963 |
| q29 `result` | >100 | 0.130 | 0.010 | 0.08 | 3825 | 7958 |
| q30 `your` | >100 | 0.130 | 0.020 | 0.15 | 3839 | 7952 |
| **resumo budget=2000** | — | — | — | p50 0.06 · máx 0.17 | | |

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
| index | python | 10 | 0.850 | 0.940 | 3.930 | 3.930 | 1.240 |
| index | rust | 10 | 0.050 | 0.050 | 0.080 | 0.080 | 0.055 |

### Pico de RSS (kB)

| grupo | impl | n | min | p50 | p95 | max | média |
|---|---|---|---|---|---|---|---|
| index | python | 10 | 21368.000 | 21762.000 | 21936.000 | 21936.000 | 21725.200 |
| index | rust | 10 | 10196.000 | 10596.000 | 10804.000 | 10804.000 | 10532.000 |

| impl | walls (todas as repetições) | índice (B) p50 | WAL (B) p50 |
|---|---|---|---|
| python | 0.940, 0.870, 0.850, 0.920, 1.000, 1.030, 0.990, 0.930, 0.940, 3.930 | 1781760 | 0 |
| rust | 0.050, 0.050, 0.050, 0.050, 0.050, 0.060, 0.050, 0.050, 0.060, 0.080 | 3727360 | 0 |

## Ciclo editar/testar: reindexar depois de uma mutação

A primeira indexação de cada cópia é *setup*, não medida: o número é o da passada seguinte à mutação, que é o que o agente paga a cada edição.

### Tempo de parede (s), por cenário

| cenário | impl | n | min | p50 | p95 | max | média |
|---|---|---|---|---|---|---|---|
| unchanged | python | 3 | 0.040 | 0.040 | 0.050 | 0.050 | 0.043 |
| unchanged | rust | 3 | 0.010 | 0.020 | 0.050 | 0.050 | 0.027 |
| edit_1 | python | 3 | 0.050 | 0.050 | 0.080 | 0.080 | 0.060 |
| edit_1 | rust | 3 | 0.040 | 0.050 | 0.050 | 0.050 | 0.047 |
| edit_10 | python | 3 | 0.100 | 0.140 | 0.170 | 0.170 | 0.137 |
| edit_10 | rust | 3 | 0.040 | 0.050 | 0.070 | 0.070 | 0.053 |
| edit_100 | python | 3 | 0.590 | 0.990 | 1.020 | 1.020 | 0.867 |
| edit_100 | rust | 3 | 0.090 | 0.100 | 0.130 | 0.130 | 0.107 |
| delete_1 | python | 3 | 0.050 | 0.060 | 0.100 | 0.100 | 0.070 |
| delete_1 | rust | 3 | 0.020 | 0.040 | 0.050 | 0.050 | 0.037 |
| rename_1 | python | 3 | 0.050 | 0.050 | 0.060 | 0.060 | 0.053 |
| rename_1 | rust | 3 | 0.020 | 0.040 | 0.050 | 0.050 | 0.037 |

### Pico de RSS (kB), por cenário

| grupo | impl | n | min | p50 | p95 | max | média |
|---|---|---|---|---|---|---|---|
| delete_1 | python | 3 | 19180.000 | 19324.000 | 19544.000 | 19544.000 | 19349.333 |
| delete_1 | rust | 3 | 7608.000 | 7608.000 | 7624.000 | 7624.000 | 7613.333 |
| edit_1 | python | 3 | 19688.000 | 19796.000 | 19900.000 | 19900.000 | 19794.667 |
| edit_1 | rust | 3 | 7780.000 | 7816.000 | 7876.000 | 7876.000 | 7824.000 |
| edit_10 | python | 3 | 19612.000 | 19756.000 | 19864.000 | 19864.000 | 19744.000 |
| edit_10 | rust | 3 | 8944.000 | 9000.000 | 9080.000 | 9080.000 | 9008.000 |
| edit_100 | python | 3 | 19808.000 | 20032.000 | 20356.000 | 20356.000 | 20065.333 |
| edit_100 | rust | 3 | 8812.000 | 8840.000 | 8880.000 | 8880.000 | 8844.000 |
| rename_1 | python | 3 | 19352.000 | 19428.000 | 19472.000 | 19472.000 | 19417.333 |
| rename_1 | rust | 3 | 7444.000 | 7636.000 | 7652.000 | 7652.000 | 7577.333 |
| unchanged | python | 3 | 19480.000 | 19564.000 | 19600.000 | 19600.000 | 19548.000 |
| unchanged | rust | 3 | 6000.000 | 6064.000 | 6316.000 | 6316.000 | 6126.667 |

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

## `expand`: segundo passo do ciclo de recuperação

Sem braço Python: a CLI de referência não tem `expand`. As tabelas são do braço Rust, e a coluna `no_overlap` é checada no harness por interseção de intervalos — não lida de `omitted.reasons`.

| orçamento | `evidence_wanted` | n | wall p50 | wall p95 | RSS p50 (kB) | unidades p50 | bytes p50 | bytes do `context` de setup p50 | razão expand/context | sem sobreposição | `used_bytes` exato |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2000 | `context` | 175 | 0.000 | 0.000 | 5404 | 8 | 7719 | 7712 | 1.01 | 175/175 | 175/175 |
| 2000 | `references` | 175 | 0.000 | 0.030 | 6292 | 8 | 7876 | 7712 | 1.02 | 175/175 | 175/175 |
| 8000 | `context` | 175 | 0.000 | 0.020 | 5576 | 29 | 25871 | 28783 | 1.00 | 175/175 | 175/175 |
| 8000 | `references` | 175 | 0.010 | 0.050 | 6152 | 30 | 30054 | 28783 | 1.00 | 175/175 | 175/175 |

Estados declarados: `ok`=285, `partial`=415. A razão `expand/context` mostra quanto material **novo** a expansão adiciona sobre a chamada anterior.

Em **39 de 70** pares (consulta, orçamento), `evidence_wanted=references` devolveu o **mesmo** número de unidades e os **mesmos** bytes que `evidence_wanted=context`. As janelas ao redor de `known_refs` são geradas primeiro e consomem o teto antes de a busca lexical contribuir; nos pares em que os dois diferem, sobrou orçamento para a busca.

## `verify`: portão de integridade

Sem braço Python: `verify` existe na referência como autoteste fixo de um arquivo, sem `--ref`. O código de saída esperado de cada cenário foi fixado **antes** da medição, então `saiu como esperado` é checagem do harness.

| cenário | n | esperado | saiu como esperado | wall p50 | wall p95 | RSS p50 (kB) | `state` declarado | `used_bytes` exato |
|---|---|---|---|---|---|---|---|---|
| `ok` | 175 | exit 0 | 175/175 | 0.000 | 0.010 | 5372 | ok=175 | 175/175 |
| `sem_hash` | 175 | exit 0 | 175/175 | 0.000 | 0.010 | 5340 | ok=175 | 175/175 |
| `hash_divergente` | 175 | exit 5 | 175/175 | 0.000 | 0.010 | 5360 | partial=175 | 175/175 |
| `linha_fora` | 175 | exit 5 | 175/175 | 0.000 | 0.010 | 5360 | partial=175 | 175/175 |
| `caminho_fora` | 175 | exit 5 | 175/175 | 0.000 | 0.010 | 5068 | partial=175 | 175/175 |

Motivos agregados de `omitted.reasons` nos cenários reprovados: `hash_divergent`=175, `line_out_of_range`=175, `outside_root`=175.

## `doctor` (processo novo, cache aquecido)

### Tempo de parede (s)

| grupo | impl | n | min | p50 | p95 | max | média |
|---|---|---|---|---|---|---|---|
| doctor | python | 10 | 0.030 | 0.040 | 0.050 | 0.050 | 0.039 |
| doctor | rust | 10 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

### Pico de RSS (kB)

| grupo | impl | n | min | p50 | p95 | max | média |
|---|---|---|---|---|---|---|---|
| doctor | python | 10 | 18744.000 | 18956.000 | 19112.000 | 19112.000 | 18931.200 |
| doctor | rust | 10 | 4872.000 | 5062.000 | 5192.000 | 5192.000 | 5061.600 |

| impl | walls |
|---|---|
| python | 0.030, 0.040, 0.040, 0.040, 0.040, 0.040, 0.040, 0.040, 0.030, 0.050 |
| rust | 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000 |

## Convenções

- Quantis por **posto mais próximo** em amostra ordenada; p50 = mediana (média dos dois centrais quando n é par).
- Tempo medido do **spawn até consumir todo o stdout**, com GNU time. Nenhuma medição é de função interna.
- Cache de filesystem **aquecido**. Frio não foi medido: exigiria `drop_caches` com root numa máquina dedicada.
- Ordem **alternada por repetição**: cada braço ocupa cada posição metade das vezes.

