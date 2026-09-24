# Índice do corpus real — REPORT (`btc-index-001`)

Pergunta: o pipeline publicado indexa o corpus v31.1 com custo e conteúdo conhecidos?
Método: `store.index_discovered` (publicada, `core_sha`) sobre checkout `--detach BTC_SHA`,
DB em runtime `/tmp` (não commitado). Sem modelo, sem build.

## Medições (reais)

- 1873 arquivos indexados, 0 pulados, **3,6s**, DB **1,45MB**,
  `stable_hash 2a320784…`.
- Símbolos: **4049**, todos `ast-exact` Python (509 classes + 3540 funções).
  C++ (1409) e JS (100): arquivos registrados, **zero símbolos** — A2 em escala,
  explícito, não falha silenciosa.
- Incremental (cópias em tmp, corpus intacto): edição PY 15→16 símbolos, `A≠B`,
  reindex `==` rebuild. Edição C++ é símbolo-vacua (só invalidação de dependentes a cobre).
- Toolchain disponível nesta máquina: cmake 4.4.0, g++ 13.3.0, sem clang++, python 3.12.2,
  16 cores, RAM livre ~2GB → **build não tentado** (1,5GB/TU exigidos; sem reserva isolada).

## Decisão

Índice `manter` como linha de base de medição (não de produto); retrieval real sobre o
corpus segue pendente de tarefas + modelo + teto. Próximo: toolchain dedicada e build
isolado, ou tarefas reais de retrieval sobre este índice.
