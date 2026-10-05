# Revisão do selo piloto-16 — NEXT-02

Data: 2026-10-05. Revisor: agente A (curador do lote). Estado: **piloto SIGA
corrigido e selado: 16 tarefas exclusivamente piloto, 4/4/4/4, smoke separado**.

Selo: `experiments/rust/siga/2026-10-05-next02-pilot-seal/seal.json`
(`atlas-pilot-seal/1`). Conjunto:
[`benchmarks/siga/rust/piloto16.tasks.json`](../../../benchmarks/siga/rust/piloto16.tasks.json)
(`sha256:919b83c1b084…`, `sealed:true`, `eval.py validate` limpo e balanceado).

## 1. O que o selo conserta (sem reescrever história)

O inventário selado em 2026-10-02 (`pilot16.tasks.json`, `sha256:6b9ea882…`)
continua válido **como inventário**: 4 smoke + 12 piloto congelados. Ele só não
atende sozinho ao desenho do pré-registro (4 smoke **mais** 16 piloto). Este
selo publica o piloto corrigido sem tocar naquele arquivo:

- **12 tarefas 05–16 copiadas fiéis** do inventário antigo (byte a byte no
  conteúdo das tarefas; conferido por teste de união fiel).
- **4 tarefas novas 17–20** do lote `pilot3.tasks.json` (1 por categoria).
- **Smoke fora do arquivo**: `piloto16.tasks.json` não contém 01–04; a
  sobreposição smoke∩piloto é vazia (conferido por teste).

## 2. Conferências do selo

| Checagem | Resultado |
|---|---|
| 16 tarefas, `split: piloto` em todas | 16/16 |
| Balanço por categoria | 4/4/4/4 |
| IDs 05–20, sem sobreposição com smoke 01–04 | vazio |
| 05–16 fiéis ao inventário selado antigo | byte a byte |
| Aceites disponíveis (`run-pilot3.sh` + 4 harnesses) | javac, exit ≠ 0 em falha |
| Baseline vermelho + referência verde no lote novo | 3/8, 6/9, 6/10, 12/14 → 8/8, 9/9, 10/10, 14/14; privado 6/11 → 11/11 |
| Runners antigos congelados | shas conferidos no selo |
| Pacote sem ouro | só hashes; referências e privados em custódia fora do git |

## 3. Famílias e arquivos compartilhados

15 famílias distintas no piloto; repetição interna só em `siga-acao` (17/18,
defeitos e trechos disjuntos). Sobreposição com o smoke só nas já conhecidas
(`siga-data-localidade`, `siga-prop`), com a regra de exclusão registrada antes
de qualquer resultado de modelo (ver curadoria §4). Arquivos compartilhados com
trechos disjuntos: `Texto.java` (16/19/20), `AcaoVO.java` (17/18), `Utils.java`
(09/10/12), `DateUtils.java` (11/13). Cada tentativa roda em workspace novo com
uma só tarefa.

## 4. Limites do selo

O selo congela inventário + aceites + revisão; não é resultado de modelo,
custo ou julgamento. Holdout segue com o curador (P4). O piloto mede o escopo
declarado (utilitários Java isolados + 4 integrações); generalizar além disso
exige a integração do domínio (NEXT-08).
