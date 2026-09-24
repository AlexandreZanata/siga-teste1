# Teste cego 3 abordagens — F10 (2026-09-24, SIGA `e3be22828`)

## Protocolo
8 perguntas (A-000, D-000 + C/E/G/F-000, E/G-003 corretas do GT). Agentes sem gabarito, tempo parede e passos registrados. Apuração do orquestrador: estrita (casa GT) + substantiva (fato verificado por leitura).

**Incidente honesto:** round-1 usei enunciados errados em 6/8 (assumi GT sem ler — o anti-padrão que proibimos). Round-1 vale só p/ A-000/D-000 (3/3 todos). Round-2 refeito com texto exato do GT.

## Round-2 (6Qs, placar estrito / substantivo)
| agente | estrito | substantivo | tempo | passos | zeros ("não encontrado") |
|---|---|---|---|---|---|
| RAW (grep/read) | 2/6 (C,F) | 6/6 | 29.8s | 9 | 0 |
| ATLAS (cápsula) | 2/6 (C,F) | 2/6 | ~106s sessão (queries 0.35s; index 2.4s) | ~6 | 4 honestos |
| ATLAS+CALLS | 3/6 (C,F + G-000) | 6/6 | 70.1s (núcleo 13.5s) | 10 | 0 |

## Achados (o que importa)
1. **GT-arquivo-único pune respostas válidas:** E-003/G-003 têm callers em `CpBL.java`/`Stamp.java`/`ExBL.java` além do GT (`FOP.java:61`) — todos verificados por leitura. Benchmark deve evoluir p/ GT-conjunto (F11).
2. **Falha real da cápsula pura:** queries sem símbolo indexado (`length`, `getResourceAsStream` — métodos JDK) → cápsula vazia → 4 zeros honestos mas inúteis. ATLAS+CALLS recuperou via `find_references`.
3. **Fix aplicado (neste commit):** fallback na cápsula — sem candidatos, usa `find_references` dos tokens. Harness dev: recall **0.92 → 1.00 (100/100)**, query média 26ms. Teste cego dirigiu o fix; harness prova que não quebrou o resto.
4. **Velocidade:** pós-index, queries em ms (0.35s/8 no ATLAS). Custo é index (2–8s p/ 504–2328 arqs, uma vez). RAW vence no lote pequeno; índice vence na escala — F11 medirá por query em lote grande.
