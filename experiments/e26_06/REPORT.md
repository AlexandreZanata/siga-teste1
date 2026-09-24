# E26-06 integração mínima — checklist técnico (sem MCP, sem piloto humano)

Data: 2026-09-24. ID: E26-06 especificação + integração mínima (P4).
Código: `archatlas/doctor.py:1` (novo) + `archatlas/cli.py` (`doctor`/`context`;
`verify`/`index`/`find` preservados). MCP: não adicionado (só se necessário —
não demonstrado). Piloto humano e transferência: P6–P7 (fora desta etapa).
Estado: `concluida` como integração mínima; sem alegação de adoção.
Método: ambiente limpo em `/tmp` (2 arqs Java), sem rede/GPU/modelo.

## Checklist (ambiente limpo, valores reais)

| passo | resultado |
|---|---|
| instalar (2 arqs) | `{indexed: 2, skipped: 0, pruned: 0/0}` |
| consultar (`classe A metodo m`, 2k) | exit 0, `state ok`, 3 refs, `used 46`, `schema_overhead 86` |
| abrir evidência (ref 1) | `verify_symbol (True, 'ok')` (bytes reais + hash) |
| atualizar (touch 1) | `{indexed: 1, skipped: 1}` |
| índice incompatível (`user_version=99`) | exit 2, `state incompatible` + conselho |
| corrompido (lixo binário) | exit 2, `state corrupt` (doctor e context) |
| inexistente | exit 2, `state missing`, sem arquivo residual |
| linguagem | `java structural`; demais `lexical-fallback` declarado |
| desinstalar | só o dir do índice removido; `stable_hash` do código idêntico |
| legados | `verify`/`index`/`find` exit 0 (comportamento preservado) |

Auto-reparo honesto: `context` sem tabela lexical reconstrói e sinaliza
`lexical_healed: true` (não falha silenciosa nem resultado vazio).
Achado do checklist: `cli.py` original nem importava (`IndentationError` —
a CLI nunca executou neste checkout); corrigido nesta etapa (1 linha).

## Leitura e decisão

O ganho do seletor sobrevive à interface mínima: mesmo motor via CLI e saída
estruturada, com custo do schema contabilizado (86tk no exemplo) e estados
`ok/partial` explícitos. Sem MCP (sem necessidade demonstrada), sem piloto humano,
sem publicação experimental: capacidades (java estrutural, resto
lexical; sem LLM no retrieval), limitações (orçamentos 2k/8k diagnósticos; sem
histórico; sem holdout) e evidências acima delimitam o escopo testado.
Próximo: P6 (2+ repos externos) e P7 (devs, ordem contrabalanceada) — ambos pós-P5.
