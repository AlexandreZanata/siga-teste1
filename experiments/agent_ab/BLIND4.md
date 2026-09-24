# Cego 4 vias (E/G duras) + bake-off — F13 (2026-09-24)

## Bake-off harness (100Qs, GT-conjunto)
| estratégia | recall | média/query |
|---|---|---|
| lexical-only (BM25) | 0.92 | 0.2ms |
| structural-only | 0.92 | 1.0ms |
| hybrid | 0.92 | 1.2ms |
| hybrid+refs | 1.00 | 14ms |
| **router (cascata)** | **1.00** | **10ms** |

Router = melhor recall com menor custo (sai cedo quando ≥3 arquivos). Artefato: `bakeoff_f13.json`.

## Cego 4 vias (6Qs E/G, sem gabarito; GT-sets limitados ao escopo-40)
Escopo-estrito (arquivo dentro do GT-set escopo-40) / substantivo (resposta real verificada por leitura, mesmo fora do escopo):

| agente | estrito | substantivo | tempo | zeros |
|---|---|---|---|---|
| RAW | 1/6 (E-003) | 6/6 | ~31s | 0 |
| LEXICAL-only | 0/6 | 0/6 (+2 candidatos honestos) | queries ~0.1ms | 4 |
| STRUCT-only | 0/6 | 6/6 | queries ~0.3s | 0 |
| ROUTER | 0/6 | 6/6 | queries 0.02–0.8s | 0 |

## Achados
1. **GT escopo-40 pune acertos fora do escopo:** 5/6 respostas RAW/STRUCT/ROUTER são callers reais verificados (ex. `CpBL.java:730`, `SigaAmazonS3.java:146`) fora das 40 arquivos-amostra. Métrica correta exige índice de escopo total → **F14** (siga-ex completo).
2. **LEXICAL-only sozinho falha em E/G** (nomes de métodos JDK/comuns não são símbolos; queries ~0.1ms mas vazias). BM25 puro não basta — confirma literatura (RepoCoder/CodeRAG precisam de geração; nós usamos travessia).
3. **Higiene achada pelo LEXICAL:** `.venv` poluía o índice (urllib3/pip). Fix neste commit: `discover()` exclui `.git/.venv/node_modules/target/build/__pycache__`.
4. **Keyword-falso-positivo:** `try (` (try-with-resources) virava callee `try` e gerou Qs E/G-005 lixo. Fix: SKIP += try/finally/throw/assert/synchronized; Qs regeneradas (callee `write`).
5. **Velocidade real:** pós-index, STRUCT ~0.3s, ROUTER 0.02–0.8s, LEXICAL ~0.1ms; RAW ~30s. Índice paga-se na escala.
