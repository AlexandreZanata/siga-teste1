# Estado da trilha Bitcoin

Dono durante execução: agente B. Track: `bitcoin`. Branch de escrita: `codex/bitcoin-context`.
`BASE_SHA`: `e6fde134f7da0d3616d90c40232d9ebe2ed9f033`. Método: mesmo P0–P7/E26-00–06 da trilha SIGA,
com dataset, tarefas, pré-registro e resultados próprios. Nenhum aceite copiado do SIGA.

## Checkpoint

- Etapa atual: **BTC-P1 concluída** (literatura aplicada + pré-registro preliminar próprio;
  sem adaptador, sem rodada, sem autorização de gasto).
- Último aceite e evidências: `research/bitcoin/LITERATURE_APPLICATION.md` (R26-01–R26-09,
  revisão congelada da base + aplicabilidade C++/Python como hipótese);
  `research/bitcoin/PREREGISTRATION.md` (preliminar, não selado; lacunas nulas explícitas);
  BTC-P0 segue em `research/bitcoin/AUDIT_BASELINE.md`, `benchmarks/bitcoin/PIN.md` (BTC_SHA pendente),
  `benchmarks/bitcoin/CENSO.md`, `research/bitcoin/WORKSPACE.md`.
- SHA publicado: `e46209b` (BTC-P0) em `origin/codex/bitcoin-context`; este commit BTC-P1 a registrar após push.
- `run_id`: nenhum (sem medição). Reserva de recursos: nenhuma ativa.
- Pedido ao core: nenhum (adaptação C++ pendente de BTC-P2; sem `BTC-CORE-NNN` ainda).
- Bloqueio exato: `BTC_SHA` indefinido (PIN) + teto/modelos/custodiante nulos (pré-registro §7);
  `main` avançou para `2b8a04f` (E26-01 SIGA: telemetria + artefatos `e26_01`) — observado, NÃO incorporado
  (execução SIGA, sem entrega de contrato ao B; nenhuma medição B em curso afetada).
- Alternativa independente: BTC-P2 pode especificar contratos e fixtures sem esperar PIN resolvido;
  sem PIN, porém, nenhuma indexação/benchmark é autorizada.
- Próximo comando/ação: resolver `BTC_SHA` (procedimento em `benchmarks/bitcoin/PIN.md`);
  depois especificar BTC-P2 (`CONTRACTS_P2.md`, adaptador, fixtures, E26-00 espelho).

## Etapas

- [x] BTC-P0 — auditoria, PIN e censo (auditoria concluída; PIN/CENSO como pendências explícitas bloqueando P2+).
- [x] BTC-P1 — aplicação da literatura e pré-registro próprio (preliminar, não selado; sem rodada autorizada).
- [ ] BTC-P2 — adaptador, ambiente e medição.
- [ ] BTC-P3 — piloto de edição.
- [ ] BTC-P4 — protótipo e ablações.
- [ ] BTC-P5 — confirmatório cego.
- [ ] BTC-P6 — portabilidade temporal e de ambiente Bitcoin.
- [ ] BTC-P7 — uso por desenvolvedor e checkpoint de integração.

Histórico de transições preservado aqui: 2026-09-24 BTC-P0 concluída (auditoria) com PIN/CENSO
pendentes; 2026-09-24 BTC-P1 concluída (literatura + pré-registro preliminar, lacunas nulas em §7).
Nenhuma fase posterior marcada. Experimentos BTC-E26-00–06: todos planejados, nenhum executado.
