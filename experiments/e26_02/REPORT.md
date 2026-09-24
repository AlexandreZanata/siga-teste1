# E26-02 — profundidade vs quantidade de arquivos (diagnóstico, sem modelo)

Data: 2026-09-24. ID: E26-02 (adaptação controlada de R26-05 Recall Trap).
Depende de: P3-dryrun (`benchmarks/siga/pilot_p3_dev.json`, 12 dev) + P2 telemetria.
Código: `archatlas/packing.py:1` + `archatlas/capsule.py:build_capsule(packing=)`.
Estado: `concluida` como caracterização de empacotamento; sem seleção de vencedor p/ patch.
Heads: repo `d153196`, dataset `e3be22828` (841 arqs Java, 1.64s em `/tmp/opencode-p3/e26.sqlite`).
Método: mesmos candidatos e ranking (`_rank_candidates` congelado); só packing varia —
(a) `one_per_file`, (b) `multi` (default F5–F19), (c) `expanded` (declaração englobante
como aproximação da unidade de código; sem parser novo). Deduplicação de spans idênticos
nas três. 12 tarefas × 3 políticas = 36 builds, budget 2000, 1 repetição, sem respostas
anteriores no contexto. Diagnóstico sem novas leituras = este relatório (comparação
principal com leitura disponível fica p/ P3 real). Saída bruta: `runs.jsonl` (36).

## Resultados (arquivo-nível idêntico; custo/profundidade diferem)

| política | hit | recall_set | payload p50 | profundidade/file | p50 (s) |
|---|---|---|---|---|---|
| one_per_file | 0.750 | 0.625 | 1248 | 1.00 | 0.0995 |
| multi | 0.750 | 0.625 | 6461 | 4.42 | 0.0979 |
| expanded | 0.750 | 0.625 | 6709 | 5.50 | 0.1096 |

Só backend/cross (frontend JSP fora do índice Java — P3-dryrun §diagnóstico):
todas hit 1.00, recall 0.833. `used<=2000` em 36/36; payload excede `used`
(overhead de serialização, cf. P2). Tempos equivalentes; `expanded` +12% p50.

## Leitura (sem vencedor por recall — cf. ficha)

1. Empacotamento não moveu hit/recall de arquivos neste dev set: cobertura de arquivos
   não distingue as políticas — exatamente a armadilha do R26-05 (maximizar arquivos ≠
   melhor patch). Escolher por recall aqui seria arbitrário.
2. O que varia é custo×profundidade: `one_per_file` entrega 5× menos payload com mesma
   cobertura de arquivos; `expanded` paga +4% payload vs `multi` por +1.1 trecho/arquivo
   de contexto declaratório. Se profundidade por arquivo importar ao patch, o candidato a
   testar no P3 real é `one_per_file` (barato) vs `expanded` (contexto) — mas patch
   aceito, dependências omitidas e releituras seguem **nulos** (36/36, sem modelo/agente).
3. Limites: efeito medido só no recuperador da cápsula; lexical/estrutural puros não
   repetidos (sem presunção de mesmo efeito); `expanded` é aproximação (declaração
   nearest-≤-linha), não unidade semântica completa; n=12 dev, 1 rep, sem IC.

## Decisão

Nenhuma política promovida a padrão. `multi` mantido como default (compat F5–F19).
Candidatas a confronto com patch no P3 real: `one_per_file` vs `expanded`, com
métricas de patch aceito/omissões/releituras/tokens/tempo do plano §6. Teste
confirmatório seguirá margem de qualidade e meta de custo do pré-registro.
