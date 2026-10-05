# R2 — microbenchmarks pareados e ciclo editar/testar

Data: 2026-09-29. ID: `R2-REPORT/1`. Etapa: **R2** de [`RUST_CLI_PILOTO_REAL.md`](../../plans/RUST_CLI_PILOTO_REAL.md) §6.
Contrato implementado: [`CLI_CONTRACT/1`](CLI_CONTRACT.md) (+ esclarecimentos §8 e §10).
Base: `main` após `97a5d38` (R2, runner do piloto). Dataset: `../siga` @ `e3be22828` (read-only, não modificado).
Revisto em 2026-09-29 após a rodada de `expand` em §8.1 (Q7 fechada, Q9 aberta).
Artefatos brutos: [`experiments/rust/siga/2026-09-29-r2-queries/`](../../experiments/rust/siga/2026-09-29-r2-queries/).

## 1. O que foi entregue

Duas frentes, e a distinção entre elas importa para ler o resto do documento.

**No produto Rust** (implementação):

| Peça | O que faz |
|---|---|
| `verify --ref arquivo:linha[@hash]` | relê o disco e confirma a citação; código 5 em qualquer item reprovado |
| `expand` (`evidence_wanted` ∈ `context`/`references`/`tests`) | amplia por referência já entregue, deduplicando spans já mostrados |
| `evidence_reserve_pct` | fatia de `max_bytes` reservada à evidência de busca; barrado sai como `evidence_reserved` |
| grupos de spans por arquivo citado | um arquivo em `known_refs` contribui também com as ocorrências do termo fora da janela |
| `--include <langs>` | restringe a indexação; `excluded_by_filter` reporta o que foi descartado |
| `RefSpec.end_line` | expansão por intervalo de linhas |
| `PackError::BadRequest` | código 2 para pedido incoerente (ex.: `expand` sem `known_refs`, reserva com `context`) |

Suíte total: **80 testes verdes** em `cargo test --release` — 50 unitários + 16 de integração de contrato + 14 de R2 ([`tests/r2.rs`](../../rust/archatlas/tests/r2.rs)) que spawnam o binário real. `cargo fmt --check` limpo, `pytest -q` 76 passed / 4 skipped.

**No harness de medição** (produto de pesquisa): `freeze_corpus.py`, `gen_queries.py`, `measure.py` (sete modos: `query`, `index`, `update`, `expand`, `verify`, `scale`, `doctor`), `report.py` e um driver `run_round.py` que executa a rodada inteira e **aborta** se o corpus não for equivalente. A ordem, os orçamentos e as flags ficam registrados em `manifest_round.json`, junto do `sha256` do binário medido — sem isso, dois relatórios de R2 não saberiam se mediram a mesma coisa.

**No runner do piloto** (a outra metade do aceite de R2): [`runner.py`](../../benchmarks/rust/runner.py) executa **uma tentativa** — valida snapshot e workspace, monta as ferramentas, mede o executor por fora, mata no primeiro teto, captura o patch, aplica em base limpa e escreve o manifesto. A parte que não depende de modelo do aceite ("captura todas as chamadas, custos e patches sem acesso ao ouro") está implementada e ensaiada com executor declarado como stub: **13 testes** em [`tests/test_rust_runner.py`](../../tests/test_rust_runner.py), incluindo a integração com o binário Rust real, que exige que o `delivered` medido pelo runner feche com o que o produto declara. Contrato completo, o que ele mede por fora em vez de acreditar e o que ele **não** garante: [`RUNNER_PILOTO.md`](RUNNER_PILOTO.md). A execução com modelo real segue bloqueada por P1/P2.

## 2. Corpus congelado e verificado — Q1 fechado

O problema era concreto: a referência Python indexa `siga-ex/src/main/java/**/*.java` (504 arquivos) e a descoberta do Rust é genérica (6 916 no repositório). Comparar "como está" mediria tamanho de corpus, não implementação.

`freeze_corpus.py` força os dois lados ao mesmo conjunto e **prova** a igualdade em duas camadas — conjunto de caminhos e hash de conteúdo por arquivo —, porque um caminho igual com bytes diferentes passaria batido:

| Verificação | Resultado |
|---|---|
| arquivos Python | 504 |
| arquivos Rust (`--include java`) | 504 |
| comuns | 504 |
| mesmo conjunto de caminhos | **sim** |
| mesmos hashes de conteúdo | **sim** |
| fingerprint de conteúdo | `bb7a99fbe4582c97…` |

Uma verificação de caminhos sozinha teria deixado passar o caso em que o Rust lê o arquivo errado; uma de bytes sozinha, o caso em que um lado indexa um arquivo a mais. Com as duas, a pendência Q1 de [`R1_REPORT.md`](R1_REPORT.md) §5 está fechada.

## 3. Método

- **Processo externo inteiro**, do spawn até consumir todo o stdout, sob GNU time com linha marcada (`%e %U %S %M %R %F %I %O %x`). Nenhuma medição é de função interna: inicializar o interpretador Python e abrir o processo Rust fazem parte do número, porque é isso que o agente paga.
- **Pareamento por consulta.** A comparação é feita *dentro* da mesma consulta, não entre médias gerais; a razão publicada é a mediana das razões por consulta.
- **Ordem alternada por repetição**: em 10 repetições cada braço ocupa cada posição 5 vezes; a primeira passada de cada (consulta, braço) é descartada como aquecimento.
- **36 consultas**: 30 estratificadas por frequência de documento (6 por estrato: 1, 2-5, 6-20, 21-100, >100 — vocabulário de 12 347 tokens) mais 6 de borda (zero correspondência, Unicode, multi-token, longa, pontuação, token curto). A seleção é determinística por posições igualmente espaçadas: rodar de novo sobre o mesmo corpus devolve as mesmas consultas.
- `max_bytes = 4 × budget_tokens` como entrada canônica, porque sem tokenizer do modelo o teto de bytes e a estimativa de tokens descrevem a mesma fronteira.
- Quantis por **posto mais próximo**; p50 = mediana (média dos dois centrais quando n é par).

