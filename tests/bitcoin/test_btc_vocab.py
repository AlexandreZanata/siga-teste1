# SPDX-License-Identifier: Apache-2.0
"""btc-vocab/1: split mecânico de identificadores. Sem corpus, sem modelo."""
from archatlas.bitcoin.vocab import ALIASES, expand_query, split_identifiers


def test_split_snake_kebab_camel_and_dedup():
    assert split_identifiers("mempool_accept") == ["mempool_accept", "mempool", "accept"]
    assert split_identifiers("top-4 X") == ["top-4", "top", "4", "x"]
    assert split_identifiers("CheckTransaction validation") == [
        "checktransaction", "check", "transaction", "validation"]
    assert split_identifiers("mempool mempool_accept") == ["mempool", "mempool_accept", "accept"]


def test_expand_adds_parts_and_optional_aliases():
    q, added = expand_query("mempool_accept failure")
    assert q == "mempool_accept mempool accept failure" and added == ["mempool", "accept"]
    q2, added2 = expand_query("address manager", ALIASES)
    assert "addrman" in q2.split() and "addrman" in added2
    q3, added3 = expand_query("address manager")
    assert "addrman" not in q3.split() and added3 == []
    assert ALIASES["address"][1] == "src/addrman.h:59@9be056a8"
