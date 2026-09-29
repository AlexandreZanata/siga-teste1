# Avaliação cega — rubrica, cegamento e adjudicação

Data: 2026-09-29. ID: `ATLAS-RUBRIC/1`. Estado: **infraestrutura implementada e ensaiada; nenhum julgamento real executado**.
Depende de: [`PREREGISTRATION_R0.md`](PREREGISTRATION_R0.md) §1.2/§1.5, [`PROTOCOLO_VALIDACAO.md`](PROTOCOLO_VALIDACAO.md) §3/§5/§6/§9, [`RUNNER_PILOTO.md`](RUNNER_PILOTO.md), [`../plans/RUST_CLI_PILOTO_REAL.md`](../../plans/RUST_CLI_PILOTO_REAL.md) §6 (R3/R5).
Ferramenta: [`benchmarks/rust/eval.py`](../../benchmarks/rust/eval.py). Testes: [`tests/test_rust_eval.py`](../../tests/test_rust_eval.py).

O aceite de R3 exige "revisão cega dos patches"; o de R5 exige que os patches sejam julgados **antes** de abrir condições e custos. Nada disso precisa esperar o modelo: o que não depende de P1/P2 é o instrumento de julgamento, e é o que este documento descreve. Ele **não** é resultado — o próprio plano (§6, R5) manda não marcar conclusão pela existência de um arquivo de pré-registro ou de um embaralhamento de IDs.

## 1. Conjunto de tarefas: `atlas-tasks/2`

O schema `/1` bastou para ensaiar o runner: `id`, `split`, `category`, `statement`, `base_sha`, `test_command`, `timeout_s`. Falta nele exatamente o que a avaliação precisa para ter dentes:

| Campo novo | Por que existe |
|---|---|
| `allowed_paths` | sem escopo declarado, "alteração indevida" vira opinião. Com ele, sair do escopo é **reprovado pela mecânica**, antes de qualquer humano |
| `immutable_paths` | o protocolo §3.4 não confia em teste que o agente possa ter enfraquecido. Tocar o teste do avaliador reprova |
| `origin` | protocolo §3: registrar de onde a tarefa veio |
| `contamination_risk` + `contamination_note` | §4: tarefa vinda de issue pública pode estar no treino do modelo; o risco é declarado por tarefa, não presumido |

`eval.py` **recusa** avaliar um conjunto `/1` — não por formalismo: sem `allowed_paths` a checagem de escopo não existe, e avaliar sem ela é pior que não avaliar, porque o número sai. O runner aceita os dois schemas (recusar `/1` quebraria tentativas já ensaiadas sem ganho), e o manifesto passa a copiar `allowed_paths`/`immutable_paths` para que a tentativa registre sob que escopo correu.

`validate` verifica o schema, o vocabulário fechado de `category` (as quatro do pré-registro §1.2) e de `split` (`smoke`/`piloto`/`holdout`), ids únicos, campos obrigatórios e o balanço 4/4/4/4 — conjunto desbalanceado só passa com `--allow-imbalance`, e a razão tem de ir para o relatório. Template em [`benchmarks/rust/tasks.template.json`](../../benchmarks/rust/tasks.template.json) (que valida, e continua `sealed: false`): os enunciados reais são decisão da pesquisa, não deste instrumento.

## 2. Rubrica: `ATLAS-RUBRIC/1`

**A mecânica tem precedência.** Item mecânico reprovado reprova a tentativa, e nenhuma nota humana compensa. Julgamento humano existe para o que não é executável.

### 2.1 Itens mecânicos (calculados do artefato, sem humano)

| Item | Pergunta | Fonte | Reprovado significa |
|---|---|---|---|
| `M1` | o patch aplica em base limpa? | `acceptance.applied` | rejeitado |
| `M2` | o comando de aceitação do avaliador sai com 0? | `acceptance.exit_code` | rejeitado |
| `M3` | houve alteração? | tamanho do patch | rejeitado — tentativa sem alteração é falha, não "não havia o que mudar" |
| `M4` | tudo que foi tocado está em `allowed_paths`? | caminhos extraídos do patch | rejeitado |
| `M5` | algum `immutable_paths` foi tocado? | idem | rejeitado |
| `M6` | a tentativa terminou por si, sem morrer num teto? | `stopped_by`/`stopped_killed` | rejeitado — teto atingido não é sucesso parcial |

`M2` merece uma frase: os testes que o **agente** escreveu são evidência complementar, nunca o critério — se ele escreve um teste que passa, isso não prova que o requisito foi atendido.

### 2.2 Itens semânticos (revisão humana)

| Item | Pergunta | O que **não** é evidência |
|---|---|---|
| `H1` | resolve o enunciado, e resolve inteiro? | semelhança textual com o patch de referência |
| `H2` | quebra algo que o teste de aceitação não cobre? | o verde do comando de aceitação (cobre o aceite, não o sistema) |
| `H3` | há alteração não relacionada, reescrita gratuita ou churn? | tamanho do diff isolado |

