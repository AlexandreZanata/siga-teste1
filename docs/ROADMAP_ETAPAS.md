# Roadmap por etapas (cada etapa = commit local + push; metodologia de ponta)

> Próxima sequência — 2026-09-29: [CLI Rust R0–R6, piloto real e confirmação cega](../plans/RUST_CLI_PILOTO_REAL.md), com [métricas e protocolo](../research/rust/PROTOCOLO_VALIDACAO.md). **R0 executado:** [contrato congelado](../research/rust/CLI_CONTRACT.md), [baseline medido](../research/rust/BASELINE.md) e [pré-registro do piloto](../research/rust/PREREGISTRATION_R0.md). **R1 executado:** binário Rust em `rust/archatlas/`, 60 testes verdes, orçamento dentro do teto em 8/8 configurações — [relatório](../research/rust/R1_REPORT.md). **R2 executado parcialmente:** `expand`/`verify`/`--include` (80 testes verdes), corpus comum congelado e verificado (504 = 504, caminhos e bytes) e rodada medida com script único — 4 245 execuções com artefato bruto (1 800 de consulta, 1 400 de `expand`, 875 de `verify`, 94 de escala, 36 de atualização, 40 de índice/`doctor`) mais 1 400 preservadas como linha de base, orçamento declarado == entregue no Rust em 900/900, ciclo editar/testar equivalente a rebuild em 36/36 e `verify` com o código previsto em 875/875. Q7 fechada: `evidence_wanted=references` deixou de repetir a janela de `known_refs` — cada arquivo citado agora contribui com as ocorrências fora dela, e pares sem nenhuma unidade de busca caíram de 63/70 para 21/70. Escala medida em corpus sintético até 50 400 arquivos / 238,7 MiB: a meta de `context` (§5 do plano) sobrevive a 10x o teto de arquivos da coorte — [relatório](../research/rust/R2_REPORT.md) §9. A comparação de R2 é declaradamente entre **produtos**, não entre linguagens. O runner de tentativa do piloto está implementado e ensaiado com executor declarado como stub (13 testes, incluindo integração com o binário real): tetos do pré-registro aplicados primeiro, `opened` só de evento real de leitura, patch aplicado em base limpa e ouro inacessível por caminho — [contrato](../research/rust/RUNNER_PILOTO.md). A camada de avaliação que R3/R5 exigem também está implementada e ensaiada: rubrica congelada com itens mecânicos (escopo declarado, teste imutável, teto) antes dos semânticos, bundle cego com custódia da chave e recusa de vazamento `hard`, adjudicação fail-closed (juiz LLM não é gabarito; item duvidoso não conta como sucesso) e agregação por tarefa com custo bloqueado em vez de zero — [contrato](../research/rust/AVALIACAO_CEGA.md), 27 testes. Próxima etapa: **R3**, bloqueada por P1 (modelo efetivo) e P2 (teto financeiro), decisões do usuário. A e B retomam os respectivos estados reais; Bitcoin já avançou e não reinicia BTC-P0. Os marcos históricos abaixo não comprovam patches corretos ou economia faturada. Para o produto Rust, os testes e dependências seguem o novo plano; as regras Python abaixo descrevem a implementação histórica.

> Atualização de planejamento — 2026-09-24: [SIGA/core](../plans/SIGA_EXECUTION.md) e [Bitcoin](../plans/BITCOIN_PARALLEL_PLAN.md) seguem P0–P7 em paralelo, com [worktrees, donos e integração separados](../plans/PARALLEL_EXECUTION.md). F0–F20 abaixo preservam o histórico SIGA. A retoma a primeira pendência comprovada nos artefatos existentes; B inicia BTC-P0. Esta revisão documental não executa etapas nem implica commit/push.

Metodologia fixa: trunk-based, fases ≤1 entrega, DCO (`-s`), `pytest -q` verde offline, stdlib-first, determinismo por hash, evidência `arquivo:linha@SHA`, dataset `/siga/` read-only em `e3be22828`.

Detalhamento atual: [papers de 2026](../research/16_BASE_EXPERIMENTAL_2026.md) → [E26-00–E26-06 SIGA/core](../plans/EXPERIMENTOS_2026.md) e [BTC-E26-00–06](../plans/bitcoin/EXPERIMENTOS_2026.md). Avanço apurado por trilha, sem copiar aceites. Ordem local: E26-00/01 em P2–P3; E26-02 primeiro em P4; E26-03/04/05 conforme evidência do piloto; E26-06 em integração e portabilidade.

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
- [ ] **F21 / P3** (planejada; depende de P0–P2) tarefas de edição reais frontend/backend + avaliação cega de patches, com custo ponta a ponta, qualidade e protocolo pré-registrado; ver plano vigente.
- [ ] **TRILHA PARALELA BITCOIN** BTC-P0–P7 + BTC-E26-00–06, conforme plano próprio. A decisão anterior de adiar Bitcoin foi substituída pelo pedido de execução paralela em 2026-09-24. Sem dependência da conclusão SIGA; resultados independentes.
- [ ] **TRANSFERÊNCIA EXTERNA** após congelamento, avaliar projetos inéditos que não participaram do ajuste SIGA/Bitcoin; consolidar paper, limitações e critérios de release.

Agente responsável por etapa: executa `docs/VERIFICATION_PROTOCOL.md` (4 portões) e anexa evidências no corpo do commit. Sem evidência, sem push.
