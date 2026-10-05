# SPDX-License-Identifier: Apache-2.0
"""Guarda o congelamento operacional da rodada smoke (R3/EXP01).

O que estes testes garantem, e por que:

- **12 arms = 4 tarefas × 3 braços × 1 repetição**, tarefas do split smoke do
  conjunto selado. Se alguém trocar tarefa, braço ou repetição, o teste cai.
- **Tetos e budget iguais ao pré-registro e aos defaults do executor.** Se o
  loop mudar sem atualizar o freeze (ou vice-versa), o teste cai.
- **Plano de ordem segue a regra documentada** (rotação por tarefa), 4/4/4 por
  braço, numeração 1..12. Ordem editada à mão sem regra quebra o teste.
- **P1/P2 continuam nulos com motivo.** Preencher modelo/chave/teto sem
  provisionamento real seria fabricar evidência; o teste exige null+motivo
  até o desbloqueio.
- **A rodada não começou.** Se existir qualquer `runs_*.jsonl` no diretório do
  plano, o teste cai: freeze não é resultado.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "benchmarks/rust"))

import real_executor  # noqa: E402

FREEZE = REPO_ROOT / "research/rust/R3_SMOKE_FREEZE.json"
PLAN = REPO_ROOT / "experiments/rust/siga/2026-10-05-r3-smoke-plan/run_plan.json"
SETS = REPO_ROOT / "benchmarks/siga/rust/pilot16.tasks.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_freeze_tem_12_arms_e_tarefas_do_smoke_selado():
    freeze = json.loads(FREEZE.read_text())
    assert freeze["schema"] == "atlas-r3-freeze/1"
    assert freeze["design"]["runs_per_trail"] == 12
    assert freeze["design"]["conditions"] == ["BASE", "LEX-RS", "CTX-RS"]
    assert freeze["design"]["reps"] == 1
    sealed = json.loads(SETS.read_text())
    smoke = [t["id"] for t in sealed["tasks"] if t["split"] == "smoke"]
    assert freeze["design"]["tasks_per_trail"] == smoke
    assert len(smoke) == 4
    for trail, ref in (("siga", freeze["task_sets"]["siga"]),):
        assert sha256_file(REPO_ROOT / ref["file"]) == ref["sha256"], trail


def test_tetos_iguais_ao_pre_reg_e_ao_executor():
    freeze = json.loads(FREEZE.read_text())
    ceilings = freeze["design"]["ceilings"]
    assert ceilings == {"wall_s": 1800, "model_turns": 40, "tool_calls": 100}
    assert freeze["design"]["output_budget_tokens"] == 2000
    assert real_executor.DEFAULT_MAX_TOKENS == 2000
    assert real_executor.DEFAULT_MAX_TURNS == 40
    assert real_executor.DEFAULT_MAX_TOOL_CALLS == 100
    assert list(real_executor.FIXED_EXECUTOR_TOOLS) == ["shell", "read", "write"]
    assert (REPO_ROOT / freeze["executor"]["file"]).exists()


def test_p1_p2_nulos_com_motivo():
    freeze = json.loads(FREEZE.read_text())
    pending = freeze["pending_P1_P2"]
    assert pending["model"] == {"provider": None, "id": None, "version": None,
                                "reason": pending["model"]["reason"]}
    assert pending["model"]["reason"].strip() != ""
    assert pending["api_key"] == {"present": False, "reason": pending["api_key"]["reason"]}
    assert pending["api_key"]["reason"].strip() != ""
    assert pending["spending_cap"]["amount"] is None
    assert pending["spending_cap"]["reason"].strip() != ""
    assert pending["prices"]["file"] is None
    assert pending["prices"]["reason"].strip() != ""


def test_plano_de_ordem_segue_a_regra_e_nao_rodou():
    plan = json.loads(PLAN.read_text())
    assert plan["schema"] == "atlas-run-plan/1"
    assert plan["runs"] == 12
    arms = plan["arms"]
    assert [a["arm"] for a in arms] == list(range(1, 13))
    rots = [["BASE", "LEX-RS", "CTX-RS"], ["LEX-RS", "CTX-RS", "BASE"],
            ["CTX-RS", "BASE", "LEX-RS"]]
    tasks = ["SIGA-REAL-01", "SIGA-REAL-02", "SIGA-REAL-03", "SIGA-REAL-04"]
    expected = []
    for i, tid in enumerate(tasks):
        for cond in rots[i % 3]:
            expected.append((tid, cond))
    assert [(a["task"], a["condition"]) for a in arms] == expected
    from collections import Counter
    assert Counter(a["condition"] for a in arms) == {"BASE": 4, "LEX-RS": 4, "CTX-RS": 4}
    assert list(PLAN.parent.glob("runs_*.jsonl")) == [], "a rodada não começou"
