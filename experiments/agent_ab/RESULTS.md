# Experimento A/B em agente — F6 (2026-09-24, SIGA `e3be22828`, 6 perguntas dev)

## Condições
- **Baseline:** só Read/Grep/Glob/rg no `/siga/`. **ArchAtlas:** busca obrigatória no índice (`store/query/lexical/capsule`), leitura só p/ confirmar.
- Perguntas: A-000, D-000, A-001, A-002, D-002, B-002 (GT em `benchmarks/siga/queries_dev.json`). D aceita qualquer referência verificada.

## Resultado (apuração do orquestrador contra GT + releitura)

| id | GT | Baseline | Atlas | veredito |
|---|---|---|---|---|
| A-000 | Documento.java:89 | :89 ✓ | :89 ✓ | ambos |
| D-000 | ref. Documento | Stamp.java:223 ✓ (lido) | ExBL.java:95/:7152 ✓ (lido) | ambos (refs distintas, válidas) |
| A-001 | Documento.java:387 | :387 ✓ | :387 ✓ | ambos |
| A-002 | FOP.java:44 | :44 ✓ | :44 ✓ | ambos |
| D-002 | ref. FOP | ConversorHTMLFactory.java:36 ✓ | mesmo arq. :4/:36/:55 ✓ | ambos |
| B-002 | siga-ex | siga-ex ✓ | siga-ex ✓ | ambos |

**Acerto: 6/6 (100%) ambos. Falso positivo: 0 ambos.**

## Tempo (honesto)
- Baseline: ~30s, 12 passos. Atlas: ~53s parede (núcleo index+queries 10.9s), 20 passos — indexou `siga-ex` inteiro (2328 arqs, 22287 docs lexicais), custo amortizável.
- **Leitura correta:** no micro-lote de 6Qs o baseline foi mais rápido; o índice paga-se na reutilização (query pós-index em ms) e na desambiguação (Atlas listou as 2 classes `Documento` explicitamente; baseline achou as mesmas 2 via grep). Hipótese NÃO provada aqui — exige F7 (lote grande + medição por query pós-index).

## Decisão
Bitcoin = FUTURO (ver roadmap). Foco SIGA-Doc: F7 fidelidade total (`siga-ex` + JSPs `sigaex`, `unresolved_rate`) + harness com tempo por query.
