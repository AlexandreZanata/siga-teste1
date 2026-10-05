#!/usr/bin/env python3
"""Aceite BTC-REAL-11: resposta JSON nao-objeto vira JSONRPCException.

Chamada unica cujo corpo e JSON valido mas nao-objeto (lista, numero,
string, null) deve gerar JSONRPCException, sem TypeError interno.
Dicts (resultado e erro) e batch com lista preservados. Conexao fake
em-processo — sem daemon, sem rede.
Exit 0 = tudo passa; exit 1 = qualquer FAIL/excecao inesperada.
"""
import json
import os
import sys

WORK = os.environ.get("BTC_WORKSPACE", os.getcwd())
sys.path.insert(0, os.path.join(WORK, "test", "functional"))

from test_framework.authproxy import (  # noqa: E402
    AuthServiceProxy,
    JSONRPCException,
)

FAILURES = []


class FakeResponse:
    status = 200
    reason = "OK"

    def __init__(self, body):
        self._body = body

    def getheader(self, name):
        if name == "Content-Type":
            return "application/json"
        return None

    def read(self):
        return self._body


class FakeConnection:
    timeout = 30

    def __init__(self, body):
        self._body = body

    def request(self, *args):
        pass

    def getresponse(self):
        return FakeResponse(self._body)


def proxy_for(body):
    return AuthServiceProxy("http://user:pass@127.0.0.1:1", "m",
                            connection=FakeConnection(body))


def check_raises(name, body):
    try:
        result = proxy_for(body)()
    except JSONRPCException:
        print("PASS %s" % name)
        return
    except Exception as e:  # noqa: BLE001
        print("FAIL %s: wrong exception %s" % (name, type(e).__name__))
        FAILURES.append(name)
        return
    print("FAIL %s: accepted %r" % (name, result))
    FAILURES.append(name)


check_raises("list-rejected", b"[1,2]")
check_raises("number-rejected", b"5")
check_raises("string-rejected", b'"str"')
check_raises("null-rejected", b"null")

try:
    got = proxy_for(json.dumps(
        {"result": 7, "error": None, "id": 1}).encode())()
    if got == 7:
        print("PASS dict-result-preserved")
    else:
        print("FAIL dict-result-preserved: got %r" % got)
        FAILURES.append("dict-result-preserved")
except Exception as e:  # noqa: BLE001
    print("FAIL dict-result-preserved: raised %s" % type(e).__name__)
    FAILURES.append("dict-result-preserved")

try:
    proxy_for(json.dumps(
        {"result": None, "error": {"code": -3, "message": "x"},
         "id": 1}).encode())()
    print("FAIL dict-error-preserved: accepted")
    FAILURES.append("dict-error-preserved")
except JSONRPCException as e:
    if e.error.get("code") == -3:
        print("PASS dict-error-preserved")
    else:
        print("FAIL dict-error-preserved: wrong code %r" % e.error)
        FAILURES.append("dict-error-preserved")

try:
    items = [{"result": 9, "error": None, "id": 1}]
    got = proxy_for(json.dumps(items).encode()).batch(
        [{"method": "m", "id": 1}])
    if got == items:
        print("PASS batch-list-preserved")
    else:
        print("FAIL batch-list-preserved: got %r" % got)
        FAILURES.append("batch-list-preserved")
except Exception as e:  # noqa: BLE001
    print("FAIL batch-list-preserved: raised %s" % type(e).__name__)
    FAILURES.append("batch-list-preserved")

if FAILURES:
    print("%d case(s) FAILED" % len(FAILURES))
    sys.exit(1)
print("all cases passed")
