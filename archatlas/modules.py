# SPDX-License-Identifier: Apache-2.0
"""P4/E26-03: mapa de módulos → seleção local, com/sem expansão por relações.

Desenho em duas partes (ficha E26-03), sem somar alterações num braço:
- Parte 1: busca plana (BM25, fora deste módulo) vs mapa → seleção local SEM arestas.
- Parte 2: MESMA política de sementes, expansão por relações DESLIGADA/LIGADA.

Núcleo lexical continua baseline (este módulo nunca faz BM25). Sem LLM:
descrições funcionais e PageRank ficam diferidos (contrato futuro: cache separado
com modelo+prompt+hash; nada manual entra nas sementes). Relações incertas seguem
candidatas (`text-match-verified`, nunca fato estrutural).
"""
from __future__ import annotations
import sqlite3

from archatlas.query import find_definition, find_references, find_symbol


def package_of(path: str) -> str:
    """Pacote Java por caminho (`src/main/java/a/b/C.java` → `a.b`); senão diretório."""
    p = path.replace("\\", "/")
    key = "src/main/java/"
    if key in p:
        pkg = p.split(key, 1)[1].rsplit("/", 1)[0]
        return pkg.replace("/", ".")
    return p.rsplit("/", 1)[0] if "/" in p else ""


def module_map(con: sqlite3.Connection) -> dict[str, list[str]]:
    """Mapa pacote → arquivos, só da tabela `files`. Determinístico."""
    out: dict[str, list[str]] = {}
    for (f,) in con.execute("SELECT path FROM files ORDER BY path").fetchall():
        out.setdefault(package_of(f), []).append(f)
    return out


def seed_entities(con: sqlite3.Connection, query: str, per_tok: int = 3) -> list[dict]:
    """Sementes compartilhadas pelos dois tratamentos (mesma política)."""
    seeds, seen = [], set()
    for tok in query.split():
        t = tok.strip("?,.")
        if not t:
            continue
        for s in find_symbol(con, t, exact=True)[:per_tok]:
            key = (s["name"], s["file"], s["line"])
            if key not in seen:
                seen.add(key)
                seeds.append(s)
        for s in find_definition(con, t):
            key = (s["name"], s["file"], s["line"])
            if key not in seen:
                seen.add(key)
                seeds.append(s)
    return seeds


def local_select(con: sqlite3.Connection, seeds: list[dict],
                 mmap: dict[str, list[str]], per_module: int = 20) -> list[dict]:
    """Entidades locais SEM arestas: módulos das sementes → tipos locais."""
    mods = sorted({package_of(s["file"]) for s in seeds if s.get("file")})
    wanted: set[str] = set()
    for m in mods:
        wanted.update(mmap.get(m, [])[:per_module])
    wanted.update(s["file"] for s in seeds if s.get("file"))
    out, seen = [], set()
    for s in seeds:  # sementes primeiro (ordem estável), depois tipos locais
        key = (s["name"], s["file"], s["line"])
        if key not in seen:
            seen.add(key)
            out.append(s)
    rows = con.execute(
        "SELECT name, kind, file, line, provenance, confidence FROM symbols "
        "WHERE kind IN ('class','interface','enum') ORDER BY file, line").fetchall()
    for r in rows:
        if r[2] not in wanted:
            continue
        key = (r[0], r[2], r[3])
        if key in seen:
            continue
        seen.add(key)
        out.append({"name": r[0], "kind": r[1], "file": r[2], "line": r[3],
                    "provenance": r[4], "confidence": r[5]})
        if len(out) >= len(seeds) + per_module * max(1, len(mods)):
            break
    return out


def expand_relations(con: sqlite3.Connection, seeds: list[dict],
                     disk: dict[str, list[str]], per_seed: int = 5) -> list[dict]:
    """Expansão por relações verificadas no disco (candidatas, com teto)."""
    out, seen = [], set()
    for s in seeds:
        for r in find_references(con, s["name"], disk)[:per_seed]:
            key = (r["name"], r["file"], r["line"])
            if key in seen:
                continue
            seen.add(key)
            out.append(r)
    return out


def select(con: sqlite3.Connection, query: str, disk: dict[str, list[str]],
           expand: bool = False) -> dict:
    """Ponto único: mesmas sementes; `expand` isola o fator relações."""
    mmap = module_map(con)
    seeds = seed_entities(con, query)
    spans = local_select(con, seeds, mmap)
    rels: list[dict] = []
    if expand:
        rels = expand_relations(con, seeds, disk)
        have = {(s["name"], s["file"], s["line"]) for s in spans}
        for r in rels:
            if (r["name"], r["file"], r["line"]) not in have:
                have.add((r["name"], r["file"], r["line"]))
                spans.append(r)
    files = sorted({s["file"] for s in spans if s.get("file")})
    return {"spans": spans, "files": files, "seeds": seeds,
            "modules": sorted({package_of(s["file"]) for s in seeds if s.get("file")}),
            "expanded": expand, "relations": rels}
