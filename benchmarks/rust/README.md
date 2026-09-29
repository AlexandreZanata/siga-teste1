# Harness de medição — braço Rust

Ferramentas de medição de [`plans/RUST_CLI_PILOTO_REAL.md`](../../plans/RUST_CLI_PILOTO_REAL.md) etapas R1/R2. Nenhum número de relatório é digitado à mão: tudo sai de `.jsonl` brutos agregados por [`report.py`](report.py).

O que este diretório **não** faz, e nenhum relatório pode sugerir que faz: não derruba o cache de filesystem (isso exige `drop_caches` com root em máquina dedicada), não isola cgroup, não chama modelo nenhum e não decide se um patch é bom. Mede processo externo, do spawn até consumir stdout, com cache aquecido.

## Rodada completa

```bash
python benchmarks/rust/run_round.py --run-id 2026-09-29-r2-queries
# opcional: --with-scale (copia o corpus ×N), --skip-*, --expand-reserve-pcts 30,50
```

Ordem: corpus congelado e verificado → consultas → índices (diretórios exclusivos) → `context` → `expand`/`verify` → `doctor` → opcionalmente escala → `tables.md`. O driver **aborta** se o corpus dos dois braços não for equivalente (mesmos caminhos **e** mesmos hashes de conteúdo) e registra em `manifest_round.json` a linha de comando, o ambiente e o `sha256` do binário medido.

## Passos isolados

Cada modo pode ser reexecutado sozinho com [`measure.py`](measure.py); o `manifest_*.json` daquele modo guarda a invocação exata, então uma tabela sempre tem origem rastreável.

```bash
# corpus comum + consultas estratificadas
python benchmarks/rust/freeze_corpus.py --out <dir> --keep-indexes
python benchmarks/rust/gen_queries.py --corpus <dir>/corpus.json --out <dir>/queries.json

# medições (--mode query|index|update|expand|verify|doctor|scale)
python benchmarks/rust/measure.py --mode expand --out <dir> \
  --queries <dir>/queries.json --rust-index <dir>/index_rust.sqlite \
  --budgets 2000,8000 --reps 5 --reserve-pcts 30,50 --include-edge

# tabelas
python benchmarks/rust/report.py --run <dir>
```

`--reserve-pcts` mede `evidence_reserve_pct` (contrato §10.5) **dentro do mesmo ensaio**: cada valor acrescenta uma variante de `references`, para que o antes/depois seja política contra política, não invocação contra invocação. `--include-edge` acrescenta as 6 consultas de borda às 30 estratificadas.

## Artefatos

| Arquivo | Conteúdo |
|---|---|
| `corpus.json` | equivalência dos dois corpora, com fingerprint de conteúdo |
| `queries.json` | 30 consultas em 5 estratos de `doc_freq` + 6 de borda |
| `runs_*.jsonl` | uma linha por execução medida, com o que cada lado **declara** e as checagens do harness |
| `manifest_*.json` | invocação, ambiente, repetições, `sha256` do binário |
| `tables.md` | agregado de todos os `runs_*.jsonl` da pasta, com a lista de artefatos no cabeçalho |

Índices `.sqlite` ficam na pasta da rodada quando `--keep-indexes` é usado; são ignorados pelo git e não entram em commit.

## Checagens que não vêm do produto

O que o braço medido declara sobre si é lido, mas não é a evidência: sobreposição de spans é calculada por interseção de intervalos, `used_bytes` é comparado ao tamanho real do stdout, o código de saída esperado de cada cenário de `verify` é fixado **antes** da medição, e `evidence_reserved`/`lexical_units`/`window_units` saem de varredura no JSON da resposta. Se o harness só lesse `omitted.reasons`, dois defeitos reais já medidos teriam passado (ver [`R2_REPORT.md`](../../research/rust/R2_REPORT.md) §3.1 e §8.1.1).

[`runner.py`](runner.py) é outro instrumento: executa **uma tentativa** do piloto (tarefa, condição, workspace, executor), aplica os tetos do pré-registro antes de qualquer medição e nunca resume resultados — a agregação é de R4/R5. Contrato em [`RUNNER_PILOTO.md`](../../research/rust/RUNNER_PILOTO.md).
