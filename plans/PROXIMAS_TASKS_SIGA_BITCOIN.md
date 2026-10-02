# Próximas tarefas reais — SIGA e Bitcoin

Data: 2026-09-30. Continuação de [R3–R5](RUST_CLI_PILOTO_REAL.md), com o [protocolo paralelo](PARALLEL_EXECUTION.md) e o [pré-registro](../research/rust/PREREGISTRATION_R0.md). Estado: **tarefas preparadas como requisitos dev; nenhum piloto com modelo executado nesta revisão**.

Objetivo: descobrir se a CLI ajuda um agente a entregar patches corretos com menor custo total e esforço. Novos microbenchmarks não respondem a essa pergunta. A próxima entrega é uma rodada de edição real com aceitação independente e julgamento cego.

## 1. Material disponível e limites

- [SIGA: 8 tarefas de código](../benchmarks/rust/tasks/siga.dev.json), na base `e3be22828f787cbe71b339aecb7a7bf569099803`.
- [Bitcoin: 8 tarefas de código](../benchmarks/rust/tasks/bitcoin.dev.json), na base `9be056a8a72b624dae9623b2f7bded92c2a21c91`.
- [Reproduções públicas](../benchmarks/rust/tasks/evidence/2026-09-30-public-probes.json): exceção na extração de delimitadores SIGA, exceção com conjunto de objetos não Comparable SIGA e duas exceções no verificador de checksum Bitcoin. Os probes usaram fontes originais, sem patch. A saída zero do probe significa que a exceção foi capturada, **não** que o comportamento passou no aceite.

Cada catálogo possui quatro candidatos smoke e quatro candidatos para o piloto, com uma categoria de cada tipo em cada grupo. São **16 requisitos concretos no total**, incluindo correções e extensões de utilitários usados por desenvolvedores. Requisito proposto não é bug confirmado upstream. Os demais precisam de reprodução contra o requisito antes de serem admitidos no benchmark.

As fontes SIGA foram inspecionadas no checkout local sem alterações rastreadas. As fontes Bitcoin foram consultadas no repositório oficial no SHA acima. Cada cartão registra caminhos e hashes para o curador. O build completo e as suítes de aceitação das duas trilhas não foram executados nesta preparação.

O schema `atlas-task-candidates/1` é deliberadamente diferente de `atlas-tasks/2`: o runner existente não deve consumir candidatos sem aceite. Não preencher `test_command` com compilação, `true`, teste genérico ou arquivo inexistente só para passar no validador. Os campos `curator_only` ficam fora do pacote do executor. `statement` e critérios públicos são requisitos; gabarito, localização da solução e casos privados pertencem à custódia.

## 2. Fila A — SIGA e core comum

### TASK-A01 — Preparar aceitação SIGA que realmente execute testes

**Prioridade P0; dono A; sem dependência de modelo ou orçamento.**

Trabalhar em cópia isolada do dataset no SHA fixado. Registrar Java, Maven, dependências e comandos de build. Começar por `SIGA-REAL-01` e `SIGA-REAL-05`, que permitem teste Java isolado; depois preparar os módulos Maven das outras tarefas sem banco ou servidor.

O `pom.xml` da base configura Surefire com `<skipTests>true</skipTests>`. Criar uma configuração de avaliação imutável que habilite testes no workspace do avaliador e comprovar no POM efetivo e no relatório Surefire que houve execução. Não presumir que `-DskipTests=false` sobrescreva a configuração literal. Arquivos em `src/test/br` também não são automaticamente descobertos como os de `src/test/java`.

**Aceite:** log e manifesto por tarefa, baseline executado, quantidade positiva de testes e casos comportamentais; nenhum aceite baseado apenas em `mvn compile`, sucesso sem testes ou suíte Python do ArchAtlas. Para Java isolado, usar asserts cuja falha produza código diferente de zero. Infraestrutura indisponível é bloqueio de ambiente, não falha do agente.

**Entrega:** `research/siga/rust/ACCEPTANCE_ENV.md` e evidências sanitizadas em `experiments/rust/siga/<run_id>/preflight/`.

