# Base experimental de 2026 para o ArchAtlas

Pesquisa realizada em 2026-09-24. Corte de inclusão: trabalhos disponíveis até essa data. Estado: fontes consultadas e experimentos propostos; nenhuma reprodução executada.

Este documento complementa o [plano principal](../plans/PESQUISA_CONTEXTO_MODULAR.md) e fundamenta os [experimentos de 2026](../plans/EXPERIMENTOS_2026.md). A prioridade é testar utilidade para desenvolvimento, não acumular referências ou presumir superioridade por recência.

## 1. Método e limites da busca

Busca dirigida por recuperação de contexto de repositório, seleção por tarefa, poda de código, compactação de histórico e avaliação de agentes. Foram pesquisadas combinações como `site.arxiv.org/abs/26 repository context retrieval coding agents pruning 2026`, `site.arxiv.org "2026" "coding agents" "Sep"`, `site.arxiv.org "2026" "context" "SWE" "Aug"` e os títulos encontrados. Houve também busca por publicações de 23–24 de setembro. Não é uma revisão sistemática exaustiva nem garantia de que não exista trabalho mais recente.

Critérios de inclusão: primeira submissão em 2026; fonte primária acessível; mecanismo ou protocolo adaptável ao ArchAtlas; comparação falsificável; custo/dependências identificáveis. Priorizados trabalhos de julho–setembro, mantendo dois anteriores por fornecerem avaliação e implementação úteis. Agregadores serviram apenas à descoberta; conclusões abaixo remetem a papers e páginas dos autores.

Foram consultados metadados, resumo e seções de método/avaliação indicadas nas fichas; não houve reprodução, download de modelos ou auditoria completa dos artefatos. Tratar as versões arXiv como preprints nesta base, sem presumir revisão por pares. “Código localizado” significa link oficial e página acessada, não execução validada. Licenças de código, pesos e datasets exigem verificação separada antes de incorporar material.

As propostas locais e critérios dos experimentos são decisões nossas. Resultados publicados não são resultados do ArchAtlas, não são metas garantidas e não devem ser comparados diretamente entre modelos ou benchmarks diferentes.

## 2. Trabalhos selecionados

### R26-01 — FeatLens

