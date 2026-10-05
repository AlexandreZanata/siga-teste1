#!/usr/bin/env python3
"""Aceite BTC-REAL-10: leituras inteiras exigem bytes exatos (EOFError).

deser_compact_size, deser_varint e deser_uint256 devem gerar EOFError em
stream truncado, em vez de 0 silencioso ou IndexError. Na cadeia, um inv
com hash truncado nao pode virar hash zerado. Roundtrips validos
preservados. Sem bitcoind, sem rede.
Exit 0 = tudo passa; exit 1 = qualquer FAIL/excecao inesperada.
"""
import os
import sys
from io import BytesIO

WORK = os.environ.get("BTC_WORKSPACE", os.getcwd())
sys.path.insert(0, os.path.join(WORK, "test", "functional"))

from test_framework.messages import (  # noqa: E402
    deser_compact_size,
    deser_uint256,
    deser_varint,
    msg_getdata,
    ser_compact_size,
)

FAILURES = []


def check(name, cond):
    if cond:
        print("PASS %s" % name)
    else:
        print("FAIL %s" % name)
        FAILURES.append(name)


def check_raises_eof(name, func):
    try:
        result = func()
    except EOFError:
        print("PASS %s" % name)
        return
    except Exception as e:  # noqa: BLE001
        print("FAIL %s: wrong exception %s" % (name, type(e).__name__))
        FAILURES.append(name)
        return
    print("FAIL %s: returned %r instead of raising" % (name, result))
    FAILURES.append(name)


check_raises_eof("compact-empty",
                 lambda: deser_compact_size(BytesIO(b"")))
check_raises_eof("compact-truncated-mid",
                 lambda: deser_compact_size(BytesIO(b"\xfd\x01")))
check_raises_eof("varint-empty",
                 lambda: deser_varint(BytesIO(b"")))
check_raises_eof("uint256-short",
                 lambda: deser_uint256(BytesIO(b"\x00" * 10)))
check_raises_eof("getdata-truncated-hash",
                 lambda: msg_getdata().deserialize(
                     BytesIO(b"\x01" + (1).to_bytes(4, "little")
                             + b"\x00" * 10)) or True)

check("compact-roundtrip",
      deser_compact_size(BytesIO(ser_compact_size(300))) == 300)
check("compact-boundaries",
      deser_compact_size(BytesIO(ser_compact_size(252))) == 252
      and deser_compact_size(BytesIO(ser_compact_size(0x10000))) == 0x10000)
check("uint256-roundtrip",
      deser_uint256(BytesIO((12345).to_bytes(32, "little"))) == 12345)


def check_valid_getdata():
    g = msg_getdata()
    g.deserialize(BytesIO(
        b"\x01" + (2).to_bytes(4, "little") + bytes(range(32))))
    return (len(g.inv) == 1 and g.inv[0].type == 2
            and g.inv[0].hash == int.from_bytes(bytes(range(32)), "little"))


check("getdata-valid-preserved", check_valid_getdata())

if FAILURES:
    print("%d case(s) FAILED" % len(FAILURES))
    sys.exit(1)
print("all cases passed")
