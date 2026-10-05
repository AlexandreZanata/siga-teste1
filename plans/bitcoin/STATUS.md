# Estado da trilha Bitcoin

Dono durante execução: agente B. Track: `bitcoin`. Branch de escrita: `codex/bitcoin-context`.
`BASE_SHA`: `e6fde134f7da0d3616d90c40232d9ebe2ed9f033`. Método: mesmo P0–P7/E26-00–06 da trilha SIGA,
com dataset, tarefas, pré-registro e resultados próprios. Nenhum aceite copiado do SIGA.

## TASK-B01 executada (2026-10-05) — smoke Bitcoin validado (coorte Python)

- **O que existe agora:** [`smoke.tasks.json`](../../benchmarks/bitcoin/rust/smoke.tasks.json) (`atlas-tasks/2`, 4 smoke, balanço 1/1/1/1, base `9be056a8…`, `eval.py validate` limpo via core principal somente-leitura) + [`acceptance/`](../../benchmarks/bitcoin/rust/acceptance/) (`run.sh` e 4 harnesses Python, exit ≠ 0 em falha, exit 3 em bloqueio de ambiente, sem bitcoind/build C++/rede de produção). Curadoria em [`CURADORIA_SMOKE.md`](../../research/bitcoin/rust/CURADORIA_SMOKE.md), ambiente em [`ACCEPTANCE_ENV.md`](../../research/bitcoin/rust/ACCEPTANCE_ENV.md), evidências em `experiments/bitcoin/rust/2026-10-05-b01-validation/preflight/`.
- **Hashes confirmados no SHA fixado** (clone isolado `--filter=blob:none` + `fetch <sha>`): 5/5 conferem com o catálogo dev (`descriptors.py 8c2a4490…`, `address.py 63e83cdd…`, `script.py 24bdbfc1…`, `authproxy.py 736246f2…`, `test_runner.py faee6591…`). Catálogo comum não alterado.
- **Vermelho→verde:** 01 → 6/9→9/9 (`IndexError`/`TypeError` em checksum malformado); 02 → 10/16→16/16 (`ValueError` em mainnet v0/v5); 03 → 4/10→10/10 (`-342` com charset); 04 → 2/5→5/5 (`FileNotFoundError` sem citar `--jobs`). Referências em custódia fora do git (diffs mínimos: guarda de tamanho + `None`; ramos v0/v5; media-type com parâmetros; validação de `--jobs` + `--help` antes de `config.ini`). Aceite medido 0,04–0,76 s por tarefa (`timeout_s: 300`).
- **Isolamento além de diretório:** custódia fora do repo; pacote sem ouro (harnesses comparam em execução, citam só `--jobs` genérico; sem campo de curadoria, só hashes); `test_command` relativo; `atlas-accept/**` em `immutable_paths`. Nota de família: `btc-authproxy` (03×05) e `btc-runner` (04×08) repetem famílias com requisitos disjuntos — se usadas para política, excluir do piloto de inferência.
- **Testes:** 5 novos em [`tests/bitcoin/test_btc_smoke_b01.py`](../../tests/bitcoin/test_btc_smoke_b01.py) (schema+balanço, sem campos de curadoria/ouro, aceite existente com dispatches, `allowed_paths` com shas, logs vermelho/verde). Nenhuma tentativa com modelo rodou; P1/P2 continuam pendentes e bloqueiam só a rodada paga.
- **O que continua aberto:** B02 abaixo (07 desbloqueada via TU — ver seção própria), EXP01 (bloqueada por P1/P2), holdout P4.

## TASK-B02 parcial executada (2026-10-05) — piloto 05/06/08 validado, 07 bloqueada

