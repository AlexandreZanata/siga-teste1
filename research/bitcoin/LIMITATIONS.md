# Limitações Bitcoin (consolidadas BTC-P0–P6; atualizar por etapa)

Data: 2026-09-24. Dono: agente B. Nenhum número abaixo é resultado em dataset real; todos os
experimentos BTC-E26 até aqui são sintéticos ou de plumbing. O que esta trilha NÃO afirma:

## Linguagem e semântica C++

- Sem parser C++: overloads, templates instanciados, chamadas virtuais, alvos de macro e
  resolução de headers NÃO são resolvidos (`btc-cpp-lex/1` é texto/includes; AUDIT A1).
- Pares header/impl e invalidação de dependentes são textuais (basename), não semânticos.
- Regex nunca prova vínculo; candidatos permanecem candidatos (`confidence` ≤ 0.6 no lexical).
- Python restrito a `ast` da stdlib; GUI (Qt) e outras linguagens sem suporte declarado.

## Build, ambiente e dados

- Sem `BTC_SHA`, sem snapshot, sem toolchain, sem `compile_commands.json`: nenhum índice do
  corpus, nenhum benchmark, nenhum piloto real executados. Diagnóstico de retrieval pode avançar
  sem build; piloto de patches, não.
- Testes funcionais exigirão regtest isolado; mainnet/fundos/nó de produção nunca fazem parte.
- `chars//4` é estimativa de diagnóstico; sem telemetria faturada, sem conclusão de economia.
- Stubs A/B dos dryruns têm qualidade NÃO interpretável; `C_btc` vale para fixtures até
  revalidação no corpus. Ensaio `btc-p5-rehearsal-001` é VOID para a rodada real.

## Método e escopo

- Bitcoin é desenvolvimento, não transferência: resultados não se agregam aos do SIGA nem
  provam generalização entre repositórios (exige projetos inéditos).
- Sem modelo resolvido, sem teto autorizado, sem custodiante, sem amostra dimensionada:
  nada autoriza rodada paga. Resultado negativo/inconclusivo continua saída válida.
