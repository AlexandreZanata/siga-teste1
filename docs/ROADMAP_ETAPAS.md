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
- [ ] **F14** performance em escala: índice `siga-ex` completo (504 arqs) + p50/p95 + index size + incremental 10/100 arqs vs rebuild
- [ ] **F13** bake-off de metodologias (lexical-only vs structural-only vs hybrid vs hybrid+refs, da literatura RepoCoder/CodeRAG/RepoGraph) + roteador adaptativo por categoria + teste cego 4 vias
- [ ] **F14** performance em escala: índice `siga-ex` completo (504 arqs) + p50/p95 + index size + incremental 10/100 arqs vs rebuild
- [ ] **F15** freeze `v1-siga` + tabelas de paper (accuracy/tokens/latência por método) + SBOM
- [ ] **F8** freeze SIGA + scoring dev completo + `v0.x-siga-frozen`
- [ ] **FUTURO (pós-SIGA)** Bitcoin transfer (sem redesign) + `LIMITATIONS_BITCOIN.md`; ablações (9) + paper + SBOM + `v1` (só via RFC) — Bitcoin removido das etapas executáveis por decisão 2026-09-24: foco 100% SIGA-Doc até fidelidade comprovada

Agente responsável por etapa: executa `docs/VERIFICATION_PROTOCOL.md` (4 portões) e anexa evidências no corpo do commit. Sem evidência, sem push.
