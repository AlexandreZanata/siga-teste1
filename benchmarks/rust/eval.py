#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Camada de avaliação: rubrica congelada, bundle cego e adjudicação.

Esta é a parte de R3/R5 que **não** depende de modelo nem de orçamento: o aceite de R3 exige
"revisão cega dos patches" e o de R5 exige que os patches sejam julgados "antes de abrir
condições e custos". O runner (`runner.py`) produz a tentativa; aqui ela vira item julgável,
sem rótulo, e o rótulo só volta depois que os julgamentos estão congelados.

Cinco decisões que valem explicação, cada uma contra algo mais fácil:

1. **A rubrica é dividida em mecânica e semântica, e a mecânica tem precedência.** Fatos
   executáveis (o patch aplica? o teste imutável do avaliador passa? o escopo declarado foi
   respeitado?) são calculados aqui, do artefato, e um deles reprovado já reprova a tentativa —
   nenhuma nota humana pode "compensar" um teste vermelho. Julgamento humano existe para o que
   não é executável: cumprimento do enunciado, regressão não coberta, alteração indevida.
2. **Fail-closed em tudo que é ambíguo.** Item `indeterminado`, item em `triagem` (julgado só por
   juiz LLM) e item `em_disputa` (dois revisores discordando sem adjudicação) **não** contam como
   sucesso. Uma taxa de sucesso que absorve dúvida é uma taxa de sucesso inflada.
3. **A chave do cegamento não é um arquivo do bundle.** Ela vai para um diretório de custódia que
   o bundle não contém nem alcança, e o caminho é recusado se estiver dentro de `--out`. Mesma
   regra de separação do ouro no runner, pelo mesmo motivo: separação de diretório não é
   isolamento, mas publicar o mapa é pior.
4. **Vazamento é escaneado em duas camadas, com severidades diferentes.** `hard` bloqueia a
   construção do bundle: rótulo de condição (`LEX-RS`, `CTX-RS`), chave proibida em qualquer JSON,
   caminho absoluto do workspace/ouro. `soft` é contado e declarado no bundle, não bloqueia:
   menções à própria ferramenta (`archatlas`, `atlas-read`) e a palavra `BASE` isolada. Isso é o
   que o protocolo §5 chama de "estilo do patch pode revelar pistas" — a resposta honesta é
   registrar, não fingir que não existe, e não chamar o estudo de duplo-cego.
5. **O julgamento é por tentativa, a inferência é por tarefa.** A unidade de inferência é a
   tarefa (pré-registro §1.2); duas tentativas da mesma tarefa não são duas tarefas. Por isso a
   agregação reporta as duas contagens, e o intervalo de confiança (R4) usa a tarefa como
   agrupamento.

O que este arquivo **não** faz: não chama modelo, não decide se o resultado científico é positivo
e não substitui o custodiante. Embaralhar IDs não é resultado — o próprio plano (§6, R5) diz para
não marcar conclusão pela existência de um teste de embaralhamento.

Uso:
    python benchmarks/rust/eval.py rubric --out experiments/rust/siga/<run_id>/rubric.json
    python benchmarks/rust/eval.py validate --tasks tarefas.json
    python benchmarks/rust/eval.py check  --attempts <dir>/attempts --tasks tarefas.json
    python benchmarks/rust/eval.py bundle --attempts <dir>/attempts --tasks tarefas.json \\
        --out <dir>/blind --key /custodia/2026-09-29/blind_key.json
    python benchmarks/rust/eval.py validate-scores --bundle <dir>/blind --key /custodia/... \\
        --scores notas.json
    python benchmarks/rust/eval.py unblind --bundle <dir>/blind --key /custodia/... \\
        --scores notas.json --out <dir>/avaliacao.json
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import random
import re
import shutil
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _bench import environment_manifest, write_json  # noqa: E402

RUBRIC_ID = "ATLAS-RUBRIC/1"
BUNDLE_SCHEMA = "atlas-blind-bundle/1"
KEY_SCHEMA = "atlas-blind-key/1"
SCORES_SCHEMA = "atlas-blind-scores/1"
REPORT_SCHEMA = "atlas-eval-report/1"
TASKS_SCHEMA = "atlas-tasks/2"
CATEGORIES = ("bug_local", "entre_arquivos", "testes_comportamento_de_api", "configuracao_interface")
SPLITS = ("smoke", "piloto", "holdout")
CONTAMINATION = ("baixo", "medio", "alto")
CONDITIONS = ("BASE", "LEX-RS", "CTX-RS")
REVIEW_SAMPLE_FRACTION = 0.25
JUDGE_KINDS = ("human", "llm")
VERDICTS = ("aceito", "rejeitado", "indeterminado")

# --- rubrica --------------------------------------------------------------------------

