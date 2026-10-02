# Curadoria piloto SIGA 05–08 — EXP02

Data: 2026-10-02. Dono: agente A. Estado: **4 tarefas piloto validadas
(vermelho na base, verde em referência sob custódia), projeção `atlas-tasks/2`
publicada sem ouro, `eval.py validate` limpo e balanceado, checkpoint disponível
para B**.

Conjunto: [`benchmarks/siga/rust/pilot.tasks.json`](../../../benchmarks/siga/rust/pilot.tasks.json)
(`sha256:fae1032d…42f58ab850`). Aceites: [`benchmarks/siga/rust/acceptance/`](../../../benchmarks/siga/rust/acceptance/)
(runner `run-pilot.sh`; o `run.sh` do smoke A03 segue congelado).
Evidências sanitizadas: `experiments/rust/siga/2026-10-02-exp02-pilot-validation/`.

## 1. Revisão por tarefa (curador)

| Tarefa | Revisão | Baseline (base `e3be22828`) | Referência (custódia) | Regressões |
|---|---|---|---|---|
| SIGA-REAL-05 (bug_local, siga-conjuntos) | Defeito reproduzido: todas as operações copiam para conjunto ordenado, que exige `Comparable`; qualquer elemento com só `equals`/`hashCode` gera `ClassCastException`. Referência: conjunto por hash, sem tocar nas entradas, sem prometer ordem. | 3/10, exit 1 | 10/10, exit 0 | Sem teste legado para `SetUtils`; subconjunto/superconjunto e vazios passam dos dois lados |
| SIGA-REAL-06 (entre_arquivos, siga-freemarker) | Defeito reproduzido em dois pontos do round-trip: barras invertidas somem na volta do HTML (substituição interpreta `\` e `$`) e aspa escapada junto ao fechamento estoura o marcador (`StringIndexOutOfBoundsException`). Referência: volta tratada como texto literal; barra escapa o próximo char dentro de strings. | 5/10, exit 1 | 10/10, exit 0 | Casos do `IndentTest` já suportados (marcador simples, `convertFtl2Html` open/close/selfcontained, round-trip simples) preservados no harness; indentador completo (tidy) fora do escopo |
| SIGA-REAL-07 (testes_comportamento_de_api, siga-data-localidade) | Requisito proposto: 27→AA, 28→AB, 52→AZ, 53→BA, 703→AAA (numeração sequencial, sem limite em Z); `<1` inválido; `String` inválida conserva o parsing atual. Data por extenso intocada. | 4/12, exit 1 | 12/12, exit 0 | Faixa 1–26 e `NumberFormatException` passam dos dois lados; overloads concordam antes e depois |
| SIGA-REAL-08 (configuracao_interface, siga-prop) | Requisito proposto: só `dd/MM/yyyy` com a entrada inteira consumida e sem normalização silenciosa (dia/mês inexistente, sufixo, ano curto, branco e formato trocado rejeitados com o mesmo tipo e mensagem da API); ausente conserva 31/12/2099. Demais getters intocados. | 5/9, exit 1 | 9/9, exit 0 | Bissexto válido, data máxima e default passam dos dois lados |

Casos privados do avaliador (9, em custódia): vermelhos 2/9 na base, verdes 9/9
na referência. Contagens publicadas, casos não.

Método (igual nos 4, mesmo da A03): cópia isolada no SHA fixado, harness `javac`
dedicado por tarefa (exit ≠ 0 em qualquer falha), baseline na base, verde na
referência, re-verificação de que a referência não quebra os casos legados. O
patch de referência **não** é critério de igualdade textual: a rubrica julga
comportamento.

## 2. Isolamento — além de separação de diretórios

1. **Custódia fora do repo.** Soluções e casos privados vivem no mesmo diretório
   de custódia da A03, fora de `git rev-parse --show-toplevel`, nunca `git add`ed.
2. **Pacote público sem ouro.** `grep` por identificadores exclusivos da referência
   e pelos nomes dos casos privados em `benchmarks/siga/`,
   `experiments/.../exp02-pilot-validation/` e neste documento: zero ocorrências.
   O conjunto não tem campo de curadoria e publica só hashes.
3. **Executor não alcança o ouro pelo instrumento.** `test_command` referencia só
   `atlas-accept/run-pilot.sh <ID>` (relativo ao workspace, sem caminho de
   custódia). O runner recusa ouro dentro do workspace (`gold_isolation.level`
   declarado como checagem por caminho, insuficiente para R5).
4. **Teste imutável.** `atlas-accept/**` está em `immutable_paths` das 4 tarefas:
   patch que toque o aceite reprova em M5 antes de qualquer revisão. O avaliador
   instala `atlas-accept/` antes do patch; o executor nunca escreve ali.

## 3. Contaminação

Código upstream público → risco `medio` nas 4. Nenhum item nem variante das
famílias `siga-conjuntos`, `siga-freemarker`, `siga-data-localidade`, `siga-prop`
pode servir de holdout. Proibido pesquisar solução upstream durante as tentativas.

Nota de família: `siga-data-localidade` (07) e `siga-prop` (08) repetem famílias
do smoke (02 e 04) com requisitos disjuntos (letras de via vs. localidade;
`getData` estrito vs. `getList` normalizada). Se essas famílias forem usadas para
ajustar política, excluí-las do piloto de inferência e buscar substitutos
(EXP02, restrição de famílias).

## 4. Checkpoint para B

[`benchmarks/siga/rust/pilot-checkpoint.json`](../../../benchmarks/siga/rust/pilot-checkpoint.json):
SHAs do conjunto, aceites, manifestos e docs. Sem ouro. B consome por SHA conforme
o protocolo paralelo; nenhum agente escreve na worktree do outro.

EXP02 completa (16 por trilha) continua aberta: faltam 8 tarefas SIGA além das
8 validadas (smoke 01–04 + piloto 05–08), com a mesma prova de
baseline/referência e análise de famílias antes de selar.
