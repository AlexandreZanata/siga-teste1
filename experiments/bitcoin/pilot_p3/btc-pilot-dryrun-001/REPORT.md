# BTC-P3 dryrun — REPORT (`btc-pilot-dryrun-001`)

Pergunta: a plumbing do piloto (pareamento, orçamento, isolamento, erros) funciona antes de
qualquer rodada com modelo? Método: 12 tarefas × 3 braços × 2 repetições = **72** rodadas offline
com executores `stub` (qualidade NÃO interpretável; braço C exercita o adaptador real).
Comando: `run_dryrun()` (`archatlas/bitcoin/dryrun.py`, seed 7). Saídas: `manifest.jsonl`, `runs.jsonl`.

## Medições (plumbing, não qualidade)

- 72/72 pares (tarefa, braço, repetição) presentes, ordens 1–72 únicas por rodada de repetição.
- `used ≤ 2000` em 72/72; `payload_tokens ≥ used` em 72/72; `recall_set` médio 0.986 e `hit` 1.0
  **entre rodadas sem erro — valores de stubs em fixtures minúsculas, sem significado de produto**.
- 1 erro registrado sem abortar o lote: `BTC-P3D-007/B_freq/rep2` (`RuntimeError` sintética injetada).
- Replay: `score_delivery(delivered, gt)` reproduz `hit`/`recall_set` em 72/72; avaliador só vê
  `(delivered, gt)`; `patch_accepted`/`cost_total` nulos com motivo em 72/72.

## Falhas e limites

Falha real: nenhuma (só a injetada). Limites: sem modelo, sem dataset, sem latência, sem custo
faturado; braços A/B são stubs textuais. Este dryrun **não valida retrieval e não autoriza gasto**;
qualidade sem modelo é sem confirmação possível.
piloto real segue bloqueado (PIN, toolchain, modelos, teto, custodiante).

## Decisão

Plumbing `manter` para o piloto real; qualidade `evidência insuficiente` por definição do dryrun.
Próximo: `BTC_SHA` + ambiente, depois piloto A/B/C com teto próprio e avaliação cega.