### TASK-A02 — Completar o executor real e a contabilidade

**Prioridade P0; dono A; começa em paralelo com A01 e B01.**

Inspecionar `benchmarks/rust/runner.py` e implementar contrato de resultado do executor externo. Atualmente identidade do modelo e custo faturado são escritos como `null`; disponibilizar um executor externo não preenche esses campos automaticamente. Preparar adaptador para o provedor que vier a ser escolhido, com fixtures de respostas reais sanitizadas quando disponíveis. Nomes informais de modelos não substituem ID/provedor/versão verificáveis.

Capturar cada chamada de modelo, tokens de entrada/saída/cache, latência, erro/retry, ferramentas, gasto e motivo de parada. Contar os limites em todas as ferramentas do agente, inclusive shell e chamadas que não passam por `atlas-read`. Quando uma métrica não puder ser observada, registrar cobertura e motivo; bytes lidos pelo shim não são tokens faturados nem total de leitura do agente.

**Aceite:** testes de integração do contrato para resposta válida, erro, retry e teto; contabilidade reconcilia com a origem, sem cobrança duplicada ou ausência tratada como zero. Tentativa `dry` continua identificada como ensaio de infraestrutura. Ausência de cobertura não autoriza alegar redução de leituras ou custo. Fixar o mesmo loop e ferramentas básicas nos três braços.

**Entrega:** código comum, atualização de `research/rust/RUNNER_PILOTO.md` e manifesto de capacidade. Implementar antes da rodada paga; esta tarefa não autoriza gastos.

### TASK-A03 — Validar tarefas SIGA e publicar checkpoint comum

**Prioridade P0; dono A; depende de A01 para os aceites, não de chamadas a modelos.**

Revisar cada requisito com um curador e preparar testes independentes. Demonstrar teste novo vermelho na base e verde em solução de referência, preservando regressões existentes. Solução de referência fica na custódia e não entra no corpus, contexto, pacote do executor ou revisão cega. Não transformar o patch de referência em critério de igualdade textual.

Projetar somente campos permitidos para um conjunto `atlas-tasks/2`, com comando de aceite realmente existente, timeout medido, escopo de edição, caminhos imutáveis, SHA, origem e contaminação. O validador atual verifica o balanço global; conferir também balanço por split, IDs, quantidade e cobertura dos casos. Separar conjunto smoke de conjunto piloto.

**Aceite:** quatro tarefas smoke prontas, hash do conjunto e dos aceites, projeção sem `curator_only`, resultados baseline/referência e `eval.py validate` sem problemas. O executor não consegue ler testes privados ou solução; mera separação de diretórios não prova isolamento. Publicar o checkpoint de documentos/core e comunicar SHA a B conforme o protocolo.

**Entrega:** `benchmarks/siga/rust/smoke.tasks.json`, manifesto público sem ouro e checkpoint disponível para B. Não publicar gabaritos junto do manifesto.

## 3. Fila B — Bitcoin em worktree própria

### TASK-B01 — Preparar a primeira coorte Python sem esperar o build C++

**Prioridade P0; dono B; independente de A01/A02.**

Após receber o checkpoint comum, ler o catálogo Bitcoin e confirmar os hashes em clone completo no SHA fixado. Preparar os quatro candidatos smoke: checksum malformado, conversão Base58 mainnet para script, Content-Type JSON com charset e validação de `--jobs`.

Usar framework completo, conexões fake/HTTP local e subprocessos com fixtures próprias. As tarefas dessa coorte não precisam de `bitcoind`. Executar testes existentes pertinentes e novos casos comportamentais. O teste do runner não deve passar por faltar `config.ini`: comprovar a validação correta antes desse acesso.

**Aceite:** baseline vermelho e referência verde em cada requisito; comandos reais, timeouts e dependências registrados; nenhuma chamada a rede de produção. Concluir `BTC-REAL-01` primeiro, cujo defeito já foi reproduzido, mas sem confundir o probe publicado com aceite completo.

