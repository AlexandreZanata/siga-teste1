# Curadoria smoke SIGA — TASK-A03

Data: 2026-10-02. Dono: agente A. Estado: **4 tarefas smoke validadas
(vermelho na base, verde em referência sob custódia), projeção `atlas-tasks/2`
publicada sem ouro, `eval.py validate` limpo, checkpoint disponível para B**.

Conjunto: [`benchmarks/siga/rust/smoke.tasks.json`](../../../benchmarks/siga/rust/smoke.tasks.json)
(`sha256:ffb9dd8b…5e820`). Aceites: [`benchmarks/siga/rust/acceptance/`](../../../benchmarks/siga/rust/acceptance/).
Evidências sanitizadas: `experiments/rust/siga/2026-10-02-a03-validation/`.

## 1. Revisão por tarefa (curador)

| Tarefa | Revisão | Baseline (base `e3be22828`) | Referência (custódia) | Regressões |
|---|---|---|---|---|
| SIGA-REAL-01 (bug_local, siga-texto) | Defeito reproduzido: `indexOf(sEnd)` a partir de 0; fechamento anterior gera `StringIndexOutOfBoundsException` ou resultado errado. Referência: `indexOf(sEnd, iBegin+len)`. | 5/6, exit 1 | 6/6, exit 0 | Nenhum teste legado cobre `extrai`; casos adjacentes/simples preservados no harness |
| SIGA-REAL-02 (entre_arquivos, siga-data-localidade) | Requisito proposto: `trim()` da localidade antes de separar UF; resto do algoritmo intacto (lista UF, `maiusculasEMinusculas`, `Locale pt-BR` explícito, `null→null`). | 4/6, exit 1 | 6/6, exit 0 | `DocumentoUtilTest` (1 método, 8 asserts) preservado: harness inclui 2 casos legados, verdes nos dois lados |
| SIGA-REAL-03 (testes_comportamento_de_api, siga-cpf) | Requisito proposto: só 11 dígitos ASCII (`[0-9]`, sem `StringUtils.isNumeric` que aceita não-ASCII) ou máscara exata `[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}`; resto (nulo/branco, `Long` com zeros) preservado. Sem dígito verificador. | 8/10, exit 1 | 10/10, exit 0 | `CPFUtilsTest` (7 testes) preservado via perfil `atlas-eval` da A01 e por construção (mensagens/tipos de exceção mantidos) |
| SIGA-REAL-04 (configuracao_interface, siga-prop) | Requisito proposto: `trim()` por entrada + descarta vazias, ordem e duplicatas mantidas, `null` se ausente; demais getters intocados. | 3/6, exit 1 | 6/6, exit 0 | Sem teste legado para `getList`; `getInt`/`getData` não tocados (diff só em `getList` + import) |

Casos privados do avaliador (7, em custódia): vermelhos 3/7 na base (discriminam:
UF com tab/newline, 14 dígitos sem máscara, vazios internos de lista), verdes 7/7
na referência. Contagens publicadas, casos não.

Método (igual nos 4): cópia isolada no SHA fixado, harness `javac` dedicado por
tarefa (exit ≠ 0 em qualquer falha), baseline na base, verde na referência,
re-verificação de que a referência não quebra os casos legados. O patch de
referência **não** é critério de igualdade textual: a rubrica julga comportamento.

## 2. Isolamento — além de separação de diretórios

1. **Custódia fora do repo.** Soluções e casos privados vivem em diretório fora de
   `git rev-parse --show-toplevel`, nunca `git add`ed (`git ls-files` não contém
   nomes de auxiliares da referência, da classe privada e da custódia`; `git status` só mostra os paths públicos novos).
2. **Pacote público sem ouro.** `grep` por identificadores exclusivos da referência
   (nomes de auxiliares e da classe privada, nomes de casos privados, caminho da
   custódia) em `benchmarks/siga/`, `experiments/.../a03-validation/` e neste
   documento: zero ocorrências — inclusive este texto evita citá-los. O conjunto
   não tem campo de curadoria e publica só hashes (SHA não revela conteúdo).
3. **Executor não alcança o ouro pelo instrumento.** `test_command` referencia só
   `atlas-accept/run.sh <ID>` (relativo ao workspace, sem caminho de custódia, sem
   variável de ambiente de ouro). O runner recusa ouro dentro do workspace e nunca
   escreve o caminho no ambiente/manifesto (`gold_isolation.level` declarado como
   checagem por caminho, insuficiente para R5 — sem fingir isolamento total).
4. **Teste imutável.** `atlas-accept/**` está em `immutable_paths` das 4 tarefas:
   patch que toque o aceite reprova em M5 antes de qualquer revisão. O avaliador
   instala `atlas-accept/` antes do patch; o executor nunca escreve ali.

## 3. Contaminação

Código upstream público → risco `medio` nas 4. Nenhum item nem variante das
famílias `siga-texto`, `siga-data-localidade`, `siga-cpf`, `siga-prop` pode servir
de holdout. Proibido pesquisar solução upstream durante as tentativas.

## 4. Checkpoint para B

[`benchmarks/siga/rust/checkpoint.json`](../../../benchmarks/siga/rust/checkpoint.json):
SHAs do conjunto, aceites, manifestos e docs. Sem ouro. B consome por SHA conforme
o protocolo paralelo; nenhum agente escreve na worktree do outro.
