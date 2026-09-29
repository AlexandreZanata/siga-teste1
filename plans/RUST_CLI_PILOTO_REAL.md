# CLI Rust: construir, medir e validar em patches reais

Data: 2026-09-29. Estado: **plano de execução; implementação Rust e piloto ainda não iniciados por esta revisão**.

Objetivo: entregar um executável local que o agente invoque por shell para obter contexto verificável rapidamente e, depois, demonstrar se isso reduz custo e esforço para produzir patches corretos. Rust é a linguagem escolhida para o produto; menor memória e latência são hipóteses a medir, não consequências garantidas dessa escolha.

Este plano é a próxima sequência operacional das duas trilhas. Complementa o [método científico](PESQUISA_CONTEXTO_MODULAR.md) e o [isolamento entre agentes](PARALLEL_EXECUTION.md); substitui a orientação de continuar ampliando diagnósticos offline antes de tentar um piloto real. O [protocolo de medição](../research/rust/PROTOCOLO_VALIDACAO.md) define comparadores, amostra, custo e cegamento. [Estado da execução](rust/STATUS.md).

## 1. O que aproveitar e o que corrigir

Base inspecionada: SIGA/core `db3e714`; worktree Bitcoin `3623afb`. São checkpoints observados, não o futuro candidato Rust. Há implementação Python, CLI, índices, fixtures e relatórios reutilizáveis. Preservar esses artefatos como referência; não reescrever todo o projeto antes de medir valor.

Os experimentos revelaram lacunas de cobertura, vantagens de empacotamento, necessidade de invalidação e limites de relações textuais. Ainda faltam patches avaliados, telemetria faturada e uso humano. Diagnóstico concluído não equivale a P3/P5/P7 concluída.

Antes de novas alegações, corrigir no novo harness:

- No E26-01 Bitcoin, a lista inteira de candidatos foi pontuada independentemente do budget; `used_tokens` não recortava essa lista. O novo avaliador mede **a resposta efetivamente entregue após o corte**, conservando o resultado antigo como diagnóstico de candidatos.
- `opened` não pode ser cópia de `delivered`: exige evento real de leitura. Reproduzir uma fórmula sobre logs não prova a correção do recuperador nem o cegamento.
- `chars//4` e budget por item não garantem limite de tokens do JSON completo. Contar a resposta final com tokenizer identificado; telemetria do provedor mede custo real da sessão.
- Índice com paths C++ registrados não significa extração de símbolos C++. Capacidade lexical é aceitável para o primeiro piloto, explicitamente rotulada.
- Rever os estados das fases com seus donos: preparação, implementação, ensaio, execução real e confirmação são aceites diferentes. Documentos históricos ficam preservados; o estado atual aponta para evidências mais recentes.

## 2. Produto mínimo para o agente

Nome de trabalho do executável: `archatlas`. Um binário Rust, sem Python no caminho normal de execução, usado pelo shell que o agente já possui. Recuperação local sem chamada de LLM, servidor, rede ou GPU. O harness experimental pode continuar em Python: mede processos e modelos, não faz parte da CLI distribuída.

Jornada: o desenvolvedor cria o índice uma vez; o agente pede contexto, abre fontes ou expande quando necessário, edita com suas ferramentas usuais, atualiza o índice e roda testes. O binário nunca escreve patches por iniciativa própria. `--help` curto e exemplos suficientes para uso sem carregar toda a documentação na conversa.

Comandos **propostos, ainda inexistentes em Rust**:

```sh
archatlas doctor --repo <checkout> --index <indice> --format json
archatlas index --repo <checkout> --index <indice>
archatlas context --repo <checkout> --index <indice> --request <pedido.json>
archatlas expand --repo <checkout> --index <indice> --request <expansao.json>
archatlas index --repo <checkout> --index <indice> --incremental
archatlas verify --repo <checkout> --index <indice> --ref <referencia>
```

No uso experimental, repo e índice sempre explícitos. Após validação, descoberta automática da raiz e diretório local ignorado pelo Git podem simplificar instalação; nunca herdar o DB global legado. Cada worktree tem identidade e índice próprios.

Pedido JSON: `schema_version`, `intent` (localizar/editar/testar/impacto/desconhecido), `query`, `known_refs`, `snapshot`, `budget_tokens`, `tokenizer_id`, `max_bytes`, `policy`. Expansão inclui referências já entregues e a evidência desejada. Limites de entrada/saída e orçamento total da tarefa são separados. Não há inferência de uma suposta intenção interna da LLM.

Resposta JSON compacta: versão, snapshot e geração do índice; estado `ok/partial/stale/unsupported`; trechos com path relativo, linhas, hash, tipo de evidência e motivo; contagem do payload, unidade/tokenizer; número e motivos agregados de omissões; pistas curtas de expansão. Não despejar centenas de paths, logs ou relações para fora do budget. Detalhes de diagnóstico vão para arquivo próprio, fora do contexto.

