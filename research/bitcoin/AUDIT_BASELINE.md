# BTC-P0 — Auditoria baseline do ponto de partida (trilha Bitcoin)

Data: 2026-09-24. Dono: agente B. `BASE_SHA`: `e6fde134f7da0d3616d90c40232d9ebe2ed9f033`.
Método: leitura de bytes reais na worktree (`codex/bitcoin-context`), sem editar o core,
sem indexar/benchmarkar Bitcoin, sem contar nenhum dado SIGA como evidência Bitcoin.
Evidências no formato `arquivo:linha@SHA` (SHA = `BASE_SHA`; hashes de conteúdo sha256
parciais registrados quando úteis). Nenhum número de dataset Bitcoin é afirmado.

## A1 — Descoberta C++ existe; extração C++ inexiste

- Implementação: `archatlas/dataset.py:8-9@e6fde13` mapeia `.c/.h/.hpp/.cpp` para `cpp`;
  `archatlas/dataset.py:45-54@e6fde13` retorna `[]` para qualquer `lang` fora de
  `java/python/jsp` (verificado em execução: `extract_any(<path>, 'cpp') == []`).
- Evidência: `archatlas/dataset.py:9@e6fde13` (`".c": "cpp", ...`);
  `archatlas/dataset.py:54@e6fde13` (`return []`); `sha256(dataset.py)=35fff68201c51447` (16 hex).
- Limitação: arquivos C++ são descobertos pelo `discover()` mas produzem zero símbolos;
  `compile_commands.json`, overloads, templates, macros e chamadas virtuais não têm suporte.
  Regex não será apresentada como resolução semântica.
- Correção necessária (futura, fora de P0): adaptador C++ em `archatlas/bitcoin/**`
  ou pedido `BTC-CORE-NNN` se exigir contrato genérico. Estado: **observada**.

## A2 — `store.index_file` é caminho Java; `index_any` delega mas C++ rende zero

- Implementação: `archatlas/store.py:8@e6fde13` importa `extract_java_symbols`;
  `archatlas/store.py:24-30@e6fde13` (`index_file`) sempre extrai Java;
  `archatlas/store.py:41-48@e6fde13` (`index_any`) delega a `extract_any`.
- Evidência: `archatlas/store.py:30@e6fde13` (`syms = extract_java_symbols(...)`);
  `sha256(store.py)=233eb22b4d1b1606`.
- Limitação: `index_many` (usado pelo harness) só indexa Java; `index_any`/`index_discovered`
  indexariam C++ como linhas vazias de símbolos (arquivo registrado, zero fatos).
  Invalidação de headers compartilhados não verificada aqui.
- Correção necessária: usar `index_any`/`index_discovered` na trilha Bitcoin somente após
  adaptador com ouro independente. Estado: **observada**.

## A3 — Dataset default é SIGA; sem alias Bitcoin no core

- Implementação: `archatlas/config.py:10-18@e6fde13` (`dataset_root()` lê `ARCHATLAS_DATASET`,
  senão `../siga`, senão erro); `archatlas/config.py:7@e6fde13` (`REPO_ROOT` = pai de `archatlas/`).
- Evidência: `archatlas/config.py:12-13@e6fde13` (`os.environ.get("ARCHATLAS_DATASET")`);
  `archatlas/config.py:14-15@e6fde13` (`REPO_ROOT.parent / "siga"`);
  `sha256(config.py)=3f7af28df1014ea2`.
- Limitação: passar dataset por variável só funciona se o chamador oferecer o parâmetro;
  default herdado aponta para SIGA/`/tmp/opencode`. Risco de contaminação cruzada se reusado sem override.
- Correção necessária: todo comando Bitcoin passa dataset explicitamente por processo;
  nunca herdar defaults. Nenhuma mudança de core nesta etapa. Estado: **observada**.

## A4 — Harness e censo estão hardcoded para SIGA

- Implementação: `archatlas/harness.py:16@e6fde13` (`SHA = "e3be22828..."`);
  `archatlas/harness.py:23-24@e6fde13` (três prefixos `siga-ex|cp|wf/.../*.java`);
  `archatlas/harness.py:27@e6fde13` (`index_many`, caminho Java);
  `archatlas/census.py:9-11@e6fde13` (`DATASET` avaliado no import + `MODULES` com 8 nomes `siga*`).
