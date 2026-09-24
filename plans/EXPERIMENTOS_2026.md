# Experimentos de 2026 e primeira entrega para desenvolvedores

Data: 2026-09-24. Estado de todos os experimentos: **planejado, não executado**.

Base: [nove papers de 2026 verificados em fontes primárias](../research/16_BASE_EXPERIMENTAL_2026.md). Este documento detalha P1–P7 do [plano principal](PESQUISA_CONTEXTO_MODULAR.md); não substitui seu cegamento, pré-registro, política de falhas ou critérios estatísticos. A seleção de papers é parte de P1; P0, P2 e as reproduções continuam pendentes.

## 1. O produto que vale a pena testar

Primeira entrega pretendida: **assistente local de contexto para uma tarefa de desenvolvimento**, utilizável pelo dev ou por seu agente, com instalação isolada e suporte declarado. Entrada: uma dúvida, falha de teste, pedido de mudança ou diff. Saída: implementações, contratos, testes e configurações relevantes, com trechos verificáveis e opção de aprofundar.

Quatro jornadas de aceitação propostas:

- “Este teste falhou; onde investigar?” — fornecer implementações candidatas além do arquivo que aparece no erro, preservar diagnóstico e permitir abrir a fonte.
- “Vou mudar esta validação; o que mais preciso ler e testar?” — incluir consumidores e testes sustentados por evidência, deixando explícitas as relações incertas.
- “Preciso ajustar este comportamento da tela.” — encontrar JSP e recursos associados quando houver evidência; validar o comportamento da alteração, não só localizar texto.
- “O projeto mudou desde a última consulta.” — detectar desatualização, reindexar ou fazer fallback, sem apresentar trechos antigos como atuais.

São classes de tarefas a selecionar no SIGA, não alegações de que exemplos ou testes específicos já existem. A ajuda ao dev será medida pelo tempo até uma alteração correta, revisão necessária e retrabalho.

Fora da primeira entrega: treino de modelo, automação que modifica o código sem solicitação, banco remoto obrigatório, configuração global do agente, servidor de inferência obrigatório e promessa de suporte estrutural completo a qualquer linguagem.

## 2. Regras comuns a todos os experimentos

Cada experimento recebe manifesto com ID, hipótese, paper/versão, tipo (`adaptação`, `reprodução` ou `diagnóstico`), SHA do ArchAtlas, snapshot do dataset, política, tokenizer, modelo efetivo, parâmetros, limites, amostra, métricas e regra de parada. Saídas futuras: `manifest.json`, `runs.jsonl`, `REPORT.md` e ponteiros para patches/avaliações. Gabaritos e testes ocultos ficam fora da árvore visível ao executor.

O log distingue `retrieved` (candidatos encontrados), `delivered` (bytes efetivamente enviados ao modelo), `opened` (leituras explícitas) e `declared_relevant` (autorrelato). Usar path relativo, span, hash e versão da árvore; não presumir “usado pelo raciocínio” a partir de uma leitura.

Budgets diagnósticos iniciais: **2k e 8k tokens de contexto recuperado**, só com tokenizer identificado ou contagem oficial. São propostas locais, congeláveis no desenvolvimento. `chars//4` permanece estimativa de diagnóstico, sem afirmar limite rígido. O custo total inclui instruções das ferramentas, chamadas, histórico, respostas, auxiliares e indexação. Se não houver telemetria confiável, não concluir economia faturada.

Controles de produto permitem busca e leitura normais. Um braço sem busca pode existir para isolar efeitos, mas não representa benefício demonstrado em uso real. Mesmo modelo e tarefa são pareados; não comparar um tratamento com modelo melhor ao baseline com modelo pior.

Executores indicados: Muse Spark 1.3, DeepSeek Flash v4.1 e Luna 6 do ChatGPT, sujeitos à resolução de IDs e capacidades reais. Começar com um disponível e replicar o candidato nos demais. Nenhuma ficha presume hidden states, seed, contagem de reasoning ou capacidade de reescrever histórico nesses serviços.

## 3. Fichas executáveis de pesquisa

### E26-00 — medir contexto de verdade

**Base:** R26-08 ContextBench. **Tipo:** adaptação de instrumentação. **Prioridade:** primeira, dentro de P2 após a auditoria P0.

**Hipótese:** o harness atual pode esconder diferenças entre acertar um arquivo, entregar contexto suficiente e resolver a tarefa.

**Entrada:** fixtures de medição e tarefas de desenvolvimento já conhecidas; nenhuma abertura do holdout. **Mudança futura mínima:** instrumentar `archatlas/harness.py` e fronteira de entrega da cápsula, sem alterar ranking.

