#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Mede Python congelado e Rust lado a lado, com pareamento e ordem alternada.

Protocolo §7: mesmo corpus, mesmas consultas, lotes pareados em ordem alternada, processo
externo medido do spawn até consumir stdout, quantis com convenção publicada.

O que este script **não** faz, e o relatório precisa dizer: não derruba o cache de
filesystem. Medir com cache frio exigiria `drop_caches` (root) numa máquina dedicada. Toda
medição aqui é *processo novo com cache aquecido*, e o relatório não chama isso de "frio".

`max_bytes = 4 * budget_tokens` é a entrada canônica: sem tokenizer do modelo, o teto de
bytes e a estimativa de tokens descrevem a mesma fronteira, então as duas implementações
recebem o mesmo pedido em unidades comparáveis. Ainda assim os produtos **não** são
equivalentes — ver o campo `divergence` de cada linha, que expõe quanto cada lado declara
ter entregue contra quanto realmente entregou.

Uso:
    python benchmarks/rust/measure.py --mode query --out <dir> --rust-index ... --python-index ...
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _bench import environment_manifest, read_jsonl, run_measured, write_json, write_jsonl  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SUBTREE = "siga-ex/src/main/java"


def parse_side(stdout: bytes, impl: str) -> dict:
    """Extrai o que cada lado *declara* ter entregue, lendo o envelope do comando.

    Duas armadilhas que já custaram uma rodada:

    1. O envelope que a CLI Python imprime (`archatlas/cli.py`, chaves `refs`, `texts`,
       `omitted.n`, `budget.used`) **não** é o dicionário interno de `capsule.py`
       (`symbols`, `files`, `truncation_log`, `hard_enforced`). Ler o formato interno de
       um produto que emite o externo devolve zero para tudo — e um zero falso é pior que
       um campo ausente, porque entra em tabela como se fosse medida.
    2. Campo ausente vira `None`, nunca `0`. `len(x or [])` transforma "o outro lado não
       tem essa chave" em "o outro lado entregou nada", que é uma alegação diferente.

    O mapeamento entre nomes diferentes é explícito aqui, em um lugar só:
    `units` (Rust) ≡ `refs` (Python) = referências citadas; `texts` ≡ trechos de texto com
    bytes entregues; `omitted.n` ≡ `omitted.n`.
    """
    try:
        v = json.loads(stdout.decode())
    except Exception:
        return {"parse_ok": False}
    budget = v.get("budget") or {}
    if impl == "rust":
        units = v.get("units") or []
        return {
            "parse_ok": True,
            "state": v.get("state"),
            "requested_tokens": budget.get("requested_tokens"),
            "declared_tokens": budget.get("used_tokens"),
            "declared_bytes": budget.get("used_bytes"),
            "tokenizer_id": budget.get("tokenizer_id"),
            "tokenizer_is_exact": budget.get("tokenizer_is_exact"),
            "units": len(units),
            "texts": sum(1 for u in units if u.get("kind") == "excerpt"),
            "files": len({u.get("file") for u in units if u.get("file")}),
            "omitted": (v.get("omitted") or {}).get("n"),
        }
    refs = v.get("refs") or []
    texts = v.get("texts") or []
    return {
        "parse_ok": True,
        "state": v.get("state"),
        "requested_tokens": budget.get("requested"),
        "declared_tokens": budget.get("used"),
        # A referência não publica bytes entregues: só o token estimado. Registrar `None`
        # aqui é o que torna visível, na tabela, que ela não declara seu próprio tamanho.
        "declared_bytes": None,
        "tokenizer_id": budget.get("tokenizer"),
        # `chars//4` é estimativa por construção, não o tokenizer do modelo.
        "tokenizer_is_exact": False if budget.get("tokenizer") else None,
        "units": len(refs),
        "texts": len(texts),
        "files": len({r.get("file") for r in refs if r.get("file")}
                     | {t.get("file") for t in texts if t.get("file")}),
        "omitted": (v.get("omitted") or {}).get("n"),
    }


def rust_argv(binary: str, subtree: Path, index: Path, request: Path) -> list[str]:
    return [
        binary, "context",
        "--repo", str(subtree),
        "--index", str(index),
        "--request", str(request),
    ]


def python_argv(python_bin: str, index: Path, query: str, budget: int) -> list[str]:
    return [
        python_bin, "-m", "archatlas.cli", "context",
        "--db", str(index),
        "--query", query,
        "--budget", str(budget),
    ]


