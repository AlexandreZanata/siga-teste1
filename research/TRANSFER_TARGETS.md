# Alvos de transferência — P6-prep (seleção pré-teste, sem execução)

Data: 2026-09-24. ID: P6-prep. Depende de P5-prep (selável, não selado).
Estado: candidatos selecionados; nada clonado, buildado ou medido.
Critério (plano §8/P6): 2+ repos externos ao SIGA, builds reproduzíveis, tarefas
independentes — um em linguagem suportada, outro em stack distinta com demanda real;
nunca só o próprio ArchAtlas; Bitcoin é dataset de desenvolvimento (fora, por §9).

## T1 — Java/Maven (linguagem suportada): `cucumber/cucumber-jvm`

Verificado via web em 2026-09-24 (metadados GitHub): Java 98.5%, licença MIT,
branch `main`, push 2026-06-10, release v7.34.3 (2026-03-04), 270 contribuidores;
build Maven (workflow `release-mvn.yaml`, publicação Maven Central) e suíte própria
extensa (framework de testes — tarefas de localização/impacto plausíveis).
 Motivo: Java real com testes, fora do SIGA; regex + verificação nome-na-linha aplicam-se.
 Dívida de verificação (P6-exec): clone isolado, SHA pinado, `mvn -q -DskipTests
 compile` local, famílias de tarefas independentes. Nada afirmado sobre build local.

## T2 — Python (stack distinta, demanda real): `pytest-dev/pytest`

Verificado via web em 2026-09-24: Python, licença MIT, branch `main`, 14k stars,
releases até 9.1.1 (2026-06-19), suíte própria em `testing/` (auto-hospedada).
Demanda real: a trilha ArchAtlas executa sua suíte sobre pytest
(`pyproject.toml: pytest>=8` — fato local, não alegação externa).
 Motivo: stack distinta do SIGA com extrator Python existente (F12); mede H5 por linguagem.
 Dívida de verificação (P6-exec): clone isolado, SHA pinado, `python -m pytest testing/ -q`
 local, tarefas independentes. Nada afirmado sobre build local.

## Rejeitados (com motivo, sem reabertura silenciosa)

- `jenkins-docs/simple-java-maven-app`: toy (hello world + 2 testes) — sem tarefas reais.
- `hibernate/hibernate-orm`: Gradle (não Maven) — divergência de build adiada; backup.
- `dweidle/copilot-agentic-playground`: 0 stars, testes exigem Docker — manutenção incerta.
- Próprio ArchAtlas: proibido como única validação externa (plano §8).
- Bitcoin Core: dataset de desenvolvimento da trilha B — não conta como transferência.

## Anti-vazamento e próximos passos

Nenhuma tarefa definida, nenhum holdout tocado, nenhum resultado — seleção precede
medição. Em P6-exec: pinar SHAs, adaptar fixtures/dev próprios sem olhar tarefas finais,
distinguir suporte lexical de estrutural por linguagem, publicar matriz de capacidades
e catálogo de falhas por projeto. Sem conclusão de generalização com 2 projetos.
