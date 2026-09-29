#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Gera as tabelas do relatório a partir dos artefatos brutos da rodada.

Separação deliberada: este script só **agrega**. Nenhum número aparece escrito à mão no
relatório, e nenhum número é calculado em outro lugar. Se um valor está no relatório, ele
veio daqui, de um `runs_*.jsonl` auditável.

Uso:
    python benchmarks/rust/report.py --run experiments/rust/siga/<run_id>
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _bench import quantiles, read_jsonl, summarize  # noqa: E402


def fmt(v, digits=3, suffix=""):
    if v is None:
        return "nao medido"
    if isinstance(v, float):
        return f"{v:.{digits}f}{suffix}"
    return f"{v}{suffix}"


def ratio(a, b):
    if a is None or b in (None, 0):
        return None
    return a / b


def load(run: Path, name: str) -> list[dict]:
    p = run / name
    if not p.exists():
        return []
    return read_jsonl(p)


def table_impl(rows: list[dict], group_key: str, value_key: str, title: str) -> str:
    """Tabela por implementação: n, min, p50, p95, max, média."""
    lines = [f"### {title}", "",
             "| grupo | impl | n | min | p50 | p95 | max | média |",
             "|---|---|---|---|---|---|---|---|"]
    groups = sorted({r[group_key] for r in rows})
    for g in groups:
        for impl in ("python", "rust"):
            sub = [r for r in rows if r[group_key] == g and r["impl"] == impl]
            if not sub:
                continue
            s = summarize(sub, value_key)
            lines.append(
                f"| {g} | {impl} | {s['n']} | {fmt(s['min'])} | {fmt(s['p50'])} | "
                f"{fmt(s['p95'])} | {fmt(s['max'])} | {fmt(s['mean'])} |"
            )
    lines.append("")
    return "\n".join(lines)


def median_by_query_impl(rows: list[dict], value_key: str) -> dict[tuple[str, str], float | None]:
    """Mediana de um campo por (consulta, implementação). Evita o erro de pegar "a linha
    daquela consulta" sem filtrar por implementação — que devolve o valor de um lado só e
    deixa a outra coluna vazia (ou, pior, preenchida com o número do outro braço)."""
    by: dict[tuple[str, str], list[float]] = defaultdict(list)
    for r in rows:
        v = r.get(value_key)
        if v is not None:
            by[(r["query_id"], r["impl"])].append(v)
    return {k: (statistics.median(v) if v else None) for k, v in by.items()}