O que este método **não** é: cache frio, cgroup isolado, ambiente dedicado. Ver §11.

### 3.1 Dois defeitos do próprio harness

Nenhum dos dois foi hipótese de projeto; os dois apareceram porque as tabelas foram conferidas contra o artefato bruto.

1. **O lado Python era lido pelo formato errado.** O envelope que a CLI imprime (`refs`, `texts`, `omitted.n`, `budget.used`) não é o dicionário interno de `capsule.py` (`symbols`, `files`, `truncation_log`, `hard_enforced`). Ler o formato interno de um produto que emite o externo devolveu **zero** em duas colunas — e zero falso é pior que campo ausente, porque entra na tabela como se fosse medida. Corrigido, e a regra passou a ser: campo ausente vira `null`, nunca `0`.
2. **O subcomando medido não era o subcomando pedido.** O construtor de linha de comando tinha `context` fixo como verbo. O modo `expand` media `context` com um pedido de expansão: saída válida, exit 0, bytes exatos — tudo plausível, nada de `expand`. Quem pegou foi a checagem independente de sobreposição de spans, que reprovou 100% das linhas. Um harness em que o comando medido não é o comando pedido não mede nada; a checagem que sobreviveu ao defeito é a que vale.

O terceiro defeito evitado foi de construção: passar `known_refs` sem `end_line` faria o span entregue ser um ponto, e o produto devolveria, corretamente, a janela ao redor dele. A dedup pareceria furada sem estar. O harness passou a usar `end_line`.

## 4. `context`: latência e memória

Política `CTX-RS`, medianas pareadas. Tabelas completas em [`tables.md`](../../experiments/rust/siga/2026-09-29-r2-queries/tables.md) §Política CTX-RS.

| orçamento | impl | wall p50 | wall p95 | RSS p50 (kB) | RSS p95 (kB) |
|---|---|---|---|---|---|
| 1 000 | python | 0,070 s | 0,080 s | 26 552 | 27 972 |
| 1 000 | rust | 0,000 s | 0,010 s | 6 570 | 8 952 |
| 2 000 | python | 0,070 s | 0,100 s | 26 572 | 27 976 |
| 2 000 | rust | 0,000 s | 0,010 s | 6 632 | 8 924 |
| 4 000 | python | 0,070 s | 0,080 s | 26 554 | 28 032 |
| 4 000 | rust | 0,000 s | 0,010 s | 6 662 | 8 960 |

O p50 do Rust aparece como `0,000 s` porque `%e` do GNU time tem resolução de 10 ms: o valor real está **abaixo do instrumento**, não em zero. A afirmação suportada é "mediana abaixo de 10 ms"; a diferença de latência não é quantificável com este instrumento. Já o p95 (10 ms contra 80–100 ms) está acima da resolução e é um número legítimo.

RSS é o eixo onde a diferença é grande e **não** está no piso do instrumento: p50 ≈ 26,0 MB contra 6,5 MB, cerca de 4x, estável nos três orçamentos. A cauda do Rust (máx 13 516 kB ≈ 13,2 MB) é 2x a mediana; nada no harness explica o caso, e ele fica registrado como observação, não como resultado.

## 5. Fidelidade do orçamento: declarado contra entregue

Esta seção mede o defeito que originou o contrato §6. `BASELINE.md` §4 o havia medido uma vez como ~2x; aqui ele é medido em 900 execuções por lado, com a mesma unidade de comparação dos dois lados — `chars//4`, a heurística que a própria referência publica como tokenizer:

| impl | n | bytes entregues (p50) | tokens por `chars//4` (p50) | tokens declarados (p50) | razão declarado/entregue (p50 · máx) | declara bytes? | acima de `max_bytes` |
|---|---|---|---|---|---|---|---|
| python | 900 | 3 914 | 978 | **438** | **0,45 · 0,50** | não | **315/900** |
| rust | 900 | 6 830 | 1 707 | **1 707** | **1,00 · 1,00** | sim | **0/900** |

- **A referência entrega cerca de 2,2x mais do que declara.** A razão 0,45 não é média de médias: é a mediana das razões *por execução*, que é onde a divergência apareceria se fosse heterogênea. A mediana e o máximo (0,45 e 0,50) mostram que o erro é sistemático, não ruído de cauda.
- **A referência não publica o tamanho do que entregou.** `declared_bytes` é `null` por ausência de campo, não por zero: sem ele, o consumidor não tem como conferir o próprio orçamento.
- **315 de 900 execuções** entregaram mais que o teto de bytes que o outro braço respeitou. Ressalva de leitura: a interface Python não recebe `max_bytes` — ela nunca foi convidada a respeitá-lo. O número diz que os dois produtos **não têm a mesma noção de teto**, não que um deles violou um contrato que aceitou.
- **O Rust fecha o envelope (razão 1,00 em mediana e em máximo, 900/900)**, e `used_bytes` é literalmente o tamanho do stdout emitido — 900/900, com a mesma asserção que R1 já usava.

### A divergência que mais importa: o orçamento é um botão?

| orçamento | impl | bytes entregues (p50) | refs/unidades (p50) | arquivos (p50) |
|---|---|---|---|---|
| 1 000 | python | 3 914 | 10 | 4 |
| 2 000 | python | 3 914 | 10 | 4 |
| 4 000 | python | 3 914 | 10 | 4 |
| 1 000 | rust | 3 830 | 3 | 3 |
| 2 000 | rust | 7 708 | 7 | 6 |
| 4 000 | rust | 14 901 | 14 | 10 |

No lado Rust, quadruplicar o orçamento quadruplica o payload — o teto é o limite efetivo. No lado Python o payload é **constante** nos três orçamentos (3 914 bytes, 10 referências, 4 arquivos); o `budget` só muda o rótulo de estado (`partial` cai de 75/180 para 10/180 e para 0/180), não o que é entregue. Uma comparação de custo por tarefa que varie o orçamento mediria, do lado Python, algo que não responde ao parâmetro.

