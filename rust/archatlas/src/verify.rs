// SPDX-License-Identifier: Apache-2.0
//! `verify --ref <arquivo:linha[@hash]>` — releitura e conferência de uma citação.
//!
//! É o portão 3 do `docs/VERIFICATION_PROTOCOL.md` transformado em comando: a citação só é
//! considerada boa se o arquivo existir dentro da raiz, o hash bater com o registrado no
//! índice e a linha existir no arquivo. Falha em qualquer item produz código 5, nunca um
//! `ok` otimista.
//!
//! Limite declarado: isto verifica **localização e integridade**. Não prova resolução
//! semântica nem ausência de falso positivo — o mesmo limite que o protocolo já registra.

use crate::pack::{settle_budget, BudgetInfo, Omitted, PackError, SnapshotInfo, Unit};
use crate::snapshot::{read_text, resolve_within, sha256_bytes};
use crate::store::{self, Store};
use crate::SCHEMA_VERSION;
use serde::Serialize;
use std::path::Path;

/// Referência já decomposta.
#[derive(Debug, Clone)]
pub struct ParsedRef {
    pub file: String,
    pub line: u32,
    pub hash: Option<String>,
}

/// Decompõe `arquivo:linha[@hash]`.
///
/// A quebra é feita da direita para a esquerda porque o hash pode conter `:` no prefixo
/// (`sha256:`), e o arquivo é quem tem a última ocorrência de `:` antes dele.
pub fn parse_ref(spec: &str) -> Result<ParsedRef, String> {
    let spec = spec.trim();
    if spec.is_empty() {
        return Err("--ref vazio".into());
    }
    let (left, hash) = match spec.rsplit_once('@') {
        Some((l, h)) if !h.is_empty() => (l, Some(normalize_hash(h))),
        Some((l, _)) => (l, None),
        None => (spec, None),
    };
    let Some((file, line_str)) = left.rsplit_once(':') else {
        return Err(format!(
            "--ref sem linha: {spec}; esperado arquivo:linha[@hash]"
        ));
    };
    if file.trim().is_empty() {
        return Err(format!("--ref sem arquivo: {spec}"));
    }
    let line: u32 = line_str
        .trim()
        .parse()
        .map_err(|_| format!("--ref com linha invalida: {line_str}"))?;
    if line == 0 {
        return Err("--ref com linha 0; linhas comecam em 1".into());
    }
    Ok(ParsedRef {
        file: file.trim().to_string(),
        line,
        hash,
    })
}

/// Aceita `sha256:<hex>` e `<hex>`, e compara sempre em minúsculas.
fn normalize_hash(h: &str) -> String {
    h.trim().trim_start_matches("sha256:").to_ascii_lowercase()
}

/// Cada item é um fato medido, não um rótulo.
#[derive(Debug, Clone, Serialize)]
pub struct Checks {
    pub inside_root: bool,
    pub file_exists: bool,
    pub registered_in_index: bool,
    /// Sempre `null`: a forma documentada de `--ref` não carrega nome de símbolo, e
    /// inventar aqui violaria a regra de não afirmar o que não foi lido.
    pub name_on_line: Option<bool>,
    pub hash_matches_index: Option<bool>,
    pub hash_matches_arg: Option<bool>,
    pub line_in_range: Option<bool>,
    pub line_count: Option<u64>,
}

#[derive(Debug, Clone, Serialize)]
pub struct RefInfo {
    pub file: String,
    pub line: u32,
    pub hash: Option<String>,
}

/// Envelope de `verify`. Mesma forma do §5; `units` traz no máximo a linha citada.
#[derive(Debug, Clone, Serialize)]
pub struct VerifyResponse {
    pub schema: String,
    pub schema_version: u32,
    pub state: String,
    pub snapshot: SnapshotInfo,
    pub reference: RefInfo,
    pub checks: Checks,
    pub units: Vec<Unit>,
    pub budget: BudgetInfo,
    pub omitted: Omitted,
    pub hints: Vec<String>,
}

