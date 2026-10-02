# SPDX-License-Identifier: Apache-2.0
"""Guarda o selo do piloto de 16 (EXP02): uniao fiel, sem desvio, sem ouro.

O selo congela a composicao: qualquer edicao no conjunto, nos lotes ou nos
runners quebra estes testes e exige nova revisao registrada.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SEALED = REPO_ROOT / "benchmarks/siga/rust/pilot16.tasks.json"
SEAL = REPO_ROOT / "experiments/rust/siga/2026-10-02-exp02-seal/seal.json"
ACC = REPO_ROOT / "benchmarks/siga/rust/acceptance"
MEMBERS = {
    "benchmarks/siga/rust/smoke.tasks.json": ["SIGA-REAL-01", "SIGA-REAL-02", "SIGA-REAL-03", "SIGA-REAL-04"],
    "benchmarks/siga/rust/pilot.tasks.json": ["SIGA-REAL-05", "SIGA-REAL-06", "SIGA-REAL-07", "SIGA-REAL-08"],
    "benchmarks/siga/rust/pilot2.tasks.json": ["SIGA-REAL-09", "SIGA-REAL-10", "SIGA-REAL-11", "SIGA-REAL-12",
                                                "SIGA-REAL-13", "SIGA-REAL-14", "SIGA-REAL-15", "SIGA-REAL-16"],
}
BASE_SHA = "e3be22828f787cbe71b339aecb7a7bf569099803"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_selo_valida_limpo_balanceado_e_fechado():
    proc = subprocess.run(
        [sys.executable, "benchmarks/rust/eval.py", "validate", "--tasks", str(SEALED)],
        cwd=str(REPO_ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    assert proc.returncode == 0, proc.stdout.decode()
    body = json.loads(proc.stdout.decode())
    assert body["problems"] == [] and body["balanced"] is True and body["sealed"] is True
    assert body["tasks"] == 16
    assert body["categories"] == {"bug_local": 4, "entre_arquivos": 4,
                                  "testes_comportamento_de_api": 4,
                                  "configuracao_interface": 4}


def test_uniao_fiel_sem_reescrita():
    sealed = json.loads(SEALED.read_text())
    assert sealed["sealed"] is True and sealed["base_sha"] == BASE_SHA
    by_id = {}
    for rel, ids in MEMBERS.items():
        doc = json.loads((REPO_ROOT / rel).read_text())
        assert [t["id"] for t in doc["tasks"]] == ids
        for t in doc["tasks"]:
            by_id[t["id"]] = t
    assert [t["id"] for t in sealed["tasks"]] == [t for ids in MEMBERS.values() for t in ids]
    for t in sealed["tasks"]:
        assert t == by_id[t["id"]], f"tarefa reescrita no selo: {t['id']}"


def test_selo_trava_hashes_dos_lotes_e_dos_runners():
    seal = json.loads(SEAL.read_text())
    assert seal["set"]["sha256"] == sha256_file(SEALED)
    for rel, ids in MEMBERS.items():
        assert seal["members"][rel]["sha256"] == sha256_file(REPO_ROOT / rel)
        assert seal["members"][rel]["tasks"] == ids
    assert seal["acceptance"]["run_sh_sha256"] == sha256_file(ACC / "run.sh")
    assert seal["acceptance"]["run_pilot_sh_sha256"] == sha256_file(ACC / "run-pilot.sh")
    assert seal["acceptance"]["run_pilot2_sh_sha256"] == sha256_file(ACC / "run-pilot2.sh")
    assert seal["acceptance"]["harness_count"] == 16
    assert seal["contains_gold"] is False
    checkpoint = json.loads((REPO_ROOT / "benchmarks/siga/rust/pilot16-checkpoint.json").read_text())
    assert checkpoint["set"]["sha256"] == sha256_file(SEALED)
    assert checkpoint["contains_gold"] is False


def test_comandos_de_aceite_apontam_runners_congelados():
    sealed = json.loads(SEALED.read_text())
    runners = {"SIGA-REAL-01": "run.sh", "SIGA-REAL-05": "run-pilot.sh", "SIGA-REAL-09": "run-pilot2.sh"}
    for t in sealed["tasks"]:
        num = int(t["id"][-2:])
        expected = "run.sh" if num <= 4 else ("run-pilot.sh" if num <= 8 else "run-pilot2.sh")
        assert t["test_command"] == ["bash", f"atlas-accept/{expected}", t["id"]]
        assert (ACC / f"AtlasAccept{num:02d}.java").exists()
    assert set(runners.values()) == {"run.sh", "run-pilot.sh", "run-pilot2.sh"}