- Evidência: `sha256(harness.py)=94251d2145591e07`; `sha256(census.py)=8be4b2f4e9912d38`.
- Limitação: reusar `harness.run`/`census` sem adaptador indexaria SIGA, não Bitcoin.
  Nenhum resultado SIGA (F0–F20, recall 1.00, p95, sweep) é contado como resultado Bitcoin.
- Correção necessária: harness/censo Bitcoin próprios em BTC-P2 (fixtures, manifestos e DB isolado).
  Estado: **observada**.

## A5 — Orçamento e telemetria: estimativa `chars//4`, payload inteiro medido, hit ≠ recall

- Implementação: `archatlas/capsule.py:13-14@e6fde13` (`count_tokens = len//4`);
  `archatlas/capsule.py:86@e6fde13` (`tokenizer: chars//4`);
  `archatlas/capsule.py:100-106@e6fde13` (`payload_tokens`, `telemetry{retrieved,delivered,opened:0,...}`);
  `archatlas/telemetry.py:19-20@e6fde13` (mesma estimativa);
  `archatlas/telemetry.py:23-34@e6fde13` (`hit` = algum esperado; `recall_set` = fração completa);
  `archatlas/telemetry.py:77-84@e6fde13` (payload = serialização inteira `excerpts+citations+symbols`).
- Evidência: `sha256(capsule.py)=9b0b562e63e9cd06`; `sha256(telemetry.py)=6654f72cdcbbcdb7`.
- Limitação: `chars//4` é estimativa de diagnóstico, não prova de limite real de tokens do modelo;
  histórico/instruções fora da cápsula não entram no número (nulos com motivo).
  Versão publicada compatível será reusada somente se o SHA publicado a contiver.
- Correção necessária: nenhuma nesta etapa; BTC-P2 declara tokenizer efetivo e mede custo total.
  Estado: **observada** (código lido; sem replay executado nesta etapa).

## A6 — Verificador com 4 portões (reuso candidato)

- Implementação: `archatlas/verify.py:8-20@e6fde13` (existe → sha256 igual → linha no intervalo →
  `nome ∈ texto da linha`; falha = descarte com motivo, nunca correção silenciosa).
- Evidência: `sha256(verify.py)=8c46f5fa560f0797`.
- Limitação: prova localização/proveniência, não resolução semântica nem ausência universal
  de falsos positivos. `confidence` são rótulos históricos, não probabilidades calibradas.
- Correção necessária: fixtures C++/Python próprias em BTC-P2 antes de alegar verificação Bitcoin.
  Estado: **observada**.

## A7 — PIN e censo Bitcoin: ausentes (bloqueio explícito, não falha silenciosa)

- `benchmarks/bitcoin/` inexistente em `BASE_SHA` (verificado: `exists False`);
  nenhum `BTC_SHA`, snapshot, censo ou build registrados por esta trilha até aqui.
- Candidato: `https://github.com/bitcoin/bitcoin` (sem ref/SHA escolhidos; nada clonado nesta etapa).
  Instruções oficiais a confrontar no SHA escolhido: `doc/build-unix.md`, `test/README.md`,
  `test/functional/README.md` (links `master` consultáveis, não substituem o PIN).
- Bloqueios separados: (a) contrato — harness/censo/extrator atuais não servem sem adaptador;
  (b) parser — C++ sem extrator (A1/A2); (c) build/ambiente — toolchain e features do snapshot
  ainda não registrados. Diagnóstico de retrieval pode avançar sem build; piloto de patches não.
- Estado: **pendente** (ver `benchmarks/bitcoin/PIN.md` e `CENSO.md`).

## Aceite BTC-P0

- [x] Toda afirmação acima cita implementação + evidência `arquivo:linha@SHA`; nenhuma usa dado SIGA como Bitcoin.
- [x] Nenhum edit no core; nenhum benchmark executado; nenhum SHA de dataset inventado.
- [x] Bloqueios separados em contrato/parser/build; próxima ação = resolver `BTC_SHA` (BTC-P0 restante) e BTC-P1.
- [x] `pytest -q` verde offline na worktree (ver STATUS; sem fixtures Bitcoin ainda — suíte comum intacta).
