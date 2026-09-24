# Roadmap por etapas (cada etapa = commit local + push; metodologia de ponta)

Metodologia fixa: trunk-based, fases ≤1 entrega, DCO (`-s`), `pytest -q` verde offline, stdlib-first, determinismo por hash, evidência `arquivo:linha@SHA`, dataset `/siga/` read-only em `e3be22828`.

- [x] **F0** bootstrap (LICENSE/README/CONTRIBUTING/CI/skeleton) — `fca3ccf`
- [x] **F1** PIN+CENSO verificados — `eb56e0a`
- [x] **F2 `v0.1`** extrator + verificação (tag `v0.1`)
- [x] **F3** índice SQLite + incremental (`store.py`, invalidação por hash, `verify` hash-estável) + teste 1/10 arquivos
- [x] **F4** Query API mínima (`find_symbol/definition/references`) + CLI `verify`
- [x] **F5** BM25 (FTS5) + Capsule sob budget (500–32k) + benchmark dev A–G (≥50 Qs) + curva
- [x] **F6** experimento A/B em agente: baseline (exploração normal) vs ArchAtlas (índice+Capsule), mesmas perguntas, tempo+acerto — `experiments/agent_ab/`
- [x] **F7** fidelidade total SIGA-Doc: `siga-ex` 504 arqs taxa 0.002 (único zero = `package-info.java` legítimo), JSPs `sigaex` 597 fora de cobertura declarada, harness JSONL recall 0.95 (A20/20 B20/20 D17/20), query média ~2ms
- [x] **F8** freeze SIGA + cápsula com expansão de referências (D 17/20 → 20/20, recall 1.00) + scoring dev + `v0.x-siga-frozen`
- [x] **F9** JSP lexer (597 pages, 581 com diretivas, 14 includes exatos + 965 marcados unresolved) + call graph candidate 0.6 + test-links naming (2 em `siga-ex`)
- [x] **F10** benchmark 100Qs A–G + cegos 3 abordagens + fallback refs (recall 0.92 → 1.00, query ~26ms)
- [x] **F11** GT-conjunto (40 Qs com sets médios 5.3 arqs) + p50/p95 por query (16/38ms) + recall 1.00
- [x] **F12** rede generalizada: dataset paramétrico + extrator Python AST + dogfooding (Python+Java mesmo DB)
- [x] **F13** bake-off (lex 0.92/0.2ms, struct 0.92, hybrid 0.92, hybrid+refs 1.00, router 1.00/10ms) + roteador cascata + cego 4 vias + higiene `.venv` + fix keyword-`try`
- [x] **F14** escala: full 504 arqs 0.92s, DB 2.5MB, router p50 26ms/p95 332ms, incr-10 0.03s (30x), incr-100 0.23s (4x)
- [x] **F15** freeze `v1-siga` + tabelas accuracy/tokens/latência + SBOM
- [x] **F16** trace multi-hop (8Qs H, cego RAW 7/8 em 66s vs TRACE 7/8 em 2.7s) — empate técnico, 24x velocidade
- [x] **F17** GT-conjunto de caminhos + harness full-504: recall 1.00 (108/108, 8 cats), p50/p95 144/326ms
- [x] **F18** 3 módulos (153Qs A–H, recall 1.00, index 841 arqs 5s, p95 372ms) + ranking tierado + fallback restaurado
- [x] **F19** privacidade (config env, GT relativo, README sem paths) + latência (cache disco único + co-ocorrência: p95 372→119ms, recall 1.00)
- [x] **F20** sweep budgets (500:.915, 1k:.948, 2k+:1.00, satura em ~1934tk) + comparativo
- [ ] **F21** (aberta) tarefas de edição reais (frontend/backend) + cego de eficiência de edição
- [ ] **FUTURO (pós-SIGA)** Bitcoin transfer (sem redesign) + `LIMITATIONS_BITCOIN.md`; ablações (9) + paper + SBOM + `v1` (só via RFC) — Bitcoin removido das etapas executáveis por decisão 2026-09-24: foco 100% SIGA-Doc até fidelidade comprovada

Agente responsável por etapa: executa `docs/VERIFICATION_PROTOCOL.md` (4 portões) e anexa evidências no corpo do commit. Sem evidência, sem push.