**Procedimento:** registrar candidatos, spans entregues e leituras; calcular hit, recall de conjunto, precisão e cobertura de caminho separadamente. Fixtures devem conter acerto parcial, arquivos alternativos válidos, spans sobrepostos, arquivo inexistente e trecho alterado depois da indexação. Verificar que o payload serializado inteiro entra na contagem.

**Aceite técnico:** resultados exatos nas fixtures; nenhuma métrica completa dá 100% por um único membro de conjunto recuperado; replay do mesmo log reproduz scoring; histórico não é contado como se fosse somente a cápsula. Não é experimento de superioridade.

**Decisão de produto:** habilita explicar o que foi entregue e por quê. Sem esse aceite, não avançar para alegações de economia.

### E26-01 — recuperar a próxima evidência necessária

**Base:** R26-06 Agent Retrieval Bench + R26-08 ContextBench. **Tipo:** adaptação de tarefas/métricas. **Prioridade:** P2–P3.

**Amostra proposta de desenvolvimento:** 20 casos positivos, cinco por tipo (`code2test`, `trace2code`, `comment2context`, `edit2ripple`), mais oito negativos: quatro naturais sem solução local e quatro controles de repositório errado. Não é o teste confirmatório e não aumenta automaticamente o lote de edições do plano principal.

**Controle:** busca lexical/BM25; **tratamentos:** ArchAtlas congelado e, posteriormente, variante selecionada. **Mudança mínima:** manifesto de tarefas e adaptação do harness, sem especializar a busca para nomes dos gabaritos.

**Procedimento:** construir ouro por revisão independente; excluir arquivos já fornecidos da medida de descoberta adicional; avaliar 2k/8k. Nos negativos, diferenciar “não há evidência local” de “índice não cobre a linguagem”. Calibrar thresholds somente no desenvolvimento. Usar releases públicos depois, pinados, com gabaritos inacessíveis ao agente.

**Métricas:** recall/precisão de arquivos adicionais, cobertura sob orçamento, todos-os-arquivos-necessários, taxa de abstenção correta e de abstenção indevida em positivos. Não calcular recall convencional com denominador zero nos negativos.

**Decisão:** promover somente uma política que preserve descoberta nos positivos e deixe a incerteza explícita. Resultado de recuperação seleciona candidatos, mas não comprova utilidade em edição.

### E26-02 — profundidade de código versus quantidade de arquivos

**Base:** R26-05 Recall Trap. **Tipo:** adaptação controlada. **Prioridade:** primeiro experimento de mecanismo após o piloto P3.

**Hipótese:** vários trechos úteis do mesmo arquivo podem ajudar mais que dispersar o budget por muitos arquivos.

**Comparação:** mesmos candidatos e ranking; variar somente empacotamento: (a) no máximo um trecho por arquivo; (b) múltiplos trechos não redundantes; (c) trecho expandido até unidade de código/contrato sob o mesmo budget. Manter deduplicação de spans idênticos nos três. **Ponto de intervenção futuro:** `archatlas/capsule.py`.

**Tarefas:** subconjunto pré-selecionado das edições dev do piloto, cobrindo mudança local e entre arquivos. Reusar definição de tarefa, mas reiniciar execução; não usar respostas anteriores no contexto. Diagnóstico sem novas leituras é separado da comparação principal com leitura disponível.

**Métricas:** patch aceito, dependências omitidas, releituras, tokens totais, tempo total e profundidade por arquivo. Não escolher vencedor apenas por recall. Verificar separadamente recuperador lexical e estrutural para não presumir mesmo efeito.

**Saída:** política de empacotamento candidata ou decisão de manter a atual. Teste confirmatório seguirá a margem de qualidade e a meta de custo do plano principal.

### E26-03 — funcionalidade, entidades e relações

**Base:** R26-01 FeatLens + R26-04 Thousand-Graph. **Tipo:** adaptação; não reprodução fiel dos papers. **Prioridade:** P4, após E26-02.

**Hipótese:** o melhor ponto de entrada depende do pedido; manter relações só vale a pena quando melhora tarefas o bastante para pagar sua manutenção.

**Desenho em duas partes para evitar confusão:** primeiro fixar entidades e montador, comparar busca plana com mapa de módulos → seleção local sem arestas. Depois comparar uma mesma política de sementes com expansão por relações desligada/ligada. Só então adicionar descrições funcionais como nova fonte de sementes e testar PageRank contra expansão simples. Não somar alterações em um único braço.

**Entrada:** código/documentação existentes no snapshot e tarefas em linguagem natural sem informar a função correta somente ao tratamento. **Intervenções futuras:** extratores, `store.py`, `strategies.py`, `query.py`; núcleo lexical continua baseline.

