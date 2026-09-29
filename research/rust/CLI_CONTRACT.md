# Contrato da CLI `archatlas` — v1 congelado para R1

Data: 2026-09-29. ID: `CLI_CONTRACT/1`. Estado: **contrato congelado; binário Rust ainda não existe**.
Depende de: [`../plans/RUST_CLI_PILOTO_REAL.md`](../../plans/RUST_CLI_PILOTO_REAL.md) §2–§4, [`PROTOCOLO_VALIDACAO.md`](PROTOCOLO_VALIDACAO.md) §§2, 6.
Estado real do core no momento: SIGA/core `db3e714`; worktree Bitcoin `3623afb`. Evidência e defeitos medidos em [`BASELINE.md`](BASELINE.md).

Este arquivo é a especificação que R1 implementa e que o runner do piloto consome. Congelar aqui evita ajustar o contrato depois de ver resultados. Mudança de contrato exige `CLI_CONTRACT/2` e invalida comparações entre versões.

## 1. Invocação e transporte

- Executável único, sem Python no caminho normal, sem daemon, sem rede, sem GPU, sem LLM.
- `repo` e `index` são **sempre explícitos** no uso experimental. Descoberta automática só após validação (R6), e nunca herdando o DB global legado.
- **stdout**: exatamente um objeto JSON, sem texto ao redor. **stderr**: diagnóstico breve, sem código-fonte e sem paths absolutos do dataset.
- Codificação: UTF-8, sem BOM, `\n` final. Serialização compacta (sem espaços inúteis), chaves em ordem de campo do schema (determinismo para hash/replay).

## 2. Comandos

```sh
archatlas doctor --repo <checkout> --index <indice> [--format json|text]
archatlas index   --repo <checkout> --index <indice> [--incremental] [--workers N] [--force]
archatlas context --repo <checkout> --index <indice> --request <pedido.json>
archatlas expand  --repo <checkout> --index <indice> --request <expansao.json>
archatlas verify  --repo <checkout> --index <indice> --ref <arquivo:linha[@hash]>
```

| Comando | Efeito | Escreve índice | Escopo R1 |
|---|---|---|---|
| `doctor` | Estado do ambiente, do índice e das linguagens suportadas | não | sim |
| `index` | Constrói ou atualiza uma geração do índice | sim | sim |
| `context` | Responde a um pedido dentro do orçamento | não | sim |
| `expand` | Amplia por referência já entregue | não | **R2** |
| `verify` | Releitura do disco de uma referência citada | não | **R2** |

Regras que valem para todos:

- `--request` e `--ref` são **arquivos**, não strings de argv: o agente escreve JSON com ferramentas comuns e não precisa escaping no shell.
- `context` e `expand` **nunca** reconstroem o índice. Índice desatualizado produz estado `stale`; reconstruir é `index --incremental` explícito.
- Uma falha não pode devolver JSON de sucesso nem tocar outro índice. Índice corrompido é diagnóstico + código 3, nunca lista vazia fingida.
- Fontes selecionadas são re-lidas e re-hasheadas **antes** de entregar texto. Hash do arquivo citado não prova completude do índice.

## 3. Códigos de saída (congelados)

| Código | Significado |
|---|---|
| 0 | Resposta válida. `partial` é uma resposta válida com estado explícito. |
| 2 | Pedido inválido: JSON malformado, `schema_version` desconhecida, campo obrigatório ausente, `budget_tokens` não inteiro positivo, `--ref` malformado. Nada foi indexado. |
| 3 | Índice ausente, incompatível, corrompido ou desatualizado, **sem resposta válida**. |
| 4 | Erro de I/O, limite operacional excedido, lock ocupado, falha explícita de recurso (memória/disco). |
| 5 | Integridade violada: hash do arquivo diverge do registrado, ou `--ref` aponta para fora da raiz do repo. Falha ruidosa, jamais entrega texto não verificado. |

`--help` curto e exemplos; a saída de `doctor` é a única autorizada a ser legível em `--format text`. Divergência conhecida e intencional: a CLI Python de `db3e714` usa **2** para índice ausente/corrompido (`archatlas/cli.py:38-56,74-80`); o contrato Rust usa **3**, reserving 2 para o pedido. Registrado para que a comparação Python/Rust de R2 não trate isso como regressão sem comentário.

## 4. Schema — pedido (`context`, `expand`)

