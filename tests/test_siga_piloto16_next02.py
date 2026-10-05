# SPDX-License-Identifier: Apache-2.0
"""Guarda o piloto corrigido (NEXT-02): 16 piloto exclusivas, smoke separado.

O selo conserta o desenho (4 smoke + 16 piloto) sem reescrever história: o
inventário antigo fica preservado e este teste trava o novo. Qualquer edição no
conjunto, no lote ou nos runners quebra estes testes e exige nova revisão.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXED = REPO_ROOT / "benchmarks/siga/rust/piloto16.tasks.json"
SEAL = REPO_ROOT / "experiments/rust/siga/2026-10-05-next02-pilot-seal/seal.json"
ACC = REPO_ROOT / "benchmarks/siga/rust/acceptance"
SMOKE = REPO_ROOT / "benchmarks/siga/rust/smoke.tasks.json"
OLD_SEALED = REPO_ROOT / "benchmarks/siga/rust/pilot16.tasks.json"
BASE_SHA = "e3be22828f787cbe71b339aecb7a7bf569099803"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_piloto_valida_limpo_balanceado_e_fechado_por_split():
    proc = subprocess.run(
        [sys.executable, "benchmarks/rust/eval.py", "validate", "--tasks", str(FIXED)],
        cwd=str(REPO_ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    assert proc.returncode == 0, proc.stdout.decode()
    body = json.loads(proc.stdout.decode())
    assert body["problems"] == [] and body["balanced"] is True and body["sealed"] is True
    assert body["tasks"] == 16
    assert body["categories"] == {"bug_local": 4, "entre_arquivos": 4,
                                  "testes_comportamento_de_api": 4,
                                  "configuracao_interface": 4}
    fixed = json.loads(FIXED.read_text())
    assert {t["split"] for t in fixed["tasks"]} == {"piloto"}, \
        "piloto corrigido só tem split piloto — smoke mora em arquivo próprio"


def test_sem_sobreposicao_com_o_smoke():
    fixed_ids = [t["id"] for t in json.loads(FIXED.read_text())["tasks"]]
    smoke_ids = [t["id"] for t in json.loads(SMOKE.read_text())["tasks"]]
    assert len(smoke_ids) == 4
    assert set(fixed_ids) & set(smoke_ids) == set(), \
        "NEXT-02 exige IDs sem sobreposição entre smoke e piloto"
    assert fixed_ids == [f"SIGA-REAL-{n:02d}" for n in range(5, 21)]


def test_fiel_ao_inventario_antigo_mais_lote_novo():
    fixed = json.loads(FIXED.read_text())
    old = json.loads(OLD_SEALED.read_text())
    old_pilot = [t for t in old["tasks"] if t["split"] == "piloto"]
    assert len(old_pilot) == 12
    lot = json.loads((REPO_ROOT / "benchmarks/siga/rust/pilot3.tasks.json").read_text())
    assert [t["id"] for t in lot["tasks"]] == ["SIGA-REAL-17", "SIGA-REAL-18",
                                              "SIGA-REAL-19", "SIGA-REAL-20"]
    for t in old_pilot:
        back = next(x for x in fixed["tasks"] if x["id"] == t["id"])
        assert back == t, f"tarefa do inventario antigo reescrita: {t['id']}"
    for t in lot["tasks"]:
        back = next(x for x in fixed["tasks"] if x["id"] == t["id"])
        assert back == t, f"tarefa do lote novo divergente: {t['id']}"
    assert fixed["base_sha"] == BASE_SHA


def test_selo_trava_hashes_runners_e_checkpoint():
    seal = json.loads(SEAL.read_text())
    assert seal["set"]["sha256"] == sha256_file(FIXED)
    assert seal["smoke_separate"]["sha256"] == sha256_file(SMOKE)
    assert seal["smoke_separate"]["overlap_with_pilot"] == []
    assert seal["acceptance"]["run_pilot3_sh_sha256"] == sha256_file(ACC / "run-pilot3.sh")
    for n in (17, 18, 19, 20):
        assert seal["acceptance"]["harnesses_sha256"][f"AtlasAccept{n:02d}"] == \
            sha256_file(ACC / f"AtlasAccept{n:02d}.java")
    # Runners antigos seguem congelados (shas verificados pelos testes dos lotes).
    assert seal["acceptance"]["run_sh_sha256"] == sha256_file(ACC / "run.sh")
    assert seal["acceptance"]["run_pilot_sh_sha256"] == sha256_file(ACC / "run-pilot.sh")
    assert seal["acceptance"]["run_pilot2_sh_sha256"] == sha256_file(ACC / "run-pilot2.sh")
    assert seal["contains_gold"] is False
    checkpoint = json.loads((REPO_ROOT / "benchmarks/siga/rust/pilot3-checkpoint.json").read_text())
    assert checkpoint["pilot16_fixed"]["sha256"] == sha256_file(FIXED)
    assert checkpoint["contains_gold"] is False


def test_comandos_e_manifestos_do_lote_novo():
    fixed = json.loads(FIXED.read_text())
    for t in [x for x in fixed["tasks"] if int(x["id"][-2:]) >= 17]:
        assert t["test_command"] == ["bash", "atlas-accept/run-pilot3.sh", t["id"]]
        num = int(t["id"][-2:])
        assert (ACC / f"AtlasAccept{num:02d}.java").exists()
        man = json.loads((REPO_ROOT / "experiments/rust/siga/2026-10-05-exp02-pilot3-validation"
                          / "manifests" / f"{t['id']}.json").read_text())
        assert man["baseline"]["result"] == "red" and man["reference"]["result"] == "green"
        assert (REPO_ROOT / "experiments/rust/siga/2026-10-05-exp02-pilot3-validation"
                / man["baseline"]["log"]).exists()
        assert (REPO_ROOT / "experiments/rust/siga/2026-10-05-exp02-pilot3-validation"
                / man["reference"]["log"]).exists()


def test_pacote_publico_sem_campo_de_curadoria_nem_ouro():
    for rel in ("benchmarks/siga/rust/pilot3.tasks.json",
                "benchmarks/siga/rust/piloto16.tasks.json",
                "benchmarks/siga/rust/pilot3-checkpoint.json",
                "experiments/rust/siga/2026-10-05-next02-pilot-seal/seal.json"):
        body = (REPO_ROOT / rel).read_text()
        assert "curator_only" not in body
        assert "siga-a03-custody" not in body
    for rel in ("benchmarks/siga/rust/pilot3.tasks.json",
                "benchmarks/siga/rust/piloto16.tasks.json"):
        doc = json.loads((REPO_ROOT / rel).read_text())
        for t in doc["tasks"]:
            assert t["base_sha"] == BASE_SHA
            assert t["contamination_risk"] == "medio" and t["contamination_note"]