**Entrega:** `research/bitcoin/rust/ACCEPTANCE_ENV.md`, `benchmarks/bitcoin/rust/smoke.tasks.json` e `experiments/bitcoin/rust/<run_id>/preflight/`. B só escreve seus namespaces na própria worktree; não altera o catálogo comum em `benchmarks/rust/tasks/`.

### TASK-B02 — Preparar integração P2P e a coorte C++

**Prioridade P1; dono B; pode avançar enquanto A prepara o executor.**

Preparar aceites dos candidatos de opções do proxy, payload truncado, parser de unidades C++ e seleção vazia do runner. A tarefa P2P deve percorrer desserialização e callback com frame sintético, não somente testar a função auxiliar. Inspecionar e preparar build do snapshot para `test_bitcoin`, registrando compilador, flags e recursos.

**Aceite:** casos Python executados; para `BTC-REAL-07`, build e `util_tests` com teste novo realmente executados. Se C++ seguir indisponível, registrar bloqueio só dessa tarefa e seguir a coorte Python. Não chamar estudo exclusivamente Python de validação da transferência para C++/Bitcoin Core em geral.

**Entrega:** evidências em `experiments/bitcoin/rust/<run_id>/preflight/` e status na worktree B. Pedido de mudança comum vai em `research/bitcoin/requests/`, com ID/SHA, sem editar o core de A.

## 4. Fila de experimentos — cada trilha executa sua própria sequência

### TASK-EXP01 — Executar smoke real e decidir prontidão

**Prioridade P0; A executa SIGA, B executa Bitcoin. Dependências: aceites da trilha, executor instrumentado, modelo efetivo e teto financeiro definidos.**

Congelar quatro tarefas, um modelo verificável, executor, ferramentas, limites, políticas e plano de ordem. Usar `BASE`, `LEX-RS`, `CTX-RS`, uma repetição: **12 tentativas por trilha**. Mesmo snapshot e condições iniciais; workspace novo por tentativa. Sem acesso a patches de outra condição ou tentativa. Na BASE, não disponibilizar CLI, índice ou pack do tratamento.

Registrar custo total, inclusive retries e contexto; tempo até patch aceito; taxas de sucesso/falha; tokens; ferramentas; tempo/RSS da CLI e overhead de indexação. Reportar amortização de índice separadamente do custo inicial. Não usar latência da consulta como substituto do tempo de entrega do patch. Fixar tokenizer ou declarar modo bytes.

**Aceite:** logs íntegros e reconciliados, patches reais, execução independente dos testes, tetos aplicados, bundle sem rótulos e falhas conservadas. Smoke resolve problemas operacionais; não prova economia. Correção de instrumento exige nova configuração registrada e rodada comparável, sem misturar tentativas anteriores silenciosamente.

**Entrega:** diretórios por trilha/run, relatório de prontidão com bloqueios específicos. Modelo/cota pendentes bloqueiam esta rodada, **não** A01–A03 ou B01–B02.

### TASK-EXP02 — Completar e congelar as 16 tarefas do piloto por trilha

**Prioridade P1; curador com A para SIGA e B para Bitcoin; depois de validar a infraestrutura do smoke.**

Cada catálogo trouxe apenas quatro candidatos para o piloto. Faltam **pelo menos 12 tarefas por trilha**, três por categoria, além de substituições de itens rejeitados. Não declarar o conjunto de 16 pronto nem reduzir silenciosamente o piloto para quatro.

Completar com problemas verificáveis de chamadas entre módulos, falhas reais ou requisitos úteis de teste/configuração, inspecionados no snapshot. Cada item precisa passar pela mesma prova de baseline/referência e análise de ambiente. Não inventar símbolos, issues ou testes para fechar a quantidade.

Os catálogos têm famílias repetidas entre smoke e candidatos piloto (`siga-prop`, `siga-data-localidade`, `btc-authproxy`, `btc-runner`). Se forem usados para ajustar política, excluir essa família do piloto de inferência e buscar substitutos. Não contar pequenas variações do mesmo defeito como tarefas independentes. Esses itens publicados são dev; nenhum é holdout. Curador do holdout precisa selecionar tarefas inéditas e separar famílias e soluções.

