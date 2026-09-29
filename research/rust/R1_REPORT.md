# R1 — fatia Rust funcional: `doctor`, `index`, `context`

Data: 2026-09-29. ID: `R1-REPORT/1`. Etapa: **R1** de [`RUST_CLI_PILOTO_REAL.md`](../../plans/RUST_CLI_PILOTO_REAL.md) §6.
Contrato implementado: [`CLI_CONTRACT/1`](CLI_CONTRACT.md) (+ esclarecimentos §8).
Base: `main` após `6e30ea2` (R0). Dataset: `../siga` @ `e3be22828`.

## 1. O que foi entregue

Pacote Rust em `rust/archatlas/`, toolchain pinada em `rust-toolchain.toml` (1.96.0). O caminho de execução **não chama Python**. Sete módulos, conforme a arquitetura prevista no plano §3:

| Módulo | Responsabilidade |
|---|---|
| `cli` | parsing, despacho, códigos de saída 0/2/3/4/5, disciplina de stdout |
| `request` | parsing estrito do pedido (`deny_unknown_fields`) e validação |
| `discovery` | varredura com exclusões; conta binário/grande/desconhecido |
| `store` | índice SQLite+FTS5, schema versionado, geração, incremental ≡ rebuild |
| `retrieve` | tokenização `[A-Za-z0-9_]+` e BM25 do FTS5 |
| `pack` | seleção por política e orçamento contado na serialização final |
| `snapshot` | hash, caminho relativo seguro, `root_id`, `sha_base` |

Suíte: **60 testes verdes** em `cargo test --release` — 44 unitários + 16 de integração que spawnam o binário real (é assim que os critérios de aceite sobre o *processo* ficam verificados).

## 2. Três defeitos encontrados e corrigidos durante a própria R1

Nenhum destes foi previsto no plano; os três apareceram porque a medição foi feita em vez de presumida.

### 2.1 Estado atribuído depois da medição (desvio de 5 bytes)

O campo `state` era escrito **após** o ponto fixo do orçamento. Como `"ok"` e `"partial"` têm tamanhos diferentes, `used_bytes` ficava 5 bytes menor que o stdout real. Foi o teste no repositório real que pegou: `assert_eq!(used_bytes, stdout.len() - 1)` falhou com 7981 contra 7986.

Correção: o estado passou a ser decidido **antes** de medir, dentro do laço. A ordem do contrato §6 ("montar JSON completo → serializar e contar") não é decorativa — medir e depois editar é exatamente o defeito da referência Python, em escala menor.

### 2.2 `DELETE` no FTS5 a cada arquivo: O(n²) na indexação

`docs` é FTS5 com `path` UNINDEXED, então `DELETE FROM docs WHERE path=?` **varre a tabela inteira**. A primeira versão executava esse `DELETE` para todo arquivo, inclusive num índice vazio.

| Cenário | Antes | Depois |
|---|---|---|
| Repo inteiro (6 916 arquivos) | **110,58 s** | **1,71 s** |
| Só Java (511 arquivos) | 0,32 s | **0,08 s** |

Correção: só apagar quando a linha existe, e preparar os statements uma vez fora do laço. Ganho de 65x, medido.

### 2.3 Ajuste de orçamento O(n²)

A primeira versão removia **uma unidade por iteração** e re-serializava a resposta inteira a cada volta. Com 200 candidatos e ~40 que cabiam, isso dava ~160 serializações completas.

| `context` no repo real | Antes | Depois |
|---|---|---|
| wall | **3,64 s** | **0,09 s** |

A consulta FTS5 equivalente custa 2 ms (medida direto no mesmo índice), então a busca lexical nunca foi o gargalo. Correção: busca binária pelo maior prefixo que cabe (`O(log n)` medições em vez de `O(n)`), mais uma tentativa de **cortar** a próxima unidade para aproveitar a sobra.

## 3. Verificação do orçamento — o aceite central

Ordem obrigatória do contrato §6 executada ponta a ponta no repositório real. `used_bytes` tem que ser literalmente o tamanho da resposta emitida:

