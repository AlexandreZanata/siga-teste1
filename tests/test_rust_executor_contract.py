# SPDX-License-Identifier: Apache-2.0
"""Testes do contrato do executor (`atlas-executor/1`) e da contabilidade que ele alimenta.

O que estes testes guardam, e por que cada um existe:

- **Ausência não é zero.** Campo que nenhum evento informou sai `null`, nunca 0; `coverage`
  sem motivo escrito é violação. Se alguém reintroduzir "sem dado = 0", o teste cai.
- **Declarado não se mistura com observado.** Chamadas de shell declaradas pelo executor entram
  no teto e no total de ferramentas, mas bytes entregues continuam vindo só do shim, em campo
  separado. Antes disso, uma tentativa podia fazer 400 chamadas de shell sem que o teto de
  chamadas de ferramenta visse uma única.
- **Evento reservado não se forja.** `opened` e os nomes `atlas`/`atlas-read` só valem com
  `source: "shim"`; vindos do executor são violação e não contam como leitura. Sem isso, o
  único número de leitura do piloto seria auto-relato.
- **Identidade de modelo é verificável ou a tentativa não é evidência.** `provider` + `id` +
  `version` + `verified_by`; nome informal não substitui, e stream divergindo do result é
  violação, não empate.
- **Ausência de cobertura bloqueia a afirmação.** O manifesto de capacidade diz o que a
  tentativa *pode* afirmar — nunca que houve "redução de leituras" ou "custo" sem cobertura.

Os scripts de executor aqui não chamam modelo, rede nem provedor: são fixtures de contrato. O
adaptador é exercitado com respostas sintéticas em `tests/fixtures/rust/executor/`.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNNER = REPO_ROOT / "benchmarks/rust/runner.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures/rust/executor"
sys.path.insert(0, str(REPO_ROOT / "benchmarks/rust"))

from executor_contract import (  # noqa: E402
    COVERAGE_METRICS,
    StreamAccounting,
    capability_manifest,
    coverage_report,
    normalize_anthropic_message,
    normalize_openai_chat_completion,
    reconcile,
    reconcile_violations,
    validate_result,
)

EMIT = '''
def emit(event):
    with open(stream, "a") as fh:
        print(json.dumps(event), file=fh)
'''


def valid_result(**overrides) -> dict:
    doc = {
        "schema": "atlas-executor-result/1",
        "model": {"provider": "provedor-ficticio", "id": "modelo-ficticio-a",
                  "version": "2026-09-01", "verified_by": "fixture:synthetic"},
        "tokenizer": {"id": "tokenizer-ficticio", "is_exact": False},
        "usage": {"model_calls": 1, "input_tokens": 10, "output_tokens": 5,
                  "cache_read_tokens": 0, "cache_write_tokens": 0,
                  "tool_calls_declared": 0, "turns": 1},
        "errors": {"count": 0, "classes": {}},
        "retries": {"count": 0},
        "stop": {"reason": "ok"},
        "cost": {"provider_billed": 0.0, "currency": "USD", "source": "fixture"},
        "coverage": {m: {"observed": True, "source": "fixture"} for m in COVERAGE_METRICS},
    }
    doc.update(overrides)
    return doc


# --------------------------------------------------------------------------- agregacao


def test_stream_conta_chamadas_tokens_custo_latencia_erro_e_retry():
    agg = StreamAccounting()
    agg.absorb({"kind": "model_call", "source": "executor", "request_id": "r1", "status": "ok",
                "tokens": {"input": 100, "output": 20}, "latency_ms": 250,
                "cost": {"amount": 0.02, "currency": "USD"}})
    agg.absorb({"kind": "model_call", "source": "executor", "request_id": "r2",
                "status": "error", "error_class": "timeout", "tokens": {"input": 5},
                "latency_ms": 900})
    agg.absorb({"kind": "retry", "source": "executor", "of_request_id": "r2"})
    agg.absorb({"kind": "tool_call", "source": "executor", "tool": "shell", "stdout_bytes": 42})
    agg.absorb({"kind": "turn", "source": "executor"})
    report = agg.report()
    assert report["model_calls"] == 2
    assert report["calls_ok"] == 1 and report["calls_error"] == 1
    assert report["tokens"]["input"] == 105
    assert report["tokens"]["cache_read"] is None, "campo nunca informado nao vira zero"
    assert report["tokens"]["reasoning"] is None
    assert report["latency_ms"] == {"total": 1150.0, "max": 900.0, "n": 2}
    assert report["cost"]["amount"] == 0.02
    assert report["cost"]["calls_with_cost"] == 1 and report["cost"]["calls_without_cost"] == 1
    assert report["errors"] == {"count": 1, "classes": {"timeout": 1}}
    assert report["retries"] == 1
    assert report["tool_calls_declared"] == 1
    assert report["tool_calls_by_tool"] == {"shell": 1}
    assert report["declared_delivered_bytes"] == 42
    assert report["turns"] == 1
    assert report["violations"] == []


def test_request_id_repetido_nao_cobra_duas_vezes():
    agg = StreamAccounting()
    event = {"kind": "model_call", "source": "executor", "request_id": "r1", "status": "ok",
             "tokens": {"input": 100, "output": 20}, "cost": {"amount": 0.02, "currency": "USD"}}
    agg.absorb(event)
    agg.absorb(dict(event))
    report = agg.report()
    assert report["model_calls"] == 1, "mesma chamada reemitida nao e duas chamadas"
    assert report["duplicate_request_ids"] == 1
    assert report["tokens"]["input"] == 100
    assert report["cost"]["amount"] == 0.02, "cobranca duplicada e o que o aceite proibe"


def test_evento_reservado_do_executor_e_violacao_e_nao_vira_leitura():
    agg = StreamAccounting()
    agg.absorb({"kind": "opened", "source": "executor", "file": "app.py", "from": 1, "to": 2})
    agg.absorb({"kind": "tool_call", "source": "executor", "tool": "atlas", "argv": ["context"]})
    report = agg.report()
    assert any("reserved_kind" in v for v in report["violations"])
    assert any("impersonated_tool" in v for v in report["violations"])
    # Nenhum evento valido foi absorvido: sem stream, nao existe "zero declarado".
    assert report["tool_calls_declared"] is None
    assert report["tool_calls_by_tool"] == {}


def test_evento_sem_source_nao_conta_como_leitura_e_e_sinalizado():
    agg = StreamAccounting()
    agg.absorb({"kind": "opened", "file": "app.py"})
    agg.absorb({"kind": "turn"})
    report = agg.report()
    assert any("unattributed_reserved_kind" in v for v in report["violations"])
    assert report["unattributed_events"] == 1
    assert report["turns"] == 1, "evento sem origem ainda conta no teto (conservador)"


# --------------------------------------------------------------------------- validacao


def test_validate_result_aceita_valido_e_recusa_identidade_incompleta():
    assert validate_result(valid_result()) == []

    fields = valid_result()
    fields["model"] = {"provider": "provedor-ficticio", "id": "modelo-ficticio-a"}
    violations = validate_result(fields)
    assert any(v.startswith("model_identity_incompleta:version") for v in violations)
    assert "model_identity_sem_verified_by" in violations

    informal = valid_result()
    informal["model"]["version"] = ""
    assert any("model_identity_incompleta" in v for v in validate_result(informal))

    coverage = valid_result()
    coverage["coverage"]["cost"] = {"observed": False}
    assert "coverage_sem_motivo:cost" in validate_result(coverage)

    missing_metric = valid_result()
    del missing_metric["coverage"]["turns"]
    assert "coverage_ausente:turns" in validate_result(missing_metric)

    no_source = valid_result()
    no_source["cost"]["source"] = ""
    assert "cost_sem_source" in validate_result(no_source)

    wrong_schema = valid_result()
    wrong_schema["schema"] = "atlas-executor-result/0"
    assert any(v.startswith("result_schema_inesperado") for v in validate_result(wrong_schema))

    no_stop = valid_result()
    no_stop["stop"] = {}
    assert "stop_sem_reason" in validate_result(no_stop)


def test_reconciliacao_separa_divergencia_de_falta():
    agg = StreamAccounting()
    agg.absorb({"kind": "model_call", "source": "executor", "request_id": "r1", "status": "ok",
                "tokens": {"input": 10, "output": 5}})
    agg.absorb({"kind": "turn", "source": "executor"})
    stream = agg.report()

    rows = {r["metric"]: r for r in reconcile(stream, valid_result())}
    assert rows["input_tokens"]["state"] == "match"
    assert rows["turns"]["state"] == "match"
    # `cache_write_tokens`: o result declarou 0 e o stream nao informou nada. A falta fica
    # registrada como falta (`missing_stream`), nunca resolvida para 0 nem para "igual".
    assert rows["cache_write_tokens"]["state"] == "missing_stream"
    assert rows["cache_write_tokens"]["stream"] is None
    assert rows["cache_write_tokens"]["result"] == 0

    divergent = valid_result()
    divergent["usage"]["model_calls"] = 7
    rows = reconcile(stream, divergent)
    violations = reconcile_violations(rows)
    assert any(v.startswith("reconciliacao_divergente:model_calls") for v in violations)

    semantic = valid_result(usage=None)
    rows = {r["metric"]: r for r in reconcile(stream, semantic)}
    assert rows["model_calls"]["state"] == "missing_result"

    assert all(r["state"] == "missing" for r in reconcile(StreamAccounting().report(), None))


def test_manifesto_de_capacidade_bloqueia_afirmacao_sem_cobertura():
    empty_stream = StreamAccounting().report()
    coverage = coverage_report(None, empty_stream, [])
    capability = capability_manifest(
        "run-1", "BASE", "unverified", "missing", coverage, empty_stream,
        {"provider_billed": None, "currency": None, "source": None},
        {"bytes": 0, "empty": True},
        {"level": "checagem_por_caminho; insuficiente para R5"})
    claims = {c["claim"]: c for c in capability["claims"]}
    assert claims["custo_faturado_do_provedor"]["supported"] is False
    assert claims["custo_faturado_do_provedor"]["reason"]
    assert claims["reducao_de_leituras_totais_do_agente"]["supported"] is False
    assert claims["teto_de_parede_aplicado"]["supported"] is True
    assert claims["isolamento_do_ouro"]["supported"] is False
    assert claims["custo_por_sucesso"]["supported"] is False
    assert capability["trust_note"]
    assert capability["not_covered"]
    assert capability["contract_state"] == "missing"


# --------------------------------------------------------------------------- adaptadores


def test_adaptador_openai_transporta_o_uso_sem_inventar_o_que_falta():
    raw = json.loads((FIXTURES / "openai_chat_completion.synthetic.json").read_text())
    event = normalize_openai_chat_completion(raw, provider="provedor-ficticio")
    assert event["kind"] == "model_call" and event["source"] == "executor"
    assert event["provider"] == "provedor-ficticio"
    assert event["model_id"] == "modelo-ficticio-a"
    assert event["request_id"] == "chatcmpl-ficticio-0001"
    assert event["stop_reason"] == "stop"
    assert event["tokens"] == {"input": 1234, "output": 56, "cache_read": 512,
                               "cache_write": None, "reasoning": 10}
    assert event["model_version"] is None and event["model_version_reason"]
    assert event["cost"] is None and event["cost_reason"]
    assert event["latency_ms"] is None and event["latency_reason"]
    assert event["backend_fingerprint"] == "fp_ficticio_0001", (
        "fingerprint do backend nao e versao do modelo"
    )
    agg = StreamAccounting()
    assert agg.absorb(event) == "executor"
    assert agg.report()["violations"] == []


def test_adaptador_anthropic_inclui_escrita_de_cache_e_respeita_o_medido():
    raw = json.loads((FIXTURES / "anthropic_message.synthetic.json").read_text())
    event = normalize_anthropic_message(raw, latency_ms=123.0,
                                       cost={"amount": 0.5, "currency": "USD"})
    assert event["model_id"] == "modelo-ficticio-b"
    assert event["tokens"] == {"input": 800, "output": 120, "cache_read": 300,
                               "cache_write": 40, "reasoning": None}
    assert event["latency_ms"] == 123.0
    assert event["cost"]["amount"] == 0.5
    assert event["stop_reason"] == "end_turn"
    error = normalize_anthropic_message({"type": "error", "error": {"type": "overloaded"}})
    assert error["status"] == "error" and error["error_class"] == "overloaded"


# --------------------------------------------------------------------------- runner: cmd


@pytest.fixture()
def workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "app.py").write_text("class App:\n    pass\n")
    for cmd in (["git", "init", "-q"], ["git", "add", "-A"],
                ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "base"]):
        subprocess.run(cmd, cwd=ws, check=True, stdout=subprocess.DEVNULL)
    return ws


@pytest.fixture()
def tasks_file(tmp_path: Path, workspace: Path) -> Path:
    doc = {
        "schema": "atlas-tasks/1",
        "platform": "teste",
        "tasks": [{"id": "s01", "split": "smoke", "category": "bug_local",
                   "statement": "fac,a App mudar", "test_command": ["true"], "timeout_s": 60}],
    }
    path = tmp_path / "tasks.json"
    path.write_text(json.dumps(doc))
    return path


def write_script(tmp_path: Path, body: str, name: str = "executor_ficticio.py") -> Path:
    script = tmp_path / name
    script.write_text(body)
    return script


def run_cmd(workspace: Path, tasks_file: Path, out: Path, script: Path,
            *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(RUNNER), "--tasks", str(tasks_file), "--task", "s01",
         "--workspace", str(workspace), "--out", str(out), "--executor", "cmd",
         "--executor-cmd", f"'{sys.executable}' '{script}'", *extra],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def manifest_of(out: Path) -> dict:
    return json.loads((out / "manifest.json").read_text())


COMPLETE_SCRIPT = '''#!/usr/bin/env python3
"""Executor ficticio com contrato completo: sem modelo, sem rede. Fixture de contrato."""
import json, os, pathlib

stream = os.environ["ATLAS_EXECUTOR_TELEMETRY"]
result_path = os.environ["ATLAS_EXECUTOR_RESULT"]
ws = pathlib.Path(os.environ["ATLAS_WORKSPACE"])
''' + EMIT + '''
def call(request_id, status="ok", error_class=None, tokens=None, latency=None, cost=None):
    emit({"kind": "model_call", "source": "executor", "provider": "provedor-ficticio",
          "model_id": "modelo-ficticio-a", "model_version": "2026-09-01", "request_id": request_id,
          "status": status, "error_class": error_class, "stop_reason": "end_turn",
          "tokens": tokens, "latency_ms": latency, "cost": cost})

call("r1", tokens={"input": 100, "output": 20, "cache_read": 5}, latency=400,
     cost={"amount": 0.01, "currency": "USD"})
call("r2", status="error", error_class="timeout", tokens={"input": 10, "output": 0},
     latency=900)
emit({"kind": "retry", "source": "executor", "of_request_id": "r2", "error_class": "timeout"})
for index in range(3):
    emit({"kind": "tool_call", "source": "executor", "tool": "shell", "argv": ["true"],
          "exit_code": 0, "stdout_bytes": 10})
    emit({"kind": "turn", "source": "executor", "index": index})
emit({"kind": "stop", "source": "executor", "reason": "task_solved"})

(ws / "solution.txt").write_text("patch do executor ficticio\\n")
result = {
    "schema": "atlas-executor-result/1",
    "executor": {"name": "executor-ficticio", "version": "1"},
    "model": {"provider": "provedor-ficticio", "id": "modelo-ficticio-a",
              "version": "2026-09-01", "verified_by": "fixture:synthetic"},
    "tokenizer": {"id": "tokenizer-ficticio", "is_exact": False},
    "usage": {"model_calls": 2, "input_tokens": 110, "output_tokens": 20,
              "cache_read_tokens": 5, "cache_write_tokens": None,
              "tool_calls_declared": 3, "turns": 3},
    "errors": {"count": 1, "classes": {"timeout": 1}},
    "retries": {"count": 1},
    "stop": {"reason": "task_solved"},
    "cost": {"provider_billed": 0.01, "currency": "USD", "source": "fixture:synthetic"},
    "coverage": {
        "model_identity": {"observed": True, "source": "fixture"},
        "tokens": {"observed": True, "source": "stream:model_call"},
        "cost": {"observed": True, "source": "fixture"},
        "tool_calls": {"observed": True, "source": "stream:tool_call"},
        "turns": {"observed": True, "source": "stream:turn"}},
}
with open(result_path, "w") as fh:
    json.dump(result, fh)
print("executor ficticio concluido")
'''

NO_RESULT_SCRIPT = '''#!/usr/bin/env python3
"""Executor externo que nao entrega result contract: identidade e custo nao verificaveis."""
print("sem result contract")
'''

SHELL_LOOP_SCRIPT = '''#!/usr/bin/env python3
"""Executor que declara centenas de chamadas de shell: o teto tem de ve-las."""
import json, os, time

stream = os.environ["ATLAS_EXECUTOR_TELEMETRY"]
''' + EMIT + '''
for index in range(400):
    emit({"kind": "tool_call", "source": "executor", "tool": "shell",
          "argv": ["echo", str(index)], "exit_code": 0, "stdout_bytes": 12})
    time.sleep(0.01)
'''

TURN_LOOP_SCRIPT = '''#!/usr/bin/env python3
"""Executor que emite turnos: com evento de turno, o teto de turnos passa a ser fiscalizavel."""
import json, os, time

stream = os.environ["ATLAS_EXECUTOR_TELEMETRY"]
''' + EMIT + '''
for index in range(400):
    emit({"kind": "turn", "source": "executor", "index": index})
    time.sleep(0.01)
'''

FORGERY_SCRIPT = '''#!/usr/bin/env python3
"""Executor que tenta fabricar leitura sancionada: `opened` e do shim, nao do executor."""
import json, os, pathlib

stream = os.environ["ATLAS_EXECUTOR_TELEMETRY"]
result_path = os.environ["ATLAS_EXECUTOR_RESULT"]
''' + EMIT + '''
emit({"kind": "opened", "source": "executor", "file": "app.py", "from": 1, "to": 9})
emit({"kind": "tool_call", "source": "executor", "tool": "atlas-read", "argv": ["app.py"]})
with open(result_path, "w") as fh:
    json.dump({
        "schema": "atlas-executor-result/1",
        "model": {"provider": "provedor-ficticio", "id": "modelo-ficticio-a",
                  "version": "2026-09-01", "verified_by": "fixture:synthetic"},
        "usage": {"model_calls": None, "input_tokens": None, "output_tokens": None,
                  "cache_read_tokens": None, "cache_write_tokens": None,
                  "tool_calls_declared": None, "turns": None},
        "stop": {"reason": "sem_modelo"},
        "cost": None,
        "coverage": {m: {"observed": False, "source": "ausente",
                         "reason": "executor sem modelo nesta fixture"}
                     for m in ["model_identity", "tokens", "cost", "tool_calls", "turns"]},
    }, fh)
print("tentativa de forja")
'''


def test_executor_com_contrato_fechado_e_evidencia_real(workspace, tasks_file, tmp_path):
    script = write_script(tmp_path, COMPLETE_SCRIPT)
    out = tmp_path / "attempt"
    proc = run_cmd(workspace, tasks_file, out, script, "--condition", "CTX-RS")
    assert proc.returncode == 0, proc.stdout
    man = manifest_of(out)
    assert man["contract"]["state"] == "ok", man["contract"]
    assert man["evidence_class"] == "real"
    assert man["model"]["id"] == "modelo-ficticio-a"
    assert man["model"]["identity_verified"] is True
    assert man["model"]["verified_by"] == "fixture:synthetic"
    assert man["tokenizer"]["id"] == "tokenizer-ficticio"
    usage = man["usage"]
    assert usage["model_calls"] == 2
    assert usage["tokens"]["input"] == 110 and usage["tokens"]["output"] == 20
    assert usage["tokens"]["cache_read"] == 5 and usage["tokens"]["cache_write"] is None
    assert usage["errors"] == {"count": 1, "classes": {"timeout": 1}}
    assert usage["retries"] == 1
    assert usage["latency_ms"] == {"total": 1300.0, "max": 900.0, "n": 2}
    assert usage["turns"] == 3 and usage["turns_reason"] is None
    # Ferramentas: declaradas pelo executor entram no total e no teto; observadas ficam separadas.
    assert usage["tool_calls"] == 3
    assert usage["tool_calls_declared"] == 3 and usage["tool_calls_observed"] == 0
    assert usage["tool_calls_rejected"] == 0
    assert usage["tool_calls_by_tool"] == {"shell": 3}
    assert usage["delivered_bytes"] == 0, "bytes entregues so do shim, nunca do declarado"
    assert usage["declared_delivered_bytes"] == 30
    assert man["cost"]["provider_billed"] == 0.01 and man["cost"]["currency"] == "USD"
    assert man["patch"]["bytes"] > 0
    # Nada reconciliado diverge; campo ausente fica `missing`, nao zero.
    states = {row["metric"]: row["state"] for row in man["contract"]["reconciliation"]}
    assert "mismatch" not in states.values()
    assert states["cache_write_tokens"] == "missing"
    capacity = json.loads((out / "capability_manifest.json").read_text())
    supported = {c["claim"] for c in capacity["claims"] if c["supported"]}
    assert "custo_faturado_do_provedor" in supported
    assert "reducao_de_leituras_totais_do_agente" not in supported
    assert capacity["evidence_class"] == "real"


def test_executor_sem_result_contract_nao_vira_evidencia_real(workspace, tasks_file, tmp_path):
    script = write_script(tmp_path, NO_RESULT_SCRIPT)
    out = tmp_path / "attempt"
    proc = run_cmd(workspace, tasks_file, out, script, "--condition", "BASE")
    assert proc.returncode == 0, proc.stdout
    man = manifest_of(out)
    assert man["contract"]["state"] == "missing"
    assert man["evidence_class"] == "unverified"
    assert man["model"]["id"] is None and man["model"]["reason"]
    assert man["cost"]["provider_billed"] is None and man["cost"]["reason"]
    assert man["contract"]["missing"], "ausencia tem de ficar registrada, nao virar zero"
    assert man["contract"]["coverage"]["model_identity"]["observed"] is False
    capacity = json.loads((out / "capability_manifest.json").read_text())
    assert all(not c["supported"] for c in capacity["claims"]
               if c["claim"] in ("custo_faturado_do_provedor", "tokens_do_modelo"))


def test_teto_conta_chamadas_de_shell_declaradas(workspace, tasks_file, tmp_path):
    script = write_script(tmp_path, SHELL_LOOP_SCRIPT)
    out = tmp_path / "attempt"
    proc = run_cmd(workspace, tasks_file, out, script, "--condition", "BASE",
                   "--tool-call-limit", "3")
    assert proc.returncode != 0, "tentativa parada por teto e falha, nao sucesso"
    man = manifest_of(out)
    assert man["stopped_by"] == "tool_calls"
    assert man["usage"]["tool_calls_observed"] == 0
    assert man["usage"]["tool_calls"] > 3
    assert man["usage"]["tool_calls_by_tool"] == {"shell": man["usage"]["tool_calls"]}


def test_teto_de_turnos_para_a_tentativa_com_evento_do_executor(workspace, tasks_file, tmp_path):
    script = write_script(tmp_path, TURN_LOOP_SCRIPT)
    out = tmp_path / "attempt"
    proc = run_cmd(workspace, tasks_file, out, script, "--condition", "BASE",
                   "--turn-limit", "2")
    assert proc.returncode != 0
    man = manifest_of(out)
    assert man["stopped_by"] == "turns"
    assert man["usage"]["turns"] > 2, "o estouro fica registrado, nao arredondado para baixo"
    assert man["usage"]["turns_reason"] is None, "com evento de turno o teto e fiscalizavel"


def test_stream_divergente_do_result_e_violacao_de_contrato(workspace, tasks_file, tmp_path):
    divergent = COMPLETE_SCRIPT.replace('"model_calls": 2,', '"model_calls": 9,')
    script = write_script(tmp_path, divergent)
    out = tmp_path / "attempt"
    proc = run_cmd(workspace, tasks_file, out, script, "--condition", "CTX-RS")
    man = manifest_of(out)
    assert man["contract"]["state"] == "violation"
    assert man["evidence_class"] == "contract_violation"
    assert any(v.startswith("reconciliacao_divergente:model_calls")
               for v in man["contract"]["violations"])
    assert man["model"]["id"] == "modelo-ficticio-a", "violacao nao apaga o declarado"
    assert proc.returncode == 0, "violacao de contrato e problema de instrumento, nao do braco"


def test_leitura_fabricada_pelo_executor_e_violacao_e_nao_conta(workspace, tasks_file, tmp_path):
    script = write_script(tmp_path, FORGERY_SCRIPT)
    out = tmp_path / "attempt"
    run_cmd(workspace, tasks_file, out, script, "--condition", "CTX-RS")
    man = manifest_of(out)
    assert man["usage"]["opened"] == 0, "sem shim, nao existe leitura sancionada"
    # A chamada com nome reservado nao entra como observada nem como declarada valida, mas
    # continua contando no teto: subdeclarar nao pode render chamada extra.
    assert man["usage"]["tool_calls"] == 1
    assert man["usage"]["tool_calls_observed"] == 0
    assert man["usage"]["tool_calls_rejected"] == 1
    assert man["usage"]["tool_calls_by_tool"] == {}
    assert man["contract"]["state"] == "violation"
    assert man["evidence_class"] == "contract_violation"
    assert any("reserved_kind" in v for v in man["contract"]["violations"])
    assert any("impersonated_tool" in v for v in man["contract"]["violations"])


def test_loop_diferente_do_fixado_e_recusado(workspace, tasks_file, tmp_path):
    script = write_script(tmp_path, NO_RESULT_SCRIPT)
    out = tmp_path / "attempt"
    proc = run_cmd(workspace, tasks_file, out, script, "--condition", "BASE",
                   "--expect-loop-sha", "sha256:0000000000000000000000000000000000000000000000000000000000000000")
    assert proc.returncode != 0
    assert "BLOQUEADO" in proc.stdout
    assert not (out / "manifest.json").exists(), "loop divergente nao pode produzir tentativa"


def test_loop_sha_e_igual_entre_bracos_com_mesmo_executor(workspace, tasks_file, tmp_path):
    script = write_script(tmp_path, NO_RESULT_SCRIPT)
    shas = []
    for condition in ("BASE", "LEX-RS", "CTX-RS"):
        out = tmp_path / f"attempt-{condition}"
        run_cmd(workspace, tasks_file, out, script, "--condition", condition)
        shas.append(manifest_of(out)["executor"]["loop_sha256"])
    assert len(set(shas)) == 1, "os tres bracos rodam o mesmo loop: executor, ferramentas e tetos"
