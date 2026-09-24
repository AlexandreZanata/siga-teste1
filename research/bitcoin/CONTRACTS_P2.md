# BTC-P2 — Contratos do adaptador e medição Bitcoin

Data: 2026-09-24. Dono: agente B. `core_sha`: `e6fde134f7da0d3616d90c40232d9ebe2ed9f033`
(somente leitura; nenhum edit em `archatlas/*.py` existentes, testes comuns ou packaging).
`schema_version`: `btc-contracts/1`. Adaptador: `btc-cpp-lex/1` (`archatlas/bitcoin/cpp_lex.py`,
commit deste checkpoint — ver `plans/bitcoin/STATUS.md`).
Reuso publicado compatível: `archatlas.telemetry:score_delivery/rescore_runs/verify_replay/
payload_tokens_for_capsule/build_manifest`, `archatlas.verify:verify_symbol`,
`archatlas.dataset:discover/extract_py/EXCLUDE_DIRS` — todos em `core_sha`, sem modificação.
Falta de extensão genérica vira pedido `BTC-CORE-NNN`; nenhum pedido aberto nesta etapa.

## 1. Snapshot do repositório

- Dataset real: `BTC_SHA` pendente (`benchmarks/bitcoin/PIN.md`). Sem SHA, sem indexação do corpus,
  sem benchmark, sem escrita no dataset base (inexistente aqui).
- Fixtures sintéticas desta etapa carregam `content_hash` (sha256) próprio e `file` absoluto do
  `tmp_path`; nunca são apresentadas como medidas do corpus. Árvore efetiva = `core_sha` + arquivos
  deste commit (ver STATUS). Nenhum blob de terceiro copiado ao repositório.

## 2. Adaptador de linguagem (`archatlas/bitcoin/cpp_lex.py`)

- `discover_cpp(root)` exige `root` explícito (`None` → `ValueError`; inexistente →
  `FileNotFoundError`); nunca lê `ARCHATLAS_DATASET` nem cai para dataset SIGA. Descobre
  `.c/.h/.hpp/.cpp` ordenados, respeitando `EXCLUDE_DIRS` publicadas.
- `extract_cpp_lexical(path)` emite fato-arquivo (`file-identity`, confiança 1.0: só identidade,
  não conteúdo) + fatos-`include` (`lexical-verified`, confiança 0.6) para `#include "..."` e
  `<...>` com verificação nome-na-linha; linhas `include` malformadas vão para `skipped` com motivo
  (nunca descarte silencioso). Retorno: `{"facts", "skipped"}`.
- `verify_fact(fact)` delega a `verify_symbol` publicada para fatos com linha; fato-arquivo verifica
  existência + hash. Falha = `(False, motivo)`, nunca correção silenciosa.
- Limites declarados: texto/includes verificáveis apenas. Sem parser C++ identificado: overload,
  template instanciado, chamada virtual, alvo de macro e resolução de header NÃO são afirmados.
  Python usa `extract_py` publicada (parser `ast` da stdlib, identificado).
- `compile_commands.json`, quando produzido (pós-PIN), integra o ambiente versionado por hash;
  headers compartilhados exigem invalidação de dependências, não só do arquivo editado.

## 3. Armazenamento e atualização (regras para a rodada real; sem DB nesta etapa)

- Runtime por rodada: `$TMPDIR/archatlas-bitcoin/<run_id>/` (SQLite/WAL, caches, logs, builds).
  Nenhum DB gravável, build-dir, datadir, socket ou proxy compartilhado com a trilha SIGA.
- Mudança/exclusão/renomeação invalidam relações/cache dependentes; equivalência lógica com rebuild
  sem exigir identidade binária do SQLite. `stable_hash` publicada serve à comparação futura.

## 4. Solicitação de contexto e orçamentos

- Campos: objetivo (`localizar|entender|editar|testar|impacto|desconhecido`), consulta, símbolos/
  arquivos conhecidos, snapshot, contexto já entregue, orçamento restante, `focus` opcional.
- Budgets diagnósticos 2k/8k com tokenizer `chars//4` (estimativa de diagnóstico — `capsule.py:13-14`,
  `telemetry.py:19-20@core_sha`); custo total inclui instruções, chamadas, histórico, respostas,
  auxiliares e indexação quando houver rodada. Sem telemetria confiável, sem conclusão faturada.

## 5. Recuperadores e montador

- Disponíveis: lexical (BM25 publicada, baseline), símbolos Python-AST, includes C++ lexicais.
  Relações: nenhuma (controle sem arestas é o padrão até prova em contrário).
- Montador futuro mede a serialização inteira via `payload_tokens_for_capsule` publicada; itens
  omitidos e limitações declarados; `opened`/`declared_relevant`/`history_tokens` nulos com motivo
  até a rodada viva.

## 6. Adaptador do agente e avaliador

- Dataset por variável **somente no processo** (`ARCHATLAS_DATASET=<checkout>` por comando);
  `ARCHATLAS_DATASET_BTC` segue alias planejado, não reconhecido pelo core. Sem profile global.
- Avaliador recebe SOMENTE `(delivered, gt)` (`score_delivery(delivered, gt)` — assinatura verificada
  em teste); gabaritos/testes ocultos futuros ficam fora da árvore do executor. Builds limpos/
  reutilizados são condições documentadas iguais entre braços.

## Aceite BTC-P2 (escopo deste commit)

- [x] Contratos especificados com versões (`core_sha`, `btc-contracts/1`, `btc-cpp-lex/1`).
- [x] Adaptador em namespace Bitcoin + fixtures C++/Python sintéticas com ouro independente.
- [x] E26-00 espelho sintético: replay estável, payload inteiro, stale detectado (`REPORT.md`).
- [x] Nenhuma queda para dataset SIGA (falha ruidosa); nenhuma escrita no dataset base.
- [ ] Pendente de PIN: manifesto de build/índice do corpus, `compile_commands.json`, piloto de patches.
