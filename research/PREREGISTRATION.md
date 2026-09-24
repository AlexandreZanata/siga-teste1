# Pré-registro preliminar — P1 (não selado, sem execução)

Data: 2026-09-24. Estado: `concluida` como documento preliminar; `bloqueada` como autorização para rodada confirmatória.
ID: P1. Dependências: P0 (`research/AUDIT_BASELINE.md`), código em `f7c5eda`, `plans/PESQUISA_CONTEXTO_MODULAR.md`, `plans/EXPERIMENTOS_2026.md`, `research/16_BASE_EXPERIMENTAL_2026.md`.
Pergunta: o que está fixado antes de qualquer rodada paga e o que só será fixado após o piloto?

Método: só leitura + escrita deste arquivo. Sem alterar `archatlas/*.py`, sem benchmark novo, sem modelo pago, sem dataset alterado. `pytest -q` verde nesta revisão: `24 passed in 38.20s` (offline).
Comandos realmente executados:
- `python -m pytest -q` → 24 passed
- `git rev-parse HEAD` → `f7c5eda9fadd2f0422b31a7863ae7966cc7284e2`
- `git status --short` → limpo antes da criação deste arquivo
Arquivos de entrada: plano vigente §§3–9, E26-00–E26-06, base R26-01–R26-09, AUDIT A1–A11, `benchmarks/siga/PIN.md` (`e3be22828`, Java 21, `desenvolvimento`), `docs/VERIFICATION_PROTOCOL.md`, `docs/ROADMAP_ETAPAS.md`.
Arquivos permitidos nesta etapa: somente `research/PREREGISTRATION.md` (este arquivo).
Aceite P1: cada escolha abaixo tem fonte ou justificativa experimental; novidade permanece hipótese; lacunas que impedem rodada estão explícitas como nulas.

## 1. Pergunta central e hipóteses (fonte: plano §3)

Central: dado mesmo modelo, tarefa, snapshot, ferramentas básicas e limites, a seleção modular de contexto diminui o custo por tarefa resolvida sem perda relevante de qualidade?

- H1 utilidade: menor custo/tarefa resolvida, sucesso dentro da margem de não inferioridade pré-registrada.
- H2 seleção: expansão progressiva > cápsula fixa e > BM25 simples em sucesso/tokens totais.
- H3 estrutura: relações verificadas ajudam entre-arquivos; custo não se justifica automaticamente no local.
- H4 manutenção: incremental ≡ rebuild em lógica e < rebuild em custo para diffs pequenos.
- H5 transferência: contratos/políticas congelados úteis fora do ajuste; medir por repositório e por linguagem separadamente.
- Saída válida inclui negativo/inconclusivo. Proibido selecionar só categorias/modelos onde vence.

## 2. Comparadores (fonte: plano §6 + E26 regras comuns)

- A: agente com busca/leitura convencionais (Read/Grep/Glob/rg). Permite leitura normal; não restringir baseline.
- B: mesmo agente + BM25/FTS5 com trechos sob orçamento (sem relações, sem expansão progressiva).
- C: mesmo agente + ArchAtlas atual congelado (cápsula + `s_router` em `archatlas/strategies.py:34-42@f7c5eda`).
- D (só pós-P3): ArchAtlas modular com expansão progressiva (contratos §5 do plano). Não existe nesta fase.
- Pareamento: mesma tarefa, snapshot inicial, modelo exato, parâmetros, ferramentas básicas, ambiente, limites totais e regra de término por bloco. Só varia disponibilização/política de contexto e seu custo inevitável. Reiniciar sessão/workspace entre execuções; ordem em blocos aleatórios por tarefa/modelo; separar índice frio/quente de cache do provedor; mesma tarefa/modelo nunca compara modelos diferentes entre braços.

## 3. Tarefas e splits (fonte: plano §6 + E26-01 + AUDIT A8)

