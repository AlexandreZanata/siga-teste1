# Curadoria piloto Bitcoin — TASK-B02 (parcial: 05/06/08; 07 bloqueada)

Data: 2026-10-05. Dono: B. Base: bitcoin/bitcoin `9be056a8a72b624dae9623b2f7bded92c2a21c91`
(v31.1). Catálogo dev: `benchmarks/rust/tasks/bitcoin.dev.json` (somente leitura,
no checkout principal — não alterado).

## Hashes confirmados no SHA fixado

| Fonte | sha256 | Confere |
|---|---|---|
| `test/functional/test_framework/authproxy.py` | `736246f2…70916d1a1a` | sim (B01) |
| `test/functional/test_framework/messages.py` | `c786651a…3403548b26` | sim |
| `test/functional/test_framework/p2p.py` | `7292865d…42b48aa9f3` | sim |
| `test/functional/test_runner.py` | `faee6591…18ca529c3` | sim (B01) |
| `src/util/strencodings.cpp` | `e7b53609…ea0be026804f` | sim (inspeção 07) |
| `src/util/strencodings.h` | `05a92016…702f698980a65` | sim (inspeção 07) |
| `src/test/util_tests.cpp` | `7dcc31af…405cfcd0ba01d` | sim (inspeção 07) |

## Vermelho → verde (05/06/08)

Referências em `/home/iiii/PESSOAL-PROJETOS-ALEXANDRE/siga-a03-custody/reference/BTC-REAL-0{5,6,8}/`
(fora do git; diffs mínimos; pacote sem ouro — ver isolamento da B01).

- **05** (base → 4/11 FAIL): filho por atributo e por `/` voltava a
  `ensure_ascii=True`/`reuse_http_connections=True`. Referência: propaga as
  duas opções na construção do derivado (conexão continua compartilhada).
  Verde 11/11; timeout, `get_request` e defaults intactos; filho congelado
  após criação.
- **06** (base → 4/6 FAIL): `deser_string` aceitava bytes curtos em silêncio
  e o callback recebia o truncado como completo. Referência: `EOFError` em
  leitura curta. Verde 6/6: `BytesIO` truncado, cursor após válida, vazia,
  e frame v1 sintético (`filterload`) percorrendo `deserialize` + `_on_data`
  (truncado não chama `on_message`; válido chama uma vez com dados íntegros).
- **08** (base → 3/7 FAIL): seleção vazia sem erro específico; flag ausente
  em `--help`. Referência: `--fail-if-empty` + erro claro antes de
  cache/daemon; sem a flag, mensagem e saída legadas. Verde 7/7:
  subprocessos com `config.ini` de fixture (criada pelo harness no workspace
  e removida ao fim; `--tmpdirprefix` único por caso — o diretório
  timestampado do runner tem resolução de 1 s e colidiria em sequência
  rápida). Sem daemon em nenhum caso.

Aceite medido (referência, execução única): 05 → 0,04 s; 06 → 0,07 s;
08 → 0,33 s (`timeout_s: 300`).

## BTC-REAL-07 — bloqueada só ela (coorte Python segue)

Requisito: sufixo `B` em `ParseByteUnits` (`src/util/strencodings.cpp:386`,
`switch` sem `case 'B'`; `ByteUnit` sem membro bytes; teste existente
`util_ParseByteUnits` em `src/test/util_tests.cpp:1623`).Fontes inspecionadas
e hashes acima conferem; **sem prova vermelho/verde: item NÃO admitido** em
`pilot.tasks.json`.

Motivo exato (verificado em 2026-10-05, sem `sudo`): headers de
desenvolvimento ausentes (`libevent-dev`, Boost ≥ 1.83 com `unit_test_framework`,
`libzmq3-dev`; só runtimes `.so` presentes) e checkout completo do `src/`
inviável neste enlace (fetch parcial >600 s para <100 MiB úteis). Mitigação
tentada: `apt-get download` + extração sem root de `libevent-dev`,
`libboost1.83-dev` (+thread/chrono/filesystem/program-options/test),
`libzmq3-dev`, `libsqlite3-dev` em `/tmp/btcdeps/root` — headers/libs
recuperados, mas sem a árvore `src/` completa não há `configure`/`test_bitcoin`.
Desbloqueio: máquina com depends (`doc/build-unix.md` do snapshot) + RAM
reservada; então configure/build isolado, `compile_commands.json` e
`test_bitcoin --run_test=util_ParseByteUnits` com caso novo executado.

## Balanço do conjunto (razão do desbalanceamento, cf. validador)

`pilot.tasks.json` traz 3 validadas (05 `bug_local`, 06 `entre_arquivos`,
08 `configuracao_interface`); `testes_comportamento_de_api` fica em 0 pela
ausência da 07. `eval.py validate` (core principal, somente leitura):
`balanced: false` sem flag (problema único: desbalanceamento vs 4/4/4/4) e
`problems: []` com `--allow-imbalance`. Esta seção é o relatório que sustenta
a exceção: conjunto parcial explícito, sem declarar piloto pronto nem 16
tarefas. Completar a 07 (ou substituta validada) antes de qualquer rodada.

## Isolamento e famílias

Mesmo padrão da B01 (custódia fora do repo; harnesses sem ouro — 08 cita só
`--fail-if-empty` genérico; `atlas-accept/**` imutável; sem testes privados
no pacote). Famílias repetidas com o smoke: `btc-authproxy` (03×05) e
`btc-runner` (04×08) — requisitos disjuntos; se usadas para política, excluir
do piloto de inferência.
