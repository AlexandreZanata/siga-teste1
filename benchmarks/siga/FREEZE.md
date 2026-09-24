# FREEZE `v0.x-siga-frozen` (F8, 2026-09-24)
- **Dataset:** `/siga/` branch `desenvolvimento`, SHA `e3be22828f787cbe71b339aecb7a7bf569099803`
- **Benchmark:** `queries_dev.json` sha256 `39a3828168e7a6e3d7679…` (60 Qs: A20/B20/D20)
- **Código:** `capsule.py 3e0507f2…`, `extract.py e913257a…`, capsule_version `1.0`, budget 2000
- **Resultado congelado:** recall **1.00** (A20/20 B20/20 D20/20), query média ~5ms, index 40 arqs ~0.1s
- **Regra:** após esta tag, `archatlas/` só muda via RFC; próximo trabalho é F9+ (JSP lexer, call graph, testes) sem invalidar este ponto.
