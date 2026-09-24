# Pré-registro preliminar Bitcoin — BTC-P1 (não selado, sem execução)

Data: 2026-09-24. Dono: agente B. ID: BTC-P1. Dependências: BTC-P0
(`research/bitcoin/AUDIT_BASELINE.md`, `benchmarks/bitcoin/PIN.md`, `benchmarks/bitcoin/CENSO.md`),
código em `e6fde134f7da0d3616d90c40232d9ebe2ed9f033`, `plans/PESQUISA_CONTEXTO_MODULAR.md`,
`plans/EXPERIMENTOS_2026.md` (fichas canônicas E26-00–E26-06), `research/16_BASE_EXPERIMENTAL_2026.md`,
`research/bitcoin/LITERATURE_APPLICATION.md`, `docs/VERIFICATION_PROTOCOL.md`.
Estado: `concluída` como documento preliminar; `bloqueada` como autorização para qualquer rodada.
Método desta etapa: só leitura + escrita de arquivos Bitcoin; sem alterar `archatlas/`, sem benchmark,
sem modelo pago, sem dataset. Mesmo método da trilha SIGA; nenhuma autorização (financeira, modelo,
dimensão amostral) é herdada — tudo próprio abaixo, parte ainda nula.

## 1. Pergunta central e hipóteses

Central: dado mesmo modelo, tarefa, snapshot, ferramentas básicas e limites operacionais, a seleção
modular de contexto diminui o custo por tarefa resolvida sem perda relevante de qualidade — no Bitcoin Core.

- H1 utilidade: menor custo/tarefa resolvida, sucesso dentro da margem de não inferioridade pré-registrada.
- H2 seleção: expansão progressiva > cápsula fixa e > BM25 simples em sucesso/tokens totais.
- H3 estrutura: relações verificadas ajudam tarefas entre-arquivos; custo não se justifica no local.
- H4 manutenção: incremental ≡ rebuild em lógica e < rebuild em custo para diffs pequenos (inclui
  invalidação de dependências de headers compartilhados, não só do arquivo editado).
- H5 temporal (não transferência entre projetos): contratos/políticas congelados mantêm utilidade em
  snapshots/famílias de tarefas posteriores do próprio Bitcoin. Bitcoin é dataset de desenvolvimento;
  generalização entre repositórios exige projetos inéditos (fora desta trilha).
- Saída válida inclui negativo/inconclusivo. Proibido selecionar só categorias/modelos onde vence.

## 2. Comparadores

- A: agente com busca/leitura convencionais. Leitura normal permitida; não restringir baseline.
- B: mesmo agente + BM25/lexical com trechos sob orçamento (sem relações, sem expansão progressiva).
- C: mesmo agente + core congelado com adaptador Bitcoin mínimo. Se C exigir correção para funcionar,
  publicar `C_btc_adapter` com lista de adaptações e SHA; não apresentá-lo como ArchAtlas original.
  Sem suporte, registrar `unsupported` como limite — sem substituir C por D silenciosamente.
- D (só pós-piloto): variante modular com expansão progressiva; mesmo adaptador entre comparações
  de política. Variante local experimental recebe nome/hash, nunca fork oculto.
- Pareamento: mesma tarefa, snapshot inicial, modelo exato, parâmetros, ferramentas básicas, ambiente,
  limites totais e regra de término por bloco. Sessão/workspace reiniciados; ordem em blocos aleatórios
  por tarefa/modelo; índice frio/quente separado de cache do provedor; builds limpos/reutilizados como
  condições documentadas iguais entre braços (não economia do recuperador).

## 3. Tarefas e splits (candidatas; a confirmar no snapshot pinado)

Famílias candidatas: RPC, validação/mempool, wallet, rede, testes C++/Python — primeiras tarefas podem
cobrir essas áreas conforme o snapshot efetivo; nenhuma lista de tarefas é afirmada aqui. Piloto BTC-P3:
12–20 tarefas executáveis locais e entre-arquivos, incluindo testes C++/Python e comportamento RPC quando
adequado; evitar lote só de renomeação/documentação; incluir simples onde o índice pode custar mais do
que ajuda. Piloto calibra protocolo; não prova ganho.
Cada tarefa: problema independente da solução, snapshot base anterior ao patch, ambiente reproduzível
isolado/regtest, comportamento esperado, testes públicos, critérios ocultos, timeout, dificuldade prévia.
Para bugs, teste falha antes / passa depois com solução válida; sem igualdade textual com referência;
compilar + regressões + rubrica semântica. Splits por famílias/áreas de mudança (dev/validação/teste
final). Gabaritos independentes do extrator; nunca indexar enunciados, patches de resposta ou testes
ocultos. Nenhuma tarefa SIGA conta como dado Bitcoin. Custódia: humano/processo segregado fora do
workspace/índice guarda tarefas finais, testes ocultos e chave; quem ajusta recuperador não lê holdout;
abrir 1x por candidato congelado; após abrir, sem retuning no mesmo conjunto.

