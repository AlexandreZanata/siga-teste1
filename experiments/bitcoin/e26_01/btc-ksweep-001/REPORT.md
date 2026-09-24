# Sweep K do braço D — REPORT (`btc-ksweep-001`)

Pergunta: quantos arquivos top-K equilibram precisão e recall no D_bm25?
Método: 26 positivas × K ∈ {5,10,20,50} = **104** rodadas; pool BM25 fixo (200), só o
corte varia. Sem modelo.

## Medições

| K | hit | recall | precisão |
|---|---|---|---|
| 5 | 0.500 | 0.288 | 0.1231 |
| 10 | 0.654 | 0.481 | 0.0962 |
| 20 | 0.692 | 0.538 | 0.0579 |
| 50 | 0.731 | 0.673 | 0.0411 |

## Leitura e decisão

Retornos decrescentes após K=20; K=50 iguala o recall de C (0.673) com ~1/4 dos arquivos
(50 vs 189). K=10 **mantido** como identidade do braço precisão; K=50 alternativa
documentada quando recall importar. K maior convergiria para a largura inútil de A —
não testado por motivo declarado. **Sem confirmação** de ganho em edição.