- **O que existe agora:** [`pilot.tasks.json`](../../benchmarks/bitcoin/rust/pilot.tasks.json) (`atlas-tasks/2`, 3 validadas 05/06/08; `validate` com `--allow-imbalance` limpo, razão do desbalanceamento em [`CURADORIA_PILOTO.md`](../../research/bitcoin/rust/CURADORIA_PILOTO.md)) + harnesses `accept_b05/b06/b08` e dispatches em [`acceptance/`](../../benchmarks/bitcoin/rust/acceptance/) + evidências em `experiments/bitcoin/rust/2026-10-05-b02-validation/preflight/`.
- **Vermelho→verde no SHA fixado:** 05 → 6/11→11/11 (filho perdia `ensure_ascii`/`reuse`); 06 → 4/6→6/6 (truncado aceito em silêncio, callback chamado); 08 → 4/7→7/7 (vazia sem erro específico, flag ausente em `--help`). Referências em custódia fora do git (diffs mínimos: propaga 2 opções; `EOFError` em leitura curta; flag + erro estrito). Aceite 0,04–0,33 s (`timeout_s: 300`). `smoke.tasks.json` da B01 intacto (verificado por teste).
- **07 bloqueada só ela** (lacuna localizada: `ParseByteUnits` sem `case 'B'`, `ByteUnit` sem bytes, teste `util_ParseByteUnits` em `util_tests.cpp:1623`; hashes 3/3 conferem): sem headers de dev (libevent/Boost/zmq), sem sudo, fetch completo do `src/` inviável no enlace; deps parciais extraídas sem root em `/tmp/btcdeps/root` (fora do git), insuficientes sem a árvore. Item NÃO admitido sem prova. Desbloqueio: depends + RAM reservada, configure/build isolado, `test_bitcoin` com caso novo.
- **Testes:** 5 novos em [`tests/bitcoin/test_btc_pilot_b02.py`](../../tests/bitcoin/test_btc_pilot_b02.py) (schema+parcial explícito, sem ouro, dispatches, logs, smoke intacto). Nenhuma tentativa com modelo; P1/P2/P4 seguem pendentes.
- **O que continua aberto:** 07 (desbloqueada via TU abaixo; build completo segue pendente), expansão para 16 (EXP02 completa), EXP01 (P1/P2), holdout P4.

## BTC-REAL-07 desbloqueada (2026-10-05) — build C++ por TU, 14/17→17/17

- **Como:** `src/util/strencodings.cpp` (+ `hex_base.cpp`, 4 headers do snapshot) compila com `g++ 13.3 -std=c++20 -O1`, sem Boost/libevent/ZMQ. `accept_b07.py` + `probe_b07.cpp` compilam as fontes do workspace, linkam e executam 17 casos (1,21 s; `timeout_s: 600`). Referência em custódia (`case 'B'` → `ByteUnit::NOOP`). Evidências em `experiments/bitcoin/rust/2026-10-05-b07-validation/preflight/`.
- **Piloto completo 05–08:** `pilot.tasks.json` agora com 4 tarefas, balanço 1/1/1/1, `validate` limpo sem flags.
- **Desvio explícito:** `test_bitcoin`/`util_tests` seguem sem executar (sem depends/sudo) — ressalva para EXP01/julgamento; build completo pendente de provisionamento.
- **O que continua aberto:** expansão para 16 (EXP02 completa exige +4 além das 12), EXP01 (P1/P2), holdout P4.

## EXP02 parcial, lote 2 (2026-10-05) — piloto 09–12 validado, trilha soma 11

- **O que existe agora:** [`pilot2.tasks.json`](../../benchmarks/bitcoin/rust/pilot2.tasks.json) (`atlas-tasks/2`, 4 piloto, balanço 1/1/1/1, `eval.py validate` limpo) + harnesses `accept_b09..b12` e dispatches em [`acceptance/`](../../benchmarks/bitcoin/rust/acceptance/) + evidências em `experiments/bitcoin/rust/2026-10-05-b02pilot2-validation/preflight/`. Curadoria (com descartes da prospecção) em [`CURADORIA_PILOTO2.md`](../../research/bitcoin/rust/CURADORIA_PILOTO2.md).
- **Vermelho→verde no SHA fixado:** 09 → 2/4→4/4 (`TypeError` em `descsum_create` Unicode); 10 → 4/9→9/9 (0 silencioso/`IndexError`/inv zerado); 11 → 3/7→7/7 (`TypeError` em JSON não-objeto, inclusive em `_get_response`); 12 → 3/5→5/5 (traceback `re.error`). Referências em custódia fora do git (diffs mínimos: `ValueError`; leitura exata; guarda dict/list+dict; valida regex). Aceite 0,01–0,26 s.
- **Somado aos lotes anteriores, a trilha tem 11 tarefas validadas** (smoke 01–04 + piloto 05/06/08 + lote2 09–12). Famílias repetidas com requisitos disjuntos (`btc-descriptors` 01×09, `btc-p2p-deserialization` 06×10, `btc-authproxy` 03×05×11, `btc-runner` 04×08×12) e regra de exclusão registrada.
- **Testes:** 5 novos em [`tests/bitcoin/test_btc_pilot2_b02.py`](../../tests/bitcoin/test_btc_pilot2_b02.py) (schema+balanço, sem ouro, dispatches, logs, conjuntos anteriores intactos). Nenhuma tentativa com modelo; P1/P2/P4 seguem pendentes.
- **O que continua aberto:** expansão para 16 (EXP02 completa exige +4 além das 12), EXP01 (P1/P2), holdout P4. Build C++ completo segue pendente.

