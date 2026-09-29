# Protocolo: desempenho da CLI e utilidade real para agentes

Data: 2026-09-29. Estado: proposta a congelar antes das respectivas rodadas; nenhum resultado novo. Plano executor: [CLI Rust e piloto](../../plans/RUST_CLI_PILOTO_REAL.md).

## 1. Separar as duas perguntas

**Implementação:** Rust reduz latência, RSS e CPU para o mesmo trabalho? Comparar Python congelado com Rust funcionalmente equivalente sobre corpus, candidatos e política equivalentes. Alterar parser/ranking e linguagem ao mesmo tempo mede mudança de produto, não efeito isolado de Rust.

**Produto:** o agente com seleção de contexto entrega patches corretos com menos custo e esforço? Comparar agentes completos com mesmo modelo, problema, snapshot, ferramentas básicas e limites; diferença controlada é acesso/política da ferramenta de contexto. Microbenchmark de consulta não responde essa pergunta.

Nenhum resultado de retrieval antigo, synthetic fixture ou replay entra como tarefa real resolvida. Todas as tarefas já usadas em desenvolvimento permanecem dev; o teste final usa famílias reservadas por custodiante.

## 2. Condições do piloto real

IDs novos, não renomeiam A/B/C/D históricos nem `D_bm25` Bitcoin:

- **BASE:** agente com shell/busca/leitura/edição/testes usuais, sem ArchAtlas.
- **LEX-RS:** mesmo agente + CLI Rust com BM25 e empacotamento simples, sem relações ou expansão estrutural. Chamadas lexicais adicionais são permitidas e cobradas.
- **CTX-RS:** mesmo agente + mesma CLI/índice Rust com política de contexto e expansão progressiva. Primeiro candidato determinístico e pequeno; não acumular todas as técnicas dos papers.

BASE vs CTX-RS mede valor sobre o fluxo usual. LEX-RS vs CTX-RS mede valor adicional da política modular sobre busca simples. Os dois braços Rust usam a mesma serialização, tokenizer e limites; não dar apenas ao tratamento uma implementação mais rápida do transporte.

O agente pode ignorar a CLI; medir taxa de uso e incluir todas as execuções designadas ao braço (análise por intenção de tratar). Não remover as que não usaram a ferramenta. Descrições necessárias das ferramentas fazem parte do tratamento e seus tokens são contabilizados; nenhuma condição recebe dica sobre solução.

O modelo é um executor real dentre os desejados pelo usuário (Muse Spark 1.3, DeepSeek Flash v4.1 ou Luna 6), **após resolver ID/provedor/versão, disponibilidade e medição de uso**. Nomes citados não são IDs de API confirmados. Primeiro um modelo, depois replicações separadas. Não trocar para outro sem registrar a decisão. Preferir o mesmo cliente/loop nos três braços; se o cliente não expuser uso ou reset verificável, montar runner isolado para o mesmo modelo ou limitar explicitamente a conclusão possível.

## 3. Tarefas reais e integridade da avaliação

Por trilha: quatro tarefas de smoke e 16 distintas para piloto. Proposta de composição do piloto: quatro bugs locais, quatro mudanças entre arquivos, quatro envolvendo testes/comportamento de API e quatro envolvendo configuração/interface ou integração suportada. Exigir diversidade real, não apenas renames ou perguntas “onde está”. Cada tarefa pertence a uma categoria primária para evitar contagem dupla.

SIGA e Bitcoin têm datasets, custos e resultados próprios. A ausência de build Bitcoin não bloqueia SIGA. Outro projeto com build disponível pode ser laboratório técnico, mas não substitui silenciosamente uma validação SIGA/Bitcoin nem passa a ser transferência inédita se for usado no ajuste.

Para cada tarefa, antes do modelo:

