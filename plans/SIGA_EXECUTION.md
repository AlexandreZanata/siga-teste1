# Entrada do agente A — continuar SIGA e manter o core

Leia primeiro [execução paralela](PARALLEL_EXECUTION.md). Seu trabalho é continuar a trilha SIGA existente, preservando artefatos e alterações em andamento, enquanto o agente B executa Bitcoin na própria worktree.

**Próxima sequência, 2026-09-29:** [CLI Rust R0–R6](RUST_CLI_PILOTO_REAL.md) e [protocolo do piloto](../research/rust/PROTOCOLO_VALIDACAO.md). A implementa uma fatia pequena do core Rust e o runner de medição, mantém Python como referência e prepara tarefas SIGA reais. Não reiniciar pesquisas antigas nem esperar grafo/port completo para chegar ao piloto. Ler status atual de B antes de preparar uma worktree que já existe.

## Sequência de retomada

1. Confirmar checkout, branch, diff atual e último commit. Não criar worktree, trocar branch ou descartar arquivos do trabalho SIGA em andamento para começar a nova organização.
2. Ler `research/AUDIT_BASELINE.md`, `research/PREREGISTRATION.md` e, se disponível no seu checkpoint, `research/CONTRACTS_P2.md`. Verificar evidências antes de determinar a primeira etapa pendente. P0/P1 já documentados não devem ser repetidos só porque o plano principal descreve sua sequência original.
3. Continuar [P0–P7](PESQUISA_CONTEXTO_MODULAR.md) e [E26-00–E26-06](EXPERIMENTOS_2026.md) no SIGA. Usar IDs `SIGA-Pn` e `SIGA-E26-nn` em novos registros; IDs antigos permanecem aliases históricos, sem renomear resultados.
4. Preparar checkpoint publicado da documentação para B iniciar BTC-P0. Se o core corrente ainda não estiver pronto, B pode usar o último core estável e registrar limites; não copiar arquivos não commitados.
5. Manter contratos comuns e atender pedidos em commits pequenos. Não assumir autoria ou conclusão do adaptador/benchmark Bitcoin; integração segue o protocolo.

## Área de escrita e evidências

Você é responsável pelo core comum, testes gerais e caminhos SIGA. O namespace `archatlas/bitcoin/**`, `tests/bitcoin/**`, `research/bitcoin/**`, `benchmarks/bitcoin/**`, `experiments/bitcoin/**` e `plans/bitcoin/**` pertence a B. Leia pedidos publicados, responda em `research/integration/**` e integre apenas em checkpoint acordado.

Manter documentos gerais existentes quando forem seu artefato de trabalho; novos logs de progresso ficam em `plans/siga/STATUS.md` e `research/siga/`. Não mover o pré-registro atual ou modificar gabaritos para encaixar Bitcoin. Na próxima emenda do pré-registro, explicitar que “só SIGA” define o escopo desse estudo, não uma proibição da trilha paralela.

Os aceites, custos, modelo efetivo e avaliação cega são por estudo. Pode continuar quando Bitcoin estiver bloqueado. Ao medir latência, respeitar reserva de recursos do host; fora da medição, desenvolvimento pode prosseguir em paralelo.

## Mensagem de entrada sugerida

> Continue a execução SIGA a partir do estado real deste checkout. Siga `plans/SIGA_EXECUTION.md` e `plans/PARALLEL_EXECUTION.md`, preserve trabalho em andamento e não reinicie etapas já comprovadas. Você mantém o core comum; Bitcoin pertence ao agente B em worktree separada. Publique contratos em checkpoints e mantenha medições, índices e logs separados. Não abra o holdout antes do pré-registro e do ambiente de avaliação estarem prontos.