**Título:** Feature-Guided Dynamic Code Graph Construction and Retrieval for Repository-Level Code Generation. Xutian Li et al. Primeira submissão: **22/09/2026**, versão consultada **v1**, arXiv **2609.26480**. [Registro](https://arxiv.org/abs/2609.26480v1) · [Método, §§3.1–3.3; avaliação, §§4–6](https://arxiv.org/html/2609.26480v1).

**Evidência:** conecta descrições de funcionalidades a funções, constrói um subgrafo por tarefa e prioriza dependências com personalized PageRank. O índice offline usa descrições, embeddings e agrupamento; ausência de chamadas LLM na recuperação não significa construção gratuita. A avaliação cobre geração de funções em DevEval/EvoCodeBench, distinta de edição livre no SIGA. A localização da função alvo participa da entrada.

**Aplicação proposta:** E26-03, comparar pontos de entrada lexicais com descrições funcionais e expansão limitada. Separar custo offline, consulta e manutenção. No nosso caso, localizar o alvo também será trabalho do sistema; não fornecê-lo só ao tratamento.

**Disponibilidade:** não foi identificado repositório dos autores no texto consultado. Não associar automaticamente pacotes homônimos ao paper. Começar por adaptação claramente identificada; reprodução fiel depende de resolver os detalhes e artefatos faltantes.

### R26-02 — CliffCompaction

**Título:** CliffCompaction: Cost-Efficient Compaction for Long-Horizon Coding Agents. Trang Nguyen, Eulrang Cho, Bingqing Chen e Tim Dettmers. Primeira submissão: **22/09/2026**, **v1**, arXiv **2609.26779**. [Registro](https://arxiv.org/abs/2609.26779v1) · [Método, §2; avaliações, §§3–5](https://arxiv.org/html/2609.26779v1).

**Evidência:** compacta ao atingir um limite, preservando trechos literais em vez de reescrevê-los. Nova compactação descarta a anterior e opera sobre o segmento seguinte de conteúdo original. Há perda deliberada de histórico. O paper avalia tarefas de coding/terminal e discute efeitos de cache.

**Aplicação proposta:** E26-05, medir se histórico menor reduz custo da sessão completa, além de reduzir a cápsula inicial. Testar perda de decisões antigas e releituras necessárias. Só cabe onde controlamos as mensagens enviadas; uma ferramenta de busca isolada não altera o histórico do cliente.

**Artefato:** [repositório dos autores](https://github.com/nguyenvuthientrang/cliffcompaction), página consultada, indica MIT e implementação como proxy. O README oferece modo por processo e modo observação. Reprodução futura deve fixar commit e configuração, preferindo ambiente isolado; não habilitar serviço ou modificar configuração global durante a pesquisa documental.

### R26-03 — Harness Design

**Título:** An Empirical Study of Harness Design for Coding Agents. Run-Ze Fan et al. Primeira submissão: **17/09/2026**, **v1**, arXiv **2609.20804**. [Registro](https://arxiv.org/abs/2609.20804v1) · [Desenho e condições, §§1–3; resultados e ablações](https://arxiv.org/html/2609.20804v1).

**Evidência:** mantém o ciclo de execução fixo e varia planejamento, ferramentas e gestão de contexto. Distingue ausência de compactação, remoção de observações antigas, recuperação de observações, resumo e estratégia em estágios. Os benefícios dependem do modelo e orçamento; disponibilizar recuperação de histórico não produziu ganho de acerto no cenário relatado.

**Aplicação proposta:** E26-05 e E26-06. Primeiro comparar políticas de contexto com ferramentas fixas; depois comparar CLI/ferramenta estruturada com a mesma seleção de evidências. Medir uso real do recurso de expansão, não apenas sua existência.

**Disponibilidade:** método consultado; implementação oficial reutilizável não confirmada nesta pesquisa. Uma implementação local das condições será adaptação. Não converter a observação sobre recuperação de histórico em proibição de reabrir código fonte atual.

### R26-04 — The Thousand-Graph Hypothesis

**Título:** The Thousand-Graph Hypothesis: A Testable Hypothesis of Task-Conditioned Relation Materialization in Repository-Level Code Reasoning. Fei Ding. Primeira submissão: **27/08/2026**, **v1**, arXiv **2608.26602**. [Registro](https://arxiv.org/abs/2608.26602v1) · [Interface, §4; experimento e limites, §§6–8](https://arxiv.org/html/2608.26602v1).

**Evidência:** propõe entidades persistidas e dois níveis de busca, global e local, sem arestas previamente construídas. Reporta avaliação com DeepSeek-V4-Flash; o próprio texto distingue sucesso comportamental de prova do mecanismo interno. Isso não confirma disponibilidade nem equivalência ao “DeepSeek Flash v4.1” indicado para nosso projeto.

**Aplicação proposta:** E26-03 inclui controle sem grafo: mapa de módulos → entidades → trechos. Comparar qualidade e custo de atualização contra a mesma base com relações, mantendo visível o custo de seleção. Se entidades bastarem, simplificar o produto.

**Limite:** as seções consultadas não fornecem detalhamento suficiente para auditar integralmente as taxas publicadas, tentativas e custos. Não adotar esses números como referência de desempenho. Código/manifestos executáveis não confirmados; manter como hipótese e adaptação de menor prioridade, não reprodução comprovada.

### R26-05 — The Recall Trap

**Título:** The Recall Trap: A Recall-Maximizing Retriever Configuration Reduces Issue Resolution in Fixed-Budget Code Context. Alexander Adkins e Teimuraz Trapaidze. Primeira submissão: **14/08/2026**, **v1**, arXiv **2608.14838**. [Registro e resumo](https://arxiv.org/abs/2608.14838v1) · [Texto do paper](https://arxiv.org/pdf/2608.14838).

**Evidência:** estudo controlado alterna uma regra de um trecho por arquivo em pacotes limitados. Na configuração principal, cobrir mais arquivos não produz os melhores patches. O efeito muda no recuperador BM25 e não foi detectado no cenário de leitura irrestrita estudado. Não sustenta abolir deduplicação universalmente.

**Aplicação proposta:** E26-02, variar diversidade de arquivos versus profundidade de trechos, com orçamento real igual. Deduplicar spans idênticos é diferente de proibir dois trechos úteis do mesmo arquivo. Medir resolução de tarefas com leitura normal, além do diagnóstico controlado sem busca.

**Artefato:** o registro aponta um [depósito de reprodução no Zenodo](https://doi.org/10.5281/zenodo.21879550). Link identificado; conteúdo e licença ainda não auditados. PDF acessado para consulta textual; não foi feita reprodução dos cálculos. Evidência contrária às nossas premissas integra a pesquisa.

### R26-06 — Agent Retrieval Bench

**Título:** Agent Retrieval Bench: Evaluating Repository Context Retrieval for Coding Agents. Bowen Qin e Yi Xie. Primeira submissão: **27/07/2026**, **v1**, arXiv **2607.24882**. [Registro](https://arxiv.org/abs/2607.24882v1) · [Método, tarefas, exemplos e avaliação](https://arxiv.org/html/2607.24882v1).

**Evidência:** avalia arquivos necessários à próxima ação usando mudança de código, comentário de revisão, falha e edição como sinais. Inclui casos naturais sem arquivo local relevante e controles de repositório errado. Mostra que ranking, cobertura sob orçamento e abstenção são objetivos diferentes.

**Aplicação proposta:** E26-01 adota `code2test`, `trace2code`, `comment2context`, `edit2ripple` e casos sem evidência local. Começar com exemplos de desenvolvimento SIGA curados independentemente; depois usar snapshots externos sem ajustar nos casos finais. Não considerar arquivo já fornecido na pergunta um novo acerto.

**Artefatos:** [site oficial](https://agent-retrieval-bench.github.io/) e [repositório ligado pelo site](https://github.com/eyuansu62/agent-retrieval-bench), ambos consultados. O site apresenta releases `v2_*`; fixar versão do dataset separadamente da versão v1 do paper. Licenças e downloads ficam para a preparação da execução.

### R26-07 — SWE-Pruner Pro

**Título:** SWE-Pruner Pro: The Coder LLM Already Knows What to Prune. Yuhang Wang et al. Primeira submissão: **20/07/2026**, **v1**, arXiv **2607.18213**. [Registro](https://arxiv.org/abs/2607.18213v1) · [Método, §3; integração ao servidor, apêndice E](https://arxiv.org/html/2607.18213v1).

**Evidência:** aprende seleção de linhas a partir das representações internas do próprio modelo, com cabeça de poda e integração ao servidor. Não é simples filtro textual aplicável a qualquer API fechada.

**Decisão:** referência condicional para E26-04, fora do MVP. Só testar reprodução se houver modelo de pesos abertos, acesso aos estados internos, servidor compatível e recursos medidos. Não substituir os executores pedidos para viabilizar esse paper nem chamar uma heurística externa de SWE-Pruner Pro.

**Artefato:** [repositório apontado pelo paper](https://github.com/Ayanami1314/swe-pruner-pro); link localizado no texto, execução e licença não auditadas. A escolha de deixá-lo condicionado evita transformar um mecanismo interessante em dependência obrigatória do produto.

### R26-08 — ContextBench

**Título:** ContextBench: A Benchmark for Context Retrieval in Coding Agents. Han Li et al. Primeira submissão: **05/02/2026**; última versão indicada no registro: **v3, 11/02/2026**, arXiv **2602.05892**. [Registro](https://arxiv.org/abs/2602.05892v3) · [Protocolo, §2.5; métricas, apêndice H](https://arxiv.org/html/2602.05892v3).

**Evidência:** acompanha contexto inspecionado e contexto declarado como relevante em arquivos, blocos e linhas, junto ao resultado do patch. Contém tarefas em oito linguagens, incluindo Java. Contexto declarado pelo agente continua sendo autorrelato, não prova causal de uso.

**Aplicação proposta:** E26-00 mede o que o índice encontrou, o que entregou ao modelo e o que foi reaberto; E26-01 verifica recuperação em granularidades distintas. Rubricas independentes e testes de edição continuam primários. Não exigir um único conjunto de contexto como única solução válida.

**Disponibilidade:** [página oficial ligada pelo paper](https://cioutn.github.io/context-bench/) consultada. A página acessada não basta para confirmar pacote de dados/harness instalável. A adaptação das métricas pode avançar com dados locais; uso do dataset externo depende de localizar release e licença.

### R26-09 — SWE-Pruner

**Título:** SWE-Pruner: Self-Adaptive Context Pruning for Coding Agents. Yuhang Wang et al. Primeira submissão: **23/01/2026**; versão indicada no registro: **v4, 07/05/2026**, arXiv **2601.16746**. [Registro](https://arxiv.org/abs/2601.16746v4) · [Objetivo explícito e filtro, §§3.1–3.4](https://arxiv.org/html/2601.16746v4).

**Evidência:** o agente informa uma pergunta de foco; um modelo auxiliar de 0,6B seleciona linhas antes de entregar a saída da ferramenta. O parâmetro de foco é opcional no desenho descrito. Isso fornece uma interface observável para a necessidade atual do agente.

**Aplicação proposta:** E26-04 compara saída completa, seleção por regras e modelo auxiliar, com mesmo foco e candidatos. Medir custo do filtro, dependências perdidas e releituras. Não assumir transferência de resultados Python para Java/JSP.

**Artefatos:** [código oficial](https://github.com/Ayanami1314/swe-pruner), página consultada indicando MIT e links para pesos/treino. Scripts de pesquisa recomendam infraestrutura com múltiplas GPUs; isso não demonstra requisito mínimo de inferência. Fazer dimensionamento separado; o core deve continuar utilizável sem o filtro neural.

## 3. Decisões que essa literatura muda

- **Qualidade do patch vem antes do recall.** Diversidade de arquivos e poda precisam ser avaliadas no comportamento final, incluindo possibilidade de o agente compensar uma omissão com nova leitura.
- **Separar três problemas:** escolher evidências do repositório, reduzir a saída de uma leitura e compactar histórico. São mecanismos distintos; combinar todos imediatamente impede atribuir ganhos.
- **Grafo passa a ser hipótese opcional.** Comparar mapa + entidades com o uso de relações; incluir custo de mantê-las corretas após edições.
- **Não carregar um catálogo inteiro na sessão.** Interface curta de capacidades, solicitação explícita de foco e expansão observável são o candidato inicial. Ferramentas extras também têm custo de contexto.
- **Portabilidade tem níveis.** Consulta/trechos podem funcionar com cliente que chama CLI; compactação exige controle do histórico; poda por estados internos exige controle do servidor. Declarar cada capacidade separadamente.
- **Recência exige cautela proporcional.** FeatLens e CliffCompaction têm dois dias nesta data de corte. São candidatos prioritários de teste, não base suficiente para prometer ganhos universais.

## 4. Ordem de aproveitamento

1. ContextBench + Agent Retrieval Bench: instrumentar e construir tarefas que representem a próxima ação do dev.
2. Recall Trap: testar o empacotamento que já existe antes de acrescentar novos componentes.
3. FeatLens + controle inspirado em Thousand-Graph: comparar entradas por funcionalidade, entidades e relações.
4. SWE-Pruner: foco explícito e poda opcional, primeiro com controle simples.
5. CliffCompaction + Harness Design: histórico e interface, em harness isolado que permita comparação válida.
6. SWE-Pruner Pro: somente uma trilha futura com infraestrutura compatível.

O próximo documento traduz essa ordem em entradas, alterações mínimas, controles e decisões de produto: [Experimentos e entrega para desenvolvedores](../plans/EXPERIMENTOS_2026.md).
