"""Guardas do piloto Bitcoin, lote 2 (EXP02 parcial): 09/10/11/12.

Valida `benchmarks/bitcoin/rust/pilot2.tasks.json` + harnesses sem exigir
clone do Bitcoin nem custódia: estrutura atlas-tasks/2, balanço 1/1/1/1,
aceite existente com dispatches, pacote sem ouro, e conjuntos anteriores
intactos.
"""
import json
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[2]
RUST = REPO / "benchmarks" / "bitcoin" / "rust"
ACC = RUST / "acceptance"

BASE_SHA = "9be056a8a72b624dae9623b2f7bded92c2a21c91"
EXPECTED = {
    "BTC-REAL-09": ("bug_local",
                    ["test/functional/test_framework/descriptors.py"]),
    "BTC-REAL-10": ("entre_arquivos",
                    ["test/functional/test_framework/messages.py"]),
    "BTC-REAL-11": ("testes_comportamento_de_api",
                    ["test/functional/test_framework/authproxy.py"]),
    "BTC-REAL-12": ("configuracao_interface",
                    ["test/functional/test_runner.py"]),
}
GOLD_MARKERS = [
    "outside the checksum alphabet",
    "_read_exact",
    "non-object JSON response",
    "--filter is not a valid regular expression",
    "siga-a03-custody",
]


def load_set():
    with open(RUST / "pilot2.tasks.json", encoding="utf-8") as f:
        return json.load(f)


def test_schema_and_balance():
    data = load_set()
    assert data["schema"] == "atlas-tasks/2"
    assert data["platform"] == "bitcoin"
    assert data["base_sha"] == BASE_SHA
    assert data["sealed"] is False
    tasks = data["tasks"]
    assert [t["id"] for t in tasks] == sorted(EXPECTED)
    cats = sorted(t["category"] for t in tasks)
    assert cats == sorted(v[0] for v in EXPECTED.values())
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
        for tid in EXPECTED:
            py = ACC / (tid.replace("BTC-REAL-", "accept_b") + ".py")
            assert marker not in py.read_text(encoding="utf-8"), (py, marker)


def test_preflight_logs_present():
    pre = (REPO / "experiments" / "bitcoin" / "rust"
           / "2026-10-05-b02pilot2-validation" / "preflight")
    for tid in EXPECTED:
        red = pre / ("red_%s.txt" % tid)
        green = pre / ("green_%s.txt" % tid)
        assert red.exists() and green.exists(), tid
        assert "FAIL" in red.read_text(encoding="utf-8")
        assert "FAILED" not in green.read_text(encoding="utf-8")


def test_previous_sets_untouched():
    smoke = json.loads((RUST / "smoke.tasks.json").read_text(encoding="utf-8"))
    assert [t["id"] for t in smoke["tasks"]] == [
        "BTC-REAL-01", "BTC-REAL-02", "BTC-REAL-03", "BTC-REAL-04"]
    pilot = json.loads((RUST / "pilot.tasks.json").read_text(encoding="utf-8"))
    assert [t["id"] for t in pilot["tasks"]] == [
        "BTC-REAL-05", "BTC-REAL-06", "BTC-REAL-07", "BTC-REAL-08"]
