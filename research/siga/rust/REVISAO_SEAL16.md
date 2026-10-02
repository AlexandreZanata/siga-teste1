# Revisão do selo — piloto SIGA de 16 (EXP02)

Data: 2026-10-02. Dono: agente A. Estado: **conjunto de 16 selado
(`pilot16.tasks.json`, `sealed:true`), `eval.py validate` limpo, balanço
4/4/4/4, composição travada por hashes em `experiments/rust/siga/2026-10-02-exp02-seal/seal.json`**.

O selo congela, não revalida: cada tarefa já tem vermelho/verde demonstrado no
lote de origem (smoke A03, piloto 05–08, piloto 09–16). A geração foi por união
programática dos três arquivos, sem reescrita — enunciado, aceite, escopo e
origem de cada tarefa são byte-idênticos aos dos lotes.

## 1. Composição

4 smoke (01–04) + 4 piloto (05–08) + 8 piloto (09–16). Por categoria: 4/4/4/4.
14 famílias distintas; repetições só em `siga-data-localidade` (02 localidade,
07 letras de via) e `siga-prop` (04 `getList`, 08 `getData`) — requisitos
disjuntos, já sinalizados nas curadorias. Regra para a rodada de inferência: se
essas famílias forem usadas para ajustar política, excluí-las e buscar
substitutos (EXP02); nenhuma é holdout (todos os itens publicados são dev).

## 2. Arquivos-fonte compartilhados

13 arquivos distintos em `allowed_paths`; 5 compartilhados (defeitos e trechos
disjuntos, aceites independentes por tarefa):

- `Texto.java`: 01 (extrai), 02 (via data por extenso), 16 (slug).
- `DocumentoUtil.java`: 02 (localidade), 07 (letras de via).
- `Prop.java`: 04 (`getList`), 08 (`getData`).
- `Utils.java`: 09 (form), 10 (zeros), 12 (zip).
- `DateUtils.java`: 11 (intervalo), 13 (formato).

Cada tentativa roda em workspace novo com uma só tarefa: compartilhar arquivo
não vaza informação entre tarefas. Compartilhar teste privado também não há —
cada harness e os casos de custódia são por tarefa/lote.

## 3. Base operacional e estimativa financeira

Aceite medido por tarefa (javac + execução, morno, 2026-10-02): 3,3 s (09),
4,7 s (11), 6,3 s (14); A03 mediu 2–5 s a frio. `timeout_s` do conjunto é 600.
Custo financeiro por tentativa: **não computável** — nenhum provedor foi chamado
(P1/P2 pendentes, nenhuma tentativa com modelo rodou). A estimativa com base no
smoke que a EXP02 pede fica registrada como pendência de P2, não como número.

## 4. O que o selo não faz

- Não cria holdout: itens publicados são dev; holdout exige curador P4 com
  tarefas inéditas e separação de famílias/soluções.
- Não autoriza rodada paga: seguem bloqueadas por P1 (modelo) e P2 (teto).
- Não congela o dataset, o core ou os aceites do Bitcoin (trilha B).
- Qualquer edição futura no conjunto exige nova revisão registrada e novo selo;
  o teste `test_siga_pilot16_seal.py` quebra se a composição mudar.