/// `true` quando todos os itens verificáveis passaram.
fn all_pass(c: &Checks) -> bool {
    c.inside_root
        && c.file_exists
        && c.registered_in_index
        && c.hash_matches_index != Some(false)
        && c.hash_matches_arg != Some(false)
        && c.line_in_range != Some(false)
}

/// Confere a referência contra o disco e o índice.
///
/// Devolve `(resposta, passou)` — o código de saída é decidido pelo chamador, mantendo este
/// módulo livre de `exit`.
pub fn check(
    repo: &Path,
    index_path: &Path,
    spec: &str,
) -> Result<(VerifyResponse, bool), PackError> {
    let parsed = parse_ref(spec).map_err(PackError::BadRequest)?;
    let snap = store::inspect(index_path, Some(repo));
    let empty_budget = |used_bytes: u64, used_tokens: u64| BudgetInfo {
        requested_tokens: 0,
        used_tokens,
        unit: "byte".to_string(),
        tokenizer_id: None,
        tokenizer_is_exact: false,
        max_bytes: 0,
        used_bytes,
    };
    let snapshot = SnapshotInfo {
        sha_base: snap.sha_base.clone(),
        index_generation: snap.generation.clone().unwrap_or_else(|| "unknown".into()),
        index_state: snap.state.as_str().to_string(),
    };

    // Caminho fora da raiz é violação de integridade, não "arquivo ausente".
    let abs = match resolve_within(repo, &parsed.file) {
        Ok(p) => p,
        Err(e) => {
            let mut resp = VerifyResponse {
                schema: "atlas-verify/1".into(),
                schema_version: SCHEMA_VERSION,
                state: "partial".into(),
                snapshot,
                reference: RefInfo {
                    file: parsed.file.clone(),
                    line: parsed.line,
                    hash: parsed.hash.clone(),
                },
                checks: Checks {
                    inside_root: false,
                    file_exists: false,
                    registered_in_index: false,
                    name_on_line: None,
                    hash_matches_index: None,
                    hash_matches_arg: None,
                    line_in_range: None,
                    line_count: None,
                },
                units: Vec::new(),
                budget: empty_budget(0, 0),
                omitted: Omitted {
                    n: 0,
                    reasons: vec!["outside_root".into()],
                },
                hints: vec![format!("referencia recusada: {e}")],
            };
            let _ = settle_budget(&mut resp, |r, b, t| {
                r.budget.used_bytes = b;
                r.budget.used_tokens = t;
            });
            return Ok((resp, false));
        }
    };

    // Relativo canônico, como o índice guarda.
    let rel = crate::snapshot::rel_path(repo, &abs).unwrap_or_else(|| parsed.file.clone());

    let store = Store::open_readonly(index_path)
        .map_err(|e| PackError::Io(format!("nao foi possivel abrir o indice: {e}")))?;
    let known: std::collections::HashMap<String, String> = store
        .logical_dump()
        .map_err(|e| PackError::Io(format!("falha ao ler o indice: {e}")))?
        .into_iter()
        .collect();

    let live = read_text(&abs);
    let (file_exists, line_count, live_hash, line_text) = match live {
        Ok(text) => {
            let lines: Vec<&str> = text.lines().collect();
            (
                true,
                Some(lines.len() as u64),
                Some(sha256_bytes(text.as_bytes())),
                lines.get(parsed.line as usize - 1).map(|s| s.to_string()),
            )
        }
        Err(_) => (false, None, None, None),
    };

    let registered = known.get(&rel).cloned();
    let hash_matches_index = match (&registered, &live_hash) {
        (Some(a), Some(b)) => Some(a == b),
        _ => None,
    };
    let hash_matches_arg = match (&parsed.hash, &live_hash) {
        (Some(a), Some(b)) => Some(a == b),
        _ => None,
    };
    let line_in_range = line_count.map(|n| (parsed.line as u64) <= n);

    let checks = Checks {
        inside_root: true,
        file_exists,
        registered_in_index: registered.is_some(),
        name_on_line: None,
        hash_matches_index,
        hash_matches_arg,
        line_in_range,
        line_count,
    };
    let pass = all_pass(&checks);

    let mut reasons: Vec<String> = Vec::new();
    if !file_exists {
        reasons.push("file_missing".into());
    }
    if registered.is_none() {
        reasons.push("not_indexed".into());
    }
    if hash_matches_index == Some(false) {
        reasons.push("stale_source".into());
    }
    if hash_matches_arg == Some(false) {
        reasons.push("hash_divergent".into());
    }
    if line_in_range == Some(false) {
        reasons.push("line_out_of_range".into());
    }

    // A linha citada volta como unidade única: verificar sem mostrar o que foi verificado
    // obrigaria o chamador a ler o arquivo de novo para conferir.
    let units = match (&line_text, pass) {
        (Some(t), true) => vec![Unit {
            file: rel.clone(),
            line: parsed.line,
            end_line: parsed.line,
            hash: format!("sha256:{}", live_hash.clone().unwrap_or_default()),
            kind: "excerpt".to_string(),
            evidence: "verify:hash+linha".to_string(),
            text: t.clone(),
            reason: "linha citada conferida no disco".to_string(),
            truncated: false,
        }],
        _ => Vec::new(),
    };

    let mut hints: Vec<String> = Vec::new();
    if hash_matches_index == Some(false) {
        hints.push("indice desatualizado para este arquivo; rode `archatlas index`".into());
    }
    if registered.is_none() {
        hints.push("arquivo nao esta no indice; indexe o repo ou use leitura direta".into());
    }
    if !reasons.is_empty() {
        hints.push("a citacao nao foi confirmada; nao use este trecho como fato".into());
    }

    let mut resp = VerifyResponse {
        schema: "atlas-verify/1".to_string(),
        schema_version: SCHEMA_VERSION,
        state: if pass { "ok" } else { "partial" }.to_string(),
        snapshot,
        reference: RefInfo {
            file: rel,
            line: parsed.line,
            hash: parsed.hash.clone(),
        },
        checks,
        units,
        budget: empty_budget(0, 0),
        omitted: Omitted {
            n: reasons.len() as u64,
            reasons,
        },
        hints,
    };
    let _ = settle_budget(&mut resp, |r, b, t| {
        r.budget.used_bytes = b;
        r.budget.used_tokens = t;
    });
    Ok((resp, pass))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn aceita_as_formas_documentadas() {
        let a = parse_ref("src/A.java:10").unwrap();
        assert_eq!(a.file, "src/A.java");
        assert_eq!(a.line, 10);
        assert!(a.hash.is_none());

        let b = parse_ref("src/A.java:10@sha256:ABCDEF").unwrap();
        assert_eq!(b.hash.as_deref(), Some("abcdef"), "hash normalizado");

        let c = parse_ref("src/A.java:10@abcdef").unwrap();
        assert_eq!(c.hash.as_deref(), Some("abcdef"));
    }

    #[test]
    fn recusa_formas_invalidas() {
        assert!(parse_ref("").is_err());
        assert!(parse_ref("sem_linha.java").is_err());
        assert!(parse_ref("a.java:0").is_err(), "linha 0 nao existe");
        assert!(parse_ref("a.java:abc").is_err());
        assert!(parse_ref(":5").is_err());
    }

    #[test]
    fn ultima_ocorrencia_de_dois_pontos_e_a_linha() {
        // O modo de falha que importa: `rsplit_once` da direita para a esquerda.
        let r = parse_ref("dir/sub/A.java:42").unwrap();
        assert_eq!(r.file, "dir/sub/A.java");
        assert_eq!(r.line, 42);
    }

    #[test]
    fn all_pass_exige_todos_os_itens() {
        let ok = Checks {
            inside_root: true,
            file_exists: true,
            registered_in_index: true,
            name_on_line: None,
            hash_matches_index: Some(true),
            hash_matches_arg: Some(true),
            line_in_range: Some(true),
            line_count: Some(10),
        };
        assert!(all_pass(&ok));

        let mut divergente = ok.clone();
        divergente.hash_matches_index = Some(false);
        assert!(!all_pass(&divergente), "hash divergente nao pode passar");

        let mut fora = ok.clone();
        fora.inside_root = false;
        assert!(!all_pass(&fora));
    }
}
