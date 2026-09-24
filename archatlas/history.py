# SPDX-License-Identifier: Apache-2.0
"""P4/E26-05: políticas de contexto acumulado (replay offline; trajetórias vivas N/A).

Três políticas sobre a MESMA lista de mensagens (sem LLM, sem reescrita):
- KEEP: nada remove (custo cheio; pode estourar — registrado, não escondido).
- DROP-OLD: remoção mecânica de observações antigas (mantém `system` + últimas N).
- CLIFF: ao atingir o limiar, preserva trechos LITERAIS (headverbatim + tail
  verbatim, meio vira marcador com contagens originais); nova compactação
  descarta a anterior e opera sobre o segmento original seguinte (inspirado em
  R26-02; adaptação, não reprodução do proxy).

Replay (`replay()`) valida: instruções verbatim, protocolo de tool calls
(pares call/response sem órfãos) e contagem exata de tokens (`chars//4`,
estimativa de diagnóstico). Trajetórias vivas, resumo por LLM, estágios,
16k/32k e cache cobrado exigem controle do histórico do cliente — indisponível
offline: marcado N/A, ferramenta de recuperação segue utilizável (limite da ficha).
"""
from __future__ import annotations

INSTRUCTIONS_ROLE = "system"


def tokens(text: str) -> int:
    return max(1, len(text) // 4)


def msg_tokens(m: dict) -> int:
    return tokens(m.get("content", "")) + (4 if m.get("tool_call") or m.get("tool_response") else 0)


def total_tokens(msgs: list[dict]) -> int:
    return sum(msg_tokens(m) for m in msgs)


def _units(non_sys: list[dict]) -> list[list[dict]]:
    """Agrupa pares call/response (atômicos) + avulsos, em ordem. Determinístico."""
    units, i = [], 0
    while i < len(non_sys):
        m = non_sys[i]
        if m.get("tool_call") and i + 1 < len(non_sys) and \
                non_sys[i + 1].get("tool_response") and \
                non_sys[i + 1].get("call_id") == m.get("call_id"):
            units.append([m, non_sys[i + 1]])
            i += 2
        else:
            units.append([m])
            i += 1
    return units


def _take_tail(units: list[list[dict]], n_msgs: int) -> list[dict]:
    out = []
    for u in reversed(units):
        out = u + out
        if len(out) >= n_msgs:
            break
    return out


def _take_head(units: list[list[dict]], n_msgs: int) -> list[dict]:
    out = []
    for u in units:
        out += u
        if len(out) >= n_msgs:
            break
    return out


def keep(msgs: list[dict], budget: int) -> dict:
    """Política atual: nada remove; estouro reportado."""
    return {"effective": list(msgs), "dropped": 0, "markers": [],
            "overflow": total_tokens(msgs) > budget, "policy": "KEEP"}


def drop_old(msgs: list[dict], budget: int, window: int = 10) -> dict:
    """Remoção mecânica: `system` + últimas N mensagens, com pares atômicos."""
    head = [m for m in msgs if m.get("role") == INSTRUCTIONS_ROLE]
    tail = _take_tail(_units([m for m in msgs if m.get("role") != INSTRUCTIONS_ROLE]), window)
    dropped = len(msgs) - len(head) - len(tail)
    eff = head + tail
    return {"effective": eff, "dropped": max(0, dropped), "markers": [],
            "overflow": total_tokens(eff) > budget, "policy": "DROP-OLD"}


def cliff(msgs: list[dict], budget: int, head_n: int = 8, tail_n: int = 10) -> dict:
    """Compactação literal no limiar: head+tail verbatim, meio vira marcador.

    Sem limiar atingido, equivale a KEEP (sem compactação prematura). Re-compactar
    descarta o marcador anterior e re-deriva do segmento original seguinte: o
    chamador re-executa sobre `original` com janela deslocada (puro; sem estado).
    """
    if total_tokens(msgs) <= budget:
        return {"effective": list(msgs), "dropped": 0, "markers": [],
                "overflow": False, "policy": "CLIFF"}
    non_sys = [m for m in msgs if m.get("role") != INSTRUCTIONS_ROLE]
    sys = [m for m in msgs if m.get("role") == INSTRUCTIONS_ROLE]
    units = _units(non_sys)
    head, tail = _take_head(units, head_n), _take_tail(units, tail_n)
    kept_ids = {id(m) for m in head + tail}
    mid = [m for m in non_sys if id(m) not in kept_ids]
    mid_tk = sum(msg_tokens(m) for m in mid)
    marker = {"role": "marker", "content":
              f"[compact:{len(mid)}msgs/{mid_tk}tk literais omitidos; reabrir fonte se preciso]",
              "dropped_refs": len(mid)}
    eff = sys + head + [marker] + tail
    return {"effective": eff, "dropped": len(mid), "markers": [marker["content"]],
            "overflow": total_tokens(eff) > budget, "policy": "CLIFF"}


def replay(effective: list[dict]) -> dict:
    """Verifica o log reproduzido: instruções, protocolo tool, contagem."""
    sys = [m["content"] for m in effective if m.get("role") == INSTRUCTIONS_ROLE]
    calls = [m.get("call_id") for m in effective if m.get("tool_call")]
    resps = [m.get("call_id") for m in effective if m.get("tool_response")]
    orphans = [c for c in resps if c not in calls] + \
              [c for c in calls if c not in resps and c is not None]
    return {"instructions_n": len(sys), "instructions_verbatim": list(sys),
            "tool_calls": len(calls), "orphans": orphans,
            "protocol_intact": not orphans, "total_tokens": total_tokens(effective)}
