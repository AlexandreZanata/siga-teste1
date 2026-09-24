# BTC-P1 — Aplicação da literatura (R26-01–R26-09) ao Bitcoin

Data: 2026-09-24. Dono: agente B. Etapa: BTC-P1. `BASE_SHA`: `e6fde134f7da0d3616d90c40232d9ebe2ed9f033`.
Entrada: `research/16_BASE_EXPERIMENTAL_2026.md` (revisão congelada em 24/09/2026:
metadados, resumo e seções de método/avaliação indicadas nas fichas; sem reprodução,
sem download de modelos, sem auditoria completa de artefatos) + `research/bitcoin/AUDIT_BASELINE.md`
(A1–A7). Nenhuma consulta nova é afirmada aqui; versões abaixo são as da base.
Aplicabilidade C++/Python é hipótese nossa, não resultado transferido dos papers.

## R26-01 — FeatLens (2609.26480v1) → E26-03 espelho

Subgrafo por tarefa a partir de descrições funcionais + PageRank personalizado; índice offline
com descrições/embeddings. Sem repo dos autores identificado na base.
Aplicabilidade Bitcoin: descrições derivadas de código C++ teriam origem, hash e custo
registrados; entradas candidatas (mudança RPC, comportamento mempool) testadas contra
busca plana e controle sem arestas. Limite: overloads, templates e macros não são
resolvidos pelo índice (AUDIT A1); semear só o tratamento com o alvo invalida a comparação.

## R26-02 — CliffCompaction (2609.26779v1) → E26-05 espelho

Compactação literal por limiar sobre conteúdo original, com perda deliberada; repo dos
autores indica MIT e modo proxy. Aplicabilidade Bitcoin: só onde controlarmos o histórico
enviado; ferramenta de retrieval isolada não altera histórico do cliente. Diagnóstico
alvo: logs longos de compilação como evidência a preservar, não texto descartável por
definição. Reprodução futura fixa commit/config; sem serviço global nesta pesquisa.

## R26-03 — Harness Design (2609.20804v1) → E26-05/E26-06 espelho

Ciclo fixo, variando planejamento/ferramentas/gestão de contexto; benefícios dependem de
modelo e orçamento. Aplicabilidade Bitcoin: comparar políticas com ferramentas fixas;
depois CLI vs ferramenta estruturada com as mesmas evidências; medir uso real da expansão.
Implementação local das condições será adaptação (implementação oficial reutilizável não
confirmada na base).

## R26-04 — Thousand-Graph (2608.26602v1) → E26-03 espelho (controle sem grafo)

Entidades persistidas, busca global/local, sem arestas pré-construídas; o próprio texto
distingue sucesso comportamental de prova de mecanismo. Aplicabilidade Bitcoin: controle
mapa de módulos → entidades → trechos antes de qualquer relação; se entidades bastarem,
simplificar. Taxas publicadas não são referência (detalhamento insuficiente na base);
sem código executável confirmado — hipótese de menor prioridade, não reprodução.

## R26-05 — Recall Trap (2608.14838v1) → E26-02 espelho (primeiro mecanismo pós-piloto)

Um-trecho-por-arquivo vs profundidade no mesmo arquivo sob mesmo orçamento; efeito muda
com BM25 e some com leitura irrestrita. Aplicabilidade Bitcoin: par header/implementação
é o caso canônico onde múltiplos trechos do "mesmo arquivo lógico" podem importar;
deduplicar spans idênticos ≠ proibir dois trechos úteis. Qualidade do patch decide, não recall.
Depósito Zenodo na base: conteúdo/licença não auditados; sem reprodução afirmada.

## R26-06 — Agent Retrieval Bench (2607.24882v1) → E26-01 espelho

`code2test`, `trace2code`, `comment2context`, `edit2ripple` + negativos naturais e de
repositório errado; ranking/cobertura/abstenção como objetivos distintos.
Aplicabilidade Bitcoin: ouro próprio por revisão independente (alteração C++ → testes
unitários/funcionais; falha C++/Python/RPC → implementação além do frame; comentário de
revisão → contratos ainda não fornecidos; diff → consumidores/testes afetados). Casos sem
ouro local exigem evidência independente; falta de parser ≠ ausência de arquivo relevante.
Arquivo já fornecido na pergunta não conta como descoberta. Versão do dataset externo a
fixar separadamente da v1 do paper; licenças/downloads na preparação da execução.

## R26-07 — SWE-Pruner Pro (2607.18213v1) → condicional, fora do MVP

Poda por estados internos do modelo + integração ao servidor; inaplicável a APIs sem esse
acesso. Decisão: referência condicional para E26-04 espelho; só com modelo de pesos abertos,
servidor compatível e recursos medidos. Não trocar executores para viabilizar o paper;
indisponibilidade registra-se, sem bloqueio dos demais experimentos.

## R26-08 — ContextBench (2602.05892v3) → E26-00/E26-01 espelho

`retrieved`/`delivered`/`opened`/`declared_relevant` em arquivos/blocos/linhas + resultado
do patch; autorrelato ≠ prova causal de uso. Aplicabilidade Bitcoin: mesma instrumentação
sobre fixtures C++/Python auditadas (definição em header, implementação em outro arquivo,
overload homônimo, spans sobrepostos, ouro alternativo, arquivo removido, mudança pós-index);
payload serializado inteiro na contagem; replay deve reproduzir scoring. Pacote de dados
externo depende de release/licença localizados — adaptação com dados locais primeiro.

## R26-09 — SWE-Pruner (2601.16746v4) → E26-04 espelho (opcional)

Foco opcional do agente + filtro auxiliar 0,6B; interface observável da necessidade atual.
Aplicabilidade Bitcoin: comparar saída completa vs seleção determinística vs filtro neural
com mesmo foco/candidatos; auditar preservação de assinaturas, guards, `#ifdef` e contexto
que distingue overloads; medir custo do filtro e releituras. Código oficial indica MIT;
scripts dos autores pedem multi-GPU — dimensionamento separado, sem dependência obrigatória.
Sem presumir transferência Python→C++.

## Ordem de aproveitamento Bitcoin (mesma régua, dataset próprio)

1. E26-00/E26-01 espelho (instrumentar + tarefas da próxima ação do dev) em BTC-P2–P3.
2. E26-02 espelho primeiro mecanismo pós-piloto (BTC-P4).
3. E26-03 (com controle sem grafo) e E26-04 opcional só se falhas do piloto justificarem.
4. E26-05 só sob pressão real de contexto observada; E26-06 especificado em BTC-P1, integrado em
   BTC-P4, usado em BTC-P6–P7. SWE-Pruner Pro só em trilha futura com infra compatível.

Nenhum componente entra no candidato por recência ou por número publicado; cada um exige
hipótese e ablação próprias. Resultado negativo/inconclusivo é saída válida.
