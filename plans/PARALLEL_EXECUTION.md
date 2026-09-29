# Execução paralela — agente SIGA e agente Bitcoin

Data: 2026-09-24. Estado: protocolo documentado; esta revisão não inicia agentes, cria worktrees ou executa experimentos.

**Emenda de 2026-09-29:** seguir o [plano CLI Rust e piloto real](RUST_CLI_PILOTO_REAL.md) como próxima sequência. A mantém exclusivamente `rust/**`, `research/rust/**`, `plans/rust/**`, `benchmarks/rust/**` e `experiments/rust/**`; B mantém os namespaces Bitcoin, incluindo suas tarefas e resultados da CLI Rust. B consome o binário/contrato publicado por A, com índice próprio, e solicita extensões ao core sem editar o workspace Cargo. Não criar duas implementações concorrentes do core. Worktree Bitcoin já observada em `codex/bitcoin-context` no checkpoint `3623afb`: verificar o estado corrente antes de qualquer preparação, sem reiniciar ou recriar o checkout. Regras de isolamento e checkpoints abaixo continuam vigentes.

## 1. Decisão e precedência

Por solicitação do usuário, SIGA e Bitcoin passam a executar **as mesmas etapas P0–P7 e técnicas E26-00–E26-06 em paralelo**, cada um com suas próprias dependências, evidências e critérios de aceite. Bitcoin não espera a conclusão do SIGA. Este protocolo substitui instruções antigas de “Bitcoin só depois do SIGA”, branch `exp/bitcoin` e troca de branch dentro do checkout compartilhado.

Ordem de leitura: este protocolo → plano do agente → experimento corrente → fontes necessárias. Método científico comum: [plano principal](PESQUISA_CONTEXTO_MODULAR.md), [experimentos canônicos](EXPERIMENTOS_2026.md) e [papers de 2026](../research/16_BASE_EXPERIMENTAL_2026.md). Em isolamento, propriedade de arquivos e integração, este protocolo prevalece. Em tarefas específicas, usar a trilha correspondente; em métricas e cegamento, manter o método comum.

Entradas dos agentes:

- **Agente A, SIGA e manutenção do core:** [SIGA_EXECUTION.md](SIGA_EXECUTION.md).
- **Agente B, Bitcoin:** [BITCOIN_PARALLEL_PLAN.md](BITCOIN_PARALLEL_PLAN.md) e [espelho dos experimentos](bitcoin/EXPERIMENTOS_2026.md).

Não duplicar fisicamente a bibliografia ou as regras estatísticas: registrar o commit e hash dos documentos comuns em cada manifesto. Igualdade das técnicas significa mesmos fatores, controles e critérios; tarefas, linguagem, build, custos e resultados são específicos de cada dataset.

## 2. Retomar o que existe

Na inspeção desta revisão havia `research/AUDIT_BASELINE.md`, `research/PREREGISTRATION.md` e trabalho de contratos/telemetria P2 no checkout principal. São artefatos SIGA/core, não prova de conclusão Bitcoin. Agente A verifica seu estado corrente e continua da primeira pendência, sem reiniciar P0 nem descartar trabalho em andamento.

Agente B começa em BTC-P0. Pode ler especificações e bibliografia publicadas pelo A, mas não copiar gabaritos, soluções ocultas ou declarações de etapa concluída. Arquivos não commitados do A não são uma dependência estável para B.

## 3. Isolamento de Git e diretórios

Cada agente precisa de **checkout/worktree, branch de escrita e diretório de execução distintos**. Duas branches no mesmo diretório não isolam arquivos. Nunca usar `git checkout`, `switch`, `reset`, `clean`, stash ou rebase no diretório do outro agente.

Configuração compatível com o trabalho atual:

- A mantém o checkout e a branch atuais durante a etapa em andamento, inclusive se for `main`. Só A escreve/commita ali. Migração futura para `codex/siga-context` exige checkpoint e nenhuma operação do A em andamento; não é requisito para B começar.
- B usa uma worktree própria e branch `codex/bitcoin-context`, criada a partir de um commit base publicado. Nunca escrever na `main` ou no checkout de A.
- Não criar segunda worktree com a mesma branch de escrita. Se o nome já existir, verificar o dono e o diretório registrados antes de reutilizar; não apagar nem resetar.

Preparação futura, pelo responsável A, sem incluir alterações de implementação alheias:

1. Publicar um checkpoint **somente da documentação revisada**, selecionando paths explicitamente e inspecionando o diff staged. Se já houver outros arquivos staged, não misturá-los. Este planejamento não faz o commit automaticamente.
2. Registrar `DOCS_SHA` e o commit inicial `BASE_SHA` acessível ao B. O core desse commit pode ser anterior a P2; declarar capacidades disponíveis.
3. Criar a worktree B em caminho próprio. Exemplo de comando a preencher, não executado nesta revisão: `git worktree add -b codex/bitcoin-context <DIRETORIO_BTC> <BASE_SHA>`. Não usar branch mutável como identidade experimental.
4. Na worktree B, confirmar `git rev-parse --show-toplevel`, `git branch --show-current`, SHA e estado inicial. Configurar venv/dependências locais sem reutilizar instalação editable do A.
5. Registrar em `research/bitcoin/WORKSPACE.md` os identificadores e caminhos relativos/aliases; caminhos absolutos locais ficam em configuração não versionada. A registra os seus em `research/siga/WORKSPACE.md` quando abrir esse registro.

Os documentos precisam estar disponíveis no checkpoint usado por B. Não presumir que arquivos novos não commitados aparecem em uma nova worktree. Se a preparação de Git ainda faltar, B pode planejar em sessão separada, mas não deve editar a árvore de A para adiantar implementação.

## 4. Propriedade dos arquivos

**A é o único escritor do core comum:** arquivos existentes em `archatlas/`, exceto o namespace Bitcoin abaixo; testes comuns; dependências/packaging; CI; configuração compartilhada; documentos canônicos em `plans/` e `research/`. A também mantém `benchmarks/siga/**`, `experiments/agent_ab/**`, `experiments/siga/**`, `research/siga/**`, `plans/siga/**` e relatórios SIGA legados.

**B é o único escritor dos namespaces Bitcoin:**

- `archatlas/bitcoin/**` — adaptadores e wrappers exclusivos de C++/Bitcoin, inicialmente novos e sem modificar inicializadores comuns;
- `tests/bitcoin/**` — testes isolados, incluindo fixtures próprias;
- `benchmarks/bitcoin/**` — PIN, censo, tarefas públicas/dev e manifestos sem ouro final;
- `experiments/bitcoin/**` — relatórios sanitizados e metadados por execução;
- `research/bitcoin/**` — auditoria, pré-registro, contratos locais, pedidos ao core e decisões;
- `plans/bitcoin/**` — espelho específico, estado e checkpoints.

B pode ler o core e o método comum. Não altera diretamente `archatlas/capsule.py`, `harness.py`, `store.py`, `config.py`, `cli.py`, `pyproject.toml`, CI ou testes comuns. Se um experimento pedir essas alterações, usar extensão local ou pedido ao A; nunca copiar o core inteiro para manter um fork oculto.

Os pontos de entrada `plans/BITCOIN_PARALLEL_PLAN.md`, `plans/SIGA_EXECUTION.md` e este protocolo ficam sob manutenção de A durante execução. B propõe ajustes em `research/bitcoin/requests/`. A não altera namespace Bitcoin sem o checkpoint/handoff de B. A integração final é uma atividade temporária de A, não exige terceiro agente permanente.

## 5. Como compartilhar mudanças no core

1. B cria pedido `research/bitcoin/requests/BTC-CORE-NNN.md`: contrato necessário, reprodução mínima sem holdout, versão base, comportamento esperado, compatibilidade e testes de aceite. B publica o commit do pedido e avisa A pelo canal da tarefa; um arquivo local isolado não é notificação automática.
2. A lê o commit/patch sem trocar a branch de B. Registra resposta em `research/integration/BTC-CORE-NNN.md` no próprio checkout: aceito, alternativa ou pendente, interface/versão e commit de entrega. São arquivos diferentes, com donos distintos.
3. A implementa a mudança geral e roda os testes comuns e SIGA pertinentes. B continua trabalho independente: fixtures C++, tarefas dev, build, auditoria ou wrappers; a falta do contrato bloqueia apenas a etapa dependente.
4. Entre rodadas, com a worktree B limpa e checkpoint registrado, B incorpora **o SHA publicado** pelo método combinado (`cherry-pick` de commits de core isolados ou merge do checkpoint comum). Não sincronizar continuamente nem usar pull/rebase automático durante medição.
5. B verifica regressões Bitcoin. Core/adaptador/schema mudaram? Criar novo `run_id` e registrar mudança. Não substituir dados de uma rodada anterior nem reusar seu rótulo como se a configuração fosse igual.

Para trazer Bitcoin à linha principal, B publica commits que tocam somente seus namespaces e A integra em um checkpoint sem rodada ativa. Executar a suíte comum e as duas suítes específicas; testes de build dependentes de ambiente ausente ficam explicitamente pendentes. Conflito textual/semântico é resolvido pelo dono da área, sem aceitar automaticamente “ours/theirs”.