Contrato de processo: stdout contém um único JSON, stderr contém diagnóstico breve sem código-fonte; saída 0 para resposta válida (`partial` é explícito), 2 para pedido inválido, 3 para índice ausente/incompatível/desatualizado sem resposta válida, 4 para erro de I/O ou limite operacional. Congelar códigos na especificação antes da implementação. O agente pode usar busca/leitura normal em qualquer estado; não esconder um rebuild caro dentro de `context`.

## 3. Arquitetura Rust com escopo controlado

Começar com um pacote em `rust/archatlas/`, módulos internos para `cli`, `request`, `discovery`, `store`, `retrieve`, `pack`, `snapshot` e `languages`. Separar crates só quando houver necessidade concreta. Fixar toolchain, `Cargo.lock`, features e licenças; não escolher versões aqui como se já tivessem sido instaladas/testadas.

Decisões iniciais a validar:

- SQLite + FTS5 como candidato de armazenamento/busca lexical, reaproveitando o desenho conhecido. SQL com top-K limitado, leitura preguiçosa dos trechos e transações em lotes. Índice Rust tem schema próprio versionado; não abre DB Python para migrá-lo silenciosamente.
- Descoberta genérica respeita exclusões e inclui testes, configuração e documentação quando suportados. Registrar arquivos ignorados, binários e grandes demais. Sem paths/SHA SIGA embutidos.
- Indexação lê um arquivo por vez, limita tamanho, workers e filas; ponto de partida de dois workers no índice e um na consulta. Não manter corpus, ASTs e texto duplicado integralmente em RAM. Cache e top-K têm limites medidos.
- MVP lexical para arquivos textuais; seleção de trechos e contexto em torno de matches. Extração sintática Java/Python/C++ é extensão seguinte, candidata via Tree-sitter, com gramáticas pinadas. Árvore sintática não equivale a resolução de tipos, overloads ou chamadas. Build C++ e `compile_commands.json` são necessários quando a técnica exigir semântica de compilação, não para bloquear a busca textual.
- Atualizações publicam uma geração consistente do índice, com hash/config/versão. Delete, rename e mudanças de exclusão invalidam registros; leitores não misturam gerações. Um escritor por índice, leitores isolados e teste de crash/lock.
- Fontes selecionadas são verificadas novamente antes de entregar texto. A descoberta de novos arquivos requer atualização: o runner a executa após edições e antes de consultas dependentes. Hash dos arquivos selecionados sozinho não prova completude. Sem atualização comprovada, indicar `stale`/cobertura parcial ou usar fallback; cobrar varreduras e atualização no tempo real.
- Sem daemon no MVP. Medir custo de iniciar o processo. Um modo persistente/stdio só entra como experiência separada se startup for gargalo; medir sua memória ociosa e acumulada. MCP é transporte posterior, não dependência do piloto.

Não portar automaticamente cada heurística Python. Preservar uma política simples de referência e incluir política progressiva apenas com contrato verificável. Foco, relações, embeddings, resumos e histórico são ablações futuras; não entram juntos numa primeira comparação causal.

Política CTX-RS inicial proposta: recuperar candidatos lexicais, selecionar trechos diversos com contexto local verificável e permitir `expand` por referência/arquivo explicitamente solicitado pelo agente, deduplicando spans já entregues. Sem expansão automática ilimitada de includes. Contrastar com LEX-RS, que entrega top-K lexical com empacotamento fixo. Ambos permitem novas consultas e leitura normal; a comparação mede o pacote de política, não isola causalmente cada detalhe. Ablações posteriores mudam um fator por vez.

## 4. Orçamento realmente aplicado

Ordem obrigatória: gerar candidatos → ranquear → selecionar trechos → montar JSON → contar a serialização final → remover/encurtar unidades permitidas → serializar/contar novamente → entregar → avaliar somente o que foi entregue. Testar Unicode, escaping, metadados, truncamento e erro de budget menor que o envelope mínimo.

O payload inclui referências, instruções/pistas retornadas e campos de contagem. Verificar a contagem após preencher esses campos; convergir até `payload_tokens <= budget_tokens`. Truncamento preserva limites de texto válidos e sinaliza perda de contexto; não declarar trecho incompleto como definição completa.

Tokenizer local deve corresponder ao modelo e ter versão/hash verificados. Sem tokenizer compatível, usar limite exato em **bytes**, declarar tokens estimados e retirar a alegação de budget rígido em tokens. Esse modo permite piloto real se houver telemetria do provedor, com a unidade de seleção congelada antes da rodada. Não transformar ausência de tokenizer local em ausência de qualquer experimento.

