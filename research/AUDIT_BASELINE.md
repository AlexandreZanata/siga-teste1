# AUDIT_BASELINE — P0 auditoria do ponto de partida

Data: 2026-09-24. Estado: `concluida` (auditoria documental + leitura de código, sem refatoração).
ID: P0. Dependências: código em `37021fc`, relatórios F0–F20, `benchmarks/siga/PIN.md`, `plans/PESQUISA_CONTEXTO_MODULAR.md`.
Pergunta: quais afirmações centrais do ArchAtlas estão sustentadas pelo código/testes atuais e o que exige correção antes de P1–P3?

Método: só leitura de bytes reais via `Read` + comandos de verificação abaixo. Sem alterar `archatlas/*.py`. `pytest -q` verde nesta revisão: `24 passed in 46.30s` (offline, stdlib-first).
Comandos realmente executados:
- `python -m pytest -q` → 24 passed
- `git rev-parse HEAD` → `37021fc3f96937e28fd64fd1ec853924d4630411`
- `python3 -c` contagem `benchmarks/siga/queries_dev.json` → 153 Qs (A36/B36/D33/C10/E10/G10/F10/H8)
- `ls ../siga` → dataset irmão existe (checkout read-only; SHA base `e3be22828f787cbe71b339aecb7a7bf569099803` por PIN)
Arquivos de entrada: `archatlas/capsule.py`, `harness.py`, `strategies.py`, `extract.py`, `verify.py`, `query.py`, `lexical.py`, `config.py`, `benchmarks/siga/PIN.md`, `benchmarks/siga/queries_dev.json`, `experiments/agent_ab/RESULTS.md`, `BLIND4.md`, `BLIND_H.md`, `research/02_RELATED_WORK.md`, `research/16_BASE_EXPERIMENTAL_2026.md`, `plans/PESQUISA_CONTEXTO_MODULAR.md`, `plans/EXPERIMENTOS_2026.md`.
Arquivos permitidos para alteração nesta etapa: somente `research/AUDIT_BASELINE.md` (este arquivo). Nenhum `archatlas/` tocado.

Classes de status: `observada` = lida no código/relatório sem reexecução do benchmark; `reproduzida` = confirmada por teste verde nesta revisão; `pendente` = exige medição futura, não usar como prova.

## 1. Achados (afirmação → implementação → evidência → limitação → correção)

### A1. Contagem de tokens / "hard budget"
- Afirmação histórica: cápsula respeita budget hard de tokens.
- Implementação: `archatlas/capsule.py:11-12@37021fc` (`count_tokens = len(text)//4`); `capsule.py:68-72@37021fc` soma custo por item selecionado; cabeçalho declara `capsule.py:83@37021fc` (`tokenizer: chars//4, hard_enforced: True`).
- Evidência disponível: leitura direta do código; `tests/test_f5.py` verde cobre curva/budget no harness antigo.
- Status: `observada` (código faz o que diz) mas **não** `reproduzida` como limite real de modelo.
- Limitação: contabiliza só itens selecionados (`item = file:line kind name :: line_text`), não a serialização inteira do payload, instruções de ferramenta, histórico, respostas ou auxiliares. `chars//4` é estimativa de diagnóstico.
- Correção (P2/E26-00): medir payload serializado inteiro + separar `retrieved/delivered/opened/declared_relevant`; congelar tokenizer/contagem oficial; não alegar economia faturada sem telemetria.

### A2. Hit/recall do harness
- Afirmação histórica: recall 1.00 em vários freezes (F7/F8/F10/F11/F17/F18/F19).
- Implementação: `archatlas/harness.py:38-50@37021fc` — `files=set(cap[files])`; se GT tem `files` → `any(f in files)`; `edges` → `any(e[file])` (+ `path_files` com `and any`); `package` → prefix; senão `gt[file] in files`. Retorna `harness.py:57@37021fc` (`recall=hits/len`).
- Evidência: leitura direta; `tests/test_harness.py` + `test_fidelity.py` verdes confirmam o cálculo atual, não a validade externa do GT.
- Status: `observada` como "hit de algum arquivo esperado"; `pendente` como recall completo de conjunto/caminho.
- Limitação: `any(...)` chama de `recall` uma taxa de acerto parcial; um membro de conjunto recuperado não é 100% de recall; caminho completo, precisão e cobertura sob orçamento não são medidos.
- Correção (P2/E26-00): renomear para `hit`, adicionar recall/precisão de conjunto, cobertura de caminho, utilidade para patch e replay determinístico; fixtures com acerto parcial/alternativos válidos/spans sobrepostos/arquivo inexistente/trecho alterado pós-index.

