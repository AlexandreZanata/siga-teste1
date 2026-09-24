# E26-01 repeat R2 — com `src/test` no índice (mesmo protocolo, 140 rodadas)

Data: 2026-09-24. ID: E26-01-R2. Mudança desde R1: `archatlas/harness.py`
indexa `siga-ex/src/test/java` + `siga-cp/src/test` (841→851 arqs, 1.97s).
`REPORT.md` (R1) congelado; este arquivo registra a repetição pré-declarada em E26-01.
Casos, braços, budgets e métricas idênticos (28×5=140; medida só adicionais).
Saídas brutas: `runs_r2.jsonl` + `manifest_r2.jsonl`.

## R1 → R2 (positivos, 20 casos)

| braço | hit | recall | todos-necessários |
|---|---|---|---|
| LEX | 0.10 → 0.10 | 0.05 → 0.05 | 0.00 → 0.00 |
| ATLAS-multi-2k | 0.30 → 0.45 | 0.175 → 0.325 | 0.05 → 0.20 |
| ATLAS-multi-8k | 0.30 → 0.55 | 0.175 → 0.40 | 0.05 → 0.25 |
| ATLAS-1p-2k/8k | 0.30 → 0.55 | 0.175 → 0.40 | 0.05 → 0.25 |

code2test ATLAS: 0/5 → 3/5 (C2T-01/03/05 recall 1.0; C2T-02/04 miss).
Negativos inalterados: abstenção ATLAS 0.0, LEX 0.875 (mecanismo segue ausente).

## Leitura

1. Cobertura cria recuperação (E26-01 achado 1 resolvido parcial): +10 arquivos de teste
   no índice dobraram o recall ATLAS sem mudar ranking — nenhuma política faria isso.
2. Budget volta a importar com índice maior: 8k>2k em arquivos (R1: 8k≡2k); one_per_file
   entrega cobertura de 8k com payload de 2k (replica E26-02).
3. Restante aberto: C2T-02/04 (ranking, não cobertura), abstenção explícita (c),
   distinção main-vs-test no ranking (limite declarado no harness).

## Decisão

E26-01 segue sem promoção a confirmatório (patch nulo, abstenção ausente).
Próximo P4-infra(c): abstenção explícita calibrada no dev + repetir (R3).
