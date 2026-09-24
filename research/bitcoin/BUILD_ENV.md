# BTC-P2 — Ambiente de build Bitcoin (especificado; nada compilado)

Data: 2026-09-24. Dono: agente B. Snapshot: `v31.1` (`9be056a8…`). Fonte: leitura dos docs
no tag (`doc/build-unix.md`, `doc/dependencies.md`, `test/functional/README.md`,
`depends/README.md`); **nenhum comando de build executado**, toolchain não registrada.
Guia futuro de `DEV_GUIDE.md`; pré-requisito do piloto real.

## Sistema de build e requisitos observados

- Build: **CMake** (`cmake -B build && cmake --build build`; sem autotools em v31.1 —
  `Makefile.am`/`configure.ac` ausentes). `depends/` presente (Boost 1.74.0, libevent 2.1.8,
  SQLite ≥3.7.17 p/ wallet, ZeroMQ 4.0.0 p/ notificações; versões mínimas no tag).
- Compilador: gcc default, clang opcional; memória recomendada ≥1.5GB por TU
  (`doc/build-unix.md`). Flags/features efetivos: **pendentes** (só após build real).
- Testes funcionais: `build/test/functional/test_runner.py` (Python 3, versão mínima em
  `doc/dependencies.md`; `--coverage` p/ RPCs; `--extended`); `example_test.py` como modelo;
  estilo PEP-8/flake8. Ambiente: **regtest isolado** (nunca mainnet/fundos/produção).

## Pendente antes de qualquer rodada com build

Toolchain instalada e versionada, `compile_commands.json` (hash), features habilitadas,
comandos realmente usados, datadir/portas/caches isolados por rodada. Builds limpos/
reutilizados como condições documentadas iguais entre braços (BTC-P1 §2).
