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
- Próxima ação executora: **R3** bloqueada por P1/P2 (modelo efetivo e teto financeiro); enquanto isso, as pendências técnicas de A estão fechadas (Q1, Q3, Q5, Q7) e o que resta aberto exige decisão do usuário — Q2 (CI), Q4 (cache frio e cgroup), Q6 (execução real do runner), Q8 (mais repetições na escala).

## R1 executado (2026-09-29)

- Binário em `rust/archatlas/` (7 módulos), toolchain pinada em `rust-toolchain.toml` (1.96.0). O caminho de execução **não chama Python**. Relatório: [`R1_REPORT.md`](../../research/rust/R1_REPORT.md).
- **60 testes verdes** em `cargo test --release` (44 unitários + 16 de integração que spawnam o binário real). Orçamento verificado em **8 de 8** configurações, com utilização de 0,77 a 1,00.
- Três defeitos encontrados e corrigidos durante a própria etapa: `state` atribuído depois da medição (desvio de 5 bytes); `DELETE` no FTS5 a cada arquivo, O(n²) — indexação do repo inteiro **110,58 s → 1,71 s**; ajuste de orçamento O(n²) — `context` **3,64 s → 0,09 s**.
- Recursos medidos (execução única, **não** benchmark): `doctor` 0,00 s / RSS 5,3 MB; `context` 0,049–0,096 s / RSS ~17 MB; `index` repo inteiro 1,71 s / RSS 20,7 MB; binário 4,59 MB.
- Comparação com Python **ainda não válida** e registrada como hipótese, não resultado: corpus difere (511 contra 504) e é execução única. Corpus comum é pendência Q1 para R2.
- R1 **não** executou smoke com modelo, patch ou custo. R3 segue bloqueado por P1/P2 (modelo e teto financeiro, decisões do usuário).

## R2 executado parcialmente (2026-09-29)

