# Pré-registro final — P5 (selável, NÃO selado; sem execução)

Data: 2026-09-24. ID: P5-prep. Depende de P0–P4 e E26-00–06 (núcleos offline).
Estado: documento selável; selo real e rodada bloqueados (§4). Nenhum número abaixo
autoriza gasto, modelo ou teste — lacunas nulas com motivo travam o selo.

## 1. Congelado agora (fontes: P1 + AUDIT + E26-00–06)

- Pergunta e H1–H5 (`research/PREREGISTRATION.md` §§1–2, inalteradas; novidade = hipótese).
- Braços A (busca/leitura), B (BM25+trechos), C (ArchAtlas congelado em `519958a`);
  D (modular progressivo) especificado, inexistente — não entra no confirmatório.
- Budgets diagnósticos 2k/8k (`chars//4` até P2; payload inteiro após E26-00).
- Margens: perda máxima 5pp no sucesso; economia mínima 20% no custo/resolvida.
  Sucesso exige IC95% dif. sucesso > −5pp E IC95% razão custos < 0,80.
- Métricas: primárias (proporção resolvida; custo total/tarefas resolvidas, ∞ se zero);
  secundárias (tokens por telemetria, p50/p95 ponta a ponta, tool calls, regressões);
  diagnóstico (`hit` vs `recall_set`/`precision_set`, `retrieved/delivered/opened`,
  payload inteiro) — nomes distintos, parcial nunca 100%.
- Cegamento: patches com IDs aleatórios, avaliador sem modelo/condição/custo/ordem,
  adjudicação antes de abrir rótulos; 1 abertura por candidato congelado, sem retuning.
- Falhas: infra/timeout/produto separados; timeout do tratamento conta contra ele;
  retry só por regra simétrica prévia; todos os logs, análise de sensibilidade.
- Manifestos (`manifest.json`: tarefa/split, snapshot+árvore, SHAs, modelo, config,
  prompt+hashes, repetição, ordem, caches, HW, timestamps, limites) + `runs.jsonl` +
  replay determinístico do avaliador.
- Componentes (E26): packing `multi` default; entidades sem arestas candidatas no
  retrieval (relações só seletivas, pendentes de patch); `focus` opcional off-default;
  gate duro de abstenção descartado, bandeira `uncertain` candidata; histórico sem
  extensão; CLI `doctor/context`, sem MCP.

## 2. Dimensionamento (fórmulas congeladas; números pendentes do piloto real)

- H1 confirmatória (não inferioridade do sucesso + superioridade do custo); H2–H5
  exploratórias (sem correção familiar cruzada; dentro de cada, correção declarada).
- Inferência pareada com agrupamento por tarefa; potência alvo 80%; estimadores +
  bootstrap pré-registrados aqui antes do holdout (método: percentil por tarefa).
- Entradas do cálculo (NULAS até o piloto real): taxa de sucesso por braço,
  pares discordantes, variância de custos. Piloto: 12–20 tarefas × 3 condições ×
  2 reps × 1 modelo (72–120 execuções, calibração — nunca prova).
- Sem poder → inconclusivo; sem significância ≠ equivalência; negativo publica.

## 3. Tarefas, splits e holdout (P1 §3 + E26-01, inalterados)

Splits por famílias/áreas (dev/validação/teste final); nenhuma Q F0–F20 como teste
inédito; ouro independente do extrator; checkout anterior ao patch; bloqueio a
commits futuros/soluções/testes ocultos; custodiante segregado; hash de manifesto ≠
controle de acesso; quem ajusta não lê o holdout.

## 4. Trava do selo (tudo nulo = sem rodada)

| campo | estado |
|---|---|
| hipóteses/braços/métricas/rubrica/falhas/estatística/manifesto | PREENCHIDO (§§1–3) |
| IDs efetivos de modelos | NULO (rótulos Spark 1.3/Flash v4.1/Luna 6 não resolvidos) |
| teto financeiro/temporal | NULO |
| ambiente build/teste SIGA executável | NULO |
| custodiante do holdout + testes ocultos | NULO |
| estimativas do piloto real (N, pares, variância) | NULO (piloto real não executado) |
| 2+ repos externos (P6) e responsáveis pela rubrica | NULO |

Selo = todos preenchidos + hash deste arquivo + data + assinatura do custodiante.
Até lá: selável, sem autorização.

## 5. Decisão e próximo passo

P5-prep concluída como documento. Próximo desbloqueado sem modelo/teto: **P6-prep**
(selecionar 2+ repos externos antes do teste, com builds reproduzíveis — um na stack
suportada, outro em stack distinta). P5-real, P6-exec e P7 seguem travados pelo §4.
