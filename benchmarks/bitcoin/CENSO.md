# CENSO Bitcoin — BTC-P0 (capacidade auditada) + contagens reais do corpus v31.1

Track: `bitcoin`. Dono: agente B. `BASE_SHA`: `e6fde134f7da0d3616d90c40232d9ebe2ed9f033`.
`BTC_SHA`: `9be056a8a72b624dae9623b2f7bded92c2a21c91` (`v31.1`; ver `PIN.md`).
Contagens por listagem real (`git ls-tree -r --name-only v31.1`, 2026-09-24). Sem blobs lidos:
LOC e bytes por linguagem pendentes de checkout com working tree.

## 1. Matriz de capacidade do core atual (observada, não herdada como suporte)

| Linguagem | Descoberta (`dataset.discover`) | Extração (`extract_any`) | Índice | Verificação |
|---|---|---|---|---|
| Java | `.java` | regex Java (`extract.py:8-9,22-31@e6fde13`) | `index_file`/`index_any` | `verify.py:8-20@e6fde13` |
| Python | `.py` | AST (`dataset.py:23-42@e6fde13`) | `index_any` | `verify.py` (nome-na-linha) |
| JSP/Tag | `.jsp/.tag` | `jsp.extract_jsp` | `index_any` | `verify.py` |
| C++ (`.c/.h/.hpp/.cpp`) | mapeado `cpp` (`dataset.py:8-9@e6fde13`) | **`[]`** (`dataset.py:54@e6fde13`; reproduzido: `extract_any(...,'cpp') == []`) | registra arquivo, zero símbolos | n/a (sem símbolos) |
| JS/TS | mapeado `js` | **`[]`** (mesma cláusula) | idem | n/a |

Exclusões de descoberta: `.git,.venv,venv,.tox,node_modules,__pycache__,target,build`
(`dataset.py:12@e6fde13`).

## 2. Censo do dataset Bitcoin (`v31.1`, 2923 paths tracked)

Por extensão (top): `.cpp` 741, `.h` 643, `.py` 364, `.md` 236, `.ts` 100, `.json` 99,
`.png` 92, `.cc` 89, `.sh` 52, `.cmake` 51, `.c` 25 (completo na evidência do commit).
Relevantes ao adaptador: C++ (`.cpp/.h/.cc/.c`) = **1498**; Python = **364**; TS/Qt-locale
fora de cobertura declarada. Por diretório: `src/` 2003 (`src/rpc/` 28, `src/wallet/` 86,
`src/test/` 334), `test/` 414 (`test/functional/` 378), `doc/` 180, `contrib/` 118.
Exclusões a aplicar na indexação: `EXCLUDE_DIRS` publicadas + `depends/`, `src/secp256k1/`
(submódulo/library externa) e locale/recursos `src/qt/` conforme desenho da rodada.
`loc_por_linguagem`: pendente (exige blobs). Nenhum corpus copiado para este repositório.

## 3. Próximo comando (checkout com working tree + toolchain)

```sh
git clone --no-checkout https://github.com/bitcoin/bitcoin <btc-readonly>
git -C <btc-readonly> checkout --detach 9be056a8a72b624dae9623b2f7bded92c2a21c91
ARCHATLAS_DATASET=<btc-readonly> python3 -c \
  "from pathlib import Path; from archatlas.dataset import discover; \
   from collections import Counter; items = discover(Path('<btc-readonly>')); \
   print(len(items), Counter(l for _, l in items))"
```

DB/índice dessa listagem (se houver) em `$TMPDIR/archatlas-bitcoin/<run_id>/`, nunca no checkout do dataset.
