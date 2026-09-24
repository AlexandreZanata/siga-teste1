# SPDX-License-Identifier: Apache-2.0
"""Call graph F9 (candidate, 0.6): método atual + `nome(` verificado na linha real."""
from __future__ import annotations
import pathlib
import re

from archatlas.extract import METHOD_RE

CALL_RE = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
SKIP = {"if", "for", "while", "switch", "catch", "return", "new", "super", "this", "class",
        "try", "finally", "throw", "throws", "assert", "synchronized", "else", "do"}


def extract_calls(path: pathlib.Path) -> list[dict]:
    lines = pathlib.Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    method_at = {}
    for m in METHOD_RE.finditer("\n".join(lines)):
        method_at[m.start()] = m.group(1)
    text = "\n".join(lines)
    bounds = sorted(method_at)
    out: list[dict] = []
    for i, line in enumerate(lines, 1):
        off = sum(len(l) + 1 for l in lines[:i - 1])
        caller = next((method_at[b] for b in reversed(bounds) if b <= off), None)
        if not caller:
            continue
        for m in CALL_RE.finditer(line.split("//")[0]):
            callee = m.group(1)
            if callee in SKIP or callee == caller:
                continue
            out.append({"caller": caller, "callee": callee, "file": str(path), "line": i,
                        "confidence": 0.6, "provenance": "call-regex-candidate"})
    return out
