# Retrieval real no corpus — REPORT (`btc-e26-01-real-001`)

Pergunta: os 3 braços recuperam arquivos reais do Bitcoin v31.1 com custo conhecido?
Método: checkout `--detach BTC_SHA` somente leitura (`/tmp/btc-readonly`, HEAD
`9be056a8`, limpo); 1773 textos (C++ + Python, 0,2s); 12 sondas dev
(`benchmarks/bitcoin/e26_01_real.json`, ouro com bytes lidos, sem holdout) ×
A_busca/B_freq/C_adapter × 2 reps = 72 rodadas, ordem embaralhada com seed.
Sem modelo (patch nulo), sem custo faturado. Saídas brutas: `manifest.jsonl` + `runs.jsonl`.

## Resultados (24 rodadas/braço, 0 erros)

| braço | hit | recall | precision | entregues med | payload-citação med | used med* |
|---|---|---|---|---|---|---|
| A_busca | 1.000 | 1.000 | 0.0016 | 1432 | 47619 | 1789 |
| B_freq (top-4) | 0.500 | 0.292 | 0.1458 | 4 | 125 | 0† |
| C_adapter | 0.917 | 0.833 | 0.0062 | 301 | 8390 | 441 |

\*`used` = soma `len//4` de arquivos inteiros até 2000 (depende da ordem);
†0 quando o 1º arquivo já excede o budget — artefato da contabilidade por arquivo
inteiro; paridade com spans da cápsula SIGA pendente. `payload` = custo de citar
(nomes), não de ler.
Famílias (C): mempool/rpc/wallet 1.00; net 0.667. Miss sistemático BTC-R12
("address manager", 2/2 reps): vocabulário (`addrman` ≠ `address`) + explosão do
salto-`#include` (170 arquivos via hubs como `validation.h`), afogando o ouro.

## Leitura e decisão

A_busca tem recall perfeito e inutilizável (1432 arquivos, 47k tk só de nomes).
B_freq é barato e perdedor (metade dos hits). C_adapter é o candidato a retrieval
(recall 0.833, determinístico, 8.4k tk de citação) com duas dívidas registradas:
(1) teto de fan-in no salto por includes (hubs onipresentes); (2) mapa de vocabulário
(`addrman`, gírias do domínio) — sem adivinhação semântica.
Nada sobre patches, custo faturado ou superioridade: 12 sondas dev, 1 snapshot,
sem modelo. Próximo: cap de fan-in + repetir; depois tarefas de edição BTC-P3
(bloqueadas por modelos/teto/custodiante).
