# ArchAtlas — Deterministic Structural Memory for Repository-Scale LLM Agents

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](pyproject.toml)

Memória estrutural externa, determinística, compacta, incremental e navegável de grandes repositórios. O LLM continua com contexto finito; o repositório fica fora do modelo; o agente recupera só a **Context Capsule** necessária.

> **Dataset base (read-only, fora deste repo):** uma versão modificada do SIGA-Doc — branch `desenvolvimento`, SHA `e3be22828`, Java 21, Hibernate 6, 19 módulos Maven. **Nunca commitamos código do dataset aqui** — só ponteiros (SHA+path relativo) + hashes + scripts. O dataset original é AGPL-3.0.

## Estrutura (100% open source)
```
archatlas/        # código Apache-2.0 (core determinístico, stdlib-first)
benchmarks/siga/  # PIN.md + CENSO.md (ponteiros, sem blobs)
tests/            # pytest, tudo reproduzível em 1 comando
research/         # fundamentos, protocolos e base experimental de papers de 2026
docs/             # protocolos operacionais (verificação, roadmap)
experiments/      # capsules por execução (hashes, sem outputs gigantes)
```

## Metodologia de ponta (resumo)
- **Trunk-based + fases curtíssimas**, cada fase = commit local + push.
- **Zero falso positivo:** todo fato estrutural exige evidência `arquivo:linha@SHA` + `content_hash`; o que não for deterministicamente verificável é marcado `heuristic/unresolved`, nunca inventado.
- **Reproduzível em 1 comando:** `python -m pytest -q` (sem rede, sem GPU, sem serviços).
- **Fonte da verdade:** código/AST/símbolos/Git — nunca LLM. Cache IA só marcado/regenerável.
- **Sem dados pessoais:** nenhum path de máquina no código ou docs; GT usa paths relativos ao dataset.

## Roadmap por etapas (cada etapa = commit + push)
Próxima entrega planejada: [CLI local em Rust, piloto real e avaliação cega](plans/RUST_CLI_PILOTO_REAL.md), com [protocolo de custo, memória, latência e qualidade dos patches](research/rust/PROTOCOLO_VALIDACAO.md) e [estado próprio](plans/rust/STATUS.md). A escolha de Rust não é uma medição de ganho: comparar implementação e utilidade do agente separadamente. R0–R2 foram executados (R2 parcialmente); **nada aqui mede utilidade** — isso exige o piloto real de R3, ainda bloqueado por decisão de modelo e orçamento.

O [plano vigente de pesquisa para contexto modular](plans/PESQUISA_CONTEXTO_MODULAR.md) orienta as próximas etapas: auditoria das evidências, literatura primária, tarefas reais de edição, avaliação cega e transferência para outros projetos. Define contratos e critérios de ganho; sua inclusão é apenas planejamento, sem implementação ou experimentos novos.

A [base experimental de 2026](research/16_BASE_EXPERIMENTAL_2026.md) reúne nove papers, incluindo trabalhos de setembro. O [roteiro de experimentos e entrega para devs](plans/EXPERIMENTOS_2026.md) converte os métodos em testes de seleção de contexto, empacotamento, poda, histórico e uso real, com controles e critérios de decisão.

Para trabalhar com dois agentes: [agente A — continuar SIGA/core](plans/SIGA_EXECUTION.md) e [agente B — Bitcoin](plans/BITCOIN_PARALLEL_PLAN.md). O [protocolo paralelo](plans/PARALLEL_EXECUTION.md) separa worktrees, arquivos, índices e recursos, com integração do core em checkpoints. Bitcoin possui [as mesmas sete fichas experimentais](plans/bitcoin/EXPERIMENTOS_2026.md) e [estado próprio](plans/bitcoin/STATUS.md).

Ver também `docs/ROADMAP_ETAPAS.md` (histórico F0–F20 e ligação com F21) e `docs/VERIFICATION_PROTOCOL.md` (verificação de evidências). Resultados históricos de recuperação não comprovam, isoladamente, economia ou correção em tarefas de desenvolvimento.

## CLI Rust (R1 implementado; R2 parcialmente)

Executável local que o agente invoca por shell: recuperação determinística, sem rede, sem daemon, sem GPU e sem Python no caminho de execução. Fonte em `rust/archatlas/`; contrato congelado em `research/rust/CLI_CONTRACT.md`; estado em `plans/rust/STATUS.md`; medições em `research/rust/R2_REPORT.md` (compare produtos, não linguagens).

```bash
cargo build --release --manifest-path rust/archatlas/Cargo.toml
B=rust/archatlas/target/release/archatlas

$B index   --repo /caminho/para/repo --index /tmp/atlas.sqlite --include java
$B doctor  --repo /caminho/para/repo --index /tmp/atlas.sqlite --format text
$B context --repo /caminho/para/repo --index /tmp/atlas.sqlite --request pedido.json
$B expand  --repo /caminho/para/repo --index /tmp/atlas.sqlite --request expansao.json
$B verify  --repo /caminho/para/repo --index /tmp/atlas.sqlite --ref br/gov/jfrj/.../X.java:42
```

`pedido.json` traz `schema_version`, `intent`, `query`, `budget_tokens`, `max_bytes` e `policy` (`LEX-RS` ou `CTX-RS`); `expansao.json` acrescenta `known_refs`, `delivered_refs` e `evidence_wanted` (`context`/`references`/`tests`). `--include` restringe a indexação a um conjunto de linguagens e reporta em `excluded_by_filter` o que ficou fora. stdout é **um único objeto JSON**; o orçamento é medido sobre a serialização final, não sobre a soma dos itens. Códigos: `0` resposta válida (`partial`/`stale` são válidos e explícitos), `2` pedido inválido, `3` índice ausente/incompatível/corrompido/vazio, `4` erro de I/O, `5` integridade violada (`verify` reprovado, hash divergente, referência fora da raiz). Limites estão declarados no [relatório de R1](research/rust/R1_REPORT.md) §7 e no [de R2](research/rust/R2_REPORT.md) §11.

Testes: `cargo test --release --manifest-path rust/archatlas/Cargo.toml`.

Rodada de medição reproduzível (corpus congelado, pareamento e ordem alternada):

```bash
ARCHATLAS_DATASET=/caminho/para/siga python benchmarks/rust/run_round.py --run-id 2026-09-29-r2-queries
```

## Uso rápido
```bash
export ARCHATLAS_DATASET=/caminho/para/siga-doc   # checkout read-only da versão modificada (SHA e3be22828)
python -m pytest -q
python -m archatlas.cli verify
```
Sem `ARCHATLAS_DATASET`, usa-se o vizinho `../siga` do checkout (quando existir).
