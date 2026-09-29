# Bitcoin — espelho E26-00–E26-06

Data: 2026-09-24. Estado: todos os experimentos planejados, nenhum executado nesta revisão.

Este é o espelho Bitcoin dos [experimentos canônicos](../EXPERIMENTOS_2026.md). Preserva as mesmas hipóteses, técnicas, comparadores, regras de medição e critérios de decisão. Usa os mesmos [R26-01–R26-09](../../research/16_BASE_EXPERIMENTAL_2026.md), mudando apenas dataset, adaptadores e tarefas. Entrada do agente: [plano Bitcoin](../BITCOIN_PARALLEL_PLAN.md); propriedade e integração: [protocolo paralelo](../PARALLEL_EXECUTION.md).

## 1. Contrato de equivalência

Antes de cada experimento, registrar `method_revision` (commit/hash do protocolo), `core_sha`, `adapter_sha`, `dataset_sha`, configuração de compilação e `policy_hash`. Mesmo nome de experimento não garante mesma implementação. Divergências são emendas explícitas antes da rodada; não reescrever retroativamente resultados.

Padrões herdados: budgets diagnósticos 2k/8k com tokenizer conhecido; A/B/C e D apenas após protótipo; mesmo modelo dentro de cada bloco; contextos/sessões resetados; busca normal disponível; todos os custos medidos; avaliação cega de patches e testes ocultos segregados. Propostas de qualidade/custo: perda máxima de 5 pontos percentuais e economia mínima de 20% com os mesmos critérios de intervalos do plano principal, a congelar no pré-registro Bitcoin.

Progresso de SIGA não conclui etapa Bitcoin. Uma variante que não suporta C++ é limitação a registrar. Mesmo que Bitcoin termine primeiro, não altera o cronograma do outro agente. Cada experimento usa `experiments/bitcoin/<experiment_id>/<run_id>/` para relatórios sanitizados e runtime externo exclusivo para DB/build/logs completos.

## 2. Fichas Bitcoin

### BTC-E26-00 — medir contexto de verdade

**Espelho:** E26-00; **papers:** R26-08; **etapa:** BTC-P2.

**Hipótese e comparador:** distinguir hit, recall completo e contexto entregue, sem alterar ranking. Reusar versão publicada de telemetria/scoring e validar fixtures independentes de Bitcoin.

**Entradas:** pequenos exemplos C++/Python auditados, incluindo definição em header, implementação em outro arquivo, overload homônimo, spans sobrepostos, ouro alternativo, arquivo removido e mudança pós-index. Não usar o próprio extrator como gerador definitivo do ouro.

**Procedimento/medição:** registrar `retrieved`, `delivered`, `opened` e `declared_relevant`; contar serialização inteira e separar histórico. Comparar métricas calculadas com valores esperados das fixtures; validar replay e identidade do snapshot. Caminho completo exige todas as relações verificadas necessárias, não apenas um arquivo.

**Aceite:** nenhum caso parcial recebe recall completo; payload e estimativas identificados; fontes obsoletas detectadas; nenhum acesso acidental ao dataset/DB SIGA. Saída: `REPORT.md` e testes em `tests/bitcoin/`. Falha em contrato geral vira pedido ao A.

### BTC-E26-01 — recuperar a próxima evidência necessária

**Espelho:** E26-01; **papers:** R26-06 e R26-08; **etapas:** BTC-P2–P3.

**Amostra dev proposta:** 20 positivos, cinco por tipo, e oito negativos, quatro naturais e quatro de repositório errado. Mesmo desenho SIGA, com ouro Bitcoin próprio e sem impor que uma categoria tenha exemplos antes de confirmá-los no snapshot.

- `code2test`: alteração C++ → testes unitários/funcionais pertinentes.
- `trace2code`: falha C++/Python/RPC → implementação candidata além do frame fornecido.
- `comment2context`: comentário de revisão → contratos/definições ainda não fornecidos.
- `edit2ripple`: diff ancorado → consumidores, interfaces e testes afetados.

**Comparação:** BM25/lexical versus core congelado com adaptador mínimo e, posteriormente, candidato modular. Casos naturais sem ouro local precisam de evidência independente; falta do parser não prova ausência de arquivo relevante.

**Métricas/aceite:** recall/precisão de arquivos novos, conjunto completo, cobertura sob budget e abstenção correta/indevida, separados por tipo. Não premiar novamente o arquivo dado na pergunta. Selecionar política dev; não concluir ganho de edição nesta etapa.

### BTC-E26-02 — profundidade versus diversidade de arquivos

**Espelho:** E26-02; **paper:** R26-05; **etapa:** BTC-P4 após piloto.

**Hipótese:** definição, contrato e corpo podem exigir múltiplos trechos do mesmo arquivo ou par header/implementação. Ampliar número de arquivos não garante patch melhor.

**Comparação:** mesmos candidatos/ranking/budget, com um trecho por arquivo; múltiplos trechos não redundantes; expansão até unidade de código/contrato. Deduplicar apenas spans idênticos nos três. Regras C++ não devem inventar resolução semântica de overloads/templates.

**Tarefas:** subset dev pré-selecionado com alterações locais e entre arquivos. Busca/leitura normal nos braços de produto. Diagnóstico sem busca é separado.

**Métricas/decisão:** patch aceito, dependências omitidas, releituras, profundidade por arquivo, custo e tempo totais. Implementar estratégia em namespace Bitcoin via extensão ou solicitar alteração genérica ao A. Promover candidato por qualidade/custo, não por quantidade de arquivos.

### BTC-E26-03 — funcionalidades, entidades e relações

**Espelho:** E26-03; **papers:** R26-01 e R26-04; **etapa:** BTC-P4.

