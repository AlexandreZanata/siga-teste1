# Runner do piloto real — uma tentativa, um teto, sem acesso ao ouro

Data: 2026-09-29 (contrato do executor: 2026-10-02). ID: `RUNNER/1`. Estado: **implementado e ensaiado com executor declarado como infraestrutura e com executor `cmd` de contrato**; execução com modelo real **não** feita, bloqueada por P1/P2.
Depende de: [`PREREGISTRATION_R0.md`](PREREGISTRATION_R0.md) §1.1–1.4, [`PROTOCOLO_VALIDACAO.md`](PROTOCOLO_VALIDACAO.md) §§2–6, [`CLI_CONTRACT.md`](CLI_CONTRACT.md) §9.
Código: [`benchmarks/rust/runner.py`](../../benchmarks/rust/runner.py) e [`benchmarks/rust/executor_contract.py`](../../benchmarks/rust/executor_contract.py). Testes: [`tests/test_rust_runner.py`](../../tests/test_rust_runner.py) e [`tests/test_rust_executor_contract.py`](../../tests/test_rust_executor_contract.py).

Este documento existe porque o aceite de R2 inclui *"o runner captura todas as chamadas, custos e patches sem acesso ao ouro"* — a única parte do aceite que não depende de modelo nem de orçamento. Ele define o que o runner faz, o que ele mede por fora em vez de acreditar, e o que ele **não** garante.

## 1. O que uma execução é

Uma execução = **uma tentativa** de uma tarefa numa condição. O runner:

1. valida tarefa, condição e workspace (snapshot esperado, workspace novo por tentativa);
2. monta o ambiente e as ferramentas do executor;
3. roda o executor medindo-o **por fora** — parede, pico de RSS do processo, chamadas de ferramenta e leituras;
4. mata o grupo de processos no primeiro teto atingido;
5. captura o diff do workspace como patch candidato;
6. se uma base limpa for fornecida, aplica o patch e roda o comando de teste do avaliador;
7. escreve manifesto com nulos **com motivo** para tudo que ainda não existe.

O runner **não** cria o snapshot, **não** julga o patch, **não** abre o índice e **não** conhece o modelo. Julgamento é do avaliador cego (§5 do protocolo); aqui só se produz o patch e a telemetria.

## 2. Condições e o que difere entre elas

IDs do pré-registro §1.1: `BASE` (sem ferramenta de contexto), `LEX-RS` (CLI Rust, política lexical) e `CTX-RS` (mesma CLI, política de contexto com `expand`).

A única diferença entre braços é a **ferramenta de contexto**: em `BASE` o shim `atlas` não existe, e o manifesto registra `tool.absent_in_base: true` com `binary: null`. Os três braços recebem o mesmo leitor sancionado `atlas-read`, e isso é uma decisão deliberada, não um descuido: `opened` precisa ser medido do mesmo jeito nos três braços para ser comparável, e um leitor que apenas imprime conteúdo não é uma vantagem de recuperação. Sem ele, `BASE` não teria como produzir o evento e a comparação entre braços mediria instrumentação, não política.

## 3. Eventos: quatro nomes, quatro origens

O contrato §9 congela os nomes. Aqui, a origem de cada um:

| Evento | Origem | Nunca |
|---|---|---|
| `delivered` | bytes que o shim `atlas` **observou** passando para o agente | não é copiado do campo declarado pelo produto (esse vai ao lado, para conferência) |
| `opened` | evento emitido pelo leitor sancionado **antes** de imprimir | nunca derivado de `delivered` por fórmula — proibido pelo contrato §9 |
| `retrieved` | candidatos internos | `null` com motivo: o envelope não expõe a contagem interna |
| `declared_relevant` | relato do próprio agente | não é inferido do raciocínio nem do patch |

