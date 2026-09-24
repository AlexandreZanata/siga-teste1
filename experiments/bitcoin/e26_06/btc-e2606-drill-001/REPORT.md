# BTC-E26-06 ensaiado — REPORT (`btc-e2606-drill-001`)

Pergunta: a jornada dev (doctor → index → context → expand → edit → validate → update →
uninstall) executa ponta a ponta com estados honestos antes de qualquer dev humano?
Método: `archatlas/bitcoin/devflow.py` sobre repo sintético. Comando:
`pytest -q tests/bitcoin/test_btc_devflow.py` → **2 passed**.

## Estados medidos (ensaio; sem usuário real)

doctor `partial` (.rs diagnosticado, não silenciado) → index `ok` (12 arquivos, 18 fatos) →
context `ok` (3 ranqueados, 6 trechos, 94 tok, gap explícito `checktransaction`) →
expand `ok` (âncora no texto) → edit `ok` (original intacto, só cópia isolada) →
validate `ok` (integridade; C++ exige revisão/build) → update `ok` (header alterado detectado) →
uninstall `ok` (nada restante). Stale (fonte ausente, linha inválida, raiz ausente) e
`partial` (sintaxe Python quebrada) verificados como estados, sem crash.

## Limites e decisão

Sem humano, sem tempo de configuração/patch/revisão medidos; sem GUI; sem build.
Jornada `manter` como procedimento; adoção real `evidência insuficiente` até BTC-P7 com dev.
Próximo: `DEV_GUIDE.md` para uso humano futuro; handoff de integração ao agente A.
