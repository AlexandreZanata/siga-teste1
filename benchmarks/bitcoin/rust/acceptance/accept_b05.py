#!/usr/bin/env python3
"""Aceite BTC-REAL-05: proxies derivados preservam opcoes do pai.

ensure_ascii e reuse_http_connections configurados no pai propagam para
filhos via atributo/metodo e via operador /. Timeout e conexao
compartilhada conservados; filho ja criado nao muda quando o pai muda.
Conexao fake em-processo — sem daemon, sem rede.
Exit 0 = tudo passa; exit 1 = qualquer FAIL/excecao inesperada.
"""
import os
import sys

WORK = os.environ.get("BTC_WORKSPACE", os.getcwd())
sys.path.insert(0, os.path.join(WORK, "test", "functional"))

from test_framework.authproxy import AuthServiceProxy  # noqa: E402

FAILURES = []


class FakeConnection:
    timeout = 30

    def request(self, *args):
        raise AssertionError("no network in acceptance")

    def getresponse(self):
        raise AssertionError("no network in acceptance")


def check(name, cond):
    if cond:
        print("PASS %s" % name)
    else:
        print("FAIL %s" % name)
        FAILURES.append(name)


def make_parent(**kwargs):
    conn = FakeConnection()
    parent = AuthServiceProxy("http://user:pass@127.0.0.1:1", **kwargs)
    # Rebind to the fake connection without network (same as constructor arg).
    parent._set_conn(conn)
    return parent, conn


parent, conn = make_parent(ensure_ascii=False)
parent.reuse_http_connections = False

def conn_of(proxy):
    return proxy._AuthServiceProxy__conn


child = parent.some_method
check("attr-ensure-ascii", child.ensure_ascii is False)
check("attr-reuse-conn", child.reuse_http_connections is False)
check("attr-shares-connection", conn_of(child) is conn_of(parent))
check("attr-timeout", child.timeout == conn_of(parent).timeout)

sub = parent / "wallet/test-wallet"
check("div-ensure-ascii", sub.ensure_ascii is False)
check("div-reuse-conn", sub.reuse_http_connections is False)
check("div-shares-connection", conn_of(sub) is conn_of(parent))

parent.ensure_ascii = True
parent.reuse_http_connections = True
check("child-frozen-after-parent-change",
      child.ensure_ascii is False and child.reuse_http_connections is False)

parent2, _ = make_parent()
check("default-ensure-ascii", parent2.other.ensure_ascii is True)
check("default-reuse-conn",
      parent2.other.reuse_http_connections is True)

req = child.get_request(1, 2)
check("child-usable", req["method"] == "some_method"
      and req["params"] == (1, 2))

if FAILURES:
    print("%d case(s) FAILED" % len(FAILURES))
    sys.exit(1)
print("all cases passed")
