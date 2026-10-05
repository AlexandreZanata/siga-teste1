#!/bin/bash
# Aceite imutavel do avaliador — terceiro lote piloto SIGA 17-20 (NEXT-02).
#
# Instalacao (workspace do AVALIADOR, nunca do executor): copiar o diretorio
# `benchmarks/siga/rust/acceptance/` deste repo para `<acceptance-repo>/atlas-accept/`
# numa base limpa no `base_sha` da tarefa, ANTES de aplicar o patch candidato.
# O executor nunca escreve em `atlas-accept/` (ver `immutable_paths`).
#
# Uso (cwd = raiz do acceptance-repo, que e um checkout do dataset SIGA):
#   bash atlas-accept/run-pilot3.sh SIGA-REAL-17
#
# O que faz: compila as fontes do workspace + harness com `javac` e executa.
# Qualquer caso FAIL ou excecao => exit != 0. Sem Maven/JUnit/rede.
# Deps resolvidas do repositorio Maven local (versoes pinadas abaixo; ausente
# => exit 3 = BLOQUEIO DE AMBIENTE, nunca falha do agente, nunca sucesso
# silencioso). jlogic 1.1.1 e a versao pinada em siga/pom.xml e atende
# AcaoVO.formatarExplicacao; os demais jars atendem Utils.java como no lote 2.
#
# Nota: `run.sh` (smoke 01-04), `run-pilot.sh` (05-08) e `run-pilot2.sh` (09-16)
# seguem congelados como evidencia; este script e o runner do terceiro lote.
set -u
TASK="${1:?uso: bash atlas-accept/run-pilot3.sh SIGA-REAL-1X}"
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

need_jars() {
  for j in "$@"; do
    if [ ! -f "$j" ]; then
      echo "ATLAS-ENV-BLOCK: dependencia ausente: $j (rede Maven ou aquecimento do repo local)" >&2
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

BASE="$WORK/siga-base/src/main/java"
UTILS_SRCS="$BASE/br/gov/jfrj/siga/base/util/Utils.java $BASE/br/gov/jfrj/siga/base/util/Texto.java $BASE/br/gov/jfrj/siga/base/GZip.java $BASE/br/gov/jfrj/siga/model/Historico.java $BASE/br/gov/jfrj/siga/model/Assemelhavel.java"
case "$TASK" in
  SIGA-REAL-17|SIGA-REAL-18)
    need_jars \
      "$M2/jakarta/servlet/jakarta.servlet-api/6.0.0/jakarta.servlet-api-6.0.0.jar" \
      "$M2/org/apache/commons/commons-text/1.9/commons-text-1.9.jar" \
      "$M2/org/apache/commons/commons-lang3/3.20.0/commons-lang3-3.20.0.jar" \
      "$M2/jakarta/persistence/jakarta.persistence-api/3.1.0/jakarta.persistence-api-3.1.0.jar" \
      "$M2/com/crivano/jlogic/1.1.1/jlogic-1.1.1.jar"
    SRCS="$UTILS_SRCS $BASE/br/gov/jfrj/siga/base/AcaoVO.java $BASE/br/gov/jfrj/siga/base/VO.java"
    case "$TASK" in
      SIGA-REAL-17) HARNESS="AtlasAccept17" ;;
      SIGA-REAL-18) HARNESS="AtlasAccept18" ;;
    esac ;;
  SIGA-REAL-19|SIGA-REAL-20)
    SRCS="$BASE/br/gov/jfrj/siga/base/util/Texto.java"
    case "$TASK" in
      SIGA-REAL-19) HARNESS="AtlasAccept19" ;;
      SIGA-REAL-20) HARNESS="AtlasAccept20" ;;
    esac ;;
  *)
    echo "tarefa desconhecida neste conjunto: $TASK" >&2
    exit 2 ;;
esac

# shellcheck disable=SC2086
"$JAVAC" -nowarn -cp "$DEPS" -d "$BUILD/classes" $SRCS || exit $?
"$JAVAC" -nowarn -cp "$BUILD/classes:$DEPS" -d "$BUILD/classes" "$HERE/$HARNESS.java" || exit $?
"$JAVA" -cp "$BUILD/classes:$DEPS" "$HARNESS"
