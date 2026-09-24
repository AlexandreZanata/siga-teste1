# ArchAtlas — Deterministic Structural Memory for Repository-Scale LLM Agents

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](pyproject.toml)

Memória estrutural externa, determinística, compacta, incremental e navegável de grandes repositórios. O LLM continua com contexto finito; o repositório fica fora do modelo; o agente recupera só a **Context Capsule** necessária.

> **Dataset base (read-only, fora deste repo):** uma versão modificada do SIGA-Doc — branch `desenvolvimento`, SHA `e3be22828`, Java 21, Hibernate 6, 19 módulos Maven. **Nunca commitamos código do dataset aqui** — só ponteiros (SHA+path relativo) + hashes + scripts. O dataset original é AGPL-3.0.

## Estrutura (100% open source)
```
archatlas/        # código Apache-2.0 (core determinístico, stdlib-first)
benchmarks/siga/  # PIN.md + CENSO.md (ponteiros, sem blobs)
tests/            # pytest, tudo reproduzível em 1 comando
research/         # fundamentos, protocolos e base experimental de papers de 2026
docs/             # protocolos operacionais (verificação, roadmap)
experiments/      # capsules por execução (hashes, sem outputs gigantes)
```

## Metodologia de ponta (resumo)
- **Trunk-based + fases curtíssimas**, cada fase = commit local + push.
- **Zero falso positivo:** todo fato estrutural exige evidência `arquivo:linha@SHA` + `content_hash`; o que não for deterministicamente verificável é marcado `heuristic/unresolved`, nunca inventado.
- **Reproduzível em 1 comando:** `python -m pytest -q` (sem rede, sem GPU, sem serviços).
- **Fonte da verdade:** código/AST/símbolos/Git — nunca LLM. Cache IA só marcado/regenerável.
- **Sem dados pessoais:** nenhum path de máquina no código ou docs; GT usa paths relativos ao dataset.

## Roadmap por etapas (cada etapa = commit + push)
O [plano vigente de pesquisa para contexto modular](plans/PESQUISA_CONTEXTO_MODULAR.md) orienta as próximas etapas: auditoria das evidências, literatura primária, tarefas reais de edição, avaliação cega e transferência para outros projetos. Define contratos e critérios de ganho; sua inclusão é apenas planejamento, sem implementação ou experimentos novos.

A [base experimental de 2026](research/16_BASE_EXPERIMENTAL_2026.md) reúne nove papers, incluindo trabalhos de setembro. O [roteiro de experimentos e entrega para devs](plans/EXPERIMENTOS_2026.md) converte os métodos em testes de seleção de contexto, empacotamento, poda, histórico e uso real, com controles e critérios de decisão.

Ver também `docs/ROADMAP_ETAPAS.md` (histórico F0–F20 e ligação com F21) e `docs/VERIFICATION_PROTOCOL.md` (verificação de evidências). Resultados históricos de recuperação não comprovam, isoladamente, economia ou correção em tarefas de desenvolvimento.

## Uso rápido
```bash
export ARCHATLAS_DATASET=/caminho/para/siga-doc   # checkout read-only da versão modificada (SHA e3be22828)
python -m pytest -q
python -m archatlas.cli verify
```
Sem `ARCHATLAS_DATASET`, usa-se o vizinho `../siga` do checkout (quando existir).
