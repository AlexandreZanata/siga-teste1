# Curadoria piloto SIGA 09–16 — EXP02 (segundo lote)

Data: 2026-10-02. Dono: agente A. Estado: **8 tarefas piloto validadas
(vermelho na base, verde em referência sob custódia), projeção `atlas-tasks/2`
publicada sem ouro, `eval.py validate` limpo e balanceado 2/2/2/2, checkpoint
disponível para B**.

Conjunto: [`benchmarks/siga/rust/pilot2.tasks.json`](../../../benchmarks/siga/rust/pilot2.tasks.json)
(`sha256:20bc851f…cab9dce5`). Aceites: [`benchmarks/siga/rust/acceptance/`](../../../benchmarks/siga/rust/acceptance/)
(runner `run-pilot2.sh`; `run.sh` do smoke e `run-pilot.sh` do primeiro lote
seguem congelados). Evidências sanitizadas:
`experiments/rust/siga/2026-10-02-exp02-pilot2-validation/`.

Somado ao smoke (01–04) e ao primeiro lote (05–08), o SIGA soma **16 tarefas
validadas** (4/4/4/4 por categoria), completando o quantitativo da EXP02 para
a trilha. Falta só a decisão de selamento/holdout (curador do holdout, P4).

## 1. Revisão por tarefa (curador)

| Tarefa | Revisão | Baseline (base `e3be22828`) | Referência (custódia) | Regressões |
|---|---|---|---|---|
| SIGA-REAL-09 (bug_local, siga-form) | Defeito reproduzido: `split("=")` descarta pares com `=` no valor (`a=b=c`) e com valor vazio (`vazio=`). Referência: corte no primeiro `=`, par sem `=` ignorado, resto do pipeline (decode + unescape) intacto. | 6/9, exit 1 | 9/9, exit 0 | Pares simples, `+`, escapes, chave repetida e nulo passam dos dois lados |
| SIGA-REAL-10 (bug_local, siga-zeros) | Defeito reproduzido: zero é inserido antes do sinal (`-5,3` → `0-5`). Referência: sinal preservado à frente do preenchimento, com dígito seguro para o mínimo do int. | 5/8, exit 1 | 8/8, exit 0 | Positivos, zero e valores já largos passam dos dois lados |
| SIGA-REAL-11 (entre_arquivos, siga-tempo) | Defeito reproduzido: variáveis de início/fim trocadas; ordem natural zera (`00:00:00`) ou negativiza (`-2 dias`) a duração via `SigaCalendar`. Referência: duração não-negativa em qualquer ordem, singular correto; o único chamador conhecido passa os argumentos invertidos e produz os mesmos valores antes e depois. | 3/8, exit 1 | 8/8, exit 0 | Ordem invertida multi-dias e timezone fixado passam dos dois lados |
| SIGA-REAL-12 (entre_arquivos, siga-zip) | Defeito reproduzido: entrada nula/vazia estoura `NullPointerException` dentro do par `Utils`/`GZip`. Referência: rejeição explícita com `IllegalArgumentException`; gzip corrompido conserva o erro de aplicação da API. | 4/8, exit 1 | 8/8, exit 0 | Round-trip simples, multibyte, longo e base64 inválido passam dos dois lados |
| SIGA-REAL-13 (testes_comportamento_de_api, siga-data-formato) | Defeito reproduzido: o nome promete `YYYY` mas o padrão usa `yy` (`30/04/25`). Referência: ano com 4 dígitos; irmãos com ano curto no nome intocados. | 3/6, exit 1 | 6/6, exit 0 | Nulo e os dois irmãos passam dos dois lados |
| SIGA-REAL-14 (testes_comportamento_de_api, siga-moeda-extenso) | Requisito proposto: milhares exatos sem `um` (`mil reais`, `mil e cem reais`); `um milhão`, `dois mil`, centavos e junção entre grupos preservados. | 5/9, exit 1 | 9/9, exit 0 | Demais qualificadores passam dos dois lados |
| SIGA-REAL-15 (configuracao_interface, siga-formato-arquivo) | Defeito reproduzido: `String.format` sem locale emite vírgula sob pt-BR (`1,5 kB`). Referência: ponto decimal em qualquer locale; unidades, faixas e `IllegalArgumentException` de zero/negativos preservados. | 2/8, exit 1 | 8/8, exit 0 | Rejeições passam dos dois lados |
| SIGA-REAL-16 (configuracao_interface, siga-slug) | Defeito reproduzido: `toLowerCase()` com o default do processo gera `i sem pingo` sob tr (`ıtbı`). Referência: minúsculas em locale neutro; acentuação, pontuação, underscore e nulo/branco preservados. | 6/9, exit 1 | 9/9, exit 0 | Casos sem `I` passam dos dois lados |

Casos privados do avaliador (10, em custódia): vermelhos 1/10 na base, verdes
10/10 na referência. Contagens publicadas, casos não.

Método (igual aos lotes anteriores): cópia isolada no SHA fixado, harness `javac`
dedicado por tarefa (exit ≠ 0 em qualquer falha), baseline na base, verde na
referência, re-verificação de regressões. Duas tarefas do lote compartilham o
arquivo com tarefas irmãs (`Utils.java` em 09/10/12, `DateUtils.java` em 11/13),
mas com defeitos e trechos disjuntos — cada referência corrige só o seu, e cada
aceite só testa o seu. O patch de referência **não** é critério de igualdade
textual: a rubrica julga comportamento.

## 2. Isolamento — além de separação de diretórios

1. **Custódia fora do repo.** Soluções e casos privados no mesmo diretório de
   custódia dos lotes anteriores, fora de `git rev-parse --show-toplevel`.
2. **Pacote público sem ouro.** `grep` por identificadores exclusivos da referência
   e pelos nomes dos casos privados em `benchmarks/siga/`,
   `experiments/.../exp02-pilot2-validation/` e neste documento: zero ocorrências.
   O conjunto não tem campo de curadoria e publica só hashes.
3. **Executor não alcança o ouro pelo instrumento.** `test_command` referencia só
   `atlas-accept/run-pilot2.sh <ID>` (relativo ao workspace, sem caminho de
   custódia). Nível declarado: checagem por caminho, insuficiente para R5.
4. **Teste imutável.** `atlas-accept/**` está em `immutable_paths` das 8 tarefas.

## 3. Contaminação

Código upstream público → risco `medio` nas 8. Nenhum item nem variante das
famílias `siga-form`, `siga-zeros`, `siga-tempo`, `siga-zip`, `siga-data-formato`,
`siga-moeda-extenso`, `siga-formato-arquivo`, `siga-slug` pode servir de holdout.
Proibido pesquisar solução upstream durante as tentativas.

## 4. Checkpoint para B

[`benchmarks/siga/rust/pilot2-checkpoint.json`](../../../benchmarks/siga/rust/pilot2-checkpoint.json):
SHAs do conjunto, aceites, manifestos e docs. Sem ouro. B consome por SHA conforme
o protocolo paralelo; nenhum agente escreve na worktree do outro.