| política | `budget_tokens` | `max_bytes` | rc | dentro do teto | `state` | unidades | arquivos | bytes | tokens | utilização |
|---|---|---|---|---|---|---|---|---|---|---|
| LEX-RS | 500 | 5 000 | 0 | sim | partial | 2 | 2 | 1 871 | 467 | 0,93 |
| LEX-RS | 1 000 | 10 000 | 0 | sim | partial | 6 | 6 | 3 720 | 930 | 0,93 |
| LEX-RS | 2 000 | 20 000 | 0 | sim | partial | 8 | 8 | 6 185 | 1 546 | 0,77 |
| LEX-RS | 4 000 | 40 000 | 0 | sim | partial | 16 | 16 | 14 680 | 3 670 | 0,92 |
| CTX-RS | 500 | 5 000 | 0 | sim | partial | 1 | 1 | 1 676 | 419 | 0,84 |
| CTX-RS | 1 000 | 10 000 | 0 | sim | partial | 2 | 2 | 3 761 | 940 | 0,94 |
| CTX-RS | 2 000 | 20 000 | 0 | sim | partial | 7 | 7 | 7 990 | 1 997 | 1,00 |
| CTX-RS | 4 000 | 40 000 | 0 | sim | partial | 11 | 11 | 15 478 | 3 869 | 0,97 |

**8 de 8 configurações dentro do teto**, com utilização entre 0,77 e 1,00 — o orçamento é usado, não subdeclarado. Contraste direto com `BASELINE.md` §4, onde a referência declarava `used: 1972` para um payload que a própria heurística colocaria em 4 089.

`used_tokens = used_bytes // 4` em todas, e `tokenizer_is_exact: false` sempre — não há tokenizer do modelo, então a unidade exata é byte e o piloto não pode alegar orçamento rígido em tokens.

Todos os estados saem `partial` porque os orçamentos testados cortam material: a saturação do CTX-RS em 7 unidades com 11 disponíveis é o corte por diversidade agindo, e aparece em `omitted.reasons`.

## 4. Recursos e latência (execuções únicas — **não** é benchmark)

Números de uma medição pontual nesta máquina compartilhada, para orientar R2. O protocolo (§7) exige 10 repetições pareadas por implementação, quantis com convenção publicada e separação de frio/quente: nada disso foi feito aqui.

| Operação | Medido | Meta do plano §5 | Situação |
|---|---|---|---|
| `doctor`, processo novo, cache aquecido | 0,00 s / RSS 5,2–5,4 MB | p95 ≤ 50 ms / ≤ 32 MiB | dentro |
| `context`, índice pronto, resposta ≤ 8k tokens | 0,049–0,096 s / RSS ~17 MB | p95 ≤ 150 ms / ≤ 96 MiB | dentro |
| `index` repositório inteiro | 1,71 s / RSS 20,7 MB | RSS ≤ 256 MiB | dentro |
| `index` 511 arquivos Java | **0,08 s** / RSS 10,5 MB | — | ver §5 |
| atualização de 1 arquivo, repo inteiro | 0,32–0,37 s | p95 ≤ 500 ms | dentro |
| binário release | 4 587 704 B (4,59 MB) | — | — |
| índice Java (511 arqs) | 3 878 912 B | — | — |
| índice repo inteiro (6 916 arqs) | 107 909 120 B | — | — |

Meta de RSS é atendida com folga em tudo, mas **RSS medido em máquina compartilhada não é teto de grupo**: nada foi medido em cgroup isolado, e page cache frio não foi derrubado. Ambas as dimensões seguem como pendência P8 de [`BASELINE.md`](BASELINE.md) §5.

## 5. A comparação com Python que ainda **não** é válida

`BASELINE.md` §3.3 mediu a referência Python indexando 504 arquivos Java em 5,54 s com RSS 21,9 MB. No mesmo subconjunto de fontes, o Rust indexa 511 arquivos em 0,08 s com RSS 10,5 MB — cerca de 69x mais rápido e metade da memória.

Isso **não** é a comparação de R2 e não deve ser citado como resultado. Três razões:

1. É uma execução única de cada lado; R2 exige 10 repetições pareadas e ordem alternada.
2. O corpus não é idêntico: 511 contra 504 (o walker do Rust inclui `.properties`/`.xml` do mesmo diretório). Divergência de corpus invalida a comparação por regra do próprio protocolo (§1).
3. É comparação de *implementação*, não de produto. Não diz nada sobre custo por patch correto.

