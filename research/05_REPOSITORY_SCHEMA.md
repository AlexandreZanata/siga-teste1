# 05 — Schema Unificado de Repositório

**Status:** DRAFT 2026-09-24 (`schema_version=v0`; mudança exige migração versionada).

## 1. Entidades
Repository(id, remote_url, default_branch, license_note) · Commit(sha, parent, author, ts, msg)
· Module(name, path_prefix, build maven/cmake, version) · File(path, lang, content_hash, n_lines, commit)
· Symbol(kind: function/method/class/struct/enum/interface/field/variable/macro/namespace/package/annotation/template; name, qualified_name, file, line/col/end, signature_hash, extractor, confidence, heuristic_flag, note)
· Import(raw, resolved_file/module?) · TestRef(test_file, covers_symbol/file?, kind unit/functional, framework junit/ctest/python) · DocRef(doc_path, anchors?) · AiCache(source_hash, summary, model, ai_generated=1 — excluída de hash determ.).

## 2. Relações (dirigidas, todas com provenance)
CONTAINS (Module→File), DEFINES (File→Symbol), IMPORTS/INCLUDES, CALLS, REFERENCES (uso/leitura/escrita), INHERITS/IMPLEMENTS, OVERLOADS, COVERS (teste→símbolo), DESCRIBES (doc→símbolo/módulo), TOUCHES (commit→file). Cada aresta: src/dst/kind/file/line/commit/extractor+version/confidence/heuristic_flag/note.
Ex.: Java `class ExMovimentacao` + `tramitar()` em `siga-ex/...java`, `import siga-cp.*` → resolved quando possível; JSP→bean = REFERENCES heuristic; C++ `CheckInput()` + `#include <mempool.h>` → resolved só com compile_commands, senão heuristic; `test/functional/mempool_accept.py` → TestRef functional.

## 3. Provenance + determinismo
Toda linha de fato: `commit_sha, schema_version, extractor, extractor_version, content_hash, confidence (1.0 determ. / <1.0 heurístico), heuristic_flag`. Regras: ORDER BY total + tie-break fixo; sem RANDOM/wall-clock/paralelismo visível; `extracted_at` lógico; hash = sha256(concat ordenado de fatos) excluindo ai_cache; upsert idempotente por `(commit,path,content_hash)` e `(commit,qualified_name,signature_hash)`; FTS5 (tokenizer/colunas/pesos BM25) fixado por schema_version. Ausência > invenção.
DDL conceitual: tabelas repository/commit_tbl/module/file/symbol/relation/import_decl/test_ref/doc_ref/ai_cache/meta + `fts_symbols`/`fts_files` (FTS5/BM25) + índices (qualified_name,commit), (src,kind), (dst,kind), (path,commit).

## 4. Heurístico vs determinístico
| Caso | Classe | Ação |
|---|---|---|
| Parse exato + resolução exata | determ. 1.0 | aresta normal |
| Fallback Tree-sitter sem tipos; include não resolvido; JSP/EL; regex template | heurístico <1.0 | aresta com flag+note |
| DI/reflexão só em config | config/heuristic | provenance config, nunca ast-exact |
| Macro/template C++ sem build | ausente ou heuristic | declarar incerteza |
| Cache IA | não-fato | `ai_generated=1`, TTL+hash, fora do hash |