## 6. Divergência semântica: a comparação é de produtos, Q3 fechado

A regra do plano §6 é explícita: divergência de semântica invalida a alegação de ganho devido apenas à linguagem; sem equivalência, publica-se comparação entre produtos distintos. **É este o caso.** Sem tokenizer comum e sem pipeline comum, nenhum número desta rodada autoriza dizer "Rust é mais rápido que Python" — autoriza dizer "estes dois produtos, medidos no mesmo corpus e nas mesmas entradas, se comportam assim".

| Dimensão | Referência Python (`archatlas/cli.py`) | Rust (`rust/archatlas`) |
|---|---|---|
| envelope | `refs` + `texts` separados | `units` com `kind`, `hash`, `evidence`, `truncated` |
| teto de bytes | não existe na interface | `max_bytes`, aplicado |
| declara bytes entregues | não | sim, exato |
| estado | `ok`/`partial` (log de truncamento) + `state: missing/corrupt` | `ok`/`partial`/`stale`/`unsupported` |
| unidade | token estimado `chars//4` | byte exato; `tokenizer_is_exact: false` |
| índice ausente | código 2 | código 3 (divergência declarada no contrato §3) |
| diversidade | sem teto por arquivo | teto por arquivo + `diversity_cap` |

As duas implementações **são** incrementais por hash de conteúdo (`store.py:44-50` e `store.rs`), e isso é o que torna a §7 interpretável: lá os dois lados fazem o mesmo trabalho, e o número compara sobrecarga.

## 7. Índice e ciclo editar/testar

### Construção do índice (10 repetições, diretórios exclusivos, nada reaproveitado)

| impl | wall min | wall p50 | wall p95 | wall máx | RSS p50 (kB) | índice (B) |
|---|---|---|---|---|---|---|
| python | 1,270 s | 3,140 s | 6,460 s | 6,460 s | 21 738 | 1 781 760 |
| rust | 0,050 s | 0,050 s | 0,150 s | 0,150 s | 10 542 | 3 727 360 |

Duas leituras honestas: o lado Rust é estável (0,05–0,15 s, sem cauda) e o Python varia 5x (1,27–6,46 s) — a dispersão do Python é informação, não ruído. E **o índice Rust é 2,1x maior em disco** (3,55 MiB contra 1,70 MiB), o que é um custo real da escolha de schema e não aparece em nenhuma meta de latência do plano.

### Ciclo editar/testar (reindexar depois de uma mutação)

A árvore do corpus é copiada para um diretório de trabalho por (cenário, repetição, implementação) — o dataset é read-only e continua intocado. A primeira indexação de cada cópia é *setup* e não é medida; o número é o da passada seguinte à mutação, que é o que o agente paga a cada edição. O alvo de `edit_1` é o maior arquivo do corpus até 100 KiB, escolhido em tempo de execução a partir de `corpus.json` (nenhum caminho do SIGA está embutido no harness).

| cenário | mutados | python wall p50 / p95 | rust wall p50 / p95 | python RSS p50 | rust RSS p50 | equivale a rebuild |
|---|---|---|---|---|---|---|
| `unchanged` | 0 | 0,030 / 0,030 s | 0,020 / 0,050 s | 19 372 | 6 224 | sim (3/3) / sim (3/3) |
| `edit_1` | 1 (99 601 B) | 0,050 / 0,060 s | 0,020 / 0,040 s | 19 728 | 8 108 | sim (3/3) / sim (3/3) |
| `edit_10` | 10 | 0,140 / 0,220 s | 0,030 / 0,040 s | 19 888 | 9 032 | sim (3/3) / sim (3/3) |
| `edit_100` | 100 | 0,490 / 1,000 s | 0,100 / 0,110 s | 20 504 | 8 920 | sim (3/3) / sim (3/3) |
| `delete_1` | 1 | 0,040 / 0,050 s | 0,020 / 0,020 s | 19 512 | 7 556 | sim (3/3) / sim (3/3) |
| `rename_1` | 1 | 0,050 / 0,100 s | 0,020 / 0,030 s | 19 384 | 7 632 | sim (3/3) / sim (3/3) |

Os dois lados declaram exatamente a mesma contagem em todos os cenários (1/10/100 reindexados, `pruned_files: 1` em delete e rename), o que é a evidência de que a semântica de invalidação bate. E cada execução medida foi conferida contra uma reindexação do zero na mesma árvore mutada: para o Rust, `generation(rebuild --force) == generation(incremental)`; para a referência, que não publica geração, o conjunto de arquivos dentro do índice tem de ser exatamente o do disco. **36 de 36 verificações passaram** — o ganho de tempo não é obtido por perda de correção.

Este é o único eixo da rodada em que a diferença de ordem de grandeza encolhe: em `edit_1` a razão é 2,5x, não 10x. O custo fixo do processo domina dos dois lados, e `edit_10`/`edit_100` mostram que o custo marginal por arquivo é o que separa as implementações.

O mesmo caminho de atualização que este quadro mede em custo tem a correção verificada em [`RUNNER_PILOTO.md`](RUNNER_PILOTO.md): o runner de tentativa captura o patch do workspace e o aplica numa base limpa antes de rodar o teste de aceitação, em vez de confiar no estado em que o agente deixou a árvore.

## 8. `expand` e `verify`: o segundo passo do ciclo

**Sem braço Python, por assimetria de produto.** A CLI de referência não tem `expand`, e o `verify` dela é um autoteste fixo de um arquivo (`archatlas/cli.py:22-29`), sem `--ref` e sem conferência de hash. As tabelas desta seção são do braço Rust e não são uma vitória sobre nada: são a única medição que existe do segundo passo do ciclo.

### 8.1 `expand` — 1 400 execuções, quatro variantes

Setup: uma chamada de `context` (não medida) fornece `known_refs`/`delivered_refs` com `end_line`. Quatro variantes em dois orçamentos (2 000, 8 000): `context`, `references` sem reserva, `references` com `evidence_reserve_pct` 30 e 50.

