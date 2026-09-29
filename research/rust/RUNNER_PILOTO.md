# Runner do piloto real — uma tentativa, um teto, sem acesso ao ouro

Data: 2026-09-29. ID: `RUNNER/1`. Estado: **implementado e ensaiado com executor declarado como infraestrutura**; execução com modelo real **não** feita, bloqueada por P1/P2.
Depende de: [`PREREGISTRATION_R0.md`](PREREGISTRATION_R0.md) §1.1–1.4, [`PROTOCOLO_VALIDACAO.md`](PROTOCOLO_VALIDACAO.md) §§2–6, [`CLI_CONTRACT.md`](CLI_CONTRACT.md) §9.
Código: [`benchmarks/rust/runner.py`](../../benchmarks/rust/runner.py). Testes: [`tests/test_rust_runner.py`](../../tests/test_rust_runner.py).

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

## 4. Tetos: primeiro o teto, depois a tentativa

Valores do pré-registro §1.4, iguais nos três braços: **1800 s** de parede, **40** turnos do modelo, **100** chamadas de ferramenta por tentativa.

- O runner acompanha o stream de telemetria enquanto o executor roda e **mata o grupo de processos** (`killpg`) no primeiro teto atingido: a tentativa vira `outcome: stopped` e o processo retorna código não-zero. Continuar "só para terminar a etapa" é o que o protocolo §4 proíbe.
- Um executor rápido demais para ser interrompido no meio **não escapa**: se o teto só for detectável depois do fim, a tentativa continua sendo falha registrada, e `stopped_killed` diz se houve interrupção ou apenas detecção posterior. Um teto que pode ser ultrapassado por velocidade não é um teto.
- Chamadas de ferramenta incluem **leituras sancionadas**: o teto do protocolo é de "chamadas de ferramenta por tentativa", e ler um arquivo por uma ferramenta é uma. Contar apenas o `atlas` deixaria o braço `BASE` sem teto algum.
- **Turnos do modelo não são fiscalizáveis por fora.** Se o executor não emitir eventos de turno, o campo é `null` com motivo (`turns_reason`) — não é zero, e o teto de turnos não é alegado como aplicado. Fechar isso exige que o executor reporte turnos, o que é parte do contrato do executor em R3.

## 5. Separação do ouro

O runner faz o que consegue por caminho e declara o que não consegue:

**Checado**

- Diretório do ouro **dentro** do workspace (ou o inverso) → o runner recusa começar; nenhum artefato de tentativa é escrito.
- O caminho do ouro **não** entra no ambiente do executor.
- O caminho do ouro **não** entra no manifesto: ele é um artefato de tentativa, e o runner entrega o diretório de saída ao executor via `ATLAS_TELEMETRY`. O manifesto guarda apenas um identificador curto (`declared_dir_ref`) para conferir que é o mesmo diretório, sem entregar o mapa.

**Não coberto, e declarado como tal no manifesto**

- Mesmo usuário do sistema; mesmo `.git` e histórico do checkout; nenhum container/namespace. O pré-registro §4 já avisa que worktree não é isolamento: o executor pode ler o disco se souber o caminho. A checagem por caminho **não** é isolamento, e `gold_isolation.level` diz isso em todas as linhas.

Para R5 (confirmação cega) o requisito continua sendo **ambiente inacessível**, com o custodiante do holdout — não esta checagem.

## 6. Manifesto mínimo, com nulos e motivo

O protocolo §6 pede um manifesto por run. O que ainda não existe sai `null` **com motivo**, nunca zero:

| Campo | Estado hoje |
|---|---|
| `model.provider/id/version` | `null` — P1 pendente (decisão do usuário) |
| `tokenizer.id` | `null` — P3 pendente |
| `cost.provider_billed` / `currency` | `null` — P2 pendente; o protocolo proíbe inventar tarifa |
| `usage.turns` | `null` com motivo quando o executor não emite turnos |
| `usage.retrieved_candidates` | `null` com motivo: o envelope não expõe candidatos internos |
| `tool.index_generation` | `null` com motivo: o runner não abre o índice |
| `acceptance.*` | `null` com motivo quando não há base limpa |
| `prompt.tool_specs_sha256` | `null` com motivo: as descrições são do executor |

Preenchidos de verdade: `snapshot.base_sha` e `tree_sha256` do workspace, `tool.binary_sha256`, `limits`, `usage.wall_s/tool_calls/opened/delivered_bytes`, `cost.local_peak_rss_kb`, `cache`, `order`, `timestamps`, `processes`, `patch`, `stopped_by`, `outcome`, `evidence_class`.

Nenhum campo ausente vira zero; nenhum campo desconhecido é omitido.

## 7. Executor `dry`: infraestrutura, nunca evidência

O executor `dry` usa as ferramentas de verdade (chama `atlas` e o leitor, edita um arquivo) sem modelo. Serve para provar que a captura funciona.

- Ele **não** roda sem `--allow-dry`: um stub não pode ser confundido com execução real.
- Todo run com ele sai `evidence_class: infrastructure_only`, com o motivo escrito no manifesto.
- O que ele valida: contagem de chamadas, evento `opened`, `delivered` medido, captura e aplicação de patch, tetos, separação do ouro.
- O que ele **não** valida: qualquer coisa sobre utilidade, custo de provedor ou qualidade de patch. Nenhum resultado de R3 pode vir dele.

## 8. O que os testes guardam

13 testes, sem rede, sem modelo e sem depender do binário Rust (exceto o de integração, que é pulado se o binário não estiver construído):

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

## 9. O que falta para R3

1. **Executor e modelo** (P1): o ID/provedor/versão e o loop que emite turnos.
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
| Tetos (§4) | x | **x** | **x** | — (turnos dependem do executor) |
| Separação do ouro (§5) | x | **x** | **x** (por caminho) | — (R5 exige ambiente inacessível) |

"Ensaiado" aqui significa: infraestrutura exercitada com executor declarado como stub e com o binário real. **Não** significa que exista qualquer resultado de utilidade — nenhuma tentativa com modelo ocorreu, e a conclusão científica segue `não avaliada`.
