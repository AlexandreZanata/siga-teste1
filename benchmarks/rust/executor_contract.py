#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Contrato do executor externo — `atlas-executor/1` — e contabilidade do que ele declara.

O runner mede por fora o que consegue (parede, RSS, patch, eventos do shim). Tudo que só
existe dentro do executor — identidade do modelo, tokens, latência, erro/retry, custo
faturado — **não é observável por fora** e por isso tem de vir por contrato. Este módulo é
esse contrato, mais as três regras que impedem que ele vire ficção:

1. **Ausência não é zero.** Campo que o executor não informou sai `null` com motivo; nunca 0.
   `coverage` é obrigatório por métrica, e `observed: false` sem motivo é violação.
2. **Declarado nunca se mistura com observado.** O que o executor declara fica ao lado do que
   o runner viu — em campos diferentes — e é conferido contra o **próprio stream** dele. A
   conferência prova consistência interna, não veracidade: nenhum total declarado é tratado
   como medição externa.
3. **Identidade de modelo é verificável ou a tentativa não é evidência.** Nome informal não
   substitui `provider` + `id` + `version`; além disso o executor tem de registrar **como**
   verificou (`verified_by`). Faltando qualquer um, o resultado é violação, não "real".

Eventos do executor (JSONL, apensados no arquivo apontado por `ATLAS_EXECUTOR_TELEMETRY`,
o mesmo do shim, com `"source": "executor"`):

    {"kind": "model_call", "provider": ..., "model_id": ..., "model_version": ...,
     "request_id": ..., "status": "ok"|"error", "error_class": ...,
     "tokens": {"input": ..., "output": ..., "cache_read": ..., "cache_write": ...,
                "reasoning": ...}, "latency_ms": ..., "stop_reason": ...,
     "cost": {"amount": ..., "currency": ...}}
    {"kind": "tool_call", "tool": "shell"|"editor"|..., "argv": [...], "exit_code": ...,
     "stdout_bytes": ...}
    {"kind": "turn", "index": ...}
    {"kind": "retry", "of_request_id": ..., "error_class": ...}
    {"kind": "error", "error_class": ...}
    {"kind": "stop", "reason": ...}

`opened` e os nomes de ferramenta `atlas`/`atlas-read` são **reservados ao shim**: evento do
executor com eles é violação de contrato, não telemetria. Sem essa regra, um executor poderia
fabricar leitura sancionada e a única evidência de leitura do piloto viraria auto-relato.

