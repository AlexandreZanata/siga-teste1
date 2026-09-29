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
- Próxima ação executora: **R3** bloqueada por P1/P2; enquanto isso, fechar a pendência Q5 (microbenchmark de `expand`/`verify`).

## R1 executado (2026-09-29)

- Binário em `rust/archatlas/` (7 módulos), toolchain pinada em `rust-toolchain.toml` (1.96.0). O caminho de execução **não chama Python**. Relatório: [`R1_REPORT.md`](../../research/rust/R1_REPORT.md).
- **60 testes verdes** em `cargo test --release` (44 unitários + 16 de integração que spawnam o binário real). Orçamento verificado em **8 de 8** configurações, com utilização de 0,77 a 1,00.
- Três defeitos encontrados e corrigidos durante a própria etapa: `state` atribuído depois da medição (desvio de 5 bytes); `DELETE` no FTS5 a cada arquivo, O(n²) — indexação do repo inteiro **110,58 s → 1,71 s**; ajuste de orçamento O(n²) — `context` **3,64 s → 0,09 s**.
- Recursos medidos (execução única, **não** benchmark): `doctor` 0,00 s / RSS 5,3 MB; `context` 0,049–0,096 s / RSS ~17 MB; `index` repo inteiro 1,71 s / RSS 20,7 MB; binário 4,59 MB.
- Comparação com Python **ainda não válida** e registrada como hipótese, não resultado: corpus difere (511 contra 504) e é execução única. Corpus comum é pendência Q1 para R2.
- R1 **não** executou smoke com modelo, patch ou custo. R3 segue bloqueado por P1/P2 (modelo e teto financeiro, decisões do usuário).

## R2 executado parcialmente (2026-09-29)

- **Produto:** `expand` (`evidence_wanted` ∈ `context`/`references`/`tests`), `verify --ref arquivo:linha[@hash]`, `--include <langs>`, `RefSpec.end_line` e `PackError::BadRequest`. Suíte em **76 testes verdes** (50 unitários + 16 de contrato + 10 de R2), `cargo fmt --check` limpo. Relatório: [`R2_REPORT.md`](../../research/rust/R2_REPORT.md).
- **Q1 fechada:** corpus comum congelado e verificado em duas camadas — 504 = 504 arquivos, mesmo conjunto de caminhos **e** mesmos hashes de conteúdo (fingerprint `bb7a99fbe4582c97…`).
- **Q3 fechada:** a comparação de R2 é declaradamente de **produtos**, não de linguagem. Sem tokenizer e pipeline comuns, nenhum número autoriza dizer "Rust é mais rápido que Python".
- **Rodada medida** em `experiments/rust/siga/2026-09-29-r2-queries/`, com script único e reproduzível (`benchmarks/rust/run_round.py`): **1 800 execuções de consulta** (100% exit 0), 20 de índice, 36 de atualização, 20 de `doctor`. `manifest_round.json` guarda linha de comando, ambiente e `sha256` do binário medido.
- **Orçamento, medido em 900 execuções por lado:** Rust declara exatamente o que entrega (razão 1,00 em mediana e máximo; `used_bytes` == stdout em 900/900; 0/900 acima de `max_bytes`). A referência Python declara 0,45 do que entrega, não publica bytes e passa o teto em 315/900. O `budget` responde no Rust (3,8/7,7/14,9 kB nos orçamentos 1k/2k/4k) e é inerte no Python (3 914 B nos três).
- **Ciclo editar/testar:** os dois lados são incrementais por hash de conteúdo e declaram as mesmas contagens (1/10/100 reindexados, `pruned_files: 1` em delete e rename). Cada execução medida foi conferida contra uma reindexação do zero: **36 de 36 equivalentes** (Rust: mesma geração; Python: índice == disco).
- **Metas do plano §5:** todas as metas do braço Rust foram atendidas (`doctor` 5,2 MB, `context` p95 0,010 s / p95 8,9 MB, `index` 10,6 MB, atualizar 1 arquivo 0,040 s), com três ressalvas registradas: corpus pequeno (504 arquivos / 4,2 MiB), latências sub-10 ms não resolvidas pelo GNU time, RSS sem cgroup isolado.
- **NÃO executado:** integração com o runner real e captura de custos/patches — bloqueada por P1/P2 (modelo efetivo e teto financeiro, decisões do usuário). `expand`/`verify` têm teste, não microbenchmark próprio (Q5). Sem smoke com modelo, sem patch, sem custo: nada aqui é conclusão de utilidade.

## Gates

- [x] R0 — contrato, estados reconciliados e ambiente evidenciado.
- [x] R1 — CLI Rust mínima funcional com orçamento aplicado (implementado e ensaiado; sem execução real).
- [~] R2 — microbenchmarks executados (planejado/implementado/ensaiado/executado parcialmente); **runner com modelo real não executado** (P1/P2). Avaliação científica não realizada.
- [ ] R3 — smoke e piloto com patches reais (status separado por trilha).
- [ ] R4 — análise, candidato e dimensão confirmatória.
- [ ] R5 — confirmação cega real concluída, qualquer que seja o resultado.
- [ ] R6 — uso por dev e distribuição validada no escopo declarado.

Cada gate registra separadamente `planejado / implementado / ensaiado / executado / avaliado` e `bloqueado` com motivo, quando aplicável. Uma preparação completa não marca execução completa. Campo de conclusão científica: `não avaliada / positiva / negativa / inconclusiva`.

Na retomada registrar dono, checkpoint, versão/hash do binário, datasets, fase, último aceite, próxima ação, execução ativa e reserva de recursos. Não copiar números dos experimentos Python para resultados Rust.

Pendências ao fim de R2: Q2 (workflow de CI para `cargo test`, dono usuário), Q4 (cache frio e cgroup isolado, dono usuário), Q5 (microbenchmark de `expand`/`verify`, dono A) e Q6 (integração com o runner real, bloqueada por P1/P2). Detalhe em [`R2_REPORT.md`](../../research/rust/R2_REPORT.md) §11.