- Primeiro só SIGA. Piloto P3/F21: 12–20 tarefas executáveis (backend, frontend JSP, entre-arquivos), incluindo simples onde o índice pode custar mais do que ajuda. Piloto calibra protocolo; não prova ganho.
- Cada tarefa: problema independente da solução, snapshot base anterior ao patch, ambiente reproduzível, comportamento esperado, testes públicos, critérios ocultos, timeout, dificuldade prévia. Bugs: teste falha antes / passa depois. UI: critério distingue ausência/presença; screenshot isolado não basta. Sem igualdade textual com patch de referência; compilar + regressões + rubrica semântica.
- Splits por famílias/áreas de mudança (dev/validação/teste final). Nenhuma Q F0–F20 (`benchmarks/siga/queries_dev.json`, 153 Qs) conta como teste inédito; localização segue diagnóstico secundário. Ouro independente do extrator; não indexar enunciados/patches/testes ocultos.
- Holdout: custodiante/processo segregado fora do workspace/índice guarda tarefas finais, testes ocultos e chave de condições. Hash de manifesto ≠ controle de acesso. Quem ajusta recuperador não lê holdout. Abrir o teste 1x por candidato congelado; após abrir, sem retuning no mesmo conjunto (emenda + novo holdout).

## 4. Métricas e critérios (fonte: plano §6 + E26-00 + AUDIT A1–A3)

Primárias (congeladas após o piloto, antes do holdout; proposta atual, não selada):
- Qualidade: proporção resolvida (aceitação + regressão + rubrica) no limite registrado; reportar também 1ª tentativa e retrabalho.
- Eficiência: custo total de todas as tentativas / tarefas resolvidas (falhas + planejamento de contexto + auxiliares + indexação/manutenção amortizadas inclusas). Zero resolvidas → indefinida/infinita, nunca zero. API e infra separados; só combinar com conversão explícita.
- Faixas propostas: perda máxima 5pp no sucesso; economia mínima 20% no custo/resolvida. Sucesso exige IC95% dif. sucesso > −5pp E IC95% razão custos < 0,80. Sem poder → inconclusivo; sem significância ≠ equivalência.

Secundárias: tokens in/out/cache/reasoning por telemetria, tempo ponta a ponta p50/p95, tool calls, arquivos/bytes lidos, regressões, intervenções. Preços/moeda/data/origem junto a estimativas; indisponível = desconhecido; não somar campos que o provedor já agrega.
Diagnóstico (E26-00, P2): separar `hit` (algum arquivo), recall/precisão de conjunto, cobertura de caminho, relações corretas, utilidade para patch, evidências obsoletas; distinguir `retrieved/delivered/opened/declared_relevant`; medir payload serializado inteiro (corrige AUDIT A1: `capsule.py:11-12@f7c5eda` `chars//4` é só estimativa de itens); budgets diagnósticos 2k/8k só com tokenizer/contagem oficial.

## 5. Rubricagem cega (fonte: plano §6)

Patches com IDs aleatórios; avaliador recebe tarefa, snapshot, patch e rubrica — sem modelo/condição/custo/ordem. Julga: aceitação passa, sem regressão, semântica correta, dependências/testes/configs necessários presentes. LLM pode auxiliar, nunca decidir sozinho. Divergência → adjudicação independente antes de abrir rótulos. Registrar pistas de descegamento. Citação válida = `arquivo:linha:símbolo:commit` verificável; sem citação = erro.

## 6. Política de falhas e infra (fonte: plano §6 + E26 comuns)

Reportar separado: falha de infra, timeout, falha do produto. Timeout/crash causado pelo tratamento conta contra ele. Retry de indisponibilidade externa só por regra simétrica prévia; log de todas as tentativas + sensibilidade; sem descartar casos desfavoráveis. Seeds só quando suportadas; temp zero ≠ determinismo; troca silenciosa de versão do modelo abre novo bloco. Volume piloto: 12–20 tarefas × 3 condições × 2 reps × 1 modelo = 72–120 execuções (não autoriza gasto; teto financeiro/temporal obrigatório antes da rodada). Não multiplicar modelos/budgets/ablações antes de depurar o protocolo. Medir frio/quente/amortizado (1/10/100 tarefas); break-even só se economia/tarefa > manutenção.