1. Fixar snapshot base anterior à solução, dependências, imagem/ambiente e rede necessária. Arquivar hashes e comandos. Preferir problema genuíno/requisito plausível revisado independentemente; registrar origem e risco de contaminação de tarefas públicas.
2. Verificar que o projeto base compila e que as regressões relevantes passam. Demonstrar teste de aceitação falhando por comportamento ausente no base e passando no patch de referência, no ambiente privado do avaliador. Falha de dependência não é falha comportamental.
3. Dar ao executor apenas enunciado e testes públicos autorizados. Ouro, solução, commits futuros e testes ocultos ficam em ambiente inacessível a shell, Git, índice e histórico do executor; worktree separada no mesmo repositório não garante isso.
4. Congelar testes e rubrica antes das saídas. Patch candidato é aplicado a base limpa; avaliador executa seus testes imutáveis, sem confiar em testes que o agente possa ter enfraquecido. Testes novos do agente são evidência complementar.
5. Registrar sucesso com testes de aceitação, regressões e revisão semântica. Sem exigir identidade textual ao patch de referência; aceitar soluções alternativas corretas.

Smoke testa infraestrutura com modelo de verdade: quatro tarefas × três braços × uma repetição = 12 runs por trilha. Piloto: 16 × três × duas = 96. Os dois budgets históricos 2k/8k não multiplicam automaticamente o piloto: escolher um (proposta inicial 2k de saída com tokenizer válido) no smoke e congelar; alternativa 8k é ablação posterior. O limite total do agente é separado.

## 4. Limites operacionais e orçamento financeiro

Propostas iniciais a calibrar **no smoke, antes do piloto**, iguais entre braços: até 30 minutos de parede, 40 turnos do modelo e 100 chamadas de ferramenta por tentativa; builds/testes com timeouts próprios documentados. Esses valores são tetos propostos, não dimensionamento comprovado. Se insuficientes para o projeto, alterá-los antes do piloto e para todos os braços.

Preencher também teto de tokens faturados e moeda por tentativa, teto por trilha, política de retries e reserva financeira para o confirmatório. O runner para ao primeiro teto atingido e registra falha; nunca continua gastando apenas porque falta “terminar uma etapa”. A solicitação de planejamento não define autorização financeira.

Após smoke, estimativa de orçamento do piloto = 96 × limite monetário por tentativa + infraestrutura/indexação + reserva explícita para os retries permitidos. Apresentar consumo esperado estimado do smoke e pior caso autorizado, separadamente. Se rodarem ambas as trilhas: 24 runs de smoke + 192 de piloto = 216 antes de retries. Confirmação não está incluída.

Evitar dependência circular do plano antigo: piloto requer seu próprio pré-registro, ambiente, telemetria, limites e avaliador; **não requer estimativas do piloto nem pré-registro confirmatório já selado**. Dimensionamento e selo finais vêm depois.

## 5. Pareamento, execução e cegamento

Executar as mesmas tarefas em todas as condições; randomizar ordem em blocos por tarefa/modelo, contrabalancear horário/cache, registrar seed quando aplicável. Repetição não é tarefa independente. Novo workspace, sessão do modelo e estado da ferramenta por tentativa; sem importar resposta, patch ou memória de outra condição.

Indexar somente o snapshot disponibilizado ao executor. Caches persistentes de outro braço/solução são proibidos. Cache de provedor pode não ser controlável: registrar tokens lidos/escritos em cache, balancear ordem e fazer análise de sensibilidade. Anunciar mudança de versão do modelo como novo bloco, não misturar silenciosamente.

Os agentes que implementam Rust e Bitcoin não são automaticamente avaliadores cegos. Custodiante independente conserva chaves e tarefas finais. Avaliador recebe enunciado, base, patch e rubrica, sem condição/modelo/custo/ordem; ocultar metadados externos sem alterar a semântica do patch. Estilo do patch pode revelar pistas: registrar suspeita de condição e não chamar o estudo de duplo-cego.

Testes automatizados têm precedência para fatos executáveis. Revisão semântica humana avalia cumprimento, regressão não coberta e alterações indevidas. Segundo revisor independente resolve rejeições/disputas e revisa amostra aleatória pré-definida dos aceites (proposta 25%). Juiz LLM pode triar, mas não constitui sozinho o gabarito nem pode ser o mesmo executor. Abrir rótulos somente após julgamentos e adjudicação congelados.