Descrições funcionais derivadas por LLM, se usadas, ficam em cache separado com modelo, prompt e hash dos arquivos que as sustentam. Não indexar enunciados, patches de resposta ou testes ocultos. Descrições manuais de smoke test são informação humana adicional e seu custo deve ser declarado. Nenhuma relação inferida vira fato estrutural sem validação.

**Métricas:** sucesso de edição, custo total/amortizado, dependências corretas, tamanho e latência do índice. Após edição/exclusão/renomeação, comparar incremental com rebuild e medir descrições/arestas obsoletas. Avaliar coortes com e sem nome explícito de símbolo.

**Decisão:** se o controle sem arestas preservar qualidade com menor manutenção, ele é candidato a padrão. Se relações ajudarem só em certas tarefas, ativá-las seletivamente. Não declarar prova de “grafo interno da LLM”.

### E26-04 — pedido explícito de foco e poda opcional

**Base:** R26-09 SWE-Pruner; R26-07 Pro apenas condicional. **Tipo:** adaptação de interface, seguida de reprodução parcial do filtro se viável. **Prioridade:** P4, opcional.

**Hipótese:** uma pergunta curta sobre a informação necessária permite reduzir trechos inúteis sem perder o contrato necessário à edição.

**Comparação:** mesmos candidatos e foco, com saída completa, seleção determinística de spans e filtro neural oficial. Rodar também sem foco para medir o custo/benefício do campo. Registrar taxa de uso, foco incorreto e fallback. Não descartar a execução quando o agente não formular o foco esperado.

**Intervenção mínima:** campo opcional `focus` na solicitação de contexto e estratégia de seleção substituível. Preservar spans originais e sinalizar omissões; não apresentar fragmento podado como arquivo integral. Reabrir fonte deve continuar possível.

**Métricas:** qualidade do patch, omissão de condições/assinaturas relevantes, releituras e custo/latência do filtro, inclusive inicialização. Scripts pesados dos autores não entram automaticamente no produto. Perfil CPU/GPU, pesos e licença vêm antes de decidir infraestrutura.

**Decisão:** filtro neural permanece extra até demonstrar ganho líquido sobre regras. Pro não entra em APIs sem acesso a estados internos; essa impossibilidade não bloqueia os outros experimentos.

### E26-05 — contexto acumulado de uma sessão longa

**Base:** R26-02 CliffCompaction + R26-03 Harness Design. **Tipo:** adaptação comparativa; reprodução do artefato só com commit/configuração congelados. **Prioridade:** depois de observar acúmulo real de contexto no piloto.

**Comparação inicial:** política atual do harness; remoção mecânica de observações antigas; compactação literal em limiar inspirada em CliffCompaction. Resumo por LLM e estratégia em estágios são comparações posteriores, não obrigatórias na primeira rodada. Mesmo budget total, mesmo número máximo de ações e tarefas pareadas.

**Procedimento:** começar com replay de mensagens para validar preservação de instruções, protocolo de tool calls e contagem; depois medir trajetórias vivas, pois replay não revela como o agente reagirá. Incluir tarefas longas naturais e diagnósticos com necessidade de recuperar uma decisão antiga. Não inflar artificialmente todas as tarefas para favorecer compactação.

**Métricas:** custo ponta a ponta, cache cobrado, overflow, ações repetidas, decisões perdidas, releituras e sucesso. Limites de 16k/32k são candidatos de diagnóstico apenas quando suportados, não defaults universais.

**Limite de integração:** se o cliente não permitir controlar o histórico, marcar este experimento indisponível nesse cliente e manter a ferramenta de recuperação utilizável. Configuração global, proxy persistente e interação com compactação nativa não fazem parte do ensaio mínimo.

**Decisão:** compactação só vira extensão se houver ganho nas sessões em que atua e nenhum benefício fictício derivado de comparar com baseline mal configurado.

### E26-06 — ferramenta que um dev consegue adotar

**Base:** R26-03 Harness Design e resultados locais anteriores. **Tipo:** validação de produto. **Prioridade:** especificação agora; integração mínima em P4; piloto humano e transferência em P6–P7.

**Hipótese:** o ganho do seletor sobrevive à interface, instalação e manutenção de um projeto real.

**Comparação de agentes:** expor o mesmo motor via CLI e ferramenta estruturada, uma alteração por vez; incluir custo dos schemas e ajuda no contexto. MCP fino é candidato apenas quando necessário ao cliente escolhido. Nenhuma opção pode receber contexto privilegiado.

