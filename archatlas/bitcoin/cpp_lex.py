# SPDX-License-Identifier: Apache-2.0
"""Adaptador lexical C++ (BTC-P2, `btc-cpp-lex/1`). Somente leitura.

Emite só fatos verificados em texto: identidade do arquivo e diretivas
`#include` com verificação nome-na-linha. Nenhuma afirmação semântica
(overload, template, chamada virtual, alvo de macro, resolução de header).
Reuso publicado (só leitura): `archatlas.dataset.EXCLUDE_DIRS`,
`archatlas.verify.verify_symbol`.
"""
from __future__ import annotations
import hashlib
import pathlib
import re

from archatlas.dataset import EXCLUDE_DIRS
from archatlas.verify import verify_symbol

SCHEMA_VERSION = "btc-cpp-lex/1"
CORE_SHA = "e6fde134f7da0d3616d90c40232d9ebe2ed9f033"

CPP_EXTS = {".c", ".h", ".hpp", ".cpp"}
INCLUDE_RE = re.compile(r"#[ \t]*include[ \t]*([\"<])([^\">\s]+)[\">]")


def discover_cpp(root: pathlib.Path | None) -> list[pathlib.Path]:
    """Lista arquivos C++ sob `root` explícito. Nunca usa dataset default."""
    if root is None:
        raise ValueError("discover_cpp exige root explícito; sem fallback para dataset SIGA")
    root = pathlib.Path(root)
    if not root.is_dir():
        raise FileNotFoundError(f"root inexistente: {root}")
    out = []
    for f in sorted(root.rglob("*")):
        if not f.is_file() or f.suffix not in CPP_EXTS:
            continue
        if EXCLUDE_DIRS & set(f.parts):
            continue
        out.append(f)
    return out


def file_record(path: pathlib.Path) -> dict:
    raw = pathlib.Path(path).read_bytes()
    return {"kind": "file", "name": pathlib.Path(path).name, "file": str(path),
            "line": 1, "content_hash": hashlib.sha256(raw).hexdigest(),
            "lines": len(raw.decode("utf-8", errors="replace").splitlines()),
            "provenance": "file-identity", "confidence": 1.0}


def extract_cpp_lexical(path: pathlib.Path) -> dict:
    """Fato-arquivo + fatos-`include` verificados. Malformados vão a `skipped`."""
    path = pathlib.Path(path)
    raw = path.read_bytes()
    chash = hashlib.sha256(raw).hexdigest()
    lines = raw.decode("utf-8", errors="replace").splitlines()
    facts = [file_record(path)]
    skipped = []
    for i, text in enumerate(lines, start=1):
        if "include" not in text:
            continue
        m = INCLUDE_RE.search(text)
        if not m:
            skipped.append({"line": i, "text": text.strip()[:120],
                            "reason": "diretiva include malformada"})
            continue
        target = m.group(2)
        if target not in text:
            skipped.append({"line": i, "text": text.strip()[:120],
                            "reason": "alvo ausente na linha"})
            continue
        facts.append({"kind": "include", "name": target, "file": str(path), "line": i,
                      "content_hash": chash, "provenance": "lexical-verified",
                      "confidence": 0.6})
    return {"facts": facts, "skipped": skipped, "schema": SCHEMA_VERSION}


def verify_fact(fact: dict) -> tuple[bool, str]:
    """Verifica um fato contra o disco. Falha nunca é silenciosa."""
    if fact.get("kind") == "file":
        p = pathlib.Path(fact["file"])
        if not p.exists():
            return False, "arquivo inexistente"
        if hashlib.sha256(p.read_bytes()).hexdigest() != fact["content_hash"]:
            return False, "content_hash divergiu (arquivo mudou)"
        return True, "ok"
    return verify_symbol(fact)
