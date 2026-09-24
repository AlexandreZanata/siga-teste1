# 13 — Plano de Implementação (microfases)

> Sequência histórica. Não reiniciar P0–P22 deste arquivo: o projeto já possui implementação e experimentos. Seguir exclusivamente a [sequência P0–P7 do plano vigente](../plans/PESQUISA_CONTEXTO_MODULAR.md#8-etapas-pequenas-para-os-agentes-de-execução), começando pela auditoria do que existe. Nenhum clone, refatoração, execução ou publicação é autorizado automaticamente pela revisão documental.

**Status:** DRAFT 2026-09-24. Cada fase: objetivo pequeno, artefato verificável, testes, done-criteria, sem irreversibilidade.

## 1. Estrutura de repo (revisada)
`archatlas/core|parsers|indexes|graph|retrieval|context|adapters|mcp|cli|schemas/` + `benchmarks/siga|bitcoin/(scripts,MANIFEST,PIN)` + `experiments/capsules/` + `research/` + `paper/` + `docs/` + `tests/`. Regras: `core` só tipos Span/Ref/Budget/Provenance/hashing (importar parsers = falha); `indexes` = store SQLite+invalidação; `graph` = arestas; `retrieval` = seleção sob budget; `context` = serialização+citações (dupla checagem); `mcp/cli` thin, sem lógica; `schemas/` JSON Schemas; só scripts+manifestos+hashes commitados (sem blobs, `compile_commands.json`, worktrees; outputs em gitignore).

## 2. Trilha P0–P22 (6 tracks, dependências P0→P1→{P2,P3}→P4→…→freeze SIGA→…→freeze v0.x→…→v1)
- **A fundação:** P0 pin read-only+censo+SHAs (ver §3); P1 skeleton+schemas+SPDX (`--help` verde); P2 parsers Java determ. (golden fixtures, defs 100%); P3 store SQLite+incremental (touch invalida só arquivo; idêntico a full).
- **B grafo:** P4 call/imports/test-links (1-hop, provenance obrigatória); P5 Git provenance (churn/owners; mesmo SHA = mesma saída); P6 docs/testes como nós citáveis (flag `code|test|doc`; ablação = flag).
- **C retrieval orçado:** P7 seed(rg/BM25)→expand→rank→cut (20 queries dev respeitam budget, refs `path:linha@sha`, pesos em config); P8 MCP+CLI thin (goldens; Muse Spark 1.3 chama local sem rede; MCP nunca chama LLM); P9 baselines frozen (mesmo harness).
- **D benchmarks:** P10 harness+splits (test selado + hash; CI falha se lido cedo); P11 RCCR/UCD frozen (`research/METRICS.md` + script determ.); P12 capsule/experimento (params, prompts, model.txt, terms.txt, env, budget, output.hash; re-exec reproduz); P13 FREEZE SIGA + scoring dev (sem preencher TBDs).
- **E transferência:** P14 freeze v0.x + TRANSFER_LOG; P15 C++ clangd vs fallback + COVERAGE; P16 espelho Bitcoin selado; P17 execução + LIMITATIONS (`ID-LIM`), sem mudar código.
- **F consolidação:** P18 9 ablações 1× dev+test; P19 scoring test final + Fig.2/3; P20 draft 17 seções (fair-use ≤10 linhas); P21 hardening (CONTRIBUTING/CoC/DCO, CI, SBOM CycloneDX, SPDX, legal); P22 release v0.x→v1 (só ID-LIM promovidos via RFC com generalidade; CHANGELOG; venue pendente).

## 3. Primeira microtarefa — P0.1 (1–2h, sem build, fora da tree)
1. `mkdir -p /tmp/opencode && ls /tmp/opencode`. 2. `git clone --bare <URL-SIGA> /tmp/opencode/siga.git` (+Bitcoin igual) e `rev-parse HEAD > PIN`. 3. Worktree detach read-only p/ censo (`chmod -R a-w`). 4. Censo script (extensões, LOC tokei/cloc ou `python3 -c pathlib`, top dirs, builds, testes) → `research/CENSO.md` (tabela+comando+SHA+data). 5. `benchmarks/{siga,bitcoin}/PIN.md` (URL+SHA+data). 6. `.gitignore` (capsules outputs, `*.sqlite`, compile_commands, worktrees). 7. `tests/test_pins.py` (SHA40 + sem blobs via `git status`). Done: PINs+CENSO commitados, reproduzível por terceiro, CI pins verde, zero código terceiro.
