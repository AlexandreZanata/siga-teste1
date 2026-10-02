# SPDX-License-Identifier: Apache-2.0
"""Guarda o conjunto piloto 05-08 da EXP02 sem exigir Java, Maven ou rede.

Espelha tests/test_siga_smoke_a03.py para o piloto: projecao sem ouro,
aceite realmente existente (run-pilot.sh; o run.sh do smoke segue congelado),
vermelho registrado e verde referenciado por hash, escopo verificavel com M5.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PILOT = REPO_ROOT / "benchmarks/siga/rust/pilot.tasks.json"
SMOKE = REPO_ROOT / "benchmarks/siga/rust/smoke.tasks.json"
ACC = REPO_ROOT / "benchmarks/siga/rust/acceptance"
VALID = REPO_ROOT / "experiments/rust/siga/2026-10-02-exp02-pilot-validation"

BASE_SHA = "e3be22828f787cbe71b339aecb7a7bf569099803"
EXPECTED = {
    "SIGA-REAL-05": {"cases": 10, "red": (3, 10), "green": "10/10"},
    "SIGA-REAL-06": {"cases": 10, "red": (5, 10), "green": "10/10"},
    "SIGA-REAL-07": {"cases": 12, "red": (4, 12), "green": "12/12"},
    "SIGA-REAL-08": {"cases": 9, "red": (5, 9), "green": "9/9"},
}
# Identificadores que so existem na referencia/custodia do piloto: se
# aparecerem no pacote publico, o ouro vazou para o corpus do executor.
GOLD_MARKERS = ("PrivateExtraPilot", "q05-diff-self", "q06-dollar-backslash",
                "q07-18278", "q08-dia-zero", "Codigo de via invalido",
                "quoteReplacement", "siga-a03-custody", '"curator_only"')


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_pilot() -> dict:
    doc = json.loads(PILOT.read_text())
    assert doc["schema"] == "atlas-tasks/2"
    return doc


def test_conjunto_valida_limpo_e_balanceado():
    proc = subprocess.run(
        [sys.executable, "benchmarks/rust/eval.py", "validate", "--tasks", str(PILOT)],
        cwd=str(REPO_ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    assert proc.returncode == 0, proc.stdout.decode()
    body = json.loads(proc.stdout.decode())
    assert body["problems"] == [] and body["balanced"] is True
    assert body["categories"] == {"bug_local": 1, "entre_arquivos": 1,
                                  "testes_comportamento_de_api": 1,
                                  "configuracao_interface": 1}
    doc = load_pilot()
    assert {t["id"] for t in doc["tasks"]} == set(EXPECTED)
    assert doc["sealed"] is False


def test_projecao_sem_ouro_nem_campo_de_curadoria():
    text = PILOT.read_text()
    for marker in GOLD_MARKERS:
        assert marker not in text, f"vazamento no conjunto público: {marker}"
    for task in load_pilot()["tasks"]:
        assert task["base_sha"] == BASE_SHA
        assert task["split"] == "piloto"
        assert task["test_command"][:2] == ["bash", "atlas-accept/run-pilot.sh"]
        assert task["test_command"][2] == task["id"]
        assert task["timeout_s"] == 600
        assert task["allowed_paths"], "escopo vazio não é verificável"
        assert task["immutable_paths"] is not None
        assert "atlas-accept/**" in task["immutable_paths"], "aceite sem M5 não é imutável"
        for path in task["allowed_paths"] + task["immutable_paths"]:
            assert not Path(path).is_absolute(), "caminho absoluto amarra o aceite à máquina"


def test_comando_de_aceite_existe_e_hashes_fecham():
    run_sh = ACC / "run-pilot.sh"
    assert run_sh.exists()
    set_man = json.loads((VALID / "manifests/set.json").read_text())
    assert set_man["set_sha256"] == sha256_file(PILOT)
    assert set_man["acceptance"]["run_pilot_sh_sha256"] == sha256_file(run_sh)
    doc = load_pilot()
    for task in doc["tasks"]:
        harness = ACC / f"AtlasAccept{task['id'][-2:]}.java"
        assert harness.exists(), f"harness ausente: {harness.name}"
        assert sha256_file(harness) == set_man["acceptance"]["harnesses"][task["id"]]
        body = run_sh.read_text()
        assert task["id"] in body, "run-pilot.sh não atende a tarefa declarada"


def test_manifestos_registram_vermelho_com_log_e_verde_com_hash():
    for task_id, exp in EXPECTED.items():
        man = json.loads((VALID / f"manifests/{task_id}.json").read_text())
        assert man["base_sha"] == BASE_SHA
        assert man["baseline"] == {"result": "red", "passed": f"{exp['red'][0]}/{exp['red'][1]}",
                                   "exit": 1, "log": f"logs/{task_id}-red.txt"}
        red = (VALID / f"logs/{task_id}-red.txt").read_text()
        summary = re.search(r"(\d+)/(\d+) passed", red)
        assert summary and (int(summary.group(1)), int(summary.group(2))) == exp["red"]
        assert "FAIL" in red, "vermelho sem caso FAIL não discrimina"
        assert man["reference"]["result"] == "green" and man["reference"]["exit"] == 0
        assert man["reference"]["passed"] == exp["green"]
        green = (VALID / f"logs/{task_id}-green.txt").read_text()
        assert f"{exp['green']} passed" in green and "FAIL" not in green
        assert len(man["reference"]["solution_sha256"]) == 64, "hash da referência ausente"
        assert man["harness"]["cases"] == exp["cases"]
        assert man["private_acceptance"] == {
            "red": "2/9", "green": "9/9",
            "note": "9 casos extras do avaliador em custodia; contagens publicadas, casos nao"}


def test_pacote_publico_sem_identificador_da_referencia():
    roots = [REPO_ROOT / "benchmarks/siga", VALID,
             REPO_ROOT / "research/siga/rust/CURADORIA_PILOTO.md"]
    hits = []
    paths = []
    for root in roots:
        if root.is_file():
            paths.append(root)
        else:
            paths.extend(sorted(root.rglob("*")))
    for path in paths:
        if path.is_file():
            if path.suffix in {".json", ".md", ".txt", ".sh", ".java"}:
                text = path.read_text(errors="replace")
                for marker in GOLD_MARKERS:
                    if marker in text:
                        rel = path.relative_to(REPO_ROOT) if REPO_ROOT in path.parents else path
                        hits.append(f"{rel}:{marker}")
    assert hits == [], f"ouro no pacote público: {hits}"


def test_smoke_congelado_e_checkpoint_do_piloto():
    # O runner do smoke nao pode mudar sob o piloto: a evidencia A03 o ancora.
    smoke_man = json.loads(
        (REPO_ROOT / "experiments/rust/siga/2026-10-02-a03-validation/manifests/set.json").read_text())
    assert smoke_man["acceptance"]["run_sh_sha256"] == sha256_file(ACC / "run.sh")
    checkpoint = json.loads((REPO_ROOT / "benchmarks/siga/rust/pilot-checkpoint.json").read_text())
    assert checkpoint["set"]["sha256"] == sha256_file(PILOT)
    assert checkpoint["acceptance"]["run_pilot_sh_sha256"] == sha256_file(ACC / "run-pilot.sh")
    assert checkpoint["contains_gold"] is False
    for task_id in EXPECTED:
        harness = ACC / f"AtlasAccept{task_id[-2:]}.java"
        assert checkpoint["acceptance"]["harnesses_sha256"][task_id] == sha256_file(harness)
