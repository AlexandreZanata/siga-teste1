# SPDX-License-Identifier: Apache-2.0
"""F9: JSP lexer resolve includes reais; calls têm caller+linha verificados; test-links espelham disco."""
import pathlib

from archatlas.calls import extract_calls
from archatlas.jsp import extract_jsp
from archatlas.testlinks import map_tests

DS = pathlib.Path("/home/iiii/PESSOAL-PROJETOS-ALEXANDRE/siga")
ANCHOR = DS / "siga-ex/src/main/java/br/gov/jfrj/siga/ex/ExMovimentacao.java"


def test_jsp_pages_and_resolved_includes():
    jsps = sorted((DS / "sigaex").rglob("*.jsp"))
    assert len(jsps) >= 500
    pages = unres = resolved = 0
    for f in jsps[:120]:
        syms = extract_jsp(f)
        assert syms and syms[0]["kind"] == "page"
        for s in syms[1:]:
            if s["kind"] == "include":
                if s["provenance"] == "jsp-include-exact":
                    resolved += 1
                    assert pathlib.Path(s["resolved"]).exists()
                else:
                    unres += 1
    assert resolved > 0  # há includes que resolvem de verdade no disco


def test_calls_verified():
    calls = extract_calls(ANCHOR)
    assert len(calls) > 10
    lines = ANCHOR.read_text(encoding="utf-8", errors="replace").splitlines()
    for c in calls[:30]:
        assert c["callee"] in lines[c["line"] - 1]
        assert c["confidence"] == 0.6  # candidate, nunca exato


def test_testlinks_mirror_disk():
    links = map_tests(DS / "siga-ex")
    assert len(links) >= 1
    for l in links:
        assert pathlib.Path(l["test"]).exists() and pathlib.Path(l["covers"]).exists()