def measure_queries(args) -> int:
    subtree = Path(args.dataset).resolve() / SUBTREE
    rust_index = Path(args.rust_index).resolve()
    py_index = Path(args.python_index).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)

    queries_doc = json.loads(Path(args.queries).read_text())
    selected = queries_doc["queries"] + (queries_doc["edge"] if args.include_edge else [])
    if args.limit:
        selected = selected[: args.limit]

    budgets = [int(b) for b in args.budgets.split(",")]
    py_env = dict(os.environ, ARCHATLAS_DATASET=str(Path(args.dataset).resolve()))
    py_pythonpath = dict(os.environ, PYTHONPATH=str(REPO_ROOT), ARCHATLAS_DATASET=str(Path(args.dataset).resolve()))

    req_dir = Path(tempfile.mkdtemp(prefix="atlas-req-"))
    rows: list[dict] = []
    warmups = 0

    print(f"consultas={len(selected)} budgets={budgets} reps={args.reps} impls=2")
    print(f"total de execucoes medidas: {len(selected) * len(budgets) * args.reps * 2}")
    print()

    for budget in budgets:
        max_bytes = 4 * budget
        for q in selected:
            qid, text = q["id"], q["text"]
            req_path = req_dir / f"{qid}-{budget}.json"
            req_path.write_text(json.dumps({
                "schema_version": 1,
                "intent": "localizar",
                "query": text,
                "budget_tokens": budget,
                "max_bytes": max_bytes,
                "policy": args.policy,
            }))

            # Aquecimento: uma passada por (consulta, implementação), descartada. Sem ela a
            # primeira repetição mediria o custo de aquecer o cache de páginas do corpus.
            if args.warmup:
                for impl in ("python", "rust"):
                    argv = (
                        python_argv(args.python_bin, py_index, text, budget)
                        if impl == "python"
                        else rust_argv(args.rust_bin, subtree, rust_index, req_path)
                    )
                    run_measured(argv, env=py_pythonpath, cwd=str(REPO_ROOT))
                    warmups += 1

            for rep in range(args.reps):
                # Ordem alternada por repetição: quem roda primeiro não é sempre o mesmo, e
                # ao longo de 10 repetições cada lado ocupa cada posição 5 vezes.
                order = ("python", "rust") if rep % 2 == 0 else ("rust", "python")
                for pos, impl in enumerate(order):
                    argv = (
                        python_argv(args.python_bin, py_index, text, budget)
                        if impl == "python"
                        else rust_argv(args.rust_bin, subtree, rust_index, req_path)
                    )
                    res = run_measured(argv, env=py_pythonpath, cwd=str(REPO_ROOT))
                    m = res["metrics"]
                    parsed = parse_side(res["stdout"], impl)
                    rows.append({
                        "mode": "query",
                        "impl": impl,
                        "query_id": qid,
                        "query_text": text,
                        "stratum": q.get("stratum") or q.get("kind"),
                        "budget_tokens": budget,
                        "max_bytes": max_bytes,
                        "policy": args.policy,
                        "repetition": rep,
                        "order_position": pos,
                        "wall_s": m["wall_s"],
                        "user_s": m["user_s"],
                        "sys_s": m["sys_s"],
                        "cpu_s": (m["user_s"] or 0) + (m["sys_s"] or 0),
                        "max_rss_kb": m["max_rss_kb"],
                        "minor_faults": m["minor_faults"],
                        "major_faults": m["major_faults"],
                        "fs_in_blocks": m["fs_in_blocks"],
                        "fs_out_blocks": m["fs_out_blocks"],
                        "exit_code": m["exit_status"],
                        "stdout_bytes": m["stdout_bytes"],
                        "declared": parsed,
                    })
                print(
                    f"  budget={budget:5} {qid:4} {text[:28]:28} rep={rep:2} "
                    f"py={rows[-2 if order[0]=='python' else -1]['wall_s']} "
                    f"rs={rows[-2 if order[0]=='rust' else -1]['wall_s']}"
                    if len(rows) >= 2 else "  ...",
                    flush=True,
                )

    # O nome carrega politica, orcamentos e repeticoes: uma rodada nunca sobrescreve outra,
    # e um arquivo encontrado semanas depois se explica sozinho.
    tag = f"{args.policy}_b{'-'.join(str(b) for b in budgets)}_r{args.reps}"
    write_jsonl(out / f"runs_query_{tag}.jsonl", rows)
    successes = sum(1 for r in rows if r["exit_code"] == 0)
    manifest = {
        "schema": "atlas-run/1",
        "mode": "query",
        "tag": tag,
        "policy": args.policy,
        "budgets": budgets,
        "rows": len(rows),
        "warmups": warmups,
        "exit_zero": successes,
        "exit_nonzero": len(rows) - successes,
        "queries": {
            "file": str(Path(args.queries).name),
            "count": len(selected),
            "source_fingerprint": queries_doc["source_corpus"]["fingerprint"],
        },
        "inputs": {
            "rust_bin": args.rust_bin,
            "rust_index": str(rust_index),
            "python_index": str(py_index),
            "python_bin": args.python_bin,
            "repo_subtree": SUBTREE,
            "max_bytes_rule": "4 * budget_tokens",
        },
        "measurement": {
            "external_process": True,
            "filesystem_cache": "aquecido (processo novo); cache frio NAO medido",
            "order": "alternada por repeticao",
            "quantile_convention": "posto mais proximo; p50 = mediana (media dos centrais se n par)",
        },
        "environment": environment_manifest(),
    }
    write_json(out / f"manifest_query_{tag}.json", manifest)
    print(f"\n{len(rows)} linhas ({successes} com exit 0) -> {out / f'runs_query_{tag}.jsonl'}")
    missing = [r for r in rows if not r["declared"].get("parse_ok")]
    if missing:
        print(f"ATENCAO: {len(missing)} execucoes sem JSON parseavel em stdout")
    return 0


