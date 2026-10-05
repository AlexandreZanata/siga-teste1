# NEXT-03 — Ensaio completo offline + isolamento (2026-10-05)

Tentativa offline completa sem modelo e sem gasto: workspace do executor,
patch em base limpa, aceite público + casos privados do avaliador, bundle
cego e adjudicação. Operadores **sintéticos** (ver `operators/README.md`);
nada aqui mede capacidade de agente — o que se ensaia é o caminho que a
primeira rodada real vai percorrer.

## 1. Desenho

Três braços BASE, fase piloto, tarefas do lote 17–20
(`benchmarks/siga/rust/pilot3.tasks.json`), base `e3be22828` (workspaces
`/tmp/n03-ws1..3`, aceitação `/tmp/n03-acc1..3`, um par novo por tentativa):

| Braço | Tarefa | Operador | Saída simulada | Esperado |
|---|---|---|---|---|
| att-a1 | SIGA-REAL-17 | exec-a1.py (query canônica) | correta | aceito |
| att-a2 | SIGA-REAL-20 | exec-a2.py (`toLowerCase`) | parcial | rejeitado |
| att-a3 | SIGA-REAL-19 | exec-a3.py (nada) | vazia | rejeitado (M3) |

Cada operador roda confinado via `benchmarks/rust/sandbox.py`
(`atlas-sandbox/1`, bwrap: usuário+montagem+rede), composto no runner por
`--executor-cmd` (o runner não mudou). Negados com prova: custódia,
`research/`, diretório das tentativas e `/tmp` (workspaces irmãos e
scratch); rede isolada; segredos removidos do ambiente (canário
`ATLAS_PROBE_CANARY` plantado e removido — `env_leaked: []` nas 3 provas).

O `atlas-accept/` (aceite público) foi instalado pelo orquestrador em cada
base de aceitação a partir do pacote versionado
`benchmarks/siga/rust/acceptance/` (`sha256:fb46624…`, só arquivos
não-rastreados — preflight de árvore rastreada limpa passa), como manda a
instalação documentada no cabeçalho do `run-pilot3.sh`.

## 2. Cadeia executada (reproduzível)

Ambiente dos gates: `PATH` com o JDK 21 primeiro,
`M2_REPO=~/.m2/repository`. Ordem: runner ×3 → `grade.py` ×3 (com
`--acceptance-scripts` e `--private-java` da custódia, caminho nunca
publicado) → `eval.py check` → `bundle` (seed `20261005`) → notas cegas
(`scores.json`) → `validate-scores` → `unblind`.

## 3. Resultados por tentativa

| Braço | Patch | Prova | Público (runner) | Privado (grade) | Mecânica | Veredito final |
|---|---|---|---|---|---|---|
| att-a1 | 1292 B | ok (4 negados, rede isolada) | 8/8 verde | 8/11, escopo r17 2/2 | aceito | **aceito** (revisor pondera escopo) |
| att-a2 | 569 B | ok | 12/14 vermelho | 4/11, escopo r20 0/2 | rejeitado (M2) | **rejeitado** |
| att-a3 | vazio | ok | vazio | — | rejeitado (M1/M2/M3) | **rejeitado** |

Adjudicação (`eval-report.json`): BASE 3 tentativas, 1 aceito (0,3333 por
tentativa). `cost_per_success: null` **com motivo** (sem custo faturado,
P2 pendente — falta de custo bloqueia, não vira zero). Bundle
`sha256:ca264e6e…`: 0 vazamentos hard, 0 soft; amostra dupla de 1 item com
segundo veredito registrado; `validate-scores` exit 0; `unblind` recusaria
abrir rótulos sobre bundle alterado (hash conferido contra a chave).

## 4. Achados (o ensaio trabalhando)