A regra que motivou tudo: um estudo que calcula `opened` a partir de `delivered` mede a fórmula, não a leitura. O teste `test_opened_zero_quando_nao_ha_leitura_mesmo_com_delivered` roda uma tentativa em que houve entrega e **nenhuma** leitura e exige `opened == 0`; e `test_integracao_com_o_binario_rust_de_verdade` exige que `delivered` medido pelo runner feche exatamente com `used_bytes` que o produto declara (mesma identidade de R2: `used_bytes == stdout − 1`).

Leituras fora do leitor sancionado (`cat`, editor, `git show`) **não** produzem evento e portanto não contam. Isso é uma limitação declarada do instrumento, não uma afirmação de que não ocorreram.

## 3b. Eventos do executor: o que só existe dentro do processo passa a ter forma

O shim cobre só o que passa por ele. Chamada de shell, edição, chamada de modelo e turno não
passam por `atlas-read` — sem contrato, elas não existem para o instrumento, e o teto de
"chamadas de ferramenta" mediria apenas uma parte das ferramentas. O contrato `atlas-executor/1`
([`executor_contract.py`](../../benchmarks/rust/executor_contract.py)) fecha isso. Mesmo stream do
shim, arquivo `ATLAS_EXECUTOR_TELEMETRY`, eventos com `"source": "executor"`:

| Evento | O que carrega | Por que existe |
|---|---|---|
| `model_call` | `request_id`, provider/id/version, tokens (entrada/saída/cache/reasoning), latência, status, erro, stop reason, custo da chamada | captura por chamada, sem total agregado solto |
| `tool_call` | ferramenta, argv, exit code, bytes de stdout | chamada que **não** passa pelo shim: shell, editor, outras. Entra no teto e no total |
| `turn` | índice do turno | turnos do modelo; destrava o teto de 40 turnos, que antes era `null` por falta de evento |
| `retry` / `error` | `of_request_id`, classe do erro | falha que não é chamada de modelo; retry contado uma vez |
| `stop` | motivo de parada | parada declarada, separada do motivo de parada do **runner** (`stopped_by`) |

**`opened` e os nomes `atlas`/`atlas-read` são reservados ao shim.** Evento com eles vindo do
executor é violação de contrato: não conta como leitura, não conta como observado, e a tentativa
deixa de poder ser `real`. Sem essa regra, o único número de leitura do piloto seria auto-relato.
Evento **sem** `source` também não passa por observado: entra no teto (conservador), é sinalizado
em `usage.unattributed_events` e derruba a afirmação de cobertura de chamadas — o aceite não
autoriza alegar contagem completa quando há evento de origem desconhecida.

O teto de chamadas conta `observadas + declaradas + rejeitadas`. Subdeclarar não rende chamada
extra: uma chamada que violou o contrato continua contando no teto. Bytes entregues, porém,
continuam vindo **só** do shim (`delivered_bytes`); o que o executor declara tem stdout, se
houver, fica ao lado (`declared_delivered_bytes`), para conferência, nunca somado.

## 4. Tetos: primeiro o teto, depois a tentativa

Valores do pré-registro §1.4, iguais nos três braços: **1800 s** de parede, **40** turnos do modelo, **100** chamadas de ferramenta por tentativa.

- O runner acompanha o stream de telemetria enquanto o executor roda e **mata o grupo de processos** (`killpg`) no primeiro teto atingido: a tentativa vira `outcome: stopped` e o processo retorna código não-zero. Continuar "só para terminar a etapa" é o que o protocolo §4 proíbe.
- Um executor rápido demais para ser interrompido no meio **não escapa**: se o teto só for detectável depois do fim, a tentativa continua sendo falha registrada, e `stopped_killed` diz se houve interrupção ou apenas detecção posterior. Um teto que pode ser ultrapassado por velocidade não é um teto.
- Chamadas de ferramenta incluem **leituras sancionadas**: o teto do protocolo é de "chamadas de ferramenta por tentativa", e ler um arquivo por uma ferramenta é uma. Contar apenas o `atlas` deixaria o braço `BASE` sem teto algum.
- **Turnos do modelo passaram a ser fiscalizáveis — quando declarados.** Com evento `turn`, o teto de 40 turnos vale como os outros: o runner mata o grupo de processos no primeiro estouro. Sem evento de turno, o campo é `null` com motivo (`turns_reason`) — não é zero, e o teto de turnos **não** é alegado como aplicado. Não existe mais caminho de código faltando para isso; o que falta é o executor emitir os eventos, o que o contrato §4b exige.

