#!/usr/bin/env python3
"""Aceite BTC-REAL-08: --fail-if-empty para selecao vazia de testes.

Com a flag, selecao vazia apos filtros/exclusoes termina com erro e
mensagem clara, sem criar cache de testes nem iniciar daemon. Sem a flag,
o comportamento atual e preservado. A flag aparece em --help.
Subprocessos com fixtures proprias (config.ini isolada, removida ao fim);
nenhum teste funcional e executado, nenhum daemon iniciado.
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
FAKE_SCRIPT = ("#!/usr/bin/env python3\nimport sys\n"
               "print('fake bench help')\n")


def check(name, cond, detail=""):
    if cond:
        print("PASS %s" % name)
    else:
        print("FAIL %s %s" % (name, detail))
        FAILURES.append(name)


def run(args, cwd, tmpbase):
    # Prefixo unico por invocacao: o diretorio timestampado do runner tem
    # resolucao de 1 s e casos consecutivos colidiriam no mesmo prefixo.
    case_tmp = tempfile.mkdtemp(prefix="atlas-b08-case-", dir=tmpbase)
    return subprocess.run(
        [sys.executable, RUNNER, "--tmpdirprefix=%s" % case_tmp] + args,
        cwd=cwd, capture_output=True, text=True, timeout=180)


def main():
    use_fixture = not os.path.exists(CONFIG)
    fashioned = []
    try:
        if use_fixture:
            envdir = tempfile.mkdtemp(prefix="atlas-b08-env-")
            srcdir = os.path.join(envdir, "src")
            scriptdir = os.path.join(srcdir, "test", "functional")
            os.makedirs(scriptdir)
            with open(os.path.join(
                    scriptdir, "tool_bench_sanity_check.py"), "w") as f:
                f.write(FAKE_SCRIPT)
            builddir = os.path.join(envdir, "build")
            os.makedirs(builddir)
            with open(CONFIG, "w") as f:
                f.write(FIXTURE_CONFIG % {"src": srcdir, "build": builddir})
            fashioned = [CONFIG, envdir, builddir]
        else:
            builddir = None

        # 1. empty selection + flag -> error citing --fail-if-empty.
        fix = tempfile.mkdtemp(prefix="atlas-b08-")
        tmpbase = tempfile.mkdtemp(prefix="atlas-b08-tmp-")
        before = set(os.listdir(fix))
        proc = run(["nosuchtest_xyz_atlas", "--fail-if-empty"], fix, tmpbase)
        out = proc.stdout + proc.stderr
        check("empty-with-flag-errors",
              proc.returncode == 1 and "--fail-if-empty" in out,
              "exit=%d out=%r" % (proc.returncode, out[-160:]))
        check("empty-with-flag-no-cache",
              set(os.listdir(fix)) == before
              and (builddir is None or not os.listdir(builddir)),
              "fixture modified or cache created")

        # 2. empty selection without flag -> legacy behavior preserved.
        proc = run(["nosuchtest_xyz_atlas"], fix, tmpbase)
        out = proc.stdout + proc.stderr
        check("empty-without-flag-legacy",
              proc.returncode == 1
              and "No valid test scripts" in out
              and "--fail-if-empty" not in out,
              "exit=%d out=%r" % (proc.returncode, out[-160:]))

        # 3. empty via --filter + flag -> error citing --fail-if-empty.
        proc = run(["--filter=zzz_no_match_atlas_xyz", "--fail-if-empty"],
                   fix, tmpbase)
        out = proc.stdout + proc.stderr
        check("filter-empty-with-flag-errors",
              proc.returncode == 1 and "--fail-if-empty" in out,
              "exit=%d out=%r" % (proc.returncode, out[-160:]))

        # 4. non-empty selection + flag -> passes the strict gate.
        proc = run(["--filter=feature_fee", "--fail-if-empty"], fix, tmpbase)
        out = proc.stdout + proc.stderr
        check("nonempty-passes-gate",
              "test selection is empty" not in out,
              "exit=%d out=%r" % (proc.returncode, out[-160:]))

        # 5. --help advertises the flag (fixture env only, deterministic).
        if use_fixture:
            proc = run(["--help"], fix, tmpbase)
            out = proc.stdout + proc.stderr
            check("help-advertises-flag",
                  proc.returncode == 0 and "--fail-if-empty" in out,
                  "exit=%d cites=%s" % (proc.returncode,
                                        "--fail-if-empty" in out))
        else:
            print("SKIP help-advertises-flag (config preexistente no workspace)")
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
