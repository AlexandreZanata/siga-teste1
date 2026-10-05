#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Executor real para o runner (`atlas-executor/1`) — loop de agente sobre a API do provedor.

O contrato (`executor_contract.py`), os normalizadores de resposta e o executor `dry`
já existem e estão testados; faltava o executor que **realmente chama um modelo**.
Este módulo é ele: loop fixo (mesmo em todos os braços), ferramentas básicas
(`shell`, `read`, `write`), telemetria evento a evento e resultado reconciliado.

Uso (o runner invoca; nunca à mão na rodada):
    ATLAS_EXECUTOR_TELEMETRY=.../stream.jsonl ATLAS_EXECUTOR_RESULT=.../result.json \\
    ATLAS_API_KEY=... python benchmarks/rust/real_executor.py \\
        --statement-file enunciado.md --dir <workspace> \\
        --provider anthropic --model <id> --prices prices.json

Sem chave, sem preços do modelo, sem enunciado ou sem telemetria/resultado: saída 2,
sem resultado (o runner trata como ausente, nunca como zero). Com eles, saída 0 e
resultado sempre escrito — inclusive em erro de API ou teto (o runner julga).

Só stdlib. Rede real nunca é tocada nos testes: o transporte (`_post_json`) é
injetável e os testes usam respostas sintéticas.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
import uuid
from pathlib import Path

API_URLS = {
    "anthropic": "https://api.anthropic.com/v1/messages",
}
ANTHROPIC_VERSION = "2023-06-01"

# Espelham o pré-registro §1.3 (budget de saída) e §1.4 (tetos operacionais).
DEFAULT_MAX_TOKENS = 2000
DEFAULT_MAX_TURNS = 40
DEFAULT_MAX_TOOL_CALLS = 100
DEFAULT_TIMEOUT_S = 120
DEFAULT_MAX_RETRIES = 3
SHELL_OUTPUT_LIMIT = 65536
SHELL_TIMEOUT_CAP = 600

FIXED_EXECUTOR_TOOLS = ("shell", "read", "write")

TOOLS_SPEC = [
    {"name": "shell",
     "description": ("Executa um comando shell no diretório do workspace e devolve "
                     "a saída combinada (stdout+stderr) e o exit code. Sem rede, "
                     "sem sudo, sem sair do workspace."),
     "input_schema": {"type": "object",
                      "properties": {"command": {"type": "string"},
                                     "timeout_s": {"type": "number"}},
                      "required": ["command"]}},
    {"name": "read",
     "description": "Lê um arquivo do workspace (caminho relativo) e devolve o texto.",
     "input_schema": {"type": "object",
                      "properties": {"path": {"type": "string"}},
                      "required": ["path"]}},
    {"name": "write",
     "description": ("Escreve (cria ou substitui por inteiro) um arquivo do workspace. "
                     "O diretório pai precisa existir; sem `..` nem caminho absoluto."),
     "input_schema": {"type": "object",
                      "properties": {"path": {"type": "string"},
                                     "content": {"type": "string"}},
                      "required": ["path", "content"]}},
]

SYSTEM_PROMPT = """Você é um engenheiro de software editando o workspace atual para cumprir o \
enunciado abaixo. Ferramentas disponíveis: shell (comandos no workspace), read (ler \
arquivo) e write (escrever arquivo por inteiro). Regras: só edite arquivos dentro do \
workspace; confira o trabalho rodando comandos relevantes via shell; quando terminar, \
responda com um resumo final em texto e SEM chamar ferramentas. Nunca exponha chaves \
ou segredos; não há rede além das suas ferramentas.
Enunciado:
"""


class TransportError(Exception):
    def __init__(self, message: str, error_class: str, retryable: bool):
        super().__init__(message)
        self.error_class = error_class
        self.retryable = retryable


