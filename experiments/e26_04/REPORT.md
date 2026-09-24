# E26-04 núcleo — foco explícito e poda determinística (sem filtro neural)

Data: 2026-09-24. ID: E26-04 partes determinísticas (adaptação R26-09; R26-07 Pro fora).
Código: `archatlas/packing.py:apply_focus` + `build_capsule(focus=)` (default None intacto).
Estado: `concluida` como mecanismo; filtro neural segue extra (sem pesos/GPU/licença aqui).
Método: mesmos candidatos e ranking; saída completa (FULL) vs seleção determinística
(FOCUS = query como proxy de foco do agente — limitação: proxy, não comportamento real)
vs foco incorreto (WRONG fixo, mede fallback). 12 piloto + 20 E26-01pos, budget 2k,
1 rep. Regra: mantém trecho com termo do foco OU esqueleto (class/interface/enum);
resto vira `focus-prune` no log + contadores; spans preservam file/line.
Saída: `runs.jsonl` (96). Patch/releituras nulos (sem agente).

## Resultados (hit/recall idênticos com menos payload)

| suite | FULL hit/recall/pay | FOCUS hit/recall/pay/omit | WRONG hit/recall/pay |
|---|---|---|---|
| piloto (12) | 0.750/0.667/5755 | 0.750/0.667/4422/5.6 | 0.667/0.472/318 |
| e26_01pos (20) | 0.450/0.325/6427 | 0.450/0.325/3252/17.4 | 0.050/0.025/314 |

Foco correto: −23% e −49% payload com zero perda de hit/recall de arquivos/adicionais.
Foco incorreto: degradação graciosa (entrega mínima + log completo de omissões, sem
exceção) — fallback honesto, não silêncio nem alucinação.

## Leitura (ficha: qualidade do patch manda; aqui, proxy de recuperação)

1. Poda por regras preserva a cobertura de recuperação e corta ~1/4–1/2 do payload:
   candidata a interface (campo `focus` opcional), com reabertura da fonte intacta.
2. Omissão de condições/assinaturas: 0 casos de perda nesta medida (recall preservado);
   a medida real exige patch (P3 real) — nenhuma alegação de edição aqui.
3. Custo do campo: sem foco, zero (default desligado); com foco, latência da regra ~0ms
   (sub-ms, dentro do `seconds` total); filtro neural: sem perfil, sem pesos, sem
   licença verificada → permanece extra; sem dimensionamento, sem decisão de infra.
4. Limites: foco=query é proxy (agente real pode formular foco vazio/errado — WRONG
   cobre o errado, o vazio equivale a FULL); n=32 dev, 1 rep, sem modelo/IC.

## Decisão

Campo `focus` mantido como opcional (default off, sem custo quando ausente).
Filtro neural: extra até ganho líquido demonstrado sobre estas regras.
Próximo: P3 real com/sem foco (taxa de uso, foco incorreto real, releituras, patch).