## EXP02 completa, lote final (2026-10-05) — piloto 13–16 validado, trilha soma 16

- **O que existe agora:** [`pilot3.tasks.json`](../../benchmarks/bitcoin/rust/pilot3.tasks.json) (`atlas-tasks/2`, 4 piloto, balanço 1/1/1/1, `eval.py validate` limpo) + harnesses `accept_b13..b16` e dispatches em [`acceptance/`](../../benchmarks/bitcoin/rust/acceptance/) + evidências em `experiments/bitcoin/rust/2026-10-05-b02pilot3-validation/preflight/`. Curadoria (com descartes da prospecção) em [`CURADORIA_PILOTO3.md`](../../research/bitcoin/rust/CURADORIA_PILOTO3.md).
- **Vermelho→verde no SHA fixado:** 13 → 3/6→6/6 (k=0 monta degenerado, k>n `AssertionError`, `[]` monta `0000ae`); 14 → 3/4→4/4 (tipo 13B truncado silencioso); 15 → 4/7→7/7 (`None` silencioso, `BOGUS`/número `TypeError`); 16 → 2/4→4/4 (prefixo inexistente cria datadir com exit 1). Referências em custódia fora do git (diffs mínimos: `ValueError` 1<=k<=n; `ValueError` len>12; `ValueError` modo + import parentetizado; `parser.error` tmpdirprefix). Aceite 0,05–0,22 s. Workspace `/tmp/btcp3` com layout `base/test_framework` + `base/test_runner.py` irmãos (`sys.path[0]` resolve symlinks).
- **Somado aos lotes anteriores, a trilha tem 16 tarefas validadas** (smoke 01–04 + piloto 05–08 + lote2 09–12 + lote-final 13–16; EXP02 completa). Famílias repetidas com requisitos disjuntos (`btc-p2p-deserialization` 06×10×14, `btc-runner` 04×08×12×16) e novas (`btc-script-multisig` 13, `btc-amount-rounding` 15), com regra de exclusão registrada.
- **Testes:** 5 novos em [`tests/bitcoin/test_btc_pilot3_b02.py`](../../tests/bitcoin/test_btc_pilot3_b02.py) (schema+balanço, sem ouro, dispatches, logs, conjuntos anteriores intactos). Nenhuma tentativa com modelo; P1/P2/P4 seguem pendentes.
- **O que continua aberto:** EXP01 (P1/P2), holdout P4. Build C++ completo segue pendente.

## TASK-EXP02 selada (2026-10-05) — piloto Bitcoin de 16 congelado (4/4/4/4, sealed:true)

