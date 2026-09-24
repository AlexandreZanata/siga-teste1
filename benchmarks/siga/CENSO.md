# CENSO — medido em 2026-09-24 no SHA e3be22828 (comando em `archatlas/census.py`)

| módulo | java_files | jsp/tag | java_loc |
|---|---|---|---|
| siga-ex | 510 | 0 | A MEDIR via script* |
| siga-cp | 251 | 0 | * |
| siga-base | 83 | 0 | * |
| siga-ws | 16 | 0 | * |
| siga-wf | 90 | 0 | * |
| sigawf | 81 | 37 | * |
| sigaex | 270 | 642 | * |
| siga | 124 | 108 | * |

\* `java_files`/`jsp_tag` contados via `pathlib.rglob` em disco (evidência: teste `test_census_verifies_real_files` lê os mesmos caminhos). `java_loc` é preenchido pelo script (soma de linhas binária, sem parse). JSPs vivem em `sigaex`/`siga`/`sigawf`, não em `siga-ex` — fato verificado que orienta o extrator F2 (Java em `siga-ex`, templates em `sigaex`).
Âncoras reais: `siga-ex/src/main/java/br/gov/jfrj/siga/ex/ExMovimentacao.java` (`class ExMovimentacao`), `siga-ex/.../logic/ExPodeTramitarPara.java`.
Reproduzir: `python -c "from archatlas.census import census; import json; print(json.dumps(census(), indent=1))"`.