MECHANICAL_ITEMS = [
    {
        "id": "M1",
        "name": "patch_aplica_em_base_limpa",
        "kind": "mechanical",
        "question": "o patch aplica com `git apply --check` numa base limpa?",
        "fonte": "`acceptance.applied` da tentativa",
        "reprovado_significa": "rejeitado — patch que nao aplica nao e solucao",
    },
    {
        "id": "M2",
        "name": "testes_do_avaliador_passam",
        "kind": "mechanical",
        "question": "o comando de aceitacao declarado na tarefa sai com codigo 0?",
        "fonte": "`acceptance.exit_code`; o comando e imutavel e do avaliador",
        "reprovado_significa": "rejeitado. Testes novos do agente sao evidencia "
                               "complementar, nunca o criterio",
    },
    {
        "id": "M3",
        "name": "patch_nao_vazio",
        "kind": "mechanical",
        "question": "a tentativa produziu alguma alteracao?",
        "fonte": "`patch.empty` e tamanho do arquivo de patch",
        "reprovado_significa": "rejeitado — tentativa sem alteracao e falha, nao "
                               "'nao havia o que mudar'",
    },
    {
        "id": "M4",
        "name": "escopo_declarado_respeitado",
        "kind": "mechanical",
        "question": "todos os arquivos tocados estao em `allowed_paths` da tarefa?",
        "fonte": "caminhos extraidos do patch contra os globs da tarefa",
        "reprovado_significa": "rejeitado — fora de escopo e alteracao indevida "
                               "por definicao, antes de qualquer revisao",
    },
    {
        "id": "M5",
        "name": "sem_enfraquecer_teste_imutavel",
        "kind": "mechanical",
        "question": "o patch toca algum arquivo de `immutable_paths` (testes do avaliador)?",
        "fonte": "caminhos do patch contra `immutable_paths`",
        "reprovado_significa": "rejeitado — o protocolo nao confia em teste que o agente "
                               "possa ter enfraquecido",
    },
    {
        "id": "M6",
        "name": "nao_parou_no_teto",
        "kind": "mechanical",
        "question": "a tentativa terminou por si, sem ser morta por um teto operacional?",
        "fonte": "`stopped_by` / `stopped_killed` da tentativa",
        "reprovado_significa": "rejeitado — falha atribuivel ao braco conta contra ele; "
                               "teto atingido nao e sucesso parcial",
    },
]

HUMAN_ITEMS = [
    {
        "id": "H1",
        "name": "atende_ao_enunciado",
        "kind": "human",
        "question": "o patch resolve o que o enunciado pede, e resolve inteiro?",
        "o_que_nao_e_evidencia": "semelhanca textual com o patch de referencia; "
                                 "solucao alternativa correta e aceita",
    },
    {
        "id": "H2",
        "name": "sem_regressao_nao_coberta",
        "kind": "human",
        "question": "o patch quebra algo que os testes do avaliador nao cobrem?",
        "o_que_nao_e_evidencia": "o verde do comando de aceitacao: ele cobre o aceite, "
                                 "nao o sistema",
    },
    {
        "id": "H3",
        "name": "sem_alteracao_indevida",
        "kind": "human",
        "question": "ha alteracao nao relacionada, reescrita gratuita, remocao ou "
                    "churn de configuracao?",
        "o_que_nao_e_evidencia": "tamanho do diff isolado — patch grande pode ser a "
                                 "solucao correta e patch pequeno pode estar errado",
    },
]

# Campo que **nao** e item: identidade textual ao patch de referencia nao e criterio (protocolo
# §3.5). Fica registrado por item para que o relatorio possa mostrar quantos aceites diferem do
# de referencia — prova de que a rubrica nao virou comparacao de texto.
NOTE_FIELDS = ["differs_from_reference", "notes"]

FORBIDDEN_KEYS = {
    "condition", "model", "cost", "usage", "order", "telemetry", "run_id", "tool",
    "environment", "gold_isolation", "evidence_class", "executor_seconds", "processes",
    "snapshot", "stopped_by", "stopped_killed", "policy", "provider_billed", "currency",
}

HARD_PATTERNS = [
    (re.compile(r"\bLEX-RS\b"), "rotulo de condicao LEX-RS"),
    (re.compile(r"\bCTX-RS\b"), "rotulo de condicao CTX-RS"),
    (re.compile(r"\bblind_key\b"), "nome do arquivo de custodia"),
    (re.compile(r"ATLAS_CONDITION"), "variavel de ambiente da condicao"),
]

SOFT_PATTERNS = [
    (re.compile(r"\bBASE\b"), "palavra BASE isolada (rotulo de condicao ou palavra comum?)"),
    (re.compile(r"archatlas"), "auto-referencia a ferramenta"),
    (re.compile(r"atlas-read|ATLAS_TELEMETRY|ATLAS_WORKSPACE"), "nome de ferramenta/variavel do runner"),
]


