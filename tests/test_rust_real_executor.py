# SPDX-License-Identifier: Apache-2.0
"""Testes do executor real (`benchmarks/rust/real_executor.py`).

Sem rede, sem chave, sem provedor: o transporte (`_post_json`) é trocado por
respostas sintéticas em forma de API. O que cada teste guarda:

- caminho feliz reconcilia stream × resultado sem `mismatch` (prova de
  compatibilidade com o runner via `StreamAccounting`+`reconcile`);
- retry conta e depois sucede; falha de auth aborta com motivo;
- echo de modelo divergente marca MISMATCH em vez de forjar identidade;
- tetos de turnos param o loop; sem preços o executor recusa (saída 2);
- matemática de custo exata; nomes reservados jamais emitidos.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "benchmarks/rust"))

import real_executor  # noqa: E402
from executor_contract import StreamAccounting, reconcile, validate_result  # noqa: E402

MODEL = "model-x"
PRICES = {"currency": "USD", "source": "fixture", "date": "2026-10-05",
          "models": {MODEL: {"input": 4.0, "output": 20.0,
                             "cache_read": 0.4, "cache_write": 5.0}}}


def msg(text=None, tools=None, usage=None, model=MODEL, stop="end_turn"):
    content = []
    if text is not None:
        content.append({"type": "text", "text": text})
    for t in tools or []:
        content.append({"type": "tool_use", "id": t["id"], "name": t["name"],
                        "input": t["input"]})
    return {"id": "msg-1", "type": "message", "role": "assistant", "model": model,
            "content": content, "stop_reason": stop,
            "usage": usage or {"input_tokens": 10, "output_tokens": 5}}


def scripted(monkeypatch, script):
    calls = {"n": 0}

    def fake(url, headers, payload, timeout_s):
        assert url.startswith("https://"), url
        assert headers.get("x-api-key") == "k-secreta-sintetica"
        assert payload["model"] == MODEL
        item = script[min(calls["n"], len(script) - 1)]
        calls["n"] += 1
        if isinstance(item, Exception):
            raise item
        return 200, {}, item

    monkeypatch.setattr(real_executor, "_post_json", fake)
    monkeypatch.setattr(real_executor.time, "sleep", lambda s: None)
    return calls


@pytest.fixture
def bench(tmp_path, monkeypatch):
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "app.py").write_text("x = 1\n")
    statement = tmp_path / "statement.md"
    statement.write_text("Some o arquivo app.py com `y = 2`.\n")
    prices = tmp_path / "prices.json"
    prices.write_text(json.dumps(PRICES))
    stream = tmp_path / "stream.jsonl"
    result = tmp_path / "result.json"
    monkeypatch.setenv("ATLAS_EXECUTOR_TELEMETRY", str(stream))
    monkeypatch.setenv("ATLAS_EXECUTOR_RESULT", str(result))
    monkeypatch.setenv("ATLAS_API_KEY", "k-secreta-sintetica")
    base = ["--statement-file", str(statement), "--dir", str(ws),
            "--provider", "anthropic", "--model", MODEL,
            "--prices", str(prices), "--retry-base-s", "0"]
    return {"ws": ws, "stream": stream, "result": result, "base": base}


def read_stream(path):
    return [json.loads(ln) for ln in path.read_text().strip().splitlines()]


def check_reconciled(result, events):
    assert validate_result(result) == []
    acc = StreamAccounting()
    for ev in events:
        acc.absorb(ev)
    assert not acc.violations, acc.violations
    states = {row["metric"]: row["state"]
              for row in reconcile(acc.report(), result)}
    assert "mismatch" not in states.values(), states
    return acc


def test_caminho_feliz_reconcilia(bench, monkeypatch):
    calls = scripted(monkeypatch, [
        msg(tools=[{"id": "t1", "name": "shell",
                    "input": {"command": "echo y=2 >> app.py"}}]),
        msg(text="pronto"),
    ])
    assert real_executor.main(bench["base"]) == 0
    assert calls["n"] == 2
    assert "y=2" in (bench["ws"] / "app.py").read_text()
    events = read_stream(bench["stream"])
    result = json.loads(bench["result"].read_text())
    acc = check_reconciled(result, events)
    assert result["stop"]["reason"] == "done"
    assert result["usage"]["model_calls"] == 2
    assert result["usage"]["tool_calls_declared"] == 1
    assert result["usage"]["turns"] == 2
    assert result["model"] == {"provider": "anthropic", "id": MODEL,
                               "version": MODEL, "verified_by": result["model"]["verified_by"]}
    assert "api-echo" in result["model"]["verified_by"]
    assert acc.report()["model_calls"] == 2


def test_retry_depois_sucesso(bench, monkeypatch):
    err = real_executor.TransportError("HTTP 500", "http_500", True)
    scripted(monkeypatch, [err, err, msg(text="ok")])
    assert real_executor.main(bench["base"]) == 0
    events = read_stream(bench["stream"])
    result = json.loads(bench["result"].read_text())
    check_reconciled(result, events)
    assert result["usage"]["model_calls"] == 3
    assert result["retries"] == {"count": 2}
    assert result["errors"]["count"] == 2
    assert result["stop"]["reason"] == "done"


def test_auth_aborta_com_motivo(bench, monkeypatch):
    err = real_executor.TransportError("HTTP 401", "auth_http_401", False)
    scripted(monkeypatch, [err])
    assert real_executor.main(bench["base"]) == 0
    events = read_stream(bench["stream"])
    result = json.loads(bench["result"].read_text())
    check_reconciled(result, events)
    assert result["stop"]["reason"] == "auth_error"
    assert result["usage"]["model_calls"] == 1
    assert result["usage"]["turns"] == 1


def test_echo_divergente_marca_mismatch(bench, monkeypatch):
    scripted(monkeypatch, [msg(text="ok", model="outro-modelo")])
    assert real_executor.main(bench["base"]) == 0
    result = json.loads(bench["result"].read_text())
    assert validate_result(result) == []
    assert "MISMATCH" in result["model"]["verified_by"]
    assert result["coverage"]["model_identity"]["observed"] is False


def test_teto_de_turnos_para_o_loop(bench, monkeypatch):
    scripted(monkeypatch, [msg(tools=[{"id": "t1", "name": "read",
                                       "input": {"path": "app.py"}}])])
    assert real_executor.main(bench["base"] + ["--max-turns", "1"]) == 0
    events = read_stream(bench["stream"])
    result = json.loads(bench["result"].read_text())
    check_reconciled(result, events)
    assert result["stop"]["reason"] == "turn_ceiling"
    assert result["usage"]["model_calls"] == 1
    assert result["usage"]["turns"] == 1


def test_teto_de_ferramentas_nao_executa_alem(bench, monkeypatch):
    scripted(monkeypatch, [msg(tools=[{"id": "t1", "name": "read",
                                       "input": {"path": "app.py"}}])])
    assert real_executor.main(bench["base"] + ["--max-tool-calls", "0"]) == 0
    events = read_stream(bench["stream"])
    result = json.loads(bench["result"].read_text())
    check_reconciled(result, events)
    assert result["stop"]["reason"] == "tool_ceiling"
    assert result["usage"]["tool_calls_declared"] == 0


def test_sem_precos_do_modelo_recusa(bench, monkeypatch, tmp_path):
    prices = tmp_path / "empty.json"
    prices.write_text(json.dumps({"currency": "USD", "source": "x", "date": "d",
                                  "models": {}}))
    args = [a for a in bench["base"]]
    args[args.index("--prices") + 1] = str(prices)
    assert real_executor.main(args) == 2
    assert not bench["result"].exists()


def test_matematica_de_custo_exata(bench, monkeypatch):
    usage = {"input_tokens": 1000, "output_tokens": 500,
             "cache_read_input_tokens": 2000, "cache_creation_input_tokens": 100}
    scripted(monkeypatch, [msg(text="fim", usage=usage)])
    assert real_executor.main(bench["base"]) == 0
    events = read_stream(bench["stream"])
    result = json.loads(bench["result"].read_text())
    check_reconciled(result, events)
    expected = round(1000 * 4 / 1e6 + 500 * 20 / 1e6
                     + 2000 * 0.4 / 1e6 + 100 * 5 / 1e6, 8)
    assert expected == 0.0153
    calls = [e for e in events if e["kind"] == "model_call"]
    assert calls[0]["cost"] == {"amount": 0.0153, "currency": "USD"}
    assert result["cost"]["provider_billed"] == 0.0153
    assert result["cost"]["currency"] == "USD"
    assert result["usage"]["input_tokens"] == 1000
    assert result["usage"]["cache_read_tokens"] == 2000
    assert result["usage"]["cache_write_tokens"] == 100


def test_nomes_reservados_jamais_emitidos(bench, monkeypatch):
    scripted(monkeypatch, [
        msg(tools=[{"id": "t1", "name": "shell", "input": {"command": "true"}},
                   {"id": "t2", "name": "write",
                    "input": {"path": "novo.txt", "content": "oi"}}]),
        msg(text="fim"),
    ])
    assert real_executor.main(bench["base"]) == 0
    events = read_stream(bench["stream"])
    for ev in events:
        assert ev["source"] == "executor"
        assert ev["kind"] != "opened", ev
        assert ev.get("tool") not in ("atlas", "atlas-read"), ev
    assert (bench["ws"] / "novo.txt").read_text() == "oi"
