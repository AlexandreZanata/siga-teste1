from archatlas.config import REPO_ROOT, dataset_root
# SPDX-License-Identifier: Apache-2.0
"""F3: incremental invalida só o arquivo tocado; reindex == full; hash estável."""
import pathlib
import shutil

from archatlas.store import index_many, open_db, stable_hash

A = dataset_root() / "siga-ex/src/main/java/br/gov/jfrj/siga/ex/ExMovimentacao.java"
B = dataset_root() / "siga-ex/src/main/java/br/gov/jfrj/siga/ex/vo/ExMobilVO.java"
SHA = "e3be22828f787cbe71b339aecb7a7bf569099803"


def _workdir(tmp_path, n=2):
    d = tmp_path / "w"
    d.mkdir()
    files = []
    for i, src in enumerate([A, B][:n]):
        dst = d / f"F{i}.java"
        shutil.copy(src, dst)
        files.append(dst)
    return files


def test_full_then_noop_stable(tmp_path):
    files = _workdir(tmp_path)
    con = open_db(tmp_path / "a.sqlite")
    assert index_many(con, files, SHA) == {"indexed": 2, "skipped": 0,
                                           "pruned_files": 0, "pruned_symbols": 0}
    h1 = stable_hash(con)
    assert index_many(con, files, SHA) == {"indexed": 0, "skipped": 2,
                                           "pruned_files": 0, "pruned_symbols": 0}
    assert stable_hash(con) == h1


def test_touch_one_file_only_it_reindexed(tmp_path):
    files = _workdir(tmp_path)
    con = open_db(tmp_path / "b.sqlite")
    index_many(con, files, SHA)
    h1 = stable_hash(con)
    files[0].write_bytes(files[0].read_bytes() + b"\n// touch\n")
    assert index_many(con, files, SHA) == {"indexed": 1, "skipped": 1,
                                           "pruned_files": 0, "pruned_symbols": 0}
    h2 = stable_hash(con)
    assert h2 != h1
    # full do zero com mesmo conteúdo == incremental
    con2 = open_db(tmp_path / "c.sqlite")
    index_many(con2, files, SHA)
    assert stable_hash(con2) == h2


def test_prune_delete_and_rename_equiv_rebuild(tmp_path):
    """P4 GC: delete/rename invalidados; incremental == rebuild lógico."""
    from archatlas.store import prune_missing
    from archatlas.verify import verify_symbol
    files = _workdir(tmp_path)
    con = open_db(tmp_path / "d.sqlite")
    index_many(con, files, SHA)
    files[0].write_bytes(files[0].read_bytes() + b"\n// edit\n")
    files[1].unlink()  # delete: path some
    assert index_many(con, [files[0]], SHA)["pruned_files"] == 1
    assert con.execute("SELECT COUNT(*) FROM files WHERE path=?",
                       (str(files[1]),)).fetchone()[0] == 0  # GC removeu o path
    assert con.execute("SELECT COUNT(*) FROM symbols WHERE file=?",
                       (str(files[1]),)).fetchone()[0] == 0  # e seus símbolos
    renamed = tmp_path / "w" / "F9.java"
    files[0].rename(renamed)  # rename = delete+add
    assert index_many(con, [renamed], SHA)["pruned_files"] == 1
    fresh = open_db(tmp_path / "e.sqlite")
    index_many(fresh, [renamed], SHA)
    assert stable_hash(fresh) == stable_hash(con)  # equivalência lógica H4
    assert prune_missing(con) == {"pruned_files": 0, "pruned_symbols": 0}  # idempotente
    row = con.execute("SELECT name,file,line,content_hash FROM symbols LIMIT 1").fetchone()
    assert verify_symbol({"name": row[0], "file": row[1], "line": row[2],
                          "content_hash": row[3]}) == (True, "ok")
