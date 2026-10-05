#!/usr/bin/env python3
"""Aceite BTC-REAL-13: multisig exige 1 <= k <= n com ValueError.

keys_to_multisig_script com k=0, k>n ou lista vazia deve gerar ValueError,
em vez de montar silenciosamente scripts degenerados. n-de-n padrao e
k validos preservados.
Exit 0 = tudo passa; exit 1 = qualquer FAIL/excecao inesperada.
"""
import os
import sys

WORK = os.environ.get("BTC_WORKSPACE", os.getcwd())
sys.path.insert(0, os.path.join(WORK, "test", "functional"))

from test_framework.script_util import (  # noqa: E402
    keys_to_multisig_script,
)

FAILURES = []
K1 = bytes(33)
K2 = bytes([1]) * 33


def check_value_error(name, func):
    try:
        result = func()
    except ValueError:
        print("PASS %s" % name)
        return
    except Exception as e:  # noqa: BLE001
        print("FAIL %s: wrong exception %s" % (name, type(e).__name__))
        FAILURES.append(name)
        return
    print("FAIL %s: built %r" % (name, bytes(result).hex()))
    FAILURES.append(name)


def check(name, cond):
    if cond:
        print("PASS %s" % name)
    else:
        print("FAIL %s" % name)
        FAILURES.append(name)


check_value_error("k-zero-rejected",
                  lambda: keys_to_multisig_script([K1, K2], k=0))
check_value_error("k-above-n-rejected",
                  lambda: keys_to_multisig_script([K1, K2], k=3))
check_value_error("empty-keys-rejected",
                  lambda: keys_to_multisig_script([]))
check("n-of-n-default",
      bytes(keys_to_multisig_script([K1, K2])).hex().startswith("52"))
check("one-of-two",
      bytes(keys_to_multisig_script([K1, K2], k=1)).hex().startswith("51"))
check("two-of-three",
      bytes(keys_to_multisig_script(
          [K1, K2, bytes([2]) * 33], k=2)).hex().startswith("52"))

if FAILURES:
    print("%d case(s) FAILED" % len(FAILURES))
    sys.exit(1)
print("all cases passed")
