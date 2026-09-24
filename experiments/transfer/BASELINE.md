# Linha de base de capacidades — P6-exec (c) (fixtures dev, sem tarefas)

Data: 2026-09-24. ID: P6-exec-c. Indexação só-leitura dos clones PIN
(`store.index_discovered` + `rebuild_lexical`); DBs em `/tmp` (nunca commitados).
Sem tarefas, sem holdout, sem conclusão de transferência.

## Medições (reais)

| alvo | arqs indexados | símbolos | verify 300/300 | tempo | DB |
|---|---|---|---|---|---|
| T1 cucumber | 846 (java 842, js 4) | 3411 (método 2562, classe 686, iface 145, enum 18; regex) | ok | 1.6s | 2220KB |
| T2 pytest | 274 (python 274) | 7328 (função 6527, classe 801; AST-exato) | ok | 1.38s | 2856KB |

`stable_hash`: T1 `e92cd4960554`, T2 `01da2e367bc8` (replay: mesmo corpus+extrator).
Censo total vs indexado: T1 1074→846 e T2 716→274 porque `discover` só inclui
extensões de `EXT_MAP` (`.feature/.md/.xml/.rst/.yml` ficam de fora do índice —
lacuna declarada, sem fallback silencioso).

## Matriz de capacidades (declarada, não prometida além do medido)

| linguagem | nível | evidência |
|---|---|---|
| Java | estrutural (regex auditado + nome-na-linha) | 3411 símbolos, verify 300/300; smoke `Glue`→`Glue.java:16` ok, `Plugin`→`Plugin.java:39` ok |
| Python | estrutural (AST + nome-na-linha) | 7328 símbolos, verify 300/300; smoke `fixture`→`fixtures.py:4129` ok, `mark`→`structures.py:264` ok |
| demais (feature/md/rst/…) | sem cobertura de índice | fora do `EXT_MAP`; fallback lexical só onde houver extrator |

## Decisão e dívida

Base `manter` para fixtures dev P6 (indexação rápida, verificação total na amostra).
Dívida: fixtures dev próprias por alvo, `mvn test` T1 (matriz maior) e matriz final
pós-tarefas. Nenhuma tarefa definida; nenhum holdout; nenhuma transferência provada.
