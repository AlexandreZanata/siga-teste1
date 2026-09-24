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

## Disponibilidade nesta máquina (2026-09-24; sem reserva, sem build executado)

cmake 4.4.0, g++ 13.3.0, **sem clang++**, python 3.12.2, 16 cores, RAM livre ~2GB.
Build NÃO tentado: 1,5GB/TU exigidos sem reserva isolada de CPU/RAM, e piloto segue
bloqueado por teto/modelos. Quando autorizado: provisionar reserva por trilha, registrar
limites e serializar benchmarks com o mutex do host conforme protocolo paralelo.

## Veredito: build BLOQUEADO nesta máquina (sondagem 2026-09-24, sem alterações)

- Depends ausentes: libevent (–), Boost headers (–), libzmq (–); presente: sqlite3 3.45.1.
- Sem sudo sem-senha (`sudo -n true` exige senha) → sem `apt-get`; compilar `depends/` do
  zero escapa ao escopo unilateral (tempo/disco/impacto no host compartilhado).
- RAM no momento da sonda: 30/31GB em uso, ~0 livre — compilar agora arriscaria OOM e
  perturbaria as trilhas ativas (A em `main`, medições B); **não tentar aqui**.
- Requisito para desbloquear: máquina (ou container) com depends instalados
  (build-essential, cmake, pkgconf, python3, libevent-dev, libboost-dev, sqlite3, zmq),
  ≥8GB livres reservados e `compile_commands.json` exportado no configure.
  Comandos então: `cmake -B <run>/build -DCMAKE_EXPORT_COMPILE_COMMANDS=ON <checkout>` +
  `cmake --build` com `-j` dentro da reserva, tudo em runtime `/tmp`, corpus intacto.

## Pendente antes de qualquer rodada com build

Toolchain instalada e versionada, `compile_commands.json` (hash), features habilitadas,
comandos realmente usados, datadir/portas/caches isolados por rodada. Builds limpos/
reutilizados como condições documentadas iguais entre braços (BTC-P1 §2).