## 5. Separação do ouro

O runner faz o que consegue por caminho e declara o que não consegue:

**Checado**

- Diretório do ouro **dentro** do workspace (ou o inverso) → o runner recusa começar; nenhum artefato de tentativa é escrito.
- O caminho do ouro **não** entra no ambiente do executor.
- O caminho do ouro **não** entra no manifesto: ele é um artefato de tentativa, e o runner entrega o diretório de saída ao executor via `ATLAS_TELEMETRY`. O manifesto guarda apenas um identificador curto (`declared_dir_ref`) para conferir que é o mesmo diretório, sem entregar o mapa.

**Não coberto, e declarado como tal no manifesto**

- Mesmo usuário do sistema; mesmo `.git` e histórico do checkout; nenhum container/namespace. O pré-registro §4 já avisa que worktree não é isolamento: o executor pode ler o disco se souber o caminho. A checagem por caminho **não** é isolamento, e `gold_isolation.level` diz isso em todas as linhas.

Para R5 (confirmação cega) o requisito continua sendo **ambiente inacessível**, com o custodiante do holdout — não esta checagem.

## 4b. Result contract: identidade verificável, ou não é evidência

No fim da tentativa o executor escreve `ATLAS_EXECUTOR_RESULT` — `atlas-executor-result/1` — com
identidade do modelo, tokenizer, totais de uso, erros, retries, parada, custo e **cobertura por
métrica**. O runner então:

1. **valida a identidade**: `provider` + `id` + `version` + `verified_by` são obrigatórios. Nome
   informal de modelo não substitui nem completa o trio — sem ele, estado `violation` e a
   tentativa nunca é `real`;
2. **reconcilia** cada total do resumo com o **próprio stream** do executor (chamadas, tokens,
   ferramentas, turnos, erros, retries, custo). Divergência é violação, não empate: um dos dois
   lados está errado e o instrumento não escolhe qual;
3. **audita a cobertura declarada**: `observed: false` sem motivo escrito é violação — é o que
   impede confundir "não observado" com "observado e omitido";
4. **recusa cobrança dupla**: a mesma `request_id` reemitida não soma tokens nem custo de novo;
5. **mantém declarado e observado em campos separados**: `tool_calls_observed` vs
   `tool_calls_declared`, `delivered_bytes` vs `declared_delivered_bytes`, `opened` só do shim.

Estados, fail-closed: `ok` (contrato fechado → `evidence_class: real`), `partial` (cobertura
incompleta declarada — continua `real`, com as afirmações sem cobertura bloqueadas no manifesto
de capacidade §11), `missing` (sem result → `unverified`), `violation` (→ `contract_violation`,
nunca `real`) e `not_applicable` (executor `dry`).

O que a reconciliação prova é **consistência interna**: os totais são declarados pelo executor e
conferidos contra o stream dele. Nenhum total de provedor é medido por fora, e o manifesto diz
isso em `contract.provenance` em toda tentativa. Isso não é uma limitação a corrigir com mais
código aqui; é o limite do que um instrumento sem acesso à API de cobrança pode afirmar.

