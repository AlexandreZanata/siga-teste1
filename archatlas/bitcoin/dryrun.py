# SPDX-License-Identifier: Apache-2.0
"""Dryrun offline do piloto BTC-P3 (sem modelo, sem dataset, sem gasto).

Valida a plumbing do piloto: pareamento, orçamento, isolamento do avaliador e
registro de erros. Executores-braço são stubs determinísticos rotulados `stub`
(qualidade NÃO interpretável); o braço C exercita o adaptador real `btc-cpp-lex/1`.
Reuso publicado (só leitura): `build_manifest`, `score_delivery`,
`payload_tokens_for_capsule`, `cpp_lex`.
"""
from __future__ import annotations
import json
import pathlib
import random
import tempfile

from archatlas.bitcoin.cpp_lex import CORE_SHA, discover_cpp, extract_cpp_lexical
from archatlas.telemetry import build_manifest, payload_tokens_for_capsule, score_delivery

ARMS = ("A_busca", "B_freq", "C_adapter")
BUDGET = 2000
TOKENIZER = "chars//4"
SEED = 7
FAIL_INJECT = ("BTC-P3D-007", "B_freq", 2)  # falha sintética determinística

FIXTURES = {
    "src/rpc/server.cpp": b'#include "server.h"\n#include "validation.h"\n// GetState VerifyBlock SendMessage rpc\n',
    "src/rpc/server.h": b"#pragma once\n// rpc network interface contract\nvoid GetState();\n",
    "src/validation.cpp": b'#include "validation.h"\n#include "mempool.h"\n// CheckTransaction validation VerifyBlock AcceptTx\n',
    "src/validation.h": b"#pragma once\n// validation spent CheckTransaction\n",
    "src/mempool.cpp": b'#include "mempool.h"\n// mempool AcceptTx limit size\n',
    "src/mempool.h": b"#pragma once\n// mempool limit size\n",
    "src/wallet/wallet.cpp": b'#include "wallet.h"\n#include "validation.h"\n// Wallet balance spent validation\n',
    "src/wallet/wallet.h": b"#pragma once\n// Wallet balance\n",
    "src/net.cpp": b'#include "net.h"\n// net message loop SendMessage\n',
    "src/net.h": b"#pragma once\n// net message loop interface\n",
    "test/validation_tests.py": b"# validation test failure CheckTransaction\n",
    "test/wallet_tests.py": b"# wallet test balance Wallet\n",
}


def build_fixture_repo(base: pathlib.Path) -> pathlib.Path:
    root = base / "btc-fixture"
    for rel, blob in FIXTURES.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(blob)
    return root


def _texts(root: pathlib.Path) -> dict:
    return {str(p.relative_to(root)): p.read_bytes().decode("utf-8", errors="replace").lower()
            for p in discover_cpp(root)} | {
        "test/validation_tests.py": (root / "test/validation_tests.py").read_bytes().decode().lower(),
        "test/wallet_tests.py": (root / "test/wallet_tests.py").read_bytes().decode().lower()}


def exec_arm(arm: str, root: pathlib.Path, query: str) -> tuple[set, list, str]:
    toks = [t.lower() for t in query.split()]
    texts = _texts(root)
    if arm == "A_busca":
        hit = {f for f, t in texts.items() if any(tok in t for tok in toks)}
        return hit, sorted(hit), "stub: busca textual sem modelo"
    if arm == "B_freq":
        ranked = sorted(texts, key=lambda f: (-sum(texts[f].count(t) for t in toks), f))
        hit = set(ranked[:4])
        return hit, sorted(hit), "stub: ranking de frequencia sem modelo"
    if arm == "C_adapter":
        names = {pathlib.Path(f).stem.lower() for f in texts}
        seeds = {f for f in texts if any(tok in pathlib.Path(f).stem.lower() or tok in f.lower().split("/")
                                         for tok in toks) and pathlib.Path(f).stem.lower() in names}
        seeds |= {f for f in texts if any(tok in pathlib.Path(f).stem.lower() for tok in toks)}
        hop = set()
        for f in list(seeds):
            p = root / f
            if p.suffix in {".c", ".h", ".hpp", ".cpp"}:
                for fact in extract_cpp_lexical(p)["facts"]:
                    if fact["kind"] != "include":
                        continue
                    base = fact["name"].split("/")[-1]
                    hop |= {g for g in texts if pathlib.Path(g).name == base}
        hit = seeds | hop
        return hit, sorted(hit), "adaptador real btc-cpp-lex/1 + seeds textuais; sem modelo"
    raise ValueError(f"braço desconhecido: {arm}")


def _used(root: pathlib.Path, delivered: set) -> int:
    total, used = 0, 0
    for f in sorted(delivered):
        total += max(1, len((root / f).read_bytes()) // 4)
        if total <= BUDGET:
            used = total
    return used


def run_dryrun(out_dir: pathlib.Path, tasks: list, seed: int = SEED) -> dict:
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="btc-pilot-dryrun-") as tmp:
        root = build_fixture_repo(pathlib.Path(tmp))
        mans, runs = [], []
        order = 0
        for rep in (1, 2):
            pairs = [(t["id"], a) for t in tasks for a in ARMS]
            random.Random(f"{seed}-{rep}").shuffle(pairs)
            for task_id, arm in pairs:
                order += 1
                task = next(t for t in tasks if t["id"] == task_id)
                mans.append(build_manifest(task_id, arm, rep, order, BUDGET, CORE_SHA, TOKENIZER))
                rec = {"task_id": task_id, "condition": arm, "repetition": rep,
                       "order": order, "budget": BUDGET, "tokenizer": TOKENIZER,
                       "sha": CORE_SHA, "patch_accepted": None,
                       "patch_note": "sem modelo: qualidade não medida",
                       "cost_total": None,
                       "cost_note": "sem telemetria faturada: dryrun offline",
                       "error": None}
                try:
                    if (task_id, arm, rep) == FAIL_INJECT:
                        raise RuntimeError("falha sintética injetada: B_freq quebrou")
                    delivered, opened, note = exec_arm(arm, root, task["query"])
                    cap = {"excerpts": [], "citations": sorted(delivered),
                           "symbols": [{"file": f, "line": 1, "kind": "n/a",
                                        "name": pathlib.Path(f).name} for f in sorted(delivered)]}
                    sc = score_delivery(delivered, {"files": task["expected_dev_files"]})
                    rec.update({"delivered": sorted(delivered), "opened": opened,
                                "executor_note": note, "used": _used(root, delivered),
                                "payload_tokens": payload_tokens_for_capsule(cap),
                                "hit": sc["hit"], "recall_set": sc["recall_set"],
                                "precision_set": sc["precision_set"]})
                except Exception as e:  # registra erro, nunca aborta o lote
                    rec.update({"delivered": [], "opened": [], "executor_note": "erro registrado",
                                "used": 0, "payload_tokens": None, "hit": False,
                                "recall_set": 0.0, "precision_set": 0.0,
                                "error": f"{type(e).__name__}: {e}"})
                runs.append(rec)
    (out_dir / "manifest.jsonl").write_text(
        "\n".join(json.dumps(m, sort_keys=True) for m in mans) + "\n", encoding="utf-8")
    (out_dir / "runs.jsonl").write_text(
        "\n".join(json.dumps(r, sort_keys=True) for r in runs) + "\n", encoding="utf-8")
    ok = [r for r in runs if not r["error"]]
    return {"n_runs": len(runs), "n_errors": len(runs) - len(ok),
            "recall_mean": sum(r["recall_set"] for r in ok) / len(ok),
            "hit_rate": sum(1 for r in ok if r["hit"]) / len(ok)}
