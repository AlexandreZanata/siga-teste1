# Estado da trilha Bitcoin

Dono durante execução: agente B. Track: `bitcoin`. Branch de escrita: `codex/bitcoin-context`.
`BASE_SHA`: `e6fde134f7da0d3616d90c40232d9ebe2ed9f033`. Método: mesmo P0–P7/E26-00–06 da trilha SIGA,
com dataset, tarefas, pré-registro e resultados próprios. Nenhum aceite copiado do SIGA.

## Checkpoint

- Etapa atual: **E26-01 repetido com teto de fan-in (teto global NÃO adotado)** — 204 rodadas,
  C 0.731/0.673 (era 0.808/0.731), −21% arquivos, +63% precisão relativa, perdas R04/R10 (ouro-hub);
  alternativa (teto além-das-seeds/co-ocorrência) registrada; sem edição, sem modelo.
- Último aceite e evidências: `archatlas/bitcoin/realretrieval.py` (`build_fanin`, teto opcional
  compatível com chamada antiga); `tests/bitcoin/test_btc_e26_01.py` (7/7: fan-in sintético +
  campos/replay da repetição); `experiments/bitcoin/e26_01/btc-e2601-002/` (runs + REPORT
  comparativo); rodada 001 e sonda 12 preservadas.
- Resultados 34 tarefas @2000: A 0.962/0.942 (idêntico); B 0.385/0.231 (idêntico);
  C sem teto 0.808/0.731/0.0071 (238 arqs) vs CAP=25 0.731/0.673/0.0116 (189 arqs, 14373 hubs
  pulados); por tipo CAP: 1.0/1.0/0.6/0.188.
- SHA publicado: `4e5d366` (E26-01 34 tarefas) em `origin/codex/bitcoin-context`; este commit
  (teto + repetição) a registrar após push.
- `run_id`: `btc-e2601-002` (leitura, 106s). Reserva: nenhuma. Pedido ao core: nenhum.
- Bloqueio exato: edição/piloto exigem teto + modelos + custodiante + dev (nulos); `main`
  observado, NÃO incorporado. Sem escritor concorrente neste turno.
- Incidente anterior RESOLVIDO e arquivado (ver histórico): um escritor por worktree/branch.
- Alternativa independente: E26-02 com spans no corpus; vocabulário de domínio (`addrman`).
- Próximo comando/ação: teto além-das-seeds ou co-ocorrência; ou build isolado.

## Etapas

- [x] BTC-P0 — auditoria, PIN e censo (auditoria + `BTC_SHA` v31.1 + censo real 2923 paths; working tree/toolchain pendentes).
- [x] BTC-P1 — aplicação da literatura e pré-registro próprio (preliminar, não selado; sem rodada autorizada).
- [x] BTC-P2 — adaptador, ambiente e medição (contratos + adaptador lexical + E26-00 sintético + BUILD_ENV + COVERAGE + corpus medido; build/índice pendentes de toolchain).
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
em escopo sem dataset; execução real e uso humano pendentes de PIN e desbloqueios);
2026-09-24 PIN resolvido (`v31.1`, `9be056a8…`, MIT, 2923 paths: C++ 1498, Python 364;
working tree e toolchain seguem pendentes);
2026-09-24 corpus medido em leitura (checkout limpo, LOC/discover reais, adaptador 12.546 includes
e 368 pares em 1409 C++; `.cc` como pendência local; build segue pendente);
2026-09-24 triagem completa (10 skipped = `__has_include`, ignorados com teste; 0 restantes),
BUILD_ENV (CMake/deps/regtest, nada compilado) e COVERAGE (áreas, 371 arqs de teste) registrados;
2026-09-24 índice do corpus (1873 arqs, 3,6s, 4049 símbolos PY, C++/JS zero; incremental == rebuild;
toolchain disponível sem clang++; build não tentado);
2026-09-24 E26-01-real no corpus, rodada 1 (12 sondas × 3 braços × 2 reps = 72 rodadas;
C_adapter 0.917/0.833, A 1.0 inutilizável, B 0.5/0.292; R12 `addrman` sistemático);
2026-09-24 E26-01 no corpus, rodada 2 (34 tarefas 26+8 × 3 braços × 2k/8k = 204 rodadas;
C 0.808/0.731, trace2code 0.312, abstenção só N05);
2026-09-24 E26-01 repetido com teto (CAP=25: C 0.731/0.673, −21% arqs, perdas R04/R10;
teto global não adotado; alternativa além-das-seeds registrada).
Nenhuma fase posterior marcada além de BTC-P7. Experimentos BTC-E26-00–06 e E26-06 espelho:
E26-00/E26-02/drills sintéticos + E26-01 em dataset (2 rodadas); edição segue sem modelo.
