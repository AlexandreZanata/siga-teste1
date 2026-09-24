# Estado da trilha Bitcoin

Dono durante execução: agente B. Track: `bitcoin`. Branch de escrita: `codex/bitcoin-context`.
`BASE_SHA`: `e6fde134f7da0d3616d90c40232d9ebe2ed9f033`. Método: mesmo P0–P7/E26-00–06 da trilha SIGA,
com dataset, tarefas, pré-registro e resultados próprios. Nenhum aceite copiado do SIGA.

## Checkpoint

- Etapa atual: **BTC-P7 concluída (guia + jornada ensaiada + handoff)** — trilha BTC-P0–P7
  completa em escopo executável sem dataset; execução real segue bloqueada (PIN e pendências).
- Último aceite e evidências: `research/bitcoin/DEV_GUIDE.md` (instalação, jornadas, capacidades);
  `archatlas/bitcoin/devflow.py` + `tests/bitcoin/test_btc_devflow.py` (2/2);
  `experiments/bitcoin/e26_06/btc-e2606-drill-001/` (manifesto + REPORT: jornada ponta a ponta);
  `research/bitcoin/INTEGRATION_HANDOFF.md` (checkpoint para A; sem merge por B); BTC-P0–P6 inalterados.
- SHA publicado: `06db15f` (BTC-P6) em `origin/codex/bitcoin-context`; este commit BTC-P7 (fim da
  trilha executável) a registrar após push.
- `run_id`: `btc-e2606-drill-001` (ensaio). Reserva de recursos: nenhuma. Pedido ao core: nenhum.
- Bloqueio exato: uso humano e execução em corpus exigem `BTC_SHA` + toolchain + teto + modelos +
  custodiante + dev (todos nulos); `main` em `36e8605` (P4-infra SIGA) observado, NÃO incorporado.
- Alternativa independente: nenhuma — trilha completa; próximos passos dependem de PIN/piloto.
- Próximo comando/ação: resolver `BTC_SHA`; revalidar `C_btc` no corpus; A integra em checkpoint.

## Etapas

- [x] BTC-P0 — auditoria, PIN e censo (auditoria concluída; PIN/CENSO como pendências explícitas bloqueando P2+).
- [x] BTC-P1 — aplicação da literatura e pré-registro próprio (preliminar, não selado; sem rodada autorizada).
- [x] BTC-P2 — adaptador, ambiente e medição (contratos + adaptador lexical + E26-00 sintético concluídos; build/índice do corpus pendentes de PIN).
- [x] BTC-P3 — piloto de edição (especificação + dryrun offline 72 rodadas concluídos; piloto real com modelo bloqueado por PIN/ambiente/teto).
- [x] BTC-P4 — protótipo e ablações (btc-pack/1 + E26-02 sintético + decisões; E26-03/04/05 com estado honesto; decisão final pendente de piloto).
- [x] BTC-P5 — confirmatório cego (pré-registro final selável + maquinaria ensaiada; selo real e rodada bloqueados por piloto/custodiante).
- [x] BTC-P6 — portabilidade temporal e de ambiente Bitcoin (desenho + drill sintético + LIMITATIONS; execução real pendente de snapshots).
- [x] BTC-P7 — uso por desenvolvedor e checkpoint de integração (guia + jornada ensaiada + handoff; sem merge por B; uso humano pendente).

Histórico de transições preservado aqui: 2026-09-24 BTC-P0 concluída (auditoria) com PIN/CENSO
pendentes; 2026-09-24 BTC-P1 concluída (literatura + pré-registro preliminar, lacunas nulas em §7);
2026-09-24 BTC-P2 concluída em escopo sem dataset (contratos, adaptador lexical, E26-00 sintético 10/10;
build/índice do corpus e piloto seguem pendentes de PIN);
2026-09-24 BTC-P3 concluída em escopo offline (especificação + dryrun 72 rodadas, replay exato;
piloto real bloqueado por PIN/ambiente/modelos/teto/custodiante);
2026-09-24 BTC-P4 concluída em escopo sintético (btc-pack/1, E26-02 4/4, candidato congelado;
E26-03/04/05 não executados/indisponíveis com motivo; final pendente de piloto);
2026-09-24 BTC-P5 concluída em preparação (pré-registro final selável, btc-seal/1 ensaiada 3/3;
selo real e rodada bloqueados por piloto/custodiante);
2026-09-24 BTC-P6 concluída em desenho + drill (temporal.py 2/2, 5/13 invalidados, fração 0.385;
LIMITATIONS consolidado; execução real pendente de snapshots);
2026-09-24 BTC-P7 concluída (guia dev, jornada 2/2, handoff sem merge; trilha BTC-P0–P7 completa
em escopo sem dataset; execução real e uso humano pendentes de PIN e desbloqueios).
Nenhuma fase posterior marcada além de BTC-P7. Experimentos BTC-E26-00–06 e E26-06 espelho:
E26-00/E26-02/drills validados em fixtures sintéticas; nenhum executado em dataset.
