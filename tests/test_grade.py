# SPDX-License-Identifier: Apache-2.0
"""Testes do julgamento do avaliador (`benchmarks/rust/grade.py`, NEXT-03).

O que estes testes guardam:

- **Verde público sozinho nunca aceita.** Sem gate privado, o melhor veredito é
  `indeterminado`; público verde + privado vermelho é `rejected` (não sucesso,
  não "quase"). Sem isso, o ensaio não provaria o gate que a NEXT-03 exige.
- **Falha persiste com motivo.** Patch vazio, público reprovado e privado
  reprovado viram `rejected` com a classe e o gate registrados; ambiente vira
  `indeterminado`. O julgamento sai 0 mesmo em `rejected` — só infraestrutura
  quebrada do próprio julgamento sai ≠ 0.
- **Base do operador intacta.** O julgamento roda num clone descartável; o
  `--acceptance-repo` informado termina limpo.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
GRADE = REPO_ROOT / "benchmarks/rust/grade.py"

sys.path.insert(0, str(REPO_ROOT / "benchmarks/rust"))
import grade as grade_mod  # noqa: E402


def test_regra_verde_publico_sozinho_nunca_aceita():
    pub = {"empty": False, "exit_code": 0, "seconds": 1.0, "timeout": False, "error": None}
    assert grade_mod.merge(pub, None)[0] == "indeterminado"
    assert grade_mod.merge(pub, {**pub})[0] == "accepted"


def test_regra_portas_de_falha():
    ok = {"empty": False, "exit_code": 0, "seconds": 1.0, "timeout": False, "error": None}
    assert grade_mod.merge({"empty": True, "exit_code": None, "seconds": 0.0,
                            "timeout": False, "error": None}, None)[0] == "rejected"
    assert grade_mod.merge({**ok, "exit_code": 1}, {**ok})[0:2] == ("rejected", "patch_fault")
    assert grade_mod.merge(ok, {**ok, "exit_code": 1})[0:2] == ("rejected", "patch_fault")
    assert grade_mod.merge(ok, {**ok, "exit_code": 1})[2].startswith("aceite privado reprovou")
    assert grade_mod.merge({**ok, "exit_code": 3}, {**ok})[0] == "indeterminado"
    assert grade_mod.merge({**ok, "timeout": True}, {**ok})[0] == "indeterminado"
    assert grade_mod.merge(ok, {**ok, "exit_code": 3})[0] == "indeterminado"


@pytest.fixture()
def minibase(tmp_path: Path) -> Path:
    base = tmp_path / "base"
    base.mkdir()
    (base / "file.txt").write_text("a\n")
    for cmd in (["git", "init", "-q"], ["git", "add", "-A"],
                ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "b"]):
        subprocess.run(cmd, cwd=base, check=True, stdout=subprocess.DEVNULL)
    return base


PATCH_B = ("diff --git a/file.txt b/file.txt\n--- a/file.txt\n+++ b/file.txt\n"
           "@@ -1 +1 @@\n-a\n+b\n")


def make_attempt(tmp_path: Path, name: str, patch: bytes) -> Path:
    att = tmp_path / name
    att.mkdir()
    (att / "manifest.json").write_text(json.dumps(
        {"task": {"id": "t1"}, "patch": {"file": "attempt.patch"}}))
    (att / "attempt.patch").write_text(patch.decode() if isinstance(patch, bytes) else patch)
    return att


def make_tasks(tmp_path: Path, command: list) -> Path:
    p = tmp_path / "tasks.json"
    p.write_text(json.dumps({"schema": "atlas-tasks/2", "platform": "t", "tasks": [{
        "id": "t1", "split": "piloto", "category": "bug_local", "statement": "troque a por b",
        "base_sha": "0" * 40, "test_command": command, "timeout_s": 60,
        "allowed_paths": ["file.txt"], "immutable_paths": [],
        "origin": "fixture", "contamination_risk": "baixo", "contamination_note": "fixture"}]}))
    return p


def make_priv_stub(tmp_path: Path) -> Path:
    stub = tmp_path / "priv-stub.sh"
    stub.write_text("#!/bin/bash\nexit ${PRIVATE_EXIT:-0}\n")
    stub.chmod(0o755)
    return stub


PASS_CMD = [sys.executable, "-c",
            "import sys,pathlib; sys.exit(0 if pathlib.Path('file.txt').read_text().strip()=='b' else 1)"]


def run_grade(attempt: Path, tasks: Path, base: Path, out: Path,
              stub: Path | None = None, scripts: Path | None = None) -> tuple[int, dict]:
    cmd = [sys.executable, str(GRADE), "--attempt", str(attempt), "--tasks", str(tasks),
           "--acceptance-repo", str(base), "--out", str(out)]
    if scripts is not None:
        cmd += ["--acceptance-scripts", str(scripts)]
    if stub is not None:
        cmd += ["--private-java", str(stub), "--private-runner", str(stub)]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    assert proc.returncode == 0, proc.stdout
    return proc.returncode, json.loads(out.read_text())


def test_grade_aceita_so_com_os_dois_verdes(minibase, tmp_path):
    tasks = make_tasks(tmp_path, PASS_CMD)
    stub = make_priv_stub(tmp_path)
    att = make_attempt(tmp_path, "att", PATCH_B.encode())
    _, g = run_grade(att, tasks, minibase, tmp_path / "g.json", stub)
    assert g["final"] == "accepted" and g["failure_class"] is None
    assert g["public"]["exit_code"] == 0 and g["private"]["exit_code"] == 0


def test_grade_reprova_no_gate_privado(minibase, tmp_path, monkeypatch):
    monkeypatch.setenv("PRIVATE_EXIT", "1")
    tasks = make_tasks(tmp_path, PASS_CMD)
    stub = make_priv_stub(tmp_path)
    att = make_attempt(tmp_path, "att", PATCH_B.encode())
    _, g = run_grade(att, tasks, minibase, tmp_path / "g.json", stub)
    assert g["final"] == "rejected" and g["failure_class"] == "patch_fault"
    assert "privado" in g["reason"]


def test_grade_sem_privado_e_indeterminado_e_vazio_rejeitado(minibase, tmp_path):
    tasks = make_tasks(tmp_path, PASS_CMD)
    att = make_attempt(tmp_path, "att", PATCH_B.encode())
    _, g = run_grade(att, tasks, minibase, tmp_path / "g.json")
    assert g["final"] == "indeterminado"
    att0 = make_attempt(tmp_path, "att0", b"")
    _, g0 = run_grade(att0, tasks, minibase, tmp_path / "g0.json")
    assert g0["final"] == "rejected" and g0["public"]["empty"] is True


def test_grade_instala_harness_relativo_no_clone(minibase, tmp_path):
    scripts = tmp_path / "scripts"
    (scripts / "stage").mkdir(parents=True)
    (scripts / "stage" / "check.sh").write_text("#!/bin/bash\nexit 0\n")
    tasks = make_tasks(tmp_path, ["bash", "atlas-accept/stage/check.sh", "t1"])
    att = make_attempt(tmp_path, "att", PATCH_B.encode())
    _, g = run_grade(att, tasks, minibase, tmp_path / "g.json",
                     make_priv_stub(tmp_path), scripts)
    assert g["final"] == "accepted", g
    assert (g["public"]["acceptance_scripts_sha256"] or "").startswith("sha256:")


def test_grade_harness_ausente_bloqueia_sem_culpar_patch(minibase, tmp_path):
    tasks = make_tasks(tmp_path, ["bash", "atlas-accept/falta.sh", "t1"])
    att = make_attempt(tmp_path, "att", PATCH_B.encode())
    _, g = run_grade(att, tasks, minibase, tmp_path / "g.json",
                     make_priv_stub(tmp_path))
    assert g["final"] == "indeterminado"
    assert g["failure_class"] == "environmental"
    assert "harness ausente" in g["public"]["error"]
    assert "não do patch" in g["public"]["error"]


def test_grade_registra_contagens_sem_conteudo_de_caso(minibase, tmp_path):
    scripts = tmp_path / "scripts"
    (scripts / "atlas-data").mkdir(parents=True)
    (scripts / "atlas-data" / "check.sh").write_text(
        "#!/bin/bash\necho 'falso expected=<x> actual=<y>'\necho 'Harness: 3/5 passed'\nexit 0\n")
    tasks = make_tasks(tmp_path, ["bash", "atlas-accept/atlas-data/check.sh", "t1"])
    att = make_attempt(tmp_path, "att", PATCH_B.encode())
    _, g = run_grade(att, tasks, minibase, tmp_path / "g.json",
                     make_priv_stub(tmp_path), scripts)
    assert (g["public"]["cases_passed"], g["public"]["cases_total"]) == (3, 5)
    blob = json.dumps(g, ensure_ascii=False)
    assert "expected=<x>" not in blob


def test_grade_gate_privado_reserva_escopo_ao_revisor():
    ok = {"empty": False, "exit_code": 0, "seconds": 1.0, "timeout": False, "error": None}
    final, cls, reason = grade_mod.merge(ok, {**ok, "exit_code": 1})
    assert (final, cls) == ("rejected", "patch_fault")
    assert "revisor" in reason


def test_grade_nao_suja_a_base_do_operador(minibase, tmp_path):
    before = subprocess.run(["git", "-C", str(minibase), "rev-parse", "HEAD"],
                            stdout=subprocess.PIPE).stdout
    tasks = make_tasks(tmp_path, PASS_CMD)
    att = make_attempt(tmp_path, "att", PATCH_B.encode())
    run_grade(att, tasks, minibase, tmp_path / "g.json", make_priv_stub(tmp_path))
    after = subprocess.run(["git", "-C", str(minibase), "rev-parse", "HEAD"],
                           stdout=subprocess.PIPE).stdout
    assert before == after
    assert subprocess.run(["git", "-C", str(minibase), "status", "--porcelain"],
                          stdout=subprocess.PIPE).stdout == b""


SIGA = REPO_ROOT.parent / "siga"


@pytest.mark.skipif(not (SIGA / "siga-base").exists(), reason="checkout SIGA ausente")
def test_private3_compila_e_roda_casos_sinteticos(tmp_path):
    # Fiação real do runner privado: clone fresco, .java sintético em tmp, javac de verdade.
    base = tmp_path / "base"
    subprocess.run(["git", "clone", "-q", str(SIGA), str(base)], check=True)
    priv = tmp_path / "PrivSint.java"
    priv.write_text("import br.gov.jfrj.siga.base.util.Texto;\n"
                    "public class PrivSint {\n"
                    "  public static void main(String[] a) {\n"
                    "    if (!\"a\".equals(Texto.removeAcentoHTML(\"&agrave;\"))) System.exit(1);\n"
                    "    System.out.println(\"PrivSint: 1/1 passed\");\n"
                    "  }\n}\n")
    build = tmp_path / "pb"
    build.mkdir()
    proc = subprocess.run(
        ["bash", str(REPO_ROOT / "benchmarks/siga/rust/acceptance/run-private3.sh"),
         "SIGA-REAL-20"], cwd=str(base), stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True,
        env={"PATH": "/data/dev/java/candidates/java/current/bin:/usr/bin:/bin",
             "PRIVATE_JAVA": str(priv),
             "PRIVATE_BUILD": str(build), "HOME": str(tmp_path),
             "M2_REPO": str(Path.home() / ".m2/repository")})
    assert proc.returncode == 1, proc.stdout
    # Base pristina (vermelha): o caso sintetico reprova com exit 1 — a fiacao
    # compilou, executou e detectou o vermelho.
