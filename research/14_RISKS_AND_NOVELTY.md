# 14 — Riscos e Novidade

**Status:** DRAFT 2026-09-24. Novidade = hipótese a validar (cápsula sob budget + cross-language determ. local-first + RCCR/UCD). Sem % pré-fixados.

## 1. Riscos (P×I → mitigação)
- **T1 clangd/compile DB inviável (P:A I:A):** fallback Tree-sitter etiquetado + COVERAGE + ID-LIM.
- **T2 macros/templates degradam call C++ (A/A):** arestas exact vs candidate; sem heurística escondida; RFC só se generalizável.
- **T3 índice stale (M/A):** invalidação por content-hash + staleness test + `index.status`.
- **T4 budget estoura em cross-cutting (M/M):** corte auditável; reportar falha, não aumentar post-hoc.
- **T5 embeddings irreproduzíveis (M/M):** só ablação, nunca default; pin ou off.
- **C1 baselines fracos (M/A):** frozen + harness único + 9 ablações, por categoria.
- **C2 overfit SIGA; Bitcoin falha (M/A):** freeze + espelho sem redesign; falha = resultado válido.
- **C3 RCCR/UCD não capturam utilidade (M/A):** frozen em METRICS.md + refs verificáveis separadas + threats.
- **C4 tuning no test (M/A):** selo + CI anti-leitura + execução única + capsules imutáveis.
- **C5 colisão FeatLens/CodeGraph (M/A):** datas, citação, diferenciação por budget+proveniência+freeze (ver §3).
- **L1 redistribuir índice SIGA c/ snippets viola AGPL (M/A):** scripts+ponteiros+hashes, regeneração local, fair-use mínimo (ver 15).
- **L2 termos do modelo/distillation (B/A):** terms por capsule; model-agnostic; nunca destilar se proibido.
- **L3 EPL Tree-sitter vs Apache-2.0 (B/M):** pin externo, THIRD_PARTY.md, CI licenças, revisão legal.
- **O1 build Bitcoin pesado (M/M):** amostra estratificada documentada. **O2 capsules pesadas (M/M):** hashes + 1 comando. **O3 perda provenance (B/A):** template obrigatório em CI.

## 2. O que NÃO é novo (atribuir no paper §5)
grep/BM25/Lucene/ctags; call graph (Soot/WALA/Clang/LSP); includes; test-links (Surefire/JaCoCo); embeddings (CodeBERT et al.); RAG; MCP tool-use; MSR. Reuso como baseline/infra; diferença hipotética = budget explícito + refs verificáveis + freeze cross-language.

## 3. Novidade provável (protocolos falsificáveis até P19)
- **H1 cápsula sob budget avaliável:** fixar tokens/bytes/calls+SHAs+modelo/prompts permite comparar métodos localmente. Falsifica se variância dominar ranking ou regeneração divergir.
- **H2 cross-language determ. local-first:** mesmo pipeline Java (parser) e C++ (clangd/fallback) com provenance e refs. Falsifica se queda total inexplicada ou exigir fork.
- **H3 RCCR/UCD + refs verificáveis:** discriminam melhor que accuracy agregada. Falsifica se colapsarem c/ baseline trivial ou auditoria discordar.
- **H4 struct+lexical orçado > lexical/structural/embeddings-only por token:** matriz 9 ablações seladas. Derrota reportada igualmente.
Colisão: monitorar preprints; TBD-1 com FeatLens/CodeGraph por leitura; se concorrente antecipar, re-posicionar como replicação/extensão honesta.
