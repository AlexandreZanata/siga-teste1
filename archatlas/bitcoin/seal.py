# SPDX-License-Identifier: Apache-2.0
"""Selamento e cegamento do confirmatório BTC-P5 (sem dataset, sem modelo, sem custodiante real).

- `seal_manifest`: congela tarefas/condições/versões num manifesto com hash sha256.
  Hash registra congelamento; NÃO controla acesso sozinho (custódia à parte).
- `blind_map`/`unblind`: IDs aleatórios por seed; `unblind` exige a chave do custodiante.
- `blind_package`: pacote do avaliador SÓ com tarefa, snapshot, patch e rubrica.
  Sem modelo/condição/custo/ordem. Puro e determinístico (stdlib-only).
"""
from __future__ import annotations
import copy
import hashlib
import json
import random

FORBIDDEN_IN_BLIND = {"model", "condition", "cost", "cost_total", "order",
                      "repetition", "tokenizer", "executor", "sha"}


def _canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")


def seal_manifest(tasks: list, conditions: list, repetitions: int, seed: int,
                  versions: dict) -> dict:
    """Congela o desenho. `tasks`: [{id, family, scope}] — sem soluções, sem ouro."""
    manifest = {"tasks": sorted(copy.deepcopy(tasks), key=lambda t: t["id"]),
                "conditions": list(conditions), "repetitions": repetitions,
                "seed": seed, "versions": dict(versions)}
    seal = hashlib.sha256(_canonical(manifest)).hexdigest()
    return {"manifest": manifest, "seal": seal, "schema": "btc-seal/1"}


def verify_seal(sealed: dict) -> bool:
    """True sse o conteúdo recomputado reproduz o selo."""
    if set(sealed) != {"manifest", "seal", "schema"} or sealed.get("schema") != "btc-seal/1":
        return False
    return hashlib.sha256(_canonical(sealed["manifest"])).hexdigest() == sealed["seal"]


def blind_map(patch_ids: list, seed: int) -> tuple[dict, dict]:
    """Embaralha IDs de patch -> IDs cegos. Retorna (mapa, chave do custodiante)."""
    ids = sorted(set(patch_ids))
    blind = [f"Blind-{i:03d}" for i in range(1, len(ids) + 1)]
    random.Random(seed).shuffle(blind)
    mapping = dict(zip(ids, blind))
    return mapping, dict(mapping)


def unblind(blind_id: str, key: dict | None) -> str:
    """Revela o ID original. Sem chave (custodiante), levanta — nunca adivinha."""
    if not key:
        raise PermissionError("unblind exige a chave do custodiante")
    rev = {v: k for k, v in key.items()}
    if blind_id not in rev:
        raise KeyError(f"ID cego desconhecido: {blind_id}")
    return rev[blind_id]


def blind_package(task: dict, snapshot_ref: str, patch: str, rubric: dict) -> dict:
    """Pacote do avaliador: tarefa, snapshot, patch e rubrica. Nada mais."""
    pkg = {"task": {"id": task["id"], "family": task.get("family"),
                    "scope": task.get("scope"), "problema": task.get("problema")},
           "snapshot_ref": snapshot_ref, "patch": patch, "rubric": dict(rubric)}
    assert not (set(pkg) & FORBIDDEN_IN_BLIND)
    return pkg