## 6. Métricas e eventos que serão coletados

Unidade de inferência: tarefa, com tentativas agrupadas. Primárias:

- `success_rate`: fração de tentativas com patch aceito segundo testes + revisão.
- `cost_per_success`: custo de **todas** as tentativas / quantidade de aceites, incluindo falhas; infinito quando não há sucesso.

O custo inclui modelo (entrada, saída, reasoning quando exposto, cache, chamadas auxiliares), runner e ferramenta local, indexação e manutenção. Registrar tarifas, moeda e data efetivas; preços não são inventados no plano. Separar custo faturado do provedor, custo local medido em recursos e custo monetário local por tarifa/máquina-hora explícita, evitando cobrar duas vezes o mesmo tempo de máquina. Se não houver tarifa local, publicar recursos e sensibilidade: não chamar a parcela do modelo de custo total.

Indexação/amortização: apresentar tarefa isolada com índice frio e reutilização em 10/100 tarefas como cenários. Informar número realmente observado; projeções não viram medição. Incluir configuração/update/remoção quando pertinentes. Não comparar tratamento aquecido com baseline artificialmente penalizado.

Secundárias: tempo até patch aceito, tempo/custo consumido por fracassos, timeouts, p50/p95 por tentativa; tokens faturados e efetivamente enviados, tool calls, leituras repetidas, expansões, tempo de revisão humana, intervenções, retrabalho e aceites sem intervenção. Reportar tempo entre sucessos junto da taxa de sucesso, para não esconder tarefas abandonadas. Esforço humano é medido no piloto/revisão e depois no estudo com devs; tool calls são proxy, não equivalência a esforço.

Eventos de contexto: `retrieved` = candidatos internos; `delivered` = bytes efetivamente enviados na resposta; `opened` = leitura explícita capturada; `declared_relevant` = relato do agente. Não inferir uso interno pelo raciocínio. Scoring diagnóstico usa trechos entregues verificados e distingue hit de arquivo, recall de conjunto e cobertura de spans essenciais. Arquivo citado sem trecho suficiente não prova que a informação necessária chegou.

Manifesto mínimo por run: trilha/tarefa/split, SHA base e hash da árvore, binário e política/contrato, schema/geração do índice, modelo/provider/version, prompt/tool specs hashes, tokenizer, budgets/limites, hardware/OS/toolchain, cache, ordem/repetição, timestamps, processos e códigos de saída. Logs vinculam requests/responses, bytes/tokens, uso faturado, patch, testes e julgamento. Campos desconhecidos são `null` com motivo; falta de custo/sucesso bloqueia a conclusão correspondente, não vira zero.

## 7. Microbenchmarks Rust: protocolo independente

Congelar coortes e consultas antes de otimizar: SIGA e Bitcoin reais, mais fixtures de equivalência. Medir separadamente corpus grande de estresse, consultas com muitos matches, zero matches, Unicode, arquivo gigante, índice obsoleto, locks e crash. Não otimizar apenas a consulta mais favorável.

Executar release com toolchain/flags pinadas; repetir lotes pareados Python/Rust em ordem alternada. Proposta: 30 consultas estratificadas × dez repetições aquecidas por implementação; dez inicializações/builds de índice em diretórios exclusivos para medir dispersão. Medir comando externo do spawn até consumir stdout, não apenas função interna. Quantis: convenção e script publicados, sem misturar mediana com ordem superior de amostra par.

“Frio” tem duas dimensões: índice ausente e cache de filesystem frio. Novo processo ou cópia de DB não garante cache de disco frio. Reportar separadamente primeiro uso, índice pronto/processo novo e cache aquecido. Limpeza de cache global só em máquina dedicada; caso contrário declarar frio de filesystem não medido.

