# SPDX-License-Identifier: Apache-2.0
"""Guarda o selo do piloto Bitcoin de 16 (EXP02 completa): uniao fiel, sem desvio, sem ouro.

O selo congela a composicao: qualquer edicao no conjunto, nos lotes ou no
runner quebra estes testes e exige nova revisao registrada.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SEALED = REPO_ROOT / "benchmarks" / "bitcoin" / "rust" / "pilot16.tasks.json"
SEAL = REPO_ROOT / "experiments" / "bitcoin" / "rust" / "2026-10-05-btc-exp02-seal" / "seal.json"
ACC = REPO_ROOT / "benchmarks" / "bitcoin" / "rust" / "acceptance"
MEMBERS = {
    "benchmarks/bitcoin/rust/smoke.tasks.json": ["BTC-REAL-01", "BTC-REAL-02", "BTC-REAL-03", "BTC-REAL-04"],
    "benchmarks/bitcoin/rust/pilot.tasks.json": ["BTC-REAL-05", "BTC-REAL-06", "BTC-REAL-07", "BTC-REAL-08"],
    "benchmarks/bitcoin/rust/pilot2.tasks.json": ["BTC-REAL-09", "BTC-REAL-10", "BTC-REAL-11", "BTC-REAL-12"],
    "benchmarks/bitcoin/rust/pilot3.tasks.json": ["BTC-REAL-13", "BTC-REAL-14", "BTC-REAL-15", "BTC-REAL-16"],
}
BASE_SHA = "9be056a8a72b624dae9623b2f7bded92c2a21c91"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_selo_fechado_balanceado_16():
    sealed = json.loads(SEALED.read_text())
    assert sealed["schema"] == "atlas-tasks/2"
    assert sealed["platform"] == "bitcoin"
    assert sealed["sealed"] is True
    assert sealed["base_sha"] == BASE_SHA
    assert len(sealed["tasks"]) == 16
    from collections import Counter
    assert Counter(t["category"] for t in sealed["tasks"]) == Counter({
        "bug_local": 4, "entre_arquivos": 4,
        "testes_comportamento_de_api": 4, "configuracao_interface": 4})


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


def test_selo_trava_hashes_dos_lotes_e_do_runner():
    seal = json.loads(SEAL.read_text())
    assert seal["set"]["sha256"] == sha256_file(SEALED)
    for rel, ids in MEMBERS.items():
        assert seal["members"][rel]["sha256"] == sha256_file(REPO_ROOT / rel)
        assert seal["members"][rel]["tasks"] == ids
    assert seal["acceptance"]["run_sh_sha256"] == sha256_file(ACC / "run.sh")
    assert seal["acceptance"]["harness_count"] == 16
    assert seal["contains_gold"] is False
    checkpoint = json.loads((REPO_ROOT / "benchmarks" / "bitcoin" / "rust" / "pilot16-checkpoint.json").read_text())
    assert checkpoint["set"]["sha256"] == sha256_file(SEALED)
    assert checkpoint["contains_gold"] is False


def test_comandos_de_aceite_apontam_runner_congelado():
    sealed = json.loads(SEALED.read_text())
    for t in sealed["tasks"]:
        num = int(t["id"][-2:])
        assert t["test_command"] == ["bash", "atlas-accept/run.sh", t["id"]]
        assert (ACC / f"accept_b{num:02d}.py").exists()
