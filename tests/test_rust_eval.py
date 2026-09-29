# SPDX-License-Identifier: Apache-2.0
"""Testes da camada de avaliação (`benchmarks/rust/eval.py`).

O que estes testes guardam, e por que cada um existe:

- **A mecânica tem precedência e é calculada do artefato.** Um teste vermelho do avaliador não
  pode ser compensado por nota humana; escopo declarado é checado contra os caminhos do patch;
  tentativa morta no teto é falha, não sucesso parcial.
- **Fail-closed em tudo que é ambíguo.** Item sem nota, item julgado só por juiz LLM, item em
  disputa sem adjudicação e item da amostra de 25% sem segundo revisor **não** contam como
  sucesso. Taxa que absorve dúvida é taxa inflada.
- **O bundle não carrega o rótulo.** Condição, modelo, custo, ordem e telemetria ficam na chave,
  em custódia; o vazamento é escaneado em duas severidades, e só o `hard` bloqueia.
- **A chave não é sobrescrita nem guardada dentro do bundle.** Mesma disciplina do ouro no
  runner, pelo mesmo motivo: separação de diretório não é isolamento, mas publicar o mapa é pior.
- **Abrir rótulo sobre outro bundle é recusado.** O hash do bundle julgado é o que a chave
  registra; se o bundle mudou depois, o julgamento não vale mais para ele.

Nenhum teste usa rede, modelo ou o binário Rust para julgar: a integração com o runner usa o
executor `dry` (marcado `infrastructure_only`) e existe para provar que o pipeline funciona no
artefato real, não para produzir resultado.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
EVAL = REPO_ROOT / "benchmarks/rust/eval.py"
RUNNER = REPO_ROOT / "benchmarks/rust/runner.py"

_spec = importlib.util.spec_from_file_location("atlas_eval", EVAL)
atlas_eval = importlib.util.module_from_spec(_spec)
sys.modules["atlas_eval"] = atlas_eval
_spec.loader.exec_module(atlas_eval)


# --- helpers --------------------------------------------------------------------------


def run_eval(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(EVAL), *args],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def write_json(path: Path, obj) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False))
    return path


def task(tid: str = "t01", category: str = "bug_local", **over) -> dict:
    base = {
        "id": tid,
        "split": "smoke",
        "category": category,
        "statement": f"enunciado de {tid}: ajuste o metodo getTitular",
        "base_sha": "0" * 40,
        "test_command": [sys.executable, "-c", "import sys; sys.exit(0)"],
        "timeout_s": 60,
        "allowed_paths": ["src/*.py"],
        "immutable_paths": ["tests/*"],
        "origin": "issue interna revisada",
        "contamination_risk": "baixo",
        "contamination_note": "revisada independentemente; nao publicada em issue aberta",
    }
    base.update(over)
    return base


def tasks_file(path: Path, tasks: list[dict]) -> Path:
    return write_json(path, {"schema": "atlas-tasks/2", "platform": "teste", "tasks": tasks})


PATCH_OK = (
    "diff --git a/src/app.py b/src/app.py\n"
    "index 1111111..2222222 100644\n"
    "--- a/src/app.py\n"
    "+++ b/src/app.py\n"
    "@@ -1,3 +1,3 @@\n"
    "-    return 1\n"
    "+    return 2\n"
)


def make_attempt(root: Path, name: str, t: dict, *, condition: str = "CTX-RS",
                 patch: str = PATCH_OK, statement: str | None = None, applied: bool = True,
                 exit_code: int = 0, stopped_by: str | None = None, cost=None,
                 model=None, repetition: int = 0, evidence_class: str = "real") -> Path:
    d = root / "attempts" / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "attempt.patch").write_text(patch)
    (d / "statement.txt").write_text(statement if statement is not None else t["statement"])
    man = {
        "schema": "atlas-run/1",
        "run_id": name,
        "platform": "teste",
        "phase": "smoke",
        "task": {"id": t["id"], "split": t["split"], "category": t["category"],
                 "base_sha": t["base_sha"], "test_command": t["test_command"],
                 "allowed_paths": t.get("allowed_paths"),
                 "immutable_paths": t.get("immutable_paths")},
        "condition": condition,
        "model": model or {"provider": "provedor-ficticio", "id": "modelo-ficticio",
                           "version": "v1"},
        "cost": cost or {"provider_billed": None, "currency": None, "reason": "P2 pendente"},
        "usage": {"tool_calls": 7, "opened": 2, "delivered_bytes": 1234},
        "order": {"repetition": repetition, "position": 0},
        "snapshot": {"base_sha": t["base_sha"], "workspace": "/tmp/nao-deve-vazar"},
        "tool": {"policy": "CTX-RS", "binary": "/tmp/archatlas"},
        "patch": {"file": "attempt.patch", "bytes": len(patch), "empty": not patch.strip()},
        "acceptance": {"applied": applied, "exit_code": exit_code, "seconds": 1.0},
        "stopped_by": stopped_by,
        "stopped_killed": False,
        "outcome": "stopped" if stopped_by else "completed",
        "evidence_class": evidence_class,
        "gold_isolation": {"declared_dir_ref": None},
        "executor_seconds": 12.0,
    }
    write_json(d / "manifest.json", man)
    return d


def check(root: Path, tasks: list[dict], name: str, tmp_path: Path) -> dict:
    tf = tasks_file(tmp_path / "tasks.json", tasks)
    out = tmp_path / "mech.json"
    proc = run_eval("check", "--attempts", str(root / "attempts"), "--tasks", str(tf),
                    "--out", str(out))
    rows = json.loads(out.read_text())["attempts"]
    row = next(r for r in rows if r["attempt"] == name)
    row["_proc"] = proc.returncode
    return row


def bundle_all(root: Path, tasks: list[dict], tmp_path: Path, *extra: str,
               key: Path | None = None, seed: str | None = None,
               search: Path | None = None) -> subprocess.CompletedProcess:
    tf = tasks_file(tmp_path / "tasks.json", tasks)
    return run_eval("bundle", "--attempts", str(root / "attempts"), "--tasks", str(tf),
                    "--out", str(tmp_path / "blind"),
                    "--key", str(key or (tmp_path / "custodia" / "blind_key.json")),
                    "--custodian", "custodiante-ficticio", *extra)


def scores_for(items: list[dict], *, verdict: str = "aceito", second: bool = True,
               kind: str = "human", extra_item: dict | None = None) -> dict:
    out = []
    for it in items:
        v = {"reviewer": "r1", "kind": kind, "verdict": verdict, "notes": "sem rotulo"}
        entry = {"item_id": it["item_id"], "verdicts": [v]}
        if second:
            entry["second_verdict"] = {"reviewer": "r2", "kind": "human", "verdict": verdict}
        if extra_item:
            entry.update(extra_item)
        out.append(entry)
    return {"schema": "atlas-blind-scores/1", "rubric": atlas_eval.RUBRIC_ID, "items": out}


# --- rubrica e checagem mecânica ------------------------------------------------------


def test_rubrica_separa_mecanica_de_semantica_com_precedencia():
    r = atlas_eval.rubric()
    ids = [i["id"] for i in r["items"]]
    assert len(ids) == len(set(ids))
    mec = [i for i in r["items"] if i["kind"] == "mechanical"]
    hum = [i for i in r["items"] if i["kind"] == "human"]
    assert {i["id"] for i in mec} == {"M1", "M2", "M3", "M4", "M5", "M6"}
    assert {i["id"] for i in hum} == {"H1", "H2", "H3"}
    assert "mecanica antes de semantica" in r["precedencia"]
    assert set(r["estados_que_nao_contam_como_sucesso"]) == {"indeterminado", "triagem",
                                                             "em_disputa"}
    # H1-H3 são semânticas e nenhuma delas aceita "igual ao patch de referência" como critério.
    assert all("o_que_nao_e_evidencia" in i for i in hum)


def test_patch_paths_le_todos_os_arquivos_tocados():
    dois = PATCH_OK + "diff --git a/docs/nota.md b/docs/nota.md\n--- a/docs/nota.md\n"
    assert atlas_eval.patch_paths(dois) == ["src/app.py", "docs/nota.md"]


def test_check_aceita_tentativa_boa_e_reprova_que_nao_aplica(tmp_path):
    t = task()
    root = tmp_path
    make_attempt(root, "boa", t)
    make_attempt(root, "nao_aplica", t, applied=False, exit_code=None)
    assert check(root, [t], "boa", tmp_path)["mechanical_verdict"] == "aceito"
    ruim = check(root, [t], "nao_aplica", tmp_path)
    assert ruim["mechanical_verdict"] == "rejeitado"
    assert set(ruim["mechanical_rejected_items"]) == {"M1", "M2"}


def test_check_reprova_escopo_fora_do_declarado(tmp_path):
    t = task()
    fora = PATCH_OK + ("diff --git a/docs/nota.md b/docs/nota.md\n--- a/docs/nota.md\n"
                       "+++ b/docs/nota.md\n")
    make_attempt(tmp_path, "fora", t, patch=fora)
    r = check(tmp_path, [t], "fora", tmp_path)
    assert r["mechanical_verdict"] == "rejeitado"
    assert r["mechanical"]["M4"]["observed"]["fora_do_escopo"] == ["docs/nota.md"]


def test_check_reprova_enfraquecimento_de_teste_imutavel(tmp_path):
    t = task()
    patch = ("diff --git a/tests/test_api.py b/tests/test_api.py\n--- a/tests/test_api.py\n"
             "+++ b/tests/test_api.py\n@@ -1 +1 @@\n-assert x == 2\n+assert True\n")
    make_attempt(tmp_path, "enfraquece", t, patch=patch)
    r = check(tmp_path, [t], "enfraquece", tmp_path)
    assert r["mechanical"]["M5"]["ok"] is False
    assert r["mechanical"]["M5"]["observed"]["tocados"] == ["tests/test_api.py"]


def test_check_reprova_tentativa_morta_no_teto(tmp_path):
    t = task()
    make_attempt(tmp_path, "morta", t, stopped_by="wall_s")
    r = check(tmp_path, [t], "morta", tmp_path)
    assert r["mechanical_rejected_items"] == ["M6"]
    assert r["mechanical"]["M6"]["observed"]["stopped_by"] == "wall_s"


def test_check_sai_com_erro_quando_ha_reprovacao_mecanica(tmp_path):
    t = task()
    make_attempt(tmp_path, "boa", t)
    make_attempt(tmp_path, "ruim", t, applied=False, exit_code=1)
    assert check(tmp_path, [t], "boa", tmp_path)["_proc"] == 1


# --- conjunto de tarefas --------------------------------------------------------------


def test_validate_exige_escopo_origem_e_risco(tmp_path):
    p = tasks_file(tmp_path / "t.json", [task(allowed_paths=[], origin=None,
                                              contamination_note=None)])
    proc = run_eval("validate", "--tasks", str(p))
    assert proc.returncode == 1
    assert "allowed_paths" in proc.stdout
    assert "origin" in proc.stdout
    assert "contamination_note" in proc.stdout


def test_validate_recusa_schema_antigo_porque_nao_ha_escopo_declarado(tmp_path):
    p = write_json(tmp_path / "t.json", {"schema": "atlas-tasks/1", "tasks": [{"id": "x"}]})
    proc = run_eval("validate", "--tasks", str(p))
    assert proc.returncode != 0
    assert "atlas-tasks/2" in proc.stdout


def test_validate_reprova_desbalanceado_sem_a_flag(tmp_path):
    desbalanceado = [task("a", "bug_local"), task("b", "bug_local")]
    p = tasks_file(tmp_path / "t.json", desbalanceado)
    assert run_eval("validate", "--tasks", str(p)).returncode == 1
    assert run_eval("validate", "--tasks", str(p), "--allow-imbalance").returncode == 0
    balanceado = [task("a", "bug_local"), task("b", "entre_arquivos"),
                  task("c", "testes_comportamento_de_api"), task("d", "configuracao_interface")]
    p2 = tasks_file(tmp_path / "t2.json", balanceado)
    assert run_eval("validate", "--tasks", str(p2)).returncode == 0


# --- bundle e custódia ----------------------------------------------------------------


def test_bundle_nao_carrega_condicao_modelo_custo_nem_ordem(tmp_path):
    t = task()
    for cond, rep in (("BASE", 0), ("LEX-RS", 0), ("CTX-RS", 1)):
        make_attempt(tmp_path, f"a-{cond}-{rep}", t, condition=cond, repetition=rep,
                     cost={"provider_billed": 1.23, "currency": "BRL"})
    proc = bundle_all(tmp_path, [t], tmp_path)
    assert proc.returncode == 0, proc.stdout
    blind = tmp_path / "blind"
    for f in blind.rglob("*"):
        if not f.is_file():
            continue
        if f.suffix == ".json":
            assert atlas_eval.forbidden_keys(json.loads(f.read_text())) == [], f
        assert not atlas_eval.scan_text(f.read_text(errors="replace"))["hard"], f
    bundle = json.loads((blind / "bundle.json").read_text())
    assert len(bundle["items"]) == 3
    assert atlas_eval.forbidden_keys(bundle) == []
    # o rótulo existe — na chave, fora do bundle
    key = json.loads((tmp_path / "custodia" / "blind_key.json").read_text())
    assert sorted(m["condition"] for m in key["mapping"].values()) == \
        ["BASE", "CTX-RS", "LEX-RS"]
    # ids opacos: não dá para ler a condição no id
    assert all(not any(c in it["item_id"] for c in ("BASE", "CTX", "LEX"))
               for it in bundle["items"])


def test_bundle_bloqueia_vazamento_duro_e_nao_escreve_chave(tmp_path):
    t = task()
    make_attempt(tmp_path, "a", t,
                 statement="repita o resultado do braco LEX-RS que voce viu antes")
    proc = bundle_all(tmp_path, [t], tmp_path)
    assert proc.returncode != 0
    assert "BLOQUEADO" in proc.stdout
    assert not (tmp_path / "blind" / "bundle.json").exists()
    assert not (tmp_path / "custodia" / "blind_key.json").exists()


def test_bundle_registra_vazamento_suave_sem_bloquear(tmp_path):
    t = task()
    make_attempt(tmp_path, "a", t,
                 patch=PATCH_OK + "# lido com archatlas\n",
                 statement="use a ferramenta atlas-read se ajudar")
    proc = bundle_all(tmp_path, [t], tmp_path)
    assert proc.returncode == 0, proc.stdout
    bundle = json.loads((tmp_path / "blind" / "bundle.json").read_text())
    assert bundle["soft_leaks"], "vazamento suave tem de ser declarado, nao ignorado"
    assert "simples" in bundle["blinding_level"]
    key = json.loads((tmp_path / "custodia" / "blind_key.json").read_text())
    assert key["leak_scan"]["hard"] == 0 and key["leak_scan"]["soft"] >= 1


def test_bundle_recusa_chave_dentro_do_bundle(tmp_path):
    t = task()
    make_attempt(tmp_path, "a", t)
    proc = bundle_all(tmp_path, [t], tmp_path,
                      key=tmp_path / "blind" / "blind_key.json")
    assert proc.returncode != 0
    assert "BLOQUEADO" in proc.stdout


def test_bundle_nao_sobrescreve_chave_existente(tmp_path):
    t = task()
    make_attempt(tmp_path, "a", t)
    assert bundle_all(tmp_path, [t], tmp_path).returncode == 0
    segunda = bundle_all(tmp_path, [t], tmp_path, "--force-bundle")
    assert segunda.returncode != 0
    assert "custodia" in segunda.stdout


def test_bundle_reproduzivel_com_a_mesma_seed(tmp_path):
    t = task()
    make_attempt(tmp_path, "a", t)
    assert bundle_all(tmp_path, [t], tmp_path).returncode == 0
    h1 = json.loads((tmp_path / "custodia" / "blind_key.json").read_text())["bundle_sha256"]
    assert bundle_all(tmp_path, [t], tmp_path, "--force-bundle", "--force-key").returncode == 0
    h2 = json.loads((tmp_path / "custodia" / "blind_key.json").read_text())["bundle_sha256"]
    assert h1 == h2
    assert bundle_all(tmp_path, [t], tmp_path, "--force-bundle", "--force-key",
                      "--seed", "7").returncode == 0
    h3 = json.loads((tmp_path / "custodia" / "blind_key.json").read_text())["bundle_sha256"]
    assert h3 != h1


def test_bundle_recusa_manifesto_com_escopo_diferente_do_conjunto(tmp_path):
    t = task()
    make_attempt(tmp_path, "a", t)
    tf = tasks_file(tmp_path / "outro.json", [task(allowed_paths=["totalmente/*"])])
    proc = run_eval("bundle", "--attempts", str(tmp_path / "attempts"), "--tasks", str(tf),
                    "--out", str(tmp_path / "blind"), "--key", str(tmp_path / "k.json"))
    assert proc.returncode != 0
    assert "allowed_paths" in proc.stdout and "manifesto difere" in proc.stdout


# --- notas, adjudicação e un-blind ----------------------------------------------------


def _prepared(tmp_path: Path, conds: tuple[str, ...] = ("BASE", "LEX-RS", "CTX-RS"),
              cost: bool = False) -> tuple[Path, list[dict]]:
    t = task()
    for i, cond in enumerate(conds):
        make_attempt(tmp_path, f"a{i}", t, condition=cond,
                     cost={"provider_billed": 2.0, "currency": "BRL"} if cost else None)
    proc = bundle_all(tmp_path, [t], tmp_path)
    assert proc.returncode == 0, proc.stdout
    return tmp_path / "blind", [it for it in
                                json.loads((tmp_path / "blind" / "bundle.json").read_text())["items"]]


def test_validate_scores_recusa_rotulo_de_condicao_e_chave_proibida(tmp_path):
    blind, items = _prepared(tmp_path)
    sc = scores_for(items)
    sc["items"][0]["verdicts"][0]["notes"] = "isto parece LEX-RS pelo estilo"
    sc["condition"] = "CTX-RS"
    p = write_json(tmp_path / "notas.json", sc)
    proc = run_eval("validate-scores", "--bundle", str(blind),
                    "--key", str(tmp_path / "custodia" / "blind_key.json"),
                    "--scores", str(p))
    assert proc.returncode == 1
    assert "chave proibida" in proc.stdout
    assert "rotulo de condicao" in proc.stdout


def test_amostra_de_25_por_cento_exige_segundo_revisor_e_sem_ele_nao_conta(tmp_path):
    blind, items = _prepared(tmp_path)
    key = json.loads((tmp_path / "custodia" / "blind_key.json").read_text())
    assert key["review_sample"], "a chave tem de registrar a amostra revisada por dois"
    amostrado = set(key["review_sample"])
    sc = scores_for(items, second=False)  # um revisor só: os da amostra ficam sem segundo
    p = write_json(tmp_path / "notas.json", sc)
    out = tmp_path / "avaliacao.json"
    run_eval("unblind", "--bundle", str(blind), "--key",
             str(tmp_path / "custodia" / "blind_key.json"), "--scores", str(p),
             "--out", str(out))
    rep = json.loads(out.read_text())
    estados = [v["state"] for v in rep["nao_contam_como_sucesso"].values()]
    assert len(estados) == len(amostrado)
    assert all(e == "indeterminado" for e in estados)
    assert all("falta_segundo_revisor" == rep["nao_contam_como_sucesso"][i]["status"]
               for i in amostrado)
    total = sum(c["aceitos"] for c in rep["condicoes"].values())
    assert total == len(items) - len(amostrado)


def test_juiz_llm_sozinho_nao_vira_gabarito(tmp_path):
    blind, items = _prepared(tmp_path)
    p = write_json(tmp_path / "notas.json", scores_for(items, kind="llm", second=False))
    proc = run_eval("validate-scores", "--bundle", str(blind),
                    "--key", str(tmp_path / "custodia" / "blind_key.json"),
                    "--scores", str(p))
    assert "triagem_llm" in proc.stdout
    out = tmp_path / "avaliacao.json"
    run_eval("unblind", "--bundle", str(blind), "--key",
             str(tmp_path / "custodia" / "blind_key.json"), "--scores", str(p),
             "--out", str(out))
    rep = json.loads(out.read_text())
    assert len(rep["nao_contam_como_sucesso"]) == len(items)
    assert all(v["state"] == "indeterminado"
               for v in rep["nao_contam_como_sucesso"].values())


def test_disputa_sem_adjudicacao_nao_conta_e_com_adjudicacao_conta(tmp_path):
    blind, items = _prepared(tmp_path, conds=("CTX-RS",))
    sc = scores_for(items)
    sc["items"][0]["second_verdict"]["verdict"] = "rejeitado"
    p = write_json(tmp_path / "notas.json", sc)
    out = tmp_path / "sem_adj.json"
    run_eval("unblind", "--bundle", str(blind), "--key",
             str(tmp_path / "custodia" / "blind_key.json"), "--scores", str(p),
             "--out", str(out))
    assert json.loads(out.read_text())["nao_contam_como_sucesso"][items[0]["item_id"]]["status"] \
        == "em_disputa"
    sc["items"][0]["adjudication"] = {"reviewer": "r3", "kind": "human", "verdict": "aceito"}
    p2 = write_json(tmp_path / "notas_adj.json", sc)
    out2 = tmp_path / "com_adj.json"
    run_eval("unblind", "--bundle", str(blind), "--key",
             str(tmp_path / "custodia" / "blind_key.json"), "--scores", str(p2),
             "--out", str(out2))
    rep = json.loads(out2.read_text())
    assert not rep["nao_contam_como_sucesso"]
    assert rep["condicoes"]["CTX-RS"]["aceitos"] == 1


def test_unblind_recusa_bundle_alterado_depois_da_chave(tmp_path):
    blind, items = _prepared(tmp_path, conds=("CTX-RS",))
    p = write_json(tmp_path / "notas.json", scores_for(items))
    with (blind / "patches" / f"{items[0]['item_id']}.patch").open("a") as fh:
        fh.write("\n# alteracao depois do julgamento\n")
    proc = run_eval("unblind", "--bundle", str(blind), "--key",
                    str(tmp_path / "custodia" / "blind_key.json"), "--scores", str(p))
    assert proc.returncode != 0
    assert "BLOQUEADO" in proc.stdout and "mudou" in proc.stdout


def test_unblind_agrega_success_rate_por_tentativa_e_por_tarefa(tmp_path):
    blind, items = _prepared(tmp_path, conds=("BASE", "CTX-RS"))
    sc = scores_for(items)
    sc["items"][0]["verdicts"][0]["verdict"] = "rejeitado"
    sc["items"][0]["second_verdict"]["verdict"] = "rejeitado"
    p = write_json(tmp_path / "notas.json", sc)
    out = tmp_path / "avaliacao.json"
    run_eval("unblind", "--bundle", str(blind), "--key",
             str(tmp_path / "custodia" / "blind_key.json"), "--scores", str(p),
             "--out", str(out))
    rep = json.loads(out.read_text())
    assert rep["rubric"] == atlas_eval.RUBRIC_ID
    assert rep["unidade_de_inferencia"].startswith("tarefa")
    rejeitada = [c for c in rep["condicoes"].values() if c["aceitos"] == 0]
    assert len(rejeitada) == 1 and rejeitada[0]["tentativas"] == 1
    assert rejeitada[0]["success_rate_por_tentativa"] == 0.0
    assert rejeitada[0]["success_rate_por_tarefa"] == 0.0
    # sem custo faturado em nenhum manifesto, custo por sucesso fica bloqueado com motivo —
    # inclusive na condicao sem aceite: sem custo nao se pode nem dizer que a razao e infinita
    for c in rep["condicoes"].values():
        assert c["cost_per_success"] is None
        assert "P2 pendente" in c["cost_per_success_reason"]
    # funções explícitas do que o palpite de condição mede: cegamento, não resultado
    assert rep["identidade_textual"]["note"].startswith("o protocolo")
    assert rep["blinding"]["note"].startswith("acuracia")


def test_unblind_calcula_custo_por_sucesso_quando_ha_custo_faturado(tmp_path):
    blind, items = _prepared(tmp_path, conds=("CTX-RS",), cost=True)
    p = write_json(tmp_path / "notas.json", scores_for(items))
    out = tmp_path / "avaliacao.json"
    run_eval("unblind", "--bundle", str(blind), "--key",
             str(tmp_path / "custodia" / "blind_key.json"), "--scores", str(p),
             "--out", str(out))
    rep = json.loads(out.read_text())
    cond = rep["condicoes"]["CTX-RS"]
    assert cond["cost_per_success"] == 2.0
    assert cond["cost_per_success_reason"] is None


def test_custo_por_sucesso_e_infinito_declarado_quando_ha_custo_e_zero_aceites(tmp_path):
    blind, items = _prepared(tmp_path, conds=("CTX-RS",), cost=True)
    sc = scores_for(items, verdict="rejeitado")
    p = write_json(tmp_path / "notas.json", sc)
    out = tmp_path / "avaliacao.json"
    run_eval("unblind", "--bundle", str(blind), "--key",
             str(tmp_path / "custodia" / "blind_key.json"), "--scores", str(p),
             "--out", str(out))
    cond = json.loads(out.read_text())["condicoes"]["CTX-RS"]
    assert cond["cost_per_success"] is None
    assert "infinito" in cond["cost_per_success_reason"]


def test_unblind_mede_acuracia_do_palpite_de_condicao(tmp_path):
    blind, items = _prepared(tmp_path, conds=("CTX-RS",))
    sc = scores_for(items)
    sc["items"][0]["suspicion_of_condition"] = "CTX-RS"
    p = write_json(tmp_path / "notas.json", sc)
    out = tmp_path / "avaliacao.json"
    run_eval("unblind", "--bundle", str(blind), "--key",
             str(tmp_path / "custodia" / "blind_key.json"), "--scores", str(p),
             "--out", str(out))
    b = json.loads(out.read_text())["blinding"]
    assert b["guesses"] == 1 and b["correct"] == 1 and b["base_rate"] == 1.0


# --- integração: runner real (dry) até o bundle ---------------------------------------


@pytest.fixture()
def workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "ws"
    (ws / "src").mkdir(parents=True)
    (ws / "src" / "app.py").write_text("class App:\n    def getTitular(self):\n        return 1\n")
    (ws / "dry_edit.txt").write_text("original\n")
    for cmd in (["git", "init", "-q"], ["git", "add", "-A"],
                ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "base"]):
        subprocess.run(cmd, cwd=ws, check=True, stdout=subprocess.DEVNULL)
    return ws


def test_integracao_runner_dry_ate_bundle_e_unblind(tmp_path, workspace):
    base_sha = subprocess.run(["git", "-C", str(workspace), "rev-parse", "HEAD"],
                              stdout=subprocess.PIPE).stdout.decode().strip()
    t = task("i01", allowed_paths=["dry_edit.txt", "src/*.py"], immutable_paths=[],
             base_sha=base_sha,
             test_command=[sys.executable, "-c",
                           "import pathlib,sys;sys.exit(0 if "
                           "pathlib.Path('dry_edit.txt').read_text().strip()!='original' else 1)"])
    tf = tasks_file(tmp_path / "tasks.json", [t])
    limpo = tmp_path / "base_limpa"
    subprocess.run(["git", "clone", "-q", str(workspace), str(limpo)], check=True)
    attempt = tmp_path / "attempts" / "i01-CTX-RS-0"
    proc = subprocess.run(
        [sys.executable, str(RUNNER), "--tasks", str(tf), "--task", "i01",
         "--condition", "CTX-RS", "--workspace", str(workspace), "--out", str(attempt),
         "--executor", "dry", "--allow-dry", "--acceptance-repo", str(limpo)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    assert proc.returncode == 0, proc.stdout
    man = json.loads((attempt / "manifest.json").read_text())
    assert man["acceptance"]["applied"] is True
    assert man["acceptance"]["exit_code"] == 0
    assert man["task"]["allowed_paths"] == ["dry_edit.txt", "src/*.py"]

    out = tmp_path / "mech.json"
    chk = run_eval("check", "--attempts", str(tmp_path / "attempts"), "--tasks", str(tf),
                   "--out", str(out))
    assert chk.returncode == 0, chk.stdout
    assert json.loads(out.read_text())["attempts"][0]["mechanical_verdict"] == "aceito"

    proc = bundle_all(tmp_path, [t], tmp_path)
    assert proc.returncode == 0, proc.stdout
    bundle = json.loads((tmp_path / "blind" / "bundle.json").read_text())
    assert len(bundle["items"]) == 1
    items = bundle["items"]
    p = write_json(tmp_path / "notas.json", scores_for(items))
    rep = tmp_path / "avaliacao.json"
    run_eval("unblind", "--bundle", str(tmp_path / "blind"), "--key",
             str(tmp_path / "custodia" / "blind_key.json"), "--scores", str(p),
             "--out", str(rep))
    doc = json.loads(rep.read_text())
    assert doc["condicoes"]["CTX-RS"]["tentativas"] == 1
    assert doc["condicoes"]["CTX-RS"]["aceitos"] == 1
