from archatlas.config import REPO_ROOT, dataset_root
# SPDX-License-Identifier: Apache-2.0
"""F12 dogfooding: mesmo DB, Python (este repo) + Java (SIGA), sem path hardcoded."""
import pathlib

from archatlas.dataset import discover, extract_any
from archatlas.lexical import bm25_search, rebuild_lexical
from archatlas.query import find_symbol
from archatlas.store import index_discovered, open_db
from archatlas.verify import verify_symbol

ATLAS = REPO_ROOT / "archatlas"
SIGA_JAVA = dataset_root() / "siga-ex/src/main/java"


def test_discover_languages():
    langs = {l for _, l in discover(ATLAS)}
    assert "python" in langs
    langs_siga = {l for _, l in discover(SIGA_JAVA)}
    assert langs_siga == {"java"}


def test_dogfood_same_db(tmp_path):
    con = open_db(tmp_path / "d.sqlite")
    c1 = index_discovered(con, ATLAS, "dogfood")
    assert c1["langs"].get("python", 0) >= 10
    c2 = index_discovered(con, SIGA_JAVA, "e3be22828", limit=40)
    assert c2["langs"].get("java", 0) == 40
    rebuild_lexical(con)
    py = find_symbol(con, "build_capsule", exact=True)
    assert py and py[0]["file"].endswith("capsule.py")
    jv = find_symbol(con, "Documento", exact=True)
    assert jv and jv[0]["file"].endswith("Documento.java")
    syms = extract_any(ATLAS / "capsule.py", "python")
    assert syms
    for s in syms:
        ok, _ = verify_symbol(s)
        assert ok
    hits = bm25_search(con, "capsule", k=5)
    assert hits
