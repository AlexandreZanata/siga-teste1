# CENSO Bitcoin — BTC-P0 (capacidade auditada; dataset pendente)

Track: `bitcoin`. Etapa: BTC-P0. Dono: agente B. `BASE_SHA`: `e6fde134f7da0d3616d90c40232d9ebe2ed9f033`.
Estado: **dataset pendente de PIN** — nenhuma contagem de arquivos do Bitcoin é afirmada aqui.

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

## 2. Censo do dataset Bitcoin

Pendente de `BTC_SHA` (ver `PIN.md`). Estrutura a preencher após o pin, por listagem real:

- `total_arquivos_por_extensao`: pendente (comando: `discover()` + contagem por sufixo no checkout somente leitura).
- `loc_por_linguagem`: pendente. `modulos_top`: pendente (`src/`, `test/...` confirmados no snapshot).
- `excluidos`: pendente (aplicar `EXCLUDE_DIRS` + regras do snapshot).
- Nenhum corpus copiado para este repositório; publicar scripts/ponteiros/hashes, não blobs.

## 3. Próximo comando (após PIN)

```sh
ARCHATLAS_DATASET=<btc-readonly> python3 -c \
  "from pathlib import Path; from archatlas.dataset import discover; \
   from collections import Counter; items = discover(Path('<btc-readonly>')); \
   print(len(items), Counter(l for _, l in items))"
```

DB/índice dessa listagem (se houver) em `$TMPDIR/archatlas-bitcoin/<run_id>/`, nunca no checkout do dataset.
