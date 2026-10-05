"""Guardas do piloto Bitcoin parcial (TASK-B02): 05/06/08 validados, 07 fora.

Valida `benchmarks/bitcoin/rust/pilot.tasks.json` + harnesses sem exigir
clone do Bitcoin nem custódia: estrutura atlas-tasks/2, categorias,
aceite existente com dispatches, pacote sem ouro, e o estado parcial
explícito (07 bloqueada, conjunto desbalanceado com razão em curadoria).
"""
import json
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[2]
RUST = REPO / "benchmarks" / "bitcoin" / "rust"
ACC = RUST / "acceptance"

BASE_SHA = "9be056a8a72b624dae9623b2f7bded92c2a21c91"
EXPECTED = {
    "BTC-REAL-05": ("bug_local",
                    ["test/functional/test_framework/authproxy.py"]),
    "BTC-REAL-06": ("entre_arquivos",
                    ["test/functional/test_framework/messages.py"]),
    "BTC-REAL-08": ("configuracao_interface",
                    ["test/functional/test_runner.py"]),
}
GOLD_MARKERS = [
    "proxy.reuse_http_connections",
    "truncated payload",
    "test selection is empty after",
    "siga-a03-custody",
]


def load_set():
    with open(RUST / "pilot.tasks.json", encoding="utf-8") as f:
        return json.load(f)


def test_schema_and_partial_balance_declared():
    data = load_set()
    assert data["schema"] == "atlas-tasks/2"
    assert data["platform"] == "bitcoin"
    assert data["base_sha"] == BASE_SHA
    assert data["sealed"] is False
    assert "07" in data["_note"] and "bloqueada" in data["_note"]
    tasks = data["tasks"]
    assert [t["id"] for t in tasks] == sorted(EXPECTED)
    assert "BTC-REAL-07" not in [t["id"] for t in tasks]
    for t in tasks:
        cat, allowed = EXPECTED[t["id"]]
        assert t["split"] == "piloto"
        assert t["category"] == cat
        assert t["base_sha"] == BASE_SHA
        assert t["timeout_s"] >= 60
        assert t["test_command"] == ["bash", "atlas-accept/run.sh", t["id"]]
        assert t["allowed_paths"] == allowed
        assert "atlas-accept/**" in t["immutable_paths"]


def test_no_curator_fields_or_gold():
    data = load_set()
    blob = json.dumps(data)
    for forbidden in ("curator_only", "reference", "solution", "gold",
                      "private", "custody", "custódia"):
        assert forbidden not in blob, forbidden


def test_acceptance_dispatches_and_is_gold_free():
    run_sh = (ACC / "run.sh").read_text(encoding="utf-8")
    for tid in EXPECTED:
        assert tid in run_sh, tid
        harness = ACC / (tid.replace("BTC-REAL-", "accept_b") + ".py")
        assert harness.exists(), str(harness)
    for marker in GOLD_MARKERS:
        for py in [ACC / "accept_b05.py", ACC / "accept_b06.py",
                   ACC / "accept_b08.py"]:
            assert marker not in py.read_text(encoding="utf-8"), (py, marker)


def test_preflight_logs_present():
    pre = (REPO / "experiments" / "bitcoin" / "rust"
           / "2026-10-05-b02-validation" / "preflight")
    for tid in EXPECTED:
        red = pre / ("red_%s.txt" % tid)
        green = pre / ("green_%s.txt" % tid)
        assert red.exists() and green.exists(), tid
        assert "FAIL" in red.read_text(encoding="utf-8")
        assert "FAILED" not in green.read_text(encoding="utf-8")


def test_smoke_still_sealed_untouched():
    data = json.loads((RUST / "smoke.tasks.json").read_text(encoding="utf-8"))
    assert [t["id"] for t in data["tasks"]] == [
        "BTC-REAL-01", "BTC-REAL-02", "BTC-REAL-03", "BTC-REAL-04"]
