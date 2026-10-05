#!/usr/bin/env python3
"""Aceite BTC-REAL-02: address_to_scriptpubkey aceita Base58 mainnet (v0/v5).

Compara bytes com os construtores independentes de script_util; preserva
testnet/regtest (111/196), witness e rejeicao de checksum invalido.
Importa do workspace do avaliador (BTC_WORKSPACE ou cwd).
Exit 0 = tudo passa; exit 1 = qualquer FAIL/excecao.
"""
import os
import sys

WORK = os.environ.get("BTC_WORKSPACE", os.getcwd())
sys.path.insert(0, os.path.join(WORK, "test", "functional"))

from test_framework.address import (  # noqa: E402
    address_to_scriptpubkey,
    byte_to_base58,
)
from test_framework.script_util import (  # noqa: E402
    keyhash_to_p2pkh_script,
    scripthash_to_p2sh_script,
)

FAILURES = []

PAYLOADS = [
    bytes.fromhex("1f8ea1702a7bd4941bca0941b852c4bbfedb2e05"),
    bytes(20),
    bytes.fromhex("00112233445566778899aabbccddeeff00112233"),
]
VERSIONS = [
    (0, keyhash_to_p2pkh_script, "mainnet-p2pkh"),
    (5, scripthash_to_p2sh_script, "mainnet-p2sh"),
    (111, keyhash_to_p2pkh_script, "testnet-p2pkh"),
    (196, scripthash_to_p2sh_script, "testnet-p2sh"),
]


def check(name, func, expected):
    try:
        got = func()
    except Exception as e:  # noqa: BLE001
        print("FAIL %s: raised %s: %s" % (name, type(e).__name__, e))
        FAILURES.append(name)
        return
    got_b = bytes(got)
    if got_b != expected:
        print("FAIL %s: got %s, expected %s"
              % (name, got_b.hex(), expected.hex()))
        FAILURES.append(name)
        return
    print("PASS %s" % name)


for version, ctor, label in VERSIONS:
    for i, payload in enumerate(PAYLOADS):
        addr = byte_to_base58(payload, version)
        check("%s-payload%d" % (label, i),
              lambda a=addr: address_to_scriptpubkey(a),
              bytes(ctor(payload)))

WITNESS = ("bcrt1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq3xueyj")
check("witness-preserved", lambda: address_to_scriptpubkey(WITNESS),
      bytes.fromhex("00200000000000000000000000000000000000000000000000000000000000000000"))


def check_rejected(name, func):
    try:
        result = func()
    except (ValueError, AssertionError):
        print("PASS %s" % name)
        return
    except Exception as e:  # noqa: BLE001
        print("FAIL %s: wrong exception %s" % (name, type(e).__name__))
        FAILURES.append(name)
        return
    print("FAIL %s: accepted %r" % (name, result))
    FAILURES.append(name)


good = byte_to_base58(bytes(20), 0)
bad = good[:-1] + ("1" if good[-1] != "1" else "2")
check_rejected("bad-checksum-rejected",
               lambda: address_to_scriptpubkey(bad))
check_rejected("unsupported-version-rejected",
               lambda: address_to_scriptpubkey(byte_to_base58(bytes(20), 42)))

if FAILURES:
    print("%d case(s) FAILED" % len(FAILURES))
    sys.exit(1)
print("all cases passed")