Orçamento de cápsula não inclui o histórico já acumulado, prompts e saídas do modelo: todos entram no custo e limite globais do runner. Logs extensos de omissão nunca escapam como conteúdo ocultamente gratuito.

## 5. Metas propostas de desempenho

São metas de produto a congelar em R0, não medições realizadas. Primeira plataforma: Linux x86_64, SSD, recursos reservados e máquina documentada. Coorte pequena/média proposta: até 5 mil arquivos e 256 MiB de texto elegível; declarar tamanho real de cada corpus. Coortes maiores são ensaio de escala separado.

- Processo novo `doctor` com filesystem aquecido: p95 até 50 ms e RSS máximo até 32 MiB.
- `context` com índice pronto, resposta até 8k tokens: p95 até 150 ms e RSS máximo até 96 MiB, incluindo abertura do processo/DB, verificação de fontes e serialização.
- Indexação: RSS máximo até 256 MiB; acompanhar duração, CPU, disco e bytes indexados. Arquivos acima do limite documentado não podem ser ignorados silenciosamente para cumprir a meta.
- Atualização de um arquivo até 100 KiB na coorte: p95 até 500 ms incluindo detecção; medir também 10/100 arquivos, delete, rename e troca de branch.

Limites internos de cache não são limites absolutos de RSS. Medir processo e filhos; em ambiente isolado, medir também memória atribuída ao grupo e cache de páginas. Não usar apenas tamanho do heap Rust. Testar limites controlados de memória e falha explícita sem corromper DB.

Comparar build release padrão com poucas variantes guiadas por perfil (por exemplo LTO thin). Escolher por latência, RSS, tamanho e correção; não assumir que `opt-level=3`, `z`, outro allocator ou mmap sempre melhora tudo. Otimização só após perfil identificar o gargalo.

## 6. Sequência executável e critérios de saída

### R0 — contrato, verdade dos estados e ambiente

Entradas: checkpoints atuais e este plano. A consolida capacidades reais, contrato CLI e protocolo de custo; B atualiza estados Bitcoin sem apagar histórico. Definir dois snapshots de desenvolvimento, recursos, modelo efetivo, medição de custo e responsável por testes/revisão. Identificar desde já build/teste que realmente executa em cada trilha. Se Bitcoin estiver bloqueado, SIGA pode seguir; não substituir silenciosamente o projeto alvo.

Saídas futuras: `research/rust/BASELINE.md`, `CLI_CONTRACT.md` e pré-registro do piloto de cada trilha. Aceite: checklist de medição independente e cada pendência com dono/ação; zero fase real concluída apenas por documentação. Não exigir estimativas do piloto ou confirmação P5 para autorizar o próprio piloto.

### R1 — uma fatia funcional em Rust

Implementar `doctor`, `index`, `context` com busca lexical e payload limitado; incluir um repositório real e fixtures independentes. Testar erro, atualização, exclusão, rename e equivalência lógica com rebuild. Rust executa o caminho inteiro sem subprocesso Python. Aceite: fonte citada corresponde aos bytes do snapshot, nada excede unidade de orçamento declarada, processo é invocável pelo agente e índices são isolados.

Não esperar grafo, parser semântico, daemon ou port completo. Depois dessa fatia, começar imediatamente a preparação das tarefas reais em paralelo com os demais testes técnicos.

### R2 — microbenchmarks e integração com runner real

Comparar Python congelado versus Rust com mesma política, corpus e entradas canônicas; divergência de semântica invalida alegação de ganho devido apenas à linguagem. Se não houver equivalência, publicar comparação entre produtos distintos. Medir frio/aquecido e corpus maior conforme protocolo. Implementar `expand` e atualização necessária ao ciclo editar/testar; integrar por shell a um único executor/modelo real.

Aceite: relatório de latência/RSS/CPU/índice com repetições e scripts reproduzíveis; fixtures de contagem da resposta efetiva; runner captura todas as chamadas, custos e patches sem acesso ao ouro. Metas não atendidas são registradas; abrir orçamento de otimização limitado, sem esconder o problema nem adiar indefinidamente o piloto.

### R3 — smoke com modelo e piloto real

Executar primeiro quatro tarefas dev inéditas no smoke; três condições, uma tentativa cada: 12 execuções por trilha. Verificar patch produzido, testes, telemetria e reset. Não usar stubs como aceite. Corrigir infraestrutura antes de congelar piloto.

Depois, 16 tarefas distintas do smoke × três condições × duas repetições = **96 execuções reais por trilha**, um modelo. SIGA e Bitcoin independentes: 108 por trilha somando smoke; 216 se ambas rodarem. Contagens não incluem retries previstos nem confirmações futuras. Procedimento, limites e custos no protocolo. Aceite: resultados reais completos, falhas incluídas e revisão cega dos patches; não exige resultado positivo.

### R4 — decidir e fazer no máximo uma rodada de ajuste planejada

