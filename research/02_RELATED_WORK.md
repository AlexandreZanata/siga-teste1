# 02 — Trabalho Relacionado (ArchAtlas)

> Ressalva de auditoria — 2026-09-24: o conteúdo abaixo é um catálogo histórico de candidatos, não uma revisão integral validada. Custos, capacidades ausentes, afirmações de novidade e referências ainda sem comprovação não devem fundamentar conclusões. O [plano vigente, seção 4](../plans/PESQUISA_CONTEXTO_MODULAR.md#4-literatura-inicial-e-como-combiná-la) reúne os fundamentos e aponta para as fichas de 2026. O antigo rótulo “verificado” foi substituído por um status de auditoria; cada afirmação exige sua própria evidência.

**Status:** catálogo histórico em auditoria, 2026-09-24. Para decisões atuais, usar a [base experimental de 2026](16_BASE_EXPERIMENTAL_2026.md), com versões, fontes e limites, e os [experimentos derivados](../plans/EXPERIMENTOS_2026.md). FeatLens e SWE-Pruner agora têm fichas específicas; isso não valida automaticamente as comparações e alegações de novidade da tabela histórica abaixo.

## 1. Tabela comparativa

| Trabalho | Ano | Representação | Retrieval | LLM no retrieval? | Grafo persistente? | Incremental? | Token overhead | Benchmarks | Open source? | Limitações | Diferença p/ ArchAtlas |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CodexGraph | 2024–25 (arxiv 2408.03910; NAACL'25) | Schema unificado + graph DB (Neo4j) | LLM escreve queries de grafo | Sim | Sim (DB externo) | Não reportado | Alto (~22k/102k rep.) | CrossCodeEval, SWE-bench, EvoCodeBench | Parcial/confirmar | Infra externa; custo alto; query-LLM frágil | Atlas: SQLite local, sem LLM no retrieval, sem servidor |
| CodeRAG | 2025 (EMNLP) | Multi-path + logprob query + BestFit rerank | Query LLM + rerank | Sim | Não (índice, não memória) | Não | Médio-Alto | ReccEval, CCEval | Sim (MIT) | Depende de LLM p/ query/rerank | Atlas: retrieval determinístico BM25+travessia |
| RepoCoder | 2023 (EMNLP) | Janelas + similaridade iterativa | Iterativo retrieval-generation | Sim | Não | Não | Médio-Alto | RepoEval | Confirmar | Propaga erro; sem grafo | Atlas: travessia determinística, sem iteração prob. |
| RepoGraph | 2024–25 (arxiv 2410.14684; ICLR'25) | Grafo nível de linha def/ref + ego-graphs | Ego-graphs | Parcial | Sim (por tarefa) | Não versionado | Médio | SWE-bench, CrossCodeEval (+32.8% rel. rep.) | Confirmar | Linha granular infla; sem persistência versionada | Atlas: símbolo/arquivo/módulo + incremental + provenance |
| CGM | 2025 (arxiv 2505.16901; NeurIPS'25) | Grafo na atenção via adapter+LoRA | Atenção estruturada | Sim (treino) | Nos pesos | Não (re-treino) | Baixo infer / altíssimo treino | SWE-bench Lite 43% (Qwen2.5-72B rep.) | Confirmar | GPU grande, acoplado a modelo | Atlas: sem treino, agnóstico a modelo |
| FeatLens | 2026 (arxiv 2609.26480) | Índice feature→função + grafo dinâmico/tarefa | Dinâmica guiada por feature | Parcial | Dinâmico (não persistente) | Não (foco overhead) | Baixo-Médio (objetivo) | Confirmar paper | Confirmar | Sem reuso/auditoria entre tarefas | Atlas: converge na cápsula, diverge na persistência incremental auditável |
| GraphCoder | 2024 (ASE) | Code context graph coarse-to-fine | Coarse+refino | Não nec. | Por query | Não | Médio | Compleção (confirmar) | Confirmar | Foco compleção | Atlas: memória geral reutilizável |
| Repoformer | 2024 (ICML) | Selective RAG (gating) | Seletivo | Sim | Não | Não | Médio (economiza) | RepoEval etc. | Confirmar | Gating falha multi-hop | Atlas: ortogonal; seletividade futura sobre base determ. |
| LocAgent | 2025 (ACL) | Localização guiada por grafo | Travessia p/ localização | Parcial | Suporte | Não | Médio | Localização | Confirmar | Só bug-localization | Atlas: localização é 1 uso da memória geral |
| SWE-Pruner/CORVUS/CoACT | 2026 | Pruning/compressão | Pós-processamento | Variável | Não | Não | Baixo | SWE-bench fam. | Confirmar | Comprimem, não constroem verdade | Atlas: combinável (pruner sobre cápsulas) |
| Vector RAG genérico | — | Chunks+embeddings | Coseno | Não | Não | Possível, sem estrutura | Médio-Alto | — | Sim | Perde def/ref/call; opaco | Atlas: vetores no máx. baseline local |
| BM25/grep | — | Índice invertido/texto | Lexical | Não | Não | Sim (trivial) | Baixo | — | Sim | Sem multi-hop; ruído | Atlas: BM25 (FTS5) como base + grafo + provenance |

Detalhes verificados: RepoCoder = Zhang et al. EMNLP'23 + RepoEval; CodeRAG = Zhang et al. EMNLP'25 + ReccEval/CCEval, MIT; RepoGraph = Ouyang et al., linha-level, ego-graphs; CodexGraph = Liu et al., custo dezenas de k tokens; CGM = Tao et al., 43% SWE-bench Lite; FeatLens = Li et al. set/2026, feature-guided dynamic — o mais próximo da Context Capsule; GraphCoder ASE'24 coarse-to-fine; Repoformer ICML'24 selective; benchmarks: SWE-bench (2294 pares, 12 repos Python), CrossCodeEval multilíngue, EvoCodeBench-2403 (275/25 repos), RepoExec/RepoEval.

## 2. O que já existe (não reinventar)
Estrutura def/ref/call ajuda factualidade; queries sofisticadas (logprob, multi-path, rerank, coarse-to-fine, gating); contexto menor bem selecionado preserva performance; benchmarks Python-centrados existem.

## 3. Lacunas abertas (posicionamento Atlas)
1. **Persistência incremental versionada** (SQLite local, `schema_version+commit_sha`, hash estável) — nenhum relacionado tem como objeto central.
2. **Determinismo sem LLM no loop** — medir quanto se preserva removendo LLM do retrieval.
3. **Local-first sem infra** (SQLite+FTS5 suficiente como memória, não só índice textual) — subexplorado.
4. **Legado Java 8/Maven/JSP + C++/CMake com build exigente** — fora de benchmarks Python-centrados; exige schema unificado real.
5. **Provenance + degradação honesta** (determ. vs heurístico vs cache IA) — não é prática padrão.
6. **Compacidade como métrica primária** (RCCR/UCD/Tokens-to-Correct) — overhead é custo colateral nos outros (exceção parcial FeatLens/pruners).

Posição em 1 frase/eixo: mesmo poder de schema que CodexGraph sem servidor/LLM-query; mesma ambição que CodeRAG/RepoCoder sem iteração prob.; mesmo uso de grafo que RepoGraph/LocAgent/GraphCoder mas persistente+incremental+auditável; mesmo respeito por estrutura que CGM sem treino; convergência com FeatLens/pruners em compacidade + persistência/determinismo; mesma base lexical que BM25/vetores quando útil, sempre com estrutura+provenance.
