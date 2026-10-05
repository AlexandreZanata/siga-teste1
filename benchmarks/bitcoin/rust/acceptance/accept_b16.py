#!/usr/bin/env python3
"""Aceite BTC-REAL-16: --tmpdirprefix inexistente vira erro de uso.

Diretorio raiz de datadirs inexistente termina com erro de argumentos
(exit 2) citando --tmpdirprefix, antes de criar qualquer diretorio, sem
traceback. Prefixo valido conserva o fluxo existente. Subprocessos com
fixtures proprias (config.ini de fixture, criada e removida pelo harness);
nenhum teste funcional e executado.
Exit 0 = tudo passa; exit 1 = qualquer FAIL.
"""
import os
import subprocess
import sys
import tempfile

WORK = os.environ.get("BTC_WORKSPACE", os.getcwd())
RUNNER = os.path.join(WORK, "test", "functional", "test_runner.py")
CONFIG = os.path.normpath(
    os.path.join(os.path.dirname(RUNNER), "..", "config.ini"))

FAILURES = []
FIXTURE_CONFIG = """[components]
ENABLE_BITCOIND = true
BUILD_BENCH = false
[environment]
SRCDIR = %(src)s
BUILDDIR = %(build)s
"""


def check(name, cond, detail=""):
    if cond:
        print("PASS %s" % name)
    else:
        print("FAIL %s %s" % (name, detail))
        FAILURES.append(name)


def run(args, cwd):
    return subprocess.run(
        [sys.executable, RUNNER] + args,
        cwd=cwd, capture_output=True, text=True, timeout=180)


def main():
    use_fixture = not os.path.exists(CONFIG)
    fashioned = []
    try:
        if use_fixture:
            envdir = tempfile.mkdtemp(prefix="atlas-b16-env-")
            srcdir = os.path.join(envdir, "src")
            os.makedirs(os.path.join(srcdir, "test", "functional"))
            builddir = os.path.join(envdir, "build")
            os.makedirs(builddir)
            with open(CONFIG, "w") as f:
                f.write(FIXTURE_CONFIG % {"src": srcdir, "build": builddir})
            fashioned = [CONFIG, envdir]

        fix = tempfile.mkdtemp(prefix="atlas-b16-")
        missing = os.path.join(fix, "no-such-prefix")

        # 1. prefixo inexistente -> erro de uso citando --tmpdirprefix.
        proc = run(["--tmpdirprefix=%s" % missing,
                    "nosuchtest_xyz_atlas"], fix)
        out = proc.stdout + proc.stderr
        check("missing-prefix-usage-error",
              proc.returncode == 2 and "--tmpdirprefix" in out
              and "Traceback" not in out,
              "exit=%d out=%r" % (proc.returncode, out[-160:]))
        check("missing-prefix-no-dirs",
              not os.path.exists(missing) and os.listdir(fix) == [],
              "fixture modified: %r" % os.listdir(fix))

        # 2. prefixo valido -> segue o fluxo (vazia, legada, sem flag).
        proc = run(["--tmpdirprefix=%s" % fix, "nosuchtest_xyz_atlas"], fix)
        out = proc.stdout + proc.stderr
        check("valid-prefix-passes-validation",
              proc.returncode == 1
              and "not an existing directory" not in out
              and "Traceback" not in out,
              "exit=%d out=%r" % (proc.returncode, out[-160:]))
    finally:
        for path in fashioned:
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                import shutil
                shutil.rmtree(path, ignore_errors=True)
        if os.path.exists(CONFIG) and use_fixture:
            print("FAIL fixture-config-removed: leftover %s" % CONFIG)
            FAILURES.append("fixture-config-removed")
        else:
            print("PASS fixture-config-removed")


main()
if FAILURES:
    print("%d case(s) FAILED" % len(FAILURES))
    sys.exit(1)
print("all cases passed")
