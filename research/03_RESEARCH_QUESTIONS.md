# 03 — Questões de Pesquisa (RQ1–RQ10)

**Status:** DRAFT 2026-09-24. Todas falsificáveis. Controles: mesmo LLM/commit/temperatura/seeds/repetições; SHA obrigatório.

## Convenções
VI = manipulada; VD = medida. Baselines obrigatórios: (a) arquivo-bruto/ls+grep+read, (b) BM25, (c) Vector RAG local. Repos: SIGA `develop` Java 8; Bitcoin C++/Python.

- **RQ1 — Redução de tokens:** Atlas reduz tokens enviados ao LLM vs exploração convencional? VI mecanismo; VD acurácia factual + tokens. Primária: acurácia@orçamento, Tokens-to-Correct. Falsifica se acurácia < melhor baseline no mesmo orçamento ou exigir ≥ tokens p/ mesma acurácia.
- **RQ2 — Preservação de precisão:** redução preserva/melhora precisão? VD correctness, grounded accuracy, hallucination/citation. Falsifica se grounded < baseline com IC95% pareado.
- **RQ3 — Supera grep/BM25/vector/híbrido?** VD Recall@K/Precision@K/MRR/nDCG/Symbol/File Recall. Falsifica se não superar nenhum baseline em nenhuma categoria com correção múltipla.
- **RQ4 — Multi-hop estrutural:** relações melhoram Qs multi-hop? VD path recall, relation accuracy, correctness. Falsifica se travessia ≤ top-k passo único em RCCR.
- **RQ5 — Generalização cross-language:** mesmo schema em SIGA-Doc e Bitcoin? VD cobertura por relação + RQ1–4 por repo. Falsifica se exigir fork de schema ou cobertura colapsar sem degradação honesta.
- **RQ6 — Custo incremental:** manter índice após 1/10/100 arquivos? VD tempo incremental/full, disco, RAM. Falsifica se escalar com repo e não com diff, ou hash divergir.
- **RQ7 — Menor cápsula viável:** qual menor budget mantém taxa X? VD curva accuracy-vs-tokens (500–32k). Descritiva; falsifica alegação de "leve" se p95/MB exceder limiar pré-registrado.
- **RQ8 — Menos tool calls:** Atlas reduz tool calls? VD tool calls/files opened/lines transferred até acerto. Falsifica se ≥ baseline.
- **RQ9 — Impact/change planning:** melhora impact analysis? VD precisão de conjunto afetado + testes afetados. Falsifica se ≤ baseline lexical.
- **RQ10 — Limites:** que Qs ainda exigem código em massa? Taxonomia de falhas (semântica profunda, runtime, UI pixel, config externa). Resultado válido mesmo se H1 falhar.

## Métricas formais
- Retrieval: Recall@K, Precision@K, MRR, nDCG@K, Symbol/File Recall, Path accuracy (fração de arestas do caminho-ouro em ordem).
- LLM: correctness (vs GT cego), grounded accuracy (correta + toda afirmação citada na cápsula), hallucination rate, citation correctness.
- Eficiência: tokens in/out/reasoning, tool calls, files opened, lines transferred, latência p50/p95, custo unitário publicado.
- Índice: full/incremental time, disco, RAM pico, CPU.
- Agentic: success, tests passed, patch correctness, iterações.
- **Novas (com cautelas):** `RCCR = repo_tokens / capsule_tokens` (compressão; reportar tokenizer); `UCD = fatos-ouro presentes / ktokens` (densidade; sempre com acurácia, nunca sozinha); Tokens/Tool-calls/Time-to-Correct (mediana+IQR+IC; time normalizado por hardware). Citação válida = `arquivo:linha:símbolo:commit` verificável automaticamente; sem citação = erro.

Matriz: QO1→RQ1,RQ3; QO2–4→RQ4; QO5→RQ9; QO6→RQ4/RQ5; QO7→RQ3; QO8–9→RQ4/RQ9; QO10→RQ9; QO11→RQ2; QO12→RQ7.