**Hipótese:** pedidos como mudança RPC ou comportamento de mempool podem se beneficiar de mapa funcional, mas relações persistentes precisam pagar seu custo.

**Comparação em partes:** busca plana versus mapa de módulos + entidades sem arestas; mesmas sementes com expansão desligada/ligada; só depois descrições funcionais e PageRank versus expansão simples. Não modificar simultaneamente sementes, parser e política ao atribuir um ganho.

**Entradas:** apenas código/documentação do snapshot, sem enunciado/solução/holdout indexados. Descrições derivadas têm origem, hash e custo registrados. Manter fatos verificáveis separados de candidatos; templates, macros e chamadas virtuais não são automaticamente resolvidos pelo índice.

**Métricas/decisão:** sucesso da edição, custo total/amortizado, cobertura, índice e atualização. Testar mudança de header, exclusão, renomeação e flags de build relevantes, comparando incremental com rebuild. Preferir controle sem arestas se obtiver melhor relação qualidade/manutenção. Fonte do paper não autoriza presumir mecanismo interno da LLM.

### BTC-E26-04 — foco explícito e poda opcional

**Espelho:** E26-04; **paper:** R26-09; R26-07 somente se elegível; **etapa:** BTC-P4 opcional.

**Comparação:** mesmo foco/candidatos com saída completa, seleção determinística e filtro neural, mais condição sem foco. Auditar preservação de assinaturas, guards, condições de compilação e contexto que distingue overloads. Não afirmar que fragmento sintaticamente válido preserva toda a semântica.

**Métricas:** taxa de uso do foco, omissões, releituras, custo de filtro/inicialização, latência e patch aceito. Verificar pesos/licença/recursos e generalização C++ antes de comparar. Usar fixtures leves primeiro; não adotar scripts distribuídos dos autores sem dimensionamento.

**Decisão:** neural permanece opcional até superar regras em ganho líquido. Pro requer controle do modelo/servidor e acesso a estados internos; indisponibilidade da API é registrada, sem trocar silenciosamente os executores escolhidos.

### BTC-E26-05 — contexto acumulado de sessão longa

**Espelho:** E26-05; **papers:** R26-02 e R26-03; **etapa:** após pressão real de contexto observada.

**Comparação:** política atual, remoção de observações antigas, compactação literal por limiar. Resumo/estágios só em segunda rodada. Fixar orçamento total e ações; preservar regras de ferramentas, instruções e limites do protocolo do cliente.

**Tarefas:** investigação entre arquivos e ciclos de build/testes Bitcoin, incluindo necessidade de recuperar decisão antiga. Logs longos de compilação são um tipo de evidência, não texto irrelevante por definição. Não alongar artificialmente todos os casos para favorecer compactação.

**Métricas/decisão:** replay para integridade e rodada viva para reação do agente; medir tokens/cache/custo total, overflow, decisões perdidas, comandos repetidos e patch aceito. Build cache e concorrência do host são controlados separadamente. Se não houver acesso ao histórico, manter o experimento indisponível naquele cliente, sem bloquear a ferramenta de retrieval.

### BTC-E26-06 — adoção por um desenvolvedor Bitcoin

**Espelho:** E26-06; **paper:** R26-03; **etapas:** especificação BTC-P1, integração BTC-P4, uso BTC-P6–P7.

**Comparação:** mesmo motor por CLI versus ferramenta estruturada, contando overhead de schemas; depois tarefas humanas equivalentes e distintas, com/sem assistência e ordem contrabalanceada. Não atribuir diferenças de modelo ao transporte.

**Jornadas:** falha funcional → implementação/testes; alteração RPC → contrato/consumidores; modificação de header → impacto/reindexação; fonte obsoleta → diagnóstico/fallback. Incluir GUI apenas se selecionada e testável no ambiente; não traduzir artificialmente tarefas JSP para Qt.

**Aceite técnico:** ambiente limpo, índice local Bitcoin, consulta/expansão com referências verificáveis, edição em checkout isolado, testes registrados, atualização e remoção reversível. Verificar datadir, portas, caches e ausência de escrita no runtime SIGA.

**Métricas/decisão:** tempo de configuração, patch aceito, revisão, retrabalho e suporte real C++/Python. Publicar candidato e limitações no namespace Bitcoin para integração por A; não publicar automaticamente pacote ou mudanças upstream.

## 3. Sequência e mesma régua de decisão

BTC-P0 → BTC-P1 → BTC-P2/E26-00–01 → BTC-P3 piloto A/B/C → BTC-P4/E26-02, depois 03/04/05 conforme diagnóstico → BTC-P5 cego → BTC-P6 portabilidade temporal/ambiente → BTC-P7/E26-06. Não há dependência de SIGA-P5 para iniciar Bitcoin.

Todas as sete fichas devem receber estado: planejada, em execução, concluída, bloqueada por dependência ou não aplicável com justificativa verificável. Mesmas técnicas não significa executar filtro neural/compactação sem infraestrutura, nem marcar “concluída” uma técnica não testada. Todos os motivos de não execução aparecem no relatório final.

Piloto Bitcoin mantém proposta de 12–20 tarefas × três condições × duas repetições × um modelo, com teto próprio. Não executar a multiplicação completa por sete experimentos. Confirmação usa amostra dimensionada no piloto Bitcoin, avaliação cega independente e candidato congelado; falhas e tentativas entram no custo.

## 4. Saída de cada etapa

Registrar pergunta, paper/método, identidade do core/adaptador/dataset, condições, comandos, logs, medições, falhas, aceite e decisão `manter`, `simplificar`, `descartar` ou `evidência insuficiente`. O arquivo `REPORT.md` público não expõe ouro do próximo holdout. O [estado da trilha](STATUS.md) aponta para artefatos existentes sem inventar SHAs/resultados.
