#!/usr/bin/env python3
"""Aceite BTC-REAL-03: AuthServiceProxy aceita application/json com charset.

Variacoes de caixa e espacos no Content-Type; text/html segue rejeitado;
erro JSON-RPC, 204 vazio e Decimal fracionario preservados. Conexao HTTP
fake em-processo — sem daemon, sem rede.
Exit 0 = tudo passa; exit 1 = qualquer FAIL/excecao inesperada.
"""
import decimal
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
    def __init__(self, status, reason, content_type, body):
        self.status = status
        self.reason = reason
        self._content_type = content_type
        self._body = body

    def getheader(self, name):
        if name == "Content-Type":
            return self._content_type
        return None

    def read(self):
        return self._body


class FakeConnection:
    timeout = 30

    def __init__(self, response):
        self._response = response

    def request(self, *args):
        pass

    def getresponse(self):
        return self._response


def proxy_for(status, reason, content_type, body):
    return AuthServiceProxy("http://user:pass@127.0.0.1:1", "m",
                            connection=FakeConnection(
                                FakeResponse(status, reason, content_type, body)))


def check_value(name, content_type, body, expected):
    try:
        got = proxy_for(200, "OK", content_type, body)()
    except Exception as e:  # noqa: BLE001
        print("FAIL %s: raised %s: %s" % (name, type(e).__name__, e))
        FAILURES.append(name)
        return
    if got != expected:
        print("FAIL %s: got %r, expected %r" % (name, got, expected))
        FAILURES.append(name)
        return
    print("PASS %s" % name)


def check_raises(name, content_type, body, expect_code=None):
    try:
        result = proxy_for(200, "OK", content_type, body)()
    except JSONRPCException as e:
        if expect_code is not None and e.error.get("code") != expect_code:
            print("FAIL %s: wrong code %r" % (name, e.error))
            FAILURES.append(name)
            return
        print("PASS %s" % name)
        return
    except Exception as e:  # noqa: BLE001
        print("FAIL %s: wrong exception %s" % (name, type(e).__name__))
        FAILURES.append(name)
        return
    print("FAIL %s: accepted %r" % (name, result))
    FAILURES.append(name)


OK_BODY = json.dumps({"result": 1, "error": None, "id": 1}).encode()

check_value("exact-json", "application/json", OK_BODY, 1)
check_value("json-charset", "application/json; charset=utf-8", OK_BODY, 1)
check_value("json-charset-case", "Application/JSON; Charset=UTF-8", OK_BODY, 1)
check_value("json-charset-spaces",
            "application/json ; charset=utf-8", OK_BODY, 1)
check_value("json-padded", "  application/json  ", OK_BODY, 1)
check_raises("html-rejected", "text/html", b"<html>nope</html>")
check_raises("rpc-error-preserved", "application/json; charset=utf-8",
             json.dumps({"result": None, "error": {"code": -1,
                                                   "message": "oops"},
                         "id": 1}).encode(), expect_code=-1)
check_value("decimal-fraction", "application/json; charset=utf-8",
            json.dumps({"result": 1.5, "error": None, "id": 1}).encode(),
            decimal.Decimal("1.5"))


def check_204():
    try:
        response, status = proxy_for(204, "No Content", "application/json",
                                     b"")._request("POST", "/", b"")
    except Exception as e:  # noqa: BLE001
        print("FAIL no-content-204: raised %s: %s" % (type(e).__name__, e))
        FAILURES.append("no-content-204")
        return
    if response is not None or status != 204:
        print("FAIL no-content-204: got (%r, %r)" % (response, status))
        FAILURES.append("no-content-204")
        return
    print("PASS no-content-204")


check_204()

if FAILURES:
    print("%d case(s) FAILED" % len(FAILURES))
    sys.exit(1)
print("all cases passed")
