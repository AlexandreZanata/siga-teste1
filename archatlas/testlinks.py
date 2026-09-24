# SPDX-License-Identifier: Apache-2.0
"""Test-links F9: *Test.java -> classe espelho em src/main, só se ambos existirem."""
from __future__ import annotations
import pathlib


def map_tests(module: pathlib.Path) -> list[dict]:
    out = []
    for t in sorted((module / "src/test/java").rglob("*Test.java")):
        rel = t.relative_to(module / "src/test/java")
        covered = module / "src/main/java" / rel.parent / (t.stem[:-len("Test")] + ".java")
        if covered.exists():
            out.append({"test": str(t), "covers": str(covered), "mapping": "naming",
                        "confidence": 0.9, "provenance": "maven-layout"})
    return out
