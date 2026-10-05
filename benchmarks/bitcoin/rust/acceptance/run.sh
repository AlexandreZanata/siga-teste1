#!/bin/bash
# Aceite imutavel do avaliador — conjuntos smoke (TASK-B01) e piloto (TASK-B02) Bitcoin.
#
# Instalacao (workspace do AVALIADOR, nunca do executor): copiar o diretorio
# `benchmarks/bitcoin/rust/acceptance/` deste repo para `<acceptance-repo>/atlas-accept/`
# numa base limpa no `base_sha` da tarefa (checkout do bitcoin/bitcoin),
# ANTES de aplicar o patch candidato. O executor nunca escreve em
# `atlas-accept/` (ver `immutable_paths` em smoke.tasks.json / pilot.tasks.json).
#
# Uso (cwd = raiz do acceptance-repo, checkout do Bitcoin no base_sha):
#   bash atlas-accept/run.sh BTC-REAL-01   # ...05..12 (todas com aceite executavel)
#
# O que faz: executa o harness Python correspondente contra as fontes do
# workspace (`test/functional/test_framework/`, `test/functional/test_runner.py`).
# Qualquer caso FAIL ou excecao => exit != 0. Sem bitcoind, sem rede de
# producao (03/05/11 usam conexao fake em-processo; 04/08/12 usam
# subprocessos com fixtures proprias; 06/10 usam socket/frame sinteticos locais;
# 08/12 criam config.ini de fixture no workspace e a removem ao fim).
# 07 compila C++ de verdade (g++): a TU autocontida + sonda do atlas-accept.
# Deps: somente Python 3 stdlib. python3 ausente ou fontes do workspace
# ausentes => exit 3 = BLOQUEIO DE AMBIENTE (nunca falha do agente, nunca
# sucesso silencioso).
set -u
TASK="${1:?uso: bash atlas-accept/run.sh BTC-REAL-0X}"
HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="$(pwd)"

PY="${PYTHON_BIN:-python3}"
if ! command -v "$PY" >/dev/null 2>&1; then
  echo "ATLAS-ENV-BLOCK: python3 ausente no PATH (exige Python 3 stdlib)" >&2
  exit 3
fi

# Workspace do avaliador pode ser apontado explicitamente (harness/teste).
if [ -n "${BTC_WORKSPACE:-}" ]; then
  WORK="$BTC_WORKSPACE"
fi

case "$TASK" in
  BTC-REAL-01)
    [ -f "$WORK/test/functional/test_framework/descriptors.py" ] || { echo "ATLAS-ENV-BLOCK: fonte ausente no workspace: test/functional/test_framework/descriptors.py" >&2; exit 3; }
    HARNESS="accept_b01" ;;
  BTC-REAL-02)
    [ -f "$WORK/test/functional/test_framework/address.py" ] || { echo "ATLAS-ENV-BLOCK: fonte ausente no workspace: test/functional/test_framework/address.py" >&2; exit 3; }
    HARNESS="accept_b02" ;;
  BTC-REAL-03)
    [ -f "$WORK/test/functional/test_framework/authproxy.py" ] || { echo "ATLAS-ENV-BLOCK: fonte ausente no workspace: test/functional/test_framework/authproxy.py" >&2; exit 3; }
    HARNESS="accept_b03" ;;
  BTC-REAL-04)
    [ -f "$WORK/test/functional/test_runner.py" ] || { echo "ATLAS-ENV-BLOCK: fonte ausente no workspace: test/functional/test_runner.py" >&2; exit 3; }
    HARNESS="accept_b04" ;;
  BTC-REAL-05)
    [ -f "$WORK/test/functional/test_framework/authproxy.py" ] || { echo "ATLAS-ENV-BLOCK: fonte ausente no workspace: test/functional/test_framework/authproxy.py" >&2; exit 3; }
    HARNESS="accept_b05" ;;
  BTC-REAL-06)
    [ -f "$WORK/test/functional/test_framework/messages.py" ] || { echo "ATLAS-ENV-BLOCK: fonte ausente no workspace: test/functional/test_framework/messages.py" >&2; exit 3; }
    [ -f "$WORK/test/functional/test_framework/p2p.py" ] || { echo "ATLAS-ENV-BLOCK: fonte ausente no workspace: test/functional/test_framework/p2p.py" >&2; exit 3; }
    HARNESS="accept_b06" ;;
  BTC-REAL-07)
    [ -f "$WORK/src/util/strencodings.cpp" ] || { echo "ATLAS-ENV-BLOCK: fonte ausente no workspace: src/util/strencodings.cpp" >&2; exit 3; }
    HARNESS="accept_b07" ;;
  BTC-REAL-08)
    [ -f "$WORK/test/functional/test_runner.py" ] || { echo "ATLAS-ENV-BLOCK: fonte ausente no workspace: test/functional/test_runner.py" >&2; exit 3; }
    HARNESS="accept_b08" ;;
  BTC-REAL-09)
    [ -f "$WORK/test/functional/test_framework/descriptors.py" ] || { echo "ATLAS-ENV-BLOCK: fonte ausente no workspace: test/functional/test_framework/descriptors.py" >&2; exit 3; }
    HARNESS="accept_b09" ;;
  BTC-REAL-10)
    [ -f "$WORK/test/functional/test_framework/messages.py" ] || { echo "ATLAS-ENV-BLOCK: fonte ausente no workspace: test/functional/test_framework/messages.py" >&2; exit 3; }
    HARNESS="accept_b10" ;;
  BTC-REAL-11)
    [ -f "$WORK/test/functional/test_framework/authproxy.py" ] || { echo "ATLAS-ENV-BLOCK: fonte ausente no workspace: test/functional/test_framework/authproxy.py" >&2; exit 3; }
    HARNESS="accept_b11" ;;
  BTC-REAL-12)
    [ -f "$WORK/test/functional/test_runner.py" ] || { echo "ATLAS-ENV-BLOCK: fonte ausente no workspace: test/functional/test_runner.py" >&2; exit 3; }
    HARNESS="accept_b12" ;;
  *)
    echo "tarefa desconhecida neste conjunto: $TASK" >&2
    exit 2 ;;
esac

BTC_WORKSPACE="$WORK" "$PY" "$HERE/$HARNESS.py"