| orçamento | `evidence_wanted` | reserva | n | wall p50 | wall p95 | RSS p50 (kB) | unidades p50 | bytes p50 | `context` de setup (bytes p50) | razão | sem sobreposição | `used_bytes` exato |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2 000 | `context` | — | 175 | 0,000 s | 0,000 s | 5 376 | 8 | 7 719 | 7 712 | 1,01 | **175/175** | **175/175** |
| 2 000 | `references` | — | 175 | 0,000 s | 0,030 s | 6 352 | 7 | 7 707 | 7 712 | 1,01 | **175/175** | **175/175** |
| 2 000 | `references` | 30% | 175 | 0,000 s | 0,030 s | 6 504 | 7 | 7 727 | 7 712 | 1,01 | **175/175** | **175/175** |
| 2 000 | `references` | 50% | 175 | 0,000 s | 0,030 s | 6 532 | 7 | 7 683 | 7 712 | 1,01 | **175/175** | **175/175** |
| 8 000 | `context` | — | 175 | 0,000 s | 0,000 s | 5 516 | 29 | 25 871 | 28 783 | 1,00 | **175/175** | **175/175** |
| 8 000 | `references` | — | 175 | 0,000 s | 0,020 s | 6 424 | 22 | 31 377 | 28 783 | 1,10 | **175/175** | **175/175** |
| 8 000 | `references` | 30% | 175 | 0,000 s | 0,030 s | 6 552 | 22 | 31 377 | 28 783 | 1,10 | **175/175** | **175/175** |
| 8 000 | `references` | 50% | 175 | 0,000 s | 0,020 s | 6 540 | 22 | 31 333 | 28 783 | 1,11 | **175/175** | **175/175** |

- A dedup foi conferida no harness por **interseção de intervalos** contra os spans entregues, não lida de `omitted.reasons`: 1 400/1 400 sem sobreposição. `used_bytes` exato em 1 400/1 400, 0 exit ≠ 0.
- São 35 consultas, não 36: `e01` (zero correspondência) não entrega referência nenhuma e não há o que ampliar. A linha é omitida, não contada como falha.
- **A razão não mede novidade.** Ela é `bytes da expansão / bytes do context de setup`; como os dois pedidos têm o **mesmo teto**, a razão mede quanto do teto a expansão usa. Novidade é a coluna `sem sobreposição`, checada por interseção de intervalos contra tudo o que o setup entregou.
- **Erro de leitura corrigido nesta etapa:** a versão anterior deste relatório dizia que a expansão devolvia "volume comparável com material novo". Metade estava errada (§8.1.1).

#### 8.1.1 O defeito que a medição de Q7 revelou

Q7 dizia "`references` é inerte quando `known_refs` consomem o teto". Ao instrumentar a válvula de reserva, apareceu um defeito maior, e anterior a ela.

Num ciclo real `known_refs` **vem do `context`** — ou seja, são justamente os arquivos que a busca alcança. Medido por sondagem: o alcance lexical da consulta é subconjunto dos arquivos já entregues em **70/70** pares (7 consultas × 2 orçamentos conferidos um a um; q01, q03, q05, q08, q13, q16, q22, com `novos_fora_do_known = 0` em todos). Logo o único material novo que `references` podia trazer não era um arquivo novo, e sim ocorrência **fora da janela** de um arquivo já citado.

E era exatamente isso que não acontecia: um arquivo de `known_refs` produzia só a janela pedida. O pedido dizia "referências" e a resposta devolvia a janela de novo. Sem reserva, **63 de 70 pares** (consulta, orçamento) saíam **sem nenhuma unidade vinda da busca** — e a resposta era válida, com `used_bytes` exato, superfície idêntica à de `context`. Nenhum dos dois sinais que o harness checava (sobreposição, bytes) pegaria isso.

Correção (contrato §10.6): cada arquivo de `known_refs` passa a produzir **dois grupos** de spans — a janela pedida e as ocorrências do termo no mesmo arquivo —, com a dedup valendo também **dentro** da resposta.

| reserva | pares únicos | sem nenhuma unidade lexical (antes) | (depois) | unidades lexicais p50 (antes → depois) |
|---|---|---|---|---|
| sem reserva | 70 | 63 | **21** | 0 → 2 |
| 30% | 70 | 38 | **15** | 0 → 3 |
| 50% | 70 | 38 | **13** | 0 → 4 |

`antes` = `runs_expand_pre_samefile.jsonl`, `depois` = `runs_expand.jsonl`, ambas na pasta da rodada, **mesmo harness e mesmo índice** — o que muda é o binário. Os 21 pares que continuam sem unidade lexical são casos em que o termo ocorre uma única vez no arquivo: a janela já cobre a ocorrência e não há nada novo a entregar. Isso é correto, não lacuna.

#### 8.1.2 A reserva: efeito real, e menor do que o defeito

| política | execuções par | idênticas a `context` | com unidade lexical | lexical sem nenhuma janela | barrado declarado (`evidence_reserved`) |
|---|---|---|---|---|---|
| sem reserva | 350 | 80 | 245 | 5 | 0 |
| reserva 30% | 350 | 75 | 275 | 5 | 210 |
| reserva 50% | 350 | 65 | 285 | 5 | 235 |

- A reserva **funciona e é declarada**: 210 e 235 execuções trazem `evidence_reserved` em `omitted.reasons` — o barrado é nomeado, não silencioso.
- Ela **satura em 30%**: o conjunto de pares resolvidos é o mesmo com 30% e 50%, e o custo em latência e RSS não se distingue (p50 RSS 6 552 contra 6 540 kB). Não há razão medida para pedir mais que 30%.
- **`lexical sem nenhuma janela` = 5** em todas as políticas: por granularidade, uma unidade de janela pode ser maior que a fatia reservada, e então a reserva barra a janela inteira em vez de encolhê-la. São 5 pares em que a resposta fica só com evidência de busca. É o custo de reservar em bytes com unidades de até 60 linhas; está declarado, não é acidente.
- **Ordem de grandeza honesta:** a reserva resolve 25 a 40 pares; a mudança de §8.1.1 resolve 42 a 63. O defeito principal era o segundo, não o primeiro — e a leitura anterior deste relatório atribuía tudo à ordem de prioridade.

