# Ambiente de aceitação Bitcoin — TASK-B01

Data: 2026-10-05. Dono: B. Coorte Python (BTC-REAL-01..04): dispensa `bitcoind`
e build C++ por desenho (veredito de build bloqueado registrado em
`research/bitcoin/BUILD_ENV.md` — esta coorte não espera por ele).

## Dependências medidas

- Python 3.12.3 (`/usr/bin/python3`), somente stdlib (`sys`, `json`,
  `decimal`, `subprocess`, `tempfile`, `unittest` indireto). Sem pip, sem venv.
- `git` 2.43.0 (clone `--filter=blob:none` + `fetch <sha>` + checkout de paths).
- Rede usada só para o clone do snapshot público (github.com); nenhum teste
  toca rede de produção: 03 usa conexão fake em-processo; 04 usa subprocessos
  locais com fixtures próprias; nenhuma chamada sai do host.
- Host no preparo: Linux x86_64, ~11 GiB disponíveis (sem reserva exclusiva —
  medições abaixo são tempos de aceite, não benchmark).

## Comandos reais e tempos (referência, execução única)

```bash
git clone --filter=blob:none --no-checkout https://github.com/bitcoin/bitcoin.git <isolado>
git fetch origin 9be056a8a72b624dae9623b2f7bded92c2a21c91
git checkout 9be056a8a72b624dae9623b2f7bded92c2a21c91 -- test/functional/test_framework/ test/functional/test_runner.py
bash atlas-accept/run.sh BTC-REAL-0X   # cwd = checkout no base_sha (ou BTC_WORKSPACE=...)
```

Aceite por tarefa: 01 → 0,04 s; 02 → 0,17 s; 03 → 0,12 s; 04 → 0,76 s
(`timeout_s: 300` em todas, folga >300×).

## Baseline / referência

- Baseline (base limpa no SHA): 01 → 6/9; 02 → 10/16; 03 → 4/10; 04 → 2/5
  (todos exit 1; detalhes em `CURADORIA_SMOKE.md`).
- Referência (custódia fora do git): 9/9, 16/16, 10/10, 5/5 (todos exit 0).
- Validador: `eval.py validate` do core (checkout principal, somente leitura,
  core `48f5037`) → 4 tarefas, 1/1/1/1, 0 problemas. Core não copiado nem
  modificado; validação registrada, sem fork.

## Bloqueios que NÃO atingem esta coorte

Build C++/`test_bitcoin` (BTC-REAL-07, TASK-B02), modelo/teto (EXP01),
curador holdout (P4). Nada desta coorte depende deles.
