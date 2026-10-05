#!/usr/bin/env python3
"""Operador SINTETICO do ensaio NEXT-03 (tentativa A1, tarefa 17).

Simula um executor que entrega a correcao da query canonica de AcaoVO.getUrl.
NAO e modelo, NAO le referencia: existe para ensaiar o pipeline.
"""
import os
from pathlib import Path

ws = Path(os.environ["ATLAS_WORKSPACE"])
p = ws / "siga-base/src/main/java/br/gov/jfrj/siga/base/AcaoVO.java"
t = p.read_text()
old = ('\t\tString resultUrl = "";\n'
       '\t\tif (this.params != null) {\n'
       '\t\t\tString valueOfParameterToAdd;\n'
       '\t\t\tMap<String, String> parameters = this.params;\n'
       '\t\t\tSet<String> parametersNames = this.params.keySet();\n'
       '\t\t\tfor (String nameOfParameterToAdd : parametersNames) {\n'
       '\t\t\t\tvalueOfParameterToAdd = parameters.get(nameOfParameterToAdd);\n'
       '\t\t\t\tresultUrl = (nameOfParameterToAdd + "=" + valueOfParameterToAdd + "&").concat(resultUrl);\n'
       '\t\t\t}\n'
       '\t\t\tif (!parametersNames.isEmpty())\n'
       '\t\t\t\tresultUrl = ("?").concat(resultUrl);\n'
       '\t\t}')
new = ('\t\tString resultUrl = "";\n'
       '\t\tif (this.params != null) {\n'
       '\t\t\tStringBuilder query = new StringBuilder();\n'
       '\t\t\tfor (Map.Entry<String, String> parameter : this.params.entrySet()) {\n'
       '\t\t\t\tif (query.length() > 0)\n'
       '\t\t\t\t\tquery.append("&");\n'
       '\t\t\t\tquery.append(parameter.getKey()).append("=").append(parameter.getValue());\n'
       '\t\t\t}\n'
       '\t\t\tif (query.length() > 0)\n'
       '\t\t\t\tresultUrl = "?" + query.toString();\n'
       '\t\t}')
assert old in t, "trecho esperado ausente na base do ensaio"
p.write_text(t.replace(old, new))
print("exec-a1: edicao simulada aplicada em AcaoVO.java")
