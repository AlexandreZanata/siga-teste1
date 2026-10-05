#!/usr/bin/env python3
"""Aceite BTC-REAL-14: build_message rejeita tipo > 12 bytes.

Tipo P2P com mais de 12 bytes gera ValueError na construcao, em vez de
montar silenciosamente um frame cujo campo carrega outro valor (despacho
corrompido). Tipos de ate 12 bytes e ida-e-volta valida preservados;
cadeia de recepcao percorre desserializacao e callback. Sem bitcoind.
Exit 0 = tudo passa; exit 1 = qualquer FAIL/excecao inesperada.
"""
import hashlib
import os
import sys

WORK = os.environ.get("BTC_WORKSPACE", os.getcwd())
sys.path.insert(0, os.path.join(WORK, "test", "functional"))

from test_framework import p2p as p2p_mod  # noqa: E402
from test_framework.messages import msg_ping  # noqa: E402
from test_framework.p2p import P2PConnection  # noqa: E402

FAILURES = []


class FakeMsg:
    def __init__(self, msgtype):
        self.msgtype = msgtype

    def serialize(self):
        return b"data"


def check(name, cond):
    if cond:
        print("PASS %s" % name)
    else:
        print("FAIL %s" % name)
        FAILURES.append(name)


def fresh_conn():
    conn = P2PConnection()
    conn.peer_connect_helper("127.0.0.1", 0, "regtest", timeout_factor=1)
    return conn


conn = fresh_conn()
try:
    conn.build_message(FakeMsg(b"1234567890123"))
    check("long-type-rejected", False)
except ValueError:
    check("long-type-rejected", True)
except Exception as e:  # noqa: BLE001
    print("FAIL long-type-rejected: wrong exception %s" % type(e).__name__)
    FAILURES.append("long-type-rejected")

frame12 = conn.build_message(FakeMsg(b"123456789012"))
check("twelve-type-preserved", frame12[4:16] == b"123456789012")
frame0 = conn.build_message(FakeMsg(b""))
check("empty-type-preserved", frame0[4:16] == b"\x00" * 12)


class Sink(P2PConnection):
    def __init__(self):
        super().__init__()
        self.calls = []
        self.peer_connect_helper("127.0.0.1", 0, "regtest", timeout_factor=1)

    def on_message(self, message):
        self.calls.append(message)


sink = Sink()
ping = msg_ping(nonce=123)
payload = ping.serialize()
digest = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
sink.recvbuf = (p2p_mod.MAGIC_BYTES["regtest"] + b"ping" + b"\x00" * 8
                + len(payload).to_bytes(4, "little") + digest + payload)
try:
    sink._on_data()
    check("ping-roundtrip-callback",
          len(sink.calls) == 1 and sink.calls[0].nonce == 123)
except Exception as e:  # noqa: BLE001
    print("FAIL ping-roundtrip-callback: raised %s" % type(e).__name__)
    FAILURES.append("ping-roundtrip-callback")

if FAILURES:
    print("%d case(s) FAILED" % len(FAILURES))
    sys.exit(1)
print("all cases passed")