Registrar wall/CPU user+system, pico de RSS incluindo subprocessos, page faults quando disponíveis, bytes lidos/escritos, tamanho de índice/WAL, tamanho do binário e tempo de instalação. Medir alto consumo pelo máximo por run e distribuição entre runs. Em cgroup isolado, registrar também pico atribuído ao grupo; não equiparar essa medida ao RSS.

Testes de correção precedem comparação: seleção da mesma política, orçamento da serialização inteira, refs verificadas, atualização incremental equivalente a rebuild em edit/delete/rename, arquivos novos/exclusões/troca de branch, DB incompleto/corrompido, caminhos fora da raiz e concorrência. A falha não pode produzir JSON de sucesso ou apagar outro índice.

Só promover otimização que preserve correção/cobertura declarada. As metas do plano são gates de engenharia, independentes do gate científico de utilidade do agente. Rust mais rápido sem patch melhor/mais barato continua sendo ganho apenas da implementação.

## 8. Estatística e critérios de decisão

Piloto é diagnóstico: estimar sucesso, pares discordantes, variância de custo e correlação entre repetições. Publicar cada braço e todas as falhas; não concluir não inferioridade com 16 tarefas por conveniência. Nem milhares de consultas sintéticas substituem essas tarefas.

Confirmatório: candidato e baseline primário escolhidos usando somente desenvolvimento/validação; congelar antes do teste final. Pré-especificar diferença de sucesso `candidato − baseline` e razão de custo por sucesso `candidato / baseline`. Bootstrap pareado agrupado por tarefa, com todas as repetições no mesmo cluster; validar o método em simulações, incluindo poucos/zero sucessos. Não descartar réplicas com denominador zero para melhorar o intervalo.

Dimensionar **tarefas independentes** por simulação com estimativas do piloto, potência alvo de 80%, considerando ambas as condições de aceitação e análise conservadora da incerteza do piloto. A margem de 5 pontos percentuais pode demandar muito mais tarefas que o piloto; obter tamanho e custo antes de selar. Pré-registrar tratamento de tarefas inviáveis e ausência de dados antes de abrir os resultados.

Critério principal proposto, herdado do plano científico:

- Limite inferior do IC95% da diferença de sucesso **maior que −0,05**.
- Limite superior do IC95% da razão de custo por sucesso **menor que 0,80**.

É necessário cumprir ambos para alegar economia de pelo menos 20% com qualidade preservada dentro da margem. Não inferioridade não significa identidade de qualidade. Usabilidade/tempo humano é dimensão adicional; qualquer alegação específica de menor esforço precisa de sua própria medição e intervalo. Demais comparações ficam exploratórias ou recebem correção por multiplicidade previamente definida.

Falha/timeouts atribuíveis ao tratamento contam contra ele. Outage externo pode gerar retry simétrico pela regra congelada, mantendo todas as tentativas e seus custos; indisponibilidade do ambiente não é exclusão escolhida depois de observar o braço vencedor. Não parar cedo em vitória sem regra sequencial pré-registrada. Se evidência/potência forem insuficientes, resultado inconclusivo.

## 9. Artefatos e responsáveis

A mantém harness/contratos comuns em áreas próprias e coordena integração. Saídas SIGA sob `experiments/rust/siga/<run_id>/`; Bitcoin sob `experiments/bitcoin/rust/<run_id>/`, mantidas por B. Instrumentação usa mesma versão publicada; ambientes separados.

Cada rodada publica manifesto, logs sanitizados, agregações geradas dos dados, relatório com limitações e hashes dos artefatos privados. Patches/rubricas selados são armazenados pelo avaliador; liberar após julgamento conforme o protocolo. Logs brutos não entram no índice nem na árvore acessível ao agente.

Checklist final: tarefa real executada; baseline e tratamento pareados; payload efetivamente limitado; nenhuma confusão entre stubs/LLM; custo completo ou limitação explícita; avaliação cega concluída; amostra e incerteza declaradas; fatos contrários publicados. Marcar “concluído” somente no nível de evidência efetivamente alcançado.
