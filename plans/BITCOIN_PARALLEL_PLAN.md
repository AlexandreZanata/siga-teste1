# Entrada do agente B — pesquisa e produto exclusivamente Bitcoin

Data: 2026-09-24. Estado: trilha planejada; PIN, implementação e resultados Bitcoin ainda não produzidos por esta revisão.

**Retomada de 2026-09-29:** o estado acima é o da criação do documento. A worktree Bitcoin avançou até `3623afb`, incluindo PIN, corpus e diagnósticos; consultar seu `plans/bitcoin/STATUS.md`, sem reiniciar BTC-P0. A próxima sequência é a [CLI Rust e piloto real](RUST_CLI_PILOTO_REAL.md), com [protocolo comum de validação](../research/rust/PROTOCOLO_VALIDACAO.md). B prepara build/testes, tarefas e avaliação Bitcoin, consome o binário Rust de A e registra em `experiments/bitcoin/rust/`. B deve distinguir preparação/ensaio de execução e corrigir a medição da entrega sob orçamento antes de novas conclusões. O core Rust pertence exclusivamente a A.

Este plano substitui o antigo roteiro BTC-0–BTC-6. Bitcoin passa a espelhar **P0–P7 e E26-00–E26-06**, sem esperar a conclusão do SIGA. Ler [protocolo de execução paralela](PARALLEL_EXECUTION.md), este arquivo e [experimentos Bitcoin](bitcoin/EXPERIMENTOS_2026.md). Bibliografia comum: [papers de 2026](../research/16_BASE_EXPERIMENTAL_2026.md).

## 1. Objetivo e limites

Investigar a mesma seleção modular de contexto no Bitcoin Core: localizar código e testes, compreender impacto de alterações, entregar evidências compactas e manter o índice atualizado. O resultado pretendido é uma ferramenta útil a quem desenvolve Bitcoin Core, com suporte C++/Python declarado e ganho medido em patches reais.

Não copiar as tarefas Java/JSP do SIGA. Preservar hipóteses, fatores, métricas, A/B/C/D, budgets e protocolo cego; adaptar domínio, build e critérios de aceitação. As primeiras tarefas podem cobrir RPC, validação/mempool, wallet, rede e testes, conforme o snapshot efetivamente escolhido. Não afirmar símbolos, caminhos de chamada ou testes sem inspecioná-los.

A pesquisa usa código e ambientes locais de teste. Testes funcionais devem usar ambiente isolado/regtest conforme documentação do snapshot; nenhum resultado depende de fundos, carteira pessoal, mainnet ou operação de um nó de produção.

## 2. Antes da primeira escrita

Confirmar worktree própria, branch `codex/bitcoin-context`, checkpoint documental e core base. Se estiver no diretório de A, parar apenas a escrita e resolver isolamento; não trocar a branch ali. `archatlas/bitcoin/**` e os namespaces Bitcoin definidos no protocolo são sua área de escrita.

