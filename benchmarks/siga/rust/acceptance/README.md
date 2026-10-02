# Aceite smoke SIGA — pacote do avaliador (TASK-A03)

Data: 2026-10-02. Conjunto: [`smoke.tasks.json`](smoke.tasks.json) (`atlas-tasks/2`,
4 tarefas, `eval.py validate` limpo).

## O que é público (este diretório)

`run.sh` + `AtlasAccept0{1,2,3,4}.java`: o comando de aceite imutável do avaliador.
Cada harness imprime `PASS`/`FAIL` por caso e sai com código diferente de zero em
qualquer falha; sem Maven/JUnit/rede (só `javac`/`java` + 3 jars do repo Maven local).
Resultados medidos nesta revisão (logs sanitizados em
`experiments/rust/siga/2026-10-02-a03-validation/logs/`):

| Tarefa | Base (vermelho) | Referência (verde) |
|---|---|---|
| SIGA-REAL-01 | 5/6, exit 1 | 6/6, exit 0 |
| SIGA-REAL-02 | 4/6, exit 1 | 6/6, exit 0 |
| SIGA-REAL-03 | 8/10, exit 1 | 10/10, exit 0 |
| SIGA-REAL-04 | 3/6, exit 1 | 6/6, exit 0 |

Casos privados do avaliador (custódia, fora deste repo): vermelho 3/7, verde 7/7.

## Instalação no workspace do avaliador

1. Base limpa no `base_sha` da tarefa (workspace novo por tentativa).
2. Copiar este diretório para `<acceptance-repo>/atlas-accept/` **antes** de aplicar
   o patch candidato.
3. Aplicar o patch, rodar `bash atlas-accept/run.sh <ID>` com cwd na raiz do repo.
4. O executor nunca escreve em `atlas-accept/` (`immutable_paths` de cada tarefa
   cobre `atlas-accept/**`; violação reprova em M5 antes de qualquer revisão).

Dependências de ambiente (bloqueio, nunca veredito): JDK 21 completo (`javac` no
PATH) e os 3 jars no repo Maven local (caminhos em `run.sh`; ausente => exit 3
`ATLAS-ENV-BLOCK`). Medido: compilação+execução de ~2–5 s a frio; `timeout_s`
do conjunto é 600.

## O que NÃO está aqui (custódia, fora do git)

Soluções de referência, casos privados e a chave de mapeamento ficam em diretório
fora do repo e fora do workspace do executor (ver `research/siga/rust/CURADORIA_SMOKE.md`
§ isolamento). Nenhum arquivo deste pacote contém, cita ou importa a solução.
