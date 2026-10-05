# Curadoria smoke Bitcoin — TASK-B01

Data: 2026-10-05. Dono: B. Base: bitcoin/bitcoin `9be056a8a72b624dae9623b2f7bded92c2a21c91`
(v31.1). Catálogo dev: `benchmarks/rust/tasks/bitcoin.dev.json` (somente leitura,
no checkout principal — não alterado).

## Hashes confirmados no clone (SHA fixado)

| Fonte | sha256 | Confere com catálogo |
|---|---|---|
| `test/functional/test_framework/descriptors.py` | `8c2a4490…4090a16a` | sim |
| `test/functional/test_framework/address.py` | `63e83cdd…58d12bf4f` | sim |
| `test/functional/test_framework/script.py` | `24bdbfc1…12bf3abf` | sim |
| `test/functional/test_framework/authproxy.py` | `736246f2…70916d1a1a` | sim |
| `test/functional/test_runner.py` | `faee6591…18ca529c3` | sim |

Clone isolado fora dos repos (`--filter=blob:none` + checkout do SHA);
framework completo extraído para inspeção; `script.py` é referência auxiliar
da 02 (construtores vêm de `script_util.py`, já importado por `address.py`).

## Vermelho → verde (base vs referência em custódia)

Referências em `/home/iiii/PESSOAL-PROJETOS-ALEXANDRE/siga-a03-custody/reference/BTC-REAL-0{1..4}/`
(fora do git; diffs mínimos, sem ouro no pacote — ver isolamento abaixo).

- **01** (base → 3/9 FAIL): `"#"` → `IndexError`; `"a#short"` → `IndexError`;
  `"☃#aaaaaaaa"` → `TypeError` (`None + list`). Referência: guarda
  `len(s) < 10` + guarda `expanded is None`. Verde 9/9; `require=False` e
  algoritmo intactos.
- **02** (base → 6/16 FAIL): versões 0/5 → `ValueError: Unsupported address
  type`. Referência: ramos v0→`keyhash_to_p2pkh_script`,
  v5→`scripthash_to_p2sh_script`. Verde 16/16 (12 conversões + witness +
  checksum inválido + versão 42); 111/196 intactos.
- **03** (base → 6/10 FAIL): `; charset=utf-8` e variações → `JSONRPCException
  -342`. Referência: compara só o media-type (`split(';')[0].strip().casefold()`).
  Verde 10/10; `text/html` segue rejeitado; erro RPC/204/Decimal intactos.
- **04** (base → 3/5 FAIL): `--jobs=0/-1/--help` sem `config.ini` →
  `FileNotFoundError` sem citar `--jobs`. Referência: valida `--jobs < 1`
  via `parser.error` (exit 2) e atende `--help` (exit 0) antes do acesso a
  `config.ini`. Verde 5/5; jobs positivo segue ao fluxo existente (falha de
  config sem build, como antes). Tradeoff registrado: `--help` antecipado
  imprime só a ajuda do runner (antes imprimia também a do primeiro script,
  mas exigia build configurado — indisponível sem `config.ini`).

## Isolamento além de diretório

- Custódia fora do repo (`git ls-files` não a lista); pacote público sem ouro:
  harnesses comparam contra construtores em tempo de execução e citam só
  `--jobs` (genérico), nunca a mensagem exata da referência; conjunto sem
  campo de curadoria, só hashes de fonte pública.
- `test_command` relativo ao workspace; `atlas-accept/**` em
  `immutable_paths`. Nível declarado: checagem por caminho, insuficiente
  para rodada cega final (mesma ressalva da A03).
- Nenhum teste privado no pacote; casos do avaliador ficam nos harnesses
  públicos acima (padrão desta coorte: critérios comportamentais observáveis).

## Nota de família (para EXP02/EXP03)

`btc-authproxy` (03 smoke × 05 piloto) e `btc-runner` (04 smoke × 08 piloto)
repetem famílias com requisitos disjuntos — mesma regra do SIGA 07/08:
se usadas para ajustar política, excluir do piloto de inferência.