def rubric() -> dict:
    return {
        "schema": RUBRIC_ID,
        "frozen_at": "2026-09-29",
        "precedencia": "mecanica antes de semantica: item mecanico reprovado reprova a tentativa, "
                       "sem compensacao por nota humana",
        "estados_que_nao_contam_como_sucesso": ["indeterminado", "triagem", "em_disputa"],
        "items": [*MECHANICAL_ITEMS, *HUMAN_ITEMS],
        "veredito_da_tentativa": "(mecanica reprovada -> rejeitado) | (mecanica indeterminada -> "
                                 "indeterminado) | (humana reprovada -> rejeitado) | (humana "
                                 "indeterminada/triagem/disputa -> indeterminado) | (tudo aceito "
                                 "-> aceito)",
        "amostra_de_revisao_dupla": REVIEW_SAMPLE_FRACTION,
        "campos_de_nota_sem_veredito": NOTE_FIELDS,
        "nota": "contagens de sucesso incluem falhas no denominador; falta de custo bloqueia "
                "custo por sucesso, nunca vira zero",
    }


# --- tarefas --------------------------------------------------------------------------


def load_tasks(path: Path) -> dict:
    doc = json.loads(path.read_text())
    if doc.get("schema") != TASKS_SCHEMA:
        raise SystemExit(
            f"conjunto de tarefas em {doc.get('schema')!r}: a avaliacao exige {TASKS_SCHEMA!r} "
            "— sem escopo declarado (`allowed_paths`) nao ha checagem mecanica de escopo, e "
            "avaliar sem ela e pior que nao avaliar"
        )
    return doc


def validate_tasks(doc: dict, allow_imbalance: bool = False) -> dict:
    problems: list[str] = []
    seen: set[str] = set()
    for t in doc.get("tasks", []):
        tid = t.get("id")
        if not tid:
            problems.append("tarefa sem `id`")
            continue
        if tid in seen:
            problems.append(f"{tid}: id repetido")
        seen.add(tid)
        if t.get("split") not in SPLITS:
            problems.append(f"{tid}: `split` fora de {SPLITS}: {t.get('split')!r}")
        if t.get("category") not in CATEGORIES:
            problems.append(f"{tid}: `category` fora de {CATEGORIES}: {t.get('category')!r}")
        for campo in ("statement", "test_command", "base_sha", "origin"):
            if not t.get(campo):
                problems.append(f"{tid}: `{campo}` ausente (obrigatorio)")
        if not t.get("allowed_paths"):
            problems.append(f"{tid}: `allowed_paths` vazio — sem ele o escopo nao e verificavel")
        if t.get("immutable_paths") is None:
            problems.append(f"{tid}: `immutable_paths` ausente (use [] se a tarefa nao tem teste imutavel)")
        if t.get("contamination_risk") not in CONTAMINATION:
            problems.append(f"{tid}: `contamination_risk` fora de {CONTAMINATION}")
        if not t.get("contamination_note"):
            problems.append(f"{tid}: `contamination_note` ausente — o protocolo §3 pede "
                            "origem e risco registrados por tarefa")
    counts = {c: 0 for c in CATEGORIES}
    for t in doc.get("tasks", []):
        if t.get("category") in counts:
            counts[t["category"]] += 1
    balanco = {k: v for k, v in counts.items()}
    balanced = len(set(balanco.values())) == 1
    note = None
    if not balanced and not allow_imbalance:
        note = ("o pre-registro §1.2 fixou 4/4/4/4 para o piloto; conjunto desbalanceado so "
                "passa com --allow-imbalance, e a razao tem de ir no relatorio")
        problems.append(note)
    return {"tasks": len(seen), "categories": balanco, "balanced": balanced,
            "problems": problems, "sealed": bool(doc.get("sealed"))}


# --- checagem mecânica ----------------------------------------------------------------


def patch_paths(patch_text: str) -> list[str]:
    out: list[str] = []
    for line in patch_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                p = parts[3]
                out.append(p[2:] if p.startswith("b/") else p)
    # renames e binarios sem `diff --git` (defensivo): nao inventa caminho, so completa
    for line in patch_text.splitlines():
        if line.startswith("rename to "):
            p = line[len("rename to "):].strip()
            if p and p not in out:
                out.append(p)
    return out


def matches_any(path: str, globs: list[str]) -> bool:
    """Glob de shell (`fnmatch`): `*` atravessa diretórios. Declarado no contrato da rubrica."""
    return any(fnmatch.fnmatch(path, g) for g in globs)