## 4. Métricas e critérios (proposta atual; a congelar pós-piloto, pré-holdout)

Primárias: proporção resolvida (aceitação + regressão + rubrica) no limite registrado; custo total de
todas as tentativas / resolvidas (falhas + planejamento de contexto + auxiliares + indexação/manutenção
amortizadas; zero resolvidas → indefinida/infinita). API e infra separados; só combinar com conversão
explícita. Faixas propostas (escolhas de produto, não derivadas dos papers): perda máxima 5pp no sucesso;
economia mínima 20% no custo/resolvida; sucesso exige IC95% dif. sucesso > −5pp E IC95% razão custos < 0,80.
Sem poder → inconclusivo; sem significância ≠ equivalência. Amostra confirmatória dimensionada pelo piloto
Bitcoin (potência 80%, inferência pareada por tarefa); repetições ≠ tarefas independentes.
Secundárias: tokens in/out/cache/reasoning por telemetria, p50/p95 ponta a ponta, tool calls,
arquivos/bytes lidos, regressões, intervenções; indisponível = desconhecido. Diagnóstico (E26-00 espelho,
BTC-P2): `hit` vs recall/precisão de conjunto vs cobertura de caminho; `retrieved/delivered/opened/
declared_relevant`; payload serializado inteiro; budgets diagnósticos 2k/8k só com tokenizer oficial.
`compile_commands.json`, quando produzido, integra o ambiente versionado por hash.

## 5. Rubricagem cega

Patches com IDs aleatórios; avaliador recebe tarefa, snapshot, patch e rubrica — sem modelo/condição/
custo/ordem. Julga: aceitação passa, sem regressão, semântica correta, dependências/testes/configs
necessários presentes. LLM pode auxiliar, nunca decidir sozinho. Divergência → adjudicação independente
antes de abrir rótulos. Registrar pistas de descegamento. Sem fundos/carteira pessoal/mainnet em nenhum
resultado — ambiente isolado/regtest conforme snapshot.

## 6. Política de falhas e volume

Infra/timeout/falha do produto reportados separadamente; timeout/crash do tratamento conta contra ele.
Retry externo só por regra simétrica prévia; log de todas as tentativas + sensibilidade. Seeds só quando
suportadas; temp zero ≠ determinismo; troca silenciosa de versão do modelo abre novo bloco. Volume piloto:
12–20 tarefas × 3 condições × 2 reps × 1 modelo = 72–120 execuções (NÃO autoriza gasto; teto
financeiro/temporal próprio obrigatório antes da rodada — ainda nulo). Não multiplicar modelos/budgets/
ablações antes de depurar o protocolo. Medir frio/quente/amortizado (1/10/100 tarefas).

## 7. Lacunas que bloqueiam rodada (nulas até resolver)

`BTC_SHA` (PIN); toolchain/flags/dependências do snapshot + comandos reais de build/teste; IDs efetivos de
modelos (rótulos: Muse Spark 1.3 / DeepSeek Flash v4.1 / Luna 6 — sem confirmação de disponibilidade);
teto de custo/tempo próprio; custodiante do holdout; responsáveis pela rubrica semântica; disponibilidade
de `compile_commands.json`; adaptação C++ (parser/build) — diagnóstico de retrieval pode avançar sem build,
piloto de patches não. Projetos inéditos de transferência ficam fora desta trilha.

## 8. Decisão e próximo passo

Decisão: BTC-P1 preliminar concluída (documento não selado). Não autoriza piloto nem confirmatório.
Próximo: **BTC-P2** (contratos em `CONTRACTS_P2.md`, adaptador `archatlas/bitcoin/**`, fixtures/testes
`tests/bitcoin/**`, manifesto de build/índice, E26-00 espelho; falta de extensão genérica vira pedido
`BTC-CORE-NNN`, nunca edição direta do core). Antes de BTC-P5, completar: dimensão amostral pós-piloto,
teto, modelos/snapshots/pesos/prompts/limites exatos e manifesto selado.
