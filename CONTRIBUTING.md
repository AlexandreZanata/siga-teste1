# Contributing (ArchAtlas)

1. **Fases curtas:** 1 etapa = 1 commit + push. Nunca acumule 2 fases num commit.
2. **DCO:** `git commit -s` (Signed-off-by obrigatório).
3. **Zero falso positivo:** todo fato novo exige evidência `arquivo:linha@SHA` verificável pelo teste; heurística deve ser marcada, nunca silenciosa.
4. **Dataset read-only:** o checkout da versão modificada do SIGA-Doc (`$ARCHATLAS_DATASET`) nunca é modificado; sem blobs AGPL neste repo (só ponteiros+hashes+scripts).
5. **Reproduzível:** `python -m pytest -q` deve passar offline. Nova dependência só com justificativa (padrão: stdlib).
6. **Testes antes do push:** `python -m pytest -q` verde + `git status` limpo do que não deve ir (ver `.gitignore`).
