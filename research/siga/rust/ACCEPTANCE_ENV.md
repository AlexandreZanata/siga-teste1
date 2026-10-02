# Ambiente de aceitação SIGA — TASK-A01

Data: 2026-10-02. Dono: agente A. Estado: **aceites isolados de SIGA-REAL-01 e SIGA-REAL-05
preparados e executados na base (vermelhos); configuração imutável de avaliação Maven
comprovada com testes > 0**. Não é conjunto executável do piloto: faltam validação de
referência e curadoria (TASK-A03), e os aceites das demais tarefas.

Evidências sanitizadas (sem ouro, sem solução de referência, sem caminho de worktree
sensível): [`experiments/rust/siga/2026-10-02-a01-preflight/preflight/`](../../../experiments/rust/siga/2026-10-02-a01-preflight/preflight/).

## 1. Ambiente registrado

| Item | Valor medido nesta revisão |
|---|---|
| Dataset | checkout inspecionado `../siga`, **não modificado** (continua só com `?? .freebuff/`, `?? siga-teste/`) |
| Cópia isolada | `git worktree add --detach /tmp/siga-a01-2026-10-02 e3be22828f787cbe71b339aecb7a7bf569099803` |
| `base_sha` | `e3be22828f787cbe71b339aecb7a7bf569099803` (igual ao catálogo) |
| Fontes no SHA | `Texto.java` → `ea5716eb…f8b82e`; `SetUtils.java` → `5732f0ff…775ded` (iguais ao `curator_only`) |
| `java` padrão | 21.0.12.1 Ubuntu (`/usr/lib/jvm/java-21-openjdk-amd64`) — **JRE sem `lib/ct.sym`** |
| `javac` no PATH | Temurin 21 (`/data/dev/java/candidates/java/current/bin`) |
| Maven | 3.8.7; `JAVA_HOME=/data/dev/java/candidates/java/current` (JDK completo, exigido — ver §2) |
| Repositório local | `~/.m2/repository`, 990M aquecido; surefire 2.16 e dependências baixados nesta revisão |
| Rede | `repo.maven.apache.org` acessível (HTTP 200); downloads registrados nos logs |

## 2. Três armadilhas comprovadas (não presumidas)

**A. `skipTests=true` literal vence em silêncio.** `mvn -B -pl siga-base test` → `Tests are
skipped`, BUILD SUCCESS, exit 0. Um aceite baseado nesse comando passaria sem executar nada.

**B. `-DskipTests=false` não sobrescreve configuração literal.** `mvn -B -pl siga-base
-DskipTests=false test` → `Tests are skipped`, BUILD SUCCESS, exit 0 (log
`mvn-flag-skip-false.txt`). A propriedade só funcionaria se o pom usasse `${...}`; o pom base
fixa `true` literal. Qualquer instrução de aceite que confie nessa flag está errada.

**C. O `java` padrão do ambiente não compila com `--release` (nem 17, nem 21).** O JRE Ubuntu
não traz `lib/ct.sym`; o compilador in-process rejeita qualquer `--release`
(`mvn-compile-debug.txt`, mais o teste mínimo em `/tmp/tooltest`, já removido). Com o `java`
padrão, `mvn -pl siga-base test` falha em `compile` com `release version 21 not supported`
— antes mesmo de chegar ao Surefire. O avaliador **fixa `JAVA_HOME` para um JDK completo**;
o manifesto registra o caminho usado (`manifests/environment.json`).

**D. `src/test/br` não é fonte de teste — e não pode ser adicionada em bloco.** Os testes
legados vivem em duas árvores: `src/test/java/br` (4 arquivos, descoberta padrão) e
`src/test/br` (10 arquivos). `CPFUtilsTest` e `CorreioTest` são byte a byte idênticos nas
duas; adicionar `src/test/br` como fonte quebra a compilação com `duplicate class`. Os 8
arquivos só existentes em `src/test/br` referenciam símbolos fora do módulo
(`ModeloPropriedade`, inexistente em `siga-base`) e não compilam no build do módulo — 58
erros (log `mvn-eval-smoke-v1-falha.txt`). Tentativa feita e revertida; o perfil final não
toca em fontes de teste.

## 3. Configuração imutável de avaliação

