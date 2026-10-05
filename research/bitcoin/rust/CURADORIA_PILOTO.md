# Curadoria piloto Bitcoin — TASK-B02 + desbloqueio 07 (05/06/07/08)

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

## BTC-REAL-07 — DESBLOQUEADA via build C++ por TU (adaptação registrada)

Requisito: sufixo `B` em `ParseByteUnits` (`src/util/strencodings.cpp:386`,
`switch` sem `case 'B'`; `ByteUnit` sem membro bytes; teste existente
`util_ParseByteUnits` em `src/test/util_tests.cpp:1623`). **Vermelho→verde
com build e execução reais:** base → 14/17 FAIL (`10B`→nullopt com K e m,
`0B`→nullopt); referência (`case 'B'` → `ByteUnit::NOOP`) → 17/17.

Como: a TU é autocontida — `strencodings.cpp` + `hex_base.cpp` compilam com
`g++ 13.3 -std=c++20 -O1 -I src` usando só 4 headers do snapshot
(`util/strencodings.h`, `crypto/hex_base.h`, `span.h`, `util/string.h`),
sem Boost/libevent/ZMQ. O harness (`accept_b07.py`) compila as fontes **do
workspace** + a sonda `probe_b07.cpp` do atlas-accept, linka e executa
(1,21 s no total); `timeout_s: 600`. Evidências em
`experiments/bitcoin/rust/2026-10-05-b07-validation/preflight/`.

**Desvio explícito do plano B02:** o aceite original pedia build completo e
`test_bitcoin`/`util_tests` com caso novo — que seguem bloqueados (sem
headers de dev, sem sudo, fetch do `src/` inviável no enlace; deps parciais
em `/tmp/btcdeps/root`, fora do git). A unidade sob teste é exercitada de
verdade (compilador, flags, fontes e tempos registrados, nada simulado),
mas regressões de `util_tests` **não** foram executadas — ressalva para o
EXP01/julgamento. Build completo continua pendente de depends + RAM.

## Balanço do conjunto (razão do desbalanceamento, cf. validador)

`pilot.tasks.json` traz 4 validadas (05 `bug_local`, 06 `entre_arquivos`,
07 `testes_comportamento_de_api`, 08 `configuracao_interface`), balanço
1/1/1/1. `eval.py validate` (core principal, somente leitura): `balanced:
true`, `problems: []` sem flags. (Exceção anterior com `--allow-imbalance`
superada pelo desbloqueio da 07; histórico preservado nesta revisão.)

## Isolamento e famílias

Mesmo padrão da B01 (custódia fora do repo; harnesses sem ouro — 08 cita só
`--fail-if-empty` genérico; `atlas-accept/**` imutável; sem testes privados
no pacote). Famílias repetidas com o smoke: `btc-authproxy` (03×05) e
`btc-runner` (04×08) — requisitos disjuntos; se usadas para política, excluir
do piloto de inferência.
