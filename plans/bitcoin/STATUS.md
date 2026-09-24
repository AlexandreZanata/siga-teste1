# Estado da trilha Bitcoin

Dono durante execução: agente B. Track: `bitcoin`. Branch de escrita: `codex/bitcoin-context`.
`BASE_SHA`: `e6fde134f7da0d3616d90c40232d9ebe2ed9f033`. Método: mesmo P0–P7/E26-00–06 da trilha SIGA,
com dataset, tarefas, pré-registro e resultados próprios. Nenhum aceite copiado do SIGA.

## Checkpoint

- Etapa atual: **BTC-P4 concluída (escopo sintético)** — `btc-pack/1`, ablação E26-02,
  decisões por componente e candidato congelado para fixtures; sem piloto real.
- Último aceite e evidências: `archatlas/bitcoin/packing.py` + `tests/bitcoin/test_btc_packing.py` (4/4);
  `experiments/bitcoin/e26_02/btc-e2602-synth-001/` (manifesto + REPORT: expanded 2 pares/113 tok);
  `research/bitcoin/ABLATIONS_P4.md` (E26-02 executado; E26-03/04/05 com estado honesto; candidato);
  BTC-P0–P3 inalterados.
- SHA publicado: `66dfbbc` (BTC-P3) em `origin/codex/bitcoin-context`; este commit BTC-P4 (candidato
  `core + btc-cpp-lex/1 + btc-pack/1`) a registrar após push.
- `run_id`: `btc-e2602-synth-001` (offline, determinístico). Reserva de recursos: nenhuma.
- Pedido ao core: nenhum (sem política geral nova).
- Bloqueio exato: decisão final de produto exige piloto real (`BTC_SHA` + toolchain + modelos + teto +
  custodiante, todos nulos); `main` em `b28c443` (P4-infra SIGA) observado, NÃO incorporado.
- Alternativa independente: BTC-P5 só inicia especificação após piloto; BTC-P6 temporal pode preparar
  desenho sem dataset.
- Próximo comando/ação: resolver `BTC_SHA` (`benchmarks/bitcoin/PIN.md`); revalidar candidato no corpus.

## Etapas

- [x] BTC-P0 — auditoria, PIN e censo (auditoria concluída; PIN/CENSO como pendências explícitas bloqueando P2+).
- [x] BTC-P1 — aplicação da literatura e pré-registro próprio (preliminar, não selado; sem rodada autorizada).
- [x] BTC-P2 — adaptador, ambiente e medição (contratos + adaptador lexical + E26-00 sintético concluídos; build/índice do corpus pendentes de PIN).
- [x] BTC-P3 — piloto de edição (especificação + dryrun offline 72 rodadas concluídos; piloto real com modelo bloqueado por PIN/ambiente/teto).
- [x] BTC-P4 — protótipo e ablações (btc-pack/1 + E26-02 sintético + decisões; E26-03/04/05 com estado honesto; decisão final pendente de piloto).
- [ ] BTC-P5 — confirmatório cego.
- [ ] BTC-P6 — portabilidade temporal e de ambiente Bitcoin.
- [ ] BTC-P7 — uso por desenvolvedor e checkpoint de integração.

Histórico de transições preservado aqui: 2026-09-24 BTC-P0 concluída (auditoria) com PIN/CENSO
pendentes; 2026-09-24 BTC-P1 concluída (literatura + pré-registro preliminar, lacunas nulas em §7);
2026-09-24 BTC-P2 concluída em escopo sem dataset (contratos, adaptador lexical, E26-00 sintético 10/10;
build/índice do corpus e piloto seguem pendentes de PIN);
2026-09-24 BTC-P3 concluída em escopo offline (especificação + dryrun 72 rodadas, replay exato;
piloto real bloqueado por PIN/ambiente/modelos/teto/custodiante);
2026-09-24 BTC-P4 concluída em escopo sintético (btc-pack/1, E26-02 4/4, candidato congelado;
E26-03/04/05 não executados/indisponíveis com motivo; final pendente de piloto).
Nenhuma fase posterior marcada. Experimentos BTC-E26-00–06: E26-00 validado em fixtures sintéticas, demais planejados, nenhum executado em dataset.
