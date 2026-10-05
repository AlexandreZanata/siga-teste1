# Aceite smoke Bitcoin — TASK-B01

Conjuntos `atlas-tasks/2` em [`smoke.tasks.json`](../smoke.tasks.json) (4 smoke
BTC-REAL-01..04, balanço 1/1/1/1) e [`pilot.tasks.json`](../pilot.tasks.json)
(3 validadas 05/06/08; 07 bloqueada, ver CURADORIA_PILOTO.md). Base
`9be056a8a72b624dae9623b2f7bded92c2a21c91` (bitcoin/bitcoin v31.1).

## Instalação no workspace do avaliador

Copiar este diretório para `<acceptance-repo>/atlas-accept/` num checkout
limpo do Bitcoin no `base_sha`, ANTES de aplicar o patch candidato:

```bash
bash atlas-accept/run.sh BTC-REAL-01   # ...02, 03, 04
```

O executor nunca escreve em `atlas-accept/` (`immutable_paths`).

## Harnesses

| Harness | Tarefa | O que verifica |
|---|---|---|
| `accept_b01.py` | checksum malformado | 9 casos: `#`/Unicode/short → False sem exceção; válido aceito; mutado rejeitado; `require=` preservado |
| `accept_b02.py` | endereços mainnet | 12 conversões v0/v5/v111/v196 × 3 payloads contra construtores de `script_util`; witness bcrt; checksum inválido e versão 42 rejeitados |
| `accept_b03.py` | Content-Type charset | 10 casos com conexão fake em-processo: json exato/com charset/caixa/espaços; `text/html` rejeitado; erro RPC, 204 e Decimal preservados |
| `accept_b04.py` | validação de `--jobs` | 5 casos em subprocessos com fixtures próprias: `--jobs=0/-1` → exit 2 citando `--jobs` sem `config.ini`; `--help` exit 0; positivo segue ao fluxo existente |
| `accept_b05.py` | propagação de opções do proxy | 11 casos com conexão fake: filho por atributo e por `/` preserva `ensure_ascii`/`reuse_http_connections`; timeout/conexão compartilhados; filho congelado |
| `accept_b06.py` | string P2P truncada | 6 casos: `EOFError` em leitura curta; cursor após válida; vazia; frame v1 sintético (`filterload`) percorrendo `deserialize` + `_on_data` |
| `accept_b08.py` | `--fail-if-empty` | 7 casos em subprocessos com `config.ini` de fixture (criada/removida pelo harness, `--tmpdirprefix` único por caso): vazia com flag → erro claro; sem flag legado; `--help` anuncia |

Tempos medidos (referência, execução única): 01 → 0,04 s; 02 → 0,17 s;
03 → 0,12 s; 04 → 0,76 s; 05 → 0,04 s; 06 → 0,07 s; 08 → 0,33 s.
`timeout_s: 300` em todas.

Sem `bitcoind`, sem build C++, sem rede de produção. Só Python 3 stdlib.
Falha de qualquer caso → exit 1. Python ou fonte ausente → exit 3
(bloqueio de ambiente).
