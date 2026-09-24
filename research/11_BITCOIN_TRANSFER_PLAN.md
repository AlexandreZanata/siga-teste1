# 11 — Plano de Transferência Bitcoin (sem redesign antecipado)

**Status:** DRAFT 2026-09-24.

## 1. Regra de congelamento
Desenvolver no SIGA → taggear `v0.x-siga-frozen` (código `archatlas/` intocado; branch protegida) → indexar Bitcoin → rodar benchmark → registrar falhas em `research/LIMITATIONS_BITCOIN.md` (`ID-LIM-xxx`) → só então RFCs `v1-dev`. Exceção única: bug que impeça qualquer indexação, com prova de generalidade (não regredir SIGA) + RFC. Nenhum tuning de schema/query observando o test Bitcoin.

## 2. Checklist indexação C++
`BTC_SHA` pinado; tentar `compile_commands.json` (CMake presets documentados; `bear` parcial aceito com cobertura declarada) → clang tooling p/ includes/calls precisos; senão Tree-sitter fallback por arquivo marcado `heuristic`. Amostrar e testar: macros (`assert`, guards), templates, headers↔TU, forward decls, `depends/` excluído, `src/test` unit vs `test/functional` Python. Artefatos: `INDEX_CONFIG.md` (build exato ou fallback), `COVERAGE.md` (por área: % arquivos precisos vs fallback).

## 3. Benchmark espelho (categorias A–G, áreas mempool/validation/chainstate/p2p/wallet/RPC/indexes)
Ex.: A "onde `CheckTx`/`AcceptToMemoryPool` definidos?"; C "caminho RPC→validação→mempool→chainstate"; D "qual `test/functional/*.py` cobre `[mempool accept]`"; E "impacto de mudar `[fee check]` em callers+testes"; F "papel de `validation` vs `chainstate` vs `mempool`"; G "cápsula 2k p/ `[nova regra de relay]`". GT do código/testes/diffs; queries seladas antes do scoring.

## 4. Falhas documentadas e promoção a v1
Cada falha: `ID-LIM, sintoma, causa (macro/template/build/fallback), frequência, severidade, workaround, RFC candidata?`. Só limitações de generalidade (ocorrem em Java e C++) viram RFC; especificidades C++ viram backend plugável, não fork de schema. Sucesso = cobertura tabelada + curva accuracy-vs-tokens Bitcoin + lista RFC — mesmo que H1 falhe em C++ (resultado válido).