O loop também é fixado e conferível em duas camadas (NEXT-01). `executor.loop_config_sha256` (`atlas-loop-config/1`) reúne **só** o que é da rodada — espécie e hash do código do executor (`runner.py` + `executor_contract.py` + `real_executor.py`), protocolo de ferramentas (`atlas-tools/1`: shims + `TOOLS_SPEC`) e tetos — sem caminhos e sem enunciado: mesmo loop em diretórios distintos produz o mesmo hash, e mudança de código, ferramenta ou teto muda o hash. `--expect-loop-config-sha` recusa iniciar fora da configuração fixada. `executor.loop_sha256` continua existindo como identidade da **tentativa** (comando efetivo + enunciado, instável entre diretórios por construção); `--expect-loop-sha` o confere por compatibilidade. Enunciado e caminhos ficam em campos próprios (`prompt.statement_sha256`, `executor.cmd`, `executor.task_identity`), e a conferência de "mesma tarefa entre braços" é por tarefa+enunciado, nunca pelo hash do loop.

## 6. Manifesto mínimo, com nulos e motivo

O protocolo §6 pede um manifesto por run. O que ainda não existe sai `null` **com motivo**, nunca zero:

| Campo | Estado hoje |
|---|---|
| `model.provider/id/version/verified_by` | declarados no result contract; sem o trio completo **e** o `verified_by`, o estado é `violation` e a tentativa nunca é `real`. P1 continua pendente para *escolher* o modelo, não para representá-lo |
| `tokenizer.id` | declarado no result; `null` com motivo quando o executor não informa (P3) |
| `cost.provider_billed` / `currency` | declarados no result **com `source`**; `null` com motivo quando não há cobrança observada — o protocolo proíbe inventar tarifa (P2) |
| `usage.turns` | deixa de ser `null` quando o executor emite evento `turn`; com evento, o teto é fiscalizável. Sem evento, `null` com motivo |
| `usage.tokens/latency_ms/errors/retries/model_calls` | do stream declarado; `null` por campo não informado — nunca 0 |
| `contract.*` | estado, violações, reconciliação e cobertura por métrica (§4b) |
| `usage.retrieved_candidates` | `null` com motivo: o envelope não expõe candidatos internos |
| `tool.index_generation` | `null` com motivo: o runner não abre o índice |
| `acceptance.*` | `null` com motivo quando não há base limpa |
| `prompt.tool_specs_sha256` | `null` com motivo: as descrições são do executor |

Preenchidos de verdade: `snapshot.base_sha` e `tree_sha256` do workspace, `tool.binary_sha256`, `limits`, `usage.wall_s`, `usage.tool_calls` (observadas + declaradas + rejeitadas), `usage.tool_calls_observed/declared/rejected`, `usage.opened`, `usage.delivered_bytes`, `executor.loop_sha256`, `cost.local_peak_rss_kb`, `cache`, `order`, `timestamps`, `processes`, `patch`, `stopped_by`, `outcome`, `evidence_class`.

Nenhum campo ausente vira zero; nenhum campo desconhecido é omitido.

**NEXT-01, sempre preenchidos:** `executor.loop_config_sha256` + `executor.loop_config` (rodada), `executor.cmd_template` + `executor.task_identity` (tentativa), `preflight.workspace` (SHA completo, HEAD, limpeza) + `preflight.overlay`, `acceptance.state` + `acceptance.test_command_sha256` + HEADs da base + `deps` + `restored`. O avaliador lê `acceptance.state` para separar `patch_fault` de `environmental` (detalhe em [`AVALIACAO_CEGA.md`](AVALIACAO_CEGA.md) §2.1).

## 7. Executor `dry`: infraestrutura, nunca evidência

O executor `dry` usa as ferramentas de verdade (chama `atlas` e o leitor, edita um arquivo) sem modelo. Serve para provar que a captura funciona.

