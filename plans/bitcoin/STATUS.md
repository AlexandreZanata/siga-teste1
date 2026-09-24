# Estado da trilha Bitcoin

Dono durante execução: agente B. Track: `bitcoin`. Branch de escrita: `codex/bitcoin-context`.
`BASE_SHA`: `e6fde134f7da0d3616d90c40232d9ebe2ed9f033`. Método: mesmo P0–P7/E26-00–06 da trilha SIGA,
com dataset, tarefas, pré-registro e resultados próprios. Nenhum aceite copiado do SIGA.

## Checkpoint

- Etapa atual: **BTC-P3 concluída (especificação + dryrun offline)** — piloto real com modelo
  segue bloqueado (PIN, toolchain, modelos, teto, custodiante).
- Último aceite e evidências: `research/bitcoin/PILOT_P3.md` (lote, braços, pareamento, aceitação, custos);
  `benchmarks/bitcoin/pilot_p3_dev.json` (12 tarefas próprias, sem soluções);
  `archatlas/bitcoin/dryrun.py` + `tests/bitcoin/test_btc_pilot_dryrun.py` (3/3);
  `experiments/bitcoin/pilot_p3/btc-pilot-dryrun-001/` (72 rodadas, 1 erro injetado ruidoso,
  replay exato, qualidade de stubs NÃO interpretável); BTC-P0–P2 inalterados.
- SHA publicado: `eebe974` (BTC-P2) em `origin/codex/bitcoin-context`; este commit BTC-P3 a registrar após push.
- `run_id`: `btc-pilot-dryrun-001` (offline, determinístico seed 7, sem medição real). Reserva de recursos: nenhuma.
- Pedido ao core: nenhum.
- Bloqueio exato: piloto real exige `BTC_SHA` + toolchain do snapshot + IDs de modelo + teto próprio +
  custodiante (todos nulos); `main` em `5d72551` (E26-03 SIGA) observado, NÃO incorporado.
- Alternativa independente: BTC-P4 pode especificar ablações sobre o adaptador sem esperar o PIN;
  nenhuma execução em corpus sem `BTC_SHA`.
- Próximo comando/ação: resolver `BTC_SHA` (`benchmarks/bitcoin/PIN.md`); depois BTC-P4
  (E26-02 espelho primeiro) ou piloto real se desbloqueado.

## Etapas

- [x] BTC-P0 — auditoria, PIN e censo (auditoria concluída; PIN/CENSO como pendências explícitas bloqueando P2+).
- [x] BTC-P1 — aplicação da literatura e pré-registro próprio (preliminar, não selado; sem rodada autorizada).
- [x] BTC-P2 — adaptador, ambiente e medição (contratos + adaptador lexical + E26-00 sintético concluídos; build/índice do corpus pendentes de PIN).
- [x] BTC-P3 — piloto de edição (especificação + dryrun offline 72 rodadas concluídos; piloto real com modelo bloqueado por PIN/ambiente/teto).
- [ ] BTC-P4 — protótipo e ablações.
- [ ] BTC-P5 — confirmatório cego.
- [ ] BTC-P6 — portabilidade temporal e de ambiente Bitcoin.
- [ ] BTC-P7 — uso por desenvolvedor e checkpoint de integração.

Histórico de transições preservado aqui: 2026-09-24 BTC-P0 concluída (auditoria) com PIN/CENSO
pendentes; 2026-09-24 BTC-P1 concluída (literatura + pré-registro preliminar, lacunas nulas em §7);
2026-09-24 BTC-P2 concluída em escopo sem dataset (contratos, adaptador lexical, E26-00 sintético 10/10;
build/índice do corpus e piloto seguem pendentes de PIN);
2026-09-24 BTC-P3 concluída em escopo offline (especificação + dryrun 72 rodadas, replay exato;
piloto real bloqueado por PIN/ambiente/modelos/teto/custodiante).
Nenhuma fase posterior marcada. Experimentos BTC-E26-00–06: E26-00 validado em fixtures sintéticas, demais planejados, nenhum executado em dataset.
