#!/usr/bin/env python3
"""Aceite BTC-REAL-07: sufixo B em ParseByteUnits (build C++ por TU).

Compila de verdade, contra o workspace do avaliador, a unidade
`src/util/strencodings.cpp` (+ `src/crypto/hex_base.cpp`, headers do
snapshot) e executa a sonda `probe_b07.cpp` do atlas-accept: "10B" deve
retornar 10 com qualquer multiplicador padrao; "0B" aceito; B sem numero,
decimal, negativo e overflow rejeitados; demais sufixos e ausencia
preservados.

Adaptacao registrada (CURADORIA_PILOTO.md): build completo (`test_bitcoin`,
Boost.Test) segue bloqueado sem depends/sudo; a TU e autocontida e o
comportamento da unidade e exercitado de verdade — compilador, flags,
fontes e tempos registrados, nada simulado.
Exit 0 = build + 17/17; exit 1 = falha; exit 3 = bloqueio de ambiente
(sem g++ ou fontes do workspace ausentes).
"""
import os
import shutil
import subprocess
import sys
import tempfile

WORK = os.environ.get("BTC_WORKSPACE", os.getcwd())
HERE = os.path.dirname(os.path.abspath(__file__))

SOURCES = [
    "src/util/strencodings.cpp",
    "src/crypto/hex_base.cpp",
]
HEADERS = [
    "src/util/strencodings.h",
    "src/crypto/hex_base.h",
    "src/span.h",
    "src/util/string.h",
]
STD = "-std=c++20"


def env_block(message):
    print("ATLAS-ENV-BLOCK: %s" % message)
    sys.exit(3)


def main():
    cxx = shutil.which(os.environ.get("CXX_BIN", "g++"))
    if cxx is None:
        env_block("g++ ausente no PATH (exige compilador C++20)")
    for rel in SOURCES + HEADERS:
        if not os.path.isfile(os.path.join(WORK, rel)):
            env_block("fonte ausente no workspace: %s" % rel)
    probe = os.path.join(HERE, "probe_b07.cpp")
    if not os.path.isfile(probe):
        env_block("sonda ausente no atlas-accept: probe_b07.cpp")

    build = tempfile.mkdtemp(prefix="atlas-b07-build-")
    try:
        objs = []
        for rel in SOURCES:
            obj = os.path.join(
                build, os.path.basename(rel).replace(".cpp", ".o"))
            proc = subprocess.run(
                [cxx, STD, "-O1", "-I%s" % os.path.join(WORK, "src"),
                 "-c", os.path.join(WORK, rel), "-o", obj],
                capture_output=True, text=True, timeout=300)
            if proc.returncode != 0:
                print("FAIL compile %s:\n%s%s"
                      % (rel, proc.stdout, proc.stderr))
                return 1
            objs.append(obj)
        probe_o = os.path.join(build, "probe_b07.o")
        proc = subprocess.run(
            [cxx, STD, "-O1", "-I%s" % os.path.join(WORK, "src"),
             "-c", probe, "-o", probe_o],
            capture_output=True, text=True, timeout=300)
        if proc.returncode != 0:
            print("FAIL compile probe_b07.cpp:\n%s%s"
                  % (proc.stdout, proc.stderr))
            return 1
        exe = os.path.join(build, "probe_b07")
        proc = subprocess.run(
            [cxx, probe_o] + objs + ["-o", exe],
            capture_output=True, text=True, timeout=300)
        if proc.returncode != 0:
            print("FAIL link:\n%s%s" % (proc.stdout, proc.stderr))
            return 1
        proc = subprocess.run([exe], capture_output=True, text=True,
                              timeout=120)
        sys.stdout.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        if proc.returncode != 0:
            print("FAIL probe exit=%d" % proc.returncode)
            return 1
        return 0
    except subprocess.TimeoutExpired as e:
        print("FAIL timeout: %s" % e)
        return 1
    finally:
        shutil.rmtree(build, ignore_errors=True)


sys.exit(main())
