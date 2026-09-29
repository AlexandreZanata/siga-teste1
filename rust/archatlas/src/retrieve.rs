// SPDX-License-Identifier: Apache-2.0
//! Recuperação lexical: tokenização determinística + BM25 do FTS5.
//!
//! A tokenização reproduz a da referência Python (`[A-Za-z0-9_]+`) para que a comparação
//! de R2 meça implementação e não gramática de consulta. Nenhum token é normalizado para
//! minúsculas: o tokenizer `porter` do FTS5 já faz case-folding, e mexer aqui criaria
//! divergência silenciosa entre os dois lados.

use anyhow::Result;
use rusqlite::{params, Connection};

/// Número de candidatos pedidos ao índice antes da seleção por política.
///
/// Generoso de propósito: a política escolhe depois, e um corte apertado aqui faria a
/// política parecer pior do que é. O custo é um `LIMIT` maior na consulta, nada mais.
pub const CANDIDATE_LIMIT: usize = 200;

/// Um arquivo candidato, ordenado por relevância (melhor primeiro).
#[derive(Debug, Clone)]
pub struct Hit {
    pub path: String,
    /// `bm25()` do FTS5: mais negativo = melhor.
    pub score: f64,
}

/// Extrai tokens `[A-Za-z0-9_]+`, preservando a ordem e removendo repetições.
pub fn tokenize(query: &str) -> Vec<String> {
    let mut out: Vec<String> = Vec::new();
    let mut cur = String::new();
    for ch in query.chars() {
        if ch.is_ascii_alphanumeric() || ch == '_' {
            cur.push(ch);
        } else if !cur.is_empty() {
            if !out.iter().any(|t| t == &cur) {
                out.push(std::mem::take(&mut cur));
            } else {
                cur.clear();
            }
        }
    }
    if !cur.is_empty() && !out.iter().any(|t| t == &cur) {
        out.push(cur);
    }
    out
}

/// Monta a consulta FTS5: cada token como frase, unidos por OR.
///
/// Tokens vêm de `[A-Za-z0-9_]+`, então não podem conter `"` e não há injeção de sintaxe.
/// Lista vazia devolve `None` — consulta sem token não deve virar `MATCH ''` silencioso.
fn fts_query(tokens: &[String]) -> Option<String> {
    if tokens.is_empty() {
        return None;
    }
    Some(
        tokens
            .iter()
            .map(|t| format!("\"{t}\""))
            .collect::<Vec<_>>()
            .join(" OR "),
    )
}

/// Busca BM25 sobre o corpo dos arquivos indexados.
pub fn search(conn: &Connection, query: &str, limit: usize) -> Result<Vec<Hit>> {
    let tokens = tokenize(query);
    let Some(fq) = fts_query(&tokens) else {
        return Ok(Vec::new());
    };
    let mut stmt = conn.prepare(
        "SELECT path, bm25(docs) AS s FROM docs WHERE docs MATCH ?1 ORDER BY s LIMIT ?2",
    )?;
    let rows = stmt.query_map(params![fq, limit as i64], |r| {
        Ok(Hit {
            path: r.get::<_, String>(0)?,
            score: r.get::<_, f64>(1)?,
        })
    })?;
    Ok(rows.collect::<rusqlite::Result<Vec<_>>>()?)
}

/// Linhas (1-based) que contêm algum token, por comparação literal sem diferenciar caixa.
///
/// É a verificação nome-na-linha do protocolo: o trecho só é entregue se o termo buscado
/// estiver realmente naquele texto, lido do disco — nunca inferido do índice.
pub fn locate_lines(text: &str, tokens: &[String]) -> Vec<usize> {
    let lowered: Vec<String> = tokens.iter().map(|t| t.to_ascii_lowercase()).collect();
    let mut out = Vec::new();
    for (i, line) in text.lines().enumerate() {
        let l = line.to_ascii_lowercase();
        if lowered.iter().any(|t| l.contains(t.as_str())) {
            out.push(i + 1);
        }
    }
    out
}

/// Tokens que aparecem literalmente num trecho, para o campo `evidence`.
pub fn tokens_present(text: &str, tokens: &[String]) -> Vec<String> {
    let l = text.to_ascii_lowercase();
    let mut out: Vec<String> = tokens
        .iter()
        .filter(|t| l.contains(&t.to_ascii_lowercase()))
        .cloned()
        .collect();
    out.truncate(5);
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn tokeniza_igual_ao_contrato() {
        assert_eq!(tokenize("ExMovimentacao"), vec!["ExMovimentacao"]);
        assert_eq!(tokenize("a.b.c"), vec!["a", "b", "c"]);
        assert_eq!(tokenize("  "), Vec::<String>::new());
        assert_eq!(tokenize("###"), Vec::<String>::new());
        assert_eq!(tokenize("_x1"), vec!["_x1"]);
    }

    #[test]
    fn tokeniza_sem_repeticao_e_em_ordem() {
        assert_eq!(tokenize("dup dup outro"), vec!["dup", "outro"]);
    }

    #[test]
    fn consulta_fts_escapa_e_une_com_or() {
        assert_eq!(fts_query(&tokenize("a b")).unwrap(), "\"a\" OR \"b\"");
        assert!(fts_query(&[]).is_none());
    }

    #[test]
    fn localiza_linhas_sem_diferenciar_caixa() {
        let text = "class A {\n  void ExMovimentacao() {}\n}\n";
        assert_eq!(locate_lines(text, &["exmovimentacao".into()]), vec![2]);
        assert_eq!(locate_lines(text, &["nada".into()]), Vec::<usize>::new());
    }

    #[test]
    fn evidencia_limita_a_cinco_tokens() {
        let text = "a b c d e f g";
        let toks: Vec<String> = "abcdefg".chars().map(|c| c.to_string()).collect();
        assert_eq!(tokens_present(text, &toks).len(), 5);
    }
}
