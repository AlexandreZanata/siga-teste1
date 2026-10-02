# Candidatos de tarefas reais

Curadoria de 2026-09-30. Execução e donos em [próximas tarefas](../../../plans/PROXIMAS_TASKS_SIGA_BITCOIN.md).

- `siga.dev.json`: oito requisitos verificados nas fontes SIGA.
- `bitcoin.dev.json`: oito requisitos verificados nas fontes Bitcoin Core no PIN.
- `evidence/2026-09-30-public-probes.json`: reproduções públicas de três tarefas, sem soluções.

O schema `atlas-task-candidates/1` não é aceito por `runner.py` ou `eval.py`. Os arquivos são cartões de curadoria, **não conjuntos executáveis ou selados**. Cada registro distingue requisito proposto de defeito reproduzido e indica preparo de ambiente/aceite pendente. A localização das fontes e seus hashes em `curator_only` ajudam o preparador; excluir esse campo da projeção enviada ao agente.

Para promover um candidato: confirmar snapshot/hash; executar baseline; criar aceites independentes na custódia; demonstrar falha na base e sucesso em referência; comprovar regressões; definir comando de aceite existente, timeout, caminhos permitidos/imutáveis, contaminação e isolamento. Só então exportar `atlas-tasks/2` no namespace da trilha e executar `python benchmarks/rust/eval.py validate --tasks <conjunto>`. Validade do JSON não comprova prontidão científica.

Não usar estes candidatos como holdout. Conferir famílias antes de escolher piloto após ajuste no smoke. O piloto previsto continua com 16 tarefas por trilha: os quatro candidatos de piloto aqui são uma primeira leva, sujeita a substituições. Não chamar oito tarefas por trilha de piloto completo.

A publica este material comum. B o adota por checkpoint e mantém a preparação/execução Bitcoin em seus próprios namespaces e worktree, conforme o protocolo paralelo.
