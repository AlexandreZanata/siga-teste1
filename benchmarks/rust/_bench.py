# SPDX-License-Identifier: Apache-2.0
"""Primitivas de medição externa de processos — protocolo §7.

Três decisões que valem registrar, porque cada uma foi escolha contra uma alternativa
mais fácil e pior:

1. **Mede o comando externo inteiro**, do spawn até consumir stdout. Chamar a função
   interna mediria a função, não o que o agente paga: o custo de inicializar o
   interpretador Python ou de abrir o processo Rust ficaria fora da conta.
2. **`/usr/bin/time -f` com linha marcada**, e não `%e` sozinho. Uma linha por execução
   com wall, CPU de usuário e sistema, pico de RSS, faltas de página e blocos de I/O.
3. **stdout é consumido por inteiro** antes de considerar a execução terminada. Um consumidor
   que mede enquanto o produtor ainda escreve mede a velocidade do pipe, não do comando.

`resource.getrusage(RUSAGE_CHILDREN)` foi evitado de propósito: ele devolve um pico
histórico entre todos os filhos já executados, não o pico do filho atual.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

# Campos de uma linha de medição. `?` do GNU time (quando o SO não suporta %I/%O) vira None.
TIME_FMT = "ATLASBENCH\t%e\t%U\t%S\t%M\t%R\t%F\t%I\t%O\t%x"
MARKER = "ATLASBENCH\t"


class TimeUnavailable(RuntimeError):
    """`/usr/bin/time` ausente ou sem suporte a formato: sem ele não há medição confiável."""


def find_time_bin() -> str:
    for cand in ("/usr/bin/time", "/bin/time"):
        if Path(cand).exists():
            return cand
    found = shutil.which("time")
    if found:
        return found
    raise TimeUnavailable(
        "/usr/bin/time (GNU time) nao encontrado; instale o pacote `time` ou declare "
        "a medicao como nao realizada"
    )


def _num(raw: str) -> float | None:
    raw = raw.strip()
    if raw in ("?", "", "N/A"):
        return None
    return float(raw)


def run_measured(argv: list[str], env: dict | None = None, cwd: str | None = None) -> dict:
    """Executa `argv` sob GNU time e devolve uma linha de medição.

    Nunca levanta por saída não-zero: um comando que falha também é um dado, e o código de
    saída entra no registro em vez de virar exceção.
    """
    time_bin = find_time_bin()
    full_env = dict(os.environ)
    if env:
        full_env.update(env)

    started = time.perf_counter()
    proc = subprocess.run(
        [time_bin, "-f", TIME_FMT, *argv],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=full_env,
        cwd=cwd,
    )
    wall_observed = time.perf_counter() - started

    stdout = proc.stdout
    stderr = proc.stderr.decode("utf-8", errors="replace")

    metrics = None
    leftover = []
    for line in stderr.splitlines():
        if line.startswith(MARKER):
            parts = line[len(MARKER):].split("\t")
            # %e %U %S %M %R %F %I %O %x
            while len(parts) < 9:
                parts.append("?")
            metrics = {
                "wall_s": _num(parts[0]),
                "user_s": _num(parts[1]),
                "sys_s": _num(parts[2]),
                "max_rss_kb": _num(parts[3]),
                "minor_faults": _num(parts[4]),
                "major_faults": _num(parts[5]),
                "fs_in_blocks": _num(parts[6]),
                "fs_out_blocks": _num(parts[7]),
                "exit_status": _num(parts[8]),
            }
        elif line.strip():
            leftover.append(line)

    if metrics is None:
        raise TimeUnavailable(
            f"GNU time nao emitiu a linha de medicao; stderr={stderr[-400:]!r}"
        )

    metrics["stdout_bytes"] = len(stdout)
    metrics["stderr_tail"] = "\n".join(leftover)[-400:]
    metrics["wall_observed_s"] = round(wall_observed, 6)
    return {"metrics": metrics, "stdout": stdout}


def quantiles(values: list[float | int | None], q: float) -> float | None:
    """Quantil por posto mais próximo em amostra ordenada.

    Convenção publicada, porque a alternativa (interpolação) daria números ligeiramente
    diferentes e o relatório precisa ser reproduzível por terceiros:
      posicao = ceil(q * n), 1-based, limitada a [1, n];  p50 = mediana
      (média dos dois centrais quando n é par).
    """
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return None
    n = len(vals)
    if q == 0.5 and n % 2 == 0:
        return (vals[n // 2 - 1] + vals[n // 2]) / 2
    import math

    idx = min(n, max(1, math.ceil(q * n)))
    return float(vals[idx - 1])


def summarize(rows: list[dict], key: str) -> dict:
    """Resumo de um campo numérico: n, mín, p50, p95, máx, média."""
    vals = [r.get(key) for r in rows]
    nums = [v for v in vals if v is not None]
    if not nums:
        return {"n": 0}
    return {
        "n": len(nums),
        "min": min(nums),
        "p50": quantiles(nums, 0.5),
        "p95": quantiles(nums, 0.95),
        "max": max(nums),
        "mean": round(sum(nums) / len(nums), 6),
    }


def environment_manifest() -> dict:
    """Ambiente da medição. Sem isto, nenhum número do relatório é interpretável."""
    def sh(*cmd: str) -> str | None:
        try:
            out = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            return out.stdout.decode().strip() or None
        except OSError:
            return None

    mem = {}
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            k, _, v = line.partition(":")
            if k in ("MemTotal", "MemAvailable"):
                mem[k] = v.strip()
    except OSError:
        pass

    return {
        "os": platform.platform(),
        "kernel": platform.release(),
        "machine": platform.machine(),
        "cpu_model": sh("sh", "-c", "grep -m1 'model name' /proc/cpuinfo | cut -d: -f2-").strip()
        if sh("sh", "-c", "grep -m1 'model name' /proc/cpuinfo | cut -d: -f2-")
        else None,
        "nproc": os.cpu_count(),
        "meminfo": mem,
        "rustc": sh("rustc", "--version"),
        "cargo": sh("cargo", "--version"),
        "python": sys.version.split()[0],
        "gnu_time": sh(find_time_bin(), "--version"),
        "git_head": sh("git", "rev-parse", "HEAD"),
        "git_head_short": sh("git", "rev-parse", "--short", "HEAD"),
        "git_dirty": bool(sh("git", "status", "--porcelain")),
    }


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=1, ensure_ascii=False, sort_keys=False) + "\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    out = []
    with Path(path).open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out
