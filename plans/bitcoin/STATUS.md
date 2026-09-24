# Estado da trilha Bitcoin

Dono durante execução: agente B. Track: `bitcoin`. Branch de escrita: `codex/bitcoin-context`.
`BASE_SHA`: `e6fde134f7da0d3616d90c40232d9ebe2ed9f033`. Método: mesmo P0–P7/E26-00–06 da trilha SIGA,
com dataset, tarefas, pré-registro e resultados próprios. Nenhum aceite copiado do SIGA.

## Checkpoint

- Etapa atual: **BTC-P2 concluída (escopo sem dataset)** — contratos `btc-contracts/1`,
  adaptador `btc-cpp-lex/1`, fixtures/testes próprios e E26-00 espelho sintético; sem rodada real.
- Último aceite e evidências: `research/bitcoin/CONTRACTS_P2.md` (aceite próprio, 4/4 + 1 pendente de PIN);
  `archatlas/bitcoin/cpp_lex.py` + `tests/bitcoin/test_btc_adapter.py` (5/5);
  `tests/bitcoin/test_btc_e26_00.py` + `experiments/bitcoin/e26_00/btc-e2600-synth-001/`
  (manifesto + REPORT, 5/5); BTC-P0/P1 inalterados.
- SHA publicado: `77bf3ee` (BTC-P1) em `origin/codex/bitcoin-context`; este commit BTC-P2 a registrar após push.
- `run_id`: `btc-e2600-synth-001` (sintético, determinístico, sem medição real). Reserva de recursos: nenhuma.
- Pedido ao core: nenhum (nada genérico exigido; parsing C++ segue local).
- Bloqueio exato: `BTC_SHA` indefinido → manifesto de build/índice do corpus, `compile_commands.json`
  e piloto de patches seguem pendentes; `main` em `2b8a04f` (E26-01 SIGA) observado, NÃO incorporado.
- Alternativa independente: BTC-P3 pode especificar tarefas/avaliação sem esperar o PIN;
  nenhuma execução real é autorizada sem `BTC_SHA` + toolchain registrados.
- Próximo comando/ação: resolver `BTC_SHA` (`benchmarks/bitcoin/PIN.md`); depois BTC-P3
  (piloto A/B/C) com teto próprio.

## Etapas

- [x] BTC-P0 — auditoria, PIN e censo (auditoria concluída; PIN/CENSO como pendências explícitas bloqueando P2+).
- [x] BTC-P1 — aplicação da literatura e pré-registro próprio (preliminar, não selado; sem rodada autorizada).
- [x] BTC-P2 — adaptador, ambiente e medição (contratos + adaptador lexical + E26-00 sintético concluídos; build/índice do corpus pendentes de PIN).
- [ ] BTC-P3 — piloto de edição.
- [ ] BTC-P4 — protótipo e ablações.
- [ ] BTC-P5 — confirmatório cego.
- [ ] BTC-P6 — portabilidade temporal e de ambiente Bitcoin.
- [ ] BTC-P7 — uso por desenvolvedor e checkpoint de integração.

Histórico de transições preservado aqui: 2026-09-24 BTC-P0 concluída (auditoria) com PIN/CENSO
pendentes; 2026-09-24 BTC-P1 concluída (literatura + pré-registro preliminar, lacunas nulas em §7);
2026-09-24 BTC-P2 concluída em escopo sem dataset (contratos, adaptador lexical, E26-00 sintético 10/10;
build/índice do corpus e piloto seguem pendentes de PIN).
Nenhuma fase posterior marcada. Experimentos BTC-E26-00–06: E26-00 validado em fixtures sintéticas, demais planejados, nenhum executado em dataset.
