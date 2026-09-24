# ArchAtlas — plano de pesquisa para contexto modular reutilizável

Data: 2026-09-24. Estado: planejamento; nenhuma etapa abaixo foi executada nesta revisão.

Atualização bibliográfica de 2026: [base experimental com nove papers](../research/16_BASE_EXPERIMENTAL_2026.md) e [sete experimentos ligados à primeira entrega para devs](EXPERIMENTOS_2026.md). Inclui trabalhos publicados até 22/09/2026, consultados em 24/09/2026. Fontes e propostas foram documentadas; experimentos permanecem não executados.

## 1. Objetivo e autoridade deste plano

Investigar se uma camada local de seleção de contexto permite que agentes resolvam tarefas reais de desenvolvimento com menor custo total e qualidade preservada. O produto pretendido é instalável em diferentes repositórios, com capacidades declaradas por linguagem e ferramenta. “Qualquer projeto” é uma direção de produto, não uma propriedade já demonstrada.

Este documento orienta as próximas etapas após F20 e detalha F21. Em conflitos sobre sequência, métricas, modelos, cegamento ou generalização, prevalece sobre os rascunhos anteriores de pesquisa e implementação. F0–F20 e os relatórios existentes permanecem como histórico; suas conclusões não são automaticamente confirmação científica. O PIN vigente continua sendo a referência do dataset SIGA.

Escopo desta revisão: documentação de pesquisa e execução futura. Não implementar módulos, executar benchmarks, chamar modelos pagos, alterar datasets, publicar ou fazer commit/push como consequência automática deste planejamento.

## 2. Ponto de partida observado

Inspeção de arquivos, sem reexecutar resultados:

- Já existem extração, SQLite, busca lexical, cápsulas, estratégias e harness em `archatlas/`. Reaproveitar a base antes de propor uma reescrita.
- `archatlas/capsule.py::count_tokens` usa `len(text)//4`. O orçamento contabiliza itens selecionados, não toda a resposta serializada nem o histórico do agente. Logo, “hard budget” atual não comprova limite real de tokens do modelo.
- `archatlas/harness.py::run` chama de `recall` a proporção de perguntas com algum arquivo esperado recuperado. Para conjuntos usa `any(...)`; isso não mede recall completo de arquivos nem recuperação integral de caminhos. Possui SHA e módulos SIGA fixos.
- `archatlas/strategies.py::s_router` encerra a cascata ao encontrar pelo menos três arquivos. Quantidade de arquivos não é evidência de contexto suficiente para editar corretamente.
- O extrator Java em `archatlas/extract.py` usa regex. Nome presente na linha e hash correto demonstram localização/proveniência, mas não comprovam resolução semântica de chamadas. Os valores `confidence` não foram tratados aqui como probabilidades calibradas.
- `experiments/agent_ab/RESULTS.md` registra seis perguntas de desenvolvimento, empate em acerto e baseline mais rápido no lote. `BLIND4.md` registra limitações do gabarito e mistura tempos de consulta com tempo do agente. Não extrapolar esses resultados para economia ponta a ponta.
- `benchmarks/siga/PIN.md` descreve Java 21, branch `desenvolvimento`, SHA `e3be22828f787cbe71b339aecb7a7bf569099803`. Referências antigas a Java 8/`develop` precisam ser reconciliadas.

Essas observações definem a auditoria inicial. Não são resultados de um novo benchmark nem uma auditoria completa do código.

## 3. Pergunta central e hipóteses

Pergunta: dado o mesmo modelo, tarefa, snapshot, ferramentas básicas e limites operacionais, a seleção modular de contexto diminui o custo por tarefa resolvida sem perda relevante de qualidade?

- **H1, utilidade:** ArchAtlas reduz custo por tarefa resolvida, mantendo taxa de sucesso dentro da margem de não inferioridade registrada antes do teste.
- **H2, seleção:** carregamento progressivo orientado pela tarefa melhora a relação entre sucesso e tokens totais frente a uma cápsula fixa e a BM25 simples.
- **H3, estrutura:** relações verificadas acrescentam valor em tarefas entre arquivos; seu custo não se justifica automaticamente em tarefas locais.
- **H4, manutenção:** atualização incremental preserva equivalência lógica com reconstrução completa e reduz custo em mudanças pequenas.
- **H5, transferência:** contratos e políticas congelados continuam úteis em projetos não usados no ajuste. Medir separadamente transferência para outro repositório e para outra linguagem.

