# Revisão do selo — piloto Bitcoin de 16 (EXP02 completa)

Data: 2026-10-05. Dono: agente B. Estado: **conjunto de 16 selado
(`pilot16.tasks.json`, `sealed:true`), `eval.py validate` limpo, balanço
4/4/4/4, composição travada por hashes em `experiments/bitcoin/rust/2026-10-05-btc-exp02-seal/seal.json`**.

O selo congela, não revalida: cada tarefa já tem vermelho/verde demonstrado no
lote de origem (smoke B01, piloto 05–08 com 07 via TU, lote2 09–12, lote-final
13–16). A geração foi por união programática dos quatro arquivos, sem
reescrita — enunciado, aceite, escopo e origem de cada tarefa são idênticos
aos dos lotes (o teste `test_btc_pilot16_seal.py` quebra se qualquer tarefa
for reescrita).

## 1. Composição

4 smoke (01–04) + 4 piloto (05–08) + 4 piloto2 (09–12) + 4 piloto3 (13–16).
Por categoria: 4/4/4/4. 8 famílias distintas; repetições só em
`btc-descriptors` (01 checksum, 09 `descsum_create`), `btc-p2p-deserialization`
(06 strings, 10 inteiros, 14 `build_message`), `btc-authproxy` (03 charset,
05 opções do proxy, 11 JSON não-objeto) e `btc-runner` (04 `--jobs`,
08 `--fail-if-empty`, 12 `--filter`, 16 `--tmpdirprefix`) — requisitos
disjuntos, já sinalizados nas curadorias. Regra para a rodada de inferência: se
essas famílias forem usadas para ajustar política, excluí-las e buscar
substitutos (EXP02); nenhuma é holdout (todos os itens publicados são dev).

## 2. Arquivos-fonte compartilhados

9 arquivos distintos em `allowed_paths`; 4 compartilhados (defeitos e trechos
disjuntos, aceites independentes por tarefa):

- `descriptors.py`: 01 (checksum), 09 (`descsum_create`).
- `authproxy.py`: 03 (charset), 05 (opções), 11 (JSON não-objeto).
- `test_runner.py`: 04 (`--jobs`), 08 (`--fail-if-empty`), 12 (`--filter`),
  16 (`--tmpdirprefix`).
- `messages.py`: 06 (strings), 10 (inteiros).

Cada tentativa roda em workspace novo com uma só tarefa: compartilhar arquivo
não vaza informação entre tarefas. Compartilhar teste privado também não há —
cada harness e os casos de custódia são por tarefa/lote. Exceção documentada:
07 compila C++ de verdade (TU autocontida + sonda, `g++ -std=c++20`), com
ressalva de que `test_bitcoin`/`util_tests` completos seguem sem executar
(sem depends/sudo).

## 3. Base operacional e estimativa financeira

Aceite medido por tarefa (execução única, referência, 2026-10-05): 01 → 0,04 s;
02 → 0,17 s; 03 → 0,12 s; 04 → 0,76 s; 05 → 0,04 s; 06 → 0,07 s;
07 → 1,21 s (build+run); 08 → 0,33 s; 09 → 0,01 s; 10 → 0,06 s; 11 → 0,04 s;
12 → 0,26 s; 13 → 0,07 s; 14 → 0,08 s; 15 → 0,05 s; 16 → 0,22 s.
`timeout_s` do conjunto é 300 (07: 600).
Custo financeiro por tentativa: **não computável** — nenhum provedor foi chamado
(P1/P2 pendentes, nenhuma tentativa com modelo rodou). A estimativa com base no
smoke que a EXP02 pede fica registrada como pendência de P2, não como número.

## 4. O que o selo não faz

- Não cria holdout: itens publicados são dev; holdout exige curador P4 com
  tarefas inéditas e separação de famílias/soluções.
- Não autoriza rodada paga: seguem bloqueadas por P1 (modelo) e P2 (teto).
- Não congela o dataset, o core comum ou os aceites do SIGA (trilha A).
- Qualquer edição futura no conjunto exige nova revisão registrada e novo selo;
  o teste `test_btc_pilot16_seal.py` quebra se a composição mudar.
