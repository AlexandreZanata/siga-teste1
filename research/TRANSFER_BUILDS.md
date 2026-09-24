# Builds locais — P6-exec (b) (cópias descartáveis; clones PIN intactos)

Data: 2026-09-24. ID: P6-exec-b. Builds em `/tmp/opencode-p6/{t1,t2}-build`
(cópias; `target/`, `.pyc`, venv fora do repo e fora dos clones PIN).
Clones `t1`/`t2` re-verificados limpos após (PINs de `TRANSFER_PINS.md` intactos).

## T2 `pytest-dev/pytest` @ `87211735` — REPRODUZÍVEL

- Ambiente: venv isolada + `pip install -e ".[dev]"` (documentado no `pyproject`;
  sem tocar no Python do host). Com pytest ambiente 9.0.3 a suíte NEM COLETA
  (13 erros: `hypothesis`/`xmlschema`/`attrs`/`setuptools` ausentes + drift de
  API interna) — registrado, não corrigido no host.
- Comando: `python -m pytest testing/ -q -p no:cacheprovider` → **4634 passed,
  49 skipped, 13 xfailed, 7 xpassed** em ~185s, +1 erro só pelo flag
  (`test_cache_makedir` exige cache; rerun com cache: **pass**).
- Veredito: build+testes reproduzíveis no env documentado; 0 falhas reais.

## T1 `cucumber/cucumber-jvm` @ `ae2ceeb5` — REPRODUZÍVEL (com Maven 3.9.9)

- Maven do sistema 3.8.7 **rejeitado** pelo enforcer (exige ≥3.9.0); sem `mvnw`
  funcional (script sem `.mvn/wrapper/*.properties`). Maven 3.9.9 via tarball
  oficial em `/tmp` (sem alterar o host).
- Comando: `mvn -q -DskipTests compile` → **exit 0**, **2143** `.class` gerados.
- Veredito: compilação reproduzível com toolchain ≥3.9.0; testes (`mvn test`)
  ficam para P6-exec-c (matriz maior, mesma trava de recursos do piloto).

## T1 testes — `mvn test` VERDE (mesma cópia, Maven 3.9.9)

Comando: `mvn test` (sem `-q`, sem skips) → **BUILD SUCCESS**: **3362 testes,
0 falhas, 0 erros, 92 skipped** (skips condicionais dos próprios módulos).
Clone PIN re-verificado limpo após (build só na cópia).

## Dívida restante

Fixtures dev próprias por alvo (sem olhar tarefas finais), distinção
lexical-vs-estrutural e matriz de capacidades em P6-exec-c. Nenhuma tarefa
definida; nenhum holdout; nenhuma conclusão de transferência.