### 8.2 `verify` — 875 execuções

Cinco cenários por consulta e repetição, com o **código de saída esperado fixado antes da medição**: 0 para `ok` e `sem_hash`, 5 para os três reprovados.

| cenário | n | esperado | saiu como esperado | wall p50 | wall p95 | RSS p50 (kB) | `state` | unidades | `used_bytes` exato |
|---|---|---|---|---|---|---|---|---|---|
| `ok` | 175 | exit 0 | **175/175** | 0,000 s | 0,010 s | 5 372 | ok=175 | 1 | 175/175 |
| `sem_hash` | 175 | exit 0 | **175/175** | 0,000 s | 0,010 s | 5 340 | ok=175 | 1 | 175/175 |
| `hash_divergente` | 175 | exit 5 | **175/175** | 0,000 s | 0,010 s | 5 360 | partial=175 | **0** | 175/175 |
| `linha_fora` | 175 | exit 5 | **175/175** | 0,000 s | 0,010 s | 5 360 | partial=175 | **0** | 175/175 |
| `caminho_fora` | 175 | exit 5 | **175/175** | 0,000 s | 0,010 s | 5 068 | partial=175 | **0** | 175/175 |

- **875/875 com o código previsto**, e os motivos agregados saem exatos: `hash_divergent`, `line_out_of_range`, `outside_root` (175 cada).
- **Nas 525 reprovações, zero unidades entregues**; nos 350 casos aprovados, exatamente a linha citada. Reprovar não devolve texto não verificado nem lista vazia fingindo resposta.
- O custo da reprovação é o mesmo do sucesso (p50 abaixo da resolução, p95 10 ms nos dois): o portão é barato, não é o caminho caro do sistema.
- **Nada foi modificado no dataset**: hash errado e linha inexistente são *entradas*, não mutações de disco.

## 9. Escala: o que acontece quando o corpus cresce

O plano §6 pede medir "corpus maior" e §5 fixa **dois** tetos para a coorte — 5 mil arquivos **e** 256 MiB de texto. Os dois não caem no mesmo ponto: o corpus base tem 504 arquivos / 2,4 MiB (4,8 kB por arquivo), enquanto os dois tetos juntos implicariam ~52 kB de média. A série multiplica o mesmo corpus por 1, 10, 30 e 100, cruzando o teto de **contagem** em ×10 (5 040 arquivos) e chegando a 238,7 MiB em ×100 (50 400 arquivos) — 56% acima do teto de volume e 10x o de contagem.

O corpus sintético é uma **cópia**: cada arquivo aparece N vezes, logo `doc_freq` e ranking não são os de um projeto real. Tudo o que está abaixo é **custo** — tempo, RSS, bytes de índice —, não qualidade de resultado. As árvores são construídas em diretório temporário e removidas a cada tamanho; o dataset não é tocado.

Proveniência: este passo foi executado em **invocação separada** da rodada principal, por ser o mais caro, e o `manifest_scale.json` registra os tamanhos, as repetições e o ambiente. A linha de comando foi `benchmarks/rust/measure.py --mode scale --scale-sizes 1,10,30,100 --index-reps 3 --reps 5 --policy CTX-RS`; o driver `run_round.py` tem o mesmo passo atrás de `--with-scale`. `tables.md` agrega os dois conjuntos e lista os arquivos de origem no cabeçalho.

### 9.1 Indexação

| × | arquivos | MiB | impl | n | wall p50 | wall máx | RSS p50 (MB) | CPU p50 | índice (MB) | índice/arquivo (B) |
|---|---|---|---|---|---|---|---|---|---|---|
| ×1 | 504 | 2,4 | python | 3 | 1,200 s | 3,190 s | 21,2 | 0,35 s | 1,59 | 3 308 |
| ×1 | 504 | 2,4 | rust | 3 | 0,050 s | 0,060 s | 10,4 | 0,04 s | 3,57 | 7 428 |
| ×10 | 5 040 | 23,9 | python | 2 | 23,255 s | 31,490 s | 30,5 | 3,57 s | 15,9 | 3 305 |
| ×10 | 5 040 | 23,9 | rust | 2 | 0,635 s | 0,670 s | 14,4 | 0,53 s | 35,7 | 7 421 |
| ×30 | 15 120 | 71,6 | python | 1 | 92,850 s | 92,850 s | 47,2 | 9,68 s | 47,9 | 3 324 |
| ×30 | 15 120 | 71,6 | rust | 1 | 1,540 s | 1,540 s | 22,6 | 1,46 s | 103,8 | 7 196 |
| ×100 | 50 400 | 238,7 | python | 1 | 283,840 s | 283,840 s | 108,6 | 30,00 s | 161,0 | 3 351 |
| ×100 | 50 400 | 238,7 | rust | 1 | 5,550 s | 5,550 s | 53,1 | 4,98 s | 342,5 | 7 125 |

- **A indexação é o eixo onde os dois produtos fazem o mesmo trabalho** — mesmo conjunto de arquivos, mesmo incremental por hash de conteúdo, contagens declaradas idênticas e equivalência a rebuild conferida (§7). Por isso, e só por isso, os dois lados deste quadro são comparáveis; no `context` não são.
- Os dois escalam **linearmente** em tempo e RSS; o que difere é a constante: ~5,6 ms por arquivo contra ~0,11 ms, e ~12/2,1 KB de RSS por arquivo. A razão de tempo cresce de 24x (×1, onde o custo fixo de iniciar o interpretador domina) e se estabiliza em ~50x a partir de 5 mil arquivos.
- **O índice Rust é 2,2x maior em disco, e a razão é estável** (7,1–7,4 kB contra 3,3 kB por arquivo, em todos os tamanhos). É o custo real da escolha de schema e aparece em 342 MB contra 161 MB no maior ponto — a decisão de disco não é gratuita, e não existe meta de disco no plano.

