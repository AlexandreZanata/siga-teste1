# E26-01 repeat R3 — gate de abstenção dev-calibrado (84 rodadas)

Data: 2026-09-24. ID: E26-01-R3. Mudança desde R2: `archatlas/abstain.py` +
`build_capsule(abstain=True)`; índice idêntico (851 arqs). `REPORT.md`/`REPEAT_R2.md`
congelados; este arquivo registra a repetição do gate.
Regra (calibrada E avaliada no mesmo dev — otimista; holdout pendente):
reter sse `seeds==0 AND lex==0` (`no-local-evidence`); bandeira `uncertain` sse
entregue e (`seeds==0 OR lex==0 OR top>-1.0`). Braços: LEX + ATLAS-multi/1p-2k-gate.
Saídas: `runs_r3.jsonl` + `manifest_r3.jsonl`.

## R2 → R3 (positivos, 20 casos)

| braço | hit | recall | gate-retenções | uncertain |
|---|---|---|---|---|
| ATLAS-multi-2k | 0.45 → 0.40 | 0.325 → 0.275 | 5/20 | 9/15 entregues |
| ATLAS-1p-2k | 0.55 → 0.45 | 0.40 → 0.325 | 5/20 | 9/15 entregues |
| LEX | 0.10 → 0.10 | 0.05 → 0.05 | N/A | N/A |

Delta de descoberta: exatamente 1 hit perdido — E01-C2C-02 (R2 True → R3 False),
descoberta genuína via fallback com zero sementes/lex. Negativos: gate retém 7/8
(WR-03 escapa: lex 18 fraco, mas recebe `uncertain=True`).

## Decisão

Gate duro **descartado como default**: troca 1 descoberta real por 7 abstenções
rotuladas — viola "preservar descoberta". Adotado como candidato sem perda:
**entregar + bandeira `uncertain`** (C2C-02 mantido E sinalizado; WR-03 sinalizado).
Retenção dura só onde a entrega seria vazia de qualquer modo (rotulagem gratuita).
Abstenção correta com preservação total segue sem solução nesta arquitetura —
limite registrado para P5/P6 (interface que exija confirmação antes de agir com
`uncertain=True` é o próximo teste honesto, não um novo threshold no mesmo dev).