Analisar tarefas em que faltou evidência, contexto sobrou, expansão ajudou ou o índice ficou desatualizado. Selecionar candidato em validação dev separada, registrar todas as variantes e o custo da busca. Se o piloto não mostrar sinal útil, simplificar e investigar a falha antes de aumentar a amostra. Ajuste requer nova versão; não repetir o mesmo dev como prova independente.

Aceite: candidato e baseline confirmatórios congelados, estimativas para dimensionamento, custo máximo da confirmação e plano estatístico selados. Se orçamento não permitir amostra adequada, publicar piloto/inconclusivo; não alargar a margem de qualidade depois de ver os resultados.

### R5 — confirmação cega em tarefas reservadas

Comparar candidato congelado com baseline operacional pré-selecionado; controle lexical adicional só se planejado/orçado. Executar amostra dimensionada no piloto, em ambiente separado da equipe que ajustou o seletor. Julgar patches antes de abrir condições e custos. Cada trilha apresenta seu próprio resultado; outra linguagem/modelo é uma replicação, não mistura de médias.

Aceite científico: critérios de qualidade e custo do protocolo, ou resultado negativo/inconclusivo claramente publicado. Não marcar conclusão pela existência de um arquivo de pré-registro ou teste de embaralhamento de IDs.

### R6 — utilidade para desenvolvedores e distribuição

Após candidato tecnicamente estável, testar instalação e trabalho real com 4–6 desenvolvedores, quatro tarefas equivalentes por pessoa, ordem contrabalanceada e sem repetir a mesma tarefa para a mesma pessoa. Amostra exploratória de usabilidade: tempo de instalação, assistência, revisão, retrabalho, abandono e percepção de esforço; não prova estatística populacional.

Entregar binário versionado, checksum, instrução curta de instalação/remoção, schema e capacidades por linguagem. Validar ambiente Linux limpo; macOS/Windows são portabilidades futuras com suas próprias medições. Publicação só conforme escopo autorizado na execução. Aceite: outro dev instala e usa o ciclo sem ajuda do autor e limitações estão documentadas.

## 7. Dois agentes sem reescrita concorrente

Mantém-se A = core/SIGA e B = Bitcoin. **A é único escritor de `rust/**`, `research/rust/**`, `plans/rust/**`, `benchmarks/rust/**` e `experiments/rust/**`**, além das áreas comuns anteriores. B é único escritor dos namespaces Bitcoin e prepara tarefas, regressões e relatórios Bitcoin; pede extensões Rust ao A com caso mínimo, sem alterar workspace Cargo ou criar outro core.

B usa binário publicado com hash e versão do contrato em sua worktree, junto de índice próprio. Artefatos do build Rust, ambientes e serviços não são compartilhados de forma gravável. A publica checkpoint funcional cedo; B prepara build/testes/datasets enquanto isso. Atualizações só entre rodadas. Integração e reserva de CPU/RAM seguem o protocolo paralelo.

O snapshot antigo do plano Bitcoin na main não representa progresso da worktree B. A primeira ação é ler o estado real de cada dono, não reiniciar BTC-P0. O custodiante/avaliador independente é um papel necessário da pesquisa, não presumidamente outro agente com acesso ao mesmo diretório.

## 8. Papers e referências de implementação

Usar a [base de 2026](../research/16_BASE_EXPERIMENTAL_2026.md) como origem das hipóteses: ContextBench/Agent Retrieval Bench para instrumentação; Recall Trap para trechos e profundidade; Harness Design para ambiente fixo. FeatLens/Thousand-Graph, poda neural e CliffCompaction ficam como ablações condicionadas às falhas do piloto. Não há reprodução integral nem ganho transferido automaticamente dos papers.

Fontes técnicas primárias consultadas em 2026-09-29; fixar versões efetivas em R0/R1:

- [Cargo: perfis](https://doc.rust-lang.org/cargo/reference/profiles.html): perfis release e opções de otimização; a documentação recomenda experimentar configurações, sem garantia de que nível maior seja mais rápido.
- [SQLite FTS5](https://www.sqlite.org/fts5.html): mecanismo candidato de busca textual/BM25.
- [SQLite: cache_size](https://www.sqlite.org/pragma.html#pragma_cache_size): configuração de cache; não é teto de memória total do processo.
- [Tree-sitter: uso de parsers](https://tree-sitter.github.io/tree-sitter/using-parsers/): candidato para extração sintática posterior, sem alegação de resolução semântica.

## 9. Entrega final exigida

Binário Rust utilizável + comandos reproduzíveis + manifestos e logs sanitizados + patches e julgamentos + custos reais + medições de recursos + limitações. Toda conclusão declara dataset, modelo, hardware, versões, unidade de amostra e intervalo de incerteza. A frase “mais rápido e econômico” só será usada no escopo que passar nos testes correspondentes.
