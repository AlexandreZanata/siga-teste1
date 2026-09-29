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


def rust_argv(binary: str, subtree: Path, index: Path, request: Path,
              cmd: str = "context") -> list[str]:
    """O subcomando é parâmetro, não constante.

    Já custou uma rodada: com `context` fixo, o modo `expand` media `context` com um pedido de
    expansão e publicava isso como custo de `expand` — o resultado pareceria plausível (exit 0,
    JSON válido, bytes exatos) e só a checagem independente de sobreposição de spans
desmascararia. Um harness em que o comando medido não é o comando pedido não mede nada.
    """
    return [
        binary, cmd,
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
    manifest["invocation"] = invocation()
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
        "invocation": invocation(),
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
        "invocation": invocation(),
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


def spans_of(response: dict) -> list[tuple[str, int, int]]:
    """Spans entregues: `(arquivo, linha, end_line)`. `end_line` ausente = linha única."""
    out = []
    for u in response.get("units") or []:
        if u.get("file") and u.get("line"):
            start = int(u["line"])
            out.append((u["file"], start, int(u.get("end_line") or start)))
    return out


def refs_of(response: dict) -> list[dict]:
    """`known_refs` realistas: com `end_line`, que é o que torna a dedup verificável."""
    return [{"file": f, "line": s, "end_line": e} for f, s, e in spans_of(response)]


def overlap(a: tuple[str, int, int], b: tuple[str, int, int]) -> bool:
    return a[0] == b[0] and a[1] <= b[2] and b[1] <= a[2]


def invocation() -> list[str]:
    """Linha de comando exata desta invocação.

    A rodada inteira roda por `run_round.py`, mas cada modo pode ser reexecutado sozinho — e
    então o `manifest_*.json` daquele modo tem de dizer **com quais flags**, senão a linha da
    tabela perde origem rastreável. Fica no artefato, não no relatório.
    """
    return ["python", "benchmarks/rust/measure.py", *sys.argv[1:]]


def context_probe(args, query: str, budget: int, req_dir: Path) -> tuple[dict | None, dict]:
    """Uma chamada de `context` como *setup*: produz as referências que `expand`/`verify`
    consomem. Não é medida — o custo de `context` já tem tabela própria."""
    req = req_dir / f"probe-{abs(hash((query, budget))) % 10**10}.json"
    req.write_text(json.dumps({
        "schema_version": 1, "intent": "localizar", "query": query,
        "budget_tokens": budget, "max_bytes": 4 * budget, "policy": args.policy,
    }))
    res = run_measured(rust_argv(args.rust_bin, Path(args.dataset).resolve() / SUBTREE,
                                 Path(args.rust_index).resolve(), req, cmd="context"),
                       cwd=str(REPO_ROOT))
    try:
        return json.loads(res["stdout"].decode()), res["metrics"]
    except Exception:
        return None, res["metrics"]


def measure_expand(args) -> int:
    """Custo e correção de `expand`, o segundo passo do ciclo de recuperação.

    O pedido de expansão é construído como o agente o construiria: `known_refs` e
    `delivered_refs` iguais às unidades que a chamada de `context` acabou de entregar, com
    `end_line`. Passar só `line` (sem `end_line`) faria a dedup parecer furada — o span
    entregue seria um ponto, e o produto devolveria, corretamente, a janela ao redor dele.

    Verificação independente do que o produto declara: nenhuma unidade devolvida pode
    sobrepor um span já entregue. Isso é checado no harness por interseção de intervalos,
    não lendo `omitted.reasons`.

    Comparabilidade: **não há braço Python**. A CLI de referência não tem `expand`; a
    comparação de produto que R2 faz no `context` não existe aqui.
    """
    subtree = Path(args.dataset).resolve() / SUBTREE
    rust_index = Path(args.rust_index).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    selected = queries_for(args)
    budgets = [int(b) for b in args.budgets.split(",")]
    req_dir = Path(tempfile.mkdtemp(prefix="atlas-exp-"))
    # `evidence_reserve_pct` (Q7 de R2): 0 é o comportamento histórico — não medir o antes e o
    # depois no mesmo ensaio seria comparar duas invocações em vez de duas políticas.
    reserve_pcts = [int(p) for p in str(getattr(args, "reserve_pcts", "") or "").split(",") if p]
    variantes: list[tuple[str, int]] = [("context", 0), ("references", 0)]
    variantes += [("references", p) for p in reserve_pcts]
    rows: list[dict] = []

    for budget in budgets:
        for q in selected:
            qid, text = q["id"], q["text"]
            for rep in range(args.reps):
                ctx, _ = context_probe(args, text, budget, req_dir)
                if ctx is None:
                    raise SystemExit(f"context de setup falhou em {qid}")
                delivered = refs_of(ctx)
                spans = spans_of(ctx)
                if not delivered:
                    continue  # nada entregue, nada a expandir — não é falha do produto
                for kind, reserve_pct in variantes:
                    req = req_dir / f"{qid}-{budget}-{rep}-{kind}-{reserve_pct}.json"
                    body = {
                        "schema_version": 1, "intent": "localizar", "query": text,
                        "known_refs": delivered, "delivered_refs": delivered,
                        "evidence_wanted": kind, "budget_tokens": budget,
                        "max_bytes": 4 * budget, "policy": args.policy,
                    }
                    if reserve_pct:
                        body["evidence_reserve_pct"] = reserve_pct
                    req.write_text(json.dumps(body))
                    res = run_measured(rust_argv(args.rust_bin, subtree, rust_index, req,
                                                 cmd="expand"),
                                       cwd=str(REPO_ROOT))
                    m = res["metrics"]
                    try:
                        resp = json.loads(res["stdout"].decode())
                    except Exception:
                        resp = {}
                    got = spans_of(resp)
                    motivos = list((resp.get("omitted") or {}).get("reasons") or [])
                    razoes = [str(u.get("reason") or "") for u in (resp.get("units") or [])]
                    rows.append({
                        "mode": "expand", "impl": "rust", "query_id": qid,
                        "query_text": text, "stratum": q.get("stratum") or q.get("kind"),
                        "budget_tokens": budget, "evidence_wanted": kind,
                        "reserve_pct": reserve_pct,
                        "repetition": rep, "wall_s": m["wall_s"], "user_s": m["user_s"],
                        "sys_s": m["sys_s"],
                        "cpu_s": (m["user_s"] or 0) + (m["sys_s"] or 0),
                        "max_rss_kb": m["max_rss_kb"], "exit_code": m["exit_status"],
                        "stdout_bytes": m["stdout_bytes"],
                        "declared": {
                            "parse_ok": bool(resp),
                            "state": resp.get("state"),
                            "units": len(resp.get("units") or []),
                            "declared_bytes": (resp.get("budget") or {}).get("used_bytes"),
                            "declared_tokens": (resp.get("budget") or {}).get("used_tokens"),
                            "omitted": (resp.get("omitted") or {}).get("n"),
                            "reasons": (resp.get("omitted") or {}).get("reasons"),
                        },
                        "checks": {
                            "no_overlap_with_delivered": not any(
                                overlap(g, d) for g in got for d in spans),
                            "bytes_exact": ((resp.get("budget") or {}).get("used_bytes")
                                            == m["stdout_bytes"] - 1),
                            "delivered_refs": len(delivered),
                            "delivered_spans": len(spans),
                            # Efeito da reserva, medido no harness: quantas unidades vieram da
                            # busca lexical, quantas são janela, e se o barrado foi declarado.
                            "lexical_units": sum(1 for r in razoes if r.startswith("lexical")),
                            "window_units": sum(1 for r in razoes if r.startswith("known_ref")),
                            "reserved_declared": "evidence_reserved" in motivos,
                            "reserve_accepted": (m["exit_status"] == 0),
                        },
                        "setup_context_bytes": (ctx.get("budget") or {}).get("used_bytes"),
                    })
            print(f"  budget={budget:5} {qid:4} {text[:24]:24} "
                  f"expand medido ({len(variantes)} variantes)", flush=True)

    write_jsonl(out / "runs_expand.jsonl", rows)
    write_json(out / "manifest_expand.json", {
        "schema": "atlas-run/1", "mode": "expand", "rows": len(rows),
        "invocation": invocation(),
        "repetitions": args.reps, "policy": args.policy, "budgets": budgets,
        "evidence_kinds": ["context", "references"],
        "reserve_pcts": reserve_pcts,
        "inputs": {"rust_bin": args.rust_bin, "rust_index": str(rust_index),
                   "python_bin": None,
                   "note": "sem braco Python: a CLI de referencia nao tem `expand`"},
        "measurement": {"external_process": True, "order": "context setup nao medido; "
                        "expand medido do spawn ate consumir stdout",
                        "checks": "no_overlap_with_delivered e bytes_exact sao checados no "
                                  "harness, nao lidos de omitted.reasons"},
        "environment": environment_manifest(),
    })
    print(f"\n{len(rows)} linhas -> {out / 'runs_expand.jsonl'}")
    return 0


VERIFY_SCENARIOS = ["ok", "sem_hash", "hash_divergente", "linha_fora", "caminho_fora"]
WRONG_HASH = "sha256:" + "0" * 64


def verify_refs(spans: list[tuple[str, int, int]], hashes: dict[str, str]) -> list[dict]:
    """Cinco refs por arquivo citado, um por cenário. O esperado é declarado **antes** de
    medir: o harness sabe qual código de saída cada cenário deve produzir."""
    if not spans:
        return []
    f, start, end = spans[0]
    h = hashes.get(f) or ("sha256:" + "0" * 64)
    return [
        {"scenario": "ok", "spec": f"{f}:{start}@{h}", "expect_exit": 0},
        {"scenario": "sem_hash", "spec": f"{f}:{start}", "expect_exit": 0},
        {"scenario": "hash_divergente", "spec": f"{f}:{start}@{WRONG_HASH}", "expect_exit": 5},
        {"scenario": "linha_fora", "spec": f"{f}:{end + 100000}", "expect_exit": 5},
        {"scenario": "caminho_fora", "spec": f"../{SUBTREE.split('/')[0]}/pom.xml:1",
         "expect_exit": 5},
    ]


def measure_verify(args) -> int:
    """Custo do portão de verificação: ler o disco, conferir hash e linha, decidir.

    As referências vêm de uma chamada real de `context` (setup não medido), com o hash
    correto lido da própria resposta. Os cenários de reprovação **não precisam modificar o
    dataset**: hash errado e linha inexistente são entradas, não mutações — `caminho_fora`
    é a única que depende de o caminho resolver fora da raiz.

    O código esperado de cada cenário é fixado antes da medição (`expect_exit`), de modo que
    "a integridade violada sai 5" vira uma checagem do harness, não uma citação do produto.

    Comparabilidade: **não há braço Python**. `verify` existe na referência, mas é um
    autoteste fixo de um arquivo (`archatlas/cli.py:22-29`), sem `--ref` e sem conferência
    de hash — não é o mesmo comando.
    """
    subtree = Path(args.dataset).resolve() / SUBTREE
    rust_index = Path(args.rust_index).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    selected = queries_for(args)
    budgets = [int(b) for b in args.budgets.split(",")]
    req_dir = Path(tempfile.mkdtemp(prefix="atlas-vfy-"))
    rows: list[dict] = []

    for budget in budgets:
        for q in selected:
            qid, text = q["id"], q["text"]
            for rep in range(args.reps):
                ctx, _ = context_probe(args, text, budget, req_dir)
                if ctx is None:
                    raise SystemExit(f"context de setup falhou em {qid}")
                spans = spans_of(ctx)
                hashes = {u["file"]: u["hash"] for u in (ctx.get("units") or [])
                          if u.get("file") and u.get("hash")}
                for case in verify_refs(spans, hashes):
                    argv = [args.rust_bin, "verify", "--repo", str(subtree),
                            "--index", str(rust_index), "--ref", case["spec"]]
                    res = run_measured(argv, cwd=str(REPO_ROOT))
                    m = res["metrics"]
                    try:
                        resp = json.loads(res["stdout"].decode())
                    except Exception:
                        resp = {}
                    exit_code = None if m["exit_status"] is None else int(m["exit_status"])
                    rows.append({
                        "mode": "verify", "impl": "rust", "query_id": qid,
                        "scenario": case["scenario"], "ref": case["spec"],
                        "budget_tokens": budget, "repetition": rep,
                        "wall_s": m["wall_s"], "user_s": m["user_s"], "sys_s": m["sys_s"],
                        "cpu_s": (m["user_s"] or 0) + (m["sys_s"] or 0),
                        "max_rss_kb": m["max_rss_kb"], "exit_code": exit_code,
                        "expect_exit": case["expect_exit"],
                        "exit_as_expected": exit_code == case["expect_exit"],
                        "stdout_bytes": m["stdout_bytes"],
                        "declared": {
                            "parse_ok": bool(resp),
                            "state": resp.get("state"),
                            "checks": resp.get("checks"),
                            "units": len(resp.get("units") or []),
                            "reasons": (resp.get("omitted") or {}).get("reasons"),
                            "declared_bytes": (resp.get("budget") or {}).get("used_bytes"),
                            "bytes_exact": ((resp.get("budget") or {}).get("used_bytes")
                                            == m["stdout_bytes"] - 1),
                        },
                    })
            print(f"  budget={budget:5} {qid:4} verify medido", flush=True)

    write_jsonl(out / "runs_verify.jsonl", rows)
    write_json(out / "manifest_verify.json", {
        "schema": "atlas-run/1", "mode": "verify", "rows": len(rows),
        "invocation": invocation(),
        "repetitions": args.reps, "scenarios": VERIFY_SCENARIOS,
        "inputs": {"rust_bin": args.rust_bin, "rust_index": str(rust_index),
                   "note": "sem braco Python: verify da referencia e autoteste fixo, sem --ref"},
        "measurement": {"external_process": True,
                        "expected_exit": "fixado antes: 0 para ok/sem_hash, 5 para os demais",
                        "dataset": "intocado; reprovacao vem de entrada (hash/linha), nao de mutacao"},
        "environment": environment_manifest(),
    })
    print(f"\n{len(rows)} linhas -> {out / 'runs_verify.jsonl'}")
    return 0


def measure_scale(args) -> int:
    """Escala: como `index` e `context` custam quando o corpus cresce.

    O plano §5 fixa dois tetos para a coorte (5 mil arquivos **e** 256 MiB de texto) e §6 pede
    medir "corpus maior". Os dois tetos **não** caem no mesmo ponto: o corpus base é 504
    arquivos / 2,4 MiB, ou seja 4,8 kB por arquivo, e o plano sugere~52 kB de média. A série
    multiplica o mesmo corpus (×1, ×10, ×30, ×100), cruzando o teto de **contagem** em ×10
    (5 040 arquivos ≈ 24 MiB) e o de **volume** em ×100 (240 MiB ≈ 50 400 arquivos). Medir os
    dois separadamente é o que diz qual deles manda no custo.

    O corpus sintético é uma **cópia**: cada arquivo aparece N vezes, então `doc_freq` e o
    ranking não são os de um projeto real. O que se interpreta aqui é **custo** — tempo, RSS e
    bytes de índice por arquivo e por MiB —, não qualidade de resultado. Cada ponto declara
    arquivos e bytes, como o plano exige.

    O dataset continua intocado: tudo é construído em cópias sob um diretório temporário, e a
    árvore de cada tamanho é removida antes do próximo. O índice em disco é registrado antes.
    """
    import shutil

    subtree = Path(args.dataset).resolve() / SUBTREE
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    corpus = json.loads(Path(args.corpus).read_text()) if args.corpus else None
    if corpus is None:
        raise SystemExit("modo scale exige --corpus (lista de caminhos do corpus congelado)")
    paths = sorted(corpus["corpus"]["paths"])
    base_bytes = sum((subtree / rel).stat().st_size for rel in paths)
    mults = [int(m) for m in args.scale_sizes.split(",")]
    qdoc = json.loads(Path(args.queries).read_text())
    selected = qdoc["queries"]  # só as estratificadas: as de borda medem outra coisa
    req_dir = Path(tempfile.mkdtemp(prefix="atlas-scl-req-"))
    work = Path(tempfile.mkdtemp(prefix="atlas-scl-"))
    py_env = dict(os.environ, PYTHONPATH=str(REPO_ROOT))
    rows: list[dict] = []

    print(f"corpus base: {len(paths)} arquivos / {base_bytes / 1048576:.1f} MiB")
    for i, mult in enumerate(mults):
        # Menos repetições nos tamanhos maiores: o ponto caro é o de escala, e repetir 3x um
        # índice de 252 MiB gastaria minutos para reduzir ruído que a curva já mostra.
        index_reps = max(1, args.index_reps - i)
        root = work / f"x{mult}"
        tree = root / SUBTREE
        tree.mkdir(parents=True, exist_ok=True)
        for r in range(mult):
            for rel in paths:
                dst = tree / f"rep{r}" / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(subtree / rel, dst)
        n_files = mult * len(paths)
        c_bytes = mult * base_bytes
        print(f"\n[{mult}x] {n_files} arquivos / {c_bytes / 1048576:.1f} MiB", flush=True)

        for rep in range(index_reps):
            order = ("python", "rust") if rep % 2 == 0 else ("rust", "python")
            for impl in order:
                idx = root / f"index-{impl}-{rep}.sqlite"
                idx.unlink(missing_ok=True)
                argv = ([args.rust_bin, "index", "--repo", str(tree), "--index", str(idx),
                         "--include", "java"]
                        if impl == "rust"
                        else [args.python_bin, "-m", "archatlas.cli", "index",
                              "--db", str(idx), "--dataset", str(root)])
                res = run_measured(argv, env=py_env, cwd=str(REPO_ROOT))
                m = res["metrics"]
                rows.append(_scale_row(
                    impl=impl, phase="index", mult=mult, files=n_files,
                    corpus_bytes=c_bytes, repetition=rep, order_position=order.index(impl),
                    query_id=None, budget_tokens=None, metrics=m,
                    declared=parse_index_side(res["stdout"], impl), args=args,
                    index_bytes=idx.stat().st_size if idx.exists() else None,
                    index_wal_bytes=(Path(str(idx) + "-wal").stat().st_size
                                     if Path(str(idx) + "-wal").exists() else 0),
                ))
                print(f"  {impl:7} index  rep={rep} wall={m['wall_s']} "
                      f"rss={m['max_rss_kb']}kB idx={rows[-1]['index_bytes']}B", flush=True)

        # Latência de consulta no tamanho atual: uma consulta de menor frequência e uma de
        # maior, das estratificadas — a curva de custo depende de quantos candidatos a consulta
        # alcança. A árvore inteira (com os índices dentro) sai ao fim deste tamanho.
        probe_queries = [selected[0], selected[-1]]
        rust_index = root / "index-rust-0.sqlite"
        py_index = root / f"index-python-{index_reps - 1}.sqlite"
        for q in probe_queries:
            for rep in range(args.reps):
                order = ("python", "rust") if rep % 2 == 0 else ("rust", "python")
                for impl in order:
                    req = req_dir / f"scl-{mult}-{q['id']}.json"
                    req.write_text(json.dumps({
                        "schema_version": 1, "intent": "localizar", "query": q["text"],
                        "budget_tokens": 2000, "max_bytes": 8000, "policy": args.policy,
                    }))
                    argv = ([args.rust_bin, "context", "--repo", str(tree),
                             "--index", str(rust_index), "--request", str(req)]
                            if impl == "rust"
                            else [args.python_bin, "-m", "archatlas.cli", "context",
                                  "--db", str(py_index), "--query", q["text"], "--budget", "2000"])
                    res = run_measured(argv, env=py_env, cwd=str(REPO_ROOT))
                    m = res["metrics"]
                    rows.append(_scale_row(
                        impl=impl, phase="context", mult=mult, files=n_files,
                        corpus_bytes=c_bytes, repetition=rep,
                        order_position=order.index(impl), query_id=q["id"],
                        budget_tokens=2000, metrics=m,
                        declared=parse_side(res["stdout"], impl), args=args,
                        index_bytes=None, index_wal_bytes=None,
                    ))
            print(f"  consulta {q['id']:4} {q['text'][:20]:20} medida", flush=True)

        shutil.rmtree(root, ignore_errors=True)  # árvore fora; os números ficam

    write_jsonl(out / "runs_scale.jsonl", rows)
    write_json(out / "manifest_scale.json", {
        "schema": "atlas-run/1", "mode": "scale", "rows": len(rows),
        "invocation": invocation(),
        "sizes": [{"multiplier": m, "files": m * len(paths), "corpus_bytes": m * base_bytes}
                  for m in mults],
        "base_corpus": {"files": len(paths), "bytes": base_bytes, "subtree": SUBTREE,
                        "fingerprint": corpus["corpus"]["content_fingerprint_sha256"]},
        "repetitions": {"context": args.reps,
                        "index": f"max(1, {args.index_reps} - indice_do_tamanho) -> "
                                 + ", ".join(str(max(1, args.index_reps - i))
                                             for i in range(len(mults)))},
        "measurement": {
            "external_process": True,
            "synthetic": "cada arquivo do corpus base e copiado N vezes; doc_freq e ranking nao "
                         "correspondem a um projeto real — interpretar CUSTO, nao qualidade",
            "dataset": "intocado; arvores em diretorio temporario, removidas por tamanho",
            "cache": "aquecido (processo novo)",
        },
        "environment": environment_manifest(),
    })
    print(f"\n{len(rows)} linhas -> {out / 'runs_scale.jsonl'}")
    return 0


def _scale_row(*, impl, phase, mult, files, corpus_bytes, repetition, order_position,
               query_id, budget_tokens, metrics, declared, args,
               index_bytes, index_wal_bytes) -> dict:
    m = metrics
    return {
        "mode": "scale", "impl": impl, "phase": phase, "multiplier": mult,
        "files": files, "corpus_bytes": corpus_bytes, "repetition": repetition,
        "order_position": order_position, "query_id": query_id,
        "budget_tokens": budget_tokens, "policy": args.policy,
        "wall_s": m["wall_s"], "user_s": m["user_s"], "sys_s": m["sys_s"],
        "cpu_s": (m["user_s"] or 0) + (m["sys_s"] or 0),
        "max_rss_kb": m["max_rss_kb"], "minor_faults": m["minor_faults"],
        "major_faults": m["major_faults"], "fs_in_blocks": m["fs_in_blocks"],
        "fs_out_blocks": m["fs_out_blocks"], "exit_code": m["exit_status"],
        "stdout_bytes": m["stdout_bytes"], "declared": declared,
        "index_bytes": index_bytes, "index_wal_bytes": index_wal_bytes,
    }


def queries_for(args) -> list[dict]:
    doc = json.loads(Path(args.queries).read_text())
    sel = doc["queries"] + (doc["edge"] if args.include_edge else [])
    return sel[: args.limit] if args.limit else sel


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
        "invocation": invocation(),
        "environment": environment_manifest(),
    })
    print(f"{len(rows)} linhas -> {out / 'runs_doctor.jsonl'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", choices=["query", "index", "update", "expand", "verify",
                                       "doctor", "scale"], default="query")
    ap.add_argument("--out", required=True)
    ap.add_argument("--dataset", default=os.environ.get("ARCHATLAS_DATASET") or str(REPO_ROOT.parent / "siga"))
    ap.add_argument("--queries", default=None)
    ap.add_argument("--corpus", default=None,
                    help="corpus.json (obrigatório em --mode update e --mode scale)")
    ap.add_argument("--scale-sizes", default="1,10,30,100",
                    help="multiplicadores do corpus base em --mode scale")
    ap.add_argument("--index-reps", type=int, default=3,
                    help="repetições de indexação no maior tamanho (decresce 1 por tamanho)")
    ap.add_argument("--rust-bin", default=str(REPO_ROOT / "rust/archatlas/target/release/archatlas"))
    ap.add_argument("--python-bin", default=sys.executable)
    ap.add_argument("--rust-index", default=None)
    ap.add_argument("--python-index", default=None)
    ap.add_argument("--budgets", default="2000")
    ap.add_argument("--policy", default="CTX-RS")
    ap.add_argument("--reps", type=int, default=10)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--reserve-pcts", default="",
                    help="percentuais de evidence_reserve_pct a medir em --mode expand "
                         "(ex. 30,50); vazio mede so o comportamento historico")
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
    if args.mode in ("expand", "verify"):
        if not args.queries:
            raise SystemExit(f"--queries e obrigatorio em --mode {args.mode}")
        if not args.rust_index:
            raise SystemExit(f"--rust-index e obrigatorio em --mode {args.mode}")
        return measure_expand(args) if args.mode == "expand" else measure_verify(args)
    if args.mode == "scale":
        if not args.queries:
            raise SystemExit("--queries e obrigatorio em --mode scale")
        return measure_scale(args)
    return measure_doctor(args)


if __name__ == "__main__":
    raise SystemExit(main())
