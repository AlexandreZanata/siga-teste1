#!/usr/bin/env python3
"""Aceite BTC-REAL-15: satoshi_round exige modo de arredondamento explicito.

Modo invalido (string desconhecida, None, numero) gera ValueError claro,
em vez de TypeError interno ou fallback silencioso para o default do
contexto. Os 8 modos decimais e os arredondamentos preservados.
Exit 0 = tudo passa; exit 1 = qualquer FAIL/excecao inesperada.
"""
import os
import sys
from decimal import (
    ROUND_05UP,
    ROUND_CEILING,
    ROUND_DOWN,
    ROUND_FLOOR,
    ROUND_HALF_DOWN,
    ROUND_HALF_EVEN,
    ROUND_HALF_UP,
    ROUND_UP,
)

WORK = os.environ.get("BTC_WORKSPACE", os.getcwd())
sys.path.insert(0, os.path.join(WORK, "test", "functional"))

from test_framework.util import satoshi_round  # noqa: E402

FAILURES = []


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
    print("FAIL %s: accepted %r" % (name, result))
    FAILURES.append(name)


def check(name, cond):
    if cond:
        print("PASS %s" % name)
    else:
        print("FAIL %s" % name)
        FAILURES.append(name)


check_value_error("bogus-mode-rejected",
                  lambda: satoshi_round("1.5", rounding="BOGUS"))
check_value_error("none-mode-rejected",
                  lambda: satoshi_round("1.5", rounding=None))
check_value_error("int-mode-rejected",
                  lambda: satoshi_round("1.5", rounding=123))
check("round-down",
      str(satoshi_round("1.000000005", rounding=ROUND_DOWN)) == "1.00000000")
check("round-up",
      str(satoshi_round("1.000000001", rounding=ROUND_UP)) == "1.00000001")
check("round-half-even",
      str(satoshi_round("1.000000005",
                        rounding=ROUND_HALF_EVEN)) == "1.00000000")
check("all-modes-accepted",
      all(satoshi_round("1.000000005", rounding=m) is not None
          for m in (ROUND_05UP, ROUND_CEILING, ROUND_DOWN, ROUND_FLOOR,
                    ROUND_HALF_DOWN, ROUND_HALF_EVEN, ROUND_HALF_UP,
                    ROUND_UP)))

if FAILURES:
    print("%d case(s) FAILED" % len(FAILURES))
    sys.exit(1)
print("all cases passed")
