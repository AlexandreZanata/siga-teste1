# Piloto P3 — dry-run offline de calibração (sem modelo, sem confirmação)

Data: 2026-09-24. ID: P3-dryrun. Depende de P2 (`4bc1460`).
Estado: `concluida` como calibração do protocolo; `bloqueada` como prova de ganho.
Pergunta: o protocolo A/B/C pareia, orça, isola e registra erros em 12 tarefas dev sem faturamento?

Método: só retrieval offline, sem LLM, sem patch, sem holdout. Índice Java
(`siga-ex/cp/wf`, 841 arqs, 1.55s em `/tmp/opencode-p3/p3.sqlite`, SHA `e3be22828`).
Comandos executados: indexação acima + 36 rodadas (12 tarefas × 3 proxies × 1 rep).
Heads: repo `4bc1460`, dataset `e3be22828f787cbe71b339aecb7a7bf569099803`.
Proxies honestos de retrieval (não são agentes editores): `A_lex=s_lexical`,
`B_cap=s_hybrid_refs(2k)`, `C_router=s_router`. Ordem por `sha256(task+cond)%6`
(blocos determinísticos). Avaliador só `(delivered, gt)` via
`archatlas/telemetry.py:score_delivery`.
Entradas: `benchmarks/siga/pilot_p3_dev.json` (12 dev: 5 backend, 3 frontend, 4 cross;
snapshot base + `public_check=mvn compile` como especificação não executada aqui;
`hidden_criteria` só ponteiros fora da árvore do executor).
Saídas: `manifest.jsonl` (36) + `runs.jsonl` (36) neste diretório.

## Resultados de retrieval (diagnóstico, n=12 dev — não confirmatório)

| cond | hit | recall_set médio | p50/p95 (s) | payload p50 |
|---|---|---|---|---|
| A_lex | 0.667 | 0.417 | 0.0027/0.048 | nulo (sem cápsula) |
| B_cap | 0.750 | 0.625 | 0.1014/0.1488 | 6461 tk (min 966, max 7010) |
| C_router | 0.750 | 0.556 | 0.0672/0.2115 | nulo (só arquivos) |

Pareamento: 36/36 `(task,cond)` presentes, 1 rep, ordens 0–5, budget 2000,
`used<=2000` em 12/12 B_cap. Replay: `verify_replay` passa (determinístico).
Erros: 0 exceções (lote sem aborto); misses são `hit False` legítimos, não crashes.

## Diagnóstico de falhas (o que o dry-run revelou)

1. **Frontend JSP fora do índice:** P3D-006/007/008 zeram nas 3 condições
   (JSP `siga/.../login.jsp`, `associarLogin.jsp`, `sigaex/index.jsp` não estão no
   índice Java `siga-ex/cp/wf`). Esperado pelo contrato P2 (capacidades por linguagem):
   retrieval Java não prova nada sobre edição JSP. Tarefas frontend seguem válidas como
   especificação, mas sem cobertura de retrieval até adaptador JSP declararem suporte.
2. **Orçamento de itens ≠ payload:** B_cap respeita `used<=2000` e mesmo assim entrega
   966–7010 tk serializados (p50 6461). Confirma AUDIT A1/P2: `chars//4` por item não
   limita o custo real; P3 real deve orçar pela serialização + histórico + chamadas.
3. **P3D-001 (backend) miss em A_lex** com recall 0.0/2 entregues: lexical sozinho perde
   a validação de assinatura; B/C recuperam (a checar no relatório por tarefa em `runs.jsonl`).

## Custos e qualidade (nulos por desenho — bloqueiam confirmação)

`patch_accepted=null` (36/36, "sem modelo"), `cost_total=null` (36/36, "sem telemetria
de modelo/teto"). Compilação `mvn` e testes de comportamento não executados neste
dry-run. Sem IC, sem não inferioridade, sem razão de custos: qualquer diferença acima é
diagnóstica. Pendências P1 §10 seguem abertas: IDs efetivos (Spark 1.3 / DeepSeek Flash
v4.1 / Luna 6), teto financeiro/temporal, ambiente build/teste SIGA executável,
custodiante do holdout, rubrica semântica. Piloto real (72–120 execuções pagas) só após
essas travas + manifesto selado (P5).
