# Estado da trilha Bitcoin

Dono durante execução: agente B. Track: `bitcoin`. Branch de escrita: `codex/bitcoin-context`.
`BASE_SHA`: `e6fde134f7da0d3616d90c40232d9ebe2ed9f033`. Método: mesmo P0–P7/E26-00–06 da trilha SIGA,
com dataset, tarefas, pré-registro e resultados próprios. Nenhum aceite copiado do SIGA.

## Checkpoint

- Etapa atual: **BTC-P5 concluída (preparação selável)** — pré-registro final pronto para selar,
  maquinaria `btc-seal/1` ensaiada; selo real e rodada bloqueados.
- Último aceite e evidências: `research/bitcoin/PREREGISTRATION_FINAL.md` (congelamento, amostra,
  cegamento, decisão; lacunas nulas); `archatlas/bitcoin/seal.py` + `tests/bitcoin/test_btc_seal.py` (3/3);
  `experiments/bitcoin/p5_seal/btc-p5-rehearsal-001/` (`sealed.json` VOID + REPORT); BTC-P0–P4 inalterados.
- SHA publicado: `2668387` (BTC-P4) em `origin/codex/bitcoin-context`; este commit BTC-P5 a registrar após push.
- `run_id`: `btc-p5-rehearsal-001` (ensaio, sem medição). Reserva de recursos: nenhuma.
- Pedido ao core: nenhum.
- Bloqueio exato: selo/rodada exigem piloto real, `BTC_SHA`, toolchain, modelo, teto e custodiante
  (todos nulos); `main` em `7ba03cc` (P4-infra SIGA) observado, NÃO incorporado.
- Alternativa independente: BTC-P6 pode preparar desenho temporal/ambiente sem dataset.
- Próximo comando/ação: resolver `BTC_SHA`; executar piloto; só então selo real único + rodada cega.

## Etapas

- [x] BTC-P0 — auditoria, PIN e censo (auditoria concluída; PIN/CENSO como pendências explícitas bloqueando P2+).
- [x] BTC-P1 — aplicação da literatura e pré-registro próprio (preliminar, não selado; sem rodada autorizada).
- [x] BTC-P2 — adaptador, ambiente e medição (contratos + adaptador lexical + E26-00 sintético concluídos; build/índice do corpus pendentes de PIN).
- [x] BTC-P3 — piloto de edição (especificação + dryrun offline 72 rodadas concluídos; piloto real com modelo bloqueado por PIN/ambiente/teto).
- [x] BTC-P4 — protótipo e ablações (btc-pack/1 + E26-02 sintético + decisões; E26-03/04/05 com estado honesto; decisão final pendente de piloto).
- [x] BTC-P5 — confirmatório cego (pré-registro final selável + maquinaria ensaiada; selo real e rodada bloqueados por piloto/custodiante).
- [ ] BTC-P6 — portabilidade temporal e de ambiente Bitcoin.
- [ ] BTC-P7 — uso por desenvolvedor e checkpoint de integração.

Histórico de transições preservado aqui: 2026-09-24 BTC-P0 concluída (auditoria) com PIN/CENSO
pendentes; 2026-09-24 BTC-P1 concluída (literatura + pré-registro preliminar, lacunas nulas em §7);
2026-09-24 BTC-P2 concluída em escopo sem dataset (contratos, adaptador lexical, E26-00 sintético 10/10;
build/índice do corpus e piloto seguem pendentes de PIN);
2026-09-24 BTC-P3 concluída em escopo offline (especificação + dryrun 72 rodadas, replay exato;
piloto real bloqueado por PIN/ambiente/modelos/teto/custodiante);
2026-09-24 BTC-P4 concluída em escopo sintético (btc-pack/1, E26-02 4/4, candidato congelado;
E26-03/04/05 não executados/indisponíveis com motivo; final pendente de piloto);
2026-09-24 BTC-P5 concluída em preparação (pré-registro final selável, btc-seal/1 ensaiada 3/3;
selo real e rodada bloqueados por piloto/custodiante).
Nenhuma fase posterior marcada. Experimentos BTC-E26-00–06: E26-00 validado em fixtures sintéticas, demais planejados, nenhum executado em dataset.
