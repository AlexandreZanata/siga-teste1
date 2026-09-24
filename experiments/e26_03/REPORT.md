# E26-03 núcleo — entidades vs relações (sem LLM; PageRank diferido)

Data: 2026-09-24. ID: E26-03 partes 1–2 (adaptação R26-01/R26-04). Depende de E26-02.
Código novo: `archatlas/modules.py:1` (só adição; `STRATEGIES`/cápsula intactos).
Estado: `concluida` como diagnóstico; sem promoção a padrão.
Heads: repo `2b8a04f`, dataset `e3be22828` (841 arqs, 1.62s, DB 5212 KB).
Método: mesmas sementes (`seed_entities`) nos dois tratamentos; `expand` isola o fator.
Braços: FLAT (`s_lexical`, baseline), ENT (`select(expand=False)`, sem arestas),
ENT_RELS (`select(expand=True)`, +refs verificadas ≤5/semente). Casos: 12 piloto
(hit de arquivo) + 20 E26-01 positivos (adicionais) = 96 rodadas, 1 rep. Sem descrições
funcionais (sem LLM; nada manual nas sementes), sem PageRank, patch nulo.

## Resultados

| suite | FLAT hit/recall | ENT hit/recall | ENT_RELS hit/recall |
|---|---|---|---|
| piloto (12) | 0.667/0.417 | 0.750/0.653 | 0.750/0.653 |
| e26_01pos (20) | 0.10/0.05 | 0.05/0.025 | 0.05/0.025 |

Custo (spans médios; payload-proxy p50 piloto): FLAT 1.8–2.8/—; ENT 20.1–10.4/697;
ENT_RELS 27.2–11.9/832 (+35% spans vs ENT, zero ganho em hit).
Coortes (32 casos): com símbolo explícito (n=18) FLAT 0.444 → ENT/RELS 0.556;
sem símbolo (n=14) FLAT 0.143 → ENT/RELS 0.0 (vazio, sem incerteza explícita).

## Manutenção: incremental × rebuild (3 arquivos tmp; edit/delete/rename)

Inicial idêntico (`stable_hash` igual). Após mutações: incremental indexou 2,
rebuild 2, mas **equivalência lógica FALSA** — linhas de paths excluídos/renomeados
persistem (chave é path, sem GC); DB sem reindex: 272/272 símbolos obsoletos
(`verify_symbol` falha). Edição de conteúdo: equivalente (mesmo path, hash novo).
Relações: calculadas ao vivo sobre o disco (sem arestas persistidas a apodrecer);
descrições: inexistentes (0 obsoletas); PageRank: N/A sem descrições.

## Leitura (regra da ficha, sem prova de "grafo interno")

1. Ponto de entrada depende do pedido (H3): entidades ajudam com símbolo explícito
   (+11pp) e colapsam sem ele (0.0 vs 0.143 do flat). Mapa→local não substitui BM25;
   combiná-los (como o router já faz) continua necessário.
2. Relações não pagam neste dev set: +35% spans, +19% payload, zero hit/recall a mais
   em ambas as suítes. Controle sem arestas preserva o (baixo) nível com menor custo —
   candidato a padrão **para retrieval**, com ativação seletiva a testar no P3 real
   (só tarefas entre-arquivos com patch podem justificar).
3. H4 refutada em escopo: incremental ≢ rebuild para exclusão/renomeação. Correção P4
   antes de qualquer alegação de manutenção: invalidação por ausência (GC de paths
   sumidos) + tratamento de rename, com teste de equivalência lógica.
4. code2test segue 0 em todos (src/test fora do índice — E26-01 achado 1, confirmado
   aqui: entidades não criam cobertura).

## Decisão

Nada promovido a padrão; nada levado ao confirmatório. Próximo P4:
(a) GC de invalidação + repetir equivalência; (b) indexar `src/test`;
(c) abstenção explícita; (d) descrições funcionais só com LLM + cache versionado, aí
sim PageRank vs expansão simples. Limites: n=32 dev, 1 rep, sem modelo/patch/IC.