1. **Tradução de caminho sandbox↔hospedeiro.** A primeira passada falhou com
   `FileNotFoundError /tmp/n03-ws1/…` dentro da sandbox. `sandbox.py` agora
   traduz hospedeiro→`/workspace`/`/out` em argv e ambiente (parte do
   isolamento: o executor nunca vê o caminho real), com `path_map`
   registrado no manifesto e teste dedicado. Re-rodada, a carga passou.
2. **O avaliador instala o harness público.** O clone fresco do `grade.py`
   não trazia `atlas-accept/` (público terminaria 127 = rejeição indevida
   do patch). Novo `--acceptance-scripts` (hash `fb46624…` registrado no
   `grade.json`, reproduzido por cálculo independente) e fail-closed: script
   relativo ausente vira `indeterminado` (`environmental`), nunca rejeição.
3. **Gate privado do lote exige ponderação de escopo.** `run-private3.sh`
   roda os 11 casos do lote por tentativa; uma tentativa unitária correta
   (att-a1) fica 8/11 porque o código das outras tarefas segue vermelho.
   O `grade.json` registra `rejected (private_gate)` **com a ressalva de
   que o escopo cabe ao revisor cego** + contagens por prefixo de tarefa
   (ex. r17 2/2); o revisor aceitou att-a1 e rejeitou att-a2 (r20 0/2).
   Regra "verde público sozinho nunca aceita" segue valendo e testada.
4. **Custódia dos logs privados.** Os `*.private.log` citam nomes e
   esperados de casos — foram revisados (contagens acima), tiveram o sha
   registrado e foram **apagados antes do commit**; no git ficam só
   contagens (`cases_passed/total`) e agregados por prefixo, na
   `review-sheet.json` sem condição/custo/ordem. Em produção esses logs
   ficam com o custodiante, fora do repo.
5. **Divergência de 1 caso no baseline privado.** Re-executado na base
   pristina: 6/11 passed (r17 0/2, r18 2/3, r19 2/4, r20 2/2) contra
   "vermelhos 6/11" da curadoria (= 5/11 passed). Consistente com att-a1
   (6+2=8/11), mas 1 caso acima do registrado — **reconciliar antes de usar
   o gate como medida**; não bloqueia o ensaio.
6. **Parcial pega no gate público, não no privado.** O operador A2 foi
   desenhado como "público verde + privado vermelho", mas o harness público
   cobre `&agrave;` (12/14). Registro corrigido: o ensaio demonstra
   rejeição no gate público com o privado também vermelho no escopo; o caso
   decisivo "público verde + privado vermelho no escopo" segue coberto pela
   regra testada (`test_grade_reprova_no_gate_privado` + fiação real do
   `run-private3.sh`).

## 5. Limites declarados deste ensaio

Operadores sintéticos (sem modelo, sem provedor, sem custo); condição única
(BASE — cegamento de condição vazio por desenho); revisor solo
(`rev-ensaio-1` = `rev-ensaio-2`: exercita a mecânica da dupla, não a
independência); sem palpites de condição; chave publicada pós-unblind como
registro (em produção, o custodiante guarda). Conclusão científica:
**não avaliada** — o ensaio prova o caminho, não utilidade.

## 6. Aceite NEXT-03

Prova de isolamento por tentativa (`sandbox_proof.json`, acesso negado
verificado, não só diretórios) ✓ · hash do pacote do avaliador
(`acceptance_scripts_sha256`, mais hash do bundle na chave) ✓ · resultados
público/privados por tentativa + final persistido em falha (`grade.json`,
`mechanical-check.json`, `eval-report.json`) ✓ · bundle sem
condição/custo/ordem/caminhos (0 hard/0 soft, `validate-scores` limpo) ✓ ·
revisores julgam o item cego antes da chave (notas → validação → unblind
com hash) ✓ · verde público não basta (regra + ponderação de escopo) ✓.

**NEXT-03 ensaiada em 2026-10-05.** Falta para a rodada real: NEXT-04
(modelo/teto) e revisores + custodiante independentes.
