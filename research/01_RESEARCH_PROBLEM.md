# 01 — Problema de Pesquisa (ArchAtlas)

**Status:** DRAFT planejamento — 2026-09-24. Sem conclusões antecipadas. Sem código de produção.

## 1. Definições operacionais
- **Memória estrutural externa:** representação persistente, navegável, determinística de um repositório, derivada só de artefatos verificáveis (código, AST, símbolos, imports, call graph, testes, Git, docs, build). Nunca de inferência LLM.
- **Determinística:** mesmo `commit + extrator + schema` → mesmo banco (hash estável, excluído cache IA).
- **Compacta / incremental / navegável:** reduz tokens por questão factual; atualiza proporcional ao diff; suporta travessia multi-hop explícita.
- **Context Capsule:** unidade mínima de contexto (símbolos + localizações + vizinhança + provenance + scores) sob budget rígido.
- **Cache IA:** resumo LLM opcional, `ai_generated=1`, regenerável, descartável, nunca prova fato.

## 2. Problema central
LLMs têm janela finita, cara e com degradação de atenção. Repositórios reais excedem qualquer janela prática. Extremos atuais:
1. **Despejo bruto/janela longa:** caro, frágil, "lost in the middle", irreprodutível.
2. **RAG vetorial genérico:** perde estrutura (define/usa/chama/testa), alucina relações, não é incremental.

**Enunciado:** Como prover a um LLM contexto factual, compacto, determinístico e atualizado sobre repositório grande, multilinguagem e evolutivo, sem exigir janelas maiores e sem delegar fatos a inferência probabilística?

## 3. Hipótese falsificável
**H1:** Conhecimento repository-scale pode ser externalizado em memória estrutural determinística que permite a coding agents operar com contextos LLM substancialmente menores preservando ou melhorando acurácia factual.
**H0:** Não reduz contexto sem perda, ou não supera baselines nas mesmas tarefas/métricas.
- VI: mecanismo de contexto (ArchAtlas vs arquivo-bruto vs BM25/grep vs Vector RAG), mesmo LLM/commit/temperatura/seeds.
- VD: acurácia factual citável + tokens consumidos.
- Falsificação: se em protocolo pré-registrado ArchAtlas não reduzir tokens com acurácia ≥ baseline (com significância), H1 é rejeitada no escopo testado.

## 4. Escopo / não-escopo
Em escopo: ingestão batch+incremental de SIGA e Bitcoin em SHAs fixos; extração determinística; schema unificado + provenance; BM25 via SQLite FTS5; Query API + CLI; MCP como adapter fino; avaliação comparativa; 100% local.
Fora de escopo: geração/auto-fix; modelo próprio/fine-tuning/adapter (linha CGM); todas as linguagens; resolução semântica C++ perfeita sem build; Neo4j/Elasticsearch/cloud; resumos LLM como verdade; plugin IDE como validação primária.

## 5. Doze questões operacionais (mapeiam para RQs e Query Engine)
1. Onde um símbolo é definido? 2. Onde é usado? 3. Quem chama F? 4. O que F chama?
5. Quais módulos dependem de C? 6. Quem implementa/estende C/I? 7. Quais testes cobrem S?
8. Quais arquivos participam de funcionalidade F? 9. Qual caminho conecta A–B?
10. Impacto provável de mudar S? 11. Quais docs/commits/testes explicam C?
12. Menor conjunto de trechos para responder Q com budget B?

## 6. Por que não "contexto infinito"
Física/custo (MLOC não cabem de forma útil); atenção factual degrada com contexto longo; evolução exige incrementalidade, não snapshot; prompts gigantes são irreprodutíveis; janelas gigantes pressupõem infra remota cara — hipótese oposta: modelos e contextos menores + estrutura externa precisa, local-first (RTX 4060 8GB/32GB, GPU não-requisito). Fatos pertencem a compilador/AST, não a adivinhação.

## 7. Repositórios de validação (fixar SHA por experimento)
- **SIGA** `projeto-siga/siga`, `develop`, AGPL-3.0, ~15412 commits. Maven Java 8, `siga-doc 11.5-SNAPSHOT`. Núcleo SIGA-Doc = `siga-ex` (+`siga-cp` identidade, `siga-base`, `siga-wf/sigawf`, `siga-ws`, legado `sigaex`). Stack Hibernate/Spring/VRaptor/JBoss/JSP/Lucene; `skipTests=true`.
- **Bitcoin** `bitcoin/bitcoin`, MIT, CMake, `src/` (validation/mempool/chainstate/net/wallet/rpc/index), `test/` unit+funcional Python, C++ com macros/templates/headers.
Rastreabilidade: QO→RQ(03)→métricas(03)→arquitetura(04)→schema(05). Mudança em H1 exige revisão deste doc.
