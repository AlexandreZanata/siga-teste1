# SPDX-License-Identifier: Apache-2.0
"""Verificador: re-lê o disco e confirma cada símbolo (100% evidência, 0 suposição)."""
from __future__ import annotations
import hashlib
import pathlib


def verify_symbol(sym: dict) -> tuple[bool, str]:
    p = pathlib.Path(sym["file"])
    if not p.exists():
        return False, "arquivo inexistente"
    raw = p.read_bytes()
    if hashlib.sha256(raw).hexdigest() != sym["content_hash"]:
        return False, "content_hash divergiu (arquivo mudou)"
    lines = raw.decode("utf-8", errors="replace").splitlines()
    if not (1 <= sym["line"] <= len(lines)):
        return False, "linha fora do intervalo"
    if sym["name"] not in lines[sym["line"] - 1]:
        return False, f"nome ausente na linha {sym['line']}"
    return True, "ok"
