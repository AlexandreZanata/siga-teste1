# E26-05 núcleo — histórico acumulado (replay offline; vivo N/A)

Data: 2026-09-24. ID: E26-05 comparação inicial (adaptação R26-02/R26-03).
Código novo: `archatlas/history.py:1` (puro, sem LLM, sem reescrita).
Estado: `concluida` como validação de replay; sem alegação de economia em sessão viva.
Método: 2 sessões sintéticas determinísticas (S1 longa 122 msgs/2853tk; S2 decisão
antiga + 50 pares + pergunta final, 104 msgs/2456tk) × KEEP/DROP-OLD/CLIFF, budget
2000. Replay valida instruções verbatim, pares call/response e contagem exata.
Janelas por pares atômicos (corte mecânico quebrava protocolo — corrigido no código).
Saída: `runs.jsonl` (6). Resumo LLM, estágios, 16k/32k, cache e trajetórias vivas:
N/A sem controle do histórico do cliente (limite da ficha; recuperação segue usável).

## Resultados (tokens efetivos / overflow / decisão antiga)

| sessão | KEEP | DROP-OLD | CLIFF |
|---|---|---|---|
| S1 longa | 2853 / OVERFLOW / — | 268 / ok / — | 473 / ok / — |
| S2 decisão | 2456 / OVERFLOW / mantida | 285 / ok / **perdida** | 504 / ok / mantida |

Replay: instruções intactas e protocolo íntegro nas 6 (pares atômicos).
DROP-OLD é o mais barato e o único que perde a decisão; CLIFF custa ~2× o DROP-OLD
e a preserva (head literal); KEEP estoura o budget nas duas.

## Leitura

1. Compactação só vira extensão onde atua: sem pressão (sob budget) CLIFF ≡ KEEP por
   desenho — nenhum benefício fictício contra baseline folgado (erro que a ficha manda
   evitar: aqui o baseline KEEP estoura de verdade).
2. Perda deliberada existe e é mensurável: DROP-OLD apaga decisão antiga; o log
   distingue `retrieved/delivered` da cápsula de `opened` do histórico — não somar.
3. Sem trajetórias vivas, sem conclusão sobre reações do agente (releituras, ações
   repetidas, sucesso): replay não revela comportamento; N/A registrado, não zerado.
4. Limites: 2 sessões sintéticas, 1 budget (2000), contagem `chars//4`, sem telemetria
   de provedor; 16k/32k só como diagnóstico futuro com suporte real.

## Decisão

Nenhuma política promovida a extensão de produto. Próximo honesto: harness isolado com
controle real do histórico (1 modelo, tarefas longas naturais + diagnósticos de decisão
antiga), medindo custo ponta a ponta, cache cobrado, overflow e sucesso — ou marcar
E26-05 indisponível no cliente sem esse controle.
