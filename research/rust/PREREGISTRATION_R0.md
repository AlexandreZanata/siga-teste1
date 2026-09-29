# Pré-registro do piloto — R0, ainda não selado

Data: 2026-09-29. ID: `PREREG_R0/1`. Estado: **pré-registro escrito; nenhuma rodada executada; nenhum orçamento autorizado**.
Depende de: [`../plans/RUST_CLI_PILOTO_REAL.md`](../../plans/RUST_CLI_PILOTO_REAL.md) §6, [`PROTOCOLO_VALIDACAO.md`](PROTOCOLO_VALIDACAO.md), [`CLI_CONTRACT.md`](CLI_CONTRACT.md), [`BASELINE.md`](BASELINE.md).
Core no momento: `db3e714`. Worktree Bitcoin: `3623afb`.

Este documento existe para que R3–R5 **não** ajustem hipótese depois de ver resultado. Ele congela o que já pode ser congelado agora e nomeia explicitamente o que ainda não pode.

O que este arquivo **não** faz, por decisão: não estima tamanho de amostra nem sela o confirmatório. O protocolo (§4) é explícito: o piloto não requer as estimativas do próprio piloto. Dimensionamento e selo final vêm depois do piloto, em documento próprio.

## 1. O que está congelado agora

### 1.1 Condições (3, nomes novos — não renomeiam A/B/C/D históricos nem `D_bm25`)

| ID | Condição | Ferramenta de contexto |
|---|---|---|
| `BASE` | Agente com shell, busca, leitura, edição e testes usuais | nenhuma |
| `LEX-RS` | Mesmo agente + `archatlas` Rust, BM25, empacotamento fixo | CLI Rust, política lexical |
| `CTX-RS` | Mesmo agente + mesma CLI/índice, política de seleção + `expand` | CLI Rust, política de contexto |

Invariantes que valem para as três: mesmo modelo, mesmo executor/loop, mesmas ferramentas básicas, mesmo snapshot inicial, mesmos tetos operacionais, mesma unidade de amostra. A única diferença é a disponibilização e a política de contexto — e o custo delas, que entra na conta.

`BASE vs CTX-RS` responde se a ferramenta vale sobre o fluxo usual. `LEX-RS vs CTX-RS` responde se a política modular acrescenta algo sobre busca lexical simples. Os dois braços Rust compartilham serialização, tokenizer e limites: tratamento não pode receber só um transporte mais rápido.

### 1.2 Unidades e integridade

- Unidade de inferência: **tarefa**, com tentativas agrupadas. Repetição não é tarefa independente.
- 4 tarefas de smoke × 3 condições × 1 repetição = **12 runs por trilha**.
- 16 tarefas de piloto × 3 condições × 2 repetições = **96 runs por trilha**.
- Cada tarefa pertence a **uma** categoria primária (bug local / mudança entre arquivos / testes-comportamento-de-API / configuração-interface), para evitar contagem dupla.
- Balanço do piloto: 4/4/4/4.

### 1.3 Budget de saída

**2 000 tokens**, escolhido no smoke e congelado antes do piloto. O alternativo de 8 000 vira ablação posterior, não braço extra — multiplicar budgets multiplicaria custo sem isolar causa.

Histórico relevante medido nesta etapa: a referência Python **satura em 50 unidades**, então pedir 8 000 não entrega 8 000 tokens (`BASELINE.md` §4). AJustes de orçamento precisam ser medidos sobre a resposta entregue, nunca sobre a configuração pedida.

### 1.4 Limites operacionais (tetos, não dimensionamento)

Até 30 min de parede, 40 turnos de modelo e 100 chamadas de ferramenta por tentativa; builds/testes com timeout próprio documentado. Iguais nos três braços. Alteração de qualquer um vale para **todos** os braços, antes do piloto.

O runner para no primeiro teto atingido e registra a tentativa como falha. Ele não continua gastando para "terminar a etapa".

### 1.5 Critérios do confirmatório (pré-especificados, ainda não dimensionados)

Sucesso: limite inferior do IC95% de `sucesso(candidato) − sucesso(baseline)` **> −0,05**. Custo: limite superior do IC95% de `custo_por_sucesso(candidato) / custo_por_sucesso(baseline)` **< 0,80**. Ambos precisam pasar para alegar economia ≥20% com qualidade preservada dentro da margem.

Não inferioridade não é identidade de qualidade. Se a evidência ou a potência ficarem insuficientes, o resultado é **inconclusivo** — não se alarga a margem depois de ver os dados.

## 2. O que NÃO está congelado, e por quê