Cada experimento declara `track`, `method_revision`, `core_sha`, `adapter_sha`, `dataset_sha`, `policy_hash`, `schema_version` e árvore efetiva. Mesmo método com implementações diferentes é adaptação comparável sob ressalvas, não resultado diretamente pareado entre datasets. Comparação cruzada forte exige core/política compatíveis e verificações de contrato em ambas as trilhas.

## 6. Isolamento de execução

Defaults do código atual podem apontar para SIGA e `/tmp/opencode/`. Não os herdar no Bitcoin. Passar dataset e DB explicitamente quando a API oferecer; senão usar variável **somente no processo**. `ARCHATLAS_DATASET_BTC` será alias do launcher planejado, não variável reconhecida automaticamente pelo core atual. Não alterar profile de shell ou configuração global.

Planejar runtime por trilha e rodada, por exemplo `$TMPDIR/archatlas-siga/<run_id>/` e `$TMPDIR/archatlas-bitcoin/<run_id>/`. Cada uma tem SQLite/WAL, caches, logs, builds, checkout editável da tarefa, diretório temporário dos testes e processos próprios. Venv e import path devem apontar para a worktree correta. Não compartilhar DB gravável, build-dir, datadir, sockets ou serviço de proxy.

Dataset base fica somente leitura; edições experimentais ocorrem em cópias/checkout descartáveis por tarefa, fora do corpus do índice e sem histórico futuro acessível ao executor. Builds de Bitcoin são externos à cópia base e obedecem as instruções do SHA escolhido. Processos de teste, portas e caches funcionais precisam ser isolados por rodada. Cleanup encerra somente PIDs registrados pela própria execução.

**Paralelo no desenvolvimento; isolamento nas medições de desempenho.** Compilação C++, JVM, GPU ou inferência simultâneas podem invalidar comparação de latência. Reservar CPU/RAM/GPU e registrar limites por trilha; se não houver isolamento verificável, serializar trechos de benchmark com um mutex comum do host, por exemplo `flock` em `/tmp/archatlas-benchmark-host.lock`, provisionado no setup. Enquanto um mede, o outro faz trabalho que respeite a reserva. Nunca remover lock de processo vivo.

Chamadas ao mesmo provedor compartilham cotas. Definir limites e teto financeiro por trilha e registrar concorrência/throttling. Índices e literatura podem ser preparados em paralelo; dobrar trilhas não autoriza dobrar gastos. Duas rodadas de 72–120 execuções totalizam 144–240 antes de ablações, se ambas forem autorizadas e tiverem ambiente.

## 7. Independência científica

BTC-Pn depende das etapas BTC anteriores e de um contrato de core utilizável, **não de SIGA-Pn concluída**. SIGA também não espera Bitcoin. A/B/C/D, budgets 2k/8k, métricas, ablações e margens são equivalentes por protocolo, com pré-registros independentes.

Os dois agentes de implementação não se tornam automaticamente avaliadores cegos um do outro. Holdouts, testes ocultos e chave de condições ficam em ambiente de avaliação segregado. Compartilhar correções de infraestrutura e falhas dev é permitido; compartilhar resultados finais para retuning contamina o teste. Se o core for ajustado depois de abrir qualquer holdout, a nova configuração precisa de nova confirmação, sem reutilizar o mesmo teste como inédito.

Como Bitcoin agora participa do desenvolvimento, seus resultados não provam transferência para repositório nunca usado em ajuste. Reservar outros repositórios para H5/P6 do produto geral. Dentro da trilha Bitcoin, tarefas/snapshots posteriores não usados no ajuste avaliam evolução temporal, não generalização entre projetos. Reportar resultados por trilha/modelo, sem somar médias Java/C++ como uma única vitória.

## 8. Checkpoints e comunicação

Cada agente mantém seu próprio `plans/<track>/STATUS.md` com etapa, último aceite, SHA, execução ativa, bloqueio exato, pedido pendente e próximo passo. Não editar um quadro compartilhado simultaneamente. O status canônico de uma etapa vem das evidências do dono, não de checkboxes copiados.

Notificações mínimas entre tarefas: pedido ao core publicado; contrato entregue; início/fim de reserva de recursos; candidato congelado; checkpoint pronto para integração. Sem mecanismo automático de mensagens, o responsável repassa o ID e SHA; nenhum agente deve presumir que o outro acompanha arquivos da sua worktree.

Definição operacional de “sem conflito”: sem escrita cruzada, sem estado de execução compartilhado e sem atualização de dependência no meio de rodada; mudanças comuns são integradas em checkpoints. Isso reduz conflitos evitáveis, mas integração ainda exige revisão.
