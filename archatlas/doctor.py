# SPDX-License-Identifier: Apache-2.0
"""P4/E26-06: diagnóstico de instalação e suporte (sem MCP; só quando necessário).

Nunca resultado vazio enganoso: índice ausente/corrompido/incompatível e linguagem
sem suporte geram diagnóstico + conselho de fallback (leitura/busca direta),
jamais lista vazia fingindo resposta. Desinstalar remove só o diretório do índice.
"""
from __future__ import annotations
import pathlib
import shutil
import sqlite3
import sys

SCHEMA_VERSION = 1
LEGACY_VERSIONS = (0, 1)  # 0 = pré-versionamento; ambos legíveis por este código
ATLAS_VERSION = "0.1.0"


def check_env() -> dict:
    """Ambiente limpo: versão, rede/GPU desnecessárias, instalação isolada."""
    return {"atlas_version": ATLAS_VERSION, "schema_version": SCHEMA_VERSION,
            "python": sys.version.split()[0], "needs_network": False,
            "needs_gpu": False, "install": "local-only"}


def language_support(lang_or_ext: str) -> dict:
    """Capacidades declaradas por linguagem (sem prometer suporte estrutural)."""
    key = lang_or_ext.lower().lstrip(".")
    if key in ("java",):
        return {"language": key, "level": "structural",
                "note": "regex auditado + verificação nome-na-linha"}
    return {"language": key, "level": "lexical-fallback",
            "note": "sem extrator dedicado; busca textual verificada no disco"}


def index_state(db: pathlib.Path | str) -> dict:
    """Estado do índice: ok | missing | corrupt | incompatible (+ contagens)."""
    db = pathlib.Path(db)
    if not db.exists():
        return {"state": "missing", "db": str(db),
                "advice": "rode archatlas index; ou use leitura/busca direta"}
    try:
        con = sqlite3.connect(db)
        tables = {r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if not {"files", "symbols"} <= tables:
            return {"state": "corrupt", "db": str(db),
                    "advice": "índice sem tabelas atlas; apague e reindexe, ou use busca direta"}
        ver = con.execute("PRAGMA user_version").fetchone()[0]
        if ver not in LEGACY_VERSIONS and ver != SCHEMA_VERSION:
            return {"state": "incompatible", "db": str(db),
                    "user_version": ver, "schema_version": SCHEMA_VERSION,
                    "advice": "versão de schema divergente; reindexe do zero"}
        n_f = con.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        n_s = con.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
        con.close()
        return {"state": "ok", "db": str(db), "files": n_f, "symbols": n_s,
                "schema_version": SCHEMA_VERSION}
    except sqlite3.DatabaseError:
        return {"state": "corrupt", "db": str(db),
                "advice": "arquivo não é SQLite válido; apague e reindexe, ou use busca direta"}


def uninstall(atlas_dir: pathlib.Path | str) -> dict:
    """Remove SÓ o diretório do índice; código e config global intocados por construção."""
    d = pathlib.Path(atlas_dir)
    if not d.exists():
        return {"removed": False, "dir": str(d), "code_untouched": True}
    shutil.rmtree(d)
    return {"removed": True, "dir": str(d), "code_untouched": True}