Identidade textual ao patch de referência é **proibida** como critério (protocolo §3.5). Para isso ficar verificável, o julgamento carrega `differs_from_reference` por item, e o relatório mostra quantos aceites diferem do de referência — prova de que a rubrica não virou comparação de texto.

### 2.3 Estados que não contam como sucesso

`indeterminado`, `triagem` (julgado só por juiz LLM) e `em_disputa` (dois revisores discordando sem adjudicação) **nunca** viram aceite. Fail-closed: uma taxa de sucesso que absorve dúvida é uma taxa inflada. O mesmo vale para `sem_nota` e `falta_segundo_revisor`.

O juiz LLM pode triar — e só isso. Nenhuma nota sem um humano assinando constitui gabarito (protocolo §5), e o juiz LLM não pode ser o mesmo executor.

### 2.4 Amostra de revisão dupla

25% dos aceites mecânicos (proposta do protocolo §5) são sorteados **com a seed registrada na chave** e exigem segundo revisor. Reprovados e indeterminados exigem segundo revisor sempre — o segundo resolve a rejeição ou a disputa. Sem o segundo veredito, o item fica `falta_segundo_revisor` e não conta.

## 3. Cegamento: o que o avaliador vê e o que não vê

O avaliador recebe, por item: **enunciado, patch, base (`sha`), categoria, escopo declarado e o veredito mecânico**. Recebe também a rubrica e o comando de aceitação, para reexecutar por conta própria na base limpa.

| Oculto no bundle | Onde fica |
|---|---|
| condição (`BASE`/`LEX-RS`/`CTX-RS`), política | chave, em custódia |
| modelo, provedor, versão, tokenizer | chave |
| custo, uso, bytes entregues, telemetria | chave |
| ordem e repetição | chave |
| caminho do workspace, do índice, do binário | não é copiado para lugar nenhum do bundle |
| `outcome`, `stopped_by`, `evidence_class` | só o veredito mecânico do item relacionado |

O bundle é **escaneado em duas severidades** antes de existir:

- **`hard` bloqueia a construção.** Rótulo de condição, `ATLAS_CONDITION`, nome do arquivo de custódia, e qualquer chave proibida (`condition`, `cost`, `model`, `usage`, `order`, `telemetry`, `run_id`, `tool`, `environment`…) em qualquer nível dos JSON do bundle.
- **`soft` é contado e declarado, não bloqueia.** Menção à própria ferramenta (`archatlas`, `atlas-read`) e a palavra `BASE` isolada. É a resposta honesta ao que o protocolo §5 chama de "estilo do patch pode revelar pistas": quando aparece, fica registrado no bundle e a acurácia do palpite de condição é medida no fim.

Consequência de leitura, escrita no próprio bundle: **o cegamento é simples, não duplo**. O avaliador não vê rótulos; o executor não está cego. Chamar isso de duplo-cego seria falso.

Dois detalhes de desenho que valem registro:

- **IDs opacos, ordem embaralhada, permutação reproduzível.** O id do item é um hash que não permite ler a condição; a ordem é sorteada com a seed registrada. A seed entra no id e no sorteio, então a mesma entrada e a mesma seed produzem o mesmo bundle — auditável — e uma seed diferente produz outro.
- **O bundle não é sobrescrito, e a chave não é sobrescrita.** Um bundle novo sobre o antigo invalidaria julgamentos em curso; a chave é material de custódia, não arquivo de trabalho.

## 4. Custódia da chave

Mesma disciplina do ouro no runner, pelo mesmo motivo: separação de diretório não é isolamento, mas **publicar o mapa** é pior.

- A chave é recusada se estiver dentro do diretório do bundle (ou contiver o bundle). Sem essa checagem, um `--key` distraído entregaria a condição de cada item.
- A chave registra `bundle_sha256`, o que **liga o julgamento ao bundle julgado**.
- `unblind` recusa abrir rótulos se o bundle tiver mudado depois da chave. Julgamento de um artefato não vale para outro.
- `--custodian` declara quem guarda a chave; sem ele o instrumento avisa que a chave está sem dono. Quem conserva chaves e tarefas finais é o custodiante independente (protocolo §5) — **não** os agentes que implementam Rust ou Bitcoin.
- A chave registra também os soft leaks, o ambiente e a amostra de 25%, e declara quando ela pode ser aberta: depois dos julgamentos e da adjudicação congelados.

## 5. Agregação: o que o relatório pode e não pode dizer

