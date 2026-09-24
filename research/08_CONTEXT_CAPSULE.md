# 08 — Context Capsule (especificação formal)

**Status:** DRAFT 2026-09-24. `capsule(query, budget) → {módulos, arquivos, símbolos, relações, call paths, testes, docs, excertos}`. Budgets: 500/1k/2k/4k/8k/16k/32k. Curva accuracy-vs-tokens = figura central; mais contexto ≠ melhor.

## 1. Schema JSON (normativo)
`capsule_version, task{query, category A–G, question_id}, budget{requested, used, tokenizer congelado, hard_enforced}, repo{name, commit, scope}, retrieval_config{id, weights, k, max_depth, fan_out, seed}, modules[]/files[]/symbols[]{id file line kind reason score provenance}/relations[]{from to kind provenance score}/call_paths[]{path kind verified_edges}/tests[]{path covers mapping naming|reference|history confidence}/docs[]/excerpts[]{id file start/end tokens truncated text anchors}/citations[]{excerpt file line symbol}/truncation_log[]/stats{candidates kept unresolved_rate}`.
Validade: `used ≤ requested` (validador rejeita); todo item exige `reason + provenance + score`; citação resolve p/ excerto existente.

## 2. Construção sob budget
1. Candidatos: lexical_top-k ∪ estrutural 1-hop. 2. Expansão (se exigir) limitada, custo ≤ 0.7·B. 3. Seleção knapsack guloso por `densidade = score/tokens_est` até 0.85·B (15% reserva); recusas em log. 4. Packing em ordem fixa (symbols→paths→relations→excerpts≤60%→tests→docs, tetos congelados). 5. Excertos ±40 linhas default; estouro: encolher → cortar imports/comentários → elidir corpo com `[... N lines]` + `truncated:true`; nunca reescrever código. 6. Contagem exata; remover menor densidade (docs→tests→periferia) até caber. 7. Validar schema + `used≤B`.

## 3. Exemplo simbólico (forma, não afirmação — linhas `0`, prefixo `EXEMPLO:`)
Query C "onde tramitação valida lotação antes de assinar?" (2k): modules `[siga-ex]`; symbols `[TramitacaoService#tramitar, LotacaoValidator#validar]` ast-exact; relation `calls`; call_path verificado; test `TramitacaoServiceTest` mapping naming medium; excerpt e1 ±janela real na execução; `truncation_log` (dup_alias legado preterido); `used 1874 ≤ 2000`.

## 4. Garantias testáveis
Budget hard nos 7 níveis; provenance obrigatória (`ast-exact|config|heuristic|text-match`); sem LLM no núcleo (rede bloqueada + seed = bytes idênticos); citações fechadas; auditabilidade (`config.id + breakdown + truncation_log`); 7 cápsulas/questão p/ curva.
