# Contratos P2 — especificação mínima + telemetria/replay/smoke

Data: 2026-09-24. ID: P2 (parte 1: infra de medição). Depende de P1. Código em `fadd5c9`.
Estado: especificação congelada para A/B/C; D segue inexistente até P4.
Fontes: plano §5 (contratos), §6 (pareamento/isolamento), E26-00/E26-01, AUDIT A1–A4, `research/PREREGISTRATION.md` §§2–9.

## 1. Contratos (nomes de campos congelados)

- **Snapshot:** `{sha_base, tree_hashes, dirty, extractor_version, caps}`. `sha_base` sozinho não representa working tree (AUDIT A9). P2 registra `sha_base=e3be22828` + `tree_hashes` quando houver edição local; P3 exigirá ambos por execução.
- **Solicitação:** `{goal, query, known, snapshot, delivered_so_far, budget_left}`. `goal ∈ {localizar, entender, editar, testar, impacto, desconhecido}`.
- **Recuperadores:** `lexical | symbols | relations | tests | config | docs`. Assinatura: `(con, query) -> arquivos`; nunca recebem GT/holdout.
- **Montador (cápsula):** saída inclui `symbols, files, excerpts, citations, relations, truncation_log, budget{requested, used, tokenizer}, stats{candidates, kept, retrieved}, payload_tokens, telemetry{retrieved, delivered, delivered_files, payload_chars, payload_tokens, opened, declared_relevant=null, history_tokens=null}`. `used` = soma de itens (compat F5); `payload_tokens` = serialização inteira (`archatlas/telemetry.py:payload_tokens_for_capsule`). Histórico/instruções fora deste número, com `history_note`.
- **Avaliador:** `archatlas/telemetry.py:score_delivery(delivered, gt)` — recebe só esses dois args (isolamento por assinatura). Retorna `{hit, recall_set, precision_set|null, expected_count, delivered_count, matched, kind, error}`. `package` → completas `null` (denominador desconhecido); `gt-vazio` → hit False, nunca exceção.
- **Manifesto:** `archatlas/telemetry.py:build_manifest(task_id, condition, repetition, order, budget, sha)` — sem relógio; pareamento A/B/C verificável offline.
- **Replay:** `rescore_runs` + `verify_replay` — mesmo log → mesmo escore (determinismo por `sort_keys`).

## 2. Telemetria (o que cada nome significa)

`retrieved` = candidatos do ranking; `delivered` = itens sob budget efetivamente serializados; `opened` = leituras explícitas fora da cápsula (0 na cápsula; harness futuro contará); `declared_relevant` = autorrelato do agente (sempre `null` aqui — não presumir uso pelo raciocínio); `history_tokens` = `null` com motivo (P3 medirá custo total). Budgets diagnósticos 2k/8k só com tokenizer/contagem oficial; `chars//4` segue estimativa.

## 3. Métricas (rótulos corrigidos, compat preservada)

- `hit`/`recall` legado no harness = taxa de algum-esperado (não chamar de recall completo).
- `hit_rate` = alias do legado; `recall_set_mean`/`precision_set_mean` = médias das completas (ignora `null` de `package`).
- Nenhuma métrica completa dá 100% por um membro (`tests/test_e26_00.py` prova com 1/4 → hit True, recall 0.25).
- `payload_tokens >= used` em geral (overhead JSON); ambos `<=` budget? Não: `used<=budget` é garantido (F5); `payload_tokens` é medido e reportado, podendo exceder `used` — orçamento da serialização inteira passa a ser visível (E26-00 aceite).

## 4. Smoke simulado (sem faturamento, sem holdout)

`tests/test_e26_00.py` verifica offline: parcial 1/4, alternativas/precisão, spans sobrepostos + determinismo de payload, arquivo inexistente sem crash, trecho alterado pós-index detectado via `verify_symbol` (hash divergiu), replay reproduz escore, histórico não contado como cápsula, manifesto de pareamento determinístico, isolamento do avaliador (sem `con`/disco na assinatura). Smoke real com modelo segue bloqueado (pendências P1 §10: IDs/teto/ambiente/custodiante).

## 5. Erros e isolamento

Harness envolve cada query em try/except: falha vira linha JSONL (`hit False`, `error`) + entrada em `errors[]`, nunca aborta o lote. Avaliador nunca toca índice/disco. Executor nunca lê GT além de entregar a escore puro após a entrega (mesma separação do plano §5: avaliador consome logs/patches; GT/testes ocultos fora do índice do executor — aqui, fora da assinatura do avaliador).

## 6. O que fica para P3

Tarefas executáveis 12–20, manifests por execução com árvore efetiva, custo total (tentativas + auxiliares + indexação amortizada), p50/p95 ponta a ponta, frio/quente/amortizado. Nenhuma alegação de economia/qualidade nesta P2.