Fragmento (propriedade do avaliador, versionado): `preflight/eval-config/atlas-eval-profile.xml`.
Aplicação no workspace do avaliador: inserir o bloco como `<profiles>` do pom do módulo sob
avaliação; o workspace é recriado por tentativa e o hash do pom aplicado consta no manifesto
da tentativa (procedimento da rodada, não deste preflight). O executor nunca edita esse arquivo.

Comprovação (módulo `siga-base`, cópia isolada):

1. `mvn -B -pl siga-base -Patlas-eval -Dtest=AtlasEvalSmokeTest test` →
   `Tests run: 1, Failures: 0, Errors: 0, Skipped: 0`, BUILD SUCCESS, exit 0
   (relatórios `TEST-*.xml` + `.txt` em `preflight/reports/`).
2. POM efetivo (`help:effective-pom`) mostra `<skipTests>false</skipTests>` no nível do plugin
   e da execução `default-test` — a configuração do perfil derrotou o literal do pom base
   (recorte em `preflight/reports/effective-pom-surefire.txt`).
3. `mvn -B -pl siga-base -Patlas-eval -Dtest=CPFUtilsTest test` →
   `Tests run: 7, Failures: 0, Errors: 0, Skipped: 0` na base: teste legado executa e passa,
   regressão preservada (relatórios em `preflight/reports/`).

## 4. Aceites por tarefa

### SIGA-REAL-01 e SIGA-REAL-05 — prontos (isolado Java)

Harness em `preflight/harness/AtlasAccept01.java` (6 casos) e `AtlasAccept05.java` (8 casos):
compilam com `javac` contra as fontes da base, sem Maven/JUnit/rede; cada caso imprime
PASS/FAIL e qualquer falha devolve exit ≠ 0. Cobrem exatamente os critérios públicos do
catálogo (01: fechamento anterior, ausências → null, adjacentes → vazio, caso simples;
05: união/interseção/diferença/simétrica por igualdade de valor, vazios, imutáveis,
entradas inalteradas).

- Baseline na base: 01 → **5/6, exit 1** (`StringIndexOutOfBoundsException` no caso exigido);
  05 → **1/8, exit 1** (7× `ClassCastException`). Logs em `preflight/logs/`.
- Validação do harness: executado contra variante corrigida **descartável em /tmp (apagada;
  nada armazenado, nenhuma solução de referência criada)**: 01 → 6/6, 05 → 8/8. A solução
  de referência curada, com preservação de regressões, pertence à TASK-A03 em custódia.

Manifestos: `preflight/manifests/SIGA-REAL-01.json`, `SIGA-REAL-05.json` (fontes+hashes,
harness+hash, casos, baseline vermelho, comandos).

### SIGA-REAL-02/03/04/06/07/08 — pendentes (módulos sem banco/servidor)

Exigem o reator Maven (`siga-base` + `siga-ex` / `siga`, conforme o cartão) com o perfil
`atlas-eval`, sem banco ou servidor. O padrão é o mesmo desta revisão: teste independente do
avaliador, baseline vermelho na base, verde em referência sob custódia, relatório Surefire
com testes > 0. `SIGA-REAL-03` (CPF) já tem o caminho pavimentado: `CPFUtilsTest` executa
pelo perfil.

## 5. Como reproduzir

```sh
git worktree add --detach /tmp/siga-a01-<data> e3be22828f787cbe71b339aecb7a7bf569099803
export JAVA_HOME=/data/dev/java/candidates/java/current   # JDK completo; ver §2-C
# Isolado Java (01/05): copiar as duas fontes + harness, javac, java; exit 1 na base.
# Maven: aplicar preflight/eval-config/atlas-eval-profile.xml ao pom do módulo,
#   mvn -B -pl <modulo> -Patlas-eval -Dtest=<Teste> test
#   e conferir TEST-*.xml (tests=..., failures=0, errors=0) + skipTests=false no POM efetivo.
```

## 6. O que isto NÃO é

- Não é conjunto executável do piloto (`runnable` continua `false` no catálogo).
- Não autoriza rodada com modelo: sem referência validada, não há o que julgar.
- Nenhuma solução de referência foi criada ou armazenada; o green-check descartável valida o
  harness, não substitui a curadoria da A03.
- Infraestrutura indisponível (rede Maven, JDK completo) é bloqueio de ambiente registrado,
  nunca falha do agente — e nunca sucesso silencioso.