- Ele **não** roda sem `--allow-dry`: um stub não pode ser confundido com execução real.
- Todo run com ele sai `evidence_class: infrastructure_only`, com o motivo escrito no manifesto.
- O que ele valida: contagem de chamadas, evento `opened`, `delivered` medido, captura e aplicação de patch, tetos, separação do ouro e — desde a TASK-A02 — o caminho do stream declarado, com um evento `stop` de infraestrutura que exercita a leitura do contrato.
- O que ele **não** valida: qualquer coisa sobre utilidade, custo de provedor ou qualidade de patch. Nenhum resultado de R3 pode vir dele. Como o `dry` não escreve result contract, ele sai `contract.state: not_applicable` e `infrastructure_only` — nunca `real`, nunca `unverified`: o ensaio de infraestrutura não é uma tentativa de contrato malfeito.

## ## 4c. Preflight fechado e falhas distintas (NEXT-01)

**Preflight do workspace, antes do executor** (recusa sem manifesto, nada rodou ainda): HEAD presente, `base_sha` da tarefa em SHA completo (40 hex, comparação exata — prefixo de 8 não fixa base) e árvore rastreada limpa. O overlay imutável (`immutable_paths`) é identificado no manifesto (`preflight.overlay`); quem o fiscaliza é M5.

**Preflight da base de aceitação, depois do executor** (falha vira estado no manifesto, sem culpar o patch): HEAD presente, base limpa e dependências do `test_command` conferidas **antes** de aplicar. Falta comprovada (`deps_missing`) não aplica o patch; base suja ou sem HEAD vira `env_blocked`. Após o teste a base é restaurada (`reset --hard` + limpeza dos caminhos do patch) — nunca reutilizar base modificada; a tentativa seguinte exige base limpa.

**Estados do aceite**, mesma regra nos três braços: `passed`, `patch_regression`, `apply_failed`, `empty_patch`, `deps_missing`, `env_blocked` (exit 3, reservado ao harness), `acceptance_timeout`, `acceptance_error`, `no_base`. Timeout escreve manifesto + log parcial e restaura a base em vez de travar o runner. O hash do comando (`test_command_sha256`) e os HEADs antes/depois ficam no manifesto, junto do binário Rust (`tool.binary_sha256`). Custos/retries do executor continuam registrados em qualquer estado.

## 8. O que os testes guardam

13 testes do runner, 13 do instrumento fechado (NEXT-01) e 17 do contrato do executor
([`tests/test_rust_executor_contract.py`](../../tests/test_rust_executor_contract.py)), sem rede,
sem modelo e sem depender do binário Rust (exceto o de integração, pulado se o binário não estiver
construído). Os do contrato cobrem: agregação de tokens/custo/latência/erro/retry, `request_id`
repetida não cobrando duas vezes, evento reservado como violação, evento sem `source`, validação do
result (identidade incompleta, cobertura sem motivo, schema, stop), reconciliação separando
`mismatch` de `missing`, manifesto de capacidade bloqueando afirmação sem cobertura, os dois
adaptadores de provedor contra as fixtures sintéticas, e — pelo runner de verdade com executor
`cmd` — contrato fechado (`real`), sem result (`unverified`), teto de shell declarada, teto de
turnos, divergência stream×result, leitura fabricada, `--expect-loop-sha` recusando e o loop
idêntico nos três braços.

Testes do runner:

