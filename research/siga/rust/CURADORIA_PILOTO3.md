# Curadoria piloto SIGA 17–20 — NEXT-02 (terceiro lote)

Data: 2026-10-05. Dono: agente A. Estado: **4 tarefas piloto validadas
(vermelho na base, verde em referência sob custódia), projeção `atlas-tasks/2`
publicada sem ouro, `eval.py validate` limpo e balanceado 1/1/1/1, checkpoint
disponível para B**.

Conjunto: [`benchmarks/siga/rust/pilot3.tasks.json`](../../../benchmarks/siga/rust/pilot3.tasks.json)
(`sha256:a45cc7164f03…`). Aceites: [`benchmarks/siga/rust/acceptance/`](../../../benchmarks/siga/rust/acceptance/)
(runner `run-pilot3.sh`; `run.sh`, `run-pilot.sh` e `run-pilot2.sh` seguem
congelados). Evidências sanitizadas:
`experiments/rust/siga/2026-10-05-exp02-pilot3-validation/`.

Somado aos lotes anteriores, o piloto corrigido
[`piloto16.tasks.json`](../../../benchmarks/siga/rust/piloto16.tasks.json)
soma **16 tarefas exclusivamente piloto (05–20), 4/4/4/4 por categoria**, com
IDs sem sobreposição com o smoke (01–04). O inventário selado antigo
(`pilot16.tasks.json`, 4 smoke + 12 piloto) fica preservado como histórico.

## 1. Revisão por tarefa (curador)

| Tarefa | Revisão | Baseline (base `e3be22828`) | Referência (custódia) | Regressões |
|---|---|---|---|---|
| SIGA-REAL-17 (bug_local, siga-acao) | Defeito reproduzido: `getUrl` monta `(nome=valor&)` à frente do acumulado — ordem invertida e `&` sobrando (`ns/act?b=2&a=1&`). Referência: query na ordem de iteração, `?` só com parâmetros; URL explícita intacta. | 3/8, exit 1 | 8/8, exit 0 | Mapa vazio/nulo (sem `?`) e URL explícita passam dos dois lados |
| SIGA-REAL-18 (entre_arquivos, siga-acao) | Efeito colateral reproduzido: `getAcoesOrdenadasPorNome` ordena a lista viva via `AcaoVO.ordena` — o "getter" reordena o VO. Referência: ordena cópia; contrato (permitidas primeiro, nome ignorando `_`, estável) preservado pela cadeia VO→AcaoVO. | 6/9, exit 1 | 9/9, exit 0 | Ordenação, empate por `_` e VO vazio passam dos dois lados |
| SIGA-REAL-19 (testes_comportamento_de_api, siga-lista-virgula) | Defeito reproduzido: `stringsSeparadarComVirgulaEE` consome a lista (`get(0)` + `remove`) — a renderização sai certa e a entrada volta vazia. Referência: itera por índice; mesma renderização, entrada intacta; vazia continua `null`. | 6/10, exit 1 | 10/10, exit 0 | Todas as renderizações e o `null` do vazio passam dos dois lados |
| SIGA-REAL-20 (configuracao_interface, siga-acentos-html) | Defeito reproduzido: `&agrave;` virava `à` (acento restante) enquanto as onze irmãs voltam ASCII puro. Referência: `&agrave;` → `a`; fora da tabela passa intacto, `null` continua `null`. | 12/14, exit 1 | 14/14, exit 0 | Onze irmãs, passthrough e `null` passam dos dois lados |

Casos privados do avaliador (11, em custódia, `PrivateExtraPilot3`): vermelhos 6/11
na base, verdes 11/11 na referência. Contagens publicadas, casos não.

Método (igual aos lotes anteriores): clones isolados no SHA fixado (árvore
verificada limpa em `e3be22828`), harness `javac` dedicado por tarefa (exit ≠ 0
em qualquer falha), baseline na base, verde só com a referência aplicada,
re-verificação de regressões. A referência de 19 não toca no `null` do vazio;
a de 17 não toca no passthrough de URL explícita. O patch de referência **não**
é critério de igualdade textual: a rubrica julga comportamento.

## 2. Classificação entre_arquivos de 18 — dependência comportamental

18 testa a cadeia `VO.getAcoesOrdenadasPorNome` → `AcaoVO.ordena` →
`Collections.sort`: a ordenação só existe através da chamada entre os dois
arquivos, e o defeito (mutação da lista viva) só se observa através dela. O
agente precisa ler os dois componentes para corrigir sem quebrar o contrato de
ordenação — e as regressões cobrem os dois lados (ordenada + interna). Não é
contagem de arquivos: é a chamada que está sob teste.

## 3. Isolamento — além de separação de diretórios

1. **Custódia fora do repo.** Soluções (`reference/SIGA-REAL-17–20`) e casos
   privados (`acceptance-private/PrivateExtraPilot3.java`) no diretório de
   custódia dos lotes anteriores, fora de `git rev-parse --show-toplevel`.
2. **Pacote público sem ouro.** `grep` pelo nome do harness privado, pelo caminho
   da custódia e por conteúdo das referências em `benchmarks/siga/`,
   `experiments/.../exp02-pilot3-validation/` e neste documento: só o nome do
   harness em notas de manifesto (como nos lotes anteriores; casos não
   publicados). O conjunto não tem campo de curadoria e publica só hashes.
3. **Executor não alcança o ouro pelo instrumento.** `test_command` referencia só
   `atlas-accept/run-pilot3.sh <ID>` (relativo ao workspace, sem caminho de
   custódia). Nível declarado: checagem por caminho, insuficiente para R5.
4. **Teste imutável.** `atlas-accept/**` está em `immutable_paths` das 4 tarefas.

## 4. Contaminação e famílias

Código upstream público → risco `medio` nas 4. Famílias novas
(`siga-acao`, `siga-lista-virgula`, `siga-acentos-html`) sem sobreposição com o
smoke (`siga-texto`, `siga-data-localidade`, `siga-cpf`, `siga-prop`); 17/18
compartilham família e arquivos com defeitos e trechos disjuntos (precedente
dos lotes: `Utils.java` em 09/10/12). Texto.java agora serve 16/19/20, também
com trechos disjuntos. Nenhum item nem variante destas famílias pode servir de
holdout. Proibido pesquisar solução upstream durante as tentativas.

**Decisão de exclusão (antes de observar resultados de modelos):** nenhuma
exclusão necessária agora — o smoke ainda não afinou política (nenhum modelo
rodou) e as famílias novas não colidem com ele. Se o smoke afinar política, as
famílias `siga-data-localidade` e `siga-prop` saem do piloto de inferência e
buscam-se substitutos.

## 5. Escopo medido

12 tarefas de utilitário isolado + 4 integrações entre componentes (06, 11, 12,
18); 100% Java, `javac` sem container. Conclusões restritas a esse escopo: sem
backend web, sem banco, sem outras linguagens. Aceite medido 0,7–1,1 s por
tarefa neste lote.

## 6. Checkpoint para B

[`benchmarks/siga/rust/pilot3-checkpoint.json`](../../../benchmarks/siga/rust/pilot3-checkpoint.json):
SHAs do lote, do piloto corrigido, dos aceites, do selo, manifestos e docs. Sem
ouro. B consome por SHA conforme o protocolo paralelo; nenhum agente escreve na
worktree do outro.
