# E26-01 — recuperar a próxima evidência (diagnóstico dev, sem modelo)

Data: 2026-09-24. ID: E26-01 (adaptação de R26-06 + R26-08). Depende de P2.
Código: `archatlas/telemetry.py:score_additional` + cápsula congelada/E26-02.
Estado: `concluida` como diagnóstico; sem promoção a confirmatório.
Heads: repo `e6fde13`, dataset `e3be22828` (841 arqs Java main, 1.45s em `/tmp/opencode-p3/e01.sqlite`).
Método: 28 casos dev (`benchmarks/siga/e26_01_dev.json`: 20 positivos 5×4 tipos + 8
negativos 4 naturais + 4 wrong-repo) × 5 braços (LEX sem budget; ATLAS-multi/one_per_file
@2k/8k) = 140 rodadas, 1 rep, ordem `sha256(id+cond)%10`. Medida só sobre
ADICIONAIS (`delivered − given`); consultas não nomeiam arquivos esperados; ouro dev
(existência em disco verificada, sem holdout; E01-C2T-04 aproximado, limitação registrada).
Sem thresholds calibrados: abstenção só por vazio. Saída bruta: `runs.jsonl` (140).

## Resultados positivos (20 casos; recall sobre adicionais)

| braço | hit | recall | todos-necessários | payload p50 |
|---|---|---|---|---|
| LEX | 0.10 | 0.05 | 0.00 | — |
| ATLAS-multi-2k | 0.30 | 0.175 | 0.05 | 6427 |
| ATLAS-multi-8k | 0.30 | 0.175 | 0.05 | 6994 |
| ATLAS-1p-2k | 0.30 | 0.175 | 0.05 | 1829 |
| ATLAS-1p-8k | 0.30 | 0.175 | 0.05 | 1829 |

Por tipo (ATLAS-multi-2k vs LEX): code2test 0.0/0.0; trace2code 0.2/0.2;
comment2context 0.6/0.2; edit2ripple 0.4/0.0. 2k≡8k em cobertura (só payload muda).

## Resultados negativos (8 casos; sem recall convencional)

Abstenção correta: LEX 0.875 (7/8 vazios) vs ATLAS 0.0 (0/8 — cápsula sempre entrega,
até 33 arquivos novos em NAT-02; wrong-repo entrega ≥3 via fallback refs).
Nenhum braço distingue "sem evidência local" de "fora de cobertura": não há mecanismo
de abstenção, só vazio acidental.

## Diagnóstico (3 achados que mudam o plano)

1. **code2test 0/5 em TODOS os braços (inclusive LEX):** `src/test` não está no índice
   (só `src/main/java` é indexado) — lacuna de cobertura, não de ranking. Nenhuma
   política vence onde o índice não cobre. Correção P4: indexar testes como fonte
   recuperável (contrato P2) ou declarar sem suporte; repetir E26-01 após.
2. **ATLAS preserva descoberta onde há cobertura** (comment 0.6 vs 0.2, ripple 0.4 vs 0.0)
   com mesmo custo de decisão por vir — mas **não deixa incerteza explícita**
   (abstenção 0.0, inclusive wrong-repo). Pela regra da ficha, sem promoção:
   utilidade em edição (P3 real) segue não comprovada.
3. **Economia de empacotamento replicada:** one_per_file ≡ multi em cobertura com
   ~1/3 do payload (1829 vs 6427); 8k≡2k em arquivos. Budget da cápsula não move
   cobertura aqui — decisão de budget fica para curvas de custo do plano §6, não
   para este diagnóstico.

## Decisão

Sem promoção de política; sem aumento do lote de edições. Próximo: P4 indexar testes +
mecanismo de abstenção explícita (thresholds calibrados só no dev), depois repetir
E26-01 no dev antes de qualquer confirmatório. Limites: n=20+8 dev, 1 rep, sem modelo
(patch nulo), sem IC; E01-C2T-04 aproximado; efeito só no recuperador da cápsula.