- **Unidade de inferência: tarefa.** Duas tentativas da mesma tarefa não são duas tarefas (pré-registro §1.2). O relatório publica as duas contagens — por tentativa e por tarefa — e o intervalo de confiança de R4 usa a tarefa como agrupamento.
- **`success_rate` inclui falhas no denominador.** Tentativa morta no teto, patch vazio, patch reprovado: tudo no denominador.
- **`cost_per_success` = custo de todas as tentativas / aceites.** Sem custo faturado, sai `null` **com motivo** (P2 pendente) — falta de custo bloqueia a conclusão e não vira zero. Com custo e zero aceites, sai `null` com o motivo "infinito, não um número".
- **Acurácia do palpite de condição** é publicada junto da taxa-base: se o avaliador acerta muito acima da base, o cegamento está furado, e isso é resultado sobre o instrumento. O campo diz, em texto, que embaralhar IDs não é resultado.
- **Nada de `--out` é conclusão.** O relatório carrega o aviso: sem modelo real, sem patch de modelo e sem rubrica aplicada por humano, nada ali é conclusão científica.

## 6. Evidência desta etapa

`pytest -q`: **103 passed, 4 skipped** (27 novos em [`tests/test_rust_eval.py`](../../tests/test_rust_eval.py)). O que os testes travam:

| Propriedade | Teste |
|---|---|
| mecânica tem precedência e separa itens M/H | `test_rubrica_separa_mecanica_de_semantica_com_precedencia` |
| caminhos do patch são lidos do artefato | `test_patch_paths_le_todos_os_arquivos_tocados` |
| `M1`/`M2` reprovam patch que não aplica | `test_check_aceita_tentativa_boa_e_reprova_que_nao_aplica` |
| `M4` reprova fora de escopo, `M5` teste imutável, `M6` teto | três testes dedicados |
| `/1` é recusado por não ter escopo declarado | `test_validate_recusa_schema_antigo...` |
| balanço 4/4/4/4 e `--allow-imbalance` | `test_validate_reprova_desbalanceado_sem_a_flag` |
| bundle sem condição/modelo/custo/ordem, varrido em todo arquivo | `test_bundle_nao_carrega_condicao...` |
| vazamento `hard` bloqueia e não escreve chave | `test_bundle_bloqueia_vazamento_duro...` |
| `soft` é declarado e não bloqueia | `test_bundle_registra_vazamento_suave...` |
| chave dentro do bundle é recusada; chave não é sobrescrita | dois testes |
| mesma seed → mesmo bundle; seed diferente → outro | `test_bundle_reproduzivel_com_a_mesma_seed` |
| escopo divergente entre manifesto e conjunto bloqueia | `test_bundle_recusa_manifesto_com_escopo_diferente...` |
| notas com rótulo de condição ou chave proibida são recusadas | `test_validate_scores_recusa...` |
| amostra de 25% sem segundo revisor não conta | `test_amostra_de_25_por_cento_exige_segundo_revisor...` |
| juiz LLM sozinho não vira gabarito | `test_juiz_llm_sozinho_nao_vira_gabarito` |
| disputa sem adjudicação não conta; com adjudicação conta | `test_disputa_sem_adjudicacao...` |
| bundle alterado depois da chave bloqueia o un-blind | `test_unblind_recusa_bundle_alterado...` |
| agregação por tentativa e por tarefa, custo ausente com motivo | `test_unblind_agrega_success_rate...` |
| custo por sucesso calculado e infinito declarado | dois testes |
| acurácia do palpite de condição | `test_unblind_mede_acuracia_do_palpite...` |
| pipeline completo no artefato real do runner (`dry`) | `test_integracao_runner_dry_ate_bundle_e_unblind` |

O último é o único que toca o runner de verdade: ele roda uma tentativa `dry`, roda `check`, constrói o bundle e abre os rótulos — provando que o formato do manifesto real atravessa a avaliação. O `dry` sai marcado `infrastructure_only`; ele valida a infraestrutura, não responde pergunta de utilidade.

Um defeito apareceu na própria primeira execução dos testes, e vale citação porque o instrumento pegou a si mesmo: o texto `declared_leak_channels` do bundle citava os rótulos de condição ao explicar os canais de vazamento — e o scanner de `hard` reprovou o bundle que ele mesmo gerou. A mensagem foi reescrita sem os rótulos. Um scanner que não reprovasse a própria documentação não estaria checando nada.

## 7. O que falta, e de quem depende

| Falta | Depende de |
|---|---|
| Tarefas reais (`atlas-tasks/2`) com enunciado, aceitação e origem | pesquisa (decisão do usuário) |
| Executar com modelo real | P1 (modelo) e P2 (teto financeiro), do usuário |
| Julgamento por revisores humanos e custodiante independente | papel da pesquisa (protocolo §5) |
| Intervalo de confiança e dimensionamento | R4, com os dados do piloto |
| Segundo revisor revisando a amostra de 25% | humanos; o instrumento só exige e registra |

Nada nesta lista é código que já se possa escrever sem inventar dado. A camada de avaliação, o runner e o harness de medição estão prontos; o que falta para R3 é o que o pré-registro §2 marca como pendente do usuário.
