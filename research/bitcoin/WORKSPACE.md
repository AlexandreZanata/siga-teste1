# WORKSPACE Bitcoin (agente B)

Dono: agente B. Etapa: BTC-P0. Track: `bitcoin`.

## Identificadores

- `BASE_SHA`: `e6fde134f7da0d3616d90c40232d9ebe2ed9f033` (commit publicado; `git log --oneline -1` na worktree).
- `method_revision`: `e6fde134f7da0d3616d90c40232d9ebe2ed9f033` (mesmo que `BASE_SHA`; nenhum core novo incorporado nesta etapa).
- `core_sha`: `e6fde134f7da0d3616d90c40232d9ebe2ed9f033` (somente leitura; nenhum edit em `archatlas/` nesta etapa).
- `adapter_sha`: nulo (nenhum adaptador `archatlas/bitcoin/**` criado em BTC-P0).
- `BTC_SHA`: não definido (PIN pendente; ver `benchmarks/bitcoin/PIN.md`). Nenhum SHA inventado.
- `DOCS_SHA`: pendente. O checkout A (`main`) contém revisão documental paralela não commitada
  (`plans/PARALLEL_EXECUTION.md`, `plans/SIGA_EXECUTION.md`, `plans/bitcoin/`, `research/bitcoin/`,
  mais edições em `plans/BITCOIN_PARALLEL_PLAN.md` e outros). Por protocolo, arquivos não commitados
  não são dependência estável: esta worktree NÃO os herdou e NÃO os copiou. A incorporação do checkpoint
  documental publicado ocorrerá entre rodadas, com SHA registrado aqui.
- Branch de escrita: `codex/bitcoin-context` (exclusiva desta worktree).
- Worktree alias: `btc-worktree` (caminho absoluto local em configuração não versionada; não publicado aqui).
- `run_id`: nenhum (BTC-P0 é auditoria documental + verificação offline; sem rodada de medição).

## Isolamento confirmado (2026-09-24, nesta worktree)

- `git rev-parse --show-toplevel` = worktree própria (não o checkout A).
- `git branch --show-current` = `codex/bitcoin-context`.
- `git rev-parse HEAD` = `e6fde134f7da0d3616d90c40232d9ebe2ed9f033`.
- `git status --short` limpo antes da escrita BTC-P0 (verificado).
- Nenhum `checkout`/`switch`/`reset`/`clean`/`stash` executado no diretório do agente A.
- Escrita somente em namespaces Bitcoin:
  `research/bitcoin/**`, `plans/bitcoin/**`, `benchmarks/bitcoin/**`.
  Nenhum edit em `archatlas/`, testes comuns, `pyproject.toml`, CI ou docs canônicos.
- Runtime por rodada (alias, sem paths absolutos versionados):
  `$TMPDIR/archatlas-bitcoin/<run_id>/` para SQLite/WAL, caches, logs e builds.
  Dataset Bitcoin ainda sem checkout: somente leitura quando pinado; sem escrita no corpus.
- Dataset via variável somente no processo (`ARCHATLAS_DATASET=/caminho/para/bitcoin` por comando).
  `ARCHATLAS_DATASET_BTC` é alias planejado do launcher, não variável reconhecida pelo core atual.
  Nenhum profile de shell ou config global alterado.
- Venv/dependências: sem reutilizar instalação editable do agente A; `pytest` executado com cwd da worktree.
- Medição de desempenho: nenhuma rodada de latência nesta etapa; reserva/mutex (`flock`) só antes de benchmarks futuros.

## Próximo passo

Resolver `BTC_SHA` (comando em `benchmarks/bitcoin/PIN.md`), depois BTC-P1
(`research/bitcoin/LITERATURE_APPLICATION.md` + `PREREGISTRATION.md` próprios).
