# Curadoria piloto Bitcoin, lote final — EXP02 completa (13/14/15/16)

Data: 2026-10-05. Dono: B. Base: bitcoin/bitcoin `9be056a8a72b624dae9623b2f7bded92c2a21c91`
(v31.1). Catálogo dev: `benchmarks/rust/tasks/bitcoin.dev.json` (somente leitura,
no checkout principal — não alterado). Este lote soma 4 tarefas validadas às
12 anteriores (smoke 01–04 + piloto 05–08 + lote2 09–12); a trilha tem **16
validadas** (EXP02 completa).

## Prospecção honesta

Sonda de arestas no framework Python já extraído (`/tmp/btcp3`, sem fetch
novo): multisig com k=0/k>n/[] (`keys_to_multisig_script` monta `00…`/`0000ae`
ou `AssertionError`), `build_message` com tipo de 13 bytes (trunca silencioso),
`satoshi_round` com modo `None`/`'BOGUS'`/número (default silencioso ou
`TypeError`), `--tmpdirprefix` inexistente (`PermissionError`/`FileExistsError`
ou criação de datadir em vez de erro de uso). Descartes: `ser_compact(-1)`
(`OverflowError` já explícito), b58 vazio, segwit `None`, batch erro/500,
`CScriptNum`, ver256, e demais sondas sem defeito reproduzível. Admitidos só
os 4 com defeito reproduzido e requisito defensável; nada inventado para
fechar quantidade.

## Vermelho → verde (base vs referência em custódia)

Referências em `/home/iiii/PESSOAL-PROJETOS-ALEXANDRE/siga-a03-custody/reference/BTC-REAL-{13,14,15,16}/`
(fora do git; diffs mínimos).

- **13** (base → 3/6 FAIL): `keys_to_multisig_script([K1,K2], k=0)` monta
  script degenerado; k=3 com n=2 → `AssertionError`; `[]` monta `0000ae`.
  Referência: guarda `1 <= k <= n` → `ValueError`. Verde 6/6; n-de-n padrão,
  1-de-2 e 2-de-3 preservados.
- **14** (base → 1/4 FAIL): `build_message` com tipo de 13 bytes monta frame
  truncado sem erro (despacho corrompido). Referência: guarda
  `len(msgtype) > 12` → `ValueError`. Verde 4/4 com 12 bytes, vazio e
  ida-e-volta `ping` (desserialização + callback) preservados.
- **15** (base → 3/7 FAIL): `satoshi_round('1.5', rounding=None)` aceita
  silencioso (default do contexto); `'BOGUS'`/número → `TypeError` interno.
  Referência: conjunto de 8 modos decimais, fora dele → `ValueError` (+
  parentetização do import decimal). Verde 7/7 com 8 modos e arredondamentos
  (down/up/half-even) preservados.
- **16** (base → 2/4 FAIL): `--tmpdirprefix` inexistente cria datadir com
  exit 1 em vez de erro de uso. Referência: `os.path.isdir` após o parse;
  `parser.error` (exit 2) citando `--tmpdirprefix`. Verde 4/4 com `config.ini`
  de fixture (criada/removida pelo harness, prefixo válido segue o fluxo).

Aceite medido (referência, execução única): 13 → 0,07 s; 14 → 0,08 s;
15 → 0,05 s; 16 → 0,22 s (`timeout_s: 300`).

## Isolamento e famílias

Mesmo padrão B01/B02 (custódia fora do repo; harnesses sem ouro — citam só
`--tmpdirprefix` genérico; `atlas-accept/**` imutável; sem testes privados;
`*.log` fora — preflight em `.txt`; `--tmpdirprefix` único por caso onde há
subprocesso; `sys.path[0]` resolve symlinks — workspaces com layout
`base/test_framework` + `base/test_runner.py` irmãos).
Famílias repetidas com requisitos disjuntos (regra de exclusão se usadas
para política): `btc-p2p-deserialization` 06×10×14, `btc-runner` 04×08×12×16;
famílias novas sem repetição: `btc-script-multisig` (13),
`btc-amount-rounding` (15). Demais famílias (`btc-descriptors` 01×09,
`btc-authproxy` 03×05×11) intactas e documentadas nos lotes anteriores.