def _post_json(url: str, headers: dict, payload: dict, timeout_s: float):
    """Transporte HTTP real. Injetável nos testes (monkeypatch)."""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            return resp.status, dict(resp.headers), json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode() or "{}")
        except Exception:  # noqa: BLE001
            body = {}
        err_type = ((body.get("error") or {}).get("type")) or f"http_{e.code}"
        retryable = e.code == 429 or 500 <= e.code < 600
        if e.code in (401, 403):
            err_type, retryable = "auth_" + err_type, False
        elif e.code == 400:
            retryable = False
        raise TransportError(f"HTTP {e.code}: {err_type}", err_type, retryable)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise TransportError(f"rede: {e}", "rede", True)


def _anthropic_headers(api_key: str) -> dict:
    return {"Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION}


def _usage_of(body: dict) -> dict:
    usage = body.get("usage") or {}
    return {"input": usage.get("input_tokens"),
            "output": usage.get("output_tokens"),
            "cache_read": usage.get("cache_read_input_tokens"),
            "cache_write": usage.get("cache_creation_input_tokens"),
            "reasoning": None}


def _split_content(body: dict):
    texts, calls = [], []
    for block in body.get("content") or []:
        if block.get("type") == "text":
            texts.append(block.get("text") or "")
        elif block.get("type") == "tool_use":
            calls.append({"id": block.get("id"), "name": block.get("name"),
                          "input": block.get("input") or {}})
    return "".join(texts), calls


class Accumulator:
    """Contadores únicos que alimentam stream E resultado (reconciliação por construção)."""

    def __init__(self) -> None:
        self.model_calls = 0
        self.tokens = {"input": 0, "output": 0, "cache_read": 0,
                       "cache_write": 0, "reasoning": 0}
        self.tokens_seen: set[str] = set()
        self.cost = 0.0
        self.cost_currency: str | None = None
        self.tool_calls = 0
        self.turns = 0
        self.errors = 0
        self.error_classes: dict[str, int] = {}
        self.retries = 0
        self.stop_reason: str | None = None

    def add_call(self, usage: dict, cost: float | None, currency: str | None,
                 ok: bool, error_class: str | None = None) -> None:
        self.model_calls += 1
        if not ok:
            self.errors += 1
            self.error_classes[error_class or "sem_classe"] = \
                self.error_classes.get(error_class or "sem_classe", 0) + 1
        for field in ("input", "output", "cache_read", "cache_write", "reasoning"):
            value = usage.get(field)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                self.tokens[field] += value
                self.tokens_seen.add(field)
        if cost is not None:
            self.cost = round(self.cost + cost, 8)
            self.cost_currency = self.cost_currency or currency


class Executor:
    def __init__(self, args, stream_path: Path, result_path: Path,
                 statement: str, prices: dict, api_key: str) -> None:
        self.args = args
        self.workspace = Path(args.dir).resolve()
        self.stream = stream_path
        self.result_path = result_path
        self.statement = statement
        self.prices = prices
        self.api_key = api_key
        self.acc = Accumulator()
        self.messages: list[dict] = []

    def emit(self, event: dict) -> None:
        event = {"source": "executor", **event}
        with open(self.stream, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")

    def call_prices(self, usage: dict) -> tuple[float | None, str | None]:
        table = (self.prices.get("models") or {}).get(self.args.model)
        if not isinstance(table, dict):
            return None, None
        total = 0.0
        for field, per_m in (("input", "input"), ("output", "output"),
                             ("cache_read", "cache_read"), ("cache_write", "cache_write")):
            value = usage.get(field)
            price = table.get(per_m)
            if isinstance(value, (int, float)) and isinstance(price, (int, float)):
                total += value * price / 1_000_000
            elif isinstance(value, (int, float)):
                return None, None
        return round(total, 8), self.prices.get("currency")

    def request(self, request_id: str):
        payload = {"model": self.args.model, "max_tokens": self.args.max_tokens,
                   "system": SYSTEM_PROMPT + self.statement,
                   "messages": self.messages, "tools": TOOLS_SPEC}
        if self.args.provider != "anthropic":
            raise TransportError(f"provedor sem transporte: {self.args.provider}",
                                 "provedor_desconhecido", False)
        started = time.monotonic()
        try:
            status, headers, body = _post_json(
                self.args.api_url or API_URLS["anthropic"],
                _anthropic_headers(self.api_key), payload, self.args.timeout_s)
        except TransportError:
            raise
        latency_ms = round((time.monotonic() - started) * 1000, 1)
        return body, latency_ms

    def run_tool(self, name: str, tool_input: dict) -> tuple[str, int]:
        """Executa uma ferramenta fixa. Devolve (saída, exit_code)."""
        if name == "shell":
            command = str(tool_input.get("command") or "")
            timeout = tool_input.get("timeout_s") or 120
            try:
                timeout = min(float(timeout), SHELL_TIMEOUT_CAP)
            except (TypeError, ValueError):
                timeout = 120
            try:
                proc = subprocess.run(["bash", "-c", command], cwd=str(self.workspace),
                                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                      timeout=timeout)
                out = proc.stdout.decode("utf-8", errors="replace")
                code = proc.returncode
            except subprocess.TimeoutExpired as e:
                out = (e.stdout or b"").decode("utf-8", errors="replace")
                code = 124
            truncated = len(out) > SHELL_OUTPUT_LIMIT
            if truncated:
                out = out[:SHELL_OUTPUT_LIMIT] + "\n[saída truncada em 64 KiB]"
            return out, code
        if name in ("read", "write"):
            rel = str(tool_input.get("path") or "")
            target = (self.workspace / rel)
            try:
                resolved = target.resolve()
            except OSError:
                return "caminho inválido", 2
            if Path(rel).is_absolute() or ".." in Path(rel).parts \
                    or not str(resolved).startswith(str(self.workspace) + os.sep):
                return "fora do workspace", 2
            if name == "read":
                try:
                    return resolved.read_text(encoding="utf-8", errors="replace"), 0
                except OSError as e:
                    return f"leitura falhou: {e}", 2
            if not resolved.parent.is_dir():
                return "diretório pai inexistente", 2
            try:
                content = str(tool_input.get("content") or "")
                resolved.write_text(content, encoding="utf-8")
                return f"escrito {len(content.encode())} bytes", 0
            except OSError as e:
                return f"escrita falhou: {e}", 2
        return f"ferramenta desconhecida: {name}", 2

    def attempt(self, turn_index: int) -> dict:
        """Uma chamada de modelo com retry; devolve o corpo ou levanta TransportError final.

        Cada tentativa HTTP tem `request_id` próprio: são chamadas distintas do
        provedor, e o contrato deduz reemissão do mesmo id (anti-cobrança dupla).
        """
        retries = 0
        while True:
            request_id = f"req-{uuid.uuid4().hex[:12]}"
            started = time.monotonic()
            try:
                body, latency_ms = self.request(request_id)
            except TransportError as e:
                latency_ms = round((time.monotonic() - started) * 1000, 1)
                self.emit({"kind": "model_call", "provider": self.args.provider,
                           "model_id": self.args.model, "request_id": request_id,
                           "status": "error", "error_class": e.error_class,
                           "tokens": {}, "latency_ms": latency_ms,
                           "cost": {"amount": 0.0,
                                    "currency": self.prices.get("currency")}})
                self.acc.add_call({}, 0.0, self.prices.get("currency"),
                                  ok=False, error_class=e.error_class)
                if e.retryable and retries < self.args.max_retries:
                    retries += 1
                    self.acc.retries += 1
                    self.emit({"kind": "retry", "of_request_id": request_id,
                               "error_class": e.error_class})
                    time.sleep(min(2.0 ** retries, 30.0) * self.args.retry_base_s / 2.0)
                    continue
                raise
            return {"body": body, "latency_ms": latency_ms, "request_id": request_id}

    def run(self) -> int:
        self._last_echo = None
        while self.acc.turns < self.args.max_turns:
            self.acc.turns += 1
            self.emit({"kind": "turn", "index": self.acc.turns})
            try:
                got = self.attempt(self.acc.turns)
            except TransportError as e:
                self.acc.stop_reason = ("auth_error" if e.error_class.startswith("auth")
                                        else "api_error")
                break
            body, latency_ms, request_id = got["body"], got["latency_ms"], got["request_id"]
            usage = _usage_of(body)
            cost, currency = self.call_prices(usage)
            if cost is None:
                self.emit({"kind": "error", "error_class": "preco_ausente"})
                self.acc.errors += 1
                self.acc.error_classes["preco_ausente"] = \
                    self.acc.error_classes.get("preco_ausente", 0) + 1
                self.acc.stop_reason = "prices_missing"
                self.acc.add_call(usage, None, None, ok=True)
                self.emit({"kind": "model_call", "provider": self.args.provider,
                           "model_id": self.args.model, "request_id": request_id,
                           "status": "ok", "tokens": usage, "latency_ms": latency_ms})
                break
            self.acc.add_call(usage, cost, currency, ok=True)
            self.emit({"kind": "model_call", "provider": self.args.provider,
                       "model_id": self.args.model, "request_id": request_id,
                       "status": "ok", "tokens": usage, "latency_ms": latency_ms,
                       "stop_reason": body.get("stop_reason"),
                       "cost": {"amount": cost, "currency": currency}})
            echo = body.get("model")
            self.messages.append({"role": "assistant", "content": body.get("content") or []})
            self._last_echo = body.get("model")
            text, calls = _split_content(body)
            if not calls:
                self.acc.stop_reason = "done"
                break
            if self.acc.tool_calls + len(calls) > self.args.max_tool_calls:
                self.acc.stop_reason = "tool_ceiling"
                break
            results = []
            for call in calls:
                out, code = self.run_tool(call["name"], call["input"])
                self.acc.tool_calls += 1
                self.emit({"kind": "tool_call", "tool": call["name"],
                           "argv": [json.dumps(call["input"], ensure_ascii=False)[:2000]],
                           "exit_code": code, "stdout_bytes": len(out.encode())})
                results.append({"type": "tool_result", "tool_use_id": call["id"],
                                "content": out})
            self.messages.append({"role": "user", "content": results})
        else:
            self.acc.stop_reason = "turn_ceiling"
        echo = getattr(self, "_last_echo", None)
        self.write_result(echo)
        self.emit({"kind": "stop", "reason": self.acc.stop_reason})
        return 0

    def write_result(self, echo) -> None:
        acc = self.acc
        tokens = {f: (acc.tokens[f] if f in acc.tokens_seen else None)
                  for f in ("input", "output", "cache_read", "cache_write", "reasoning")}
        requested = self.args.model
        version = self.args.model_version or echo or requested
        if echo is None:
            verified_by = ("sem echo de modelo na resposta; identidade não verificada; "
                           "versão assume o id requisitado")
            identity_ok = False
        elif echo != requested:
            verified_by = (f"MISMATCH: requisitado {requested!r} mas a API respondeu "
                           f"{echo!r}; identidade não verificada")
            identity_ok = False
        else:
            verified_by = (f"api-echo: response.model={echo!r} == id requisitado; "
                           f"versão de pesos não exposta pela API")
            identity_ok = True
        doc = {
            "schema": "atlas-executor-result/1",
            "model": {"provider": self.args.provider, "id": requested,
                      "version": version, "verified_by": verified_by},
            "usage": {"model_calls": acc.model_calls or None,
                      "input_tokens": tokens["input"], "output_tokens": tokens["output"],
                      "cache_read_tokens": tokens["cache_read"],
                      "cache_write_tokens": tokens["cache_write"],
                      "tool_calls_declared": acc.tool_calls,
                      "turns": acc.turns},
            "errors": {"count": acc.errors, "classes": acc.error_classes},
            "retries": {"count": acc.retries},
            "stop": {"reason": acc.stop_reason},
            "cost": ({"provider_billed": acc.cost, "currency": acc.cost_currency,
                      "source": self.prices.get("source")}
                     if acc.cost_currency else None),
            "coverage": {
                "model_identity": {"observed": identity_ok, "source": "executor-stream",
                                   "reason": None if identity_ok else
                                   "echo do modelo diverge do requisitado"},
                "tokens": {"observed": bool(acc.tokens_seen), "source": "executor-stream",
                           "reason": None if acc.tokens_seen else "nenhuma chamada com uso"},
                "cost": {"observed": acc.cost_currency is not None,
                         "source": "executor-stream",
                         "reason": ("estimativa por tabela publicada; fatura reconcilia "
                                    "fora de banda (P2)")},
                "tool_calls": {"observed": True, "source": "executor-stream",
                               "reason": None},
                "turns": {"observed": True, "source": "executor-stream", "reason": None},
            },
        }
        with open(self.result_path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=1)
            fh.write("\n")


def load_prices(path: Path, model: str) -> dict:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise SystemExit(f"preços ilegíveis ({path}): {e}")
    for field in ("currency", "source", "models"):
        if not doc.get(field):
            raise SystemExit(f"preços sem {field!r} ({path})")
    table = (doc.get("models") or {}).get(model)
    if not isinstance(table, dict) or not all(
            isinstance(table.get(f), (int, float)) for f in
            ("input", "output", "cache_read", "cache_write")):
        raise SystemExit(f"preços sem tabela por-1M para o modelo {model!r} ({path})")
    return doc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--statement-file", required=True)
    ap.add_argument("--dir", required=True, help="workspace da tentativa")
    ap.add_argument("--provider", default="anthropic")
    ap.add_argument("--model", required=True)
    ap.add_argument("--model-version", default=None)
    ap.add_argument("--api-key-env", default="ATLAS_API_KEY")
    ap.add_argument("--api-url", default=None)
    ap.add_argument("--prices", required=True, help="tabela de preços por-1M (JSON)")
    ap.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    ap.add_argument("--max-turns", type=int, default=DEFAULT_MAX_TURNS)
    ap.add_argument("--max-tool-calls", type=int, default=DEFAULT_MAX_TOOL_CALLS)
    ap.add_argument("--timeout-s", type=float, default=DEFAULT_TIMEOUT_S)
    ap.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES)
    ap.add_argument("--retry-base-s", type=float, default=2.0)
    args = ap.parse_args(argv)

    stream_path = os.environ.get("ATLAS_EXECUTOR_TELEMETRY")
    result_path = os.environ.get("ATLAS_EXECUTOR_RESULT")
    if not stream_path or not result_path:
        print("ATLAS_EXECUTOR_TELEMETRY/ATLAS_EXECUTOR_RESULT ausentes", file=sys.stderr)
        return 2
    try:
        statement = Path(args.statement_file).read_text(encoding="utf-8")
    except OSError as e:
        print(f"enunciado ilegível: {e}", file=sys.stderr)
        return 2
    if not statement.strip():
        print("enunciado vazio", file=sys.stderr)
        return 2
    if not Path(args.dir).is_dir():
        print(f"workspace ausente: {args.dir}", file=sys.stderr)
        return 2
    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        print(f"chave ausente ({args.api_key_env})", file=sys.stderr)
        return 2
    try:
        prices = load_prices(Path(args.prices), args.model)
    except SystemExit as e:
        print(e, file=sys.stderr)
        return 2

    ex = Executor(args, Path(stream_path), Path(result_path), statement, prices, api_key)
    return ex.run()


if __name__ == "__main__":
    raise SystemExit(main())