```json
{
  "schema_version": 1,
  "intent": "localizar|editar|testar|impacto|desconhecido",
  "query": "texto",
  "known_refs": [{"file": "caminho/relativo", "line": 120, "hash": "sha256:..."}],
  "snapshot": {"sha_base": "e3be22828", "tree_hashes": {}},
  "budget_tokens": 2000,
  "tokenizer_id": "identificador+versão+hash",
  "max_bytes": 20000,
  "policy": "CTX-RS|LEX-RS",
  "delivered_refs": []
}
```

- `policy` é obrigatória e nomeada; o runner registra qual política cada braço usou. Não existe política "padrão" implícita, para que uma falha de política não possa ser atribuída ao tratamento errado.
- `expand` exige `delivered_refs` e `evidence_wanted`; dedup spans já entregues.
- `budget_tokens` e `max_bytes` são **tetos independentes e simultâneos**: o limite efetivo é o primeiro atingido. Ambos declarados porque `tokenizer_id` pode faltar e o piloto ainda assim rodar em modo bytes.
- Campo desconhecido no pedido → código 2. Campo desconhecido na resposta é proibido.

## 5. Schema — resposta (`context`, `expand`, `doctor`, `verify`)

```json
{
  "schema": "atlas-context/1",
  "schema_version": 1,
  "state": "ok|partial|stale|unsupported",
  "snapshot": {"sha_base": "e3be22828", "index_generation": "...", "index_state": "ok"},
  "units": [
    {"file": "caminho/relativo", "line": 74, "end_line": 90,
     "hash": "sha256:...", "kind": "symbol|excerpt|relation|config|test",
     "text": "...", "evidence": "...", "reason": "...",
     "truncated": false}
  ],
  "budget": {"requested_tokens": 2000, "used_tokens": 1968,
             "unit": "tokenizer|byte", "tokenizer_id": null,
             "tokenizer_is_exact": false, "max_bytes": 20000, "used_bytes": 12043},
  "omitted": {"n": 11, "reasons": ["budget", "duplicate", "too_large"]},
  "hints": ["..."]
}
```

Regras de campo, todas obrigatórias:

- **`file` é relativo à raiz do repo.** Proibido absoluto, `..` ou home. Vazamento de path é defeito de privacidade, não detalhe de formatação.
- **`text` é o conteúdo entregue**, com hash do trecho. `reason` diz por que foi selecionado. `evidence` diz o que sustenta a seleção; `declared_relevant` do agente nunca é inferido aqui.
- `budget.used_tokens` conta **a serialização final inteira** (§6). `used_tokens` nunca é a soma dos itens. `tokenizer_is_exact: false` é obrigatório e visível quando o tokenizer não corresponde ao modelo.
- `omitted.n` e `omitted.reasons` são agregados, nunca logs. Lote de omissão vai para arquivo de diagnóstico próprio, fora do contexto.
- `hints` é curto e limitedíssimo: sem dump de paths, sem relações em massa.
- `state: stale` significa "índice anterior ao snapshot pedido", com `advice`; não significa "nada encontrado".

## 6. Ordem obrigatória do orçamento

O defeito que motiva esta seção está medido em [`BASELINE.md`](BASELINE.md) §4: o `used` declarado na referência Python é ~2x menor que o JSON realmente emitido.

1. gerar candidatos → 2. ranquear → 3. selecionar unidades → 4. montar JSON **completo**, já com `omitted`, `budget` e `hints` → 5. serializar e **contar a serialização final** → 6. remover/curtar → 7. serializar e contar de novo, iterar até convergir → 8. só então escrever em stdout → 9. avaliar exclusivamente o que foi entregue.

O campo `budget` só é preenchido após a contagem; a contagem é refeita depois do preenchimento. Budget menor que o envelope mínimo → `state: partial` com `omitted.reasons: ["envelope_too_large"]` e lista vazia de unidades, **não** payload estourado.

Sem tokenizer compatível, o limite é **exato em bytes**, `tokenizer_is_exact: false`, e o piloto é permitido rodar com telemetria de provedor. Ausência de tokenizer local não cancela o experimento; cancela apenas a alegação de budget rígido em tokens.

## 7. Compatibilidade e versionamento

- `schema_version` no pedido e na resposta. Pedido com versão desconhecida → código 2, sem fallback silencioso.
- Índice Rust tem schema próprio versionado (`index_generation`). Não abre nem migra DB legado Python.
- Mudança incompatível de campo ou de código de saída → novo `CLI_CONTRACT/N`. Comparações cruzam versões publicam a versão nos dois lados.

## 8. Esclarecimentos de R1