### A3. Tempo / latência (p50/p95, "24x", "paga-se na escala")
- Afirmação histórica: query ~ms pós-index; F16 RAW 66s vs TRACE 2.7s (24x); F19 p95 372→119ms; F14 p50/p95 26/332ms.
- Implementação: `archatlas/harness.py:33-36,54-59@37021fc` mede `perf_counter` por query (só `build_capsule`), p50/p95 por índice ordenado.
- Evidência: `experiments/agent_ab/RESULTS.md:21@37021fc` declara baseline ~30s/12 passos vs Atlas ~53s parede (núcleo 10.9s) e conclui "baseline mais rápido no micro-lote"; `BLIND4.md:21@37021fc` mistura queries ms vs agente s; `BLIND_H.md:7@37021fc` compara 66s/18 passos vs 2.7s.
- Status: `observada` (números estão nos relatórios); `pendente` como custo ponta a ponta.
- Limitação: tempo de consulta ≠ tempo do agente; custo de indexação fria/quente, chamadas auxiliares, histórico e manutenção não entram no mesmo denominador; amostra pequena (6Qs F6, 8Qs H).
- Correção (P3): custo total de todas as tentativas / tarefas resolvidas, com p50/p95 ponta a ponta, frio/quente/amortizado (1/10/100 tarefas), preços/data/fonte; timeout/crash do tratamento conta contra ele.

### A4. Provenance e verificação (anti-falso-positivo)
- Afirmação: todo fato carrega `arquivo:linha@SHA` + hash, re-verificado antes do commit.
- Implementação: `archatlas/verify.py:8-20@37021fc` (existe + hash idêntico + linha no intervalo + nome na linha, senão descarta com log); `archatlas/query.py:44-55@37021fc` (`find_references` exige nome literal na linha lida do disco, `confidence 0.7 text-match-verified`); `archatlas/capsule.py:65-67@37021fc` descarta classe sem nome na linha.
- Evidência: `tests/test_extract.py` + `tests/test_census.py` verdes (execução automatizada do protocolo F1/F2).
- Status: `reproduzida` como localização/integridade no escopo testado.
- Limitação: releitura + hash + nome na linha provam localização/proveniência, não resolução semântica (tipos/chamadas), nem ausência universal de falsos positivos. `confidence` 1.0/0.9/0.7 são rótulos históricos, não probabilidades calibradas.
- Correção (P1/P2): tratar `confidence` como rótulo; separar fatos estruturais de candidatos heurísticos; após edições locais verificar hashes da árvore efetiva (SHA base sozinho não representa working tree).

### A5. Extrator Java por regex
- Afirmação: extração determinística de classes/métodos.
- Implementação: `archatlas/extract.py:8-9@37021fc` (`CLASS_RE`, `METHOD_RE`); `extract.py:27-29@37021fc` filtra keyword (`if/for/while/...`) e exige nome na linha.
- Evidência: leitura direta; testes verdes para casos cobertos.
- Status: `observada`/`reproduzida` no escopo dos testes; `pendente` como resolução semântica geral.
- Limitação: regex não resolve overloads, DI, macros/templates, includes dinâmicos, JSP/JS/CSS; `BLIND4.md:27@37021fc` registra caso `try (` virando callee (fix com SKIP + regeneração de Qs).
- Correção (P4/E26-03): declarar capacidades por linguagem; relações incertas seguem candidatas; não indexar enunciados/patches/testes ocultos.

### A6. Roteador em cascata (s_router)
- Afirmação: router 1.00 com menor custo (sai cedo).
- Implementação: `archatlas/strategies.py:34-42@37021fc` — estrutural → se ≥3 arquivos retorna; senão une lexical → se ≥3 retorna; senão `hybrid_refs` (cápsula).
- Evidência: `BLIND4.md:4-10@37021fc` (bake-off 100Qs: lex/struct/hybrid 0.92, hybrid+refs/router 1.00, router 10ms).
- Status: `observada`.
- Limitação: critério de parada é quantidade de arquivos (≥3), não suficiência para editar; não mede tokens totais nem qualidade de patch.
- Correção (P4/E26-02): comparar cápsula fixa vs expansão progressiva com mesmo ranking/budget, cobrando novas consultas; escolher vencedor por patch aceito/dependências omitidas/releituras/custo, não só recall.

### A7. Bibliografia / novidade / custos de relacionados
- Afirmação antiga em `research/02_RELATED_WORK.md`: tabela com token overhead, diferenças e "verificado".
- Implementação documental: ressalva adicionada em `research/02_RELATED_WORK.md:3-5@working-tree` (catálogo histórico em auditoria, não revisão integral).
- Evidência: `research/16_BASE_EXPERIMENTAL_2026.md` registra 9 papers 2026 com versões/fontes/limites consultados em 24/09/2026, sem reprodução; `plans/PESQUISA_CONTEXTO_MODULAR.md:43-58` fixa fundamentos 2023–2025 + uso da base 2026.
- Status: `pendente` para qualquer decisão (custos, capacidades ausentes, novidade, licenças exigem ficha com artefato pinado).
- Limitação: ausência de informação ≠ ausência de capacidade no relacionado; recência (FeatLens/CliffCompaction com 2 dias no corte) não é prova de ganho.
- Correção (P1): completar fichas com artefatos pinados, licenças, custo real; distinguir reprodução/adaptação/inspiração; alvos iniciais Agent Retrieval Bench + CliffCompaction condicionados a artefato/controle do histórico (alternativa E26-02 registrada).

