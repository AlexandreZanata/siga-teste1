#!/usr/bin/env python3
"""Operador SINTETICO do ensaio NEXT-03 (tentativa A2, tarefa 20).

Simula um executor que entrega correcao PARCIAL: minusculiza a saida de
removeAcentoHTML. O aceite publico (todo minusculo) passa, mas o privado
cobra o passthrough de '&Aacute;' — e o ensaio demonstra o gate.
NAO e modelo, NAO le referencia: existe para ensaiar o pipeline.
"""
import os
from pathlib import Path

ws = Path(os.environ["ATLAS_WORKSPACE"])
p = ws / "siga-base/src/main/java/br/gov/jfrj/siga/base/util/Texto.java"
t = p.read_text()
old = '\t\ttemp = temp.replaceAll("&otilde;", "o");\n\t\treturn temp;'
new = '\t\ttemp = temp.replaceAll("&otilde;", "o");\n\t\treturn temp.toLowerCase();'
assert old in t, "trecho esperado ausente na base do ensaio"
p.write_text(t.replace(old, new))
print("exec-a2: edicao simulada aplicada em Texto.java")
