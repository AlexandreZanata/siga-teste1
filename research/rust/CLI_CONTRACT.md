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

## 8. Eventos de telemetria (nomes congelados)

`retrieved` (candidatos internos), `delivered` (bytes realmente enviados na resposta), `opened` (leitura explícita capturada pelo runner), `declared_relevant` (relato do agente, `null` por padrão).

Regra que motivou a seção: **`opened` exige evento real de leitura capturado pelo runner.** Derivar `opened` de `delivered` por fórmula sobre logs é proibido e invalida o cegamento do piloto.
