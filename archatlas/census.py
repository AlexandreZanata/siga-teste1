# SPDX-License-Identifier: Apache-2.0
"""Censo determinístico do dataset SIGA (F1). Só afirma o que leu do disco."""
from __future__ import annotations
import hashlib
import json
import pathlib

DATASET = pathlib.Path("/home/iiii/PESSOAL-PROJETOS-ALEXANDRE/siga")
MODULES = ["siga-ex", "siga-cp", "siga-base", "siga-ws", "siga-wf", "sigawf", "sigaex", "siga"]


def sha_of(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def census(dataset: pathlib.Path = DATASET) -> dict:
    mods = {}
    for mod in MODULES:
        p = dataset / mod
        if not p.exists():
            mods[mod] = {"exists": False}
            continue
        java = list(p.rglob("*.java"))
        jsp = list(p.rglob("*.jsp")) + list(p.rglob("*.tag"))
        n_lines = 0
        for f in java:
            try:
                with open(f, "rb") as fh:
                    n_lines += sum(1 for _ in fh)
            except OSError:
                pass
        mods[mod] = {"exists": True, "java_files": len(java), "jsp_tag": len(jsp), "java_loc": n_lines}
    return {"dataset": str(dataset), "modules": mods}
