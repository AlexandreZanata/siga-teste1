# ArchAtlas — Deterministic Structural Memory for Repository-Scale LLM Agents

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](pyproject.toml)

Memória estrutural externa, determinística, compacta, incremental e navegável de grandes repositórios. O LLM continua com contexto finito; o repositório fica fora do modelo; o agente recupera só a **Context Capsule** necessária.

> **Dataset base (read-only, fora deste repo):** `/home/iiii/PESSOAL-PROJETOS-ALEXANDRE/siga/` — branch `desenvolvimento`, GitLab `controladoria/siga`, SHA `e3be22828` (14 commits à frente do ponto anterior `48610bd65`, incorporados via `git pull --ff-only` em 2026-09-24). Java 21, Hibernate 6, EAP 8.1, 19 módulos Maven. **Nunca commitamos código do SIGA aqui** — só ponteiros (URL+SHA+path) + hashes + scripts. SIGA é AGPL-3.0.

## Estrutura (100% open source)
```
archatlas/        # código Apache-2.0 (core determinístico, stdlib-first)
benchmarks/siga/  # PIN.md + CENSO.md (ponteiros, sem blobs)
tests/            # pytest, tudo reproduzível em 1 comando
research/         # 15 docs de planejamento (01–15)
docs/             # protocolos operacionais (verificação, roadmap)
experiments/      # capsules por execução (hashes, sem outputs gigantes)
```

## Metodologia de ponta (resumo)
- **Trunk-based + fases curtíssimas**, cada fase = commit local + push (este README evolui por fase).
- **Zero falso positivo:** todo fato estrutural exige evidência `arquivo:linha@SHA` + `content_hash`; o que não for deterministicamente verificável é marcado `heuristic/unresolved`, nunca inventado. Agente verificador lê bytes reais do disco em cada etapa.
- **Reproduzível em 1 comando:** `python -m pytest -q` (sem rede, sem GPU, sem serviços).
- **Fonte da verdade:** código/AST/símbolos/Git — nunca LLM. Cache IA só marcado/regenerável.

## Roadmap por etapas (cada etapa = commit + push)
| Etapa | Entrega | Done |
|---|---|---|
| F0 | Bootstrap open-source (este commit) | LICENSE/README/CONTRIBUTING/CI/skeleton + push |
| F1 | PIN + CENSO verificados do `/siga/` | scripts + testes verdes + push |
| F2 `v0.1` | Extrator determinístico + protocolo verificação | pytest verde + tag `v0.1` + push |
| F3 | Índice SQLite + incremental + Query API mínima | `verify` hash-estável + push |
| F4 | Retrieval BM25 + Capsule sob budget + benchmark dev | curva 500–32k + push |
| F5+ | Bitcoin transfer (freeze, sem redesign) → paper | LIMITATIONS + push por etapa |

Ver `docs/ROADMAP_ETAPAS.md` (plano completo) e `docs/VERIFICATION_PROTOCOL.md` (anti-alucinação).

## Uso rápido
```bash
python -m pytest -q
python -m archatlas.cli verify --dataset /home/iiii/PESSOAL-PROJETOS-ALEXANDRE/siga
```
