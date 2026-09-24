# 04 — Arquitetura Proposta (e alternativas)

> Rascunho de alternativas, não inventário da implementação. O [plano vigente, seção 5](../plans/PESQUISA_CONTEXTO_MODULAR.md#5-arquitetura-a-investigar) define os contratos a investigar, reaproveitando o código atual. Parsers, transportes e mecanismos opcionais só serão introduzidos conforme a necessidade experimental; não presumir que as escolhas abaixo já existem ou foram validadas.

**Status:** DRAFT 2026-09-24. Princípios: correção > verificabilidade > reprodutibilidade > generalização > eficiência > velocidade > simplicidade > extensibilidade. 100% local.

## 1. Pipeline
```
Repo (SHA fixo) → Language detection → Parser específico/linguagem → Unified IR
→ Structural Store (SQLite+FTS5) → Full-text (BM25) → Graph Relations
→ Query Engine (determinística) → Context Capsule Builder (sob budget)
→ Query API → CLI (primária) ; Query API → MCP adapter (fino, separado) → agente
```
Incremental: `git diff → arquivos → partial parse → símbolos/edges afetados → upsert por content-hash → invalida FTS5 + cache IA`.

## 2. Decisões por camada
- **Parsing genérico:** Tree-sitter (rápido, incremental, multilinguagem; sem tipos — MVP + fallback C++).
- **Java/SIGA:** P0 Tree-sitter Java → P1 JavaParser (AST puro, sem classpath) → opcional Eclipse JDT com classpath p/ bindings; jdt.ls só refinamento pontual (stateful, pesado p/ batch). JSP/EL/Freemarker: Tree-sitter + regex auditada (heuristic). HQL/Criteria: extrator de strings como aresta `data_access`.
- **C++/Bitcoin:** clangd/clang tooling com `compile_commands.json` (preciso; exige build CMake configurado) senão Tree-sitter fallback marcado `heuristic`. Macros/templates sem build = ausência honesta, nunca invenção.
- **Storage:** SQLite + FTS5 (zero-dep, transacional, incremental, arquivo único, offline). Rejeitados: Neo4j/Elasticsearch (infra externa, RAM, viola local-first); DuckDB+FTS como núcleo (analítico, overkill, autoload fragiliza offline); Tantivy como núcleo (BM25 nativo bom, bindings Python imaturos p/ MVP). Vetores só baseline opcional (sqlite-vec/FAISS local), nunca núcleo.
- **Retrieval:** BM25 (FTS5) + filtros estruturais + travessia 1..3 hops com fan-out limitado; rerank determinístico (pesos congelados, tie-break total). LLM nunca no caminho.
- **Interfaces:** Core → Query API → CLI; MCP adapter separado e sem lógica estrutural (só traduz gramática fechada). Permite benchmarkar motor sem agente.

## 3. Hardware e operação
Referência RTX 4060 8GB / 32GB RAM; GPU não-requisito (núcleo é CPU+SQLite). Linux primeiro; Windows/macOS futuro. Banco por `commit_sha`, copiável, inspecionável via SQL. Modos: full ingest, incremental, query, verify (reingestão = mesmo hash), explain (trilha BM25+travessia+filtros).

## 4. Alternativas rejeitadas (resumo)
Graph DB servidor; search server; embedding-first; LLM escreve query de grafo (padrão CodexGraph, custo alto); treino/adapter de atenção (padrão CGM); LS como extrator batch primário; parser total de templates no MVP.
