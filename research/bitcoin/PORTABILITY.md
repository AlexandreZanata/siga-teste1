# BTC-P6 — Portabilidade temporal e de ambiente (desenho + drill; sem corpus)

Data: 2026-09-24. Dono: agente B. Candidato: `C_btc` (BTC-P4). Esta etapa NÃO comprova
transferência entre repositórios: Bitcoin é dataset de desenvolvimento; H5/P6 do produto geral
exige projetos inéditos. Drill sintético em `experiments/bitcoin/p6_temporal/btc-p6-drill-001/`.

## 1. Eixo temporal (t0 → t1, ambos pinados antes dos resultados)

Congelar candidato e avaliar snapshots Bitcoin posteriores com novas famílias de tarefas:
registrar `BTC_SHA(t0)`, `BTC_SHA(t1)`, diff de arquivos, `diff_snapshots` (added/removed/changed/
unchanged/invalidated) e `update_cost` (fração a reextrair). Mudança temporal, cobertura de
feature e diferença de ambiente analisadas separadamente — nunca somadas numa média única.
Revalidação obrigatória do candidato em t1 antes de qualquer confirmatório posterior.

## 2. Eixo ambiente (matriz a preencher no snapshot; hoje nula)

Compilador + versão, flags, dependências, features habilitadas, comandos reais de build/teste,
`compile_commands.json` (hash versionado quando produzido), datadir/portas/caches isolados.
Outro ambiente de build pertinente escolhido antes dos resultados; comparar incremental vs
rebuild após edição/exclusão/renomeação/troca de flags. Testes funcionais em regtest isolado;
nada depende de mainnet, fundos ou nó de produção.

## 3. Cobertura de feature e custos de atualização

Cobertura declarada do adaptador: arquivos e `#include` verificados (texto); Python-AST;
pares header/impl textuais. Fora de cobertura: macros, templates instanciados, overloads,
chamadas virtuais, despacho dinâmico, GUI. Custo de atualização = fração invalidada +
rebuilds + revalidação; break-even só se economia/tarefa superar manutenção (a medir).

## 4. Bloqueios (execução real pendente)

`BTC_SHA(t0/t1)`, toolchain, teto, modelos, custodiante — todos nulos. Drill valida a
maquinaria, não o produto.
