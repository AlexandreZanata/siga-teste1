# SPDX-License-Identifier: Apache-2.0
"""JSP lexer F9: página + includes resolvidos no disco (nada inventado)."""
from __future__ import annotations
import hashlib
import pathlib
import re

INC_RE = re.compile(r"""<%@\s*include\s+file\s*=\s*["']([^"']+)["']|<jsp:include\s+page\s*=\s*["']([^"']+)["']|<c:import\s+url\s*=\s*["']([^"']+)["']""")
TAGLIB_RE = re.compile(r"""<%@\s*taglib\s+uri\s*=\s*["']([^"']+)["']""")


def extract_jsp(path: pathlib.Path) -> list[dict]:
    raw = pathlib.Path(path).read_bytes()
    text = raw.decode("utf-8", errors="replace")
    chash = hashlib.sha256(raw).hexdigest()
    out = [{"kind": "page", "name": pathlib.Path(path).stem, "file": str(path), "line": 1,
            "content_hash": chash, "confidence": 1.0, "provenance": "jsp-file"}]
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        for m in INC_RE.finditer(line):
            target = next(g for g in m.groups() if g)
            resolved = (pathlib.Path(path).parent / target).resolve()
            ok = resolved.exists()
            out.append({"kind": "include", "name": target, "file": str(path), "line": i,
                        "content_hash": chash, "confidence": 1.0 if ok else 0.5,
                        "provenance": "jsp-include-exact" if ok else "jsp-include-unresolved",
                        "resolved": str(resolved) if ok else None})
        for m in TAGLIB_RE.finditer(line):
            out.append({"kind": "taglib", "name": m.group(1), "file": str(path), "line": i,
                        "content_hash": chash, "confidence": 0.8, "provenance": "jsp-taglib"})
    return out
