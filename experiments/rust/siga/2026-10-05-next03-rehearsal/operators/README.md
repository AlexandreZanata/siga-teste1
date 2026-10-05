# Operadores sintéticos do ensaio NEXT-03

Estes scripts **simulam saídas de executor** para ensaiar o pipeline
(isolamento → tentativa → aceite público → gate privado → bundle cego →
adjudicação). Eles **não** são modelo, não chamam provedor e não constituem
evidência de capacidade: existem para que a primeira rodada real encontre o
caminho já percorrido, não para provar que algum agente resolve tarefas.

- `exec-a1.py`: aplica na workspace a correção da tarefa 17 (query canônica).
  Saída simulada **correta** → esperado: público verde + privado verde.
- `exec-a2.py`: aplica na workspace `return temp.toLowerCase()` em
  `removeAcentoHTML` (tarefa 20). Saída simulada **parcialmente correta** →
  esperado: público verde + privado vermelho (o gate que o ensaio demonstra).
- `exec-a3.py`: não edita nada (tarefa 19). Saída simulada **vazia** →
  esperado: `rejected` por patch vazio, com resultado final persistido.

Cada operador roda confinado (`sandbox.py`, rede isolada), com prova de acesso
negado antes de executar. Nenhum deles lê referência, custódia ou outro caso.
