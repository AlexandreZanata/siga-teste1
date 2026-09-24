# GC de invalidação — correção da refutação E26-03 §manutenção

Data: 2026-09-24. ID: P4-infra(a). Código: `archatlas/store.py:prune_missing`.
`REPORT.md` desta pasta permanece congelado como evidência do achado;
este arquivo registra a correção e sua verificação (sem reescrever história).

## Mudança (só `store.py` + testes)

`prune_missing(con)`: remove `files`+`symbols` cujos paths sumiram do disco
(delete; rename = delete+add), com contagens p/ telemetria. Chamado ao final de
`index_many` e `index_discovered` (retorno agora inclui `pruned_files`/
`pruned_symbols`; contratos atualizados em `tests/test_store.py`).
`index_file`/`index_any` unitários não podam (operação de 1 arquivo).

## Verificação (mesmo procedimento do achado, 3 arquivos tmp)

- init: `{indexed: 3, skipped: 0, pruned: 0/0}`.
- Após edit/delete/rename: incremental `{indexed: 2, pruned_files: 2,
  pruned_symbols: 249}`; rebuild `{indexed: 2, pruned: 0/0}`.
- `logical_equiv` (stable_hash): **True** (era False). `stale_rows`: **0** (eram 272).
- Idempotente: segunda chamada `{pruned: 0/0}`.

## Limites

GC é por ausência no disco; move fora do roots indexados exige o caller passar a
nova lista (rename entre diretórios segue delete+add). H4 volta a valer para
edit/delete/rename no escopo testado; troca de branch segue pendente de teste próprio.
