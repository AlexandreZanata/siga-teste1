# Estado — CLI Rust e validação real

Criado em 2026-09-29. Dono: agente A (core), com validação Bitcoin pelo agente B em seus namespaces.

Plano: [construção e etapas](../RUST_CLI_PILOTO_REAL.md). Método: [protocolo](../../research/rust/PROTOCOLO_VALIDACAO.md).

## Evidência atual

- **R0 executado** (2026-09-29): contrato congelado em [`CLI_CONTRACT.md`](../../research/rust/CLI_CONTRACT.md), levantamento em [`BASELINE.md`](../../research/rust/BASELINE.md) e pré-registro em [`PREREGISTRATION_R0.md`](../../research/rust/PREREGISTRATION_R0.md).
- Checkpoints reconciliados: SIGA/core `db3e714` (igual a `origin/main`); worktree Bitcoin `codex/bitcoin-context` @ `3623afb`. Dataset SIGA `../siga` @ `e3be22828`, 504 arquivos Java, confirmado.
- Ambiente medido: Linux x86_64, i7-13620H/16 threads, 31 793 MiB totais com **4 859 MiB disponíveis**; `rustc`/`cargo` 1.96.0; `gcc` presente, `clang` ausente; 1 568 crates em cache cargo; crates.io acessível.
- O que executa: `pytest -q` verde — **63 passed, 4 skipped em 44,50 s**. Os 4 skips são de clones `/tmp/opencode-p6` ausentes (T1/T2), logo a cobertura de transferência real não está verificada neste checkout.
- Referência Python medida (execução única, não benchmark): `index` 504 arquivos em 5,54 s / RSS 21 928 kB; `doctor` 0,03 s / RSS 19 128 kB; `context` 0,15 s / RSS 34 940 kB com payload de 16 358 bytes.
- **Defeito quantificado:** `budget.used` declarado é ~2,07x menor que o JSON realmente emitido (2 000 pedidos → 1 972 declarados vs. 4 089 por `chars//4`); `refs[].file` vaza path absoluto; seleção sem diversidade (39 refs de um único arquivo); envelope não fecha. Correções já congeladas no contrato §5–§6.
- R0 **não** executou piloto, custo nem confirmação. Nenhuma conclusão de utilidade existe até R5.
- Bloqueios de ambiente: RAM disponível restringe medições de RSS; build Bitcoin segue bloqueado (sem `depends`/sudo) — SIGA não espera.
- Pendências de dono **usuário**: modelo efetivo (P1), teto financeiro (P2), custodiante do holdout (P4). As demais têm dono A ou B e estão em `BASELINE.md` §5.
- Próxima ação executora: **R1** — fatia mínima em Rust (`doctor`, `index`, `context`), sem modelo e sem gasto.

## Gates

- [x] R0 — contrato, estados reconciliados e ambiente evidenciado.
- [ ] R1 — CLI Rust mínima funcional com orçamento aplicado.
- [ ] R2 — comparação técnica e runner com telemetria.
- [ ] R3 — smoke e piloto com patches reais (status separado por trilha).
- [ ] R4 — análise, candidato e dimensão confirmatória.
- [ ] R5 — confirmação cega real concluída, qualquer que seja o resultado.
- [ ] R6 — uso por dev e distribuição validada no escopo declarado.

Cada gate registra separadamente `planejado / implementado / ensaiado / executado / avaliado` e `bloqueado` com motivo, quando aplicável. Uma preparação completa não marca execução completa. Campo de conclusão científica: `não avaliada / positiva / negativa / inconclusiva`.

Na retomada registrar dono, checkpoint, versão/hash do binário, datasets, fase, último aceite, próxima ação, execução ativa e reserva de recursos. Não copiar números dos experimentos Python para resultados Rust.
