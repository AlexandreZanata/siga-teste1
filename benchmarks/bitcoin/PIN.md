# PIN Bitcoin (dataset pinado) — BTC-P0 resolvido em follow-up

Track: `bitcoin`. Dono: agente B. Origem criada em BTC-P0; SHA resolvido em 2026-09-24
(pós-BTC-P7) via `git ls-remote` + clone filtrado somente leitura. Nenhum valor inventado.

## Snapshot pinado

- Origem: `https://github.com/bitcoin/bitcoin` (repositório oficial).
- Ref: `v31.1` (última release estável publicada antes do corte 2026-09-24 — release 31.1 de
  2026-07-08; tags de release são imutáveis; escolha determinística, sem cherry-picking).
- `BTC_SHA`: `9be056a8a72b624dae9623b2f7bded92c2a21c91` (commit do tag, verificado por
  `ls-remote 'refs/tags/v31.1*'` → `v31.1^{}` e `rev-parse 'v31.1^{commit}'` no clone).
- Commit: `2026-07-06 15:09:19 +0200`, `Merge bitcoin/bitcoin#35666: [31.x] Finalise 31.1`.
- Data da resolução: 2026-09-24. Método: `git clone --filter=blob:none --no-checkout` (sem blobs,
  sem working tree por desenho) + `ls-tree`/`cat-file`/`show` sobre o object store.
- Estado da árvore: tag verificado no object store (`rev-parse` confere) + checkout
  `--detach BTC_SHA` somente leitura em 2026-09-24 (HEAD `9be056a8`, `status` limpo, 151M).
  Caminho local em configuração não versionada; edições futuras só em cópias descartáveis.
- Licença observada: **MIT** (`v31.1:COPYING`: "The MIT License (MIT)", © 2009-2026).
- Layout confirmado por listagem (2923 paths): `src/` (2003), `test/` (414, inclui
  `test/functional/`), `doc/` (180); `src/rpc/` (28), `src/wallet/` (86), `src/test/` (334).
  Sem afirmação de símbolos/caminhos de chamada antes de inspeção de bytes.
- Nenhum corpus copiado para este repositório; checkout descartável fora da árvore, somente leitura.

## Referências de build no snapshot (existência verificada no tag; conteúdo/toolchain pendentes)

- `doc/build-unix.md`, `test/README.md`, `test/functional/README.md`, `src/test/README.md`:
  todos EXISTEM em `v31.1` (verificado via `cat-file -e`; conteúdo ainda não confrontado).
- Pendente (fase de build/índice): compilador, flags, dependências, features habilitadas e
  comandos realmente usados (conteúdo dos docs ainda não confrontado).
  Testes funcionais usam ambiente isolado/regtest; nenhum resultado depende de mainnet,
  fundos, carteira pessoal ou nó de produção.

## Critério de aceite deste arquivo

`BTC_SHA` completo + origem + data + licença observada: **verificados**.
Estado da árvore: tag verificado, working tree pendente. CENSO com contagens reais registrado;
adaptador e benchmarks seguem bloqueados até checkout com working tree + toolchain
(edições experimentais futuras: cópias/checkout descartáveis por tarefa, sem histórico futuro).
