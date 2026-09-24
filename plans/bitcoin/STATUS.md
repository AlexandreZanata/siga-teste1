# Estado da trilha Bitcoin

Dono durante execução: agente B. Track: `bitcoin`. Branch de escrita: `codex/bitcoin-context`.
`BASE_SHA`: `e6fde134f7da0d3616d90c40232d9ebe2ed9f033`. Método: mesmo P0–P7/E26-00–06 da trilha SIGA,
com dataset, tarefas, pré-registro e resultados próprios. Nenhum aceite copiado do SIGA.

## Checkpoint

- Etapa atual: **BTC-P0 concluída** (auditoria + PIN/CENSO honestos; sem adaptador, sem rodada).
- Último aceite e evidências: `research/bitcoin/AUDIT_BASELINE.md` (A1–A7, `arquivo:linha@e6fde13`);
  `benchmarks/bitcoin/PIN.md` (BTC_SHA pendente); `benchmarks/bitcoin/CENSO.md` (dataset pendente);
  `research/bitcoin/WORKSPACE.md` (isolamento `codex/bitcoin-context` confirmado).
- SHA publicado: a registrar após push deste commit (branch `codex/bitcoin-context`).
- `run_id`: nenhum (sem medição). Reserva de recursos: nenhuma ativa.
- Pedido ao core: nenhum (bloqueios A1–A7 registrados como pendências BTC-P2, sem `BTC-CORE-NNN` ainda).
- Bloqueio exato: `BTC_SHA` indefinido (PIN) + checkpoint documental paralelo ainda não publicado
  em `main` (`DOCS_SHA` pendente; worktree baseada em `BASE_SHA` publicado, sem herdar não commitados).
- Alternativa independente: BTC-P1 pode referenciar R26-01–R26-09 publicados sem esperar o checkpoint;
  sem PIN, porém, nenhuma indexação/benchmark é autorizada.
- Próximo comando/ação: resolver `BTC_SHA` via `git ls-remote` + clone somente leitura
  (procedimento em `benchmarks/bitcoin/PIN.md`); depois abrir BTC-P1 com pré-registro próprio.

## Etapas

- [x] BTC-P0 — auditoria, PIN e censo (auditoria concluída; PIN/CENSO como pendências explícitas bloqueando P2+).
- [ ] BTC-P1 — aplicação da literatura e pré-registro próprio.
- [ ] BTC-P2 — adaptador, ambiente e medição.
- [ ] BTC-P3 — piloto de edição.
- [ ] BTC-P4 — protótipo e ablações.
- [ ] BTC-P5 — confirmatório cego.
- [ ] BTC-P6 — portabilidade temporal e de ambiente Bitcoin.
- [ ] BTC-P7 — uso por desenvolvedor e checkpoint de integração.

Histórico de transições preservado aqui: 2026-09-24 BTC-P0 concluída (auditoria) com PIN/CENSO
pendentes; nenhuma fase posterior marcada. Experimentos BTC-E26-00–06: todos planejados, nenhum executado.
