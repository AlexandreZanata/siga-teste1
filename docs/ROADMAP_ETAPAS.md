# Roadmap por etapas (cada etapa = commit local + push; metodologia de ponta)

Metodologia fixa: trunk-based, fases ≤1 entrega, DCO (`-s`), `pytest -q` verde offline, stdlib-first, determinismo por hash, evidência `arquivo:linha@SHA`, dataset `/siga/` read-only em `e3be22828`.

- [x] **F0** bootstrap (LICENSE/README/CONTRIBUTING/CI/skeleton) — `fca3ccf`
- [x] **F1** PIN+CENSO verificados — `eb56e0a`
- [x] **F2 `v0.1`** extrator + verificação (tag `v0.1`)
- [x] **F3** índice SQLite + incremental (`store.py`, invalidação por hash, `verify` hash-estável) + teste 1/10 arquivos
- [x] **F4** Query API mínima (`find_symbol/definition/references`) + CLI `verify`
- [x] **F5** BM25 (FTS5) + Capsule sob budget (500–32k) + benchmark dev A–G (≥50 Qs) + curva
- [ ] **F6** baselines grep/BM25/vector + harness `benchmark run/report` (JSONL)
- [ ] **F7** freeze SIGA + scoring test + `v0.x-siga-frozen`
- [ ] **F8** Bitcoin transfer (sem redesign) + `LIMITATIONS_BITCOIN.md`
- [ ] **F9** ablações (9) + paper draft + SBOM + release `v1` (só via RFC)

Agente responsável por etapa: executa `docs/VERIFICATION_PROTOCOL.md` (4 portões) e anexa evidências no corpo do commit. Sem evidência, sem push.
