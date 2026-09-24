# Estado da trilha Bitcoin

Dono durante execução: agente B. Track: `bitcoin`. Branch de escrita: `codex/bitcoin-context`.
`BASE_SHA`: `e6fde134f7da0d3616d90c40232d9ebe2ed9f033`. Método: mesmo P0–P7/E26-00–06 da trilha SIGA,
com dataset, tarefas, pré-registro e resultados próprios. Nenhum aceite copiado do SIGA.

## Checkpoint

- Etapa atual: **BTC-P6 concluída (desenho + drill)** — portabilidade temporal/ambiente
  especificada, maquinaria `temporal.py` exercitada, limitações consolidadas; sem corpus.
- Último aceite e evidências: `research/bitcoin/PORTABILITY.md` (eixos, pré-seleção, matriz nula,
  não-transferência); `archatlas/bitcoin/temporal.py` + `tests/bitcoin/test_btc_portability.py` (2/2);
  `experiments/bitcoin/p6_temporal/btc-p6-drill-001/` (manifesto + REPORT: 5/13 invalidados);
  `research/bitcoin/LIMITATIONS.md` (teto honesto BTC-P0–P6); BTC-P0–P5 inalterados.
- SHA publicado: `85af030` (BTC-P5) em `origin/codex/bitcoin-context`; este commit BTC-P6 a registrar após push.
- `run_id`: `btc-p6-drill-001` (sintético, determinístico). Reserva de recursos: nenhuma.
- Pedido ao core: nenhum.
- Bloqueio exato: execução temporal real exige `BTC_SHA(t0/t1)` + toolchain + teto + modelos
  (todos nulos); `main` em `7ba03cc` (P4-infra SIGA) observado, NÃO incorporado.
- Alternativa independente: BTC-P7 (guia dev + handoff) pode avançar sem dataset.
- Próximo comando/ação: resolver `BTC_SHA`; revalidar `C_btc` no corpus; depois BTC-P7.

## Etapas

- [x] BTC-P0 — auditoria, PIN e censo (auditoria concluída; PIN/CENSO como pendências explícitas bloqueando P2+).
- [x] BTC-P1 — aplicação da literatura e pré-registro próprio (preliminar, não selado; sem rodada autorizada).
- [x] BTC-P2 — adaptador, ambiente e medição (contratos + adaptador lexical + E26-00 sintético concluídos; build/índice do corpus pendentes de PIN).
- [x] BTC-P3 — piloto de edição (especificação + dryrun offline 72 rodadas concluídos; piloto real com modelo bloqueado por PIN/ambiente/teto).
- [x] BTC-P4 — protótipo e ablações (btc-pack/1 + E26-02 sintético + decisões; E26-03/04/05 com estado honesto; decisão final pendente de piloto).
- [x] BTC-P5 — confirmatório cego (pré-registro final selável + maquinaria ensaiada; selo real e rodada bloqueados por piloto/custodiante).
- [x] BTC-P6 — portabilidade temporal e de ambiente Bitcoin (desenho + drill sintético + LIMITATIONS; execução real pendente de snapshots).
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
selo real e rodada bloqueados por piloto/custodiante);
2026-09-24 BTC-P6 concluída em desenho + drill (temporal.py 2/2, 5/13 invalidados, fração 0.385;
LIMITATIONS consolidado; execução real pendente de snapshots).
Nenhuma fase posterior marcada além de BTC-P7. Experimentos BTC-E26-00–06 e E26-06 espelho:
E26-00/E26-02/drills validados em fixtures sintéticas; nenhum executado em dataset.
