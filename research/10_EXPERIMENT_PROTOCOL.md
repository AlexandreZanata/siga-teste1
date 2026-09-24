# 10 — Protocolo Experimental

**Status:** DRAFT 2026-09-24. Principal: Muse Spark 1.3 × condições (A-grep, B-BM25, C-vector, E-Atlas; D se 5 braços) + sweeps.

## 1. Congelamento (bloqueante)
`SIGA_SHA` (+`BTC_SHA` separado; nunca agregar Java+C++), modelo+provider+versão+reasoning+data+temp(0)+seeds, índice/baselines/adaptadores (config.id, pesos, k/depth/fanout, BM25, embeddings), `pre-registration.md` (grade, métricas, testes, hash do test selado). Mudança = emenda datada.

## 2. Harness
`archatlas benchmark run --experiment ID --siga-sha SHA --model "Muse Spark 1.3" --conditions A,B,C,E --budgets 500,…,32000 --splits dev,test --seeds 1,2,3 --repeats 3 --out artifacts/ID.jsonl` + `report` (R1–R3, curva, COSTS, PRIVACY). Infra-falha = `infra_error`, nunca `incorrect`; retry mesma seed + tentativa.

## 3. Randomização e grade
Questões embaralhadas por seed (blocos A–G); condições em quadrado latino; budgets crescentes (reuso c/ `cache_hit`); ≥3 reps; retrieval/cápsula byte-idênticos entre reps (divergência = bug); contexto LLM resetado (`prompt_hash`). Ordem: (1) principal 2k dev+test; (2) budget sweep E(+D) 7 budgets; (3) multi-hop C depth×fanout; (4) incremental 1/10/100 vs rebuild; (5) ablações 1-componente em 2k dev; (6) privacidade (bytes externos + destino + base).

## 4. Estatística (pré-registrada)
Unidade = questão; micro-média/categoria → macro-média. IC95% bootstrap 10k seed fixa (Recall, grounded, RCCR, UCD, mediana Time-to-correct + IQR). Pareados: McNemar (binário) / Wilcoxon (contínuo) + Holm–Bonferroni (família fixada). Curva sem assumir monotonicidade. Efeito + p; TBD até execução.

## 5. Ameaças e checklist
Vazamento (focar grounded/citação; janela temporal; corte do modelo); GT ruidoso (validador + acordo); configs desiguais (revisão pré-run); custo/latência (mesmo HW/região + preços); overfit dev (test 1 acesso final); nondeterminismo (hashes replay; divergência invalida). Checklist: SHAs, modelo, configs+hash test, grade, métricas+testes+correção, orçamento de acessos, definições RCCR/UCD/adjudicação.
Log JSONL obrigatório/rodada: `experiment_id, siga_sha, model/provider/version/reasoning/date/temp/seed, prompt_hash, retrieval_config, budget, capsule_hash, context_files, response, tokens_in/out/reasoning, tool_calls, files_opened, lines_transferred, latency_ms, cost, source_bytes_transmitted, scores{recall,mrr,ndcg,symbol,path,grounded,hallucination,citation,rccr,ucd}, timestamp` (+Parquet). Aceite: 100% schema válido + replay + test dentro do orçamento; senão rodada descartada.
