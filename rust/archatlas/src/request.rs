// SPDX-License-Identifier: Apache-2.0
//! Pedido JSON: parsing estrito e validação antes de tocar o índice.
//!
//! `deny_unknown_fields` implementa a regra do contrato §4 ("campo desconhecido no pedido →
//! código 2"). É deliberadamente rígido: um cliente que envia um campo que o servidor ignora
//! acredita que ele teve efeito, e isso invalida a medição do piloto.

use serde::Deserialize;
use std::collections::HashMap;

/// Política de empacotamento. Congelada em `CLI_CONTRACT/1` §4.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Policy {
    /// Busca lexical com empacotamento fixo: top-K por BM25, sem diversidade nem contexto.
    LexRs,
    /// Política de contexto: trechos diversos com contexto local verificável.
    CtxRs,
}

impl Policy {
    pub fn as_str(self) -> &'static str {
        match self {
            Policy::LexRs => "LEX-RS",
            Policy::CtxRs => "CTX-RS",
        }
    }

    fn parse(s: &str) -> Option<Policy> {
        match s {
            "LEX-RS" => Some(Policy::LexRs),
            "CTX-RS" => Some(Policy::CtxRs),
            _ => None,
        }
    }
}

/// Referência declarada pelo agente (`known_refs`) ou já entregue (`delivered_refs`).
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RefSpec {
    pub file: String,
    #[serde(default)]
    pub line: Option<u32>,
    #[serde(default)]
    pub hash: Option<String>,
}

/// Snapshot que o agente acredita estar consultando.
#[derive(Debug, Clone, Default, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RequestSnapshot {
    #[serde(default)]
    pub sha_base: Option<String>,
    #[serde(default)]
    pub tree_hashes: HashMap<String, String>,
}

/// Pedido de `context` (e, em R2, de `expand`).
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Request {
    pub schema_version: u32,
    pub intent: String,
    pub query: String,
    #[serde(default)]
    pub known_refs: Vec<RefSpec>,
    #[serde(default)]
    pub snapshot: RequestSnapshot,
    pub budget_tokens: u64,
    #[serde(default)]
    pub tokenizer_id: Option<String>,
    pub max_bytes: u64,
    pub policy: String,
    #[serde(default)]
    pub delivered_refs: Vec<RefSpec>,
}

/// Pedido já validado, com a política convertida.
#[derive(Debug, Clone)]
pub struct ValidRequest {
    pub raw: Request,
    pub policy: Policy,
}

/// Intenções aceitas. Congeladas no contrato §4; um valor novo é mudança de contrato.
const INTENTS: &[&str] = &["localizar", "editar", "testar", "impacto", "desconhecido"];

/// Faz o parsing e a validação semântica. A mensagem de erro vira stderr; o código é 2.
pub fn parse(raw: &str) -> Result<ValidRequest, String> {
    let req: Request = serde_json::from_str(raw).map_err(|e| {
        // A mensagem do serde já aponta o campo; não reescrevemos para não perder detalhe.
        format!("pedido invalido: {e}")
    })?;

    if req.schema_version != crate::SCHEMA_VERSION {
        return Err(format!(
            "schema_version {} desconhecida; esta versao aceita {}",
            req.schema_version,
            crate::SCHEMA_VERSION
        ));
    }
    if !INTENTS.contains(&req.intent.as_str()) {
        return Err(format!(
            "intent desconhecida: {}; esperado um de {}",
            req.intent,
            INTENTS.join("|")
        ));
    }
    let Some(policy) = Policy::parse(&req.policy) else {
        return Err(format!(
            "policy desconhecida: {}; esperado LEX-RS ou CTX-RS",
            req.policy
        ));
    };
    if req.budget_tokens == 0 {
        return Err("budget_tokens precisa ser inteiro positivo".into());
    }
    if req.max_bytes == 0 {
        return Err("max_bytes precisa ser inteiro positivo".into());
    }
    // Um pedido sem termo buscável e sem referência não tem o que recuperar. Recusar aqui
    // evita devolver `state: ok` com lista vazia, que é indistinguível de "não existe".
    if crate::retrieve::tokenize(&req.query).is_empty() && req.known_refs.is_empty() {
        return Err("query sem termo buscavel e sem known_refs".into());
    }

    Ok(ValidRequest { raw: req, policy })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn base() -> String {
        r#"{"schema_version":1,"intent":"localizar","query":"ExMovimentacao",
            "budget_tokens":2000,"max_bytes":20000,"policy":"CTX-RS"}"#
            .to_string()
    }

    #[test]
    fn aceita_pedido_minimo() {
        let v = parse(&base()).unwrap();
        assert_eq!(v.policy, Policy::CtxRs);
        assert!(v.raw.known_refs.is_empty());
    }

    #[test]
    fn recusa_campo_desconhecido() {
        let s = base().replace("\"policy\"", "\"policy_extra\":1,\"policy\"");
        assert!(parse(&s).is_err());
    }

    #[test]
    fn recusa_schema_versao_desconhecida() {
        assert!(parse(&base().replace("\"schema_version\":1", "\"schema_version\":2")).is_err());
    }

    #[test]
    fn recusa_intent_e_policy_desconhecidas() {
        assert!(parse(&base().replace("localizar", "adivinhar")).is_err());
        assert!(parse(&base().replace("CTX-RS", "AUTO")).is_err());
    }

    #[test]
    fn recusa_budget_zero() {
        assert!(parse(&base().replace("\"budget_tokens\":2000", "\"budget_tokens\":0")).is_err());
        assert!(parse(&base().replace("\"max_bytes\":20000", "\"max_bytes\":0")).is_err());
    }

    #[test]
    fn recusa_query_sem_termo_e_sem_refs() {
        assert!(parse(&base().replace("ExMovimentacao", "###")).is_err());
        // Com known_refs, a mesma query é aceita.
        let s = base().replace("ExMovimentacao", "###").replace(
            "\"policy\"",
            "\"known_refs\":[{\"file\":\"a.java\"}],\"policy\"",
        );
        assert!(parse(&s).is_ok());
    }

    #[test]
    fn recusa_json_malformado() {
        assert!(parse("{nao json").is_err());
    }

    #[test]
    fn aceita_snapshot_e_tokenizer_explicitos() {
        let s = base().replace(
            "\"policy\"",
            "\"snapshot\":{\"sha_base\":\"e3be22828\"},\"tokenizer_id\":\"x/1\",\"policy\"",
        );
        let v = parse(&s).unwrap();
        assert_eq!(v.raw.snapshot.sha_base.as_deref(), Some("e3be22828"));
        assert_eq!(v.raw.tokenizer_id.as_deref(), Some("x/1"));
    }
}
