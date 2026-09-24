# SPDX-License-Identifier: Apache-2.0
"""Dataset paramétrico F12: qualquer repo, discovery por extensão, sem paths hardcoded."""
from __future__ import annotations
import ast
import hashlib
import pathlib

EXT_MAP = {".java": "java", ".py": "python", ".jsp": "jsp", ".tag": "jsp",
           ".c": "cpp", ".h": "cpp", ".hpp": "cpp", ".cpp": "cpp", ".js": "js", ".ts": "js"}


EXCLUDE_DIRS = {".git", ".venv", "venv", ".tox", "node_modules", "__pycache__", "target", "build"}


def discover(root: pathlib.Path) -> list[tuple[pathlib.Path, str]]:
    out = []
    for f in sorted(root.rglob("*")):
        if f.is_file() and f.suffix in EXT_MAP and not (EXCLUDE_DIRS & set(f.parts)):
            out.append((f, EXT_MAP[f.suffix]))
    return out


def extract_py(path: pathlib.Path) -> list[dict]:
    raw = pathlib.Path(path).read_bytes()
    text = raw.decode("utf-8", errors="replace")
    chash = hashlib.sha256(raw).hexdigest()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    lines = text.splitlines()
    out = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            kind = "class" if isinstance(node, ast.ClassDef) else "function"
            name = node.name
            line = node.lineno
            if name not in lines[line - 1]:
                continue  # anti-falso-positivo
            out.append({"kind": kind, "name": name, "file": str(path), "line": line,
                        "content_hash": chash, "confidence": 1.0, "provenance": "ast-exact"})
    return out


def extract_any(path: pathlib.Path, lang: str) -> list[dict]:
    if lang == "java":
        from archatlas.extract import extract_java_symbols
        return extract_java_symbols(path)
    if lang == "python":
        return extract_py(path)
    if lang == "jsp":
        from archatlas.jsp import extract_jsp
        return extract_jsp(path)
    return []
