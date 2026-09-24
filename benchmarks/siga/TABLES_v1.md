# TABLES v1-siga (geradas 2026-09-24, SHA e3be22828)

## T1 — accuracy/latência por método (100Qs, budget 2k)
| método | recall | média/query |
|---|---|---|
| lexical | 0.92 | 0.2ms |
| structural | 0.92 | 1.0ms |
| hybrid | 0.92 | 1.2ms |
| hybrid_refs | 1.00 | 14.3ms |
| router | 1.00 | 9.7ms |

## T2 — custo de contexto
| métrica | valor |
|---|---|
| cápsula média usada (2k budget) | 1191 tokens |
| full index 504 arqs | 0.92s |
| DB | 2512 KB |
| router p50/p95 | 26/332ms |
| incr-10 / incr-100 vs full | 0.03s / 0.23s |

## T3 — fidelidade
| escopo | arquivos | unresolved |
|---|---|---|
| siga-ex java | 504 | 0.002 (só package-info.java) |
| sigaex JSP | 597 | pages 597/597; includes 14 exatos, 965 unresolved declarados |

hashes: queries badac7d83488f784 capsule 2306d6546cb8ea9a