| Item | Estado | Desbloqueia |
|---|---|---|
| Modelo efetivo (ID/provedor/versão) | pendente do usuário | smoke |
| Teto financeiro e moeda | pendente do usuário | smoke |
| Tokenizer exato do modelo | dependente do modelo; senão modo bytes | contagem rígida |
| Custodiante do holdout | pendente do usuário | R5 |
| Tamanho de amostra do confirmatório | depende das estimativas do piloto | R4 |
| Custo máximo da confirmação | depende de P2 | R4 |
| Consolidação de custos e reservas | protocolo paralelo | execução |

Escrever estimativas aqui seria inventar número. Cada célula fica `null` com motivo, conforme o protocolo §6.

## 3. Checklist de medição independente (R2)

Antes de qualquer alegação de "Rust é mais rápido", **todos** os itens precisam ser verdes. Item vermelho significa resultado não publicável, não resultado ruim.

**Correção antes de comparação**

- [ ] Mesma política, mesmo corpus, mesmas entradas canônicas nos dois lados.
- [ ] Mesmo limite aplicado sobre a **serialização inteira**, não sobre itens.
- [ ] Referências re-verificadas nos bytes do snapshot antes de entregar texto.
- [ ] Incremental ≡ rebuild em lógica, para `edit`, `delete` e `rename`.
- [ ] Arquivos novos, exclusões e troca de branch tratados.
- [ ] DB incompleto/corrompido → diagnóstico, nunca JSON de sucesso.
- [ ] Caminho fora da raiz do repo → rejeitado.
- [ ] Concorrência: um escritor por índice, leitores isolados, crash/lock testados.
- [ ] Falha nunca apaga outro índice nem produz resposta vazia fingida.

**Medição**

- [ ] Release com toolchain e flags pinadas; `Cargo.lock` versionado.
- [ ] Lotes pareados Python/Rust em ordem alternada.
- [ ] 30 consultas estratificadas × 10 repetições aquecidas por implementação.
- [ ] 10 execuções de `index` em diretórios exclusivos, para dispersão.
- [ ] Tempo medido do comando externo até consumir stdout (spawn incluído).
- [ ] wall, CPU user+system, pico de RSS **incluindo subprocessos**, page faults, bytes lidos/escritos, tamanho de índice/WAL/binário, tempo de instalação.
- [ ] Query com muitos matches, zero matches, Unicode, arquivo gigante, índice obsoleto, lock e crash — separadas. Não otimizar só a query favorável.
- [ ] "Frio" em duas dimensões reportadas separadamente: índice ausente vs. cache de filesystem frio. Processo novo não é cache frio; se o cache não puder ser derrubado sem máquina dedicada, declarar **não medido**.

**Só então**

- [ ] Comparar release padrão contra variantes guiadas por perfil (ex.: LTO thin) **após** o perfil apontar o gargalo.
- [ ] Otimização só é promovida se preservar correção e cobertura declarada.
- [ ] Metas não atendidas registradas com o número, não omitidas nem arredondadas.

## 4. Riscos que este pré-registro não elimina

- **Contaminação de tarefas públicas.** Tarefas tiradas de issues abertas podem já estar no treino do modelo. Registrar origem e risco por tarefa; preferir problema genuíno revisado independentemente.
- **Worktree não é isolamento.** Mesma máquina, mesmo repo, mesmo `.git` — o executor pode alcançar ouro por `git log`, `git stash`, reflog ou worktree vizinha. Ouro e testes ocultos exigem ambiente separado, não diretório separado.
- **Estilo do patch vaza condição.** Registrar suspeita quando o avaliador notar indício; não chamar o estudo de duplo-cego.
- **Bitcoin bloqueado no ambiente.** RAM disponível (~4,9 GiB) e dependências de build não resolvidas. H3 (transferência) fica `não avaliada` até BTC-P2, e não se infere conclusão de SIGA para Bitcoin.
- **Derivar `opened` de `delivered`.** Já detectado na auditoria anterior; o contrato §8 proíbe e o runner tem que capturar o evento de leitura real.

## 5. Estado do gate

| Gate | Planejado | Implementado | Ensaiado | Executado | Avaliado | Conclusão científica |
|---|---|---|---|---|---|---|
| R0 | x | x | x | — | — | não avaliada |
| R1 | x | — | — | — | — | não avaliada |
| R2 | x | — | — | — | — | não avaliada |
| R3 | x | — | — | — | — | não avaliada |
| R4 | x | — | — | — | — | não avaliada |
| R5 | x | — | — | — | — | não avaliada |
| R6 | x | — | — | — | — | não avaliada |

R0 está documentado e verificado; "implementado" em R0 significa contrato e medição definidos, **não** código de produto. Nenhuma execução real ocorreu. Nenhuma conclusão de utilidade existe até R5.

Próxima ação: **R1**, sem depender de modelo, orçamento ou custodiante.
