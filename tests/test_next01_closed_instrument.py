# SPDX-License-Identifier: Apache-2.0
"""NEXT-01 — fechar o instrumento antes da rodada.

O que estes testes guardam, e por que cada um existe:

- **Configuração estável.** O probe da auditoria 2026-10-05 mostrou `loop_fingerprint`
  mudando só porque os caminhos temporários mudaram. `loop_config_sha256` exclui
  caminhos e enunciado: mesmo loop em diretórios distintos produz o mesmo hash, e
  mudança de código, ferramenta ou teto muda o hash. Enunciado e caminhos ficam em
  campos próprios, e a conferência de "mesma tarefa entre braços" é por tarefa, não
  pelo loop.
- **Preflight fechado.** SHA completo (sem prefixo), HEAD presente e árvore rastreada
  limpa no workspace; base de aceitação suja/sem HEAD recusa o julgamento sem culpar
  o patch. Sem isso, uma tentativa pode medir a base errada e ninguém percebe.
- **Falhas distintas.** Timeout, falha de aplicação, regressão do patch, dependência
  ausente e bloqueio de ambiente são estados diferentes no manifesto. Falta comprovada
  antes do patch não vira rejeição do patch; timeout gera manifesto + log + base
  restaurada; saída 3 (reservada ao harness) bloqueia o julgamento em vez de reprovar.
  A regra é a mesma nos três braços — o executor nunca escolhe a classe da própria
  falha. Nenhuma falha sai do denominador: nada aqui vira sucesso.

Nenhum teste usa rede, modelo ou provedor: o executor é o `dry` (`infrastructure_only`).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNNER = REPO_ROOT / "benchmarks/rust/runner.py"
sys.path.insert(0, str(REPO_ROOT / "benchmarks/rust"))
import eval as atlas_eval  # noqa: E402


@pytest.fixture()
def workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "app.py").write_text("class App:\n    def getTitular(self):\n        return 1\n")
    (ws / "dry_edit.txt").write_text("original\n")
    for cmd in (["git", "init", "-q"], ["git", "add", "-A"],
                ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "base"]):
        subprocess.run(cmd, cwd=ws, check=True, stdout=subprocess.DEVNULL)
    return ws


def fresh_workspace(workspace: Path, tmp_path: Path, name: str) -> Path:
    clone = tmp_path / name
    subprocess.run(["git", "clone", "-q", str(workspace), str(clone)], check=True)
    return clone


def head(repo: Path) -> str:
    return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                          stdout=subprocess.PIPE).stdout.decode().strip()


def tasks_file(tmp_path: Path, base: Path, test_command: list, name: str = "tasks.json",
               timeout_s: int = 60, base_sha: str | None = "AUTO") -> Path:
    doc = {
        "schema": "atlas-tasks/1",
        "platform": "teste",
        "tasks": [{
            "id": "s01", "split": "smoke", "category": "bug_local",
            "statement": "faca getTitular devolver 2",
            "base_sha": head(base) if base_sha == "AUTO" else base_sha,
            "test_command": test_command,
            "timeout_s": timeout_s,
        }],
    }
    p = tmp_path / name
    p.write_text(json.dumps(doc))
    return p


def run_runner(workspace: Path, tasks: Path, out: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(RUNNER), "--tasks", str(tasks), "--task", "s01",
         "--workspace", str(workspace), "--out", str(out), "--executor", "dry",
         "--allow-dry", *extra],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def manifest_of(out: Path) -> dict:
    return json.loads((out / "manifest.json").read_text())


PASS_CMD = [sys.executable, "-c", "import sys; sys.exit(0)"]


# --- configuração estável -------------------------------------------------------


def test_config_hash_estavel_entre_caminhos_distintos(workspace, tmp_path):
    """Mesmo loop em workspaces/saídas distintos => mesmo config; tentativa difere."""
    tasks = tasks_file(tmp_path, workspace, PASS_CMD)
    manifests = []
    for i in ("a", "b"):
        ws = fresh_workspace(workspace, tmp_path, f"ws-{i}")
        base = fresh_workspace(workspace, tmp_path, f"base-{i}")
        out = tmp_path / f"attempt-{i}"
        proc = run_runner(ws, tasks, out, "--condition", "BASE",
                          "--acceptance-repo", str(base))
        assert proc.returncode == 0, proc.stdout
        manifests.append(manifest_of(out))
    a, b = manifests
    assert a["executor"]["loop_config_sha256"] == b["executor"]["loop_config_sha256"], \
        "só caminhos mudaram: a configuração da rodada é a mesma"
    assert a["executor"]["loop_sha256"] != b["executor"]["loop_sha256"], \
        "a identidade da tentativa carrega caminhos e continua distinta"
    assert a["executor"]["task_identity"] == b["executor"]["task_identity"], \
        "mesma tarefa entre braços se confere por tarefa+enunciado, não pelo loop"
    assert a["prompt"]["statement_sha256"] == b["prompt"]["statement_sha256"]
    assert a["executor"]["cmd"] != b["executor"]["cmd"], \
        "os caminhos efetivos ficam registrados, fora do hash de configuração"


def test_config_muda_com_teto_e_traz_codigo_e_ferramentas(workspace, tmp_path):
    tasks = tasks_file(tmp_path, workspace, PASS_CMD)
    outs = []
    for i, extra in enumerate(([], ["--tool-call-limit", "7"])):
        ws = fresh_workspace(workspace, tmp_path, f"wsc-{i}")
        out = tmp_path / f"att-{i}"
        proc = run_runner(ws, tasks, out, "--condition", "BASE", *extra)
        assert proc.returncode == 0, proc.stdout
        outs.append(manifest_of(out))
    assert outs[0]["executor"]["loop_config_sha256"] != outs[1]["executor"]["loop_config_sha256"], \
        "mudar o teto tem de mudar a configuração"
    config = outs[0]["executor"]["loop_config"]
    assert config["schema"] == "atlas-loop-config/1"
    assert config["executor"]["code_sha256"] and config["executor"]["code_sha256"].startswith("sha256:")
    assert config["tools"]["protocol"] == "atlas-tools/1"
    assert config["tools"]["spec_sha256"] and config["tools"]["spec_sha256"].startswith("sha256:")
    assert config["limits"] == {"wall_s": 1800, "turns": 40, "tool_calls": 100}


def test_expect_loop_config_sha_bloqueia_divergencia_e_passa_em_outro_caminho(
        workspace, tmp_path):
    tasks = tasks_file(tmp_path, workspace, PASS_CMD)
    ws0 = fresh_workspace(workspace, tmp_path, "ws-0")
    out0 = tmp_path / "att-0"
    assert run_runner(ws0, tasks, out0, "--condition", "BASE").returncode == 0
    config_sha = manifest_of(out0)["executor"]["loop_config_sha256"]

    ws1 = fresh_workspace(workspace, tmp_path, "ws-1")
    out1 = tmp_path / "att-1"
    proc = run_runner(ws1, tasks, out1, "--condition", "LEX-RS",
                      "--expect-loop-config-sha", config_sha)
    assert proc.returncode == 0, proc.stdout
    assert manifest_of(out1)["executor"]["loop_config_sha256"] == config_sha

    ws2 = fresh_workspace(workspace, tmp_path, "ws-2")
    out2 = tmp_path / "att-2"
    proc = run_runner(ws2, tasks, out2, "--condition", "CTX-RS",
                      "--expect-loop-config-sha", "sha256:" + "0" * 64)
    assert proc.returncode != 0
    assert "BLOQUEADO" in proc.stdout
    assert not (out2 / "manifest.json").exists(), \
        "configuração divergente não pode produzir tentativa"


# --- preflight fechado ----------------------------------------------------------


def test_preflight_recusa_sha_incorreto(workspace, tmp_path):
    tasks = tasks_file(tmp_path, workspace, PASS_CMD,
                       base_sha="0" * 40, name="tasks-badsha.json")
    out = tmp_path / "attempt"
    proc = run_runner(workspace, tasks, out, "--condition", "BASE")
    assert proc.returncode != 0
    assert "BLOQUEADO" in proc.stdout
    assert not (out / "manifest.json").exists()


def test_preflight_recusa_prefixo_curto_mesmo_correto(workspace, tmp_path):
    tasks = tasks_file(tmp_path, workspace, PASS_CMD,
                       base_sha=head(workspace)[:8], name="tasks-prefix.json")
    out = tmp_path / "attempt"
    proc = run_runner(workspace, tasks, out, "--condition", "BASE")
    assert proc.returncode != 0
    assert "SHA completo" in proc.stdout
    assert not (out / "manifest.json").exists(), \
        "prefixo de 8 caracteres não fixa base"


def test_preflight_recusa_workspace_sem_head(tmp_path):
    ws = tmp_path / "ws-nohead"
    ws.mkdir()
    (ws / "app.py").write_text("x = 1\n")
    tasks = tasks_file(tmp_path, ws, PASS_CMD, base_sha=None, name="tasks-nohead.json")
    out = tmp_path / "attempt"
    proc = run_runner(ws, tasks, out, "--condition", "BASE")
    assert proc.returncode != 0
    assert "BLOQUEADO" in proc.stdout
    assert not (out / "manifest.json").exists()


def test_preflight_recusa_workspace_sujo(workspace, tmp_path):
    (workspace / "app.py").write_text("class App:\n    def getTitular(self):\n        return 999\n")
    tasks = tasks_file(tmp_path, workspace, PASS_CMD)
    out = tmp_path / "attempt"
    proc = run_runner(workspace, tasks, out, "--condition", "BASE")
    assert proc.returncode != 0
    assert "suja" in proc.stdout
    assert not (out / "manifest.json").exists()


def test_preflight_registrado_no_manifesto(workspace, tmp_path):
    ws = fresh_workspace(workspace, tmp_path, "ws-pre")
    out = tmp_path / "attempt"
    tasks = tasks_file(tmp_path, workspace, PASS_CMD)
    assert run_runner(ws, tasks, out, "--condition", "BASE").returncode == 0
    man = manifest_of(out)
    assert man["preflight"]["workspace"]["base_sha_full"] == head(workspace)
    assert len(man["preflight"]["workspace"]["base_sha_full"]) == 40
    assert man["snapshot"]["base_sha"] == head(workspace)


# --- estados distintos do aceite -------------------------------------------------


def test_timeout_gera_manifesto_log_e_julgamento_bloqueado(workspace, tmp_path):
    sleep_cmd = [sys.executable, "-c", "import time; time.sleep(30)"]
    tasks = tasks_file(tmp_path, workspace, sleep_cmd, timeout_s=2)
    ws = fresh_workspace(workspace, tmp_path, "ws-tmo")
    base = fresh_workspace(workspace, tmp_path, "base-tmo")
    out = tmp_path / "attempt"
    proc = run_runner(ws, tasks, out, "--condition", "BASE",
                      "--acceptance-repo", str(base))
    assert proc.returncode == 0, proc.stdout
    man = manifest_of(out)
    acc = man["acceptance"]
    assert acc["state"] == "acceptance_timeout", acc
    assert acc["exit_code"] is None
    assert (out / "acceptance_output.txt").exists(), "timeout gera log parcial"
    assert acc["restored"]["tracked_clean_after"] is True, "base restaurada após timeout"
    assert man["usage"]["wall_s"] > 0, "custos de falha continuam registrados"
    row = atlas_eval.check_attempt(out, tasks_doc_2(tasks, workspace))
    assert row["mechanical_verdict"] == "indeterminado", row
    assert row["failure_class"] == "environmental"
    assert row["mechanical_verdict"] != "aceito", "timeout nunca é sucesso"


def test_exit_3_e_bloqueio_de_ambiente_igual_nos_tres_bracos(workspace, tmp_path):
    env_cmd = [sys.executable, "-c", "import sys; sys.exit(3)"]
    tasks = tasks_file(tmp_path, workspace, env_cmd)
    states = []
    for i, cond in enumerate(("BASE", "LEX-RS", "CTX-RS")):
        ws = fresh_workspace(workspace, tmp_path, f"ws-env-{i}")
        base = fresh_workspace(workspace, tmp_path, f"base-env-{i}")
        out = tmp_path / f"attempt-env-{i}"
        proc = run_runner(ws, tasks, out, "--condition", cond,
                          "--acceptance-repo", str(base))
        assert proc.returncode == 0, proc.stdout
        man = manifest_of(out)
        states.append(man["acceptance"]["state"])
        assert man["acceptance"]["exit_code"] == 3
        row = atlas_eval.check_attempt(out, tasks_doc_2(tasks, workspace))
        assert row["mechanical_verdict"] == "indeterminado", (cond, row)
        assert row["failure_class"] == "environmental"
        assert "M2" in row["mechanical_rejected_items"]
    assert states == ["env_blocked"] * 3, "regra igual nos três braços"


def test_dependencia_ausente_nao_culpa_o_patch(workspace, tmp_path):
    tasks = tasks_file(tmp_path, workspace, ["binario-que-nao-existe-xyz", "--version"])
    ws = fresh_workspace(workspace, tmp_path, "ws-dep")
    base = fresh_workspace(workspace, tmp_path, "base-dep")
    before = head(base)
    out = tmp_path / "attempt"
    proc = run_runner(ws, tasks, out, "--condition", "BASE",
                      "--acceptance-repo", str(base))
    assert proc.returncode == 0, proc.stdout
    man = manifest_of(out)
    acc = man["acceptance"]
    assert acc["state"] == "deps_missing", acc
    assert acc["applied"] is None, "patch nem aplicado: falta comprovada antes do patch"
    assert head(base) == before, "base intocada"
    row = atlas_eval.check_attempt(out, tasks_doc_2(tasks, workspace))
    assert row["mechanical_verdict"] == "indeterminado"
    assert row["mechanical_verdict"] != "aceito"


def test_apply_failed_e_regressao_sao_distintos(workspace, tmp_path):
    # Base de aceitação com conteúdo divergente: o patch do dry não aplica.
    divergent = tmp_path / "divergent"
    subprocess.run(["git", "clone", "-q", str(workspace), str(divergent)], check=True)
    (divergent / "dry_edit.txt").write_text("conteudo-divergente\n")
    subprocess.run(["git", "-C", str(divergent), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(divergent), "-c", "user.email=t@t",
                    "-c", "user.name=t", "commit", "-qm", "diverge"], check=True)
    tasks = tasks_file(tmp_path, workspace, PASS_CMD, name="tasks-apply.json")
    ws = fresh_workspace(workspace, tmp_path, "ws-apply")
    out = tmp_path / "attempt-apply"
    assert run_runner(ws, tasks, out, "--condition", "BASE",
                      "--acceptance-repo", str(divergent)).returncode == 0
    acc = manifest_of(out)["acceptance"]
    assert acc["state"] == "apply_failed", acc
    assert acc["applied"] is False

    # Regressão: aplica, mas o teste reprova (exit 1, não 3).
    tasks2 = tasks_file(tmp_path, workspace,
                        [sys.executable, "-c", "import sys; sys.exit(1)"],
                        name="tasks-reg.json")
    ws2 = fresh_workspace(workspace, tmp_path, "ws-reg")
    base2 = fresh_workspace(workspace, tmp_path, "base-reg")
    out2 = tmp_path / "attempt-reg"
    assert run_runner(ws2, tasks2, out2, "--condition", "BASE",
                      "--acceptance-repo", str(base2)).returncode == 0
    man2 = manifest_of(out2)
    assert man2["acceptance"]["state"] == "patch_regression", man2["acceptance"]
    assert man2["acceptance"]["applied"] is True
    row = atlas_eval.check_attempt(out2, tasks_doc_2(tasks2, workspace))
    assert row["mechanical_verdict"] == "rejeitado", row
    assert row["failure_class"] == "patch_fault"


def test_base_suja_recusa_julgamento_sem_culpar_o_patch(workspace, tmp_path):
    tasks = tasks_file(tmp_path, workspace, PASS_CMD)
    ws = fresh_workspace(workspace, tmp_path, "ws-dirty")
    base = fresh_workspace(workspace, tmp_path, "base-dirty")
    (base / "app.py").write_text("sujeira da tentativa anterior\n")
    out = tmp_path / "attempt"
    proc = run_runner(ws, tasks, out, "--condition", "BASE",
                      "--acceptance-repo", str(base))
    assert proc.returncode == 0, proc.stdout
    acc = manifest_of(out)["acceptance"]
    assert acc["state"] == "env_blocked", acc
    assert acc["applied"] is None, "nunca reutilizar base modificada"


def tasks_doc_2(tasks_path: Path, workspace: Path) -> dict:
    """Conjunto equivalente em `atlas-tasks/2` para o avaliador (mesma tarefa)."""
    doc = json.loads(tasks_path.read_text())
    t = doc["tasks"][0]
    return {
        "schema": "atlas-tasks/2",
        "tasks": [{
            "id": t["id"], "split": "smoke", "category": "bug_local",
            "statement": t["statement"], "test_command": t["test_command"],
            "base_sha": t["base_sha"], "origin": "teste",
            "allowed_paths": ["dry_edit.txt", "app.py"],
            "immutable_paths": [],
            "contamination_risk": "baixo",
            "contamination_note": "fixture sintética de instrumento",
        }],
    }