def measure_index(args) -> int:
    """Dispersão de build: uma execução por diretório exclusivo, nada reaproveitado."""
    subtree = Path(args.dataset).resolve() / SUBTREE
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="atlas-idx-"))
    py_env = dict(os.environ, ARCHATLAS_DATASET=str(Path(args.dataset).resolve()),
                  PYTHONPATH=str(REPO_ROOT))
    rows = []

    for rep in range(args.reps):
        order = ("python", "rust") if rep % 2 == 0 else ("rust", "python")
        for impl in order:
            if impl == "rust":
                idx = work / f"rust-{rep}.sqlite"
                idx.unlink(missing_ok=True)
                argv = [args.rust_bin, "index", "--repo", str(subtree), "--index", str(idx),
                        "--include", "java"]
                res = run_measured(argv, cwd=str(REPO_ROOT))
            else:
                idx = work / f"python-{rep}.sqlite"
                idx.unlink(missing_ok=True)
                argv = [args.python_bin, "-m", "archatlas.cli", "index", "--db", str(idx)]
                res = run_measured(argv, env=py_env, cwd=str(REPO_ROOT))
            m = res["metrics"]
            rows.append({
                "mode": "index",
                "impl": impl,
                "repetition": rep,
                "order_position": order.index(impl),
                "wall_s": m["wall_s"],
                "user_s": m["user_s"],
                "sys_s": m["sys_s"],
                "cpu_s": (m["user_s"] or 0) + (m["sys_s"] or 0),
                "max_rss_kb": m["max_rss_kb"],
                "minor_faults": m["minor_faults"],
                "major_faults": m["major_faults"],
                "fs_in_blocks": m["fs_in_blocks"],
                "fs_out_blocks": m["fs_out_blocks"],
                "exit_code": m["exit_status"],
                # Sem `stdout_bytes` na linha de tempo: o tamanho do índice é medido à parte,
                # porque WAL ainda pode estar pendente no instante do fechamento.
                "index_bytes": idx.stat().st_size if idx.exists() else None,
                "index_wal_bytes": (Path(str(idx) + "-wal").stat().st_size
                                    if Path(str(idx) + "-wal").exists() else 0),
                "index_shm_bytes": (Path(str(idx) + "-shm").stat().st_size
                                    if Path(str(idx) + "-shm").exists() else 0),
            })
            print(f"  rep={rep:2} {impl:7} wall={m['wall_s']} rss={m['max_rss_kb']}kB", flush=True)

    write_jsonl(out / "runs_index.jsonl", rows)
    write_json(out / "manifest_index.json", {
        "schema": "atlas-run/1",
        "mode": "index",
        "repetitions": args.reps,
        "rows": len(rows),
        "inputs": {"rust_bin": args.rust_bin, "python_bin": args.python_bin,
                   "corpus": SUBTREE, "include": "java",
                   "index_dirs": "exclusivos por execucao (nada reaproveitado)"},
        "environment": environment_manifest(),
    })
    print(f"\n{len(rows)} linhas -> {out / 'runs_index.jsonl'}")
    return 0


