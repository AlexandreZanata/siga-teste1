#!/usr/bin/env python3
"""Aceite BTC-REAL-12: --filter invalido vira erro de uso antes de filtrar.

Regex invalida em --filter termina com erro de argumentos (exit 2) citando
--filter, sem traceback e sem acessar a selecao. Regex valida segue o fluxo
existente. Subprocessos com fixtures proprias (config.ini de fixture,
criada e removida pelo harness); nenhum teste funcional e executado.
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


def run(args, cwd, tmpbase):
    case_tmp = tempfile.mkdtemp(prefix="atlas-b12-case-", dir=tmpbase)
    return subprocess.run(
        [sys.executable, RUNNER, "--tmpdirprefix=%s" % case_tmp] + args,
        cwd=cwd, capture_output=True, text=True, timeout=180)


def main():
    use_fixture = not os.path.exists(CONFIG)
    fashioned = []
    try:
        if use_fixture:
            envdir = tempfile.mkdtemp(prefix="atlas-b12-env-")
            srcdir = os.path.join(envdir, "src")
            os.makedirs(os.path.join(srcdir, "test", "functional"))
            builddir = os.path.join(envdir, "build")
            os.makedirs(builddir)
            with open(CONFIG, "w") as f:
                f.write(FIXTURE_CONFIG % {"src": srcdir, "build": builddir})
            fashioned = [CONFIG, envdir, builddir]

        fix = tempfile.mkdtemp(prefix="atlas-b12-")
        tmpbase = tempfile.mkdtemp(prefix="atlas-b12-tmp-")

        # 1. regex invalida -> erro de uso citando --filter, sem traceback.
        proc = run(["--filter=(["], fix, tmpbase)
        out = proc.stdout + proc.stderr
        check("invalid-filter-usage-error",
              proc.returncode == 2 and "--filter" in out
              and "Traceback" not in out,
              "exit=%d out=%r" % (proc.returncode, out[-160:]))

        # 2. outra regex invalida -> mesmo contrato.
        proc = run(["--filter=*abc"], fix, tmpbase)
        out = proc.stdout + proc.stderr
        check("invalid-filter-star",
              proc.returncode == 2 and "--filter" in out,
              "exit=%d out=%r" % (proc.returncode, out[-160:]))

        # 3. regex valida que casa nada -> segue o fluxo (vazia, legada).
        proc = run(["--filter=zzz_no_match_atlas_xyz"], fix, tmpbase)
        out = proc.stdout + proc.stderr
        check("valid-filter-passes-validation",
              proc.returncode == 1
              and "not a valid regular expression" not in out
              and "Traceback" not in out,
              "exit=%d out=%r" % (proc.returncode, out[-160:]))

        # 4. regex valida que casa testes -> passa da filtragem.
        proc = run(["--filter=feature_fee", "nosuchtest_xyz_atlas"],
                   fix, tmpbase)
        out = proc.stdout + proc.stderr
        check("matching-filter-passes-validation",
              "not a valid regular expression" not in out
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
