# SPDX-License-Identifier: Apache-2.0
"""P2/E26-00: telemetria e scoring do avaliador (sem LLM, stdlib-only).

Separação executor/avaliador:
- Executor (`capsule.py`, `harness.py`) acessa índice + disco.
- Avaliador (este módulo) recebe SOMENTE (delivered, gt) — nunca `con`,
  nunca disco, nunca índice. Assinatura sem `con` é o isolamento.

Corrige AUDIT A1/A2 sem mudar ranking:
- `hit` = algum arquivo esperado entregue (compat legado).
- `recall_set`/`precision_set` = métricas completas; um membro nunca dá 100%.
- `payload_tokens_for_capsule` mede a serialização inteira entregue,
  não só a soma de itens (`chars//4` segue estimativa de diagnóstico).
"""
from __future__ import annotations
import json


def count_tokens_chars4(text: str) -> int:
    return max(1, len(text) // 4)


def score_delivery(delivered: set[str] | list[str], gt: dict) -> dict:
    """Escore puro e determinístico. Nunca levanta em GT estranho."""
    det = sorted(set(delivered))
    det_set = set(det)
    if "files" in gt:
        exp = sorted(set(gt["files"]))
        inter = sorted(det_set & set(exp))
        n_exp, n_det, n_hit = len(exp), len(det), len(inter)
        return {"hit": n_hit > 0, "recall_set": (n_hit / n_exp if n_exp else 0.0),
                "precision_set": (n_hit / n_det if n_det else 0.0),
                "expected_count": n_exp, "delivered_count": n_det, "matched": inter,
                "kind": "files", "error": None if n_exp else "gt-vazio"}
    if "path_files" in gt:
        path = sorted(set(gt["path_files"]))
        inter = sorted(det_set & set(path))
        n_path, n_det, n_hit = len(path), len(det), len(inter)
        edge_ok = True
        if "edges" in gt:
            edge_files = {e["file"] for e in gt["edges"]}
            edge_ok = bool(edge_files & det_set)
        hit = edge_ok and n_hit > 0
        return {"hit": hit, "recall_set": (n_hit / n_path if n_path else 0.0),
                "precision_set": (n_hit / n_det if n_det else 0.0),
                "expected_count": n_path, "delivered_count": n_det, "matched": inter,
                "kind": "path", "error": None if n_path else "gt-vazio"}
    if "edges" in gt:
        exp = sorted({e["file"] for e in gt["edges"]})
        inter = sorted(det_set & set(exp))
        n_exp, n_det, n_hit = len(exp), len(det), len(inter)
        return {"hit": n_hit > 0, "recall_set": (n_hit / n_exp if n_exp else 0.0),
                "precision_set": (n_hit / n_det if n_det else 0.0),
                "expected_count": n_exp, "delivered_count": n_det, "matched": inter,
                "kind": "edges", "error": None if n_exp else "gt-vazio"}
    if "package" in gt:
        pkg = gt.get("package", "")
        one = gt.get("file")
        hit = bool(one and one in det_set) or any(f.startswith(pkg) for f in det_set)
        # Denominador do pacote é desconhecido: nunca alegar recall/precision completos.
        return {"hit": hit, "recall_set": None, "precision_set": None,
                "expected_count": None, "delivered_count": len(det), "matched": [],
                "kind": "package", "error": None}
    if "file" in gt and gt.get("file"):
        exp = [gt["file"]]
        hit = gt["file"] in det_set
        n_det = len(det)
        return {"hit": hit, "recall_set": 1.0 if hit else 0.0,
                "precision_set": ((1.0 / n_det) if hit and n_det else 0.0),
                "expected_count": 1, "delivered_count": n_det,
                "matched": exp if hit else [], "kind": "file", "error": None}
    return {"hit": False, "recall_set": 0.0, "precision_set": 0.0,
            "expected_count": 0, "delivered_count": len(det), "matched": [],
            "kind": "unknown", "error": "gt-vazio"}


def payload_tokens_for_capsule(cap: dict) -> int:
    """Tokens da serialização inteira entregue (determinística)."""
    payload = {"excerpts": cap.get("excerpts", []), "citations": cap.get("citations", []),
               "symbols": [{"file": s.get("file"), "line": s.get("line"),
                            "kind": s.get("kind"), "name": s.get("name")}
                           for s in cap.get("symbols", [])]}
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return count_tokens_chars4(blob)


def score_additional(delivered: set[str] | list[str],
                     expected_additional: set[str] | list[str],
                     given: set[str] | list[str] | None = None) -> dict:
    """E26-01: escore sobre arquivos ADICIONAIS (dado o já fornecido). Puro.

    `novel = delivered − given`; esperado vazio (negativos) nunca gera recall
    convencional: retorna `recall_set=None` + `abstained` (novel vazio?).
    """
    det, exp, giv = set(delivered), set(expected_additional), set(given or [])
    novel = det - giv
    inter = sorted(novel & exp)
    if not exp:
        return {"hit": False, "recall_set": None, "precision_set": None,
                "all_necessary": False, "abstained": len(novel) == 0,
                "novel_count": len(novel), "expected_count": 0,
                "matched": inter, "kind": "negative", "error": None}
    n_exp, n_nov, n_hit = len(exp), len(novel), len(inter)
    return {"hit": n_hit > 0, "recall_set": n_hit / n_exp,
            "precision_set": (n_hit / n_nov if n_nov else 0.0),
            "all_necessary": n_hit == n_exp, "abstained": False,
            "novel_count": n_nov, "expected_count": n_exp,
            "matched": inter, "kind": "additional", "error": None}


def build_manifest(task_id: str, condition: str, repetition: int, order: int,
                   budget: int, sha: str, tokenizer: str = "chars//4",
                   extra: dict | None = None) -> dict:
    """Manifesto determinístico de pareamento (sem relógio)."""
    m = {"task_id": task_id, "condition": condition, "repetition": repetition,
         "order": order, "budget": budget, "sha": sha, "tokenizer": tokenizer}
    if extra:
        m.update(extra)
    return m


def rescore_runs(runs: list[dict]) -> list[dict]:
    """Replay puro: re-escora (delivered, gt) sem índice/disco."""
    return [score_delivery(r["delivered"], r["gt"]) for r in runs]


def verify_replay(runs: list[dict], stored: list[dict]) -> bool:
    """True sse o replay reproduz exatamente os escores armazenados."""
    fresh = rescore_runs(runs)
    return json.dumps(fresh, sort_keys=True) == json.dumps(stored, sort_keys=True)
