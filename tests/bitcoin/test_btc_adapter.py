# SPDX-License-Identifier: Apache-2.0
"""BTC-P2: adaptador lexical C++ — fixtures sintéticas próprias, sem LLM, sem dataset."""
import hashlib
import pathlib

import pytest

from archatlas.bitcoin.cpp_lex import (discover_cpp, extract_cpp_lexical,
                                       file_record, verify_fact)
from archatlas.dataset import extract_py

VALIDATION_CPP = b"""#include "validation.h"
#include <map>
#include <vector>
#if __has_include(<string_view>)
// palavras 'include/included' em comentario nao sao diretivas nem skipped
#endif
bool CheckTransaction() {
    return true;
}
"""
MALFORMED_CPP = b'#include "validation.h"\n#include "oops\n#include <map>\n'


def _tree(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "validation.cpp").write_bytes(VALIDATION_CPP)
    (src / "validation.h").write_bytes(b"#pragma once\nbool CheckTransaction();\n")
    (src / "broken.cpp").write_bytes(MALFORMED_CPP)
    (tmp_path / "wallet.py").write_bytes(b"class Wallet:\n    def balance(self):\n        return 0\n")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "evil.cpp").write_bytes(b"#include <x>\n")
    return tmp_path


def test_discover_requires_explicit_root_and_ignores_excluded(tmp_path):
    with pytest.raises(ValueError):
        discover_cpp(None)
    with pytest.raises(FileNotFoundError):
        discover_cpp(tmp_path / "nope")
    found = discover_cpp(_tree(tmp_path))
    names = sorted(p.name for p in found)
    assert names == ["broken.cpp", "validation.cpp", "validation.h"]
    assert not any(".git" in str(p) for p in found)


def test_discover_never_falls_back_to_env_dataset(tmp_path, monkeypatch):
    monkeypatch.setenv("ARCHATLAS_DATASET", "/inexistente/siga")
    found = discover_cpp(_tree(tmp_path))
    assert len(found) == 3  # root explícito funciona; env ignorado, sem exceção mascarada


def test_extract_includes_verified_and_malformed_skipped_loudly(tmp_path):
    _tree(tmp_path)
    res = extract_cpp_lexical(tmp_path / "src" / "validation.cpp")
    assert res["schema"] == "btc-cpp-lex/1"
    assert res["skipped"] == []
    kinds = [(f["kind"], f["name"]) for f in res["facts"]]
    assert kinds[0][0] == "file"
    assert ("include", "validation.h") in kinds and ("include", "map") in kinds
    for f in res["facts"][1:]:
        line = (tmp_path / "src" / "validation.cpp").read_bytes().decode().splitlines()[f["line"] - 1]
        assert f["name"] in line  # nome literalmente na linha
        assert verify_fact(f) == (True, "ok")
    bad = extract_cpp_lexical(tmp_path / "src" / "broken.cpp")
    assert [f["name"] for f in bad["facts"][1:]] == ["validation.h", "map"]
    assert len(bad["skipped"]) == 1 and bad["skipped"][0]["line"] == 2


def test_file_record_hash_stable_and_change_detected(tmp_path):
    _tree(tmp_path)
    p = tmp_path / "src" / "validation.cpp"
    rec = file_record(p)
    assert rec["content_hash"] == hashlib.sha256(VALIDATION_CPP).hexdigest()
    assert verify_fact(rec) == (True, "ok")
    assert extract_cpp_lexical(p)["facts"][0] == rec  # determinismo
    p.write_bytes(p.read_bytes() + b"\n// touch\n")
    ok, msg = verify_fact(rec)
    assert ok is False and "divergiu" in msg
    p.unlink()
    ok, msg = verify_fact(rec)
    assert ok is False and "inexistente" in msg


def test_python_path_uses_identified_ast_parser(tmp_path):
    _tree(tmp_path)
    syms = extract_py(tmp_path / "wallet.py")
    by_name = {s["name"]: s for s in syms}
    assert by_name["Wallet"]["provenance"] == "ast-exact"
    assert by_name["balance"]["provenance"] == "ast-exact"
    for s in syms:
        assert verify_fact({**s, "file": str(tmp_path / "wallet.py")}) == (True, "ok")
