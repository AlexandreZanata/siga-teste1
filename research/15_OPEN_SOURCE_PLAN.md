# 15 — Plano Open-Source, Licenças e Releases

**Status:** DRAFT 2026-09-24. Não é aconselhamento jurídico; decisão final com revisão institucional.

## 1. Licença do código: Apache-2.0 (recomendada)
≈ MIT em permissividade + grant de patente/retaliação + NOTICE/atribuição claros (úteis p/ retrieval/indexação e artifacts). MIT aceitável se política exigir fricção mínima. NÃO AGPL/GPL no código próprio (contaminaria adoção por agentes/IDEs e confundiria fronteira com SIGA AGPL). Ações: `LICENSE` + `NOTICE` + SPDX por arquivo + `pyproject.toml` + CI `reuse/licensee`.

## 2. Deps
MIT: atribuir em NOTICE+SBOM. Tree-sitter/gramáticas (atenção EPL): depender pinado, não copiar; isolar em `parsers/` plugável; `THIRD_PARTY.md`; CI `pip-licenses/deny`; escalar se EPL confirmado. clangd/LLVM: ferramenta externa, só documentar versão. Modelos (Muse Spark 1.3+): termos por capsule; sem chaves commitadas; respeitar proibição de distillation.

## 3. Artifacts (scripts+manifestos, sem blobs)
Comitar ponteiros (`URL+SHA+path:linha`)+hashes+scripts; regenerar localmente. **SIGA AGPL-3.0** (copyleft forte, network trigger): fatos estruturais não-copyrightable, mas excertos sim — nunca redistribuir checkout/índice c/ snippets; benchmark = ponteiros + `MANIFEST.md` "fetch+verify+build local"; paper só fair-use ≤10 linhas c/ citação. **Bitcoin MIT:** mesma disciplina por simetria + atribuição em NOTICE. Queries autorais + ponteiros (sem colar código terceiro); ground-truth grandes como `*.hash` + gerador.

## 4–6. Governança, CI, releases
`CONTRIBUTING.md` (setup, pytest/ruff, parsers sem heurística escondida, RFC v1, sem tuning no test), CoC Covenant, DCO signoff + check (sem CLA), PRs pequenos/1 hipótese. CI: pins, lint-spdx, pytest, schemas, licenses (deny AGPL/GPL no distribuído), freshness, secrets, dependabot. SBOM CycloneDX por tag (`sbom/<tag>.json`). Releases: `v0.1→v0.4` (skeleton→java→retrieval→siga-dev) → `v0.x-siga-frozen` (protegida) → `v0.x-bitcoin-eval` (só benchmarks/research) → `v1` (só ID-LIM via RFC com generalidade; CHANGELOG; notes sem prometer ganho). Público só após checklist §7: LICENSE/NOTICE/SPDX + THIRD_PARTY(EPL veredito) + sem blobs/indices/compile_commands + MANIFEST+PIN+hash reproduz em máquina limpa + snippets ≤10 linhas c/ SHA/licença + termos modelo + SBOM + DCO + revisão legal p/ venue.
