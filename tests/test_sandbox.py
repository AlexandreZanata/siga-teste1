# SPDX-License-Identifier: Apache-2.0
"""Testes da sandbox do executor (`benchmarks/rust/sandbox.py`, NEXT-03).

O que estes testes guardam:

- **Negação com prova.** Caminhos sensíveis somem do mapa e o laudo
  (`sandbox_proof.json`) registra cada um como invisível; segredos do ambiente
  são removidos antes de entrar. Sem isso, "isolamento" seria diretório distinto.
- **Fail-closed.** Se a prova falha, a carga útil NÃO executa (saída 3). Sem
  `bwrap`, a resposta é recusar (saída 2), nunca fingir.
- **Carga útil íntegra.** Workspace legível/gravável, `/out` gravável e código
  de saída repassado — a sandbox isola, não sabota o trabalho legítimo.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SANDBOX = REPO_ROOT / "benchmarks/rust/sandbox.py"
PY = "/usr/bin/python3"

NEEDS_BWRAP = pytest.mark.skipif(not shutil.which("bwrap"), reason="bwrap ausente")
NEEDS_PY = pytest.mark.skipif(not Path(PY).exists(), reason="/usr/bin/python3 ausente")


def run_sb(out: Path, *extra: str, env: dict | None = None) -> subprocess.CompletedProcess:
    base = dict(os.environ)
    if env:
        base.update(env)
    return subprocess.run([sys.executable, str(SANDBOX), *extra],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True, env=base)


@NEEDS_BWRAP
@NEEDS_PY
def test_prova_nega_caminhos_e_limpa_segredos(tmp_path: Path):
    ws = tmp_path / "ws"
    ws.mkdir()
    out = tmp_path / "out"
    denied = str(tmp_path / "segredo")
    proc = run_sb(out, "--workspace", str(ws), "--out-dir", str(out),
                  "--deny", denied, "--proof-only",
                  env={"ATLAS_GOLD": "/x/ouro", "ATLAS_PROBE_CANARY": "cvd-1",
                       "MINHA_API_KEY": "sk-fake"})
    assert proc.returncode == 0, proc.stdout
    proof = json.loads((out / "sandbox_proof.json").read_text())
    assert proof["ok"] is True
    assert proof["denied"] == [{"path": denied, "visible": False, "how": "tmpfs vazio"}]
    assert proof["env_leaked"] == []
    manifest = json.loads((out / "sandbox_manifest.json").read_text())
    assert manifest["schema"] == "atlas-sandbox/1"
    assert manifest["network_isolated"] is True
    for var in ("ATLAS_GOLD", "ATLAS_PROBE_CANARY", "MINHA_API_KEY"):
        assert var in manifest["env_removed"]


@NEEDS_BWRAP
@NEEDS_PY
def test_prova_falha_bloqueia_a_carga_util(tmp_path: Path):
    # Negar /usr esconde o próprio python da prova: fail-closed antes da carga.
    ws = tmp_path / "ws"
    ws.mkdir()
    out = tmp_path / "out"
    proc = run_sb(out, "--workspace", str(ws), "--out-dir", str(out),
                  "--deny", "/usr", "--", PY, "-c",
                  "open('/out/nao-deveria-existir.txt','w').write('x')")
    assert proc.returncode == 3
    assert "NÃO executada" in proc.stdout
    assert not (out / "nao-deveria-existir.txt").exists()


@NEEDS_BWRAP
@NEEDS_PY
def test_carga_util_ve_workspace_e_repasse_de_saida(tmp_path: Path):
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "dado.txt").write_text("ola")
    out = tmp_path / "out"
    proc = run_sb(out, "--workspace", str(ws), "--out-dir", str(out),
                  "--", PY, "-c",
                  "import pathlib,sys; "
                  "assert pathlib.Path('dado.txt').read_text()=='ola'; "
                  "open('/out/artefato.txt','w').write('feito'); "
                  "sys.exit(7)")
    assert proc.returncode == 7, proc.stdout
    assert (out / "artefato.txt").read_text() == "feito"


@NEEDS_BWRAP
@NEEDS_PY
def test_segredos_nao_atravessam_para_a_carga(tmp_path: Path):
    ws = tmp_path / "ws"
    ws.mkdir()
    out = tmp_path / "out"
    proc = run_sb(out, "--workspace", str(ws), "--out-dir", str(out),
                  "--", PY, "-c",
                  "import os; print('GOLD=' + str(os.environ.get('ATLAS_GOLD')))",
                  env={"ATLAS_GOLD": "/x/ouro"})
    assert proc.returncode == 0, proc.stdout
    assert "GOLD=None" in proc.stdout


@NEEDS_BWRAP
@NEEDS_PY
def test_caminhos_do_hospedeiro_viram_workspace_e_out(tmp_path: Path):
    ws = tmp_path / "ws"
    ws.mkdir()
    out = tmp_path / "out"
    proc = run_sb(out, "--workspace", str(ws), "--out-dir", str(out),
                  "--", PY, "-c",
                  "import os; print('WS=' + os.environ.get('ATLAS_WORKSPACE', ''))",
                  env={"ATLAS_WORKSPACE": str(ws)})
    assert proc.returncode == 0, proc.stdout
    assert "WS=/workspace" in proc.stdout, proc.stdout


def test_sem_bwrap_recusa_em_vez_de_fingir(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path))
    ws = tmp_path / "ws"
    ws.mkdir()
    out = tmp_path / "out"
    proc = run_sb(out, "--workspace", str(ws), "--out-dir", str(out), "--proof-only")
    assert proc.returncode != 0
    assert "bwrap" in proc.stdout
