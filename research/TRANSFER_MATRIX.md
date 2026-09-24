# Matriz de capacidades — P6 (síntese, sem medição nova)

Data: 2026-09-24. ID: P6-matrix. Síntese de evidências já commitadas
(`TRANSFER_TARGETS/PINS/BUILDS`, `transfer/BASELINE`, `probes_001`, `edit_tasks_dev`);
nenhum número novo, nenhuma conclusão além das fontes.

## Por alvo (fontes entre parênteses)

| dimensão | T1 cucumber-jvm @ `ae2ceeb5` | T2 pytest @ `87211735` |
|---|---|---|
| PIN + censo | 1074 arqs, 842 Java, LOC 68871 (`PINS`) | 716 arqs, 274 py, LOC 116157 (`PINS`) |
| build local | `mvn -q -DskipTests compile` exit 0, 2143 classes; `mvn test` 3362 passed (`BUILDS`) | venv+`.[dev]`: 4634 passed/49 skipped/13 xfailed (`BUILDS`) |
| índice | 846 arqs, 3411 simb (regex), verify 300/300 (`BASELINE`) | 274 arqs, 7328 simb (AST), verify 300/300 (`BASELINE`) |
| sondas dev (10) | LEX 0.90 / CÁPSULA 0.90 (`probes_001`) | LEX 0.80 / CÁPSULA 1.00 (`probes_001`) |
| tarefas dev | 3 definidas, testes existem (`edit_tasks_dev`) | 3 definidas, testes existem (`edit_tasks_dev`) |

## Nível por linguagem (declarado)

Java e Python: estrutural (regex/AST + nome-na-linha, verify total nas amostras).
Demais extensões (`.feature/.md/.rst/.yml`): fora do `EXT_MAP`, sem cobertura —
lacuna que limita T1 (70 `.feature`) mais que T2.

## Lacunas que impedem qualquer alegação de transferência

Ambiguidade de nomes sem desambiguação (T1-005); payload > budget (P2);
6 tarefas dev sem execução (modelos/teto/custodiante nulos); n=10+10 sondas;
2 projetos ≠ generalização. Pronto para execução quando desbloqueado; nada provado.