- **O que existe agora:** [`pilot16.tasks.json`](../../benchmarks/bitcoin/rust/pilot16.tasks.json) (união fiel smoke 01–04 + piloto 05–08 + piloto2 09–12 + piloto3 13–16, sem reescrita, `eval.py validate` limpo, balanço 4/4/4/4) + [`pilot16-checkpoint.json`](../../benchmarks/bitcoin/rust/pilot16-checkpoint.json) + selo travado por hashes em `experiments/bitcoin/rust/2026-10-05-btc-exp02-seal/seal.json` (lotes, `run.sh`, 16 harnesses). Revisão em [`REVISAO_SEAL16.md`](../../research/bitcoin/rust/REVISAO_SEAL16.md).
- **Composição travada:** 8 famílias distintas; repetições só em `btc-descriptors` 01×09, `btc-p2p-deserialization` 06×10×14, `btc-authproxy` 03×05×11, `btc-runner` 04×08×12×16 (requisitos disjuntos, regra de exclusão). 9 arquivos em `allowed_paths`, 4 compartilhados com trechos disjuntos. Base operacional: aceite 0,01–1,21 s por tarefa (`timeout_s` 300, 07: 600); custo financeiro não computável (P1/P2 pendentes, nenhum modelo rodou).
- **Testes:** 4 novos em [`tests/bitcoin/test_btc_pilot16_seal.py`](../../tests/bitcoin/test_btc_pilot16_seal.py) (selo fechado 16, união fiel, hashes dos lotes/runner, aceites no runner congelado). O selo não cria holdout (P4) nem autoriza rodada paga (EXP01/EXP03 seguem bloqueadas por modelo/teto).
- **O que continua aberto:** EXP01 (P1/P2), EXP03 (depende de EXP01), EXP04 (P2), holdout P4. Build C++ completo segue pendente.

## Checkpoint

- Etapa atual: **build verificado como BLOQUEADO (veredito registrado)** — libevent/Boost/ZMQ
  ausentes, sem sudo, RAM ~0 livre; compilar aqui arriscaria o host; requisitos documentados.
- Último aceite e evidências: `research/bitcoin/BUILD_ENV.md` (sondagem + veredito + requisitos
  de desbloqueio); resto inalterado.
- SHA publicado: `ba4d901` (lote final 13–16) em `origin/codex/bitcoin-context`; este commit
  (selo EXP02) a registrar após push.
- `run_id`: nenhum (sondagem). Reserva: nenhuma. Pedido ao core: nenhum.
- Bloqueio exato: build (veredito) + teto + modelos + custodiante + dev (todos nulos ou externos);
  `main` em `f4523d5` (P6 SIGA) observado, NÃO incorporado. Sem escritor concorrente neste turno.
- Alternativa independente: nenhuma unilateral restante — trilha aguarda provisionamento/autorização.
- Próximo comando/ação: máquina com depends + RAM reservada; então configure/build isolado,
  `compile_commands.json`, índice com símbolos e tarefas reais de edição.

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
teto global não adotado; alternativa além-das-seeds registrada);
2026-09-24 E26-02 no corpus (78 linhas: largura vence sob ordem alfabética, gt 0.340 vs 0.051;
ranking confunde — inconclusivo, próximo com scores);
2026-09-24 E26-02 ranqueado (top-200 BM25: 1/file 16/26, expanded 13/26 + 65 pares, multi 11/26;
confound resolvido; produto inconclusivo sem edição);
2026-09-24 coexistência cooperativa na branch (commit alheio cbdefc3 mantido: CAP=100 zero perda
na sonda; este commit: BM25 textual + E26-02 ranqueado; sem reescrita);
2026-09-24 E26-01 com braço D_bm25 (272 rodadas: D 0.654/0.481 a 10 arqs, C 0.731/0.673;
D precisão, C recall; A/B idênticos);
2026-09-24 E26-01 com split (272 rodadas: A 1.0, C 0.808/0.750, R17+R18 ganhos, zero perdas;
D inalterado; R12 pede alias verdadeiro);
2026-09-24 E26-01 com text-seed em C (272 rodadas: C 0.962/0.885, R04+R10+R12+R19 ganhos,
zero perdas; R20 único miss; A/B/D idênticos);
2026-09-24 sweep K do braço D (104 rodadas: K=10 mantido; K=50 iguala C com ~1/4 dos arqs);
2026-09-24 build verificado BLOQUEADO (libevent/Boost/ZMQ ausentes, sem sudo, RAM ~0;
requisitos de desbloqueio em BUILD_ENV; última pendência unilateral encerrada).
Nenhuma fase posterior marcada além de BTC-P7. Experimentos BTC-E26-00–06 e E26-06 espelho:
E26-00/E26-02/drills sintéticos + E26-01 em dataset (2 rodadas); edição segue sem modelo.
