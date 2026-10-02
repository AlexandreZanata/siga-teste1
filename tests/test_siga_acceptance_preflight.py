# SPDX-License-Identifier: Apache-2.0
"""Guarda os artefatos do preflight da TASK-A01 sem exigir Java, Maven ou rede.

O que estes testes guardam, e por que cada um existe:

- Baseline vermelho **registrado, não presumido**: o manifesto declara vermelho, o log mostra
  a falha com a classe da exceção esperada e a contagem `N/M passed` fecha com o manifesto.
  Se alguém trocar o log ou o manifesto, o teste cai.
- Hashes que amarram harness e fontes ao catálogo: o sha256 do harness no manifesto tem de
  ser o do arquivo commitado, e o sha256 da fonte tem de ser o do `curator_only` do
  `siga.dev.json`. Aceite contra fonte trocada não passa aqui.
- Prova Surefire com testes > 0: o XML do relatório tem `tests` positivo e zero
  falhas/erros; sucesso sem testes (o modo padrão do pom base) não satisfaz este teste.
- Config imutável auditável: o fragmento do perfil contém `skipTests=false` e **não**
  adiciona `src/test/br` (a tentativa quebrou a compilação com `duplicate class`).
"""

from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PREFLIGHT = REPO_ROOT / "experiments/rust/siga/2026-10-02-a01-preflight/preflight"
CATALOG = REPO_ROOT / "benchmarks/rust/tasks/siga.dev.json"

BASE_SHA = "e3be22828f787cbe71b339aecb7a7bf569099803"
EXPECTED_RED = {
    "SIGA-REAL-01": {"passed": 5, "failed": 1, "threw": "StringIndexOutOfBoundsException"},
    "SIGA-REAL-05": {"passed": 1, "failed": 7, "threw": "ClassCastException"},
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest(name: str) -> dict:
    return json.loads((PREFLIGHT / "manifests" / name).read_text())


def catalog_task(task_id: str) -> dict:
    doc = json.loads(CATALOG.read_text())
    for task in doc["tasks"]:
        if task["id"] == task_id:
            return task
    raise AssertionError(f"tarefa ausente no catálogo: {task_id}")


def test_manifestos_de_tarefa_registram_baseline_vermelho_com_evidencia():
    for task_id, expected in EXPECTED_RED.items():
        man = load_manifest(f"{task_id}.json")
        assert man["schema"] == "atlas-acceptance-preflight/1"
        assert man["task"] == task_id
        assert man["base_sha"] == BASE_SHA
        baseline = man["baseline"]
        assert baseline["result"] == "red", "baseline que não é vermelho não é baseline desta revisão"
        assert baseline["exit"] != 0, "vermelho com exit 0 seria sucesso silencioso"
        assert baseline["passed"] == expected["passed"]
        assert baseline["failed"] == expected["failed"]
        assert baseline["passed"] > 0 and baseline["failed"] > 0, (
            "quantidade positiva dos dois lados: casos preservados e defeito demonstrado")
        log = (PREFLIGHT / baseline["log"]).read_text()
        assert expected["threw"] in log, "o log tem de mostrar a exceção do defeito reproduzido"
        summary = re.search(r"(\d+)/(\d+) passed", log)
        assert summary, "harness sem linha de resumo não é auditável"
        assert (int(summary.group(1)), int(summary.group(2))) == (
            expected["passed"], expected["passed"] + expected["failed"])


def test_harness_e_fontes_estao_amarrados_por_hash_ao_catalogo():
    for task_id in EXPECTED_RED:
        man = load_manifest(f"{task_id}.json")
        harness = PREFLIGHT / man["harness"]["file"]
        assert harness.exists()
        assert sha256_file(harness) == man["harness"]["sha256"], "harness trocado sem atualizar manifesto"
        assert man["harness"]["exit_nonzero_on_failure"] is True
        catalog = catalog_task(task_id)
        catalog_hashes = {e["sha256"] for e in catalog["curator_only"]["source_evidence"]}
        for source in man["sources"]:
            assert source["sha256"] in catalog_hashes, (
                f"fonte do aceite fora do curator_only: {source['path']}")


def test_relatorios_surefire_comprovam_execucao_com_testes_positivos():
    man = load_manifest("maven-surefire-proof.json")
    smoke_xml = None
    for step in man["steps"]:
        for report in step.get("reports", []):
            if report.endswith(".xml"):
                path = PREFLIGHT / report
                assert path.exists(), f"relatório Surefire ausente: {report}"
                root = ET.parse(path).getroot()
                tests = int(root.attrib["tests"])
                assert tests > 0, "relatório com zero testes não prova execução"
                assert int(root.attrib["failures"]) == 0
                assert int(root.attrib["errors"]) == 0
                if "AtlasEvalSmokeTest" in report:
                    smoke_xml = root
    assert smoke_xml is not None, "relatório do smoke do avaliador ausente"


def test_config_imutavel_habilita_testes_sem_reintroduzir_src_test_br():
    fragment = (PREFLIGHT / "eval-config" / "atlas-eval-profile.xml").read_text()
    assert "<id>atlas-eval</id>" in fragment
    assert "<skipTests>false</skipTests>" in fragment
    assert "<source>src/test/br</source>" not in fragment, (
        "adicionar src/test/br quebra a compilação (duplicate class + símbolos de outro módulo)")
    assert "add-test-source" not in fragment
    excerpt = (PREFLIGHT / "reports" / "effective-pom-surefire.txt").read_text()
    assert "<skipTests>false</skipTests>" in excerpt, "POM efetivo sem a derrota do skip literal"


def test_logs_das_armadilhas_maven_estao_registrados():
    man = load_manifest("maven-surefire-proof.json")
    by_log = {}
    for step in man["steps"]:
        if "log" in step:
            by_log[step["log"]] = (PREFLIGHT / step["log"]).read_text()
    assert "Tests are skipped" in by_log["logs/mvn-default-skip.txt"]
    assert "Tests are skipped" in by_log["logs/mvn-flag-skip-false.txt"], (
        "-DskipTests=false também pula: a armadilha tem de constar na evidência")
