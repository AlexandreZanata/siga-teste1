# SPDX-License-Identifier: Apache-2.0
"""P6-exec (a): PINs com 40 hex + clones limpos nos SHAs + censo confere. Sem build."""
import pathlib
import re
import subprocess

import pytest

T1_SHA = "ae2ceeb5a79f9459f54ecaa9f4b2f8e095a2277b"
T2_SHA = "8721173580390a9d297e5af06cac3f0b6841f425"
T1 = pathlib.Path("/tmp/opencode-p6/t1")
T2 = pathlib.Path("/tmp/opencode-p6/t2")
clones_here = T1.is_dir() and T2.is_dir()


def test_pins_format():
    for sha in (T1_SHA, T2_SHA):
        assert re.fullmatch(r"[0-9a-f]{40}", sha)


@pytest.mark.skipif(not clones_here, reason="clones /tmp/opencode-p6 ausentes: só formato")
def test_pins_match_clean_checkouts_and_census():
    for root, sha, ext, n_files in ((T1, T1_SHA, ".java", 842), (T2, T2_SHA, ".py", 274)):
        out = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                             capture_output=True, text=True, check=True)
        assert out.stdout.strip() == sha
        st = subprocess.run(["git", "-C", str(root), "status", "--short"],
                            capture_output=True, text=True, check=True)
        assert st.stdout.strip() == ""
        got = sum(1 for p in root.rglob(f"*{ext}") if p.is_file() and ".git/" not in str(p))
        assert got == n_files