Registrado aqui como **hipótese para R2**, não como ganho.

Há também uma diferença de escopo que R2 precisa resolver antes de qualquer número: a referência Python é fixada em `siga-ex/src/main/java/**/*.java` (504 arquivos), enquanto a descoberta do Rust é genérica e cobre o repo inteiro (6 916 arquivos). Comparar os dois "como estão" mediria tamanho de corpus, não linguagem. R2 tem que congelar um corpus comum aos dois lados.

## 6. Comportamento verificado, não presumido

Cada linha abaixo tem teste que a executa; nenhuma é afirmação de projeto.

- Fonte citada corresponde aos bytes do snapshot: o `hash` de cada unidade é conferido contra o `sha256` do arquivo em disco, e cada linha entregue é conferida contra o arquivo real.
- Nenhum caminho absoluto nem `..` em nenhuma resposta; o stdout é varrido procurando a raiz do repo.
- `doctor` e `context` **não modificam** o arquivo de índice (bytes antes e depois comparados).
- Incremental ≡ rebuild em geração lógica, após edição, exclusão e rename.
- Arquivo apagado deixa de ser entregue; arquivo novo entra.
- Índices isolados: consultar o índice A não devolve arquivo do repo B, e o índice B continua íntegro.
- `--workers 1` e `--workers 4` produzem a mesma geração.
- stdout byte-idêntico entre execuções (determinismo para replay).
- Estado `stale` quando o `sha_base` pedido difere do indexado, ou quando uma fonte reprova na verificação — com a parte verificada ainda entregue e pista acionável.
- Códigos 2/3/4/5 exercitados: pedido inválido, índice ausente/corrompido/vazio, I/O, referência fora da raiz, nada verificável.
- Orçamento menor que o envelope: `partial` + `envelope_too_large`, zero unidades.
- `LEX-RS` e `CTX-RS` divergem de fato: LEX entrega uma unidade por arquivo; CTX respeita teto de 3 por arquivo e reporta `diversity_cap`.

## 7. Limitações declaradas

- **Lexical, não estrutural.** Não há extrator de símbolos nem resolução de tipos. Nenhuma resposta pode ser lida como definição. `doctor` declara `lexical` para todas as 14 linguagens, e um teste guarda contra promover Java a `structural` sem extrator.
- **`expand` e `verify` não existem.** Saem com código 2 e mensagem explícita. São R2.
- **Sem atalho por `mtime`.** O incremental compara hash de conteúdo. Mais lento que o possível, correto por construção.
- **`ignored` não medido** (`null` com motivo): o walker poda antes de reportar.
- **Comparabilidade com Python não resolvida** (§5).
- **Nenhum smoke com modelo, nenhum patch, nenhum custo.** R1 não toca nada disso; R3 é bloqueado por P1/P2 de `BASELINE.md` §5.
- **Sem CI.** A suíte roda localmente; não há workflow que a execute em outro ambiente. Ver pendência abaixo.

## 8. Estado do gate

| Gate | Planejado | Implementado | Ensaiado | Executado | Avaliado | Conclusão científica |
|---|---|---|---|---|---|---|
| R1 | x | **x** | **x** | — | — | não avaliada |

"Implementado" e "ensaiado" em R1 significam: binário funcional e suíte verde exercitando o contrato. **Não** significa melhoria de retenção ou economia — isso exige execução real (R3) e confirmação cega (R5), ambas bloqueadas por decisões do usuário (modelo, teto financeiro, custodiante).

Pendências novas abertas por R1, além das 8 de `BASELINE.md` §5:

| # | Pendência | Dono | Ação |
|---|---|---|---|
| Q1 | Corpus comum Python/Rust para R2 | A | congelar coorte idêntica antes de comparar (§5) |
| Q2 | Workflow de CI para `cargo test` | usuário | autorizar; hoje a suíte só roda localmente |
| Q3 | Normalizar tokenização/ranking entre Python e Rust | A | decidir em R2 se a comparação é de implementação ou de produto |

Próxima ação: **R2** — microbenchmarks com repetições pareadas e corpus congelado, implementação de `expand`/`verify`, e integração com o runner real.
