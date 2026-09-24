# 06 — Análise SIGA / SIGA-Doc

**Status:** DRAFT 2026-09-24. Nenhuma contagem afirmada sem medição — tudo não medido marcado `A MEDIR (P0)`.

## 1. Onde vive o SIGA-Doc
Não é 1 diretório: núcleo `siga-ex` (expedientes/processos/dossiês, tramitação, assinatura, e-Arq) + dependências duras `siga-cp` (identidade: pessoas/lotações/permissões), `siga-base` (transversal), `siga-wf`/`sigawf` (workflow/estados), `siga-ws` (fachadas WS), legado `sigaex` (aliases/duplicados), `siga` (web), `siga-rel` (relatórios), `siga-ext`, `siga-arq`, `siga-jwt/oidc/ldap/integracao`. Escopo inicial: `siga-ex + siga-cp + siga-base`; P0b adiciona `siga-ws` + `siga-wf/sigawf`; `sigagc/sigasr/sigatp` só como alvos de impacto.
Confirmar em P0: `git rev-parse HEAD` + POMs (`<modules>`, `<dependency>` inter-módulos) + classificação núcleo-dura/adjacente/fora.

## 2. Build/testes/dependências
Maven multi-módulo Java 8 (`source/target 1.8`), `siga-doc 11.5-SNAPSHOT patch 8`; Hibernate 5.3.7 + Spring 4.0.6 + VRaptor 4.2.2 + Wildfly/JBoss EAP + JSP/JSTL + Freemarker + Lucene 3.6.2 + JasperReports/POI + Flyway; `skipTests=true` (cobertura de execução esparsa — mapear testes por convenção+refs, nunca alegar passagem). Congelar `SHA + mvn -v + java -version` por rodada.

## 3. Pontos de entrada (hipóteses a validar em P0)
Controllers VRaptor → serviços (`*Service/*BL`) → DAOs/Hibernate (entidades, HQL/Criteria, `*.hbm.xml`) → JSPs/tags/fragmentos (+actions/forms) → fachadas `siga-ws` → fluxos `siga-wf` → identidade `siga-cp`. Critério P0: 3–5 caminhos reais por categoria registrados; sem isso, sem GT de entrada.

## 4. Desafios p/ indexador
D1 JSP/tags/EL fora do AST Java → parser JSP léxico + EL como ref fraca heuristic. D2 Reflexão/DI (Spring/VRaptor/JBoss) → resolvedor de beans, provenance `config|heuristic`. D3 Classpath parcial → incluir `siga-cp+siga-base`, registrar `unresolved_rate`. D4 Lucene embutido ≠ índice Atlas → excluir dirs de índice do produto; queries em strings = `text-match`. D5 Legado `sigaex` duplicado + `skipTests` → alias explícito legacy, teste por convenção com confidence. D6 HQL/Criteria → aresta `data_access` separada de `calls`. D7 Descritores JBoss/JNDI → nós `docs/config` com budget próprio. Tudo com `provenance+score`; sem provenance não entra na cápsula.

## 5. Escala — A MEDIR em P0
Tabela a preencher (`*.java`, LOC via cloc/wc, `*.jsp/*.tag`, `*.xml`, `*Test.java`) por `siga-ex/siga-cp/siga-base/siga-ws/siga-wf`. Comandos canônicos com saída integral no artifact P0. Budgets 500–32k só se calibram após medição. Parada: se `unresolved_rate` não cair com `siga-base`, registrar limitação em vez de forçar heurística silenciosa.
