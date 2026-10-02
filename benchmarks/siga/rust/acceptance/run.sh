#!/bin/bash
# Aceite imutavel do avaliador — conjunto smoke SIGA (TASK-A03).
#
# Instalacao (workspace do AVALIADOR, nunca do executor): copiar o diretorio
# `benchmarks/siga/rust/acceptance/` deste repo para `<acceptance-repo>/atlas-accept/`
# numa base limpa no `base_sha` da tarefa, ANTES de aplicar o patch candidato.
# O executor nunca escreve em `atlas-accept/` (ver `immutable_paths`).
#
# Uso (cwd = raiz do acceptance-repo, que e um checkout do dataset SIGA):
#   bash atlas-accept/run.sh SIGA-REAL-01
#
# O que faz: compila as fontes do workspace + harness com `javac` e executa.
# Qualquer caso FAIL ou excecao => exit != 0. Sem Maven/JUnit/rede.
# Deps (commons-lang, jakarta.inject, jcabi-manifests) resolvidas do repositorio
# Maven local; se ausentes, sai com codigo 3 = BLOQUEIO DE AMBIENTE (nunca falha
# do agente, nunca sucesso silencioso).
set -u
TASK="${1:?uso: bash atlas-accept/run.sh SIGA-REAL-0X}"
HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="$(pwd)"
BUILD="$WORK/.atlas-accept-build"
rm -rf "$BUILD"; mkdir -p "$BUILD/classes"

M2="${M2_REPO:-$HOME/.m2/repository}"
D1="$M2/commons-lang/commons-lang/2.6/commons-lang-2.6.jar"
D2="$M2/jakarta/inject/jakarta.inject-api/2.0.1/jakarta.inject-api-2.0.1.jar"
D3="$M2/com/jcabi/jcabi-manifests/1.1/jcabi-manifests-1.1.jar"
for j in "$D1" "$D2" "$D3"; do
  if [ ! -f "$j" ]; then
    echo "ATLAS-ENV-BLOCK: dependencia ausente: $j (rede Maven ou aquecimento do repo local)" >&2
    exit 3
  fi
done
DEPS="$D1:$D2:$D3"

JAVAC="${JAVAC_BIN:-javac}"
JAVA="${JAVA_BIN:-java}"
if ! command -v "$JAVAC" >/dev/null 2>&1; then
  echo "ATLAS-ENV-BLOCK: javac ausente no PATH (exige JDK 21 completo)" >&2
  exit 3
fi

BASE="$WORK/siga-base/src/main/java"
EX="$WORK/siga-ex/src/main/java"
case "$TASK" in
  SIGA-REAL-01)
    SRCS="$BASE/br/gov/jfrj/siga/base/util/Texto.java"
    HARNESS="AtlasAccept01" ;;
  SIGA-REAL-02)
    SRCS="$BASE/br/gov/jfrj/siga/base/util/Texto.java $EX/br/gov/jfrj/siga/ex/util/DocumentoUtil.java"
    HARNESS="AtlasAccept02" ;;
  SIGA-REAL-03)
    SRCS="$BASE/br/gov/jfrj/siga/base/util/CPFUtils.java $BASE/br/gov/jfrj/siga/base/AplicacaoException.java $BASE/br/gov/jfrj/siga/base/SigaVersion.java"
    HARNESS="AtlasAccept03" ;;
  SIGA-REAL-04)
    SRCS="$BASE/br/gov/jfrj/siga/base/Prop.java $BASE/br/gov/jfrj/siga/base/AplicacaoException.java $BASE/br/gov/jfrj/siga/base/SigaVersion.java $BASE/br/gov/jfrj/siga/model/enm/NivelDaConta.java"
    HARNESS="AtlasAccept04" ;;
  *)
    echo "tarefa desconhecida neste conjunto: $TASK" >&2
    exit 2 ;;
esac

# shellcheck disable=SC2086
"$JAVAC" -nowarn -cp "$DEPS" -d "$BUILD/classes" $SRCS || exit $?
"$JAVAC" -nowarn -cp "$BUILD/classes:$DEPS" -d "$BUILD/classes" "$HERE/$HARNESS.java" || exit $?
"$JAVA" -cp "$BUILD/classes:$DEPS" "$HARNESS"
