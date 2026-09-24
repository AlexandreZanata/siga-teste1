# SPDX-License-Identifier: Apache-2.0
"""Retrieval real sobre o corpus (BTC-E26-01-real). Somente leitura, sem modelo.

Difere de `dryrun.py` (fixtures sintéticas em tmp): aqui os textos vêm do checkout
real somente-leitura (`discover_cpp` + `*.py` de teste/funcional). Mesmos 3 braços
(A_busca/B_freq/C_adapter) para comparabilidade; C usa `extract_cpp_lexical` real
com salto por `#include`. Ouro dev em `benchmarks/bitcoin/e26_01_real.json`
(nenhum holdout; patch nulo). Reuso publicado (só leitura): `cpp_lex`,
`EXCLUDE_DIRS`, telemetria do core na versão pinada do checkout.
"""
from __future__ import annotations
import pathlib
import random

from archatlas.bitcoin.cpp_lex import CORE_SHA, discover_cpp, extract_cpp_lexical
from archatlas.dataset import EXCLUDE_DIRS
from archatlas.telemetry import build_manifest, score_delivery

ARMS = ("A_busca", "B_freq", "C_adapter")
BUDGET = 2000
TOKENIZER = "chars//4"
RUN_ID = "btc-e26-01-real-001"


def corpus_texts(root: pathlib.Path) -> dict[str, str]:
    """{rel: texto minúsculo} de C++ + Python. Ordenado; só lê bytes."""
    root = pathlib.Path(root)
    out: dict[str, str] = {}
    for p in discover_cpp(root):
        out[str(p.relative_to(root))] = p.read_bytes().decode("utf-8", errors="replace").lower()
    pys = [f for f in sorted(root.rglob("*.py"))
           if f.is_file() and not (EXCLUDE_DIRS & set(f.parts))]
    for p in pys:
        out[str(p.relative_to(root))] = p.read_bytes().decode("utf-8", errors="replace").lower()
    return out


def exec_arm(arm: str, root: pathlib.Path, texts: dict[str, str], query: str) -> tuple[set, str]:
    """Braço determinístico rotulado; qualidade só interpretável no REPORT."""
    toks = [t.lower() for t in query.split()]
    if arm == "A_busca":
        hit = {f for f, t in texts.items() if any(tok in t for tok in toks)}
        return hit, "busca textual sem modelo"
    if arm == "B_freq":
        ranked = sorted(texts, key=lambda f: (-sum(texts[f].count(t) for t in toks), f))
        return set(ranked[:4]), "ranking de frequencia sem modelo"
    if arm == "C_adapter":
        names = {pathlib.Path(f).stem.lower() for f in texts}
        seeds = {f for f in texts if any(tok in pathlib.Path(f).stem.lower() for tok in toks)
                 and pathlib.Path(f).stem.lower() in names}
        hop = set()
        for f in sorted(seeds):
            p = root / f
            if p.suffix not in {".c", ".h", ".hpp", ".cpp"} or not p.exists():
                continue
            for fact in extract_cpp_lexical(p)["facts"]:
                if fact["kind"] != "include":
                    continue
                base = fact["name"].split("/")[-1]
                hop |= {g for g in texts if pathlib.Path(g).name == base}
        return seeds | hop, "adaptador real btc-cpp-lex/1 + seeds textuais; sem modelo"
    raise ValueError(f"braço desconhecido: {arm}")


def used_tokens(root: pathlib.Path, delivered: set, budget: int = BUDGET) -> int:
    """Soma `len//4` em ordem até o budget (compatível com o dryrun)."""
    total, used = 0, 0
    for f in sorted(delivered):
        p = root / f
        if not p.exists():
            continue
        total += max(1, len(p.read_bytes()) // 4)
        if total <= budget:
            used = total
    return used


def verify_gold(tasks: list, texts: dict[str, str]) -> None:
    """Falha ruidosa se qualquer arquivo de ouro/dado não existir no corpus."""
    missing = []
    for t in tasks:
        for f in t.get("given_files", []) + t.get("expected_dev_files", []):
            if f not in texts:
                missing.append((t["id"], f))
    if missing:
        raise FileNotFoundError(f"ouro fora do corpus: {missing}")


def run_all(root: pathlib.Path, tasks: list, budgets=(2000, 8000), seed: int = 7) -> tuple[list, list]:
    """12–34 tarefas × 3 braços × budgets. Retorna (runs, manifests). Sem modelo."""
    root = pathlib.Path(root)
    texts = corpus_texts(root)
    verify_gold(tasks, texts)
    runs, mans = [], []
    order = 0
    for budget in budgets:
        pairs = [(t["id"], a) for t in tasks for a in ARMS]
        random.Random(f"{seed}-{budget}").shuffle(pairs)
        for task_id, arm in pairs:
            order += 1
            task = next(t for t in tasks if t["id"] == task_id)
            mans.append(build_manifest(task_id, arm, 1, order, budget, CORE_SHA, TOKENIZER))
            delivered, note = exec_arm(arm, root, texts, task["query"])
            if task.get("type") == "negative":
                rec = {"abstained": not delivered, "hit": False,
                       "delivered_count": len(delivered)}
            else:
                gt = {"files": [f for f in task["expected_dev_files"]
                                if f not in task.get("given_files", [])]}
                sc = score_delivery(delivered, gt)
                rec = {"hit": sc["hit"], "recall_set": sc["recall_set"],
                       "precision_set": sc["precision_set"]}
            runs.append({"task_id": task_id, "condition": arm, "budget": budget,
                         "order": order, "sha": CORE_SHA, "tokenizer": TOKENIZER,
                         "type": task.get("type"), "delivered": sorted(delivered),
                         "opened": sorted(delivered), "executor_note": note,
                         "used": used_tokens(root, delivered, budget),
                         "patch_accepted": None, "patch_note": "sem modelo",
                         "cost_total": None, "cost_note": "sem telemetria faturada",
                         "error": None} | rec)
    return runs, mans
