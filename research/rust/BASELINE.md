# Baseline real — o que existe, o que executa e o que está quebrado

Data: 2026-09-29. ID: `R0-BASELINE/1`. Etapa: **R0 (contrato, verdade dos estados, ambiente)**.
Natureza: levantamento por execução. Nenhuma fase de produto foi executada aqui; nenhuma conclusão de utilidade é possível a partir deste arquivo.

Comandos abaixo foram realmente executados neste checkout e são reprodutíveis. Durações são de **execução única**, não são benchmark: R2 mede com repetições e pareamento.

## 1. Checkpoints e estados reconciliados

| Item | Valor | Como verificado |
|---|---|---|
| Branch de trabalho | `main` | `git branch -vv` |
| HEAD local | `db3e714` | `git rev-parse --short HEAD` |
| `origin/main` | `db3e714` (em paridade, sem ahead/behind) | `git log --oneline -1 origin/main` |
| Worktree Bitcoin | `codex/bitcoin-context` @ `3623afb` | `git worktree list` |
| Last commit Bitcoin | `Build verificado BLOQUEADO: sem depends, sem sudo, sem RAM` | `git -C ../siga-teste1-bitcoin log -1` |

Sobreposição: o commit `db3e714` **não** está na branch Bitcoin; a worktree parte de uma base comum anterior. Os dois históricos são complementares, não conflictivos, e a main não contém o namespace `archatlas/bitcoin/`.

**Trabalho não commitado no momento deste levantamento** (9 modificados, 8 não rastreados) — a revisão de planejamento de 2026-09-29 que criou `plans/RUST_CLI_PILOTO_REAL.md`, `plans/rust/`, `plans/bitcoin/`, `research/rust/` e `research/bitcoin/`. R0 publica essa revisão no mesmo commit, porque o plano executado precisa estar versionado junto do estado que ele descreve.

## 2. Ambiente (medido nesta máquina)

| Item | Valor |
|---|---|
| SO / kernel | Linux `7.1.5-76070105-generic` x86_64 |
| CPU | Intel Core i7-13620H, 16 threads lógicos |
| RAM | 31 793 MiB total; **4 859 MiB disponíveis** no momento da medição |
| Disco | 460 GiB, 161 GiB livres |
| Python | 3.12.3 (sistema, sem pytest) |
| pytest | 9.1.1 em `.venv` local criado nesta etapa |
| SQLite (Python) | 3.45.1 |
| Rust | `rustc 1.96.0`, `cargo 1.96.0` |
| Compilador C | `gcc` presente (`/usr/bin/cc`); `clang` ausente |
| Registry cargo | 1 568 crates em cache local; `index.crates.io` e `static.crates.io` respondem 200 |

Duas conclusões que isso **libera** e duas que **bloqueia**:

- **Libera R1**: toolchain Rust presente, compilador C presente (necessário para `rusqlite` bundled com FTS5), rede de crates disponível. Não há bloqueio de infraestrutura para começar a fatia Rust.
- **Libera o piloto SIGA**: build/test executa de verdade nesta máquina (abaixo).
- **Bloqueia build Bitcoin**: apenas ~4,9 GiB livres e sem `sudo`/`depends` resolvidos. Coerente com o bloqueio registrado em `3623afb`. **Não reiniciar BTC-P0 por isso** — o plano (§6 R0) autoriza SIGA a seguir sem esperar Bitcoin.
- **Restringe metas de memória**: os tetos de RSS do plano (§5) continuam válidos como metas de produto, mas qualquer medição feita nesta máquina carrega a caveat de RAM compartilhada com outros processos. Metas que dependem de cgroup isolado ficam para a máquina dedicada.

## 3. O que realmente executa hoje

### 3.1 Suíte do core (SIGA) — verde nesta revisão

```sh
python3 -m venv .venv && .venv/bin/pip -q install pytest
ARCHATLAS_DATASET="$PWD/../siga" .venv/bin/python -m pytest -q -rs
# 63 passed, 4 skipped in 44.50s
```