No fim da tentativa o executor escreve o resumo em `ATLAS_EXECUTOR_RESULT`
(`atlas-executor-result/1`), que é **reconciliado** com o stream: divergência entre os dois é
violação, e métrica ausente num dos lados é `missing` — nunca arredondada para zero.
"""

from __future__ import annotations

import json
from pathlib import Path

CONTRACT_SCHEMA = "atlas-executor/1"
RESULT_SCHEMA = "atlas-executor-result/1"
STREAM_ENV = "ATLAS_EXECUTOR_TELEMETRY"
RESULT_ENV = "ATLAS_EXECUTOR_RESULT"

SHIM_SOURCE = "shim"
EXECUTOR_SOURCE = "executor"
UNATTRIBUTED = "unattributed"

# Só o shim escreve estes: `opened` é o evento de leitura sancionada e os dois nomes de
# ferramenta são os do leitor/envelope. Executor que os emite está fabricando evidência.
RESERVED_KINDS = ("opened",)
RESERVED_TOOLS = ("atlas", "atlas-read")

TOKEN_FIELDS = ("input", "output", "cache_read", "cache_write", "reasoning")
MODEL_IDENTITY_FIELDS = ("provider", "id", "version")
COVERAGE_METRICS = ("model_identity", "tokens", "cost", "tool_calls", "turns")

# Cada par liga o campo do stream (declarado evento a evento) ao total do result (declarado de
# uma vez). Os nomes são os do relatório; os caminhos são tuplas dentro de cada documento.
RECONCILE_FIELDS = (
    ("model_calls", ("model_calls",), ("usage", "model_calls")),
    ("input_tokens", ("tokens", "input"), ("usage", "input_tokens")),
    ("output_tokens", ("tokens", "output"), ("usage", "output_tokens")),
    ("cache_read_tokens", ("tokens", "cache_read"), ("usage", "cache_read_tokens")),
    ("cache_write_tokens", ("tokens", "cache_write"), ("usage", "cache_write_tokens")),
    ("tool_calls_declared", ("tool_calls_declared",), ("usage", "tool_calls_declared")),
    ("turns", ("turns",), ("usage", "turns")),
    ("error_count", ("errors", "count"), ("errors", "count")),
    ("retry_count", ("retries",), ("retries", "count")),
    ("provider_billed", ("cost", "amount"), ("cost", "provider_billed")),
)

EXTERNALLY_OBSERVED = (
    "parede (wall_s) e pico de RSS do processo externo",
    "eventos do shim: chamadas `atlas`, leituras sancionadas (`opened`) e bytes entregues",
    "patch do workspace e exit code do comando de aceite",
    "aplicacao do patch em base limpa e teste imutavel do avaliador",
)

DECLARED_BY_EXECUTOR = (
    "identidade do modelo (provider/id/version/verified_by)",
    "chamadas de modelo, tokens, latencia, erro e retry",
    "chamadas de ferramenta que nao passam pelo shim (shell, editor, outros)",
    "turnos do modelo, motivo de parada e custo faturado",
)


def _nonempty(value) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _num(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _dig(doc: dict, path: tuple[str, ...]):
    cur = doc
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    return cur


def classify(ev: dict) -> tuple[str, str | None]:
    """Separa evento do shim, do executor e sem origem. Devolve (origem, violação)."""
    source = ev.get("source")
    kind = ev.get("kind")
    tool = ev.get("tool")
    if source == SHIM_SOURCE:
        return SHIM_SOURCE, None
    if source == EXECUTOR_SOURCE:
        if kind in RESERVED_KINDS:
            return EXECUTOR_SOURCE, f"reserved_kind:{kind} (so o shim emite)"
        if tool in RESERVED_TOOLS:
            return EXECUTOR_SOURCE, f"impersonated_tool:{tool} (so o shim emite)"
        return EXECUTOR_SOURCE, None
    # Sem `source` nao ha como saber quem escreveu. Evento reservado nunca passa por
    # observacao; o resto e contado como declarado (conservador para o teto) e sinalizado.
    if kind in RESERVED_KINDS or tool in RESERVED_TOOLS:
        return UNATTRIBUTED, f"unattributed_reserved_kind:{kind or tool} (sem source: shim)"
    return UNATTRIBUTED, None


class StreamAccounting:
    """Agrega os eventos do executor. Nada aqui é observado por fora: é declaração."""

    def __init__(self) -> None:
        self.model_calls = 0
        self.calls_ok = 0
        self.calls_error = 0
        self.retries = 0
        self.errors = 0
        self.error_classes: dict[str, int] = {}
        self.tokens: dict[str, float] = {f: 0 for f in TOKEN_FIELDS}
        self._tokens_seen: set[str] = set()
        self.latency_sum = 0.0
        self.latency_max = 0.0
        self.latency_n = 0
        self.cost_amount = 0.0
        self.cost_currency: str | None = None
        self.cost_calls = 0
        self.cost_missing_calls = 0
        self.tool_calls_declared = 0
        self.tool_calls_by_tool: dict[str, int] = {}
        self.declared_delivered_bytes = 0
        self.turns = 0
        self.stop_reasons: dict[str, int] = {}
        self.stop_reason: str | None = None
        self.duplicate_request_ids = 0
        self.unattributed_events = 0
        self.events = 0
        self.violations: list[str] = []
        self._request_ids: set[str] = set()

    def absorb(self, ev: dict) -> str:
        """Absorve um evento e devolve a origem classificada (`shim`/`executor`/sem origem)."""
        if not isinstance(ev, dict):
            return UNATTRIBUTED
        source, violation = classify(ev)
        if violation:
            self.violations.append(violation)
            return source
        if source == SHIM_SOURCE:
            return source  # o shim tem contabilidade propria, observada, no runner

        self.events += 1
        if source == UNATTRIBUTED:
            self.unattributed_events += 1

        kind = ev.get("kind")
        if kind == "model_call":
            request_id = ev.get("request_id")
            if _nonempty(request_id):
                if request_id in self._request_ids:
                    # Mesma chamada emitida duas vezes: nao soma de novo. Sem isso, um stream
                    # com reemissao infla tokens e custo — a dupla cobranca que o aceite proibe.
                    self.duplicate_request_ids += 1
                    return source
                self._request_ids.add(request_id)
            self.model_calls += 1
            if ev.get("status") == "error":
                self.calls_error += 1
                # Cada falha entra **uma vez**: chamada que falhou conta aqui, pela propria
                # chamada. O evento `error` e para falha que nao e chamada de modelo.
                self.errors += 1
                error_class = ev.get("error_class") or "sem_classe"
                self.error_classes[error_class] = self.error_classes.get(error_class, 0) + 1
            else:
                self.calls_ok += 1
            tokens = ev.get("tokens") or {}
            for field in TOKEN_FIELDS:
                value = tokens.get(field)
                if _num(value):
                    self.tokens[field] += value
                    self._tokens_seen.add(field)
            if _num(ev.get("latency_ms")):
                self.latency_sum += float(ev["latency_ms"])
                self.latency_max = max(self.latency_max, float(ev["latency_ms"]))
                self.latency_n += 1
            cost = ev.get("cost")
            if isinstance(cost, dict) and _num(cost.get("amount")):
                currency = cost.get("currency")
                if _nonempty(currency) and self.cost_currency and currency != self.cost_currency:
                    self.violations.append(f"mixed_currency:{self.cost_currency}->{currency}")
                elif _nonempty(currency):
                    self.cost_currency = currency
                self.cost_amount += float(cost["amount"])
                self.cost_calls += 1
            else:
                self.cost_missing_calls += 1
        elif kind == "tool_call":
            self.tool_calls_declared += 1
            tool = ev.get("tool") or "sem_nome"
            self.tool_calls_by_tool[tool] = self.tool_calls_by_tool.get(tool, 0) + 1
            if _num(ev.get("stdout_bytes")):
                self.declared_delivered_bytes += int(ev["stdout_bytes"])
        elif kind == "turn":
            self.turns += 1
        elif kind == "retry":
            self.retries += 1
        elif kind == "error":
            self.errors += 1
            self.error_classes[ev.get("error_class") or "sem_classe"] = \
                self.error_classes.get(ev.get("error_class") or "sem_classe", 0) + 1
        elif kind == "stop":
            if _nonempty(ev.get("reason")):
                self.stop_reason = ev["reason"]
                self.stop_reasons[ev["reason"]] = self.stop_reasons.get(ev["reason"], 0) + 1
        else:
            self.violations.append(f"unknown_kind:{kind!r}")
        return source

    def report(self) -> dict:
        """Relatório do stream declarado. Sem evento, o campo é `null` — nunca 0."""
        stream_seen = self.model_calls > 0
        tokens = {f: (self.tokens[f] if f in self._tokens_seen else None) for f in TOKEN_FIELDS}
        any_token = any(v is not None for v in tokens.values())
        return {
            "model_calls": self.model_calls if stream_seen else None,
            "calls_ok": self.calls_ok if stream_seen else None,
            "calls_error": self.calls_error if stream_seen else None,
            # Stream com chamada e nenhum evento de erro significa zero erro **no stream**; o
            # result reconcilia. Sem stream, nao ha observacao e o campo fica nulo.
            "errors": {"count": self.errors, "classes": self.error_classes} if stream_seen else None,
            "retries": self.retries if stream_seen else None,
            "tokens": tokens if any_token else None,
            "latency_ms": {"total": round(self.latency_sum, 1), "max": round(self.latency_max, 1),
                           "n": self.latency_n} if self.latency_n else None,
            "cost": {"amount": round(self.cost_amount, 8), "currency": self.cost_currency,
                     "calls_with_cost": self.cost_calls,
                     "calls_without_cost": self.cost_missing_calls} if self.cost_calls else None,
            # Stream sem nenhum evento nao declara zero chamada: nao ha observacao de ausencia.
            "tool_calls_declared": self.tool_calls_declared if self.events else None,
            "tool_calls_by_tool": dict(sorted(self.tool_calls_by_tool.items())),
            "declared_delivered_bytes": self.declared_delivered_bytes
            if self.tool_calls_declared else None,
            "executor_events": self.events,
            "turns": self.turns if self.turns or stream_seen else None,
            "stop": {"reason": self.stop_reason, "reasons": self.stop_reasons}
            if self.stop_reason else None,
            "duplicate_request_ids": self.duplicate_request_ids,
            "unattributed_events": self.unattributed_events,
            "violations": list(self.violations),
        }


def load_result(path: Path) -> tuple[dict | None, str | None]:
    """Lê o result contract. Devolve (documento, motivo) — um dos dois é sempre preenchido."""
    if not path.exists():
        return None, "executor nao escreveu o result contract no caminho informado"
    try:
        doc = json.loads(path.read_text())
    except Exception as exc:  # noqa: BLE001 - qualquer falha de leitura e violacao declarada
        return None, f"result contract ilegivel: {exc.__class__.__name__}: {exc}"
    if not isinstance(doc, dict):
        return None, "result contract nao e um objeto JSON"
    return doc, None


def validate_result(doc: dict) -> list[str]:
    """Violações do `atlas-executor-result/1`. Qualquer uma impede o rótulo `real`."""
    violations: list[str] = []
    if doc.get("schema") != RESULT_SCHEMA:
        violations.append(f"result_schema_inesperado:{doc.get('schema')!r}")
    model = doc.get("model")
    if not isinstance(model, dict):
        violations.append("model_identity_ausente")
    else:
        missing = [f for f in MODEL_IDENTITY_FIELDS if not _nonempty(model.get(f))]
        if missing:
            violations.append("model_identity_incompleta:" + ",".join(missing))
        if not _nonempty(model.get("verified_by")):
            violations.append("model_identity_sem_verified_by")
    usage = doc.get("usage")
    if not isinstance(usage, dict):
        violations.append("usage_ausente")
    else:
        for field in ("model_calls", "input_tokens", "output_tokens", "cache_read_tokens",
                      "cache_write_tokens", "tool_calls_declared", "turns"):
            value = usage.get(field)
            if value is not None and (not _num(value) or value < 0):
                violations.append(f"usage_invalido:{field}={value!r}")
    cost = doc.get("cost")
    if cost is not None:
        if not isinstance(cost, dict):
            violations.append("cost_nao_e_objeto")
        else:
            if not _num(cost.get("provider_billed")) or cost.get("provider_billed", -1) < 0:
                violations.append(f"cost_invalido:provider_billed={cost.get('provider_billed')!r}")
            if not _nonempty(cost.get("currency")):
                violations.append("cost_sem_currency")
            if not _nonempty(cost.get("source")):
                violations.append("cost_sem_source")
    stop = doc.get("stop")
    if not isinstance(stop, dict) or not _nonempty(stop.get("reason")):
        violations.append("stop_sem_reason")
    coverage = doc.get("coverage")
    if not isinstance(coverage, dict):
        violations.append("coverage_ausente")
    else:
        for metric in COVERAGE_METRICS:
            entry = coverage.get(metric)
            if not isinstance(entry, dict):
                violations.append(f"coverage_ausente:{metric}")
                continue
            if "observed" not in entry:
                violations.append(f"coverage_sem_observed:{metric}")
            elif entry["observed"] is False and not _nonempty(entry.get("reason")):
                # Ausencia de cobertura sem motivo escrito e o que o aceite proibe: nao da para
                # distinguir "nao observado" de "observado e omitido".
                violations.append(f"coverage_sem_motivo:{metric}")
    return violations


def _compare(stream_value, result_value) -> str:
    if stream_value is None and result_value is None:
        return "missing"
    if stream_value is None:
        return "missing_stream"
    if result_value is None:
        return "missing_result"
    if _num(stream_value) and _num(result_value):
        return "match" if abs(float(stream_value) - float(result_value)) < 1e-6 else "mismatch"
    return "match" if stream_value == result_value else "mismatch"


def reconcile(stream_report: dict, result: dict | None) -> list[dict]:
    """Confronta stream declarado e resumo declarado. Divergência é violação; falta é falta."""
    rows: list[dict] = []
    for name, stream_path, result_path in RECONCILE_FIELDS:
        stream_value = _dig(stream_report, stream_path) if len(stream_path) > 1 \
            else stream_report.get(stream_path[0])
        result_value = _dig(result, result_path) if result is not None else None
        state = _compare(stream_value, result_value)
        rows.append({"metric": name, "stream": stream_value, "result": result_value,
                     "state": state})
    return rows


def reconcile_violations(rows: list[dict]) -> list[str]:
    return [f"reconciliacao_divergente:{r['metric']} "
            f"(stream={r['stream']!r} result={r['result']!r})"
            for r in rows if r["state"] == "mismatch"]


def coverage_report(result: dict | None, stream_report: dict, violations: list[str]) -> dict:
    """Cobertura **por métrica**, derivada do que existe — não do que se gostaria que existisse."""
    model = (result or {}).get("model") or {}
    identity_ok = (all(_nonempty(model.get(f)) for f in MODEL_IDENTITY_FIELDS)
                   and _nonempty(model.get("verified_by"))
                   and not any(v.startswith("model_identity") for v in violations))
    tokens = stream_report.get("tokens") or {}
    result_usage = (result or {}).get("usage") or {}
    token_sources = [k for k, v in tokens.items() if v is not None]
    result_tokens = [k for k in ("input_tokens", "output_tokens") if result_usage.get(k) is not None]
    unattributed = stream_report.get("unattributed_events") or 0
    cost_stream = stream_report.get("cost") or {}
    cost_result = (result or {}).get("cost") or {}
    return {
        "model_identity": {
            "observed": identity_ok,
            "source": "result:model" if identity_ok else "ausente",
            "reason": None if identity_ok else
                      ("identidade declarada pelo executor sem provider/id/version/verified_by "
                       "verificaveis" if result else "executor nao entregou result contract"),
        },
        "tokens": {
            "observed": bool(token_sources or result_tokens),
            "source": "stream:model_call" if token_sources else
                      ("result:usage" if result_tokens else "ausente"),
            "reason": None if (token_sources or result_tokens) else
                      "nenhuma chamada de modelo com tokens observada no stream nem no result",
        },
        "cost": {
            "observed": bool(cost_stream or _num(cost_result.get("provider_billed"))),
            "source": "stream:model_call" if cost_stream else
                      ("result:cost" if _num(cost_result.get("provider_billed")) else "ausente"),
            "reason": None if (cost_stream or _num(cost_result.get("provider_billed"))) else
                      "sem custo faturado: nenhuma tarifa observada (P2 pendente nao autoriza "
                      "inventar preco)",
        },
        "tool_calls": {
            "observed": unattributed == 0,
            "source": "stream:tool_call (shim + executor)",
            "reason": None if unattributed == 0 else
                      f"{unattributed} evento(s) sem `source`: a contagem de chamadas pode estar "
                      "incompleta",
        },
        "turns": {
            "observed": stream_report.get("turns") is not None,
            "source": "stream:turn" if stream_report.get("turns") is not None else "ausente",
            "reason": None if stream_report.get("turns") is not None else
                      "executor nao emitiu evento de turno; teto de turnos nao fiscalizavel",
        },
    }


def _claim(name: str, supported: bool, reason: str, requires: tuple[str, ...]) -> dict:
    return {"claim": name, "supported": bool(supported), "reason": reason,
            "requires": list(requires)}


def capability_manifest(run_id: str, condition: str, evidence_class: str, contract_state: str,
                        coverage: dict, usage: dict, cost: dict, patch_info: dict,
                        gold_isolation: dict) -> dict:
    """Manifesto de capacidade: o que esta tentativa **pode** afirmar, e o que não pode."""
    by_metric = {name: coverage.get(name, {}) for name in COVERAGE_METRICS}
    cost_supported = bool(by_metric["cost"].get("observed")) and cost.get("provider_billed") is not None
    tokens_supported = bool(by_metric["tokens"].get("observed"))
    calls_supported = bool(by_metric["tool_calls"].get("observed"))
    turns_supported = bool(by_metric["turns"].get("observed"))
    claims = [
        _claim("custo_faturado_do_provedor", cost_supported,
               "custo faturado declarado pelo executor e conferido contra o proprio stream; "
               "nenhum total de provedor e medido por fora" if cost_supported else
               f"nao sustentado: {by_metric['cost'].get('reason')}",
               ("contract.coverage.cost", "result.cost.source")),
        _claim("tokens_do_modelo", tokens_supported,
               "tokens declarados por chamada e reconciliados com o result" if tokens_supported
               else f"nao sustentado: {by_metric['tokens'].get('reason')}",
               ("contract.coverage.tokens",)),
        _claim("contagem_de_chamadas_de_ferramenta_em_todas_as_ferramentas", calls_supported,
               "shim observa `atlas`/`atlas-read`; o executor declara as demais (shell, editor) e "
               "ambas entram no teto e no total" if calls_supported else
               f"nao sustentado: {by_metric['tool_calls'].get('reason')}",
               ("contract.coverage.tool_calls", "stream executado com `source` em todo evento")),
        _claim("turnos_do_modelo", turns_supported,
               "turnos vem de evento do executor e alimentam o teto" if turns_supported else
               f"nao sustentado: {by_metric['turns'].get('reason')}",
               ("contract.coverage.turns",)),
        _claim("teto_de_parede_aplicado", True,
               "parede medida por fora, com kill do grupo de processos no primeiro estouro",
               ("processo externo",)),
        _claim("teto_de_chamadas_aplicado", calls_supported,
               "teto conta eventos do shim e chamadas declaradas pelo executor" if calls_supported
               else f"nao sustentado: {by_metric['tool_calls'].get('reason')}",
               ("contract.coverage.tool_calls",)),
        _claim("patch_do_executor_capturado", True,
               f"diff do workspace capturado ({patch_info.get('bytes')} bytes, "
               f"vazio={patch_info.get('empty')})",
               ("workspace git",)),
        _claim("reducao_de_leituras_totais_do_agente", False,
               "nao sustentado pelo instrumento: `opened`/`delivered` contam so o leitor "
               "sancionado; leitura por `cat`, editor ou `git show` nao produz evento. Medir "
               "total de leitura exigiria sandbox de IO, nao shim em PATH",
               ("sandbox de IO", "ou declaracao do executor sobre cada leitura")),
        _claim("isolamento_do_ouro", False,
               f"nao sustentado: nivel `{gold_isolation.get('level')}`; mesmo usuario, mesmo "
               ".git e sem container. R5 exige ambiente inacessivel, nao checagem por caminho",
               ("container/usuario separado", "custodiante do holdout")),
        _claim("custo_por_sucesso", False,
               "decidido no avaliador cego (aceite por tarefa), nunca no runner; sem aceite e "
               "custo faturado o valor e indefinido, nao zero",
               ("avaliacao cega", "custo faturado")),
    ]
    return {
        "schema": "atlas-executor-capacity/1",
        "run_id": run_id,
        "condition": condition,
        "evidence_class": evidence_class,
        "contract_state": contract_state,
        "externally_observed": list(EXTERNALLY_OBSERVED),
        "declared_by_executor": list(DECLARED_BY_EXECUTOR),
        "trust_note": ("totais declarados sao conferidos apenas contra o proprio stream do "
                       "executor: consistencia interna nao e verificacao externa"),
        "metrics": [{"metric": name, **by_metric[name]} for name in COVERAGE_METRICS
                    if name in by_metric],
        "usage": usage,
        "claims": claims,
        "not_covered": [
            "leituras fora do leitor sancionado (sem evento, nao estimadas)",
            "turnos/chamadas de ferramenta internos ao processo do modelo que o executor "
            "nao emita como evento",
            "custo faturado sem tarifa oficial do provedor (P2)",
            "qualidade do patch e aceite humano (avaliacao cega, fora do runner)",
        ],
    }


def _provider_event(provider: str, model_id, model_version, request_id, status: str,
                    error_class, stop_reason, tokens: dict, latency_ms, cost, extra: dict,
                    cost_reason: str | None) -> dict:
    """Evento comum aos adaptadores. Nada e inventado: o que o provedor não devolveu fica nulo."""
    event = {
        "kind": "model_call",
        "source": EXECUTOR_SOURCE,
        "provider": provider,
        "model_id": model_id,
        "model_version": model_version,
        "model_version_reason": None if model_version else
                                "o provedor nao devolve a versao do modelo no corpo da resposta; "
                                "o chamador tem de registra-la e verifica-la",
        "request_id": request_id,
        "status": status,
        "error_class": error_class,
        "stop_reason": stop_reason,
        "tokens": tokens,
        "latency_ms": latency_ms,
        "latency_reason": None if latency_ms is not None else
                          "latencia nao medida pelo chamador; nao e derivada do corpo da resposta",
        "cost": cost,
        "cost_reason": None if cost else (cost_reason or
                                          "custo faturado nao acompanha a resposta do provedor; "
                                          "vem de fonte oficial de cobranca"),
    }
    event.update(extra)
    return event


def normalize_openai_chat_completion(raw: dict, *, provider: str, latency_ms=None,
                                     request_id=None, cost=None, cost_reason=None,
                                     model_version=None) -> dict:
    """Resposta de `/v1/chat/completions` (e compatíveis) → evento `model_call`.

    `system_fingerprint` é registrado como impressão do backend, **não** como versão: chamar
    aquilo de versão do modelo seria declarar mais do que a resposta sustenta.
    """
    usage = raw.get("usage") or {}
    prompt_details = usage.get("prompt_tokens_details") or {}
    completion_details = usage.get("completion_tokens_details") or {}
    tokens = {
        "input": usage.get("prompt_tokens"),
        "output": usage.get("completion_tokens"),
        "cache_read": prompt_details.get("cached_tokens"),
        # A API nao expoe escrita de cache nesta rota: ausente, nao zero.
        "cache_write": None,
        "reasoning": completion_details.get("reasoning_tokens"),
    }
    choices = raw.get("choices") or []
    finish = choices[0].get("finish_reason") if choices and isinstance(choices[0], dict) else None
    error = raw.get("error") or {}
    return _provider_event(
        provider, raw.get("model"), model_version, request_id or raw.get("id"),
        "error" if error else "ok",
        error.get("type") or error.get("code") if error else None,
        finish, tokens, latency_ms, cost,
        {"backend_fingerprint": raw.get("system_fingerprint")}, cost_reason)


def normalize_anthropic_message(raw: dict, *, provider: str = "anthropic", latency_ms=None,
                                request_id=None, cost=None, cost_reason=None,
                                model_version=None) -> dict:
    """`/v1/messages` da Anthropic → evento `model_call`."""
    usage = raw.get("usage") or {}
    tokens = {
        "input": usage.get("input_tokens"),
        "output": usage.get("output_tokens"),
        "cache_read": usage.get("cache_read_input_tokens"),
        "cache_write": usage.get("cache_creation_input_tokens"),
        "reasoning": None,  # a rota nao separa tokens de raciocinio
    }
    error = raw.get("error") or {}
    return _provider_event(
        provider, raw.get("model"), model_version, request_id or raw.get("id"),
        "error" if (error or raw.get("type") == "error") else "ok",
        error.get("type") if error else None,
        raw.get("stop_reason"), tokens, latency_ms, cost,
        {"stop_sequence": raw.get("stop_sequence")}, cost_reason)
