# 09 — Benchmark SIGA-Doc

**Status:** DRAFT 2026-09-24. Alvo: ≥200 dev + ≥200 test (calibrar em P0). Splits train/dev/test com embargo do test (hash selado, acesso só via harness).

## 1. Taxonomia A–G (moldes; instanciar `[…]` em P0 com símbolos reais)
- **A localization:** A1 classe de `[entidade expediente/processo/dossiê]`; A2 método de `[tramitação]` desambiguando legado; A3 JSP/tag de `[assinatura]` + controller.
- **B dependency:** B1 POMs diretas p/ `[op X]`; B2 entidades/DAO/HQL de `[Y]`; B3 beans Spring de `[S]` (XML vs anotação).
- **C call-path:** C1 controller→serviço→DAO/entidade; C2 `[op WS]`→serviço interno; C3 `[validação siga-cp]`→`[assinatura siga-ex]`.
- **D test mapping:** D1 testes de `[tramitar]` (naming/reference/history); D2 símbolo coberto por `[*Test]`; D3 símbolos de `[assinatura]` sem teste (vazio + justificativa).
- **E impact:** E1 callers+testes se `[M]` mudar; E2 DAOs/HQL/JSPs se `[E]` ganhar campo; E3 injeções se bean `[B]` renomeado.
- **F architecture:** F1 `siga-ex` vs `siga-cp` vs `siga-base` em `[X]`; F2 fronteira `siga-ex`/`siga-wf`; F3 superfícies (`siga-ws`+controllers) de `[Y]`.
- **G change planning:** G1 cápsula 2k p/ `[validação antes de assinar]` (julgar por cobertura GT); G2 aliases/ordem p/ migrar `sigaex`→`siga-ex`; G3 impacto de trocar `[HQL→Criteria]`.

## 2. Ground truth
Programático (AST/refs/call/diffs: ex. `callers(M)` fechado no SHA) + issues só inspiram wording + sintético (G) só como proposta com validação independente (2º extrator ou juiz cego; taxa de rejeição publicada) + adjudicação amostral com acordo + dedup por resposta-canônica + exclusão por janela temporal/contaminação.

## 3. Baselines (configs congeladas, mesmo harness)
A `grep` (rg literal + truncamento); B `BM25` (tok/stop/k1/b/k fixos, chunk função/JSP); C `vector` (modelo/dim/chunk/ANN fixos + bytes transmitidos); D `híbrido` (RRF/pesos+k+depth+fanout + rerank); E `ArchAtlas` (= D + packing/citação fechada; única diferença E−D). Extras se viável: RepoGraph/CodexGraph/CodeRAG/FeatLens com versão+adaptador (ou declarados incomparáveis p/ citação). Controles: mesmo LLM (Muse Spark 1.3 no principal), commit, temp 0, seeds, repetições, budgets.

## 4. Métricas
Retrieval (Recall@K, Precision@K, MRR, nDCG, Symbol/File Recall, Path accuracy c/ crédito por aresta); LLM (correctness, grounded, hallucination, citation); eficiência (tokens in/out/reasoning, tool calls, files/lines, p50/p95, custo); índice (full/incremental, disco, RAM, CPU; incremental 1/10/100 vs rebuild); agentic (success, tests, patch, iterações); novas RCCR (cobertura GT na cápsula; c/ Precision), UCD (desperdício; c/ adjudicação+IC), Tokens/Tool-calls/Time-to-correct (mediana+IQR+IC; time normalizado).

## 5. Tabelas TBD (vazias até execução)
R1 retrieval por baseline×categoria (dev, 2k); R2 curva budget 500–32k (E); R3 eficiência/índice/agentic+privacidade. Nenhum número antecipado. Cada questão: `id, categoria, query, GT, provenance, gerador+seed, SHA, split`; cada rodada: envelope §10 em JSONL/Parquet via `archatlas benchmark run/report`.