Resultado negativo ou inconclusivo é uma saída válida. Não selecionar apenas categorias ou modelos em que a proposta vence.

## 4. Literatura inicial e como combiná-la

As seis referências abaixo são fundamentos de 2023–2025. A prioridade experimental atual vem da [base de 2026](../research/16_BASE_EXPERIMENTAL_2026.md): FeatLens, CliffCompaction, Harness Design, Thousand-Graph, Recall Trap, Agent Retrieval Bench, SWE-Pruner Pro, ContextBench e SWE-Pruner. As fichas identificam versões, seções consultadas, artefatos e limitações; o [roteiro E26-00–E26-06](EXPERIMENTOS_2026.md) define os testes locais.

Para os fundamentos abaixo, foram consultadas páginas primárias e resumos em 2026-09-24. Nos trabalhos de 2026 também foram consultadas seções metodológicas e páginas de artefatos conforme as fichas. Leitura integral, auditoria executável e reprodução não estão concluídas. As sugestões de aplicação são hipóteses nossas, não resultados transferidos dos papers.

1. **RepoCoder — Zhang et al., 2023.** Recuperação e geração iterativas para completar código em repositórios. Inspira buscar contexto novamente quando a tarefa revela dependências. Experimento: uma busca versus expansão iterativa com limite. Limite da transferência: completar código difere de corrigir uma aplicação. [Paper](https://arxiv.org/abs/2303.12570).
2. **Repoformer — Wu et al., ICML 2024.** Recuperação seletiva, incluindo evitar buscas desnecessárias. Inspira uma política que pode escolher não expandir. Comparar seleção determinística e, apenas como braço opcional, seleção por modelo; uma heurística não será chamada de reprodução do mecanismo treinado do paper. [Publicação](https://proceedings.mlr.press/v235/wu24a.html).
3. **RepoGraph — Ouyang et al., ICLR 2025.** Estrutura de repositório como componente integrável a sistemas de engenharia de software. Inspira separar representação, navegação e agente consumidor. Experimento: mesmo recuperador com e sem relações. Persistência, custo incremental e utilidade no SIGA precisam de avaliação própria. [Paper](https://arxiv.org/abs/2410.14684).
4. **Agentless — Xia et al., 2024.** Fluxo explícito de localização, reparo e validação. Inspira um controle simples para separar qualidade do contexto de complexidade de orquestração. Não comparar números publicados diretamente com nossos modelos/datasets. [Paper](https://arxiv.org/abs/2407.01489).
5. **SWE-bench — Jimenez et al., ICLR 2024.** Avaliação de patches para problemas reais em repositórios. Inspira tarefas executáveis com snapshot anterior à solução e testes independentes. Seus resultados não substituem avaliação Java/JSP ou de nossos projetos. [Paper](https://arxiv.org/abs/2310.06770).
6. **Lost in the Middle — Liu et al., 2023/2024.** Sensibilidade à posição de informação em contexto longo nas tarefas estudadas. Inspira controles de ordem, tamanho e distratores; não demonstra que menos contexto sempre melhora agentes atuais. [Paper](https://arxiv.org/abs/2307.03172).

A combinação candidata é: representação navegável + seleção opcional + expansão progressiva + validação por execução. Cada componente deve ter uma hipótese e uma ablação; juntar papers não constitui novidade por si só.

Na revisão integral, completar as fichas com artefatos pinados, licenças e custo real de reprodução. A base de 2026 já registra consultas, critérios e evidência contrária às premissas do projeto. Os dois alvos iniciais são Agent Retrieval Bench e CliffCompaction, condicionados à disponibilidade de artefatos e controle do histórico; o roteiro E26 prevê alternativa quando essa integração não existir. Distinguir reprodução fiel, adaptação e inspiração.

O catálogo anterior em `research/02_RELATED_WORK.md` contém afirmações de novidade, custos e candidatos ainda sem verificação suficiente nesta revisão. Nenhum deles sustenta decisões até passar pela ficha acima; ausência de informação não significa ausência da capacidade no trabalho relacionado.

## 5. Arquitetura a investigar

“Entender o que a LLM quer” será operacionalizado como interpretar uma solicitação explícita, o estado observável da tarefa e pedidos de expansão. Não há acesso à intenção interna do modelo nem garantia de encontrar o contexto mínimo perfeito.

Fluxo proposto: solicitação → plano de busca → recuperação de evidências → pacote de contexto → ação do agente → resultado observável → eventual expansão.

### Contratos mínimos, antes de diretórios novos

- **Snapshot do repositório:** identificador, SHA base, hashes dos arquivos atuais, estado de alterações locais, versão dos extratores e capacidades disponíveis. Um SHA isolado não representa a árvore após edições do agente.
- **Adaptador de linguagem:** descobre e extrai fatos com localização, origem e limitações. Suporte lexical é um nível válido; resolução de tipos/chamadas exige evidência específica. Relações incertas permanecem candidatas.
- **Armazenamento e atualização:** fatos, dependências e invalidação. Mudança, exclusão e renomeação invalidam também relações/cache dependentes; comparar conteúdo lógico com rebuild, sem exigir identidade binária do SQLite.
- **Solicitação de contexto:** objetivo (`localizar`, `entender`, `editar`, `testar`, `impacto`), consulta, símbolos/arquivos conhecidos, snapshot, contexto já entregue e orçamento restante. Permitir `desconhecido`, ambiguidades e busca ampla.
- **Política de seleção:** escolhe recursos pela tarefa e evidência disponível; saída inclui razões observáveis, limites e necessidade de expansão. Regras determinísticas primeiro; classificador LLM opcional, isolado e cobrado no experimento.
- **Recuperadores intercambiáveis:** lexical, símbolos, relações, testes, configuração e documentação. Evitar carregar automaticamente todos. Embeddings só como baseline/extensão com custo de construção e atualização medido.
- **Montador de contexto:** evidências citáveis, trechos suficientes para entender contratos e dependências, deduplicação, orçamento da serialização inteira, itens omitidos e limitações. Resumos por LLM, se estudados, serão derivados e nunca substitutos silenciosos de código verificável.
- **Adaptador do agente:** API/CLI primeiro; MCP fino depois de demonstrada utilidade. Não embutir regras de negócio no transporte. Acesso normal a leitura/busca continua disponível e é medido.
- **Avaliador separado:** consome logs e patches; gabaritos, testes ocultos e rótulos de condições não entram no índice nem no contexto do executor.

### Carregamento progressivo

1. Disponibilizar um mapa pequeno de capacidades e orientações indispensáveis do projeto, com seu custo contabilizado.
2. Recuperar arquivos/símbolos prováveis e contratos relevantes para a solicitação.
3. Acrescentar implementações, testes, configurações ou relações quando houver uma necessidade observável: referência não resolvida, arquivo insuficiente, erro de build/teste ou pedido explícito do agente.
4. Encerrar por suficiência avaliada na ação, limite de recursos ou falta de evidência; permitir fallback de busca/leitura e reportar lacunas.

Exemplo a testar: alteração de validação backend pode começar por método e contrato, depois expandir para callers e testes. Alteração visual pode precisar de JSP, estilos, scripts e validação visual. Esses roteiros são candidatos; palavras-chave não garantem escopo completo.

O adaptador controla o que entrega, mas não apaga mensagens já presentes no histórico do cliente. Separar tamanho da cápsula, contexto acumulado e tokens faturados. Deduplicação, sessões novas e eventual compactação devem ter políticas explícitas e ser iguais entre condições quando não forem a variável estudada.

## 6. Desenho experimental

### Condições e comparabilidade

Começar com três braços: **A**, agente com busca/leitura convencionais; **B**, mesmo agente com BM25 e trechos sob orçamento; **C**, mesmo agente com ArchAtlas atual, congelado. Só depois adicionar **D**, ArchAtlas modular com expansão progressiva. Isso separa o valor existente do valor da proposta.

Mesma tarefa, snapshot inicial, modelo exato, parâmetros suportados, ferramentas básicas, ambiente de execução, limites totais e regra de término por bloco. Variam apenas a disponibilização/política do contexto e seu custo inevitável. Não restringir artificialmente leitura do baseline ou do tratamento. Acesso à cápsula não pode vir acompanhado de dicas extra sobre a solução.

Reiniciar sessão e workspace entre execuções; alternar ordem das condições em blocos aleatórios por tarefa/modelo. Separar índice frio/quente de cache do provedor. Seeds só quando suportadas; temperatura zero não é garantia de determinismo. Mudança silenciosa de versão do modelo cria outro bloco experimental.

Duas avaliações complementares: (a) recursos operacionais iguais, comparando sucesso e consumo; (b) curvas por orçamento total, comparando eficiência. Budget da cápsula é um fator separado do budget total da execução.

### Tarefas e separação de dados

Primeiro SIGA, sem reabrir a implementação Bitcoin nesta fase. Piloto proposto: 12–20 tarefas executáveis, cobrindo backend, frontend e alterações entre arquivos. É calibração do protocolo, não amostra suficiente por definição para comprovar ganhos.

Cada tarefa terá problema independente da solução, snapshot base, ambiente reproduzível, comportamento esperado, testes públicos, critérios ocultos, timeout e classe de dificuldade definida antes de observar o desempenho. Incluir tarefas simples em que o índice pode custar mais do que ajuda. Perguntas de localização continuam como diagnóstico secundário.

Para bugs, demonstrar que o teste de aceitação falha antes e passa com uma solução válida. Para funcionalidades/UI, validar que os critérios distinguem ausência e presença da funcionalidade. Não exigir igualdade textual com patch de referência. Compilar, verificar regressões e revisar semântica; screenshot isolado não comprova comportamento.

Separar desenvolvimento, validação e teste final por famílias de tarefas/áreas de mudança; não dividir aleatoriamente perguntas quase idênticas. Nenhuma tarefa já usada em F0–F20 conta como teste inédito. Gabaritos independentes do extrator evitam avaliar o sistema pela própria saída.

Tarefas históricas usam checkout anterior ao patch. Bloquear acesso a commits futuros, soluções, resultados e testes ocultos. Isso não garante ausência de memorização no treinamento; registrar essa limitação e incluir tarefas recentes/inéditas quando disponíveis.

### Teste cego operacional

O executor inevitavelmente percebe algumas ferramentas disponíveis. Portanto, o desenho é **avaliação cega de patches com condições randomizadas**, não promessa de duplo-cego completo.

Um custodiante humano ou processo segregado guarda tarefas finais, testes ocultos e chave de condições fora do workspace e do índice dos executores. Hash de manifesto registra o congelamento, mas não controla acesso sozinho. O agente que ajusta o recuperador não lê o holdout. Se a mesma sessão já viu soluções, usá-las apenas no desenvolvimento.

Patches recebem IDs aleatórios; avaliadores recebem tarefa, snapshot, patch e rubrica, sem modelo, condição, custo ou ordem. Registrar possíveis pistas de descegamento. Divergências de revisão vão para adjudicação independente antes de abrir os rótulos. Julgamento por LLM pode auxiliar, mas não é a única medida de correção.

Abrir o teste uma vez por candidato congelado. Falha descoberta depois não autoriza retuning e nova alegação de teste inédito no mesmo conjunto: registrar emenda e usar novo holdout. Se faltar ambiente ou custodiante, concluir preparação e marcar o confirmatório pendente.

### Métricas e critério de decisão

Primária de qualidade: proporção de tarefas resolvidas conforme testes de aceitação, regressão e rubrica semântica, no limite de recursos registrado. Reportar também sucesso na primeira tentativa e tentativas/retrabalho. Testes insuficientes limitam a conclusão.

Primária de eficiência: custo total de todas as tentativas dividido pelo número de tarefas resolvidas. Incluir falhas, planejamento de contexto, chamadas auxiliares, indexação e manutenção amortizadas. Se nenhuma tarefa for resolvida, a métrica é indefinida/infinita, nunca zero. Registrar custo de API e infraestrutura separadamente; só combiná-los com regra de conversão explícita.

Secundárias: tokens de entrada/saída/cache/reasoning conforme telemetria disponível, tempo ponta a ponta p50/p95, chamadas de ferramentas, arquivos/bytes lidos, regressões e intervenções humanas. Não somar campos de tokens que o provedor já contabiliza conjuntamente. Preços, moeda, data e origem devem acompanhar estimativas; campo indisponível permanece desconhecido.

Diagnóstico de recuperação: hit de algum arquivo esperado, recall e precisão do conjunto, relações corretas, caminho completo, utilidade para o patch e evidências obsoletas. Usar nomes distintos; um acerto parcial não vira recall 100%.

Proposta inicial de ganho prático, a congelar após o piloto e antes do holdout: economia de pelo menos 20% no custo por tarefa resolvida e margem máxima de perda de 5 pontos percentuais na taxa de sucesso. São escolhas de produto, não valores derivados dos papers. Para concluir sucesso, exigir limite inferior do IC95% da diferença de sucesso acima de −5 pontos e limite superior do IC95% da razão de custos abaixo de 0,80. Caso a amostra não sustente isso, resultado inconclusivo; não interpretar “sem significância” como equivalência.

Dimensionar a amostra confirmatória com taxa de sucesso, discordâncias pareadas e variabilidade de custos do piloto, margem e potência alvo de 80%. Repetições da mesma tarefa não são novas tarefas independentes. Usar inferência pareada com agrupamento por tarefa; em transferência, reportar por repositório/modelo e explicitar a incerteza com poucos projetos. Pré-registrar bootstrap/estimadores, análise de não inferioridade, família de comparações e correção de multiplicidade. Não escolher o melhor braço olhando o teste final.

Reportar falhas de infraestrutura, timeouts e falhas do produto separadamente. Timeout ou crash causado pelo tratamento conta contra ele. Retry de indisponibilidade externa segue regra simétrica definida antes; manter logs de todas as tentativas e análise de sensibilidade, sem descartar silenciosamente casos desfavoráveis.

### Custos e volume de execuções

Piloto inicial: 12–20 tarefas × 3 condições × 2 repetições × 1 modelo = 72–120 execuções. O total não autoriza gastos agora. Estimar custo com smoke tests futuros e fixar teto financeiro/temporal antes da rodada.

Não multiplicar imediatamente três modelos, vários budgets e todas as ablações. Primeiro depurar o protocolo; depois selecionar configurações no desenvolvimento; por último replicar o candidato congelado nos modelos e projetos restantes. Medir custo frio, custo quente e custo amortizado para 1, 10 e 100 tarefas. Break-even existe apenas se a economia por tarefa superar a manutenção; reportar quando não existir.

## 7. Experimentos de mecanismo e ablações

Executar conforme as [fichas E26-00–E26-06](EXPERIMENTOS_2026.md): medir primeiro, testar empacotamento, comparar entidades com relações, avaliar foco/poda e depois histórico/interface. Os papers de 2026 acrescentam controles sem grafo, abstenção com evidência e profundidade de trechos do mesmo arquivo. Não executar todas as combinações por padrão.

Executar primeiro no desenvolvimento, alterando um fator por comparação:

- BM25 versus BM25 + relações, com mesmo montador e budget.
- Cápsula fixa versus expansão progressiva, cobrando toda nova consulta e mensagem.
- Política por regras versus seleção opcional por LLM, incluindo custo e erros de interpretação.
- Trechos brutos versus resumos derivados, preservando referências e medindo perda de informação.
- Com/sem testes, configuração e documentação, por classe de tarefa.
- Com/sem deduplicação, e controles de ordem/distratores no contexto.
- Índice frio/quente e atualização incremental versus rebuild após edição, exclusão, renomeação e troca de branch.

Controles diagnósticos: contexto irrelevante de mesmo tamanho e contexto selecionado por especialista. O segundo é um teto aproximado, isolado dos braços de produto e dos executores sem acesso ao gabarito. Testar também nomes ambíguos, código dinâmico, dependências externas ausentes, linguagens não suportadas e índices obsoletos.

Não transportar ao teste toda uma busca combinatória. Registrar quantas variantes foram tentadas e replicar apenas hipóteses selecionadas previamente. Ganho de uma combinação não prova contribuição de cada componente.

## 8. Etapas pequenas para os agentes de execução

Executores previstos pelo usuário: **Muse Spark 1.3**, **DeepSeek Flash v4.1** ou **Luna 6 do ChatGPT**. Os nomes são rótulos fornecidos, não confirmação de disponibilidade ou IDs de API. Antes de cada rodada, resolver provedor, ID/versão efetivos, interface, parâmetros, contexto máximo e telemetria. Se não disponíveis, registrar impedimento; não trocar silenciosamente de modelo.

Separar modelo usado para desenvolver o ArchAtlas do modelo avaliado como consumidor. Não tratar os três como um único agente equivalente nem agregar resultados sem estratificação. Cada microetapa deve caber em uma sessão com objetivo único e artefato verificável, sem depender de lembrança da conversa.

### P0 — auditoria do ponto de partida

Entrada: código atual, relatórios F0–F20, PIN e este plano. Saída futura: `research/AUDIT_BASELINE.md`, relacionando afirmação, implementação, evidência disponível, limitação e correção necessária. Auditar bibliografia, contagem de tokens, hit/recall, tempo total, provenance e gabaritos. Aceite: toda alegação central classificada como observada, reproduzida ou pendente; nenhum resultado antigo renomeado silenciosamente. Sem refatoração nesta etapa.

### P1 — revisão de literatura e pré-registro preliminar

Depende de P0. A seleção inicial e as fichas de nove papers estão em `research/16_BASE_EXPERIMENTAL_2026.md`; os experimentos, em `plans/EXPERIMENTOS_2026.md`. Isso é progresso documental, não conclusão de P1. Completar leitura e auditoria de artefatos e produzir `research/PREREGISTRATION.md` preliminar. Fixar hipóteses, comparadores, métricas, rubricagem, política de falhas e lacunas de ambiente. Aceite: cada escolha metodológica tem fonte ou justificativa experimental; novidade permanece hipótese.

### P2 — contratos e infraestrutura de medição

Depende de P1. Saídas futuras: especificação dos contratos, telemetria, replay e tarefas smoke. Só então implementar o mínimo necessário ao comparativo A/B/C. Corrigir rótulos métricos, medir payload inteiro e isolar avaliador/executor. Aceite: execuções simuladas não faturadas verificam pareamento, orçamento, isolamento e registro de erros; smoke real depende de modelo e teto definidos. CLI de harness descrita em planos antigos não deve ser presumida existente.

### P3 — piloto de edição real no SIGA (F21)

Depende de P2 e ambiente executável. Saídas: manifestos, logs brutos e relatório do piloto A/B/C. Aceite: tarefas com critérios válidos, custos completos e diagnóstico de falhas. Se qualidade/telemetria forem insuficientes, corrigir o método e repetir no desenvolvimento, sem alegar confirmação.

### P4 — protótipo modular mínimo e ablações

Depende de P3. Implementar apenas contratos necessários para substituir a política e montar contexto progressivo, reaproveitando módulos atuais. Introduzir D, reproduções selecionadas e ablações prioritárias. Saída: um candidato congelado e registro das variantes descartadas. Aceite: evidência de desenvolvimento justifica cada componente; remover complexidade sem benefício demonstrável.

### P5 — avaliação confirmatória cega

Depende de P4. Antes de executar: completar pré-registro com dimensão amostral, teto de gasto, modelos exatos, snapshots, pesos, prompts, limites, estatística e manifesto selado. Saídas: avaliação cega, intervalos, resultado positivo/negativo/inconclusivo e limitações. Aceite: protocolo íntegro e conclusão proporcional à evidência, mesmo sem ganho. Não ajustar candidato após abrir o teste.

### P6 — transferência e portabilidade

Depende de P5 para a trilha de produto; achado negativo pode abrir novo ciclo de pesquisa explicitamente separado. Selecionar antes do teste pelo menos dois repositórios externos ao SIGA, com builds reproduzíveis e tarefas independentes: um em linguagem já suportada, outro em stack diferente com demanda real da equipe. Não considerar apenas o próprio ArchAtlas como validação externa.

Congelar core/políticas. Ajustar adaptadores em fixtures/dev próprios, sem olhar tarefas finais. Distinguir suporte lexical básico de suporte estrutural completo. Bitcoin é candidato opcional posterior, não próximo passo obrigatório. Saídas: matriz de capacidades, desempenho por projeto e catálogo de falhas. Aceite de generalização: instalação/configuração documentada, sem regras especiais escondidas para cada tarefa; regressões e adaptações publicadas.

### P7 — piloto de uso por desenvolvedores e decisão de produto

As jornadas, o contrato de CLI futuro e os critérios de instalação/atualização/fallback estão detalhados em [E26-06 e primeira fatia implementável](EXPERIMENTOS_2026.md). Priorizar a ferramenta local de consulta e expansão; compactação de histórico e filtros neurais têm capacidades e dependências separadas.

Depende de evidência favorável e limitada ao escopo validado. Planejar instalação reversível, atualização, migração de schema, modo sem índice e diagnóstico de cobertura; adaptador MCP só se necessário ao fluxo real. Medir tempo de configuração, intervenções, tempo de revisão e retrabalho em tarefas distintas, com ordem contrabalanceada para evitar efeito de aprendizagem.

Saídas: pacote experimental versionado, guia de suporte e decisão manter/simplificar/reprojetar. “Pronto para uso” exige ganhos reproduzidos, manutenção mensurada e limitações claras. Publicação científica e implantação ampla vêm após esses resultados, sem compromisso antecipado com superioridade.

## 9. Registro e passagem entre sessões

Cada microetapa futura registra: ID e dependências; uma pergunta; arquivos de entrada; fontes; arquivos permitidos para alteração; comandos previstos e realmente executados; critérios de aceite; resultados/erros; hashes; decisão e próximo passo. Estados: `planejada`, `em_execucao`, `concluida`, `bloqueada`, `inconclusiva`. Código implementado e hipótese validada são estados diferentes.

Entregar ao próximo executor apenas este resumo, contratos necessários e ponteiros para evidências; expandir sob demanda. Instruções curtas não autorizam omitir limitações nem critérios. Se contexto acabar, registrar checkpoint antes de continuar. Nenhum executor preenche números ausentes por estimativa não identificada.

Manifesto de execução deve identificar: tarefa/split, snapshot base e árvore efetiva, versão do ArchAtlas, condição, modelo/provedor/versão, configuração, prompt e hashes, repetição, ordem aleatória, caches, hardware, ambiente, timestamps e limites. Log deve registrar consultas, expansões, evidências, leituras, consumo, erros, patch e avaliações. Dados ausentes permanecem nulos com motivo.

Reprodução significa conseguir reconstruir ambiente, entradas, cápsulas determinísticas e scoring. Respostas de serviços LLM podem variar; guardar saídas para replay do avaliador e medir variância em novas chamadas. O índice e logs devem respeitar exclusões do projeto; soluções e testes ocultos nunca são candidatos de retrieval. Conservar ponteiros/hashes sem copiar blobs do dataset ao repositório.

## 10. Próxima ação e pendências

Próxima ação quando a execução for iniciada: **P0 — auditoria**, seguida de P1. Não começar instalador universal, MCP, treino, banco vetorial obrigatório ou migração massiva de diretórios.

Pendências que bloqueiam apenas as etapas dependentes: IDs efetivos dos modelos; teto de custo/tempo; ambiente de build/teste SIGA; custodiante do holdout; seleção de projetos de transferência; responsáveis pela avaliação semântica. Resolver durante preparação, antes de qualquer rodada correspondente. Até lá, pesquisa documental e especificações podem avançar.

Definição de êxito: evidência reproduzível de que desenvolvedores ou agentes resolvem tarefas com menos recursos e qualidade preservada no escopo testado — ou uma conclusão clara de por que a proposta ainda não entrega esse ganho.
