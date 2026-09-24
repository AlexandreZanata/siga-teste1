# 12 — Plano do Paper

**Status:** DRAFT 2026-09-24. Sem conclusões antecipadas; tabelas TBD vazias; venue sem decisão até resultados (candidatos: MSR/ICSE/FSE/ASE/EMSE/TOSEM).

## 1. Títulos provisórios (nenhum definitivo)
`ArchAtlas: Deterministic Structural Memory for Token-Efficient Repository-Scale LLM Agents` / `Beyond the Context Window: External Structural Memory for Repository-Scale Software Agents`.

## 2. Outline (17 seções, 3–5 bullets cada no draft completo)
1 Abstract (problema, H1, método, resultados TBD, artifacts). 2 Introduction (janela finita, RAG perde estrutura, H1 falsificável). 3 Motivation (SIGA-Doc legado + Bitcoin sistêmico como casos). 4 Related Work (tabela §02 TBD-1). 5 Design (pipeline, local-first, sem LLM no loop). 6 Repository Representation (schema v0 + provenance + determ./heurístico). 7 Retrieval & Capsule (BM25+travessia+packing, budgets). 8 Experimental Setup (SHAs, Muse Spark 1.3 model-agnostic, baselines A–E, controles). 9 SIGA-Doc Evaluation (R1+R2+curva). 10 Cross-Language Bitcoin (cobertura, ID-LIMs, sem redesign). 11 Ablations (matriz 9: sem call/Git/testes/docs/expansão; lexical-only; structural-only; struct+lexical; struct+embeddings). 12 Efficiency (tokens, tool calls, latência, custo, bytes externos, incremental). 13 Threats (vazamento, GT, configs, HW, overfit). 14 Limitations (JSP/DI/macros, skipTests, build). 15 Ethics & Licensing (AGPL vs MIT, snippets fair-use ≤10 linhas, termos modelo, sem distillation proibida). 16 Reproducibility (envelope, JSONL/Parquet, 1 comando). 17 Conclusion (só após P19; reportar negativos).

## 3. Figuras/tabelas planejadas
Fig.1 pipeline; Fig.2 **accuracy-vs-tokens** (central, 7 budgets × métodos, IC95%); Fig.3 path-recall multi-hop; Tab. TBD-1 related; TBD-2 `| grep | BM25 | Vector | Atlas |` × Accuracy/Tokens/ToolCalls/Latency (vazia); TBD-3 ablações; TBD-4 incremental. Snippets ≤10 linhas c/ SHA+licença.

## 4. Cronograma gated (sem datas fictícias)
A fundação P0–P3 (regen. mínima, testes verdes) → B índice+retrieval P4–P9 (cápsula dev sob budget) → C benchmark congelado P10–P13 (test selado) → D transferência P14–P17 (LIMITATIONS) → E ablações+test P18–P19 (preencher TBDs 1×) → F escrita+venue P21–P22 (só após E). Nenhum claim antes de E.
