#!/usr/bin/env python3
"""Aceite BTC-REAL-09: descsum_create rejeita fora do alfabeto com ValueError.

Criar checksum de descritor com caracteres fora do alfabeto deve gerar
ValueError claro, sem TypeError interno e sem mudar o algoritmo.
Importa `descriptors` do workspace do avaliador (BTC_WORKSPACE ou cwd).
Exit 0 = todos os casos passam; exit 1 = qualquer FAIL/excecao.
"""
import os
import sys

WORK = os.environ.get("BTC_WORKSPACE", os.getcwd())
sys.path.insert(0, os.path.join(WORK, "test", "functional", "test_framework"))

import descriptors  # noqa: E402

FAILURES = []


def check_value_error(name, func):
    try:
        result = func()
    except ValueError:
        print("PASS %s" % name)
        return
    except Exception as e:  # noqa: BLE001
        print("FAIL %s: wrong exception %s: %s"
              % (name, type(e).__name__, e))
        FAILURES.append(name)
        return
    print("FAIL %s: accepted %r" % (name, result))
    FAILURES.append(name)


def check(name, func, expected):
    try:
        got = func()
    except Exception as e:  # noqa: BLE001
        print("FAIL %s: raised %s: %s" % (name, type(e).__name__, e))
        FAILURES.append(name)
        return
    if got != expected:
        print("FAIL %s: got %r, expected %r" % (name, got, expected))
        FAILURES.append(name)
        return
    print("PASS %s" % name)


check_value_error("unicode-body-rejected",
                  lambda: descriptors.descsum_create("pk(☃)"))
check_value_error("unicode-suffix-rejected",
                  lambda: descriptors.descsum_create("wpkh(abc)☃"))
check("valid-create-checks",
      lambda: descriptors.descsum_check(descriptors.descsum_create(
          "pk(0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798)")),
      True)
check("empty-preserved",
      lambda: descriptors.descsum_create(""), "#7h0w2xvg")

if FAILURES:
    print("%d case(s) FAILED" % len(FAILURES))
    sys.exit(1)
print("all cases passed")
