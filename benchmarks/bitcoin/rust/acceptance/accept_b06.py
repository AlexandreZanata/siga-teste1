#!/usr/bin/env python3
"""Aceite BTC-REAL-06: desserializacao rejeita string P2P truncada.

deser_string com EOF antes do comprimento declarado gera EOFError; na
recepcao P2P sintetica (frame v1 valido com payload truncado) a mensagem
nao chega ao on_message; mensagem valida chama uma vez. Vazias, validas
e cursor apos leitura preservados. Socket/frame sinteticos locais —
sem bitcoind, sem rede.
Exit 0 = tudo passa; exit 1 = qualquer FAIL/excecao inesperada.
"""
import hashlib
import os
import sys
from io import BytesIO

WORK = os.environ.get("BTC_WORKSPACE", os.getcwd())
sys.path.insert(0, os.path.join(WORK, "test", "functional"))

from test_framework import p2p as p2p_mod  # noqa: E402
from test_framework.messages import (  # noqa: E402
    deser_string,
    msg_filterload,
    ser_compact_size,
    ser_string,
)
from test_framework.p2p import P2PConnection  # noqa: E402

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


check_raises_eof("truncated-raises-eoferror",
                 lambda: deser_string(BytesIO(ser_compact_size(100) + b"AB")))

f = BytesIO(ser_string(b"AB") + b"TRAIL")
check("valid-cursor-preserved",
      deser_string(f) == b"AB" and f.read() == b"TRAIL")
check("empty-string-ok",
      deser_string(BytesIO(ser_compact_size(0))) == b"")
check("valid-string-ok",
      deser_string(BytesIO(ser_string(b"hello world"))) == b"hello world")


class Sink(P2PConnection):
    def __init__(self):
        super().__init__()
        self.calls = []
        self.peer_connect_helper("127.0.0.1", 0, "regtest", timeout_factor=1)

    def on_message(self, message):
        self.calls.append(message)


def frame(msgtype, payload):
    digest = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    return (p2p_mod.MAGIC_BYTES["regtest"] + msgtype
            + b"\x00" * (12 - len(msgtype))
            + len(payload).to_bytes(4, "little") + digest + payload)


trunc = Sink()
trunc.recvbuf = frame(b"filterload", ser_compact_size(100) + b"AB")
try:
    trunc._on_data()
    check("p2p-truncated-no-callback", False)
except EOFError:
    check("p2p-truncated-no-callback", len(trunc.calls) == 0)
except Exception as e:  # noqa: BLE001
    print("FAIL p2p-truncated-no-callback: wrong exception %s"
          % type(e).__name__)
    FAILURES.append("p2p-truncated-no-callback")

valid = Sink()
msg = msg_filterload(data=b"hello", nHashFuncs=3, nTweak=7, nFlags=1)
valid.recvbuf = frame(b"filterload", msg.serialize())
try:
    valid._on_data()
except Exception as e:  # noqa: BLE001
    print("FAIL p2p-valid-called-once: raised %s" % type(e).__name__)
    FAILURES.append("p2p-valid-called-once")
else:
    check("p2p-valid-called-once",
          len(valid.calls) == 1 and valid.calls[0].data == b"hello"
          and valid.calls[0].nHashFuncs == 3)

if FAILURES:
    print("%d case(s) FAILED" % len(FAILURES))
    sys.exit(1)
print("all cases passed")