| Teste | O que impede |
|---|---|
| `dry` sem `--allow-dry` | stub virar artefato de tentativa |
| ouro dentro do workspace | tentativa começar com ouro alcançável |
| ambiente e artefatos sem o caminho nem o conteúdo do ouro | vazamento de solução por ambiente ou por manifesto |
| `opened` com leitura real | evento de leitura não sendo capturado |
| `opened == 0` apesar de `delivered > 0` | a fórmula proibida (derivar `opened` de `delivered`) |
| teto de chamadas e teto de parede | teto que não para a tentativa, ou que para sem registrar motivo |
| turnos nulos com motivo | ausência de dado virando zero |
| patch capturado, aplicado em base limpa, teste com exit 0 | patch que não é o que o executor produziu |
| sem base limpa → aceite nulo com motivo | conclusão de sucesso sem teste |
| manifesto mínimo + `infrastructure_only` | run de stub passando por evidência real |
| `BASE` sem ferramenta de contexto | braço de controle recebendo a intervenção |
| integração com o binário real | `delivered` medido divergindo do declarado pelo produto |
| executor `cmd` com contrato fechado | total declarado virando evidência sem reconciliação |
| executor sem result contract | ausência de identidade/custo virando `real` ou zero |
| stream divergente do result | dois lados discordando sem que nada acuse |
| leitura fabricada pelo executor | `opened` virando auto-relato |
| teto de shell declarada e teto de turnos | chamadas fora do shim escapando do teto |
| `--expect-loop-sha` divergente | braço mudando de loop sem que a rodada pare |
| config estável entre caminhos, instável com teto novo | caminho temporário virando "mudança de loop" falsa, ou teto mudando sem deixar rastro |
| preflight recusando SHA curto/HEAD ausente/base suja | tentativa medindo a base errada sem ninguém perceber |
| timeout/env/dep sem culpar o patch | falha de infra virando rejeição de patch (ou sucesso), ou base modificada reutilizada |

## 9. O que falta para R3

1. **Executor e modelo** (P1): o contrato (§3b–§4b) está implementado e ensaiado, inclusive com
   adaptadores para as duas famílias de API mais prováveis e fixtures de formato. Falta o insumo
   que é decisão do usuário: qual provedor/modelo, e a captura **real sanitizada** que substitui a
   fixture sintética. O loop do executor precisa emitir os eventos do contrato; nenhum código de
   contabilidade falta para recebê-los.
2. **Testes de aceitação por tarefa** e rubrica congelada, no ambiente do avaliador.
3. **Base limpa por tarefa** para o passo de aceite (`--acceptance-repo`), e o snapshot de base por tentativa.
4. **Teto financeiro** (P2) para o custo de provedor deixar de ser `null`.
5. **Cegamento**: o avaliador recebe enunciado, base, patch e rubrica, sem condição/modelo/custo/ordem (protocolo §5).

Nenhum desses itens é código de infraestrutura pendente: são insumos de decisão e de avaliação.

## 10. Estado do gate

| Item | Planejado | Implementado | Ensaiado | Executado |
|---|---|---|---|---|
| Runner de tentativa | x | **x** | **x** (13 testes + integração com o binário real) | — (P1/P2) |
| Captura de eventos (§3) | x | **x** | **x** | — |
| Tetos (§4) | x | **x** | **x** (inclui teto de shell declarada e de turnos) | — |
| Contrato do executor (§3b–§4b) | x | **x** | **x** (17 testes, executor `cmd` de verdade) | — (nenhum executor com modelo) |
| Separação do ouro (§5) | x | **x** | **x** (por caminho) | — (R5 exige ambiente inacessível) |

"Ensaiado" aqui significa: infraestrutura exercitada com executor declarado como stub, com um
executor `cmd` de contrato e com o binário real. **Não** significa que exista qualquer resultado
de utilidade — nenhuma tentativa com modelo ocorreu, e a conclusão científica segue `não avaliada`.

## 11. Manifesto de capacidade: o que uma tentativa pode afirmar

Além do manifesto, cada tentativa escreve `capability_manifest.json`
(`atlas-executor-capacity/1`), com três listas: o que é **observado por fora** (parede, RSS,
eventos do shim, patch, exit code do aceite), o que é **declarado pelo executor** (identidade,
tokens, latência, erro/retry, ferramentas fora do shim, turnos, custo) e o que **não é coberto**
(leitura fora do leitor sancionado, chamadas internas não emitidas, custo sem tarifa oficial,
qualidade do patch). Cada afirmação tem um veredito `supported` com o motivo:

