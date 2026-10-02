#!/bin/bash
# Aceite imutavel do avaliador — conjunto piloto SIGA 05-08 (EXP02).
#
# Instalacao (workspace do AVALIADOR, nunca do executor): copiar o diretorio
# `benchmarks/siga/rust/acceptance/` deste repo para `<acceptance-repo>/atlas-accept/`
# numa base limpa no `base_sha` da tarefa, ANTES de aplicar o patch candidato.
# O executor nunca escreve em `atlas-accept/` (ver `immutable_paths`).
#
# Uso (cwd = raiz do acceptance-repo, que e um checkout do dataset SIGA):
#   bash atlas-accept/run-pilot.sh SIGA-REAL-05
#
# O que faz: compila as fontes do workspace + harness com `javac` e executa.
# Qualquer caso FAIL ou excecao => exit != 0. Sem Maven/JUnit/rede.
# Deps (commons-lang, jakarta.inject, jcabi-manifests e, so para 06, jsoup
# 1.15.3 pinado em siga-base/pom.xml) resolvidas do repositorio Maven local;
# se ausentes, sai com codigo 3 = BLOQUEIO DE AMBIENTE (nunca falha do agente,
# nunca sucesso silencioso).
#
# Nota: `run.sh` (smoke 01-04, TASK-A03) esta congelado como evidencia da A03
# e nao atende 05-08; este script e o runner do piloto.
set -u
TASK="${1:?uso: bash atlas-accept/run-pilot.sh SIGA-REAL-0X}"
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
FM="$WORK/siga/src/main/java"
case "$TASK" in
  SIGA-REAL-05)
    SRCS="$BASE/br/gov/jfrj/siga/base/util/SetUtils.java"
    HARNESS="AtlasAccept05" ;;
  SIGA-REAL-06)
    JSOUP="$M2/org/jsoup/jsoup/1.15.3/jsoup-1.15.3.jar"
    if [ ! -f "$JSOUP" ]; then
      echo "ATLAS-ENV-BLOCK: dependencia ausente: $JSOUP (versao pinada em siga-base/pom.xml)" >&2
      exit 3
    fi
    DEPS="$DEPS:$JSOUP"
    SRCS="$FM/br/gov/jfrj/siga/util/FreemarkerMarker.java $FM/br/gov/jfrj/siga/util/FreemarkerIndent.java"
    HARNESS="AtlasAccept06" ;;
  SIGA-REAL-07)
    SRCS="$BASE/br/gov/jfrj/siga/base/util/Texto.java $EX/br/gov/jfrj/siga/ex/util/DocumentoUtil.java"
    HARNESS="AtlasAccept07" ;;
  SIGA-REAL-08)
    SRCS="$BASE/br/gov/jfrj/siga/base/Prop.java $BASE/br/gov/jfrj/siga/base/AplicacaoException.java $BASE/br/gov/jfrj/siga/base/SigaVersion.java $BASE/br/gov/jfrj/siga/model/enm/NivelDaConta.java"
    HARNESS="AtlasAccept08" ;;
  *)
    echo "tarefa desconhecida neste conjunto: $TASK" >&2
    exit 2 ;;
esac

# shellcheck disable=SC2086
"$JAVAC" -nowarn -cp "$DEPS" -d "$BUILD/classes" $SRCS || exit $?
"$JAVAC" -nowarn -cp "$BUILD/classes:$DEPS" -d "$BUILD/classes" "$HERE/$HARNESS.java" || exit $?
"$JAVA" -cp "$BUILD/classes:$DEPS" "$HARNESS"
