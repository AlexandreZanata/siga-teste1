#!/usr/bin/env python3
"""Aceite BTC-REAL-01: descsum_check retorna False para checksum malformado.

Sem excecao (IndexError/TypeError), sem mudar o algoritmo de checksum.
Importa `descriptors` do workspace do avaliador (BTC_WORKSPACE ou cwd).
Exit 0 = todos os casos passam; exit 1 = qualquer FAIL/excecao.
"""
import os
import sys

WORK = os.environ.get("BTC_WORKSPACE", os.getcwd())
sys.path.insert(0, os.path.join(WORK, "test", "functional", "test_framework"))

import descriptors  # noqa: E402

FAILURES = []


def check(name, func, expected):
    try:
        got = func()
    except Exception as e:  # noqa: BLE001 — excecao aqui e FAIL, nao crash
        print("FAIL %s: raised %s: %s" % (name, type(e).__name__, e))
        FAILURES.append(name)
        return
    if got is not expected and got != expected:
        print("FAIL %s: got %r, expected %r" % (name, got, expected))
        FAILURES.append(name)
        return
    print("PASS %s" % name)


VALID1 = descriptors.descsum_create(
    "pk(0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798)")
VALID2 = descriptors.descsum_create(
    "wpkh(0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798)")
MUTATED = VALID1[:-1] + ("q" if VALID1[-1] != "q" else "p")

check("short-hash-returns-false", lambda: descriptors.descsum_check("#"), False)
check("unicode-body-returns-false",
      lambda: descriptors.descsum_check("☃#aaaaaaaa"), False)
check("short-checksum-returns-false",
      lambda: descriptors.descsum_check("a#short"), False)
check("empty-checksum-returns-false",
      lambda: descriptors.descsum_check("#12345678"), False)
check("valid-checksum-accepted", lambda: descriptors.descsum_check(VALID1), True)
check("valid-wpkh-accepted", lambda: descriptors.descsum_check(VALID2), True)
check("mutated-checksum-rejected",
      lambda: descriptors.descsum_check(MUTATED), False)
check("no-separator-require-true",
      lambda: descriptors.descsum_check("pk(abc)", require=True), False)
check("no-separator-require-false",
      lambda: descriptors.descsum_check("pk(abc)", require=False), True)

if FAILURES:
    print("%d case(s) FAILED" % len(FAILURES))
    sys.exit(1)
print("all %d cases passed" % 9)
