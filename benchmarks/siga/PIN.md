# PIN — dataset SIGA-Doc modificado (F1, verificado 2026-09-24)
- **Base:** versão modificada do SIGA-Doc, branch `desenvolvimento`
- **SHA:** `e3be22828f787cbe71b339aecb7a7bf569099803`
- **Build:** Maven, Java **21**, `siga-doc 11.5-SNAPSHOT`, 19 módulos, Hibernate 6
- **Licença dataset:** AGPL-3.0 — nenhum blob neste repo (só ponteiros+hashes+scripts)
- **Setup local:** `export ARCHATLAS_DATASET=/caminho/para/siga-doc` (checkout read-only no SHA acima)
- **Verificação:** `git -C "$ARCHATLAS_DATASET" rev-parse HEAD` deve imprimir o SHA; `tests/test_pins.py` automatiza.
