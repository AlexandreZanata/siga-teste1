# SPDX-License-Identifier: Apache-2.0
"""Retrieval real sobre o corpus (BTC-E26-01). Somente leitura, sem modelo.

Textos do checkout real somente-leitura (`discover_cpp` + `*.py`). Mesmos 3 braços
(A_busca/B_freq/C_adapter); C usa `extract_cpp_lexical` real com salto por `#include`
limitado por teto de fan-in (`FANIN_CAP`; hubs onipresentes pulados com registro).
Ouro dev em `benchmarks/bitcoin/e26_01_dev.json` (nenhum holdout; patch nulo).
Reuso publicado (só leitura): `cpp_lex`, `EXCLUDE_DIRS`, telemetria do core.
"""
from __future__ import annotations
import pathlib
import random
import re
import sqlite3

from archatlas.bitcoin.bm25text import bm25_lines
from archatlas.bitcoin.cpp_lex import CORE_SHA, discover_cpp, extract_cpp_lexical
from archatlas.bitcoin.vocab import expand_query
from archatlas.dataset import EXCLUDE_DIRS
from archatlas.telemetry import build_manifest, score_delivery

ARMS = ("A_busca", "B_freq", "C_adapter")
BUDGET = 2000
TOKENIZER = "chars//4"
RUN_ID = "btc-e26-01-real-001"
FANIN_CAP = 25  # teto de fan-in (p90≈27 em v31.1); alvos acima pulados com registro
D_TOP_FILES = 10  # D_bm25 (braço extra, fora de ARMS) entrega os top arquivos por BM25


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


def build_fanin(root: pathlib.Path) -> dict[str, int]:
    """{basename de header: nº de arquivos que o incluem} (1 voto por arquivo)."""
    root = pathlib.Path(root)
    fanin: dict[str, int] = {}
    for p in discover_cpp(root):
        seen = set()
        for fact in extract_cpp_lexical(p)["facts"]:
            if fact.get("kind") == "include":
                seen.add(fact["name"].split("/")[-1])
        for base in seen:
            fanin[base] = fanin.get(base, 0) + 1
    return fanin


def exec_arm(arm: str, root: pathlib.Path, texts: dict[str, str], query: str,
             fanin: dict[str, int] | None = None, cap: int = FANIN_CAP,
             ranker=None) -> tuple[set, str]:
    """Braço determinístico rotulado; qualidade só interpretável no REPORT.

    `fanin=None` desliga o teto (comportamento original); senão alvos com
    `fanin > cap` são pulados e contados em `hubs_skipped` na nota.
    `D_bm25` (braço extra, fora de `ARMS`) exige `ranker(query, k)` e entrega os
    `D_TOP_FILES` arquivos com melhor linha BM25.
    """
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
        skipped = 0
        for f in sorted(seeds):
            p = root / f
            if p.suffix not in {".c", ".h", ".hpp", ".cpp"} or not p.exists():
                continue
            for fact in extract_cpp_lexical(p)["facts"]:
                if fact["kind"] != "include":
                    continue
                base = fact["name"].split("/")[-1]
                if fanin is not None and fanin.get(base, 0) > cap:
                    skipped += 1
                    continue
                hop |= {g for g in texts if pathlib.Path(g).name == base}
        return (seeds | hop,
                f"adaptador real btc-cpp-lex/1 + seeds textuais; sem modelo; "
                f"hubs_skipped={skipped}; fanin_cap={cap if fanin is not None else 'off'}")
    if arm == "D_bm25":
        if ranker is None:
            raise ValueError("D_bm25 exige ranker BM25 (db_path em run_all)")
        best: dict[str, float] = {}
        for h in ranker(query, 200):
            if h["file"] not in best or h["bm25"] < best[h["file"]]:
                best[h["file"]] = h["bm25"]
        top = sorted(best, key=lambda f: (best[f], f))[:D_TOP_FILES]
        return set(top), f"bm25-text file rank top-{D_TOP_FILES}; sem modelo"
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


def run_all(root: pathlib.Path, tasks: list, budgets=(2000, 8000), seed: int = 7,
            cap: int = FANIN_CAP, extra_arms: tuple = (),
            db_path: pathlib.Path | None = None, split_ids: bool = False) -> tuple[list, list]:
    """Tarefas × (ARMS + extras) × budgets. Retorna (runs, manifests). Sem modelo.

    `split_ids=True` expande a query com partes de identificadores (`vocab`,
    mecânico, sem semântica); registrado por rodada.
    """
    root = pathlib.Path(root)
    texts = corpus_texts(root)
    verify_gold(tasks, texts)
    fanin = build_fanin(root)
    ranker = None
    con = None
    if "D_bm25" in extra_arms:
        if db_path is None:
            raise ValueError("D_bm25 exige db_path com índice btc-bm25text/1")
        con = sqlite3.connect(db_path)
        def ranker(query: str, k: int = 200):
            return bm25_lines(con, query, k)
    arms = ARMS + tuple(extra_arms)
    runs, mans = [], []
    order = 0
    for budget in budgets:
        pairs = [(t["id"], a) for t in tasks for a in arms]
        random.Random(f"{seed}-{budget}").shuffle(pairs)
        for task_id, arm in pairs:
            order += 1
            task = next(t for t in tasks if t["id"] == task_id)
            mans.append(build_manifest(task_id, arm, 1, order, budget, CORE_SHA, TOKENIZER))
            query, added = task["query"], []
            if split_ids:
                query, added = expand_query(task["query"])
            delivered, note = exec_arm(arm, root, texts, query, fanin, cap, ranker)
            m = re.search(r"hubs_skipped=(\d+)", note)
            hubs = int(m.group(1)) if m else 0
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
                         "fanin_cap": cap, "split_ids": split_ids,
                         "added_tokens": added,
                         "type": task.get("type"), "delivered": sorted(delivered),
                         "opened": sorted(delivered), "executor_note": note,
                         "hubs_skipped": hubs,
                         "used": used_tokens(root, delivered, budget),
                          "patch_accepted": None, "patch_note": "sem modelo",
                          "cost_total": None, "cost_note": "sem telemetria faturada",
                          "error": None} | rec)
    if con is not None:
        con.close()
    return runs, mans
