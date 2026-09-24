# 07 — Design de Retrieval

**Status:** DRAFT 2026-09-24. LLM fora do caminho crítico. Budget como restrição dura.

## 1. Estratégias
- **Lexical** (`search_text`: ripgrep + BM25 sobre path/identificador/comentário/string): nomes exatos, erros, HQL/Lucene em strings, JSP/EL, siglas. Recall base de todo pipeline. Sozinho confunde legado `siga-ex↔sigaex`.
- **Estrutural** (AST + definition/references/callers/callees/implementations/dependencies/test-links): tudo que exige aresta. DI/reflexão/JSP/HQL viram `config|heuristic`; `unresolved_rate` é métrica de saúde.
- **Híbrida (default, baseline D):** união + fusão determinística (RRF/pesos congelados) + expansão limitada + rerank determinístico.
- **Vetorial (baseline C, nunca núcleo):** embeddings de função/método/JSP + ANN; aresta vetorial = `text-match` até confirmação; congelar modelo/dim/chunking; registrar `source bytes transmitted`.

## 2. Expansão em grafo (limites)
Seeds validadas → `max_depth` 3, `fan_out` 8/nó (defaults congelados), `allow_kinds` (calls, implements, data_access, config; text-match só explícito); ordenação `(kind_priority, score, path)`; `visited` global anti-ciclo; alias legado = aresta `alias(legacy)` explícita; parar se custo estimado > 0.7·budget com `truncated_by_budget`. Estimativa `≈4 chars/token`, contagem exata antes do packing.

## 3. Rerank determinístico
`score = w_exact·exact + w_struct·edge + w_bm25·norm + w_graph·(1/(1+depth))·kind − penalties(legacy/text-quando-aresta)`; desempate total `(score↓, path↑, linha↑, símbolo↑)`; BM25 normalizado por consulta; saída com `rank/score_breakdown/provenance` persistida.

## 4. Fronteira LLM
`query → retrieval → expansão → rerank → packing → Capsule(JSON) →→ LLM (só consome Capsule, sem ferramentas na resposta medida)`. Citação válida só dentro da Capsule; fora = `citation_incorrect`; afirmação sem âncora = hallucination (protocolo em 10).

## 5. Cobertura das 12 Qs
`repo_overview` (POMs→entidades→controllers→contagem testes); `find_symbol` (exato→BM25→desambig. legado); `definition/references/callers/callees/implementations/dependencies` (estrutural); `related_tests` (convenção→refs→histórico); `trace_path` (bidirecional + caminho mínimo verificado); `impact_analysis` (callers transitivos + data_access + testes); `search_text` (grep+BM25); `search_concept` (BM25 + 1-hop, nunca afirma aresta); `get_context_for_change` (composição sob budget). Toda resposta: `repo, commit, file, linha, símbolo, provenance` — falta = incompleta.