### 9.2 `context` — onde o alvo é de produto

| × | arquivos | impl | n | wall p50 | wall p95 | RSS p50 (MB) | RSS máx (MB) |
|---|---|---|---|---|---|---|---|
| ×1 | 504 | python | 10 | 0,070 s | 0,090 s | 25,7 | 33,4 |
| ×1 | 504 | rust | 10 | **0,005 s** | 0,010 s | 7,2 | 8,8 |
| ×10 | 5 040 | python | 10 | 0,485 s | 0,790 s | 81,0 | 141,7 |
| ×10 | 5 040 | rust | 10 | **0,010 s** | 0,010 s | 8,7 | 9,3 |
| ×30 | 15 120 | python | 10 | 1,295 s | 2,050 s | 203,3 | 385,3 |
| ×30 | 15 120 | rust | 10 | **0,020 s** | 0,020 s | 12,3 | 13,2 |
| ×100 | 50 400 | python | 10 | 4,300 s | 7,330 s | **630,5** | **1 234,3** |
| ×100 | 50 400 | rust | 10 | **0,050 s** | 0,070 s | 22,2 | 25,5 |

- **A meta de `context` do plano §5 (p95 ≤ 150 ms, RSS ≤ 96 MiB) sobrevive a 10x o teto de arquivos da coorte:** no ×100, Rust entrega p95 de 0,070 s e pico de RSS de 25,5 MB. Medido — não projetado.
- A partir de ×30 as latências do Rust **saem do piso do instrumento** (20 ms, 50 ms): aqui a curva é um número, não um limite superior.
- A referência Python estoura os dois alvos no maior ponto: p95 de 7,33 s (49x o teto de 150 ms) e pico de RSS de 1,23 GB (13x o teto de 96 MiB). Como no §6, isso **não** é "Rust venceu": são produtos diferentes, com semânticas de payload diferentes, e o que a série mostra é uma constante por arquivo de ~12,8 kB de RSS contra ~0,45 kB.

## 10. Metas do plano §5

Metas de produto congeladas em R0, medidas aqui pela primeira vez com repetições. Todas as linhas abaixo são do braço Rust:

| Meta (§5) | Medido | Situação |
|---|---|---|
| `doctor`, processo novo, cache aquecido: p95 ≤ 50 ms / RSS ≤ 32 MiB | p95 abaixo da resolução de 10 ms / 5,2 MB | dentro |
| `context` até 8k tokens: p95 ≤ 150 ms / RSS ≤ 96 MiB | p95 0,010 s / p95 8,9 MB | dentro |
| `index`: RSS ≤ 256 MiB | 10,6 MB | dentro |
| atualizar 1 arquivo ≤ 100 KiB: p95 ≤ 500 ms | p95 0,040 s | dentro |
| 10 / 100 arquivos, delete, rename | 0,040 / 0,110 / 0,020 / 0,030 s (p95) | dentro |

Três ressalvas que impedem ler a tabela como validação de escala:

1. **O corpus base é pequeno.** 504 arquivos e 2,4 MiB de texto, contra os dois tetos da coorte (5 mil arquivos e 256 MiB). Este quadro vale para essa coorte; a extrapolação é medida à parte em §9, sobre corpus sintético, e é lá que ela deve ser lida.
2. **Latências abaixo de 10 ms não estão resolvidas** pelo instrumento usado (GNU time `%e`). As metas de `doctor` e `context` são atendidas com margem ampla, mas o número exato não existe neste relatório.
3. **RSS em máquina compartilhada não é teto de grupo.** Nada foi medido em cgroup isolado e o page cache não foi derrubado (pendência P8). Os valores são do processo, não do grupo.

## 11. Comportamento verificado, não presumido

Cada linha tem teste que a executa ([`tests/r2.rs`](../../rust/archatlas/tests/r2.rs), [`tests/contract.rs`](../../rust/archatlas/tests/contract.rs)):

- `verify` confirma citação válida, confere hash quando fornecido, recusa linha fora do arquivo, recusa referência fora da raiz e recusa `--ref` malformado — cada reprovação sai com código 5, nunca com texto não verificado.
- `verify` denuncia índice desatualizado para o arquivo citado em vez de responder com base em estado velho.
- `expand` amplia sem repetir trecho já entregue, alcança outros arquivos por `references`, filtra por caminho quando `evidence_wanted: tests`, respeita o orçamento (700/1 500/12 000 bytes testados) e recusa `context` sem `known_refs` com código 2.
- `expand` traz a ocorrência **fora da janela** de um arquivo já citado, sem sobrepor o que já foi entregue nem a própria resposta — teste com o grupo de spans desabilitado **falha**, então a cobertura tem dentes.
- `evidence_reserve_pct` muda o resultado com o mesmo pedido e o mesmo índice (teste mede o antes e o depois com o teto vinculando), é byte-idêntico a ausente quando vale 0, recusa `context` e recusa > 100 com código 2.
- `--include` restaura o corpus exato da referência Python e reporta `excluded_by_filter` — nunca descarta em silêncio.
- `name_on_line` permanece `null`: não há extrator de símbolos, e nenhuma resposta pode ser lida como definição.

## 12. Limitações declaradas

