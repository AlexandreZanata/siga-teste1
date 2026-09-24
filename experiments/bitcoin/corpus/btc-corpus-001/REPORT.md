# Primeira medição no corpus real — REPORT (`btc-corpus-001`)

Pergunta: o adaptador Bitcoin opera no corpus v31.1 com custo e cobertura conhecidos?
Método: checkout `--detach BTC_SHA` somente leitura; `discover()` + LOC + `cpp_lex` sobre
1409 C++; `header_pairs` sobre os fatos. Sem modelo, sem índice persistente, sem benchmark.

## Medições (reais; leitura, sem edição)

- Checkout: HEAD `9be056a8`, `status` limpo; 151M com working tree.
- `discover()`: 1873 arquivos (cpp 1409, python 364, js 100) — `.cc` (89) fora do `EXT_MAP`
  publicado: lacuna registrada, sem correção silenciosa do core.
- LOC: cpp 372.576, python 90.096, js 295.906 (js = locale Qt, fora de cobertura).
- Adaptador: 1409/1409 arquivos, 0 erros, 0,2s; **12.546** fatos-`include`; **368** pares
  header/impl; top: `vector` 396, `string` 351, `cstdint` 336, `test/util/setup_common.h` 194.
- Correção deste commit: `skipped` 662 → **10** (heurística confundia a palavra "include" em
  comentários; agora só diretivas `#` malformadas vão a `skipped`, resto ignorado sem ruído).
  As 10 restantes são diretivas reais a triar — pendência registrada, sem descarte.

## Limites e decisão

Sem símbolos/entidades (A1/A2 confirmados em escala); sem build; sem qualidade de retrieval
medida. Achado `manter` como linha de base do corpus; `C_btc` segue candidato sintético até
revalidação com tarefas reais. Próximo: triar os 10 skipped + pilha de tarefas reais pós-ambiente.
