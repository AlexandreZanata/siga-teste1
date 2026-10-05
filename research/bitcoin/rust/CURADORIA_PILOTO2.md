# Curadoria piloto Bitcoin, lote 2 — EXP02 parcial (09/10/11/12)

Data: 2026-10-05. Dono: B. Base: bitcoin/bitcoin `9be056a8a72b624dae9623b2f7bded92c2a21c91`
(v31.1). Catálogo dev: `benchmarks/rust/tasks/bitcoin.dev.json` (somente leitura,
no checkout principal — não alterado). Este lote soma 4 tarefas validadas às
7 anteriores (smoke 01–04 + piloto 05/06/08); a trilha tem **11 validadas**,
faltando 07 (bloqueada) e expansão para 16 (EXP02 completa).

## Prospecção honesta

Sonda de arestas no framework Python já extraído (sem fetch novo): 9 sondas
(`deser_compact_size` vazio/meio, `deser_uint256` curto, endereço vazio,
base58 inválido/vazio, `descsum_create` Unicode/vazio, `--filter` inválido,
batch com erro/500). Descartes: `ser_compact_size(-1)` (OverflowError já
explícito), base58 vazio (retorno `b''` existente), segwit inválido
(`(None, None)` por desenho), batch com erro/500 (contratos existentes).
Admitidos só os 4 com defeito reproduzido e requisito defensável; nada
inventado para fechar quantidade.

## Vermelho → verde (base vs referência em custódia)

Referências em `/home/iiii/PESSOAL-PROJETOS-ALEXANDRE/siga-a03-custody/reference/BTC-REAL-{09,10,11,12}/`
(fora do git; diffs mínimos).

- **09** (base → 2/4 FAIL): `descsum_create("pk(☃)")` → `TypeError`
  (`None + list`). Referência: guarda `expanded is None` → `ValueError`.
  Verde 4/4; válido e vazio (`#7h0w2xvg`) preservados.
- **10** (base → 4/9 FAIL): compact vazio/meio → 0 silencioso; varint vazio
  → `IndexError`; uint256 curto → valor errado; inv truncado → hash zerado.
  Referência: leitura exata (`_read_exact`) → `EOFError` nas três funções.
  Verde 9/9 com cadeia `getdata` (truncado rejeitado, válido íntegro).
- **11** (base → 4/7 FAIL): corpo `[1,2]`/`5`/`"str"`/`null` → `TypeError`
  (inclusive dentro de `_get_response`, no `"error" in response`).
  Referência: guarda `isinstance(response, (dict, list))` em `_get_response`
  + guarda `dict` em `__call__` (batch com lista passa ileso). Verde 7/7.
- **12** (base → 2/5 FAIL): `--filter='(['` → traceback `re.error`, exit 1.
  Referência: compila após o parse; `parser.error` (exit 2) citando
  `--filter`. Verde 5/5 com `config.ini` de fixture (criada/removida pelo
  harness, `--tmpdirprefix` único por caso).

Aceite medido (referência, execução única): 09 → 0,01 s; 10 → 0,06 s;
11 → 0,04 s; 12 → 0,26 s (`timeout_s: 300`).

## Isolamento e famílias

Mesmo padrão B01/B02 (custódia fora do repo; harnesses sem ouro — citam só
`--filter` genérico; `atlas-accept/**` imutável; sem testes privados).
Famílias repetidas com requisitos disjuntos (regra de exclusão se usadas
para política): `btc-descriptors` 01×09, `btc-p2p-deserialization` 06×10,
`btc-authproxy` 03×05×11, `btc-runner` 04×08×12.