| Afirmativa | Sustentada quando |
|---|---|
| `custo_faturado_do_provedor` | existe `cost.provider_billed` com `currency` e `source`, e a reconciliação bate |
| `tokens_do_modelo` | existem tokens no stream ou no result, reconciliados |
| `contagem_de_chamadas_de_ferramenta_em_todas_as_ferramentas` | todo evento tem `source` (nenhum sem origem) |
| `turnos_do_modelo` / `teto_de_chamadas_aplicado` | há evento de turno / cobertura completa de chamadas |
| `teto_de_parede_aplicado` | sempre: a parede é medida por fora, com kill do grupo de processos |
| `patch_do_executor_capturado` | sempre: o diff do workspace é capturado antes de qualquer julgamento |
| `reducao_de_leituras_totais_do_agente` | **nunca** neste instrumento: só o leitor sancionado emite evento, e `cat`/editor/`git show` não deixam rastro |
| `isolamento_do_ouro` | **nunca** com checagem por caminho: R5 exige ambiente inacessível |
| `custo_por_sucesso` | **nunca** aqui: depende do aceite cego e de custo faturado |

O manifesto de capacidade existe para que a ausência de cobertura não vire silêncio: em vez de
um número que parece medido, fica escrito o que não foi observado e por quê. Uma tentativa com
contrato `partial` continua `real` — mas nenhuma afirmativa sem cobertura entra no relatório.

## 12. Executor real (P1/P2): `benchmarks/rust/real_executor.py`

O contrato `atlas-executor/1` e o `dry` já existiam; faltava o comando que
**realmente chama um modelo**. O executor real é um loop de agente autocontido
(só stdlib), com as três ferramentas básicas fixas — `shell`, `read`, `write` —
iguais nos três braços, tetos do pré-registro §1.3/§1.4 (2 000 tokens de saída,
40 turnos, 100 chamadas de ferramenta) e telemetria evento a evento. Ele escreve
também o `atlas-executor-result/1`, reconciliável com o stream por construção.

Contrato de comando (o runner invoca; nunca à mão na rodada):

```bash
ATLAS_EXECUTOR_TELEMETRY=<att>/stream.jsonl ATLAS_EXECUTOR_RESULT=<att>/result.json \
ATLAS_API_KEY=<segredo> python benchmarks/rust/real_executor.py \
  --statement-file <att>/statement.md --dir <workspace> \
  --provider anthropic --model <id> --prices benchmarks/rust/prices.json
```

- **Preço obrigatório:** sem tabela por-1M do modelo (`prices.json`, formato em
  `prices.example.json`) o executor sai 2 e **não** escreve resultado — custo
  não é estimado por chute. Com tabela, o custo é reconciliado com o tarifário
  oficial que o P2 fixa.
- **Identidade verificável:** `model.version`/`verified_by` vêm do echo da API
  (`response.model`). Echo ausente ou divergente marca `coverage.model_identity:
  false` (MISMATCH) — o rótulo `real` exige contrato fechado, não nome informal.
- **Ausência nunca vira zero:** sem chave, sem enunciado, sem telemetria/result,
  ou sem preços, saída 2 sem resultado. Erro de auth para o loop
  (`stop.reason: auth_error`); erro de API transitório faz retry contado, cada
  tentativa com `request_id` próprio (reemissão do mesmo id não é nova chamada).
- **Reconciliado por construção:** stream e result saem do mesmo acumulador, então
  `StreamAccounting` + `reconcile` não acusam divergência no caminho feliz —
  por isso o teste de integração fecha.

Provado offline (sem rede, sem chave): `tests/test_rust_real_executor.py`, 9 testes
com transporte sintético — caminho feliz, retry→sucesso, auth, echo divergente,
tetos de turnos e ferramentas, recusa sem preços, matemática de custo exata e
não-emissão de nomes reservados. O que continua **pendente do usuário (P1/P2)**:
modelo efetivo, chave e teto financeiro; sem eles a rodada smoke não começa.