- **Produto:** `expand` (`evidence_wanted` ∈ `context`/`references`/`tests`), `verify --ref arquivo:linha[@hash]`, `--include <langs>`, `RefSpec.end_line`, `evidence_reserve_pct` e `PackError::BadRequest`. Suíte em **80 testes verdes** (50 unitários + 16 de contrato + 14 de R2), `cargo fmt --check` limpo, `pytest -q` 76 passed / 4 skipped. Relatório: [`R2_REPORT.md`](../../research/rust/R2_REPORT.md).
- **Q1 fechada:** corpus comum congelado e verificado em duas camadas — 504 = 504 arquivos, mesmo conjunto de caminhos **e** mesmos hashes de conteúdo (fingerprint `bb7a99fbe4582c97…`).
- **Q3 fechada:** a comparação de R2 é declaradamente de **produtos**, não de linguagem. Sem tokenizer e pipeline comuns, nenhum número autoriza dizer "Rust é mais rápido que Python".
- **Rodada medida** em `experiments/rust/siga/2026-09-29-r2-queries/`, com script único e reproduzível (`benchmarks/rust/run_round.py`): **1 800 execuções de consulta** (100% exit 0), 20 de índice, 36 de atualização, 20 de `doctor`. `manifest_round.json` guarda linha de comando, ambiente e `sha256` do binário medido.
- **Orçamento, medido em 900 execuções por lado:** Rust declara exatamente o que entrega (razão 1,00 em mediana e máximo; `used_bytes` == stdout em 900/900; 0/900 acima de `max_bytes`). A referência Python declara 0,45 do que entrega, não publica bytes e passa o teto em 315/900. O `budget` responde no Rust (3,8/7,7/14,9 kB nos orçamentos 1k/2k/4k) e é inerte no Python (3 914 B nos três).
- **Ciclo editar/testar:** os dois lados são incrementais por hash de conteúdo e declaram as mesmas contagens (1/10/100 reindexados, `pruned_files: 1` em delete e rename). Cada execução medida foi conferida contra uma reindexação do zero: **36 de 36 equivalentes** (Rust: mesma geração; Python: índice == disco).
- **Metas do plano §5:** todas as metas do braço Rust foram atendidas (`doctor` 5,2 MB, `context` p95 0,010 s / p95 8,9 MB, `index` 10,6 MB, atualizar 1 arquivo 0,040 s), com três ressalvas registradas: corpus base pequeno (504 arquivos / 2,4 MiB), latências sub-10 ms não resolvidas pelo GNU time, RSS sem cgroup isolado.
- **Escala medida (94 execuções):** corpus sintético em ×1/×10/×30/×100 (504 → 50 400 arquivos, 2,4 → 238,7 MiB). A meta de `context` (p95 ≤ 150 ms, RSS ≤ 96 MiB) **sobrevive a 10x o teto de arquivos da coorte**: no maior ponto, Rust p95 0,070 s e RSS máximo 25,5 MB. A referência chega a p95 7,33 s e pico de 1,23 GB. A indexação — o único eixo em que os dois produtos fazem o mesmo trabalho — escala linearmente nos dois lados com constantes de ~5,6 ms/arquivo contra ~0,11 ms, e o índice Rust é 2,2x maior em disco (7,1 kB contra 3,3 kB por arquivo, razão estável). Corpus sintético é cópia: interpretar custo, não qualidade.
- **Segundo passo do ciclo, medido:** `expand` em 700 execuções (700/700 sem sobrepor span já entregue, checado por interseção de intervalos no harness, e 700/700 com `used_bytes` exato) e `verify` em 875 execuções (875/875 com o código de saída previsto antes da medição; nas 525 reprovações, zero unidades entregues). Só braço Rust: a referência não tem `expand` nem um `verify` de referência — logo, sem comparação de velocidade.
- **Achado (Q7) medido a fundo e corrigido.** A reserva `evidence_reserve_pct` (fatia de `max_bytes` para a busca, `evidence_reserved` declarado no que foi barrado) foi implementada e medida, mas instrumentá-la revelou defeito maior e anterior: um arquivo em `known_refs` só produzia a **janela pedida**, nunca as ocorrências do termo fora dela. Como `known_refs` vem do `context`, o alcance lexical da consulta é subconjunto dos arquivos já entregues em **70/70** sondagens — ou seja, o único material novo possível era a ocorrência fora da janela, e era justamente o que não vinha. Cada arquivo citado passou a produzir **dois grupos de spans**, com dedup também dentro da resposta. **Antes/depois medido** com o mesmo harness e o mesmo índice: pares (consulta, orçamento) sem nenhuma unidade de busca caíram de **63/70 → 21/70** sem reserva e de **38/70 → 13/70** com reserva. Os 21 restantes são casos de ocorrência única no arquivo: a janela já cobre, não há o que acrescentar.
- **A reserva satura em 30%:** mesmo conjunto de pares resolvidos com 30% e 50%, custo indistinguível (RSS p50 6 552 contra 6 540 kB). E ela é menor que o defeito — resolve 25 a 40 pares, contra 42 a 63 da mudança de grupos. `lexical sem nenhuma janela` = 5 pares em toda política: reserva em bytes com unidades de até 60 linhas pode barrar a janela inteira em vez de encolhê-la. Declarado, não acidental.
- **Rodada de `expand` refeita:** 1 400 execuções em quatro variantes (1 400/1 400 sem sobreposição, 1 400/1 400 com `used_bytes` exato, 0 exit ≠ 0), mais a linha de base de 1 400 preservada em `runs_expand_pre_samefile.jsonl` para o antes/depois.
- **Runner do piloto implementado e ensaiado** ([`RUNNER_PILOTO.md`](../../research/rust/RUNNER_PILOTO.md)): uma tentativa por run, tetos do pré-registro §1.4 aplicados primeiro (parede, chamadas de ferramenta; turnos do modelo são `null` com motivo enquanto o executor não os emitir), `opened` só de evento real de leitura, `delivered` medido do stdout observado e não do campo declarado, patch capturado e aplicado em base limpa para o teste de aceitação, e recusa a começar com o ouro alcançável a partir do workspace. **13 testes** em `tests/test_rust_runner.py`, incluindo integração com o binário Rust real. O executor `dry` existe para validar a infraestrutura e todo run dele sai marcado `infrastructure_only`.
- **NÃO executado:** nenhuma tentativa com modelo real — bloqueada por P1/P2 (modelo efetivo e teto financeiro, decisões do usuário), e a rubrica/avaliador cego não existem. Sem smoke com modelo, sem patch julgado, sem custo faturado: nada aqui é conclusão de utilidade.

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

Pendências ao fim de R2: Q2 (workflow de CI para `cargo test`, dono usuário), Q4 (cache frio e cgroup isolado, dono usuário), Q6 (execução real do runner: infraestrutura pronta, faltam executor/modelo, rubrica do avaliador e teto financeiro), Q8 (mais repetições no ensaio de escala) e Q9 (o alcance lexical da consulta é subconjunto dos arquivos que o `context` já entregou — quem quer alcance novo consulta, não expande). Q1, Q3, Q5 e **Q7** fechadas. Detalhe em [`R2_REPORT.md`](../../research/rust/R2_REPORT.md) §13.

O que ainda não tem dono técnico e é o caminho natural: **R3 só depende de P1/P2**, mas a rubrica por tarefa e o avaliador cego de R4 podem ser escritos antes — são eles que decidem o que "aceite" significa quando o modelo enfim rodar.
