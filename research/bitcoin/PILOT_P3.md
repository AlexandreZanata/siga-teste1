# BTC-P3 — Especificação do piloto de edição real (sem execução; dryrun cobre a plumbing)

Data: 2026-09-24. Dono: agente B. Pré-requisito: BTC-P2 (`CONTRACTS_P2.md`, `btc-cpp-lex/1`).
Piloto real (72–120 execuções com modelo) **bloqueado**: `BTC_SHA` indefinido, toolchain do
snapshot não registrada, IDs de modelo não resolvidos, teto próprio não fixado, custodiante
não designado (ver `PREREGISTRATION.md` §7). O dryrun offline desta etapa valida pareamento,
orçamento, isolamento e registro de erros; **não valida qualidade de retrieval nem autoriza gasto**.

## 1. Lote e tarefas

12–20 tarefas executáveis (dryrun: 12, `benchmarks/bitcoin/pilot_p3_dev.json`, IDs `BTC-P3D-001–012`;
sem soluções ou patches embutidos). Famílias candidatas: `rpc`, `validation` (inclui mempool),
`wallet`, `network`, `tests` (C++/Python). Cada tarefa real futura terá: problema independente da
solução, snapshot base anterior ao patch, ambiente isolado/regtest reproduzível, comportamento
esperado, testes públicos, critérios ocultos (`oculto:BTC-P3D-xxx`), timeout ≥60s e budget de
cápsula 2000. Misturar alterações locais e entre arquivos; incluir simples onde o índice pode
custar mais do que ajuda; nunca lote só de renomeação/documentação.

## 2. Braços (mesmo lote, mesmos custos inevitáveis por bloco)

- **A_busca**: agente com busca/leitura convencionais (leitura normal permitida, sem restrição artificial).
- **B_bm25**: mesmo agente + BM25/lexical com trechos sob orçamento (sem relações, sem expansão).
- **C_adapter**: mesmo agente + core congelado (`core_sha`) com adaptador Bitcoin mínimo publicado
  (`C_btc_adapter` = `btc-cpp-lex/1` + lista de adaptações e SHA se corrigido; `unsupported` registrado
  como limite se faltar suporte — sem troca silenciosa por D). Mesmo adaptador entre comparações de política.
- Pareamento: mesma tarefa, snapshot, modelo exato, parâmetros, ferramentas básicas, ambiente, limites
  e regra de término por bloco; ordem em blocos aleatórios por tarefa/modelo; sessão/workspace
  reiniciados; índice frio/quente separado de cache do provedor; builds limpos/reutilizados como
  condições documentadas iguais entre braços (não economia do recuperador).

## 3. Aceitação e custos

Aceitação combina testes de comportamento (falha antes / passa depois), regressões e revisão
semântica cega; sem igualdade textual com referência. Custo total inclui falhas, planejamento de
contexto, chamadas auxiliares e indexação/manutenção amortizadas; timeout/crash do tratamento conta
contra ele; retry externo só por regra simétrica prévia. `patch_accepted`/`cost_total` do dryrun são
**nulos com motivo** (sem modelo, sem telemetria faturada).

## 4. Dryrun desta etapa

`archatlas/bitcoin/dryrun.py` executa 12 tarefas × 3 braços × 2 repetições = 72 rodadas offline com
executores-armas determinísticos rotulados `stub` (qualidade NÃO interpretável): A por busca textual,
B por ranking de frequência, C pelo adaptador real (`cpp_lex`). Saídas em
`experiments/bitcoin/pilot_p3/btc-pilot-dryrun-001/` (`manifest.jsonl`, `runs.jsonl`, `REPORT.md`).
Verifica: pareamento completo, `used ≤ 2000`, isolamento do avaliador (`score_delivery` só vê
`delivered/gt`), replay exato e 1 falha sintética injetada registrada sem abortar o lote.
