"""Guardas do smoke Bitcoin (TASK-B01): conjunto, aceite e isolamento.

Valida `benchmarks/bitcoin/rust/smoke.tasks.json` + `acceptance/` sem exigir
clone do Bitcoin nem custódia: estrutura atlas-tasks/2, balanço 1/1/1/1,
aceite existente com hashes amarrados ao catálogo, e pacote público sem ouro.
"""
import json
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[2]
RUST = REPO / "benchmarks" / "bitcoin" / "rust"
ACC = RUST / "acceptance"

BASE_SHA = "9be056a8a72b624dae9623b2f7bded92c2a21c91"
EXPECTED_SOURCES = {
    "BTC-REAL-01": [("test/functional/test_framework/descriptors.py",
                     "8c2a4490c1b2a09c6c6e209eda090b160214d8156e20d6db671459cb4090a16a")],
    "BTC-REAL-02": [("test/functional/test_framework/address.py",
                     "63e83cdd2054afbccff8932729dc65cf8feafc8ce3bd9b0071d492058d12bf4f")],
    "BTC-REAL-03": [("test/functional/test_framework/authproxy.py",
                     "736246f2495578e0b1f38775ae44c59514e5bd45bf83b427d90b2370916d1a1a")],
    "BTC-REAL-04": [("test/functional/test_runner.py",
                     "faee6591d749e7fae8340430039f0b6f7450c6eb5a2960d61f0be2118ca529c3")],
}
EXPECTED_CATEGORIES = {
    "BTC-REAL-01": "bug_local",
    "BTC-REAL-02": "entre_arquivos",
    "BTC-REAL-03": "testes_comportamento_de_api",
    "BTC-REAL-04": "configuracao_interface",
}
GOLD_MARKERS = [
    "must be a positive integer",
    "expanded is None",
    "version == 0",
    "split(';')[0]",
    "siga-a03-custody",
]


def load_set():
    with open(RUST / "smoke.tasks.json", encoding="utf-8") as f:
        return json.load(f)


def test_schema_and_balance():
    data = load_set()
    assert data["schema"] == "atlas-tasks/2"
    assert data["platform"] == "bitcoin"
    assert data["base_sha"] == BASE_SHA
    tasks = data["tasks"]
    assert [t["id"] for t in tasks] == sorted(EXPECTED_SOURCES)
    assert all(t["split"] == "smoke" for t in tasks)
    assert all(t["base_sha"] == BASE_SHA for t in tasks)
    cats = [t["category"] for t in tasks]
    assert sorted(cats) == sorted(EXPECTED_CATEGORIES.values())
    for t in tasks:
        assert t["category"] == EXPECTED_CATEGORIES[t["id"]]
        assert t["timeout_s"] >= 60
        assert t["test_command"] == ["bash", "atlas-accept/run.sh", t["id"]]
        assert "atlas-accept/**" in t["immutable_paths"]


def test_no_curator_fields_or_gold():
    data = load_set()
    blob = json.dumps(data)
    for forbidden in ("curator_only", "reference", "solution", "gold",
                      "private", "custody", "custódia"):
        assert forbidden not in blob, forbidden
    for t in data["tasks"]:
        assert set(t) <= {"id", "split", "category", "statement", "base_sha",
                          "test_command", "timeout_s", "allowed_paths",
                          "immutable_paths", "origin", "contamination_risk",
                          "contamination_note"}


def test_acceptance_exists_and_dispatches_all():
    run_sh = (ACC / "run.sh").read_text(encoding="utf-8")
    for tid in EXPECTED_SOURCES:
        assert tid in run_sh, tid
        harness = ACC / (tid.replace("BTC-REAL-", "accept_b") + ".py")
        assert harness.exists(), str(harness)
    for marker in GOLD_MARKERS:
        for py in ACC.glob("accept_*.py"):
            assert marker not in py.read_text(encoding="utf-8"), (py, marker)


def test_allowed_paths_match_catalog_hashes():
    data = load_set()
    for t in data["tasks"]:
        expected = EXPECTED_SOURCES[t["id"]]
        assert t["allowed_paths"] == [p for p, _ in expected]
        assert len(expected[0][1]) == 64  # sha256 registrado por fonte


def test_preflight_logs_present():
    pre = (REPO / "experiments" / "bitcoin" / "rust"
           / "2026-10-05-b01-validation" / "preflight")
    for tid in EXPECTED_SOURCES:
        red = pre / ("red_%s.txt" % tid)
        green = pre / ("green_%s.txt" % tid)
        assert red.exists() and green.exists(), tid
        assert "FAIL" in red.read_text(encoding="utf-8")
        assert "FAILED" not in green.read_text(encoding="utf-8")