def check_attempt(attempt: Path, tasks: dict) -> dict:
    man = json.loads((attempt / "manifest.json").read_text())
    task = next((t for t in tasks["tasks"] if t["id"] == man["task"]["id"]), None)
    if task is None:
        raise SystemExit(f"{attempt}: tarefa {man['task']['id']!r} ausente do conjunto")
    patch_file = attempt / man["patch"]["file"]
    patch_text = patch_file.read_text(errors="replace") if patch_file.exists() else ""
    paths = patch_paths(patch_text)
    acc = man.get("acceptance") or {}
    fora = [p for p in paths if not matches_any(p, task["allowed_paths"])]
    imutaveis = [p for p in paths if matches_any(p, task.get("immutable_paths") or [])]
    stopped = bool(man.get("stopped_by") or man.get("stopped_killed"))
    items = {
        "M1": {"ok": acc.get("applied") is True,
               "observed": acc.get("applied"),
               "reason": acc.get("reason")},
        "M2": {"ok": acc.get("applied") is True and acc.get("exit_code") == 0,
               "observed": acc.get("exit_code")},
        "M3": {"ok": bool(patch_text.strip()),
               "observed": {"patch_bytes": man["patch"].get("bytes"), "paths": paths}},
        "M4": {"ok": not fora, "observed": {"fora_do_escopo": fora,
                                            "allowed_paths": task["allowed_paths"]}},
        "M5": {"ok": not imutaveis, "observed": {"tocados": imutaveis,
                                                 "immutable_paths": task.get("immutable_paths") or []}},
        "M6": {"ok": not stopped, "observed": {"stopped_by": man.get("stopped_by")}},
    }
    rejeitados = [k for k, v in items.items() if not v["ok"]]
    return {
        "attempt": attempt.name,
        "task_id": man["task"]["id"],
        "condition": man.get("condition"),
        "paths": paths,
        "mechanical": items,
        "mechanical_verdict": "rejeitado" if rejeitados else "aceito",
        "mechanical_rejected_items": rejeitados,
        "acceptance_command": man["task"].get("test_command"),
        "evidence_class": man.get("evidence_class"),
    }


def cmd_check(args) -> int:
    tasks = load_tasks(Path(args.tasks))
    dirs = sorted(p.parent for p in Path(args.attempts).glob("*/manifest.json"))
    if not dirs:
        raise SystemExit(f"nenhuma tentativa com manifest.json em {args.attempts}")
    rows = [check_attempt(d, tasks) for d in dirs]
    out = {"schema": "atlas-mechanical-check/1", "rubric": RUBRIC_ID,
            "attempts": rows}
    if args.out:
        write_json(Path(args.out), out)
    rejeitadas = [r for r in rows if r["mechanical_verdict"] == "rejeitado"]
    print(f"{len(rows)} tentativas, {len(rejeitadas)} reprovadas pela mecanica antes de "
          f"qualquer revisao")
    for r in rejeitadas:
        print(f"  {r['attempt']} [{r['task_id']}] {r['mechanical_rejected_items']}")
    if args.out:
        print(f"-> {args.out}")
    return 0 if not rejeitadas else 1


# --- vazamento e bundle ---------------------------------------------------------------


def scan_text(text: str) -> dict:
    hard = [{"pattern": why, "count": len(rx.findall(text))}
            for rx, why in HARD_PATTERNS if rx.search(text)]
    soft = [{"pattern": why, "count": len(rx.findall(text))}
            for rx, why in SOFT_PATTERNS if rx.search(text)]
    return {"hard": hard, "soft": soft}