Dataset candidato: [Bitcoin Core oficial](https://github.com/bitcoin/bitcoin). Escolher ref explícita e registrar SHA completo real em `benchmarks/bitcoin/PIN.md`, além de origem, data, estado da árvore e licença observada. `BTC_SHA` não é um valor pronto neste documento. O core CLI/harness legado contém caminhos SIGA; definir dataset por variável não garante suporte Bitcoin. Auditar antes de rodar e usar adaptador local ou pedido ao core.

Consultar as instruções **do SHA escolhido**, partindo das referências oficiais de [build Unix](https://github.com/bitcoin/bitcoin/blob/master/doc/build-unix.md), [testes](https://github.com/bitcoin/bitcoin/blob/master/test/README.md) e [testes funcionais](https://github.com/bitcoin/bitcoin/blob/master/test/functional/README.md), consultadas em 2026-09-24. Esses links acompanham `master` e não substituem o PIN. Registrar compilador, flags, dependências, features habilitadas e comandos realmente usados.

## 3. Etapas espelhadas

### BTC-P0 — auditoria e PIN

Equivale a SIGA-P0. Entradas: checkpoint comum, código Bitcoin pinado, capacidades atuais dos extratores e contratos públicos. Saídas futuras: `research/bitcoin/AUDIT_BASELINE.md`, `benchmarks/bitcoin/PIN.md` e `CENSO.md`. Verificar hardcodes SIGA, tokens/métricas, suporte a C++, headers, Python e cobertura real. Separar bloqueios de contrato, parser e build. Aceite: evidência por afirmação, nenhum dado SIGA contado como Bitcoin. Começar sem editar core.

### BTC-P1 — literatura aplicada e pré-registro próprio

Equivale a SIGA-P1; depende só de BTC-P0. Referenciar os mesmos R26-01–R26-09 com revisão congelada e registrar aplicabilidade C++/Python em `research/bitcoin/LITERATURE_APPLICATION.md`. Produzir `research/bitcoin/PREREGISTRATION.md` preliminar: hipóteses, braços, famílias de tarefa, falhas, custódia, limites e orçamento próprios. Mesmo método; não herdar autorização financeira, modelo resolvido ou dimensão amostral do SIGA.

### BTC-P2 — adaptador e medição

Equivale a SIGA-P2. Saídas: `research/bitcoin/CONTRACTS_P2.md`, adaptadores em `archatlas/bitcoin/**`, fixtures/testes em `tests/bitcoin/**`, manifesto de build/índice e E26-00 Bitcoin. Reusar telemetria e scoring somente em versão publicada compatível. Falta de extensão genérica vira pedido ao A, não edição direta do core.

Começar com capacidades honestas: texto/includes verificáveis; entidades sintáticas com parser identificado; resolução semântica apenas onde houver tooling e configuração de compilação suficientes. `compile_commands.json`, quando produzido, faz parte do ambiente versionado por hash. Regex não prova overload, template instanciado, chamada virtual ou alvo de macro. Headers compartilhados exigem invalidação de dependências, não apenas do arquivo editado.

Aceite: fixtures de C++ e Python, ouro independente, replay estável, payload inteiro contabilizado com método identificado, nenhuma queda silenciosa para dataset SIGA e nenhuma escrita no dataset base. Se build estiver indisponível, diagnóstico de retrieval pode avançar; piloto de patches permanece pendente.

### BTC-P3 — piloto de edição real

Equivale a SIGA-P3/F21; depende de BTC-P2, ambiente, modelos e teto definidos. Selecionar 12–20 tarefas executáveis com alterações locais e entre arquivos, incluindo testes C++/Python e comportamento RPC quando adequado. Evitar lote composto apenas de renomeação/documentação.

Braços A (busca/leitura), B (BM25), C (core congelado com adaptador Bitcoin mínimo). Caso C exija correção para funcionar, publicar `C_btc_adapter` com lista de adaptações e SHA; não apresentá-lo como ArchAtlas original sem modificações. Manter o mesmo adaptador entre comparações de política. Se não houver suporte, registrar `unsupported` como limite do produto, sem substituir silenciosamente C por D.

Aplicar o mesmo lote piloto de 72–120 execuções, condicionado a custo e ambiente. Aceitação combina testes de comportamento, regressões e revisão semântica. Builds limpos/reutilizados são condições documentadas e iguais entre braços, não economia atribuída ao recuperador.

### BTC-P4 — modularização e mesmas ablações

Equivale a SIGA-P4. Executar [BTC-E26-02–05](bitcoin/EXPERIMENTOS_2026.md) conforme os mesmos critérios de priorização e aplicabilidade. Usar o contrato do core publicado; adaptar em namespace Bitcoin. Novas políticas gerais são propostas ao A. Variante local experimental recebe nome/hash e não vira fork oculto.

Saída: candidato congelado, variantes tentadas e decisão por componente. Mesmas técnicas não exigem resultado igual ao SIGA; incompatibilidade com API/GPU/histórico é resultado documentado, não experimento concluído.

### BTC-P5 — confirmatório cego Bitcoin

Equivale a SIGA-P5; depende apenas de BTC-P4 e pré-registro final próprio. Dimensionar amostra pelo piloto Bitcoin, selar tarefas/avaliação, congelar core/adaptador/política e randomizar condições. Custodiante ou processo externo controla ouro e rótulos. Nenhum executor acessa commits de solução, logs de julgamento ou testes ocultos antes da hora.

Aplicar as mesmas propostas de margem de qualidade e ganho de custo, congeladas antes da rodada; publicar positivo, negativo ou inconclusivo. Não atualizar core quando A entregar novidade no meio da rodada. Resultados de Bitcoin não são agregados aos do SIGA para mascarar regressões.

### BTC-P6 — portabilidade temporal e de ambiente

Equivale à etapa de portabilidade, preservando o pedido de trilha **apenas Bitcoin**. Congelar candidato e avaliar novas famílias de tarefas/snapshots Bitcoin e outro ambiente de build pertinente, escolhidos antes dos resultados. Separar mudança temporal, cobertura de feature e diferença de ambiente.

Essa etapa não comprova transferência entre repositórios. H5/P6 do produto geral continua exigindo projetos que não participaram do desenvolvimento; Bitcoin agora é dataset de desenvolvimento. Saída: `research/bitcoin/PORTABILITY.md` e `LIMITATIONS.md`, com custos de atualização, macros/templates/dinâmica e cobertura de testes.

### BTC-P7 — piloto com desenvolvedor Bitcoin

Equivale a SIGA-P7. Executar BTC-E26-06: instalar ambiente isolado, consultar tarefa, abrir evidência, editar em checkout de tarefa, validar testes, atualizar índice e remover integração. Medir configuração, tempo até patch aceito, revisão e retrabalho com ordem contrabalanceada. Declarar capacidades C++/Python/GUI realmente validadas.

Entrega: guia `research/bitcoin/DEV_GUIDE.md`, relatório, pacote/adaptador candidato e checkpoint para integração por A. Não fazer merge em `main`, release ou push a Bitcoin upstream como efeito automático de concluir pesquisa.

## 4. Documentos, dados e estados

Todos os documentos de execução e relatórios específicos ficam em `research/bitcoin/**` e `plans/bitcoin/**`. Usar `track=bitcoin`, IDs `BTC-P0`…`BTC-P7`, `BTC-E26-00`…`BTC-E26-06` e `run_id` único. Dados de tarefa e corpus pertencem a `benchmarks/bitcoin/**`; relatórios sanitizados a `experiments/bitcoin/<experiment_id>/<run_id>/`. Índices/builds/logs volumosos ficam no runtime externo por rodada.

Publicar scripts e ponteiros/hashes, não copiar o corpus para o repositório ArchAtlas. Gabaritos finais não ficam em branch acessível ao executor. Manter `plans/bitcoin/STATUS.md` e registrar o primeiro ponto bloqueado sem marcar fases posteriores concluídas. Parada de uma fase não impede preparação independente das seguintes.

## 5. Mensagem de entrada sugerida

> Execute a trilha Bitcoin na sua worktree isolada. Leia `plans/PARALLEL_EXECUTION.md`, `plans/BITCOIN_PARALLEL_PLAN.md` e `plans/bitcoin/EXPERIMENTOS_2026.md`. Comece em BTC-P0; use os mesmos papers, técnicas e critérios da trilha SIGA, com dataset, tarefas, pré-registro, resultados e runtime próprios. Escreva somente nos namespaces Bitcoin. Peça alterações do core ao agente A por pedido versionado; não espere SIGA terminar para avançar nas etapas independentes. Resolva o PIN e as capacidades reais antes de executar comandos de indexação ou benchmark.