def paired_by_query(rows: list[dict], value_key: str) -> list[tuple[str, float, float, float]]:
    """Mediana por consulta e por implementação, depois razão. É o pareamento de verdade:
    a comparação é feita dentro da mesma consulta, não entre médias gerais."""
    by_q: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r.get(value_key) is None:
            continue
        by_q[r["query_id"]][r["impl"]].append(r[value_key])
    out = []
    for qid in sorted(by_q):
        py = statistics.median(by_q[qid]["python"]) if by_q[qid]["python"] else None
        rs = statistics.median(by_q[qid]["rust"]) if by_q[qid]["rust"] else None
        out.append((qid, py, rs, ratio(rs, py)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    run = Path(args.run).resolve()

    # Descobre os artefatos em vez de adivinhar nomes: a rodada pode ter qualquer
    # combinação de política, orçamentos e repetições.
    qrows: list[dict] = []
    loaded = []
    for path in sorted(run.glob("runs_query_*.jsonl")):
        loaded.append(path.name)
        qrows.extend(read_jsonl(path))
    irows = load(run, "runs_index.jsonl")
    urows = load(run, "runs_update.jsonl")
    drows = load(run, "runs_doctor.jsonl")
    if loaded:
        print(f"artefatos de consulta: {', '.join(loaded)}")

    parts: list[str] = ["# R2 — tabelas geradas", ""]
    parts.append(f"Rodada: `{run.name}`. Gerado por `benchmarks/rust/report.py`; nenhum "
                 "número deste arquivo foi escrito à mão.")
    parts.append("")

    if qrows:
        policies = sorted({r["policy"] for r in qrows})
        parts.append("## Integridade da medição")
        parts.append("")
        total = len(qrows)
        ok = sum(1 for r in qrows if r["exit_code"] == 0)
        parts.append(f"- Execuções: **{total}**, com código 0: **{ok}** "
                     f"({100 * ok / total:.1f}%), não-zero: **{total - ok}**.")
        # A regra que o defeito de R0 violava: número declarado == bytes emitidos.
        rust_rows = [r for r in qrows if r["impl"] == "rust"
                     and r["declared"].get("declared_bytes") is not None]
        viol = [r for r in rust_rows
                if r["declared"]["declared_bytes"] != r["stdout_bytes"] - 1]
        parts.append(f"- Rust: `used_bytes` igual ao stdout real em "
                     f"**{len(rust_rows) - len(viol)}/{len(rust_rows)}** execuções"
                     + ("" if not viol else f" — {len(viol)} violações"))
        parts.append(f"- Consultas distintas: {len({r['query_id'] for r in qrows})}")
        parts.append(f"- Políticas: {', '.join(policies)}")
        combos = sorted({(r["policy"], r["budget_tokens"]) for r in qrows})
        parts.append("- Combinações (política, orçamento) medidas:")
        for pol, budget in combos:
            sub = [r for r in qrows if r["policy"] == pol and r["budget_tokens"] == budget]
            reps = len(sub) // max(1, len({(r["query_id"], r["impl"]) for r in sub}))
            parts.append(f"  - `{pol}` orçamento {budget}: {reps} repetições por consulta/braço")
        parts.append("")
        parts.append("")

        for policy in policies:
            sub = [r for r in qrows if r["policy"] == policy]
            parts.append(f"## Política `{policy}`")
            parts.append("")
            parts.append(table_impl(sub, "budget_tokens", "wall_s",
                                    "Tempo de parede (s), por orçamento"))
            parts.append(table_impl(sub, "budget_tokens", "cpu_s",
                                    "CPU user+sistema (s), por orçamento"))
            parts.append(table_impl(sub, "budget_tokens", "max_rss_kb",
                                    "Pico de RSS (kB), por orçamento"))

            parts.append("### Razão Rust/Python por consulta (medianas pareadas)")
            parts.append("")
            parts.append("| consulta | estrato | py wall p50 | rs wall p50 | razão rs/py | py bytes | rs bytes |")
            parts.append("|---|---|---|---|---|---|---|")
            for budget in sorted({r["budget_tokens"] for r in sub}):
                bsub = [r for r in sub if r["budget_tokens"] == budget]
                pairs = paired_by_query(bsub, "wall_s")
                bytes_by = median_by_query_impl(bsub, "stdout_bytes")
                for qid, py, rs, rt in pairs:
                    row = next(r for r in bsub if r["query_id"] == qid)
                    parts.append(
                        f"| {qid} `{row['query_text'][:22]}` | {row['stratum']} | "
                        f"{fmt(py)} | {fmt(rs)} | {fmt(rt, 2)} | "
                        f"{fmt(bytes_by.get((qid, 'python')), 0)} | "
                        f"{fmt(bytes_by.get((qid, 'rust')), 0)} |"
                    )
                ratios = [r for _, _, _, r in pairs if r is not None]
                if ratios:
                    parts.append(
                        f"| **resumo budget={budget}** | — | — | — | "
                        f"p50 {fmt(quantiles(ratios, 0.5), 2)} · máx {fmt(max(ratios), 2)} | | |"
                    )
            parts.append("")

            parts.append("### Divergência semântica: declarado vs entregue")
            parts.append("")
            parts.append("| orçamento | impl | estado (contagem) | bytes entregues (p50) | "
                         "tokens declarados (p50) | bytes declarados (p50) | refs (p50) | "
                         "trechos (p50) | arquivos (p50) | `tokenizer_is_exact` |")
            parts.append("|---|---|---|---|---|---|---|---|---|---|")
            for budget in sorted({r["budget_tokens"] for r in sub}):
                for impl in ("python", "rust"):
                    bsub = [r for r in sub if r["budget_tokens"] == budget and r["impl"] == impl]
                    if not bsub:
                        continue
                    states = Counter(r["declared"].get("state") for r in bsub)
                    states_txt = ", ".join(f"{k}={v}" for k, v in sorted(
                        states.items(), key=lambda kv: str(kv[0])))
                    parts.append(
                        f"| {budget} | {impl} | {states_txt} | "
                        f"{fmt(quantiles([r['stdout_bytes'] for r in bsub], 0.5), 0)} | "
                        f"{fmt(quantiles([r['declared'].get('declared_tokens') for r in bsub], 0.5), 0)} | "
                        f"{fmt(quantiles([r['declared'].get('declared_bytes') for r in bsub], 0.5), 0)} | "
                        f"{fmt(quantiles([r['declared'].get('units') for r in bsub], 0.5), 0)} | "
                        f"{fmt(quantiles([r['declared'].get('texts') for r in bsub], 0.5), 0)} | "
                        f"{fmt(quantiles([r['declared'].get('files') for r in bsub], 0.5), 0)} | "
                        f"{bsub[0]['declared'].get('tokenizer_is_exact')} |"
                    )
            parts.append("")

        # O defeito que originou o contrato §6, medido em vez de citado: quanto cada lado
        # *declara* ter usado contra quanto efetivamente entregou. A unidade de comparação
        # é `chars//4`, a mesma que a referência Python publica como tokenizer, para que a
        # razão não dependa de duas convenções diferentes.
        parts.append("## Fidelidade do orçamento declarado (todas as políticas)")
        parts.append("")
        parts.append("| impl | n | bytes entregues (p50) | tokens estimados `chars//4` (p50) | "
                     "tokens declarados (p50) | razão declarado/entregue (p50 · máx) | "
                     "declara bytes entregues? | execuções acima de `max_bytes` | "
                     "declarado acima de `budget_tokens` |")
        parts.append("|---|---|---|---|---|---|---|---|---|")
        for impl in ("python", "rust"):
            isub = [r for r in qrows if r["impl"] == impl]
            if not isub:
                continue
            est = [r["stdout_bytes"] // 4 for r in isub]
            decl = [r["declared"].get("declared_tokens") for r in isub]
            ratios = [d / e for d, e in zip(decl, est) if d is not None and e > 0]
            declares_bytes = all(r["declared"].get("declared_bytes") is not None for r in isub)
            over_bytes = sum(1 for r in isub if r["stdout_bytes"] > r["max_bytes"])
            over_decl = sum(1 for r, d in zip(isub, decl)
                            if d is not None and d > r["budget_tokens"])
            parts.append(
                f"| {impl} | {len(isub)} | "
                f"{fmt(quantiles([r['stdout_bytes'] for r in isub], 0.5), 0)} | "
                f"{fmt(quantiles(est, 0.5), 0)} | {fmt(quantiles(decl, 0.5), 0)} | "
                f"{fmt(quantiles(ratios, 0.5), 2)} · {fmt(max(ratios) if ratios else None, 2)} | "
                f"{'sim' if declares_bytes else 'não'} | {over_bytes}/{len(isub)} | "
                f"{over_decl}/{len(isub)} |"
            )
        parts.append("")
        parts.append("`ratio` é a mediana das razões **por execução** (declarado ÷ bytes entregues "
                     "÷ 4), não a razão de duas medianas: agregar antes de dividir esconderia "
                     "justamente as execuções em que a declaração diverge.")
        parts.append("")

    if irows:
        parts.append("## Construção do índice (dispersão, diretórios exclusivos)")
        parts.append("")
        parts.append(table_impl(irows, "mode", "wall_s", "Tempo de parede (s)"))
        parts.append(table_impl(irows, "mode", "max_rss_kb", "Pico de RSS (kB)"))
        parts.append("| impl | walls (todas as repetições) | índice (B) p50 | WAL (B) p50 |")
        parts.append("|---|---|---|---|")
        for impl in ("python", "rust"):
            sub = [r for r in irows if r["impl"] == impl]
            if not sub:
                continue
            walls = ", ".join(fmt(r["wall_s"]) for r in sub)
            parts.append(
                f"| {impl} | {walls} | "
                f"{fmt(quantiles([r.get('index_bytes') for r in sub], 0.5), 0)} | "
                f"{fmt(quantiles([r.get('index_wal_bytes') for r in sub], 0.5), 0)} |"
            )
        parts.append("")

    if urows:
        parts.append("## Ciclo editar/testar: reindexar depois de uma mutação")
        parts.append("")
        parts.append("A primeira indexação de cada cópia é *setup*, não medida: o número é o da "
                     "passada seguinte à mutação, que é o que o agente paga a cada edição.")
        parts.append("")
        order = ["unchanged", "edit_1", "edit_10", "edit_100", "delete_1", "rename_1"]
        present = [s for s in order if any(r["scenario"] == s for r in urows)]
        present += sorted({r["scenario"] for r in urows} - set(present))
        parts.append("### Tempo de parede (s), por cenário")
        parts.append("")
        parts.append("| cenário | impl | n | min | p50 | p95 | max | média |")
        parts.append("|---|---|---|---|---|---|---|---|")
        for sc in present:
            for impl in ("python", "rust"):
                sub = [r for r in urows if r["scenario"] == sc and r["impl"] == impl]
                if not sub:
                    continue
                s = summarize(sub, "wall_s")
                parts.append(f"| {sc} | {impl} | {s['n']} | {fmt(s['min'])} | {fmt(s['p50'])} | "
                             f"{fmt(s['p95'])} | {fmt(s['max'])} | {fmt(s['mean'])} |")
        parts.append("")
        parts.append(table_impl(urows, "scenario", "max_rss_kb", "Pico de RSS (kB), por cenário"))
        parts.append("### O que cada lado declara ter reindexado, e a checagem independente")
        parts.append("")
        parts.append("| cenário | impl | arquivos mutados | reindexados (p50) | pulados (p50) | "
                     "removidos (p50) | equivale a rebuild |")
        parts.append("|---|---|---|---|---|---|---|")
        for sc in present:
            for impl in ("python", "rust"):
                sub = [r for r in urows if r["scenario"] == sc and r["impl"] == impl]
                if not sub:
                    continue
                ok = sum(1 for r in sub if r.get("equivalent_to_rebuild"))
                parts.append(
                    f"| {sc} | {impl} | {sub[0]['mutated_files']} | "
                    f"{fmt(quantiles([(r['declared'] or {}).get('indexed') for r in sub], 0.5), 0)} | "
                    f"{fmt(quantiles([(r['declared'] or {}).get('skipped') for r in sub], 0.5), 0)} | "
                    f"{fmt(quantiles([(r['declared'] or {}).get('pruned_files') for r in sub], 0.5), 0)} | "
                    f"{'sim' if ok == len(sub) else 'não'} ({ok}/{len(sub)}) |"
                )
        parts.append("")
        parts.append("`equivale a rebuild` é checagem independente do que o comando declara: para o "
                     "Rust, uma reindexação do zero (com `--force`) na mesma árvore mutada tem de "
                     "produzir a **mesma geração**; para a referência Python, que não publica "
                     "geração, o conjunto de arquivos dentro do índice tem de ser exatamente o do "
                     "disco.")
        parts.append("")

    if drows:
        parts.append("## `doctor` (processo novo, cache aquecido)")
        parts.append("")
        parts.append(table_impl(drows, "mode", "wall_s", "Tempo de parede (s)"))
        parts.append(table_impl(drows, "mode", "max_rss_kb", "Pico de RSS (kB)"))
        parts.append("| impl | walls |")
        parts.append("|---|---|")
        for impl in ("python", "rust"):
            sub = [r for r in drows if r["impl"] == impl]
            if sub:
                parts.append(f"| {impl} | {', '.join(fmt(r['wall_s']) for r in sub)} |")
        parts.append("")

    parts.append("## Convenções")
    parts.append("")
    parts.append("- Quantis por **posto mais próximo** em amostra ordenada; p50 = mediana "
                 "(média dos dois centrais quando n é par).")
    parts.append("- Tempo medido do **spawn até consumir todo o stdout**, com GNU time. "
                 "Nenhuma medição é de função interna.")
    parts.append("- Cache de filesystem **aquecido**. Frio não foi medido: exigiria "
                 "`drop_caches` com root numa máquina dedicada.")
    parts.append("- Ordem **alternada por repetição**: cada braço ocupa cada posição "
                 "metade das vezes.")
    parts.append("")

    out = Path(args.out) if args.out else run / "tables.md"
    out.write_text("\n".join(parts) + "\n")
    print(f"tabelas geradas em {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