**Aceite:** 16 tarefas distintas, balanço 4/4/4/4, aceites independentes, revisão de contaminação e famílias, estimativa financeira com base no smoke e selo antes de resultados. Emenda necessária ao método deve ser registrada antes da rodada correspondente.

### TASK-EXP03 — Rodar piloto, julgar às cegas e medir ganho

**Prioridade P1; depende de EXP01/EXP02 aprovadas para a trilha.**

Executar **16 × 3 × 2 = 96 tentativas por trilha**, com ordem registrada/contrabalanceada e mesmos tetos do pré-registro. Não atualizar core, índice, dataset, modelo ou política no meio da rodada. Falha atribuível ao braço conta contra ele; erro externo comprovado segue regra de reexecução congelada para todos os braços.

Construir bundle cego sem condição, modelo, custo ou ordem. Revisores julgam cumprimento do requisito, regressões e alterações indevidas depois dos testes mecânicos e antes de abrir custos/condições. Aplicar dupla revisão/adjudicação do protocolo. Não chamar revisão apenas por LLM de aceite humano independente.

**Aceite:** julgamentos congelados, chave em custódia, rastreabilidade tentativa→patch→aceite→nota, taxas de sucesso e custo por patch aceito com intervalos agrupados por tarefa. Se não houver sucessos, custo por sucesso é indefinido; não produzir divisão artificial. SIGA e Bitcoin são estudos separados, sem somar suas tentativas como amostra pareada. Resultados negativos e inconclusivos permanecem no relatório.

**Entrega:** relatório gerado dos dados brutos por trilha e decisão sobre próxima hipótese/ablação. Os critérios de economia e qualidade do confirmatório permanecem os do pré-registro; piloto serve para estimar e planejar, não substitui a confirmação dimensionada.

### TASK-EXP04 — Verificar uso real por um desenvolvedor

**Prioridade P2; depois de obter piloto interpretável.**

Registrar o fluxo mínimo de instalação, indexação e pedido de contexto da CLI. Selecionar tarefas dev novas fora do conjunto medido para uma sessão local observada. Cronometrar setup, espera, intervenções e recuperações de erro; incluir índice desatualizado após edição. Não usar participante como juiz de suas próprias tentativas cegas.

**Aceite:** dev consegue concluir um fluxo documentado sem o autor operar a CLI; registrar dificuldades e tempo, sem extrapolar uma sessão para ganho geral. Descobertas de usabilidade viram tarefas de produto com evidência. Mudança posterior na CLI tem nova revisão experimental.

## 5. Execução paralela sem conflito

A mantém este documento, contratos e `benchmarks/rust/**` no checkout principal. B consome checkpoint publicado e mantém tarefas finais, aceites e resultados Bitcoin em sua worktree/namespaces. Cada dono atualiza seu status. Nenhum agente troca branch, reseta, limpa ou escreve na worktree do outro.

SIGA e Bitcoin têm diretórios de tentativa, SQLite/WAL, caches, builds, logs e temporários próprios. Framework Bitcoin recebe aliases/caminhos explícitos; não herdar defaults SIGA. Container/sandbox/usuário separado precisa efetivamente impedir acesso ao ouro, não apenas apontar uma pasta diferente.

Preparação e curadoria podem rodar em paralelo. **Medições de latência/RSS no mesmo host exigem reserva exclusiva e não coincidem com build ou indexação pesada da outra trilha**. Limitar paralelismo de build à memória disponível. Registrar reserva e janela no manifesto; compartilhamento de provedor/cota também exige limite comum conhecido.

Próximas ações imediatas: A começa **A01 e A02**; B começa **B01** depois do checkpoint. Não esperar orçamento para preparar os aceites e o contrato de telemetria. Esta revisão só criou tarefas e documentação; não executou soluções de referência, modelos, piloto ou build completo.