**Comparação com devs:** tarefas equivalentes e distintas em ordem contrabalanceada, com e sem assistência. Não dar ao mesmo dev a solução recém-aprendida no segundo braço. Registrar experiência prévia, tempo de configuração, tempo até patch aceito, tempo de revisão e intervenções. Piloto pequeno avalia usabilidade; não prova generalização populacional.

**Aceite técnico proposto:** instalar em ambiente limpo; consultar; abrir evidência; atualizar após mudança; detectar índice incompatível; cair para leitura/busca se preciso; desinstalar sem alterações em código ou configuração global. Índice corrompido e linguagem não suportada geram diagnóstico, não resultado vazio enganoso.

**Decisão:** publicar versão experimental apenas com capacidades, limitações e evidências do escopo testado. Ganho em benchmark sem adoção prática não encerra a pesquisa.

## 4. Primeira fatia implementável após a preparação

Contrato de CLI proposto — **os comandos abaixo são especificação futura, não funcionalidades existentes**:

- `archatlas doctor`: informa suporte, raiz, estado do índice e limitações.
- `archatlas index`: cria/atualiza índice local com exclusões e versão do snapshot.
- `archatlas context`: recebe tarefa/foco/budget e devolve trechos + referências + lacunas.
- `archatlas expand`: amplia evidência previamente devolvida, com limites e snapshot atualizado.
- `archatlas verify`: valida integridade/proveniência; seu alcance atual será auditado antes de ampliar o contrato.

Formato de saída futuro: versão de schema, snapshot, referências, texto original, motivo de seleção, estimativa/contagem identificada, itens omitidos e estado (`ok`, `partial`, `stale`, `unsupported`). Exemplo de interface não implica que todos os campos possam ser obtidos em toda linguagem.

Reaproveitar API/CLI existentes. Separar adaptador do projeto, recuperador, empacotador e transporte por contratos pequenos; criar novas pastas apenas quando necessário. Começar com Java/Python conforme cobertura auditada e JSP no nível realmente sustentado; outras linguagens podem ter fallback lexical declarado.

O protótipo deve produzir uma demonstração reproduzível: dev fornece uma tarefa → vê evidências → agente faz a edição em checkout isolado → testes e revisão julgam o patch → relatório compara com baseline. A demonstração sozinha não substitui o holdout.

## 5. Ordem, volume e portões de decisão

1. **P0–P2:** concluir auditoria, consolidar fichas e executar E26-00. Preparar E26-01 sem inferência paga, exceto revisão assistida explicitamente contabilizada.
2. **P3:** executar o piloto A/B/C de 72–120 execuções já previsto no plano principal, instrumentado. Não repetir o lote integral para cada paper.
3. **P4:** E26-02 primeiro. Rodar E26-03 e E26-04 somente se as falhas observadas justificarem; E26-05 apenas se houver sessões com pressão de contexto. Uma nova comparação usa inicialmente um subconjunto dev previamente declarado. Testes de viabilidade não recebem linguagem confirmatória.
4. **P5:** escolher e congelar uma configuração e comparadores antes de abrir o teste cego. Aplicar dimensionamento e critérios de qualidade/custo do plano principal. Incluir todas as tentativas e componentes no custo.
5. **P6–P7:** E26-06, replicação nos demais modelos disponíveis e em pelo menos dois projetos externos selecionados antes do teste. Usar capacidades, não nomes comerciais, para definir compatibilidade.

Dois alvos iniciais de reprodução/adaptação de baixa barreira: métricas/casos do Agent Retrieval Bench e política de compactação do CliffCompaction. O primeiro pode começar em diagnóstico local; o segundo depende de controle do histórico. Se essa dependência faltar, substituir o alvo operacional por E26-02, mantendo o registro de que foi adaptação, não reprodução do paper.

Os limiares do plano principal continuam propostas pré-confirmatórias: preservar qualidade dentro da margem de 5 pontos percentuais e demonstrar redução de pelo menos 20% no custo por tarefa resolvida, com intervalos apropriados. E26-00 tem aceite técnico próprio; benchmarks diagnósticos não precisam “vencer” para serem úteis. Não descartar falhas para atingir esses valores.

## 6. Entregáveis e parada

Antes de inferência: fontes/versionamento, fixtures de métricas, tarefas/splits, IDs efetivos de modelos, ambiente, orçamento e protocolo congelados. Antes de confirmação: manifestos selados e avaliador separado. Antes de adoção: instalação/atualização/fallback verificados, suporte declarado e comparação em tarefa real.

Cada módulo experimental termina com `manter`, `simplificar`, `descartar` ou `evidência insuficiente`, acompanhado de artefatos. Nenhum componente entra no padrão só porque o paper é recente. Uma implementação menor que elimina custo sem piorar o trabalho do dev é um resultado de pesquisa válido.