### A8. Gabaritos / GT (queries_dev 153 Qs, GT-sets, caminhos)
- Afirmação: GT cobre A–H com sets e caminhos.
- Implementação/artefatos: `benchmarks/siga/queries_dev.json` com 153 Qs nesta revisão (A36/B36/D33/C10/E10/G10/F10/H8); harness aceita `file/line`, `files`, `edges/path_files`, `package` (ver A2).
- Evidência: `BLIND4.md:25@37021fc` admite GT escopo-40 pune acertos fora do escopo (5/6 callers reais fora da amostra) → exigiu F14 escopo total; `BLIND_H.md:11@37021fc` admite GT-caminho-único subestima (3 caminhos válidos para `converter→ByteArrayInputStream`) → F17 GT-conjunto; `RESULTS.md:5@37021fc` admite D aceita qualquer ref verificada.
- Status: `observada` a estrutura; `pendente` a validade externa (gabaritos independentes do extrator, splits por família/área, holdout isolado).
- Limitação: nenhuma tarefa F0–F20 conta como teste inédito; divisão aleatória de perguntas quase idênticas vaza; repetição ≠ amostra independente.
- Correção (P1–P3): ouro por revisão independente; splits por família/área; checkout anterior ao patch; bloqueio a commits futuros/soluções/testes ocultos; custodiante + manifesto selado; avaliação cega de patches com IDs aleatórios.

### A9. PIN / dataset / stack
- Afirmação vigente: `benchmarks/siga/PIN.md:1-7@37021fc` — SIGA-Doc modificado, branch `desenvolvimento`, SHA `e3be22828f787cbe71b339aecb7a7bf569099803`, Java 21, `siga-doc 11.5-SNAPSHOT`.
- Evidência: `tests/test_pins.py` automatiza `rev-parse == PIN`; `archatlas/config.py:10-18@37021fc` lê `ARCHATLAS_DATASET` sem path de máquina; `config.py:21-28@37021fc` usa paths relativos (`as_rel`).
- Status: `reproduzida` a mecânica (teste verde + config sem paths); `observada` a SHA base.
- Limitação: refs antigas a Java 8/`develop` em `research/03_RESEARCH_QUESTIONS.md:8@working-tree` estão desatualizadas (ressalva adicionada); SHA base não representa árvore após edições do agente.
- Correção: reconciliar docs antigos (feito via ressalvas nesta revisão); em P2+ registrar snapshot + hashes da árvore efetiva + versão de extratores por execução.

### A10. F0–F20 como histórico
- Afirmação: F0–F20 concluídos com SHAs em `docs/ROADMAP_ETAPAS.md`.
- Evidência: `git log --oneline` contém F13–F20; roadmap marca F0–F20 `[x]` e F21/P3 `[ ]` com dependência P0–P2.
- Status: `observada` como registro histórico; `pendente` como confirmação científica (sem revalidação nesta revisão).
- Limitação: conclusões antigas (recall, latência, "vitórias") não são confirmação de economia/qualidade em edição.
- Correção: nenhum resultado antigo renomeado silenciosamente (aceite P0 atendido via ressalvas em README/ROADMAP/VERIFICATION/MEMORY/02/03/04/10/13 + base 16 + planos P/E26).

### A11. Bitcoin / transferência
- Afirmação vigente: Bitcoin removido das etapas executáveis; foco 100% SIGA-Doc até fidelidade comprovada (`docs/ROADMAP_ETAPAS.md:31@working-tree`); `plans/BITCOIN_PARALLEL_PLAN.md` isola `exp/bitcoin` (branch próprio, só `benchmarks/bitcoin/**`, `experiments/bitcoin_ab/**`, `archatlas/cpp.py` novo, `tests/test_btc_*.py` novos, DBs em `/tmp/opencode-btc/`).
- Status: `observada` (isolamento documentado, sem execução nesta revisão).
- Correção: Bitcoin segue candidato opcional pós-P5 (P6), não próximo passo; transferência exige ≥2 repos externos selecionados antes do teste.

## 2. Aceite P0
- [x] Toda alegação central acima classificada como observada/reproduzida/pendente.
- [x] Nenhum resultado antigo renomeado silenciosamente (ressalvas explícitas, histórico F0–F20 preservado).
- [x] Sem refatoração nesta etapa (só este arquivo criado; `git status` deve mostrar apenas docs + este arquivo).
- [x] `pytest -q` verde registrado (24 passed).

## 3. Decisão e próximo passo
Decisão: P0 concluída. Próximo: **P1** (completar leitura/auditoria de artefatos dos 9 papers + `research/PREREGISTRATION.md` preliminar com hipóteses, comparadores A/B/C, métricas, rubricagem, política de falhas) e **P2** (contratos + telemetria + E26-00 instrumentação de `retrieved/delivered/opened/declared_relevant`). Não iniciar F21/P3, instalador universal, MCP, vetores obrigatórios ou publicação antes desses portões. Pendências que bloqueiam rodadas pagas: IDs efetivos de modelos (Muse Spark 1.3 / DeepSeek Flash v4.1 / Luna 6 a resolver), teto de custo/tempo, ambiente build/teste SIGA, custodiante do holdout, projetos de transferência, responsáveis pela rubrica semântica.
