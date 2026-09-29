# SPDX-License-Identifier: Apache-2.0
"""Testes do runner de tentativa (`benchmarks/rust/runner.py`).

O que estes testes guardam, e por que cada um existe:

- `opened` **não** é derivado de `delivered`. O teste roda duas tentativas, uma que lê e outra
  que não lê, e exige os dois números diferentes — se alguém reintroduzir a fórmula proibida no
  contrato §9, o teste cai.
- Ouro dentro do workspace **bloqueia** a tentativa, e o ambiente do executor não contém o
  caminho do ouro. O pré-registro §4 diz que worktree não é isolamento; o runner não pode
  fingir o contrário, mas pode recusar o caso que ele *consegue* detectar.
- Teto primeiro: parede e chamadas de ferramenta param a tentativa como falha, e o motivo fica
  registrado. Continuar "só para terminar a etapa" é o que o protocolo §4 proíbe.
- Campo desconhecido é `null` **com motivo**, nunca zero (protocolo §6).

Nenhum teste usa rede, modelo ou o binário Rust: o `atlas` é um fake com o mesmo contrato de
processo, e o executor é o `dry` marcado como `infrastructure_only`.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNNER = REPO_ROOT / "benchmarks/rust/runner.py"

FAKE_ATLAS = '''#!/usr/bin/env python3
"""Fake com o contrato de processo do binario real: um JSON, exit 0."""
import json, sys, pathlib

cmd = sys.argv[1] if len(sys.argv) > 1 else ""
body = ""
if cmd == "context":
    body = "class App:\\n    def getTitular(self):\\n        return 1\\n"
env = {
    "schema": "atlas-context/1", "schema_version": 1, "state": "ok",
    "snapshot": {"sha_base": "teste", "index_generation": "gen", "index_state": "ok"},
    "units": [{"file": "app.py", "line": 2, "end_line": 2, "hash": "sha256:" + "0" * 64,
               "kind": "excerpt", "text": body, "evidence": "tokens=getTitular",
               "reason": "bm25", "truncated": False}],
    "budget": {"requested_tokens": 2000, "used_tokens": 40, "unit": "byte",
               "tokenizer_id": None, "tokenizer_is_exact": False, "max_bytes": 8000,
               "used_bytes": 120},
    "omitted": {"n": 0, "reasons": []}, "hints": [],
}
print(json.dumps(env))
'''


@pytest.fixture()
def workspace(tmp_path: Path) -> Path:
    """Checkout de base limpa: um repo git com um arquivo, já commitado."""
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "app.py").write_text("class App:\n    def getTitular(self):\n        return 1\n")
    (ws / "dry_edit.txt").write_text("original\n")
    for cmd in (["git", "init", "-q"], ["git", "add", "-A"],
                ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "base"]):
        subprocess.run(cmd, cwd=ws, check=True, stdout=subprocess.DEVNULL)
    return ws


@pytest.fixture()
def tasks_file(tmp_path: Path, workspace: Path) -> Path:
    doc = {
        "schema": "atlas-tasks/1",
        "platform": "teste",
        "tasks": [{
            "id": "s01", "split": "smoke", "category": "bug_local",
            "statement": "fac,a getTitular devolver 2",
            "base_sha": subprocess.run(["git", "-C", str(workspace), "rev-parse", "HEAD"],
                                       stdout=subprocess.PIPE).stdout.decode().strip(),
            "test_command": [sys.executable, "-c",
                             "import pathlib,sys;sys.exit(0 if pathlib.Path('dry_edit.txt')"
                             ".read_text().strip()!='original' else 1)"],
            "timeout_s": 60,
        }],
    }
    p = tmp_path / "tasks.json"
    p.write_text(json.dumps(doc))
    return p


@pytest.fixture()
def gold(tmp_path: Path) -> Path:
    g = tmp_path / "ouro"
    g.mkdir()
    (g / "s01.patch").write_text("diff --git a/app.py b/app.py\n+SOLUCAO_DO_OURO\n")
    return g


def run_runner(workspace: Path, tasks_file: Path, out: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(RUNNER), "--tasks", str(tasks_file), "--task", "s01",
         "--workspace", str(workspace), "--out", str(out), "--executor", "dry",
         "--allow-dry", *extra],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def manifest_of(out: Path) -> dict:
    return json.loads((out / "manifest.json").read_text())


def test_dry_sem_allow_dry_e_recusado(workspace, tasks_file, tmp_path):
    out = tmp_path / "attempt"
    proc = subprocess.run(
        [sys.executable, str(RUNNER), "--tasks", str(tasks_file), "--task", "s01",
         "--workspace", str(workspace), "--out", str(out), "--condition", "BASE",
         "--executor", "dry"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    assert proc.returncode != 0
    assert "dry" in proc.stdout
    assert not (out / "manifest.json").exists(), "stub nao pode produzir artefato de tentativa"


def test_ouro_dentro_do_workspace_bloqueia(workspace, tasks_file, tmp_path):
    inside = workspace / "ouro"
    inside.mkdir()
    (inside / "s01.patch").write_text("SOLUCAO\n")
    out = tmp_path / "attempt"
    proc = run_runner(workspace, tasks_file, out, "--condition", "BASE", "--gold", str(inside))
    assert proc.returncode != 0
    assert "BLOQUEADO" in proc.stdout
    assert not (out / "manifest.json").exists()


def test_ambiente_nao_expoe_ouro_nem_o_conteudo(workspace, tasks_file, gold, tmp_path):
    out = tmp_path / "attempt"
    proc = run_runner(workspace, tasks_file, out, "--condition", "BASE", "--gold", str(gold))
    assert proc.returncode == 0, proc.stdout
    man = manifest_of(out)
    assert man["gold_isolation"]["state"] == "verificado_por_caminho"
    assert man["gold_isolation"]["in_executor_env"] is False
    assert man["gold_isolation"]["path_recorded"] is False
    # O caminho do ouro nao pode aparecer em **nenhum** artefato de tentativa: o runner entrega
    # o diretorio de saida ao executor via ATLAS_TELEMETRY, logo o manifesto tambem e legivel.
    for artefact in out.rglob("*"):
        if artefact.is_file():
            assert str(gold) not in artefact.read_text(errors="replace"), artefact
    # Nem o conteudo do patch de ouro.
    for artefact in [out / "executor_output.txt", out / "attempt.patch"]:
        assert "SOLUCAO_DO_OURO" not in artefact.read_text(errors="replace")


def test_opened_vem_de_leitura_real(workspace, tasks_file, tmp_path):
    fake = tmp_path / "fake_atlas.py"
    fake.write_text(FAKE_ATLAS)
    fake.chmod(0o755)
    out = tmp_path / "attempt"
    proc = run_runner(workspace, tasks_file, out, "--condition", "CTX-RS",
                      "--atlas-bin", str(fake), "--atlas-repo", str(workspace))
    assert proc.returncode == 0, proc.stdout
    man = manifest_of(out)
    # Duas chamadas de ferramenta: uma ao `atlas` (contexto) e uma leitura sancionada.
    assert man["usage"]["tool_calls"] == 2, "atlas e leitura contam como chamada de ferramenta"
    assert man["usage"]["opened"] == 1, "a leitura sancionada tem de virar evento `opened`"
    assert man["usage"]["delivered_bytes"] > 0, "`delivered` e medido do stdout observado"


def test_opened_zero_quando_nao_ha_leitura_mesmo_com_delivered(workspace, tasks_file, tmp_path):
    """A regra do contrato §9: sem evento de leitura, `opened` nao existe — nao se deriva."""
    out = tmp_path / "attempt"
    proc = run_runner(workspace, tasks_file, out, "--condition", "BASE")
    assert proc.returncode == 0, proc.stdout
    man = manifest_of(out)
    assert man["usage"]["opened"] == 0
    assert man["usage"]["delivered_bytes"] == 0
    assert man["usage"]["tool_calls"] == 0
    assert man["tool"]["absent_in_base"] is True


def test_teto_de_chamadas_para_a_tentativa(workspace, tasks_file, tmp_path):
    extra = json.dumps([["atlas-read", "app.py"], ["atlas-read", "app.py"],
                        ["atlas-read", "app.py"], ["atlas-read", "app.py"]])
    out = tmp_path / "attempt"
    proc = run_runner(workspace, tasks_file, out, "--condition", "BASE",
                      "--tool-call-limit", "2", "--dry-extra-calls", extra)
    assert proc.returncode != 0, "tentativa parada por teto e falha, nao sucesso"
    man = manifest_of(out)
    assert man["stopped_by"] == "tool_calls"
    assert man["outcome"] == "stopped"
    # O evento que estourou o teto ja estava escrito quando o runner matou o processo, entao a
    # contagem final passa do limite — o estouro fica registrado em vez de arredondado para baixo.
    assert man["usage"]["tool_calls"] > 2
    assert man["usage"]["opened"] == man["usage"]["tool_calls"]


def test_teto_de_parede_para_a_tentativa(workspace, tasks_file, tmp_path):
    out = tmp_path / "attempt"
    proc = run_runner(workspace, tasks_file, out, "--condition", "BASE",
                      "--wall-limit", "1", "--dry-extra-calls", "SLEEP")
    assert proc.returncode != 0
    man = manifest_of(out)
    assert man["stopped_by"] == "wall_s"
    assert man["usage"]["wall_s"] < 30, "o kill tem de acontecer logo apos o teto"


def test_turnos_nulos_com_motivo_quando_o_executor_nao_emite(workspace, tasks_file, tmp_path):
    out = tmp_path / "attempt"
    run_runner(workspace, tasks_file, out, "--condition", "BASE")
    man = manifest_of(out)
    assert man["usage"]["turns"] is None
    assert "executor" in man["usage"]["turns_reason"]
    assert man["model"]["id"] is None and man["model"]["reason"]
    assert man["cost"]["provider_billed"] is None and man["cost"]["reason"]
    assert man["tokenizer"]["id"] is None and man["tokenizer"]["reason"]


def test_patch_capturado_e_testado_em_base_limpa(workspace, tasks_file, tmp_path):
    clean = tmp_path / "clean"
    subprocess.run(["git", "clone", "-q", str(workspace), str(clean)], check=True)
    out = tmp_path / "attempt"
    proc = run_runner(workspace, tasks_file, out, "--condition", "BASE",
                      "--acceptance-repo", str(clean))
    assert proc.returncode == 0, proc.stdout
    man = manifest_of(out)
    assert man["patch"]["bytes"] > 0
    assert man["acceptance"]["applied"] is True
    assert man["acceptance"]["exit_code"] == 0, "o patch tem de fazer o teste de aceitacao passar"
    assert "dry_edit.txt" in (out / "attempt.patch").read_text()


def test_sem_base_limpa_o_aceite_e_nulo_com_motivo(workspace, tasks_file, tmp_path):
    out = tmp_path / "attempt"
    run_runner(workspace, tasks_file, out, "--condition", "BASE")
    man = manifest_of(out)
    assert man["acceptance"]["applied"] is None
    assert man["acceptance"]["exit_code"] is None
    assert man["acceptance"]["reason"], "ausencia de base limpa bloqueia a conclusao, nao vira zero"


def test_manifesto_minimo_e_rotulado_como_infraestrutura(workspace, tasks_file, tmp_path):
    out = tmp_path / "attempt"
    run_runner(workspace, tasks_file, out, "--condition", "LEX-RS")
    man = manifest_of(out)
    for key in ("schema", "run_id", "phase", "task", "condition", "snapshot", "tool", "model",
                "tokenizer", "prompt", "limits", "usage", "cost", "cache", "order",
                "timestamps", "processes", "patch", "acceptance", "stopped_by", "outcome"):
        assert key in man, f"campo obrigatorio ausente: {key}"
    assert man["evidence_class"] == "infrastructure_only"
    assert man["snapshot"]["base_sha"]
    assert man["snapshot"]["tree_sha256"]
    assert man["limits"] == {"wall_s": 1800, "turns": 40, "tool_calls": 100}
    assert man["phase"] == "smoke"


ATLAS_BIN = REPO_ROOT / "rust/archatlas/target/release/archatlas"


@pytest.mark.skipif(not ATLAS_BIN.exists(), reason="binário Rust não construído")
def test_integracao_com_o_binario_rust_de_verdade(tmp_path):
    # O caminho completo com o produto real: shim, binário, índice e captura de delivered.
    # A asserção que importa é a disciplina de R2 dentro do runner: o delivered medido pelo
    # runner tem de ser exatamente o que o produto declarou ter entregue.
    repo = tmp_path / "app"
    (repo / "br/gov").mkdir(parents=True)
    (repo / "br/gov/App.java").write_text(
        "package br.gov;\n\npublic class App {\n  public int getTitular() { return 7; }\n}\n"
    )
    (repo / "br/gov/Outro.java").write_text("package br.gov;\n\npublic class Outro {}\n")
    index = tmp_path / "idx.sqlite"
    built = subprocess.run(
        [str(ATLAS_BIN), "index", "--repo", str(repo), "--index", str(index),
         "--include", "java"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    assert built.returncode == 0, built.stdout.decode()

    tasks = tmp_path / "tasks.json"
    tasks.write_text(json.dumps({
        "schema": "atlas-tasks/1", "platform": "teste",
        "tasks": [{"id": "i01", "split": "smoke", "category": "bug_local",
                   "statement": "devolva 8 em getTitular",
                   "test_command": ["git", "--version"], "timeout_s": 60}],
    }))
    out = tmp_path / "attempt"
    proc = subprocess.run(
        [sys.executable, str(RUNNER), "--tasks", str(tasks), "--task", "i01",
         "--condition", "CTX-RS", "--workspace", str(repo), "--out", str(out),
         "--executor", "dry", "--allow-dry", "--atlas-bin", str(ATLAS_BIN),
         "--atlas-repo", str(repo), "--atlas-index", str(index)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    assert proc.returncode == 0, proc.stdout
    man = manifest_of(out)
    assert man["usage"]["tool_calls"] == 2
    assert man["usage"]["opened"] == 1
    assert man["tool"]["binary_sha256"]
    events = [json.loads(line) for line in (out / "telemetry.jsonl").read_text().splitlines()]
    call = next(e for e in events if e["kind"] == "tool_call")
    assert call["declared"]["declared_bytes"] == call["stdout_bytes"] - 1, (
        "o delivered medido pelo runner tem de fechar com os bytes declarados pelo produto"
    )


def test_condicao_base_nao_recebe_ferramenta_de_contexto(workspace, tasks_file, tmp_path):
    out = tmp_path / "attempt"
    run_runner(workspace, tasks_file, out, "--condition", "BASE")
    man = manifest_of(out)
    assert man["tool"]["binary"] is None
    assert man["tool"]["policy"] is None
    assert man["tool"]["absent_in_base"] is True
