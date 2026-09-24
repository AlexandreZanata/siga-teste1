# SPDX-License-Identifier: Apache-2.0
"""Extrator determinístico v0.1 (stdlib-only). Emite só o que verificou em bytes reais."""
from __future__ import annotations
import hashlib
import pathlib
import re

CLASS_RE = re.compile(r"^\s*(?:public\s+|protected\s+|private\s+|abstract\s+|final\s+)*(class|interface|enum)\s+(\w+)", re.M)
METHOD_RE = re.compile(r"^\s*(?:public|protected|private|static|final|synchronized|abstract|native|\s)+\s*[\w<>\[\].,? ]+\s+(\w+)\s*\([^;]*\)\s*(?:throws\s+[\w., ]+)?\s*[{;]", re.M)


def extract_java_symbols(path: pathlib.Path) -> list[dict]:
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    chash = hashlib.sha256(raw).hexdigest()
    lines = text.splitlines()
    out: list[dict] = []
    for m in CLASS_RE.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        out.append({"kind": m.group(1), "name": m.group(2), "file": str(path),
                    "line": line, "content_hash": chash, "confidence": 1.0, "provenance": "ast-regex-exact"})
    for m in METHOD_RE.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        name = m.group(1)
        if name in {"if", "for", "while", "switch", "catch", "return", "new"}:
            continue
        snippet = lines[line - 1].strip()
        if name not in snippet:
            continue  # anti-falso-positivo: nome deve estar literalmente na linha
        out.append({"kind": "method", "name": name, "file": str(path),
                    "line": line, "content_hash": chash, "confidence": 0.9, "provenance": "ast-regex-candidate"})
    return out
