# Handoff de integração Bitcoin → agente A (checkpoint; sem merge por B)

Data: 2026-09-24. De: agente B. Branch: `codex/bitcoin-context` (este commit; SHA no STATUS
após push). **B não faz merge em `main`, release ou push upstream.** Integração é atividade
de A, em checkpoint sem rodada ativa, tocando somente namespaces Bitcoin.

## 1. Entregue (7 commits BTC-P0–P7 sobre `e6fde13`)

- `research/bitcoin/`: AUDIT_BASELINE, LITERATURE_APPLICATION, PREREGISTRATION(+FINAL),
  CONTRACTS_P2, PILOT_P3, ABLATIONS_P4, PORTABILITY, LIMITATIONS, DEV_GUIDE, WORKSPACE,
  este handoff.
- `archatlas/bitcoin/`: `cpp_lex` (btc-cpp-lex/1), `packing` (btc-pack/1), `dryrun`,
  `seal` (btc-seal/1), `temporal`, `devflow`.
- `tests/bitcoin/`: 24 testes (adapter 5, e26_00 5, dryrun 3, packing 4, seal 3, portability 2,
  devflow 2; suíte total verde, ver STATUS).
- `benchmarks/bitcoin/`: PIN (BTC_SHA pendente), CENSO, `pilot_p3_dev.json` (12 tarefas).
- `experiments/bitcoin/`: e26_00/e26_02/pilot_p3/p5_seal(rehearsal VOID)/p6_temporal/e26_06 + REPORTs.
- `plans/bitcoin/STATUS.md`: histórico completo de transições e bloqueios.

## 2. Versões e compatibilidade

`core_sha=e6fde13` (lido, nunca editado); `main` observado até `36e8605`, NÃO incorporado
(execução SIGA, sem entrega de contrato). Reuso publicado: telemetry, verify, dataset,
packing-canônica como referência. Pedidos `BTC-CORE-NNN`: **nenhum aberto**.

## 3. Pendências que bloqueiam execução real (todas nulas)

`BTC_SHA`, toolchain do snapshot, modelos, teto, custodiante, amostra dimensionada, dev humano.
Nada autoriza rodada paga. Ao integrar: rodar suíte comum + SIGA + Bitcoin; testes de build
ausentes ficam explicitamente pendentes; conflitos resolvidos pelo dono da área.