- **Nada aqui é sobre patches, modelos ou custo.** R2 não executou smoke com modelo, nenhum patch foi produzido, nenhuma telemetria de provedor foi lida. Isso é R3, bloqueado por P1 (modelo efetivo) e P2 (teto financeiro) — decisões do usuário.
- **Todas as medições são com cache de filesystem aquecido.** Cache frio exigiria `drop_caches` com root em máquina dedicada. O relatório não chama nada de "frio".
- **Sem cgroup isolado.** RSS é pico do processo; memória do grupo e page cache não foram medidos (pendência P8).
- **Resolução do instrumento.** `%e` do GNU time entrega 10 ms; qualquer valor do Rust abaixo disso é "abaixo de 10 ms". Isso também explica a coincidência de p50 = 0,000 nas três políticas — não é código sem custo, é teto de medição.
- **`expand` e `verify` não têm comparação.** Foram medidos (§8), mas só do lado Rust: a referência não tem `expand` nem um `verify` de referência. Latência e RSS existem; 'mais rápido que' não.
- **`expand` foi medido em dois orçamentos e duas evidências**, não numa grade. Outras políticas e `evidence_wanted=tests` não têm tabela.
- **A reserva é em bytes com unidades de até 60 linhas**, então pode barrar uma janela inteira em vez de encolhê-la: em 5 dos 350 pares reservados a resposta fica só com evidência de busca. Reserva em linhas ou em tokens exigiria o tokenizer do modelo (P3).
- **O antes/depois de §8.1.1 compara dois binários**, não duas configurações: `runs_expand_pre_samefile.jsonl` e `runs_expand.jsonl` saíram do mesmo harness e do mesmo índice, mas de binários diferentes. É a única forma de medir a correção de um defeito que o harness não sabia detectar na primeira rodada — e é por isso que a linha de base foi preservada em vez de sobrescrita.
- **Uma única rodada, uma única máquina.** As repetições estão dentro da rodada; não há replicação em outro hardware. O `manifest_round.json` traz o `sha256` do binário, o ambiente e a linha de comando exata para permitir replicação.
- **A escala (§9) usa corpus sintético por cópia** e nos dois maiores tamanhos há **uma** execução por lado (`n=1` no ×30 e ×100). Ali a curva de tendência é o resultado; o valor de um ponto isolado não é. `doc_freq` e ranking do corpus copiado não são os de um projeto real, então nada da §9 fala de qualidade de recuperação.
- **Consultas de borda entram nas linhas das tabelas de razão** (com `stratum` = tipo de borda) e portanto no `máx` das linhas de resumo: o pior caso de `CTX-RS` orçamento 1000 é a consulta Unicode, não uma consulta estratificada. As linhas individuais estão separadas; as de resumo, não.
- **`tokenizer_is_exact: false` em todo o relatório.** Sem tokenizer do modelo, a unidade rígida é byte; nenhuma conclusão sobre "orçamento de tokens" é feita.
- **Sem CI.** A suíte roda localmente (pendência Q2, do usuário).

## 13. Estado do gate

| Gate | Planejado | Implementado | Ensaiado | Executado | Avaliado | Conclusão científica |
|---|---|---|---|---|---|---|
| R2 | x | **x** | **x** | **parcial** (microbenchmarks em 6 tamanhos; runner ensaiado com stub, sem modelo) | — | não avaliada |

Executado **parcialmente**, e a distinção é o ponto: os microbenchmarks foram executados — **4 245 execuções com artefato bruto auditável** (1 800 de consulta, 1 400 de `expand`, 875 de `verify`, 94 de escala, 36 de atualização, 20 de índice, 20 de `doctor`) mais **1 400 preservadas** como linha de base do antes/depois (§8.1.1) —, mas a segunda metade do aceite de R2 — "integrar por shell a um único executor/modelo real" e "runner captura todas as chamadas, custos e patches sem acesso ao ouro" — **não foi executada**, porque depende de P1/P2 (modelo efetivo e teto financeiro, decisões do usuário).

Pendências ao fim de R2:

| # | Pendência | Dono | Situação |
|---|---|---|---|
| Q1 | Corpus comum Python/Rust | A | **fechada** (§2: 504 = 504, caminhos e bytes) |
| Q2 | Workflow de CI para `cargo test` | usuário | aberta |
| Q3 | Comparação de implementação ou de produto | A | **fechada** (§6: de produto, declarado) |
| Q4 | Cache frio e cgroup isolado (P8) | usuário | aberta — exige máquina dedicada/root |
| Q8 | Corpus de escala sintético e `n=1` nos dois maiores tamanhos | A | **replicada em 2026-10-05** (Adendo: índice ×30 n=4, ×100 n=3; `context` n=10; tendência confirmada) — resta medir um corpus real grande não copiado |
| Q5 | Microbenchmark de `expand` e `verify` | A | **fechada** (§8: 700 + 875 execuções, 875/875 códigos previstos) |
| Q6 | Integração com o runner real | A (infra) + usuário (P1/P2) | **infraestrutura pronta e ensaiada** ([`RUNNER_PILOTO.md`](RUNNER_PILOTO.md)); falta executor/modelo, rubrica e teto financeiro |
| Q7 | `evidence_wanted=references` inerte quando `known_refs` consomem o teto | A | **fechada** (§8.1.1 e §8.1.2: dois grupos de spans por arquivo citado + `evidence_reserve_pct`, com antes/depois medido) |
| Q9 | Alcance lexical ser subconjunto dos arquivos já entregues | A | registrada (§8.1.1: 70/70 sondagens). Enquanto `known_refs` vier do `context`, "arquivo novo" é impossível por construção — quem quiser alcance novo deve consultar em vez de expandir |

Próxima ação: **R3** (smoke com modelo, 3 condições × 4 tarefas = 12 execuções por trilha) assim que o modelo efetivo e o teto financeiro existirem. R3 não pode começar por documentação. De R2 seguem abertos Q2 (CI), Q4 (cache frio), Q6 (runner real, bloqueado por P1/P2), Q8-parcial (resta corpus real não copiado) e Q9 (alcance lexical é subconjunto do que o `context` já entregou). Q1, Q3, Q5 e Q7 fechadas.

## Adendo 2026-10-05 — replicação Q8 (×30/×100 com mais repetições)