## 7. Orçamento de contexto e telemetria (fonte: E26 §2 + AUDIT A1)

`chars//4` segue diagnóstico até P2 trocar por contagem oficial/tokenizer pinado. Custo total = instruções de ferramentas + chamadas + histórico + respostas + auxiliares + indexação. Sem telemetria confiável, sem conclusão de economia faturada. E26-00 primeiro: fixtures com parcial/alternativos/spans sobrepostos/inexistente/trecho pós-index; aceite = exatidão nas fixtures, nenhuma métrica completa com 100% por 1 membro, replay reproduz scoring, histórico ≠ cápsula.

## 8. Literatura usada e limites (fonte: base R26-01–R26-09 + plano §4)

Fundamentos 2023–2025 (RepoCoder, Repoformer, RepoGraph, Agentless, SWE-bench, Lost in the Middle) + 9 fichas 2026 (FeatLens 2609.26480v1; CliffCompaction 2609.26779v1; Harness 2609.20804v1; Thousand-Graph 2608.26602v1; Recall Trap 2608.14838v1; Agent Retrieval Bench 2607.24882v1; SWE-Pruner Pro 2607.18213v1; ContextBench 2602.05892v3; SWE-Pruner 2601.16746v4 — consultas 24/09/2026, sem reprodução). Combinação candidata (navegável + seleção opcional + expansão progressiva + validação por execução) é hipótese; cada componente exige ablação (E26-02 primeiro; E26-03/04/05 só se piloto justificar; E26-06 em P6–P7). Alvos iniciais Agent Retrieval Bench + CliffCompaction condicionados a artefato/controle do histórico, senão alternativa E26-02. Novidade não é provada por junção de papers. `research/02_RELATED_WORK.md` segue catálogo histórico em auditoria.

## 9. Manifesto e replay (fonte: plano §9 + E26 §2)

Cada rodada futura registra `manifest.json` (tarefa/split, snapshot + árvore efetiva, ArchAtlas SHA, condição, modelo/provedor/versão, config, prompt+hashes, repetição, ordem, caches, HW, ambiente, timestamps, limites) e `runs.jsonl` (consultas, expansões, evidências `path relativo + span + hash + árvore`, leituras, consumo, erros, patch, avaliações) + `REPORT.md`. Reprodução = ambiente + entradas + cápsulas determinísticas + scoring refeitos; saídas LLM guardadas para replay do avaliador. Respeitar exclusões; nunca copiar blobs AGPL (só ponteiros+hashes+scripts); dataset read-only em `e3be22828`.

## 10. Lacunas que bloqueiam rodada (nulas até resolver)

IDs efetivos de modelos (rótulos: Muse Spark 1.3 / DeepSeek Flash v4.1 / Luna 6 — sem confirmação de disponibilidade/IDs/capacidades); teto de custo/tempo; ambiente build/teste SIGA executável; custodiante do holdout; 2+ repos externos para P6; responsáveis pela rubrica semântica. Resolver na preparação da rodada correspondente. Antes disso, só especificação documental.

## 11. Decisão e próximo passo

Decisão: P1 preliminar concluída (documento não selado). Não autoriza piloto nem confirmatório. Próximo: **P2** (contratos, telemetria `retrieved/delivered/opened/declared_relevant`, replay, tarefas smoke; só então o mínimo A/B/C). Completar antes de P5: dimensão amostral pós-piloto (potência 80%, inferência pareada por tarefa, bootstrap/estimadores, não inferioridade, multiplicidade), teto de gasto, modelos/snapshots/pesos/prompts/limites exatos e manifesto selado.
