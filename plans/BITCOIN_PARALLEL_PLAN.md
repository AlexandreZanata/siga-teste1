# BITCOIN — Plano de execução paralela (agente isolado, zero conflito)

> Instruções para o agente paralelo: execute do início ao fim NESTE documento. Não leia outros planos. Não toque em nada fora do escopo abaixo.

## 0. Isolamento (anti-conflito — ler 3x antes de começar)
1. `git checkout -b exp/bitcoin` (TODO o trabalho vive neste branch; `main` é do experimento SIGA).
2. Dataset: `export ARCHATLAS_DATASET_BTC=/caminho/para/bitcoin` (checkout read-only; pin SHA em `benchmarks/bitcoin/PIN.md`).
   O código ArchAtlas lê `$ARCHATLAS_DATASET`; neste experimento passe `--dataset` explícito ou exporte temporariamente — NUNCA mude o default de outro experimento.
3. Escrita permitida SOMENTE em: `benchmarks/bitcoin/**`, `experiments/bitcoin_ab/**`, `archatlas/cpp.py` (novo), `tests/test_btc_*.py` (novos), `plans/BITCOIN_LOG.md`.
   PROIBIDO: `benchmarks/siga/*`, `experiments/agent_ab/*`, qualquer edição em `archatlas/*.py` existente (só leitura; extensão via arquivo novo + RFC).
4. DBs/artefatos locais: `/tmp/opencode-btc/` (nunca `/tmp/opencode/`).
5. Commits: `git commit -s -m "BTC-n: ..."` + push SÓ `exp/bitcoin`. Merge em `main` só pelo orquestrador após green + review.

## 1. Fases (espelho da metodologia SIGA, mesma rigidez)
- **BTC-0** bootstrap: `benchmarks/bitcoin/PIN.md` (SHA fixo) + teste `test_btc_pins.py` (rev-parse == PIN). Commit+push.
- **BTC-1** censo: `archatlas/cpp.py` discovery (`.cpp/.h`: funções/classes via regex auditada + `#include`; macros = `heuristic`, nunca fato) + `CENSO.md` medido + `test_btc_census.py`. Commit+push.
- **BTC-2** extrator+verificação: `extract_cpp` + reuso de `verify.py` (nome-na-linha + hash); zero-falso-positivo; âncora ex. `src/validation.cpp`. Commit+push.
- **BTC-3** índice+incremental: reuso de `store.py`/`dataset.py` (adicionar ext `.cpp/.h` se ausente — additive) + `test_btc_store.py`. Commit+push.
- **BTC-4** benchmark dev (≥60Qs A–G: mempool/validation/chainstate/p2p/wallet/RPC): GT programático verificado, ids `BTC-A-000…`. Commit+push.
- **BTC-5** bake-off (lexical/structural/hybrid/router) + cego RAW vs ROUTER (6Qs, tempo+acerto) + `REPORT.md`. Commit+push.
- **BTC-6** transferência: rodar pipeline CONGELADO (sem adaptar `archatlas/`); documentar `LIMITATIONS_BITCOIN.md` (macros/templates não resolvidos). Commit+push + relatório final ao orquestrador.

## 2. Anti-vício (obrigatório)
Provenance `arquivo:linha@SHA` em todo fato; heurística marcada; GT gerado por script versionado; teste cego sem gabarito; splits por janela temporal de commits; nenhum tuning observando o test; resultado negativo = resultado válido.

## 3. Done
`exp/bitcoin` verde (`pytest tests/test_btc_*`), 60+Qs, 1+ cego documentado, limitações listadas. Avisar o orquestrador; NÃO fazer merge.