Linha de comando (mesmo harness, mesmos insumos congelados de 29/09 — `corpus.json`/`queries.json` reutilizados, fingerprint `bb7a99fb…` conferido, dataset intocado): `measure.py --mode scale --scale-sizes 30,100 --index-reps 4 --reps 5 --policy CTX-RS`. Binário reconstruído do fonte (`rustc 1.96.0`, mesmo toolchain de 29/09; `git_head 48f5037`, sujo só por untracked). Artefatos brutos em `experiments/rust/siga/2026-10-05-r2-scale-q8/` (`runs_scale.jsonl` 54 linhas, exit ≠ 0 zero, `indexed == files` em todas; `tables.md` gerado por `report.py`, nenhum número à mão). Reserva: sem build/indexação pesada concorrente da outra trilha no período; host compartilhado sem reserva exclusiva (load ~5–7, MemAvailable ~6 GiB contra ~11 GiB em 29/09) — registrado porque as condições diferem.

| × | fase | impl | n (29/09) | wall p50 | wall máx | RSS p50 | índice/arquivo |
|---|---|---|---|---|---|---|---|
| ×30 | index | python | 4 (1) | 196,73 s (92,85 s) | 295,05 s | 46,6 MB (47,2) | 3 323,9 B (3 324) |
| ×30 | index | rust | 4 (1) | 2,28 s (1,54 s) | 6,68 s | 22,8 MB (22,6) | 7 195,9 B (7 196) |
| ×100 | index | python | 3 (1) | 435,38 s (283,84 s) | 493,73 s | 108,1 MB (108,6) | 3 350,6 B (3 351) |
| ×100 | index | rust | 3 (1) | 12,67 s (5,55 s) | 13,57 s | 53,3 MB (53,1) | 7 125,2 B (7 125) |
| ×30 | context | python | 10 (10) | 1,27 s (1,295 s) | 2,33 s | 203,5 MB (203,3) | — |
| ×30 | context | rust | 10 (10) | 0,020 s (0,020 s) | 0,080 s | 12,3 MB (12,3) | — |
| ×100 | context | python | 10 (10) | 4,28 s (4,300 s) | 7,28 s | 631,0 MB (630,5) | — |
| ×100 | context | rust | 10 (10) | 0,065 s (0,050 s) | **0,350 s** | 22,1 MB (22,2) | — |

Leitura honesta, ponto a ponto:

- **A tendência de §9 sobrevive com repetições:** índice escala linearmente nos dois lados; bytes de índice por arquivo são determinísticos e byte-idênticos aos de 29/09 (3 324/3 351 e 7 196/7 125 B); `context` replica os valores de 29/09 dentro de centésimos (p50) e do ruído de pico (RSS máx).
- **Paredes absolutas de indexação ~2x maiores que em 29/09** (python ×30 p50 197 s contra 93 s; ×100 435 s contra 284 s). A primeira repetição de cada série é a mais lenta (295 s → 124 s no ×30), padrão de cache/contenção, não de produto: o `declared` (contagens, bytes de índice) é idêntico entre reps. Nada aqui muda constante por arquivo como conclusão — muda o aviso de que parede absoluta depende do host.
- **A meta §5 de `context` (p95 ≤ 150 ms) NÃO é atendida nesta replicação no ×100:** p95 por posto mais próximo = máx = 0,350 s (9/10 reps ≤ 0,10 s; o outlier é a primeira repetição sob load). Em 29/09 o máx era 0,070 s. O quadro de §10 continua valendo para a rodada original; para este host carregado, o número com repetições é 0,35 s de pior caso, não 0,07 s.
- **Q8 segue parcial:** a metade "mais repetições" está feita; a metade "corpus real grande não copiado" continua aberta — o harness de escala só sabe copiar a subárvore Java congelada (`SUBTREE` fixo) e não há corpus real grande alternativo disponível neste host (o checkout Bitcoin local é C++/Python, fora do formato do harness; adaptá-lo seria outro experimento, não esta replicação).

## Adendo 2026-10-05 (2) — enabler Q8-real: `--subtree` aditivo + sonda da raiz

Para medir um corpus real não copiado, o escopo estava fixo em três lugares (`archatlas/cli.py`, `freeze_corpus.py`, `gen_queries.py`/`measure.py`). Passo 1, aditivo e com prova de não-regressão: `archatlas index` e `freeze_corpus.py` aceitam `--subtree` (default idêntico ao fixo anterior). Prova: congelar com default e com `--subtree siga-ex/src/main/java` explícito reproduz o fingerprint publicado `bb7a99fb…` (504 arquivos, equivalência OK) — teste `tests/test_corpus_subtree.py` (3 testes).

Sonda da raiz (`--subtree .`, repo SIGA real, 2,1 GiB): Python 2328 × Rust 2278, mesmos bytes em todo o comum, bloqueio só por **50 arquivos só-Python, todos em `siga-teste/data/external_repos/`** (amostra `spring-petclinic` vendoredada com `.git` aninhado: o walker Rust a ignora, o `rglob` Python não). Ou seja: o corpus real existe e é quase todo equivalente; falta decidir o escopo (excluir fixtures externas vendoredadas com motivo declarado, ou alinhar walkers) antes de congelar, derivar consultas e medir. Isso é o passo 2, ainda aberto — Q8-real continua parcial.

## Adendo 2026-10-05 (3) — Q8-real passo 2: equivalência na raiz, corpus real congelado

Alinhamento em vez de exclusão: o indexador Python pula subdiretórios com `.git` próprio (regra de repos aninhados, igual ao walker Rust; a raiz do escopo nunca é excluída), e `gen_queries.py` aceita `--subtree` (default idêntico ao fixo; regenerar as 30 consultas do corpus 504 produz lista idêntica). Provas em `tests/test_corpus_subtree.py` (5 testes: fingerprint 504 pinado, flag noop, walker unitário, raiz equivalente, regen idêntica).

Corpus real congelado em `experiments/rust/siga/2026-10-05-q8-realcorpus/corpus.json`: **2278 arquivos, fingerprint `34eb6630…`, equivalência OK (conjunto e bytes)**. Falta o passo 3, ainda aberto: rosquear `--subtree` nos modos `index`/`query` de `measure.py`, derivar as consultas do corpus real e medir (índice + `context`) — só então Q8 fecha.
