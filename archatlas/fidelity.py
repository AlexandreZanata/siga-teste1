# SPDX-License-Identifier: Apache-2.0
"""Fidelidade F7: cobertura medida no disco (nunca estimada)."""
from __future__ import annotations
from archatlas.config import REPO_ROOT, dataset_root
import pathlib
import time

from archatlas.extract import extract_java_symbols

DATASET = dataset_root()
SHA = "e3be22828f787cbe71b339aecb7a7bf569099803"


def measure_scope(java_root: pathlib.Path) -> dict:
    files = sorted(java_root.rglob("*.java"))
    t0 = time.perf_counter()
    zero, nsym, zero_files = 0, 0, []
    for f in files:
        s = extract_java_symbols(f)
        nsym += len(s)
        if not s:
            zero += 1
            zero_files.append(str(f))
    return {"files": len(files), "unresolved": zero,
            "unresolved_rate": zero / max(1, len(files)), "symbols": nsym,
            "zero_files": zero_files, "seconds": round(time.perf_counter() - t0, 2)}


def measure_jsp(root: pathlib.Path) -> dict:
    files = sorted(root.rglob("*.jsp"))
    return {"files": len(files), "unresolved": len(files), "unresolved_rate": 1.0,
            "note": "extrator v0.1 é Java-only; JSPs declarados fora de cobertura (sem invenção)"}