A implementação da fatia R1 encontrou pontos que o contrato não especificava. Ficam fixados aqui para que R2 compare contra uma regra escrita, e não contra o comportamento acidental do binário. Nenhum item altera campo, nome ou código já descrito acima: todos **preenchem lacunas**.

### 8.1 Payloads de `doctor` e `index`

`§5` descreve o envelope de `context`. `doctor` e `index` usam a mesma *forma* de envelope, mas com `schema` próprio — um consumidor deve selecionar pelo id antes de validar campos:

- `doctor` → `"schema": "atlas-doctor/1"`, mais `env`, `index` e `languages`.
- `index` → `"schema": "atlas-index/1"`, mais `repo_root_id`, `index` e `counts`.

A proibição de campo desconhecido (`§4`) vale por id de `schema`: o cliente que só entende `atlas-context/1` não deve ler um payload de `atlas-doctor/1`.

### 8.2 Semântica de `hash`, `state` e caminhos

- `units[].hash` é `sha256:<hex>` do **conteúdo inteiro do arquivo**, recalculado no disco no momento da entrega. É o mesmo valor que `verify --ref` compara, o que mantém uma única noção de "hash verificado" no contrato.
- `state`, em ordem de severidade: `unsupported` (índice não pode responder de forma alguma) > `stale` (índice anterior ao snapshot pedido, ou fonte reprovada na verificação) > `partial` (algo foi omitido: orçamento, diversidade, truncamento) > `ok`.
- **Nenhum comando publica caminho absoluto em JSON.** Caminhos de máquina saem só em `doctor --format text`, que é modo humano. Para comparar raiz sem vazar path, `doctor` e `index` publicam `root_id` (sha256 do caminho canônico, 12 hex) e `index.root_matches`.
- Tempo decorrido **nunca** entra em stdout. Medição vai para stderr ou para o runner: stdout precisa ser determinístico para replay e hash.

### 8.3 Índice indisponível e verificação reprovada

- `doctor` sai 0 só com índice `ok`; nos demais estados emite o diagnóstico e sai 3.
- `context` com índice ausente/corrompido/incompatível/vazio emite o envelope com `state: unsupported` e sai 3 — nunca lista vazia fingida.
- **Nada verificável**: se havia candidatos e nenhuma fonte passou na verificação de bytes, não existe resposta verificada a dar → saída 5, sem JSON de sucesso.
- **Parcialmente verificável**: se parte das fontes reprovou, as reprovadas saem da resposta, `state` vira `stale` e o motivo `stale_source` é agregado em `omitted.reasons` — a parte verificada ainda é entregue.
- `expand` e `verify` pertencem a R2. Nesta versão saem 2 com mensagem explícita, em vez de aceitar o pedido e devolver algo diferente do contratado.

### 8.4 Piso do envelope

`max_bytes` pode ser menor que o envelope vazio, que é irreduzível. Nesse caso a resposta é `state: partial`, `units: []`, `omitted.reasons: ["envelope_too_large"]` e as pistas de expansão são omitidas (elas só aumentariam o piso). `budget.used_bytes` reporta o tamanho real, **mesmo quando excede `max_bytes`**: esconder o piso seria pior que reportá-lo. Nenhuma unidade é entregue, então nenhum trecho estoura teto.

### 8.5 Limitações declaradas de R1

- `index --incremental` é o padrão e compara **hash de conteúdo**; `--force` reconstrói do zero. O atalho por `mtime` não existe: ele trocaria correção por velocidade e quebraria a equivalência incremental ≡ rebuild que R1 exige.
- `index.counts.ignored` é `null` com `ignored_reason`. O walker poda entradas ignoradas antes de reportá-las; contar exigiria uma segunda varredura sem filtro.
- Todo `file` é indexado no nível **lexical**. Não há extrator de símbolos, então nenhuma resposta pode ser lida como definição ou resolução semântica.

## 9. Eventos de telemetria (nomes congelados)

`retrieved` (candidatos internos), `delivered` (bytes realmente enviados na resposta), `opened` (leitura explícita capturada pelo runner), `declared_relevant` (relato do agente, `null` por padrão).

Regra que motivou a seção: **`opened` exige evento real de leitura capturado pelo runner.** Derivar `opened` de `delivered` por fórmula sobre logs é proibido e invalida o cegamento do piloto.

## 10. Esclarecimentos de R2

Como em §8: nada aqui altera campo, nome ou código já descrito — preenche lacunas que a implementação de `expand` e `verify` encontrou. Relatório medido em [`R2_REPORT.md`](R2_REPORT.md).

