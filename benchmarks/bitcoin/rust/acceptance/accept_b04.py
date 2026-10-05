#!/usr/bin/env python3
"""Aceite BTC-REAL-04: test_runner rejeita --jobs invalido antes do config.

--jobs=0 e --jobs=-1 terminam com erro de uso citando --jobs, mesmo sem
config.ini; --help segue disponivel (exit 0); --jobs positivo passa pela
validacao de argumentos (segue para a leitura de config, que falha sem
build — comportamento existente preservado). Subprocessos com fixtures
proprias em diretorio temporario; nenhum teste funcional e executado.
Exit 0 = tudo passa; exit 1 = qualquer FAIL.
"""
import os
import subprocess
import sys
import tempfile

WORK = os.environ.get("BTC_WORKSPACE", os.getcwd())
RUNNER = os.path.join(WORK, "test", "functional", "test_runner.py")

FAILURES = []


def run(args, fixture):
    return subprocess.run(
        [sys.executable, RUNNER] + args,
        cwd=fixture, capture_output=True, text=True, timeout=120)


def check_invalid_jobs(label, jobs_arg):
    fixture = tempfile.mkdtemp(prefix="atlas-b04-")
    assert not os.path.exists(os.path.join(fixture, "config.ini"))
    before = set(os.listdir(fixture))
    proc = run([jobs_arg], fixture)
    out = proc.stdout + proc.stderr
    problems = []
    if proc.returncode != 2:
        problems.append("exit=%d, expected 2" % proc.returncode)
    if "--jobs" not in out:
        problems.append("output does not cite --jobs")
    if "config.ini" in out or "Traceback" in out:
        problems.append("fell through to config access")
    if set(os.listdir(fixture)) != before:
        problems.append("fixture dir was modified")
    if problems:
        print("FAIL %s: %s" % (label, "; ".join(problems)))
        FAILURES.append(label)
    else:
        print("PASS %s" % label)


def check_help():
    fixture = tempfile.mkdtemp(prefix="atlas-b04-")
    proc = run(["--help"], fixture)
    out = proc.stdout + proc.stderr
    if proc.returncode == 0 and "--jobs" in out:
        print("PASS help-available")
    else:
        print("FAIL help-available: exit=%d cites-jobs=%s"
              % (proc.returncode, "--jobs" in out))
        FAILURES.append("help-available")


def check_positive_passes_validation():
    fixture = tempfile.mkdtemp(prefix="atlas-b04-")
    proc = run(["--jobs=4"], fixture)
    out = proc.stdout + proc.stderr
    # Sem config.ini o fluxo existente falha na leitura de config (exit 1);
    # o ponto e que a validacao de argumentos NAO o rejeitou antes disso.
    if proc.returncode == 1 and "config.ini" in out \
            and "--jobs must be" not in out:
        print("PASS positive-jobs-pass-validation")
    else:
        print("FAIL positive-jobs-pass-validation: exit=%d out=%r"
              % (proc.returncode, out[-200:]))
        FAILURES.append("positive-jobs-pass-validation")


def check_nonnumeric_rejected():
    fixture = tempfile.mkdtemp(prefix="atlas-b04-")
    proc = run(["--jobs=abc"], fixture)
    if proc.returncode == 2:
        print("PASS nonnumeric-jobs-rejected")
    else:
        print("FAIL nonnumeric-jobs-rejected: exit=%d" % proc.returncode)
        FAILURES.append("nonnumeric-jobs-rejected")


check_invalid_jobs("jobs-zero-rejected", "--jobs=0")
check_invalid_jobs("jobs-negative-rejected", "--jobs=-1")
check_help()
check_positive_passes_validation()
check_nonnumeric_rejected()

if FAILURES:
    print("%d case(s) FAILED" % len(FAILURES))
    sys.exit(1)
print("all cases passed")