def forbidden_keys(obj, found: list | None = None, path: str = "$") -> list[str]:
    found = [] if found is None else found
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in FORBIDDEN_KEYS:
                found.append(f"{path}.{k}")
            forbidden_keys(v, found, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            forbidden_keys(v, found, f"{path}[{i}]")
    return found


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def bundle_sha256(bundle: Path) -> str:
    files = sorted(p for p in bundle.rglob("*") if p.is_file())
    h = hashlib.sha256()
    for p in files:
        h.update(p.relative_to(bundle).as_posix().encode())
        h.update(b"\0")
        h.update(hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()


def opaque_id(nonce: str, key: str) -> str:
    return "it-" + hashlib.sha256(f"{nonce}|{key}".encode()).hexdigest()[:10]


def cmd_bundle(args) -> int:
    tasks = load_tasks(Path(args.tasks))
    attempts = sorted(p.parent for p in Path(args.attempts).glob("*/manifest.json"))
    if not attempts:
        raise SystemExit(f"nenhuma tentativa com manifest.json em {args.attempts}")
    out = Path(args.out).resolve()
    key_path = Path(args.key).resolve()
    if out == key_path or out in key_path.parents or key_path in out.parents:
        raise SystemExit(
            "BLOQUEADO: a chave do cegamento esta dentro (ou contem) o diretorio do bundle "
            f"({key_path} vs {out}). Publicar o mapa anula o cegamento."
        )
    if key_path.exists() and not args.force_key:
        raise SystemExit(f"chave ja existe em {key_path}: custodia nao e sobrescrita. "
                         "Use outro caminho (ou --force-key, que apaga a anterior).")
    if out.exists() and any(out.iterdir()) and not args.force_bundle:
        raise SystemExit(f"{out} nao esta vazio; um bundle nao e sobrescrito em silencio")
    if out.exists() and args.force_bundle:
        shutil.rmtree(out)
    (out / "patches").mkdir(parents=True, exist_ok=True)
    (out / "statements").mkdir(parents=True, exist_ok=True)

    seed = args.seed
    rng = random.Random(seed)
    # Nonce derivado de seed + destino, **sem** relógio: mesma entrada e mesma seed produzem o
    # mesmo bundle, e quem audita pode reproduzir a permutação. O id continua opaco — não dá
    # para ler condição nele — mas deixa de ser irrepetível.
    nonce = sha256_bytes(f"{seed}|{out}".encode())[:16]
    items = []
    mapping = {}
    leaks: list[dict] = []
    for attempt in attempts:
        man = json.loads((attempt / "manifest.json").read_text())
        task = next((t for t in tasks["tasks"] if t["id"] == man["task"]["id"]), None)
        if task is None:
            raise SystemExit(f"{attempt}: tarefa {man['task']['id']!r} ausente do conjunto")
        # O escopo declarado entra na comparação porque a checagem mecânica o usa: se o
        # manifesto registrou outro `allowed_paths`, a tentativa correu sob outro escopo e
        # julgá-la com o escopo do arquivo atual mediria a coisa errada.
        for campo in ("split", "category", "base_sha", "allowed_paths", "immutable_paths"):
            declared, esperado = man["task"].get(campo), task.get(campo)
            if declared is not None and esperado is not None and declared != esperado:
                raise SystemExit(
                    f"{attempt}: `{campo}` do manifesto difere do conjunto de tarefas — "
                    "artefato adulterado, conjunto trocado ou escopo divergente; "
                    "julgar assim mediria outro escopo"
                )
        item_id = opaque_id(nonce, attempt.name)
        patch = attempt / man["patch"]["file"]
        patch_text = patch.read_text(errors="replace") if patch.exists() else ""
        statement = (attempt / "statement.txt").read_text(errors="replace") \
            if (attempt / "statement.txt").exists() else ""
        (out / "patches" / f"{item_id}.patch").write_text(patch_text)
        (out / "statements" / f"{item_id}.txt").write_text(statement)
        acc = man.get("acceptance") or {}
        mech = check_attempt(attempt, tasks)
        item = {
            "item_id": item_id,
            "task": {"id": task["id"], "category": task["category"], "split": task["split"],
                     "base_sha": task["base_sha"],
                     "allowed_paths": task["allowed_paths"],
                     "immutable_paths": task.get("immutable_paths") or []},
            "statement_file": f"statements/{item_id}.txt",
            "patch_file": f"patches/{item_id}.patch",
            "acceptance": {"command": task["test_command"], "applied": acc.get("applied"),
                           "exit_code": acc.get("exit_code"),
                           "output_file": None,
                           "output_reason": "o avaliador reexecuta o comando na base limpa; a saida "
                                            "do runner nao entra no bundle porque pode citar "
                                            "artefatos do braco"},
            "mechanical": {"verdict": mech["mechanical_verdict"],
                           "rejected_items": mech["mechanical_rejected_items"]},
        }
        items.append(item)
        mapping[item_id] = {
            "attempt": attempt.name,
            "task_id": task["id"],
            "condition": man.get("condition"),
            "repetition": (man.get("order") or {}).get("repetition"),
            "position": (man.get("order") or {}).get("position"),
            "outcome": man.get("outcome"),
            "evidence_class": man.get("evidence_class"),
            "cost": man.get("cost"),
            "usage": man.get("usage"),
            "executor_seconds": man.get("executor_seconds"),
            "mechanical_verdict": mech["mechanical_verdict"],
        }
        for path_field in ("statement_file", "patch_file"):
            rel = item[path_field]
            txt = (out / rel).read_text(errors="replace")
            sc = scan_text(txt)
            if sc["hard"]:
                leaks.append({"item": item_id, "file": rel, "severity": "hard", "hits": sc["hard"]})
            if sc["soft"]:
                leaks.append({"item": item_id, "file": rel, "severity": "soft", "hits": sc["soft"]})
        # Só o item é escaneado como conteúdo do bundle. O `mapping` guarda condição e custo
        # de propósito — e por isso ele **não** entra no bundle: vai para a chave, em custódia.
        fk = forbidden_keys(item)
        if fk:
            leaks.append({"item": item_id, "file": "json:item", "severity": "hard",
                          "hits": [{"pattern": "chave proibida no item", "keys": fk}]})
    hard = [l for l in leaks if l["severity"] == "hard"]
    soft = [l for l in leaks if l["severity"] == "soft"]
    if hard:
        print(json.dumps({"bloqueado": True, "hard": hard}, indent=2, ensure_ascii=False))
        raise SystemExit("BLOQUEADO: vazamento `hard` no bundle; corrigir a entrada antes de cegar")

    rng.shuffle(items)
    # a amostra de revisão dupla é sorteada com a mesma seed, sobre os itens que a mecânica
    # aceitou — o protocolo §5 propõe 25% dos aceites revisados por um segundo revisor
    aceitos = [it["item_id"] for it in items if it["mechanical"]["verdict"] == "aceito"]
    k = max(1, int(round(len(aceitos) * REVIEW_SAMPLE_FRACTION))) if aceitos else 0
    sample = sorted(rng.sample(aceitos, k)) if k else []
    bundle_doc = {
        "schema": BUNDLE_SCHEMA,
        "rubric": RUBRIC_ID,
        "items_order_is_randomized": True,
        "blinding_level": (
            "simples: o avaliador nao ve condicao, modelo, custo, ordem nem telemetria; o "
            "executor nao esta cego. Nao e duplo-cego — ver `declared_leak_channels`"
        ),
        "declared_leak_channels": [
            "estilo do patch e auto-referencia a ferramenta podem sugerir o braco; registrar "
            "`suspicion_of_condition` por item",
            "o revisor avalia um patch por vez, mas o mesmo revisor ve patches de todos os bracos",
            "a presenca da ferramenta de contexto nas ferramentas usadas nao aparece no bundle, "
            "mas o estilo de quem a usou pode aparecer no patch",
        ],
        "items": items,
        "soft_leaks": soft,
    }
    write_json(out / "bundle.json", bundle_doc)
    write_json(out / "rubric.json", rubric())
    bsha = bundle_sha256(out)
    key = {
        "schema": KEY_SCHEMA,
        "bundle_sha256": f"sha256:{bsha}",
        "created": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "seed": seed,
        "custody": {
            "holder": args.custodian or None,
            "holder_reason": None if args.custodian else "informe --custodian: a chave precisa de dono",
            "may_be_opened": "depois dos julgamentos e da adjudicacao congelados",
            "not_inside_bundle": True,
        },
        "review_sample": sample,
        "mapping": mapping,
        "leak_scan": {"hard": 0, "soft": len(soft), "soft_detail": soft},
        "environment": environment_manifest(),
    }
    key_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(key_path, key)
    if not args.custodian:
        print("AVISO: sem --custodian a chave fica sem dono declarado")
    print(f"{len(items)} itens cegados em {out}; chave em {key_path} "
          f"(sha256 do bundle {bsha[:12]}…, amostra dupla {len(sample)})")
    print(f"vazamento: 0 hard, {len(soft)} soft (declarados no bundle)")
    return 0


# --- notas e adjudicação --------------------------------------------------------------


def load_json(path: Path) -> dict:
    return json.loads(Path(path).read_text())


def validate_scores(scores: dict, bundle: dict, key: dict) -> dict:
    problems: list[str] = []
    if scores.get("schema") != SCORES_SCHEMA:
        problems.append(f"schema de notas desconhecido: {scores.get('schema')!r}")
    if scores.get("rubric") != bundle.get("rubric"):
        problems.append("notas de outra versao de rubrica")
    if not key.get("review_sample") and bundle["items"]:
        problems.append("chave sem amostra de revisao dupla registrada")
    fk = forbidden_keys(scores)
    if fk:
        problems.append(f"notas com chave proibida ({', '.join(fk)}): o avaliador nao pode "
                        "receber nem devolver condicao/custo/ordem")
    legit = {it["item_id"] for it in bundle["items"]}
    sample = set(key.get("review_sample") or [])
    for nota in scores.get("items", []):
        iid = nota.get("item_id")
        if iid not in legit:
            problems.append(f"{iid}: item fora do bundle")
            continue
        verdicts = nota.get("verdicts") or []
        if not verdicts:
            problems.append(f"{iid}: sem veredito")
            continue
        for v in verdicts:
            if v.get("verdict") not in VERDICTS:
                problems.append(f"{iid}: veredito fora de {VERDICTS}: {v.get('verdict')!r}")
            if v.get("kind") not in JUDGE_KINDS:
                problems.append(f"{iid}: `kind` fora de {JUDGE_KINDS}: {v.get('kind')!r}")
            if not v.get("reviewer"):
                problems.append(f"{iid}: veredito sem `reviewer` (autoria e parte do registro)")
        sc = scan_text(json.dumps([{k: v for k, v in v.items() if k in ("notes", "why")}
                                   for v in verdicts], ensure_ascii=False))
        if sc["hard"]:
            problems.append(f"{iid}: texto da nota cita rotulo de condicao {sc['hard']}")
    return {"problems": problems, "sample": sorted(sample)}


def adjudicate(scores: dict, bundle: dict, key: dict) -> dict:
    """Veredito por item, com as regras de fail-closed do cabeçalho."""
    items = {nota["item_id"]: nota for nota in scores.get("items", [])}
    sample = set(key.get("review_sample") or [])
    out = {}
    for item in bundle["items"]:
        iid = item["item_id"]
        nota = items.get(iid)
        mech = item["mechanical"]["verdict"]
        if nota is None:
            out[iid] = {"status": "sem_nota", "state": "indeterminado",
                        "reason": "item sem julgamento registrado"}
            continue
        verdicts = nota.get("verdicts") or []
        humanos = [v for v in verdicts if v.get("kind") == "human"]
        rejects = [v for v in verdicts if v.get("verdict") == "rejeitado"]
        indef = [v for v in verdicts if v.get("verdict") == "indeterminado"]
        precisa_segundo = bool(rejects) or bool(indef) or iid in sample
        segundo = nota.get("second_verdict") or (verdicts[1] if len(verdicts) > 1 else None)
        adj = nota.get("adjudication")
        if mech == "rejeitado":
            out[iid] = {"status": "mecanica_reprovada", "state": "rejeitado",
                        "items": item["mechanical"]["rejected_items"]}
            continue
        if not humanos:
            out[iid] = {"status": "triagem_llm", "state": "indeterminado",
                        "reason": "juiz LLM tria, mas nao constitui gabarito sozinho (protocolo §5)"}
            continue
        if precisa_segundo and not segundo:
            out[iid] = {"status": "falta_segundo_revisor", "state": "indeterminado",
                        "reason": "reprovacao, indeterminacao ou item da amostra de 25% "
                                  "exige segundo revisor"}
            continue
        primeiro = (humanos or verdicts)[0].get("verdict")
        segundo_v = (segundo or {}).get("verdict")
        if primeiro == "indeterminado":
            out[iid] = {"status": "indeterminado_por_revisor", "state": "indeterminado",
                        "reason": "revisor humano declarou nao saber decidir: nao vira aceite"}
            continue
        if segundo_v and segundo_v != primeiro:
            if adj:
                out[iid] = {"status": "adjudicado", "state": adj.get("verdict"),
                            "reason": "dois revisores discordaram; adjudicacao registrada"}
            else:
                out[iid] = {"status": "em_disputa", "state": "indeterminado",
                            "reason": "revisores discordam sem adjudicacao; nao conta como sucesso"}
            continue
        out[iid] = {"status": "julgado", "state": primeiro}
    return out


def cmd_validate_scores(args) -> int:
    bundle = load_json(Path(args.bundle) / "bundle.json")
    key = load_json(Path(args.key))
    scores = load_json(Path(args.scores))
    res = validate_scores(scores, bundle, key)
    adjud = adjudicate(scores, bundle, key)
    nao_sucesso = {k: v for k, v in adjud.items() if v["state"] != "aceito"}
    print(f"{len(bundle['items'])} itens; {len(nao_sucesso)} sem aceite")
    for k, v in sorted(nao_sucesso.items()):
        print(f"  {k}: {v['status']} ({v['state']})")
    if res["problems"]:
        print(json.dumps({"problemas": res["problems"]}, indent=2, ensure_ascii=False))
        return 1
    print("notas validas: sem chave proibida, sem rotulo de condicao, amostra dupla coberta")
    return 0


# --- un-blind e agregação --------------------------------------------------------------


def cmd_unblind(args) -> int:
    bundle_dir = Path(args.bundle).resolve()
    bundle = load_json(bundle_dir / "bundle.json")
    key = load_json(Path(args.key))
    scores = load_json(Path(args.scores))
    atual = bundle_sha256(bundle_dir)
    if f"sha256:{atual}" != key.get("bundle_sha256"):
        raise SystemExit(
            f"BLOQUEADO: o bundle mudou depois que a chave foi escrita "
            f"({key.get('bundle_sha256')} vs sha256:{atual}). Rotulos nao podem ser abertos "
            "sobre um bundle diferente daquele que foi julgado."
        )
    val = validate_scores(scores, bundle, key)
    if val["problems"]:
        print(json.dumps({"problemas": val["problems"]}, indent=2, ensure_ascii=False))
        raise SystemExit("BLOQUEADO: notas invalidas; corrigir antes de abrir rotulos")
    adjud = adjudicate(scores, bundle, key)

    por_cond: dict[str, dict] = {}
    blinding = {"guesses": 0, "correct": 0, "items_with_suspicion": 0, "base_rate": None}
    mapa = key["mapping"]
    for item in bundle["items"]:
        iid = item["item_id"]
        info = mapa[iid]
        cond = info["condition"]
        st = adjud[iid]["state"]
        c = por_cond.setdefault(cond, {"attempts": 0, "aceitos": 0, "estados": {},
                                       "tasks": {}, "cost_null": 0, "cost_total": 0.0})
        c["attempts"] += 1
        c["estados"][st] = c["estados"].get(st, 0) + 1
        c["aceitos"] += 1 if st == "aceito" else 0
        c["tasks"].setdefault(info["task_id"], False)
        c["tasks"][info["task_id"]] = c["tasks"][info["task_id"]] or st == "aceito"
        custo = (info.get("cost") or {}).get("provider_billed")
        if custo is None:
            c["cost_null"] += 1
        else:
            c["cost_total"] += float(custo)
        nota = next((n for n in scores.get("items", []) if n["item_id"] == iid), {})
        palpite = nota.get("suspicion_of_condition")
        if palpite:
            blinding["items_with_suspicion"] += 1
            blinding["guesses"] += 1
            blinding["correct"] += 1 if palpite == cond else 0
    n_cond = len(por_cond) or 1
    blinding["base_rate"] = round(1 / n_cond, 3)

    tabela = {}
    difere = {"aceitos_que_diferem_da_referencia": 0, "respostas": 0,
              "por_condicao": {}}
    for cond, c in sorted(por_cond.items()):
        custo_ok = c["cost_null"] == 0 and c["attempts"] > 0
        if custo_ok and c["aceitos"]:
            custo_por_sucesso, motivo = round(c["cost_total"] / c["aceitos"], 4), None
        elif not custo_ok:
            custo_por_sucesso, motivo = None, (
                "custo faturado ausente em %d de %d tentativas (P2 pendente): falta de custo "
                "bloqueia a conclusao, nao vira zero" % (c["cost_null"], c["attempts"]))
        else:
            custo_por_sucesso, motivo = None, (
                "zero aceites: custo por sucesso e infinito, nao um numero")
        tabela[cond] = {
            "tentativas": c["attempts"],
            "aceitos": c["aceitos"],
            "success_rate_por_tentativa": round(c["aceitos"] / c["attempts"], 4),
            "tarefas": len(c["tasks"]),
            "tarefas_com_aceite": sum(1 for v in c["tasks"].values() if v),
            "success_rate_por_tarefa": round(
                sum(1 for v in c["tasks"].values() if v) / len(c["tasks"]), 4) if c["tasks"] else None,
            "estados": c["estados"],
            "cost_per_success": custo_por_sucesso,
            "cost_per_success_reason": motivo,
        }
        resp = [n for n in scores.get("items", []) if mapa.get(n["item_id"], {})
                .get("condition") == cond and n.get("differs_from_reference") is not None]
        aceitos_resp = [n for n in resp
                        if adjud.get(n["item_id"], {}).get("state") == "aceito"]
        difere["por_condicao"][cond] = {
            "respostas": len(resp),
            "aceitos": len(aceitos_resp),
            "aceitos_que_diferem_da_referencia": sum(
                1 for n in aceitos_resp if n.get("differs_from_reference")),
        }
        difere["respostas"] += len(resp)
        difere["aceitos_que_diferem_da_referencia"] += difere["por_condicao"][cond][
            "aceitos_que_diferem_da_referencia"]
    report = {
        "schema": REPORT_SCHEMA,
        "rubric": bundle["rubric"],
        "bundle_sha256": key["bundle_sha256"],
        "condicoes": tabela,
        "unidade_de_inferencia": "tarefa; tentativas da mesma tarefa nao sao tarefas "
                                 "independentes (pre-registro §1.2)",
        "blinding": {**blinding,
                     "note": "acuracia do palpite de condicao mede a qualidade do cegamento; "
                             "embaralhar IDs nao e resultado (plano §6, R5)"},
        "identidade_textual": {**difere,
                               "note": "o protocolo §3.5 proibe exigir identidade ao patch de "
                                       "referencia; este quadro existe para mostrar que nao foi exigida"},
        "nao_contam_como_sucesso": {k: v for k, v in adjud.items() if v["state"] != "aceito"},
        "aviso": "infraestrutura de avaliacao. Sem modelo real, sem patch de modelo e sem "
                 "rubrica aplicada por humano, nada aqui e conclusao cientifica.",
    }
    if args.out:
        write_json(Path(args.out), report)
    print(json.dumps({c: {"tentativas": v["tentativas"], "aceitos": v["aceitos"],
                          "success_rate_por_tentativa": v["success_rate_por_tentativa"]}
                      for c, v in tabela.items()}, indent=2, ensure_ascii=False))
    print(f"cegamento: {blinding['correct']} de {blinding['guesses']} palpites corretos "
          f"(base {blinding['base_rate']})")
    if args.out:
        print(f"-> {args.out}")
    return 0


# --- CLI ------------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("rubric", help="escreve a rubrica congelada")
    p.add_argument("--out", default=None)
    p.set_defaults(func=cmd_rubric)

    p = sub.add_parser("validate", help="valida um conjunto de tarefas")
    p.add_argument("--tasks", required=True)
    p.add_argument("--allow-imbalance", action="store_true")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("check", help="checagem mecanica das tentativas")
    p.add_argument("--attempts", required=True)
    p.add_argument("--tasks", required=True)
    p.add_argument("--out", default=None)
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("bundle", help="constroi o bundle cego e a chave em custodia")
    p.add_argument("--attempts", required=True)
    p.add_argument("--tasks", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--key", required=True, help="caminho FORA do bundle (custodia)")
    p.add_argument("--seed", type=int, default=20260929)
    p.add_argument("--custodian", default=None, help="quem guarda a chave")
    p.add_argument("--force-bundle", action="store_true")
    p.add_argument("--force-key", action="store_true",
                   help="sobrescreve a chave existente, invalidando a custodia anterior")
    p.set_defaults(func=cmd_bundle)

    p = sub.add_parser("validate-scores", help="valida um conjunto de julgamentos")
    p.add_argument("--bundle", required=True)
    p.add_argument("--key", required=True)
    p.add_argument("--scores", required=True)
    p.set_defaults(func=cmd_validate_scores)

    p = sub.add_parser("unblind", help="abre rotulos e agrega por condicao")
    p.add_argument("--bundle", required=True)
    p.add_argument("--key", required=True)
    p.add_argument("--scores", required=True)
    p.add_argument("--out", default=None)
    p.set_defaults(func=cmd_unblind)

    args = ap.parse_args()
    return args.func(args)


def cmd_validate(args) -> int:
    res = validate_tasks(load_tasks(Path(args.tasks)), allow_imbalance=args.allow_imbalance)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0 if not res["problems"] else 1


def cmd_rubric(args) -> int:
    doc = rubric()
    if args.out:
        write_json(Path(args.out), doc)
        print(f"rubrica {RUBRIC_ID} -> {args.out}")
    else:
        print(json.dumps(doc, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
