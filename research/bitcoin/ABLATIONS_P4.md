# BTC-P4 — Ablações e candidato (escopo sintético; sem piloto real)

Data: 2026-09-24. Dono: agente B. `core_sha`: `e6fde134...e2ed9f033` (só leitura).
Variante local experimental: `btc-pack/1` (`archatlas/bitcoin/packing.py`, commit deste
checkpoint — ver STATUS). Nenhum fork oculto do core; nenhuma política geral nova (nada a
propor ao A nesta rodada). Decisão final de cada componente exige piloto real; abaixo, o
estado honesto por experimento.

## E26-02 espelho — profundidade vs arquivos: EXECUTADO (sintético)

`experiments/bitcoin/e26_02/btc-e2602-synth-001/` (manifesto + REPORT, 4/4 em
`tests/bitcoin/test_btc_packing.py`). Resultado: `expanded` (2 pares, 113 tok) > `multi`
(0 pares, 108 tok) > `one_per_file` (0 pares, 48 tok, perde profundidade) no repo sintético.
Decisão: `expanded` candidato; produto final `evidência insuficiente` sem piloto.

## E26-03 espelho — entidades e relações: NÃO EXECUTADO

Nenhuma entidade/relação implementada; controle sem arestas permanece o padrão por ausência
de alternativa, não por vitória. Oportunidade e desenho (mapa → entidades → expansão ligada/
desligada) registrados em `LITERATURE_APPLICATION.md` (R26-01/R26-04). Nada a simplificar ou
descartar além de manter o produto sem grafo até evidência do piloto.

## E26-04 espelho — foco e poda: NÃO EXECUTADO (neural fora)

Filtro neural e Pro seguem excluídos (sem modelo de pesos abertos, servidor compatível ou
recursos medidos). Campo `focus` existe nos contratos como opcional; seleção determinística
é a única implementada (via políticas `btc-pack/1`). Ativação condicionada a falhas do piloto
que a justifiquem.

## E26-05 espelho — contexto acumulado: INDISPONÍVEL

Nenhuma pressão real de contexto observada (sem rodada viva); sem acesso ao histórico do
cliente, a ferramenta de retrieval segue utilizável e o experimento marcado indisponível
naquele cliente — sem bloquear BTC-P2–P4.

## Candidato congelado BTC-P4 (sintético)

`C_btc = core(e6fde13) + btc-cpp-lex/1 + btc-pack/1(expanded candidato)` — congelado NESTE
commit (SHA a registrar no STATUS após push). Vale para fixtures sintéticas; revalidação
obrigatória no corpus pós-PIN antes de qualquer confirmatório. Tentadas: 1 variante de
empacotamento (3 políticas, mesma base); descartadas: nenhuma além de `one_per_file` como
padrão (perde pares); simplificadas: grafo (não construído).