Os 4 skips são **formato apenas**, não cobertura perdida: `tests/test_transfer_baseline.py:33`, `test_transfer_pins.py:21`, `test_transfer_probes.py:29`, `test_transfer_tasks.py:32` pulam porque os clones `/tmp/opencode-p6` (T1 cucumber-jvm, T2 pytest) não existem. Com os clones presentes, esses testes exercitam dados reais. Isso é limitação de ambiente, não falha de código — e significa que **a cobertura de transferência real não está verificada neste checkout**.

### 3.2 Dataset pinado — confirmado

```sh
git -C ../siga rev-parse --short HEAD        # e3be22828
git -C ../siga cat-file -t e3be22828         # commit
find ../siga/siga-ex/src/main/java -name '*.java' | wc -l   # 504
```

Dataset presente, no SHA pinado por `docs/ROADMAP_ETAPAS.md`, com as 504 fontes Java do SIGA. O SHA sozinho não representa working tree; `git -C ../siga status --short` mostra apenas `.freebuff/` e `siga-teste/` não rastreados, sem modificação de fonte versionada.

### 3.3 Referência Python — medidas únicas (não são benchmark)

```sh
export ARCHATLAS_DATASET="$PWD/../siga"
.venv/bin/python -m archatlas.cli index --db /tmp/r0-baseline.sqlite
# {'indexed': 504, 'skipped': 0, 'pruned_files': 0, 'pruned_symbols': 0}
# wall 5.54s, RSS 21 928 kB

.venv/bin/python -m archatlas.cli doctor --db /tmp/r0-baseline.sqlite
# index: ok, 504 arquivos, 4189 símbolos
# wall 0.03s, RSS 19 128 kB

.venv/bin/python -m archatlas.cli context --db /tmp/r0-baseline.sqlite --query ExMovimentacao --budget 2000
# wall 0.15s, RSS 34 940 kB, payload 16 358 bytes
```

O caminho de referência **executa ponta a ponta hoje**: indexar 504 arquivos, 4 189 símbolos, e entregar contexto em centésimos de segundo com RSS na casa das dezenas de MB. Esses números são o ponto de partida a bater, não um resultado. Comparação contra Rust é R2, com repetições e pareamento.

Estado do produto Rust: **zero código**. `rust/archatlas/` não existe. Os crates `rusqlite`, `ignore` e `blake3` não estão no cache local (baixáveis pela rede); `serde`, `serde_json`, `clap`, `anyhow`, `thiserror`, `walkdir`, `rayon`, `sha2` já estão.

## 4. Defeitos medidos na referência (motivos do contrato, não opinião)

Medidos em `db3e714`, consulta `ExMovimentacao`, mesmo índice:

| `budget_tokens` pedido | bytes do JSON real | `chars//4` do JSON real | `budget.used` declarado | razão declarado/real |
|---|---|---|---|---|
| 1 000 | 8 410 | 2 102 | 984 | **2,14x** |
| 2 000 | 16 358 | 4 089 | 1 972 | **2,07x** |
| 8 000 | 20 704 | 5 176 | 2 483 | 0,48x |

Quatro defeitos confirmados, cada um com correção já congelada em [`CLI_CONTRACT.md`](CLI_CONTRACT.md):

1. **`budget.used` não conta a resposta entregue.** Conta só os itens de texto; o envelope, refs, hints e metadados ficam fora. O plano já suspeitava disso (`plans/RUST_CLI_PILOTO_REAL.md` §1); agora há número. Por isso §6 do contrato torna a contagem da serialização final obrigatória e iterativa.
2. **`refs[].file` vaza path absoluto.** A resposta emite `/home/iiii/PESSOAL-PROJETOS-ALEXANDRE/siga-teste1/../siga/...`. Isso viola privacidade já endereçada em F19 e é proibido pelo contrato §5.
3. **Seleção sem diversidade.** Com budget 2 000, as 39 refs vêm quase todas do **mesmo arquivo** (`Documento.java`), linhas 74–141, um por "bm25 rank". Hanking diversity exists. Sem isso, o orçamento é gasto repetindo um arquivo.
4. **Envelope não fecha em budget pequeno.** `schema_overhead_tokens` é calculado sobre um subconjunto do JSON, não sobre a resposta. E o `chars//4` não é limite exato, como o próprio código declara (`"tokenizer": "chars//4"`).

