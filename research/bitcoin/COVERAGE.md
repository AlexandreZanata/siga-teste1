# BTC-P2 — Cobertura do adaptador no corpus v31.1 (medida; sem semântica)

Data: 2026-09-24. Dono: agente B. Método: `discover()` + `cpp_lex` + `header_pairs` sobre
checkout `--detach BTC_SHA` (1409 C++, 0 erros, 0,2s). Fatos: **12.546** includes,
**368** pares header/impl (737 arquivos em pares), `skipped` **0** após triagem
(`__has_include` não é diretiva — corrigido neste commit com teste).

## Por área (`src/*`; arquivos / includes / arquivos-em-pares)

node 62/598/58 · wallet 83/900/53 · util 78/427/57 · rpc 28/459/18 · crypto 40/154/32 ·
script 22/192/20 · kernel 29/210/16 · policy 18/159/17 · index 12/213/10 · ipc 58/449/16 ·
consensus 10/38/7 · primitives 5/53/2 · support 8/42/5 · interfaces 9/75/3 · zmq 10/78/10 ·
bench 59/676/22 · leveldb 58/208/4 · minisketch 30/148/2 · init 7/59/0 · univalue 10/110/2 ·
common 25/226/22 · compat 7/32/2 · logging 2/8/0 · src raiz 155/1869/126.

## Contrapartes de teste e fora de cobertura

- 371 arquivos sob dirs de teste (`src/test/`, `src/wallet/test/`, `test/functional/` 378 PY);
  hub: `test/util/setup_common.h` (194 includes). `code2test` futuro ancora aqui.
- Fora de cobertura: `qt/` (136 arqs, GUI), `secp256k1/` + `leveldb/` + `crc32c/` (libs externas),
  `.cc` (89, fora do `EXT_MAP`), `.ts` locale, semântica (overloads/templates/macros/virtuais).
- Decisão: áreas RPC/validação/mempool/wallet/rede/testes têm fatos densos para tarefas BTC-P3;
  GUI/libs externas excluídas do lote por desenho (não por falha).
