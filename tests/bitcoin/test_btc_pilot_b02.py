"""Guardas do piloto Bitcoin (TASK-B02 + desbloqueio 07): 05/06/07/08.

Valida `benchmarks/bitcoin/rust/pilot.tasks.json` + harnesses sem exigir
clone do Bitcoin nem custódia: estrutura atlas-tasks/2, balanço 1/1/1/1,
aceite existente com dispatches (07 com sonda C++), pacote sem ouro.
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
    "BTC-REAL-07": ("testes_comportamento_de_api",
                    ["src/util/strencodings.cpp"]),
}
GOLD_MARKERS = [
    "proxy.reuse_http_connections",
    "truncated payload",
    "test selection is empty after",
    "multiplier = ByteUnit::NOOP",
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
    tasks = data["tasks"]
    assert [t["id"] for t in tasks] == sorted(EXPECTED)
    cats = sorted(t["category"] for t in tasks)
    assert cats == ["bug_local", "configuracao_interface",
                    "entre_arquivos", "testes_comportamento_de_api"]
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
                   ACC / "accept_b07.py", ACC / "accept_b08.py",
                   ACC / "probe_b07.cpp"]:
            assert marker not in py.read_text(encoding="utf-8"), (py, marker)


def test_preflight_logs_present():
    pre = (REPO / "experiments" / "bitcoin" / "rust"
           / "2026-10-05-b02-validation" / "preflight")
    pre07 = (REPO / "experiments" / "bitcoin" / "rust"
             / "2026-10-05-b07-validation" / "preflight")
    for tid in EXPECTED:
        d = pre07 if tid == "BTC-REAL-07" else pre
        red = d / ("red_%s.txt" % tid)
        green = d / ("green_%s.txt" % tid)
        assert red.exists() and green.exists(), tid
        assert "FAIL" in red.read_text(encoding="utf-8")
        assert "FAILED" not in green.read_text(encoding="utf-8")


def test_smoke_still_sealed_untouched():
    data = json.loads((RUST / "smoke.tasks.json").read_text(encoding="utf-8"))
    assert [t["id"] for t in data["tasks"]] == [
        "BTC-REAL-01", "BTC-REAL-02", "BTC-REAL-03", "BTC-REAL-04"]
