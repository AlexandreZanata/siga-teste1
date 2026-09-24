# Estado da trilha Bitcoin

Dono durante execução: agente B. Track: `bitcoin`. Branch de escrita: `codex/bitcoin-context`.
`BASE_SHA`: `e6fde134f7da0d3616d90c40232d9ebe2ed9f033`. Método: mesmo P0–P7/E26-00–06 da trilha SIGA,
com dataset, tarefas, pré-registro e resultados próprios. Nenhum aceite copiado do SIGA.

## Checkpoint

- Etapa atual: **BTC-E26-01-real (retrieval no corpus, sem modelo)** — 12 sondas dev
  (`benchmarks/bitcoin/e26_01_real.json`, ouro com bytes lidos, sem holdout) ×
  A_busca/B_freq/C_adapter × 2 reps = 72 rodadas em `/tmp/btc-readonly` (HEAD
  `9be056a8`, limpo); C_adapter hit 0.917/recall 0.833 (precision 0.006);
  A recall 1.0 inutilizável (1432 arqs); B_freq 0.5/0.292; miss sistemático
  BTC-R12 (`addrman` + explosão de `#include`); patch/custo nulos.
- Último aceite e evidências: `archatlas/bitcoin/realretrieval.py` (textos do corpus +
  3 braços) + `experiments/bitcoin/e26_01_real/btc-e26-01-real-001/` (manifest+runs+REPORT)
  + `tests/bitcoin/test_btc_e26_01_real.py` (3/3 herméticos + skip de corpus);
  BTC-P0–P7, índice e triagem inalterados.
- SHA publicado: nenhum novo (commit a registrar após push); base `8d1a58b`.
- `run_id`: `btc-e26-01-real-001`. Reserva de recursos: nenhuma. Pedido ao core: nenhum.
- Bloqueio exato: modelos/teto/custodiante/dev (nulos); rascunho paralelo não commitado
  (`benchmarks/bitcoin/e26_01_dev.json`, `pilot_p3_dev.json`, `tests/bitcoin/test_btc_e26_01.py`
  com 2 testes vermelhos por artefatos ausentes) observado e NÃO tocado/commitado.
- Alternativa independente: nenhuma nesta etapa (retrieval direto, sem build).
- Próximo comando/ação: teto de fan-in no salto por includes + repetir; depois tarefas
  de edição BTC-P3 (bloqueadas).

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
2026-09-24 E26-01-real no corpus (12 sondas × 3 braços × 2 reps = 72 rodadas, 0 erros;
C_adapter 0.917/0.833, A 1.0 inutilizável, B 0.5/0.292; R12 `addrman` sistemático;
patch/custo nulos; rascunho paralelo alheio com mesmos IDs observado, intocado).
Nenhuma fase posterior marcada além de BTC-P7. Experimentos BTC-E26-00–06 e E26-06 espelho:
E26-00/E26-02/drills validados em fixtures sintéticas; nenhum executado em dataset.
