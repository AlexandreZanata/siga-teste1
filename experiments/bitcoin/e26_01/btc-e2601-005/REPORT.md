# E26-01 com text-seed em C — REPORT (`btc-e2601-005`)

Pergunta: sementes textuais (top-30 por frequência) destravam frames sem salto?
Método: mesmas 34 tarefas × 4 braços × 2k/8k = **272** rodadas; único fator vs 004 é
`text_seed=True` em C (split on em todos). Sem modelo.

## Medições @2000 (004 → 005, C_adapter)

hit 0.808 → **0.962**; recall 0.750 → **0.885**; precisão 0.0129 → 0.0058;
entregues ~210 → ~322. Ganhos: R04, R10, R12 (`addrman` recuperado!), R19.
Perdas: **zero**. Resta 1 miss: R20 (p2p_segwit → net_processing + net.h).
A/B/D bit-idênticos a 004.

## Decisão

Text-seed `manter` (ganho sem perda, mecânico, determinístico). Preço: +53% arquivos e
metade da precisão — E26-02 com spans é quem deve converter volume em contexto útil.
R20 (frame Python sem ponte textual p/ impl) marca o limite do lexical puro; próximo:
ponte teste→impl ou aceitar como `unsupported` de retrieval. **Sem confirmação** de edição.
