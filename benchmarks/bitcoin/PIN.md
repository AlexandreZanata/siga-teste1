# PIN Bitcoin (dataset pinado) — BTC-P0

Track: `bitcoin`. Etapa: BTC-P0. Dono: agente B.
Estado: **pendente de SHA** — este arquivo registra o candidato e o procedimento,
sem inventar hash, contagem ou caminho de código.

## Candidato

- Origem: `https://github.com/bitcoin/bitcoin` (repositório oficial).
- Ref: **não escolhida** (ex.: tag de release ou commit `master` posterior à decisão;
  a escolha ocorre antes de qualquer indexação e fica registrada aqui com data).
- `BTC_SHA`: **não definido** (40/64 hex completos reais exigidos; nenhum valor pronto neste documento).
- Data do snapshot: pendente. Estado da árvore: pendente (`git status` limpo + `rev-parse HEAD` no checkout do dataset).
- Licença observada: pendente de leitura no snapshot (esperado MIT com contribuidores; confirmar em `COPYING`).
- Corpus inicial pretendido: `src/`, `test/functional/`, `test/unit/` (ou layout do snapshot escolhido);
  confirmar por listagem, sem afirmar caminhos de chamada/símbolos antes de inspeção.

## Procedimento de pin (não executado em BTC-P0)

```sh
git ls-remote https://github.com/bitcoin/bitcoin HEAD
git clone --no-checkout https://github.com/bitcoin/bitcoin <btc-readonly>
git -C <btc-readonly> rev-parse <ref-escolhida>   # 40 hex completos -> BTC_SHA
git -C <btc-readonly> checkout --detach <BTC_SHA>
git -C <btc-readonly> status --short && git -C <btc-readonly> rev-parse HEAD
```

Somente leitura; edições experimentais futuras ocorrem em cópias/checkout descartáveis
por tarefa, fora do corpus do índice e sem histórico futuro acessível ao executor.

## Referências de build a confrontar no SHA escolhido

- `doc/build-unix.md`, `test/README.md`, `test/functional/README.md` do próprio snapshot
  (consultadas como `master` em 2026-09-24 no plano; o PIN vale pelo snapshot, não pelo `master`).
- Registrar: compilador, flags, dependências, features habilitadas e comandos realmente usados.
  Testes funcionais usam ambiente isolado/regtest; nenhum resultado depende de mainnet,
  fundos, carteira pessoal ou nó de produção.

## Critério de aceite deste arquivo

`BTC_SHA` completo + origem + data + estado da árvore + licença observada,
todos verificados no checkout somente leitura. Até lá, CENSO, adaptador e qualquer
benchmark permanecem bloqueados por este PIN.
