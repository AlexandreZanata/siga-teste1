# SPDX-License-Identifier: Apache-2.0
"""F1: o censo só passa se os arquivos reais existirem no disco."""
import pathlib

from archatlas.census import census

DATASET = pathlib.Path("/home/iiii/PESSOAL-PROJETOS-ALEXANDRE/siga")


def test_census_verifies_real_files():
    c = census(DATASET)
    assert c["modules"]["siga-ex"]["java_files"] >= 500
    assert c["modules"]["sigaex"]["jsp_tag"] >= 600
    anchor = DATASET / "siga-ex/src/main/java/br/gov/jfrj/siga/ex/ExMovimentacao.java"
    assert anchor.exists()
    assert "class ExMovimentacao" in anchor.read_text(encoding="utf-8", errors="replace")
