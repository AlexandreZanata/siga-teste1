# Fixtures do adaptador de provedor — sintéticas, não capturadas

Estes arquivos têm a **forma** das respostas documentadas de dois provedores para exercitar
`benchmarks/rust/executor_contract.py` sem rede, sem chave e sem modelo. Nenhuma chamada real
foi feita para produzi-los: são escritos à mão a partir do schema público, com nomes de modelo
deliberadamente fictícios (`modelo-ficticio-a`, `modelo-ficticio-b`) para que nada aqui pareça
uma medição de provedor.

O que a fixture **não** pode fornecer, e o adaptador se recusa a inventar:

- **versão do modelo** — nenhuma das duas rotas devolve a versão no corpo da resposta; o
  chamador tem de registrá-la e verificá-la (`model_version` e `verified_by` no result contract);
- **custo faturado** — não acompanha a resposta; vem de fonte oficial de cobrança;
- **latência** — é medida por quem faz a chamada, nunca derivada do corpo.

Quando P1 (modelo efetivo) for decidido e existirem respostas reais, estas fixtures devem ser
substituídas por capturas **sanitizadas** do provedor escolhido, mantendo o nome `*.synthetic`
apenas nos arquivos sintéticos. Trocar a fixture não muda o contrato: o adaptador só transporta
o que a resposta traz.

`/v1/chat/completions` (e compatíveis) → `normalize_openai_chat_completion`;
`/v1/messages` (Anthropic) → `normalize_anthropic_message`.
