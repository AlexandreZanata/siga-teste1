#!/bin/bash
# Aceite PRIVADO do avaliador — terceiro lote piloto SIGA 17-20 (NEXT-03).
#
# Quem roda: o OPERADOR da custodia (avaliador), NUNCA o executor. O arquivo
# com os casos privados ($PRIVATE_JAVA, na custodia, fora do git) e informado
# por caminho absoluto e compilado direto de la: nenhum caso privado e copiado
# para o acceptance-repo, e o build ocorre em $PRIVATE_BUILD (scratch do
# avaliador, apagado apos o julgamento).
#
# Uso (cwd = raiz de um CLONE FREsco da base no `base_sha` da tarefa, com o
# patch candidato ja aplicado; variaveis do operador):
#   PRIVATE_JAVA=/custodia/acceptance-private/CasosPrivadosPilot3.java \
#   PRIVATE_BUILD=/tmp/scratch-privado \
#   bash atlas-accept/run-private3.sh SIGA-REAL-17
#
# O que faz: compila as fontes do workspace + casos privados com `javac` e
# executa. Qualquer caso FAIL ou excecao => exit != 0. Sem Maven/JUnit/rede.
# Deps como em run-pilot3.sh (ausente => exit 3 = BLOQUEIO DE AMBIENTE).
# O verde publico NAO basta: o veredito final exige este runner tambem verde
# (ver `benchmarks/rust/grade.py`, regra `atlas-grade/1`).
set -u
TASK="${1:?uso: bash atlas-accept/run-private3.sh SIGA-REAL-1X}"
HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="$(pwd)"
: "${PRIVATE_JAVA:?variavel PRIVATE_JAVA ausente (caminho do .java privado na custodia)}"
BUILD="${PRIVATE_BUILD:-$(mktemp -d atlas-private-build.XXXXXX)}"
mkdir -p "$BUILD/classes"

M2="${M2_REPO:-$HOME/.m2/repository}"
D1="$M2/commons-lang/commons-lang/2.6/commons-lang-2.6.jar"
D2="$M2/jakarta/inject/jakarta.inject-api/2.0.1/jakarta.inject-api-2.0.1.jar"
D3="$M2/com/jcabi/jcabi-manifests/1.1/jcabi-manifests-1.1.jar"
for j in "$D1" "$D2" "$D3" "$PRIVATE_JAVA"; do
  if [ ! -f "$j" ]; then
    echo "ATLAS-ENV-BLOCK: ausente: $j" >&2
    exit 3
  fi
done
DEPS="$D1:$D2:$D3"

need_jars() {
  for j in "$@"; do
    if [ ! -f "$j" ]; then
      echo "ATLAS-ENV-BLOCK: dependencia ausente: $j" >&2
      exit 3
    fi
    DEPS="$DEPS:$j"
  done
}

JAVAC="${JAVAC_BIN:-javac}"
JAVA="${JAVA_BIN:-java}"
if ! command -v "$JAVAC" >/dev/null 2>&1; then
  echo "ATLAS-ENV-BLOCK: javac ausente no PATH (exige JDK 21 completo)" >&2
  exit 3
fi

# Superconjunto das fontes do lote: atende 17-20 sem matriz por tarefa.
BASE="$WORK/siga-base/src/main/java"
need_jars \
  "$M2/jakarta/servlet/jakarta.servlet-api/6.0.0/jakarta.servlet-api-6.0.0.jar" \
  "$M2/org/apache/commons/commons-text/1.9/commons-text-1.9.jar" \
  "$M2/org/apache/commons/commons-lang3/3.20.0/commons-lang3-3.20.0.jar" \
  "$M2/jakarta/persistence/jakarta.persistence-api/3.1.0/jakarta.persistence-api-3.1.0.jar" \
  "$M2/com/crivano/jlogic/1.1.1/jlogic-1.1.1.jar"
SRCS="$BASE/br/gov/jfrj/siga/base/util/Utils.java $BASE/br/gov/jfrj/siga/base/util/Texto.java $BASE/br/gov/jfrj/siga/base/GZip.java $BASE/br/gov/jfrj/siga/model/Historico.java $BASE/br/gov/jfrj/siga/model/Assemelhavel.java $BASE/br/gov/jfrj/siga/base/AcaoVO.java $BASE/br/gov/jfrj/siga/base/VO.java"

case "$TASK" in
  SIGA-REAL-17|SIGA-REAL-18|SIGA-REAL-19|SIGA-REAL-20) ;;
  *)
    echo "tarefa desconhecida neste conjunto: $TASK" >&2
    exit 2 ;;
esac

# shellcheck disable=SC2086
"$JAVAC" -nowarn -cp "$DEPS" -d "$BUILD/classes" $SRCS || exit $?
CLASS="$(basename "$PRIVATE_JAVA" .java)"
"$JAVAC" -nowarn -cp "$BUILD/classes:$DEPS" -d "$BUILD/classes" "$PRIVATE_JAVA" || exit $?
"$JAVA" -cp "$BUILD/classes:$DEPS" "$CLASS"
