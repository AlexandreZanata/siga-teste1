# SPDX-License-Identifier: Apache-2.0
"""F1: o PIN afirma exatamente o HEAD real do dataset (zero suposição)."""
import pathlib
import subprocess

DATASET = pathlib.Path("/home/iiii/PESSOAL-PROJETOS-ALEXANDRE/siga")
EXPECTED_SHA = "e3be22828f787cbe71b339aecb7a7bf569099803"


def test_pin_matches_real_head():
    out = subprocess.run(
        ["git", f"--git-dir={DATASET / '.git'}", "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert out == EXPECTED_SHA, f"HEAD real {out} != PIN {EXPECTED_SHA}"
    assert (DATASET / "pom.xml").exists()
    assert (DATASET / "siga-ex").is_dir()
