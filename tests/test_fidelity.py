# SPDX-License-Identifier: Apache-2.0
"""F7: fidelidade Java ~total (único zero = package-info legítimo); JSPs fora de cobertura declarada."""
import pathlib

from archatlas.fidelity import measure_jsp, measure_scope

DS = pathlib.Path("/home/iiii/PESSOAL-PROJETOS-ALEXANDRE/siga")


def test_java_fidelity():
    m = measure_scope(DS / "siga-ex/src/main/java")
    assert m["files"] >= 500
    assert m["unresolved_rate"] < 0.01
    assert m["zero_files"] == [str(DS / "siga-ex/src/main/java/br/gov/jfrj/siga/ex/package-info.java")]


def test_jsp_gap_declared():
    m = measure_jsp(DS / "sigaex")
    assert m["files"] >= 500 and m["unresolved_rate"] == 1.0
