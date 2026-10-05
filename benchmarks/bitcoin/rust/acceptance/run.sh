#!/bin/bash
# Aceite imutavel do avaliador — conjunto smoke Bitcoin (TASK-B01).
#
# Instalacao (workspace do AVALIADOR, nunca do executor): copiar o diretorio
# `benchmarks/bitcoin/rust/acceptance/` deste repo para `<acceptance-repo>/atlas-accept/`
# numa base limpa no `base_sha` da tarefa (checkout do bitcoin/bitcoin),
# ANTES de aplicar o patch candidato. O executor nunca escreve em
# `atlas-accept/` (ver `immutable_paths` em smoke.tasks.json).
#
# Uso (cwd = raiz do acceptance-repo, checkout do Bitcoin no base_sha):
#   bash atlas-accept/run.sh BTC-REAL-01
#
# O que faz: executa o harness Python correspondente contra as fontes do
# workspace (`test/functional/test_framework/`, `test/functional/test_runner.py`).
# Qualquer caso FAIL ou excecao => exit != 0. Sem bitcoind, sem build C++,
# sem rede de producao (03 usa conexao fake em-processo; 04 usa subprocessos
# com fixtures proprias em diretorio temporario).
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
  *)
    echo "tarefa desconhecida neste conjunto: $TASK" >&2
    exit 2 ;;
esac

BTC_WORKSPACE="$WORK" "$PY" "$HERE/$HARNESS.py"