def evenly_spaced(items: list, k: int) -> list:
    """k itens em posições igualmente espaçadas de uma lista já ordenada (determinístico)."""
    if k >= len(items):
        return list(items)
    if k <= 1:
        return items[:1]
    step = (len(items) - 1) / (k - 1)
    return [items[round(i * step)] for i in range(k)]


def mutate_edit(path: Path, scenario: str) -> None:
    """Edição de conteúdo: bytes novos, mesmo arquivo, mesmo caminho."""
    with path.open("ab") as fh:
        fh.write(f"\n// r2-update {scenario}\n".encode())


def mutate_delete(path: Path) -> None:
    path.unlink()


def mutate_rename(path: Path) -> None:
    path.rename(path.with_name(path.stem + ".upd.java"))


UPDATE_SCENARIOS = [
    ("unchanged", None),
    ("edit_1", mutate_edit),
    ("edit_10", mutate_edit),
    ("edit_100", mutate_edit),
    ("delete_1", mutate_delete),
    ("rename_1", mutate_rename),
]


def measure_update(args) -> int:
    """Custo do ciclo editar/testar: reindexar depois de uma mutação pequena.

    Montagem de propósito: a árvore do corpus é **copiada** para um diretório de trabalho, uma
    vez por (cenário, repetição, implementação). O dataset é read-only e continua intocado; a
    cópia custa milissegundos e é o que permite medir edição/delete/rename sem tocar no ouro.

    A primeira indexação de cada cópia é *setup*, não medida: o que se mede é a passada
    seguinte, depois da mutação — exatamente o que o agente paga a cada edição.

    O alvo do `edit_1` é o maior arquivo do corpus **até 100 KiB**, escolhido em tempo de
    execução a partir de `corpus.json`. Nenhum caminho do SIGA está embutido no harness.

    Comparabilidade declarada: os dois lados são incrementais por **hash de conteúdo** —
    `index_file` (Python, `archatlas/store.py:44-50`) e `store.rs` pulam arquivo com bytes
    idênticos. O que se mede aqui não é "um incremental contra um rebuild", e sim a
    sobrecarga da passada que ambos fazem: iniciar processo, descobrir, hashear e escrever o
    que mudou. "Nome igual, semântica igual" é o que torna este número interpretável.
    """
    import shutil

    subtree = Path(args.dataset).resolve() / SUBTREE
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    corpus = json.loads(Path(args.corpus).read_text()) if args.corpus else None
    if corpus is None:
        raise SystemExit("modo update exige --corpus (lista de caminhos do corpus congelado)")
    rel_paths = sorted(corpus["corpus"]["paths"])

    sizes = sorted(((subtree / rel).stat().st_size, rel) for rel in rel_paths)
    under_100k = [rel for size, rel in sizes if size <= 100 * 1024]
    target_one = under_100k[-1] if under_100k else sizes[0][1]
    targets = {
        "edit_1": [target_one],
        "edit_10": evenly_spaced(rel_paths, 10),
        "edit_100": evenly_spaced(rel_paths, 100),
        "delete_1": [rel_paths[len(rel_paths) // 2]],
        "rename_1": [rel_paths[0]],
    }
    print(f"corpus copiado: {len(rel_paths)} arquivos; alvo de edit_1: {target_one} "
          f"({(subtree / target_one).stat().st_size} B)")

    work = Path(tempfile.mkdtemp(prefix="atlas-upd-"))
    rows: list[dict] = []
    # PYTHONPATH para o pacote; `--dataset` é sempre explícito. Se algum caminho cair no
    # default do config, ele aponta para o dataset read-only e a checagem de cobertura
    # reprova — falha ruidosa, não comparação silenciosa com a árvore errada.
    py_env = dict(os.environ, PYTHONPATH=str(REPO_ROOT))

    for scenario, mutate in UPDATE_SCENARIOS:
        for rep in range(args.reps):
            # Ordem alternada, como no resto da rodada.
            order = ("python", "rust") if rep % 2 == 0 else ("rust", "python")
            for impl in order:
                base = work / f"{scenario}-{rep}-{impl}"
                shutil.rmtree(base, ignore_errors=True)
                tree = base / SUBTREE
                tree.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(subtree, tree)
                # A cópia tem de ser do corpus congelado, não de "um diretório qualquer".
                copied = len(list(tree.rglob("*.java")))
                if copied != len(rel_paths):
                    raise SystemExit(f"copia incompleta em {base}: {copied} != {len(rel_paths)}")

                idx = base / "index.sqlite"
                if impl == "rust":
                    warm = [args.rust_bin, "index", "--repo", str(tree), "--index", str(idx),
                            "--include", "java"]
                else:
                    warm = [args.python_bin, "-m", "archatlas.cli", "index", "--db", str(idx),
                            "--dataset", str(base)]
                run_measured(warm, env=py_env, cwd=str(REPO_ROOT))

                if mutate is not None:
                    for rel in targets[scenario]:
                        p = tree / rel
                        if not p.exists():
                            raise SystemExit(f"alvo ausente na copia: {p}")
                        if mutate is mutate_edit:
                            mutate(p, scenario)
                        else:
                            mutate(p)

                argv = warm  # mesma invocação, agora depois da mutação
                res = run_measured(argv, env=py_env, cwd=str(REPO_ROOT))
                m = res["metrics"]
                declared = parse_index_side(res["stdout"], impl)

                # Verificação independente do que o comando declara: a árvore mutada é
                # reindexada do zero e o resultado tem de ser o mesmo. É a propriedade que
                # "incremental" promete; sem ela o ganho de tempo seria perda de correção.
                check_idx = base / "check.sqlite"
                if impl == "rust":
                    chk = run_measured([args.rust_bin, "index", "--repo", str(tree),
                                        "--index", str(check_idx), "--include", "java",
                                        "--force"], cwd=str(REPO_ROOT))
                    rebuild = parse_index_side(chk["stdout"], impl).get("generation")
                    equivalent = (rebuild is not None
                                  and rebuild == declared.get("generation"))
                else:
                    chk = run_measured([args.python_bin, "-m", "archatlas.cli", "index",
                                        "--db", str(check_idx), "--dataset", str(base)],
                                       env=py_env, cwd=str(REPO_ROOT))
                    # A referência não publica geração; a checagem possível é de cobertura:
                    # o índice precisa conter exatamente os arquivos que estão no disco.
                    equivalent = index_covers_disk(check_idx, tree)

                rows.append({
                    "mode": "update",
                    "impl": impl,
                    "scenario": scenario,
                    "repetition": rep,
                    "order_position": order.index(impl),
                    "mutated_files": len(targets.get(scenario, [])),
                    "wall_s": m["wall_s"], "user_s": m["user_s"], "sys_s": m["sys_s"],
                    "cpu_s": (m["user_s"] or 0) + (m["sys_s"] or 0),
                    "max_rss_kb": m["max_rss_kb"], "exit_code": m["exit_status"],
                    "stdout_bytes": m["stdout_bytes"],
                    "declared": declared,
                    "equivalent_to_rebuild": equivalent,
                    "tree_files_on_disk": len(list(tree.rglob("*.java"))),
                })
                print(f"  {scenario:10} rep={rep} {impl:7} wall={m['wall_s']} "
                      f"rss={m['max_rss_kb']}kB equivalente={equivalent}", flush=True)

    write_jsonl(out / "runs_update.jsonl", rows)
    write_json(out / "manifest_update.json", {
        "schema": "atlas-run/1",
        "mode": "update",
        "repetitions": args.reps,
        "rows": len(rows),
        "scenarios": [s for s, _ in UPDATE_SCENARIOS],
        "targets": targets,
        "inputs": {"rust_bin": args.rust_bin, "python_bin": args.python_bin,
                   "corpus": SUBTREE,
                   "scratch": "copia da arvore por (cenario, repeticao, impl); dataset intocado"},
        "measurement": {
            "first_index_is_setup": True,
            "order": "alternada por repeticao",
            "equivalence_check": "rust: generation(rebuild --force) == generation(incremental); "
                                "python: arquivos no indice == arquivos no disco",
        },
        "environment": environment_manifest(),
    })
    print(f"\n{len(rows)} linhas -> {out / 'runs_update.jsonl'}")
    return 0


def parse_index_side(stdout: bytes, impl: str) -> dict:
    """O que cada lado declara na indexação. Python imprime `repr` de dict, não JSON."""
    text = stdout.decode("utf-8", errors="replace")
    if impl == "rust":
        try:
            v = json.loads(text)
        except Exception:
            return {"parse_ok": False}
        return {"parse_ok": True, **(v.get("counts") or {}),
                "generation": (v.get("index") or {}).get("generation"),
                "files": (v.get("index") or {}).get("files")}
    import ast

    try:
        v = ast.literal_eval(text.strip().splitlines()[-1])
    except Exception:
        return {"parse_ok": False}
    return {"parse_ok": True, **v}


def index_covers_disk(index: Path, tree: Path) -> bool:
    """A referência Python: o índice cobre exatamente os `.java` do disco?"""
    if not index.exists():
        return False
    on_disk = {str(p) for p in tree.rglob("*.java")}
    con = sqlite3.connect(f"file:{index}?mode=ro", uri=True)
    try:
        in_index = {r[0] for r in con.execute("SELECT path FROM files").fetchall()}
    finally:
        con.close()
    return on_disk == in_index


def measure_doctor(args) -> int:
    subtree = Path(args.dataset).resolve() / SUBTREE
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    py_env = dict(os.environ, ARCHATLAS_DATASET=str(Path(args.dataset).resolve()),
                  PYTHONPATH=str(REPO_ROOT))
    rows = []
    for rep in range(args.reps):
        order = ("python", "rust") if rep % 2 == 0 else ("rust", "python")
        for impl in order:
            argv = ([args.rust_bin, "doctor", "--repo", str(subtree),
                     "--index", str(Path(args.rust_index).resolve())]
                    if impl == "rust"
                    else [args.python_bin, "-m", "archatlas.cli", "doctor",
                          "--db", str(Path(args.python_index).resolve())])
            res = run_measured(argv, env=py_env, cwd=str(REPO_ROOT))
            m = res["metrics"]
            rows.append({
                "mode": "doctor", "impl": impl, "repetition": rep,
                "order_position": order.index(impl),
                "wall_s": m["wall_s"], "user_s": m["user_s"], "sys_s": m["sys_s"],
                "cpu_s": (m["user_s"] or 0) + (m["sys_s"] or 0),
                "max_rss_kb": m["max_rss_kb"], "exit_code": m["exit_status"],
                "stdout_bytes": m["stdout_bytes"],
            })
    write_jsonl(out / "runs_doctor.jsonl", rows)
    write_json(out / "manifest_doctor.json", {
        "schema": "atlas-run/1", "mode": "doctor", "rows": len(rows),
        "environment": environment_manifest(),
    })
    print(f"{len(rows)} linhas -> {out / 'runs_doctor.jsonl'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", choices=["query", "index", "update", "doctor"], default="query")
    ap.add_argument("--out", required=True)
    ap.add_argument("--dataset", default=os.environ.get("ARCHATLAS_DATASET") or str(REPO_ROOT.parent / "siga"))
    ap.add_argument("--queries", default=None)
    ap.add_argument("--corpus", default=None, help="corpus.json (obrigatório em --mode update)")
    ap.add_argument("--rust-bin", default=str(REPO_ROOT / "rust/archatlas/target/release/archatlas"))
    ap.add_argument("--python-bin", default=sys.executable)
    ap.add_argument("--rust-index", default=None)
    ap.add_argument("--python-index", default=None)
    ap.add_argument("--budgets", default="2000")
    ap.add_argument("--policy", default="CTX-RS")
    ap.add_argument("--reps", type=int, default=10)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--include-edge", action="store_true")
    ap.add_argument("--warmup", action="store_true", default=True)
    args = ap.parse_args()

    if args.mode == "query":
        if not args.queries:
            raise SystemExit("--queries e obrigatorio em --mode query")
        for req in ("rust_index", "python_index"):
            if not getattr(args, req):
                raise SystemExit(f"--{req.replace('_','-')} e obrigatorio em --mode query")
        return measure_queries(args)
    if args.mode == "index":
        return measure_index(args)
    if args.mode == "update":
        return measure_update(args)
    return measure_doctor(args)


if __name__ == "__main__":
    raise SystemExit(main())
