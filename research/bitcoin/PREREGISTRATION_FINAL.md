# Pré-registro final Bitcoin — BTC-P5 (selável; rodada bloqueada)

Data: 2026-09-24. Dono: agente B. Base: `research/bitcoin/PREREGISTRATION.md` (BTC-P1),
candidato `C_btc` (BTC-P4), maquinaria `btc-seal/1` (`archatlas/bitcoin/seal.py`, ensaiada em
`experiments/bitcoin/p5_seal/btc-p5-rehearsal-001/` — VOID). Estado: documento pronto para selar;
**selo real e rodada bloqueados** (sem piloto dimensionador, sem custodiante, sem `BTC_SHA`).
Nada aqui autoriza execução.

## 1. Congelamento pré-rodada (valores a fixar no selo real; atuais entre parênteses)

- Tarefas finais + splits por família/área (candidatas: `BTC-P3D-*`; finais seladas depois).
- Snapshots: `BTC_SHA` (nulo) + árvore efetiva por execução.
- `core_sha` (`e6fde13`), adaptador + commit (`btc-cpp-lex/1`, este checkpoint),
  política (`btc-pack/1+expanded` candidato), budgets (2000 diagnóstico; total a fixar).
- Modelo/provedor/versão/parâmetros/contexto/telemetria (nulos — rótulos sem confirmação).
- Pesos/prompts/limites, hash de manifesto (`btc-seal/1`), seed de ordem/cegamento.
- Regra: nenhum ajuste de candidato, core ou adaptador após o selo; falha descoberta depois
  vira emenda + novo holdout, nunca retuning no mesmo conjunto.

## 2. Amostra (método selado; entradas nulas até o piloto)

Dimensionada no piloto Bitcoin: taxa de sucesso, discordâncias pareadas e variabilidade de
custos, margem 5pp, potência 80%. Repetições ≠ tarefas independentes. Sem piloto, sem número —
qualquer N afirmado antes disso é inválido. Não agregar resultados Bitcoin aos do SIGA.

## 3. Avaliação cega e decisão

Custodiante/processo segregado guarda tarefas finais, testes ocultos e chave de condições fora
do workspace/índice. Patches com IDs `Blind-###`; avaliador recebe tarefa, snapshot, patch e
rubrica (sem modelo/condição/custo/ordem); divergências → adjudicação independente antes de abrir
rótulos; pistas de descegamento registradas; LLM auxiliar nunca decide sozinho. Margens congeladas:
IC95% dif. sucesso > −5pp E IC95% razão custos < 0,80 → positivo; violações → negativo; sem poder →
inconclusivo. Publicar qualquer dos três com limitações. Falhas e tentativas entram no custo.
Pré-registrar bootstrap/estimadores, não inferioridade, família de comparações e multiplicidade;
não escolher o melhor braço olhando o teste final.

## 4. Lacunas que bloqueiam selo e rodada (todas nulas)

Piloto real com custos; `BTC_SHA` + toolchain; modelo/versão/telemetria efetivos; teto de gasto;
custodiante e avaliadores semânticos; amostra dimensionada. Resolver na preparação da rodada.
