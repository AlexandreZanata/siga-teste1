# MEMORY — visão do produto + system prompt instalável (EN)

> Visão de produto, ainda não garantia de portabilidade ou ganho. O [plano vigente de pesquisa](PESQUISA_CONTEXTO_MODULAR.md) define a sequência executável e substitui a aplicação imediata do instalador abaixo. Primeiro medir utilidade em edição real no SIGA; depois validar transferência com capacidades declaradas. Bitcoin permanece candidato futuro opcional.

## Goal
A project-level **context memory** that is always available, triggerable on user request, constantly updatable as the project evolves, and installable into ANY repository. End state: user says "install \<project\> in this repository" and the agent maps the whole project under rigid criteria, producing measurable LLM-agent efficiency gains (fewer tokens, fewer tool calls, same-or-better correctness).

## System prompt (drop-in, EN)
```
You are the Repository Memory Installer. The user asked: "install <project-name> in this repository".

Do this autonomously, with zero invented facts:
1. PIN the repository: record remote URL, branch, commit SHA. All facts are versioned to this SHA.
2. CENSUS: count files/LOC per language (measured, never estimated). Write CENSO.md.
3. MAP with rigid criteria — every emitted fact MUST carry file:line@SHA + content_hash.
   Emit ONLY what you read: definitions, references, callers/callees, imports, tests, docs.
   Anything uncertain is marked heuristic/unresolved, NEVER stated as fact.
4. INDEX into .atlas/atlas.sqlite (SQLite + FTS5, local-first, no network, no GPU needed).
5. VERIFY: re-read every emitted fact from disk (name-on-line + hash match). Drop failures with log.
6. REPORT: coverage (unresolved_rate per language), index size/time, sample queries with evidence.
7. UPDATE HOOK: record the file→symbols invalidation map so future diffs re-index incrementally.
Refuse to guess. Absence of evidence is a finding, not a failure.
```

## Rigid mapping criteria (v1)
- `deterministic`: same SHA + same extractor = same DB (stable hash, cache excluded).
- `evidenced`: file:line@SHA + sha256; re-verified pre-commit.
- `honest`: heuristic/unresolved labeled with cause (macro/template/DI/dynamic include).
- `incremental`: diff → re-parse touched files only; rest hash-verified untouched.
- `budgeted`: every context answer respects a token budget; truncation logged.

## Real-task proving ground (F21+, both tracks)
Edit-efficiency blinds (agent WITHOUT memory vs WITH memory, timed, diff-judged):
- SIGA frontend: "change the reset-password button label/style on the login screen" (JSP legeacy `sigaex`).
- SIGA backend: "add a validation before signing a document" (siga-ex service + tests).
- BTC: "add an RPC argument validation" + "document mempool acceptance path".
Metrics: time-to-correct-diff, tokens, tool calls, tests passing. Memory wins only if measured.
