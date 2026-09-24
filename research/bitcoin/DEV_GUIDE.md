# Guia do desenvolvedor Bitcoin (capacidades reais BTC-P0–P7; sem promessa de ganho)

Dono: agente B. Candidato: `C_btc` = core(`e6fde13`) + `btc-cpp-lex/1` + `btc-pack/1`.
Instalação isolada e reversível; nada global, nada no dataset base, nada em produção.

## 1. Instalação e remoção

Use worktree/branch próprias e runtime por rodada (`$TMPDIR/archatlas-bitcoin/<run_id>/`
para DB, caches, logs, builds). Dataset por variável só no processo
(`ARCHATLAS_DATASET=<checkout-somente-leitura>`); nunca herde defaults. Remoção:
apague worktree, branch local e runtime — nenhum resíduo em código ou config global
(`uninstall` do `devflow` demonstra reversibilidade total no ensaio).

## 2. Jornadas suportadas (ensaio em `experiments/bitcoin/e26_06/btc-e2606-drill-001/`)

- Falha de teste → implementação/testes: consulte, abra a evidência (`expand`), edite em
  checkout isolado da tarefa, valide, atualize o índice.
- Mudança RPC → contrato/consumidores: includes e pares header/impl textuais; macros e
  despacho dinâmico NÃO resolvidos — declare a lacuna.
- Mudança de header → impacto/reindexação: `temporal.diff_snapshots` lista invalidados;
  reextraia a fração indicada, não o corpus inteiro.
- Fonte obsoleta → diagnóstico/fallback: estado `stale`, nunca trecho antigo como atual;
  linguagem sem suporte → `unsupported` com diagnóstico, nunca vazio enganoso.

## 3. Capacidades declaradas (reais; resto é `unsupported`)

| Capacidade | Estado |
|---|---|
| C++: arquivos + `#include` verificados; pares header/impl textuais | suportado (lexical) |
| Python: símbolos via `ast` | suportado |
| Overloads, templates, macros, virtuais, dinâmica, GUI | NÃO suportado |
| Build/teste funcionais | pendente de snapshot + toolchain (regtest isolado) |
| Economia de custo / adoção medida | NÃO medida (sem humano até aqui) |

## 4. Regras

Mesmo modelo/tarefa/snapshot/ambiente por bloco ao comparar; cite `arquivo:linha@SHA`;
gabaritos e testes ocultos nunca no índice; sem mainnet/fundos/nó de produção.
Achou `unsupported`? É limite documentado (ver `LIMITATIONS.md`), não bug a contornar em silêncio.
