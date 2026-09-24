# SPDX-License-Identifier: Apache-2.0
"""Config F19: nenhum path de máquina no código. Dataset via env ARCHATLAS_DATASET."""
from __future__ import annotations
import os
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def dataset_root() -> pathlib.Path:
    env = os.environ.get("ARCHATLAS_DATASET")
    if env:
        return pathlib.Path(env)
    sib = REPO_ROOT.parent / "siga"
    if sib.is_dir():
        return sib
    raise RuntimeError("ARCHATLAS_DATASET não definido e ../siga não existe; "
                       "export ARCHATLAS_DATASET=/caminho/para/siga-doc")


def as_rel(path: str | pathlib.Path) -> str:
    """Caminho relativo ao dataset (portável); fora dele, devolve como está."""
    p = pathlib.Path(path)
    try:
        return str(p.relative_to(dataset_root()))
    except ValueError:
        return str(p)


def as_abs(rel: str | pathlib.Path) -> pathlib.Path:
    p = pathlib.Path(rel)
    return p if p.is_absolute() else dataset_root() / p
