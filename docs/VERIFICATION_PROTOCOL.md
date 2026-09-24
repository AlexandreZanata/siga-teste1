# Protocolo de Verificação — anti-falso-positivo (v0.1)

> Limite metodológico: releitura, hash e nome na linha verificam localização e integridade; não provam resolução semântica nem ausência universal de falsos positivos. Valores de `confidence` abaixo são rótulos históricos, não probabilidades calibradas. Complementar este protocolo com a auditoria e os critérios do [plano vigente](../plans/PESQUISA_CONTEXTO_MODULAR.md). Após edições locais, verificar também hashes da árvore efetiva, pois o SHA base não representa sozinho o código alterado.

Toda afirmação estrutural passa por 4 portões, executados pelo agente responsável **antes** de qualquer commit:

1. **Ler bytes reais:** `path.read_bytes()` no dataset pinado (`e3be22828`). Proibido afirmar símbolo sem abrir o arquivo.
2. **Evidência `arquivo:linha@SHA`:** cada símbolo carrega `file + line + content_hash(sha256)`.
3. **Re-verificação independente:** `archatlas/verify.py::verify_symbol` re-lê o disco e exige: arquivo existe + hash idêntico + linha no intervalo + `nome ∈ texto da linha`. Falha em qualquer item = descarte + log, nunca correção silenciosa.
4. **Classes de confidence:** `1.0 ast-regex-exact` (declaração de tipo na linha) / `0.9 candidate` (método com nome literal na linha) / `unresolved` (sem evidência — registrado, nunca emitido como fato).

**Proibido:** resumir sem citar, inferir caller sem aresta lida, afirmar teste sem abrir o teste, usar cache LLM como prova. Testes `test_extract.py` e `test_census.py` são a execução automatizada deste protocolo na F2/F1.