Achado adicional, sem impacto no plano: fechar stdout cedo (`| head -c`) produz `BrokenPipeError` e exit 120 em vez de saída limpa. Cosmético para o piloto, mas registrado porque corruptaria contagem de bytes se o runner algum dia capturasse por pipe truncado.

Sobre o caso de 8 000 tokens: `state: ok`, `used: 2483`, 50 unidades entregues. A seleção **satura em 50 unidades**, então pedir 8 000 não entrega 8 000 — o teto efetivo é o número de unidades candidatas. Isso explica a não monotonicidade da tabela e é exatamente o tipo de coisa que só aparece medindo a resposta real.

## 5. Pendências com dono e ação (nada aqui está "concluído")

| # | Pendência | Dono | Ação | Bloqueia |
|---|---|---|---|---|
| P1 | Modelo efetivo: ID, provedor, versão, disponibilidade e métrica de uso | **usuário** | escolher entre os candidatos do protocolo ou fornecer outro | R3 real |
| P2 | Teto financeiro por tentativa, por trilha, moeda e política de retries | **usuário** | autorizar valor | R3 real |
| P3 | Tokenizer local correspondente ao modelo, com versão e hash | A | resolver após P1; senão congelar modo bytes | R3 real |
| P4 | Custodiante independente de tarefas/chaves do holdout | **usuário** | nomear pessoa fora do workspace do agente | R5 |
| P5 | Coorte e consultas de microbenchmark congeladas | A | derivar de P1/R1; corpora reais + fixtures de equivalência | R2 |
| P6 | Clones T1/T2 em `/tmp/opencode-p6` | B | materializar para reativar 4 testes de transferência | cobertura de transferência |
| P7 | Ambiente de build Bitcoin (deps, RAM, sudo) | B | resolver antes de BTC-P2; SIGA não espera | BTC-P2+ |
| P8 | Máquina/cgroup isolado para RSS e page cache frios | usuário | reservar, ou declarar "não medido" no relatório | frio do §7 do protocolo |

Nenhuma dessas pendências é resolvível por agente. **R1 não depende de nenhuma delas** — é implementação local sem modelo e sem gasto.

## 6. Conclusão de R0

R0 entregou: contrato congelado, capacidades reais inventariadas com evidência reproduzível, defeitos quantificados, ambiente medido, e pendências nomeadas com dono e ação.

**R0 não entregou, e não pode ter entregue**: qualquer execução de piloto, qualquer medição de custo, qualquer confirmação cega, qualquer binário Rust. Registrar isso evita que este arquivo seja lido depois como "R0 concluído" significando "validação concluída".

Portões de aceitação do R0, verificados:

- [x] Contrato de CLI congelado antes da implementação (`CLI_CONTRACT/1`).
- [x] Estados reconciliados com evidência de SHA (`db3e714`, `3623afb`, dataset `e3be22828`).
- [x] Build/test que realmente executa identificado por trilha (pytest verde no core; Bitcoin bloqueado com causa).
- [x] Ambiente evidenciado (toolchain, RAM, disco, rede, compilador).
- [x] Cada pendência com dono e ação, nenhuma resolvida por agente.
- [x] Zero fase real declarada concluída apenas por documentação.

Próxima ação executora: **R1** — fatia mínima em Rust (`doctor`, `index`, `context`), executando o caminho inteiro sem subprocesso Python, com orçamento contado na serialização final.
