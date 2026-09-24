# Cego multi-hop H — F16 (2026-09-24)

## Placar (arestas GT verificadas, 8 no total)
| agente | H-000 | H-001 | H-002 | H-003 | total | tempo | passos |
|---|---|---|---|---|---|---|---|
| RAW | 2/2 | 2/2 | 2/2 | 1/2 | **7/8** | 66s | 18 |
| TRACE | 2/2 | 2/2 | 2/2 | 1/2 | **7/8** | **~2.7s** (index 504 incl.) | 2-4 |

## Achados
1. **Empate técnico, goleada em velocidade:** mesma assertividade (7/8), TRACE ~24× mais rápido; queries pós-index ~0ms vs dezenas de segundos de grep+leitura.
2. **H-003 revela ambiguidade real:** `converter → ByteArrayInputStream` existe em `FlyingSaucer.java:223`, `FOP.java:144` e `Nheengatu.java:42` (GT escolheu a última). Múltiplos caminhos válidos → GT-caminho-único subestima; F17 usará GT-conjunto de caminhos.
3. RAW precisou ler 4+ arquivos por questão; TRACE respondeu do índice com confirmação pontual — o padrão "memória externa + verificação" escala para cadeias longas onde exploração manual degrada.
