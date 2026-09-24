# PIN + censo dos alvos — P6-exec (a) (clones em runtime externo, sem build)

Data: 2026-09-24. ID: P6-exec-a. Clones somente leitura em `/tmp/opencode-p6/`
(nunca commitados; blobs de terceiros fora do repo — só ponteiros+hashes).
`status` limpo nos dois; nenhum build executado (próxima fatia).

## T1 — `cucumber/cucumber-jvm`

- Origem: `https://github.com/cucumber/cucumber-jvm`, branch `main`.
- SHA pinado: `ae2ceeb5a79f9459f54ecaa9f4b2f8e095a2277b` (HEAD em 2026-09-24).
- Licença observada: `LICENSE` presente (MIT, cf. seleção).
- Build: `pom.xml` + `mvnw` presentes (Maven confirmado no checkout).
- Censo medido (`rglob`, sem `.git`): 1074 arquivos — `.java` 842, `.feature` 70,
  `.md` 43, `.xml` 32, `.properties` 20; LOC Java 68871 (soma binária, sem parse).

## T2 — `pytest-dev/pytest`

- Origem: `https://github.com/pytest-dev/pytest`, branch `main`.
- SHA pinado: `8721173580390a9d297e5af06cac3f0b6841f425` (HEAD em 2026-09-24).
- Licença observada: `LICENSE` presente (MIT, cf. seleção).
- Build: `pyproject.toml` presente, `setup.py` ausente (build moderno; `testing/` é a suíte).
- Censo medido (`rglob`, sem `.git`): 716 arquivos — `.rst` 353, `.py` 274, `.yml` 14;
  LOC Python 116157 (soma binária, sem parse).

## Dívida restante (P6-exec-b/c, sem reabertura silenciosa)

Build local (`mvn -q -DskipTests compile` / `pytest testing/ -q`), fixtures dev próprias
sem olhar tarefas finais, distinção lexical-vs-estrutural por linguagem e matriz de
capacidades. Nenhuma tarefa definida; nenhum holdout; nenhuma conclusão de transferência.
