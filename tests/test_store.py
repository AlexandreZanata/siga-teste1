# SPDX-License-Identifier: Apache-2.0
"""F3: incremental invalida só o arquivo tocado; reindex == full; hash estável."""
import pathlib
import shutil

from archatlas.store import index_many, open_db, stable_hash

A = pathlib.Path("/home/iiii/PESSOAL-PROJETOS-ALEXANDRE/siga/siga-ex/src/main/java/br/gov/jfrj/siga/ex/ExMovimentacao.java")
B = pathlib.Path("/home/iiii/PESSOAL-PROJETOS-ALEXANDRE/siga/siga-ex/src/main/java/br/gov/jfrj/siga/ex/vo/ExMobilVO.java")
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
    assert index_many(con, files, SHA) == {"indexed": 2, "skipped": 0}
    h1 = stable_hash(con)
    assert index_many(con, files, SHA) == {"indexed": 0, "skipped": 2}
    assert stable_hash(con) == h1


def test_touch_one_file_only_it_reindexed(tmp_path):
    files = _workdir(tmp_path)
    con = open_db(tmp_path / "b.sqlite")
    index_many(con, files, SHA)
    h1 = stable_hash(con)
    files[0].write_bytes(files[0].read_bytes() + b"\n// touch\n")
    assert index_many(con, files, SHA) == {"indexed": 1, "skipped": 1}
    h2 = stable_hash(con)
    assert h2 != h1
    # full do zero com mesmo conteúdo == incremental
    con2 = open_db(tmp_path / "c.sqlite")
    index_many(con2, files, SHA)
    assert stable_hash(con2) == h2