### 10.1 `verify` — payload e veredito

Payload com `"schema": "atlas-verify/1"`, mesma forma de §5, mais `reference` e `checks`. Cada item de `checks` é um **fato medido**, não um rótulo:

| Campo | Significado |
|---|---|
| `inside_root` | o caminho resolvido fica dentro da raiz do repo |
| `file_exists` | o arquivo existe no disco agora |
| `registered_in_index` | o caminho relativo está registrado no índice |
| `hash_matches_index` | o `sha256` do disco é igual ao registrado; `null` se não há um dos dois |
| `hash_matches_arg` | o hash passado em `@` bate com o do disco; `null` se não foi passado |
| `line_in_range` / `line_count` | a linha citada existe no arquivo, e quantas linhas ele tem |
| `name_on_line` | **sempre `null`**: a forma `arquivo:linha[@hash]` não carrega nome de símbolo; inventar esse campo violaria a regra de não afirmar o que não foi lido |

Forma do argumento: `arquivo:linha[@hash]`, decomposto **da direita para a esquerda** (`dir/A.java:42`, e `sha256:` no hash não pode ser confundido com o separador de linha). `@` aceita `sha256:<hex>` ou `<hex>`, normalizado para minúsculas. Linha `0`, linha não numérica, `--ref` vazio e `--ref` sem `:` são código 2.

Veredito: **qualquer item verificável reprovado → código 5**, com `omitted.reasons` nomeando o motivo (`file_missing`, `not_indexed`, `stale_source`, `hash_divergent`, `line_out_of_range`) e um `hint` dizendo para não usar o trecho como fato. Caminho que escapa da raiz é `outside_root`, também código 5 — é violação de integridade, não "arquivo ausente". Quando a referência passa, a linha citada volta como **uma unidade** em `units`: verificar sem mostrar o que foi verificado obrigaria o chamador a reabrir o arquivo.

Limite declarado: `verify` confere **localização e integridade**. Não prova resolução semântica nem ausência de falso positivo.

### 10.2 `expand` — o que `evidence_wanted` significa

Vocabulário **fechado**: `context` (padrão), `references`, `tests`. Valor fora da lista é código 2 — um valor novo é mudança de contrato, não extensão silenciosa.

| `evidence_wanted` | De onde vem a evidência |
|---|---|
| `context` | ao redor das linhas apontadas por `known_refs` |
| `references` | arquivos que a consulta alcança, procurando pelo termo |
| `tests` | idem, restrito a caminhos que a heurística classifica como teste |

Regras de recusa, todas código 2, porque devolver vazio pareceria "nada encontrado":

- `expand` com `evidence_wanted` ausente ou `context` **exige** `known_refs` não vazio — sem referência apontada não há o que ampliar.
- `references` e `tests` procuram por termo, logo exigem `query` com pelo menos um token buscável.
- `end_line` (opcional) amplia por intervalo; `end_line < line` é normalizado para `line`.

Deduplicação em duas frentes: contra `delivered_refs` (o que o agente já recebeu) e contra os spans da própria chamada. `context` não é expansão ilimitada de trechos incluídos; cada unidade entregue tem `reason`.

### 10.3 `--include`

Lista por vírgula, validada contra o vocabulário de linguagens reconhecidas; item vazio ou desconhecido é erro de uso. Item descartado pelo filtro **nunca é descartado em silêncio**: `counts.excluded_by_filter` reporta quantos arquivos reconhecidos ficaram fora. É esse campo que permitiu congelar o corpus comum com a referência Python (504 arquivos) em vez do repositório inteiro (6 916).

### 10.4 O que o envelope fechado passou a valer, medido

§6 descreve a ordem obrigatória. R2 a mediu em 900 execuções por lado, com `chars//4` como unidade comum aos dois:

- Rust: `used_bytes` == tamanho do stdout emitido em **900/900**; razão declarado/entregue = **1,00** em mediana e em máximo; **0/900** acima de `max_bytes`.
- Referência Python: declara **438** tokens para um payload de 978 tokens pela própria heurística (razão **0,45**), não publica bytes entregues, e **315/900** execuções entregam mais que o teto de bytes que o outro braço respeitou.

Fica registrado que a interface Python **não recebe** `max_bytes`: a divergência é de contrato entre produtos, não descumprimento de um teto aceito. A comparação de R2 é, por isso, entre produtos distintos — conforme a cláusula de não equivalência do plano §6.
