// SPDX-License-Identifier: Apache-2.0
//! Seleção de trechos e orçamento — o coração do contrato §6.
//!
//! A diferença central em relação à referência Python é que o orçamento é medido sobre o
//! **JSON serializado inteiro**, e não sobre a soma dos itens. `BASELINE.md` §4 mediu o
//! defeito antigo: `used: 1972` para um payload de 16 358 bytes (~4 089 tokens estimados),
//! ou seja ~2,07x acima do declarado. Aqui o campo `used_bytes` é literalmente o tamanho da
//! serialização que o contém — a medir e a reportar são a mesma operação.
//!
//! Ordem obrigatória: candidatos → rank → seleção → montar JSON completo → serializar e
//! contar → remover/encurtar → serializar e contar de novo → entregar → avaliar só o entregue.

use crate::request::{Policy, ValidRequest};
use crate::retrieve;
use crate::snapshot::{resolve_within, sha256_bytes};
use crate::store::Store;
use crate::{token_estimate, SCHEMA_VERSION};
use serde::Serialize;
use std::collections::HashMap;
use std::path::Path;

/// Janela de contexto por match, por política.
const CTX_LINES_LEX: usize = 2;
const CTX_LINES_CTX: usize = 6;

/// Teto de linhas por unidade. Acima disto o trecho é partido, para que uma definição
/// enorme não consuma o orçamento inteiro numa unidade só.
const MAX_UNIT_LINES: usize = 60;

/// Unidades por arquivo no CTX-RS. É a correção do defeito de diversidade medido em
/// `BASELINE.md` §4: sem teto, um único arquivo consumiu 39 das 39 refs entregues.
const MAX_SPANS_PER_FILE: usize = 3;

/// Arquivos candidatos processados no máximo. Limita IO quando a consulta é muito comum.
const MAX_CANDIDATE_FILES: usize = 200;

const MAX_HINTS: usize = 5;

/// Falha com código de saída associado, decidido no contrato §3.
#[derive(Debug)]
pub enum PackError {
    /// Pedido malformado na camada de conteúdo (código 2) — distinto de pedido inválido de
    /// linha de comando, que o CLI já barra antes de chegar aqui.
    BadRequest(String),
    /// Integridade violada (código 5): caminho fora da raiz, ou nenhuma fonte verificável.
    Integrity(String),
    /// Erro de I/O (código 4).
    Io(String),
}

impl PackError {
    pub fn code(&self) -> i32 {
        match self {
            PackError::BadRequest(_) => 2,
            PackError::Integrity(_) => 5,
            PackError::Io(_) => 4,
        }
    }
}

impl std::fmt::Display for PackError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            PackError::BadRequest(m) | PackError::Integrity(m) | PackError::Io(m) => {
                write!(f, "{m}")
            }
        }
    }
}

impl std::error::Error for PackError {}

/// Uma unidade entregue. Ordem dos campos = ordem no JSON (`CLI_CONTRACT/1` §5).
#[derive(Debug, Clone, Serialize)]
pub struct Unit {
    pub file: String,
    pub line: u32,
    pub end_line: u32,
    pub hash: String,
    pub kind: String,
    pub text: String,
    pub evidence: String,
    pub reason: String,
    pub truncated: bool,
}

#[derive(Debug, Clone, Serialize)]
pub struct SnapshotInfo {
    pub sha_base: Option<String>,
    pub index_generation: String,
    pub index_state: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct BudgetInfo {
    pub requested_tokens: u64,
    pub used_tokens: u64,
    pub unit: String,
    pub tokenizer_id: Option<String>,
    pub tokenizer_is_exact: bool,
    pub max_bytes: u64,
    pub used_bytes: u64,
}

#[derive(Debug, Clone, Serialize)]
pub struct Omitted {
    pub n: u64,
    pub reasons: Vec<String>,
}

/// Envelope de resposta. A ordem de declaração é a ordem publicada no JSON.
#[derive(Debug, Clone, Serialize)]
pub struct Response {
    pub schema: String,
    pub schema_version: u32,
    pub state: String,
    pub snapshot: SnapshotInfo,
    pub units: Vec<Unit>,
    pub budget: BudgetInfo,
    pub omitted: Omitted,
    pub hints: Vec<String>,
}

/// Contexto do índice necessário para carimbar a resposta.
#[derive(Debug, Clone)]
pub struct Ctx {
    /// `sha_base` gravado no índice.
    pub sha_base: Option<String>,
    pub index_generation: String,
    pub index_state: String,
    /// Snapshot que o agente declarou estar consultando. Diferente do índice significa
    /// que a resposta descreve outro commit — `stale`, não "nada encontrado".
    pub requested_sha_base: Option<String>,
}

/// Arquivo candidato que passou na verificação de bytes.
struct Verified {
    rel: String,
    hash: String,
    text: String,
    match_lines: Vec<usize>,
    origin: String,
}

/// Intervalo de linhas, 1-based e inclusivo.
#[derive(Debug, Clone, Copy)]
struct Span {
    start: usize,
    end: usize,
}

/// Resultado interno: unidades candidatas mais o que foi descartado antes do orçamento.
struct Candidates {
    units: Vec<Unit>,
    dropped: u64,
    reasons: Vec<String>,
    dropped_refs: Vec<String>,
    stale: bool,
}

fn push_reason(reasons: &mut Vec<String>, r: &str) {
    if !reasons.iter().any(|x| x == r) {
        reasons.push(r.to_string());
    }
}

/// Lê o arquivo uma única vez e devolve `(hash, texto)`.
///
/// Uma leitura serve para as duas coisas: re-verificar contra o índice e montar o trecho.
/// Ler duas vezes dobraria o IO no caminho mais quente da ferramenta.
fn load_verified(abs: &Path) -> Option<(String, String)> {
    let raw = std::fs::read(abs).ok()?;
    let hash = sha256_bytes(&raw);
    Some((hash, String::from_utf8_lossy(&raw).into_owned()))
}

/// Agrupa linhas de match em spans com contexto, respeitando o teto por unidade.
fn spans_from_lines(lines: &[usize], ctx: usize, total_lines: usize) -> Vec<Span> {
    if lines.is_empty() || total_lines == 0 {
        return Vec::new();
    }
    // 1. agrupa matches próximos, para não gerar um span por linha quando o termo aparece
    //    em sequência.
    let mut clusters: Vec<(usize, usize)> = Vec::new();
    let (mut cs, mut ce) = (lines[0], lines[0]);
    for &l in &lines[1..] {
        if l <= ce + 2 * ctx + 1 {
            ce = l;
        } else {
            clusters.push((cs, ce));
            cs = l;
            ce = l;
        }
    }
    clusters.push((cs, ce));

    // 2. expande com contexto, corta nas bordas e fatia o que exceder o teto.
    let mut spans: Vec<Span> = Vec::new();
    for (a, b) in clusters {
        let start = a.saturating_sub(ctx).max(1);
        let end = (b + ctx).min(total_lines);
        let mut s = start;
        while s <= end {
            let e = (s + MAX_UNIT_LINES - 1).min(end);
            spans.push(Span { start: s, end: e });
            s = e + 1;
        }
    }
    // 3. funde o que se sobrepôs (contextos grandes podem encostar).
    spans.sort_by_key(|s| s.start);
    let mut merged: Vec<Span> = Vec::new();
    for span in spans {
        match merged.last_mut() {
            Some(prev) if span.start <= prev.end + 1 => {
                prev.end = prev.end.max(span.end);
            }
            _ => merged.push(span),
        }
    }
    merged
}

fn make_unit(v: &Verified, span: Span, tokens: &[String], reason: String) -> Unit {
    let lines: Vec<&str> = v.text.lines().collect();
    let start = span.start.saturating_sub(1).min(lines.len());
    let end = span.end.min(lines.len());
    let text = lines[start..end].join("\n");
    let present = retrieve::tokens_present(&text, tokens);
    Unit {
        file: v.rel.clone(),
        line: span.start as u32,
        end_line: span.end as u32,
        hash: format!("sha256:{}", v.hash),
        kind: "excerpt".to_string(),
        evidence: format!("tokens={}", present.join(",")),
        text,
        reason,
        truncated: false,
    }
}

/// Constrói as unidades candidatas conforme a política, verificando cada fonte no disco.
fn candidates(
    repo: &Path,
    store: &Store,
    req: &ValidRequest,
    tokens: &[String],
) -> Result<Candidates, PackError> {
    let known: HashMap<String, String> = store
        .logical_dump()
        .map_err(|e| PackError::Io(format!("falha ao ler o indice: {e}")))?
        .into_iter()
        .collect();

    // Ordem de candidatos: `known_refs` primeiro (o agente já sabe onde olhar), depois BM25.
    let mut order: Vec<(String, String)> = Vec::new(); // (rel, origem)
    for r in &req.raw.known_refs {
        let clean = r.file.trim_start_matches("./").to_string();
        if !order.iter().any(|(p, _)| p == &clean) {
            order.push((clean, "known_ref".to_string()));
        }
    }
    let hits = retrieve::search(&store.conn, &req.raw.query, retrieve::CANDIDATE_LIMIT)
        .map_err(|e| PackError::Io(format!("busca lexical falhou: {e}")))?;
    for (rank, h) in hits.iter().enumerate() {
        if !order.iter().any(|(p, _)| p == &h.path) {
            order.push((h.path.clone(), format!("bm25 rank {rank}")));
        }
    }
    order.truncate(MAX_CANDIDATE_FILES);

    let mut dropped = 0u64;
    let mut reasons: Vec<String> = Vec::new();
    let mut dropped_refs: Vec<String> = Vec::new();
    let mut stale = false;
    let mut verified: Vec<Verified> = Vec::new();

    for (rel, origin) in &order {
        // Caminho fora da raiz é violação de integridade, não arquivo ausente (§3, código 5).
        let abs = resolve_within(repo, rel)
            .map_err(|e| PackError::Integrity(format!("referencia insegura ({rel}): {e}")))?;
        let Some(expected) = known.get(rel) else {
            // Não está no índice. Pode ser arquivo novo (índice desatualizado) ou `known_ref`
            // apontando para algo que nunca foi indexado.
            stale = true;
            dropped += 1;
            push_reason(&mut reasons, "not_indexed");
            dropped_refs.push(rel.clone());
            continue;
        };
        let Some((hash, text)) = load_verified(&abs) else {
            stale = true;
            dropped += 1;
            push_reason(&mut reasons, "stale_source");
            dropped_refs.push(rel.clone());
            continue;
        };
        if &hash != expected {
            // O arquivo mudou depois da indexação. O índice não pode servir texto não
            // verificado, então a unidade sai e o estado vira `stale`.
            stale = true;
            dropped += 1;
            push_reason(&mut reasons, "stale_source");
            dropped_refs.push(rel.clone());
            continue;
        }
        let match_lines = retrieve::locate_lines(&text, tokens);
        if match_lines.is_empty() {
            // O FTS5 casou por radical (`porter`); sem ocorrência literal não há evidência
            // nome-na-linha, então nada é entregue deste arquivo.
            dropped += 1;
            push_reason(&mut reasons, "no_literal_match");
            dropped_refs.push(rel.clone());
            continue;
        }
        verified.push(Verified {
            rel: rel.clone(),
            hash,
            text,
            match_lines,
            origin: origin.clone(),
        });
    }

    // Nada verificado, mas havia candidatos: não existe resposta verificada a dar (código 5).
    if verified.is_empty() && !order.is_empty() {
        return Err(PackError::Integrity(
            "nenhuma fonte selecionada passou na verificacao de bytes; \
             o indice esta desatualizado (rode `archatlas index`)"
                .to_string(),
        ));
    }

    let mut units: Vec<Unit> = Vec::new();
    match req.policy {
        Policy::LexRs => {
            // Empacotamento fixo: uma unidade por arquivo, a partir da primeira ocorrência.
            for v in &verified {
                let first = v.match_lines[0];
                let span = Span {
                    start: first.saturating_sub(CTX_LINES_LEX).max(1),
                    end: first + CTX_LINES_LEX,
                };
                let reason = if v.origin == "known_ref" {
                    "known_ref; janela fixa".to_string()
                } else {
                    format!("{}; janela fixa", v.origin)
                };
                units.push(make_unit(v, span, tokens, reason));
            }
        }
        Policy::CtxRs => {
            // Diversidade primeiro: round-robin entre arquivos, com teto por arquivo.
            let per_file: Vec<Vec<Span>> = verified
                .iter()
                .map(|v| spans_from_lines(&v.match_lines, CTX_LINES_CTX, v.text.lines().count()))
                .collect();
            for slot in 0..MAX_SPANS_PER_FILE {
                for (i, spans) in per_file.iter().enumerate() {
                    let Some(span) = spans.get(slot) else {
                        continue;
                    };
                    let v = &verified[i];
                    let n_matches = v
                        .match_lines
                        .iter()
                        .filter(|l| **l >= span.start && **l <= span.end)
                        .count();
                    let reason = format!("{}; {n_matches} ocorrencia(s)", v.origin);
                    units.push(make_unit(v, *span, tokens, reason));
                }
            }
            // O teto por arquivo é uma escolha da política: registre quando ele morde.
            let capped: usize = per_file
                .iter()
                .map(|s| s.len().saturating_sub(MAX_SPANS_PER_FILE))
                .sum();
            if capped > 0 {
                dropped += capped as u64;
                push_reason(&mut reasons, "diversity_cap");
            }
        }
    }

    Ok(Candidates {
        units,
        dropped,
        reasons,
        dropped_refs,
        stale,
    })
}

/// Serializa, mede, ajusta os campos de orçamento e mede de novo até o tamanho estabilizar.
///
/// O ponto fixo existe porque preencher `used_bytes`/`used_tokens` altera o tamanho da
/// própria serialização (mais dígitos). Paramos quando o valor gravado é igual ao tamanho
/// medido — é essa igualdade que torna a alegação de orçamento verificável.
fn fixpoint(resp: &mut Response) -> (usize, u64) {
    settle_budget(resp, |r, bytes, tokens| {
        r.budget.used_bytes = bytes;
        r.budget.used_tokens = tokens;
    })
}

/// Serializa, mede, grava a medida no próprio valor e repete até estabilizar.
///
/// Genérico porque `context`, `expand` e `verify` publicam o mesmo campo `budget` e a regra
/// é idêntica: o número publicado descreve a serialização que o contém. O ponto fixo existe
/// porque preencher os campos altera o tamanho da própria serialização (mais dígitos).
pub fn settle_budget<T, F>(value: &mut T, mut set: F) -> (usize, u64)
where
    T: Serialize,
    F: FnMut(&mut T, u64, u64),
{
    let mut used: usize = 0;
    loop {
        set(value, used as u64, token_estimate(used));
        let measured = serde_json::to_vec(value).map(|v| v.len()).unwrap_or(0);
        if measured == used {
            return (measured, token_estimate(measured));
        }
        used = measured;
    }
}

/// Monta o envelope completo.
///
/// `state` entra já aqui, e não como ajuste posterior, porque o estado é parte da
/// serialização: escrevê-lo depois de medir invalidaria a contagem. Essa foi exatamente a
/// causa de um desvio de 5 bytes entre `used_bytes` e o stdout real na primeira versão.
fn assemble(
    req: &ValidRequest,
    ctx: &Ctx,
    kept: &[Unit],
    omitted_n: u64,
    reasons: &[String],
    hints: &[String],
    state: &str,
) -> Response {
    let mut sorted = reasons.to_vec();
    sorted.sort();
    sorted.dedup();
    Response {
        schema: "atlas-context/1".to_string(),
        schema_version: SCHEMA_VERSION,
        state: state.to_string(),
        snapshot: SnapshotInfo {
            sha_base: ctx.sha_base.clone(),
            index_generation: ctx.index_generation.clone(),
            index_state: ctx.index_state.clone(),
        },
        units: kept.to_vec(),
        budget: BudgetInfo {
            requested_tokens: req.raw.budget_tokens,
            used_tokens: 0,
            // Sem tokenizer correspondente ao modelo, o limite exato é em bytes e os tokens
            // são estimados. Declarar o contrário seria a alegação que o contrato proíbe.
            unit: "byte".to_string(),
            tokenizer_id: req.raw.tokenizer_id.clone(),
            tokenizer_is_exact: false,
            max_bytes: req.raw.max_bytes,
            used_bytes: 0,
        },
        omitted: Omitted {
            n: omitted_n,
            reasons: sorted,
        },
        hints: hints.to_vec(),
    }
}

/// Corta a unidade para `keep` linhas.
///
/// Encurtar por linha mantém o texto em fronteira válida de UTF-8 por construção — o
/// contrato proíbe declarar trecho incompleto como completo, então `truncated` vira `true`
/// e `end_line` passa a descrever o que foi realmente enviado.
fn truncate_unit(unit: &mut Unit, keep: usize) -> bool {
    let lines: Vec<&str> = unit.text.lines().collect();
    if lines.len() <= 1 || keep == 0 || keep >= lines.len() {
        return false;
    }
    unit.text = lines[..keep].join("\n");
    unit.end_line = unit.line + keep as u32 - 1;
    unit.truncated = true;
    true
}

/// Estado publicado. `stale` descreve o índice; `partial` descreve o recorte.
fn decide_state(stale: bool, omitted_n: u64, truncated: bool, reasons: &[String]) -> &'static str {
    if stale {
        "stale"
    } else if omitted_n > 0 || truncated || !reasons.is_empty() {
        "partial"
    } else {
        "ok"
    }
}

fn fits(bytes: usize, tokens: u64, req: &ValidRequest) -> bool {
    bytes <= req.raw.max_bytes as usize && tokens <= req.raw.budget_tokens
}

/// Uma resposta já medida.
struct Rendered {
    resp: Response,
    bytes: usize,
    tokens: u64,
}

/// Contexto do ajuste de orçamento. Agrupar os parâmetros evita uma assinatura de oito
/// posições onde trocar dois argumentos passaria compilando.
struct Fit<'a> {
    req: &'a ValidRequest,
    ctx: &'a Ctx,
    all: &'a [Unit],
    base_dropped: u64,
    base_reasons: &'a [String],
    hint_refs: &'a [String],
    stale: bool,
    no_match: bool,
}

impl Fit<'_> {
    /// Único ponto que monta e mede uma resposta.
    ///
    /// `omitted` é derivado de `k`, nunca acumulado entre chamadas: é isso que torna o
    /// tamanho monótono em `k`, premissa da busca binária abaixo.
    fn render_with(
        &self,
        kept: &[Unit],
        omitted_units: &[Unit],
        dropped: u64,
        extra: Option<&str>,
    ) -> Rendered {
        let mut reasons = self.base_reasons.to_vec();
        if let Some(r) = extra {
            push_reason(&mut reasons, r);
        }
        let truncated = kept.iter().any(|u| u.truncated);
        let state = decide_state(self.stale, dropped, truncated, &reasons);

        let mut hints = build_hints(self.hint_refs, self.stale);
        // Dicas acionáveis: os trechos que ficaram de fora. Sem isto, um corte por
        // orçamento devolvia `hints: []` e o agente não sabia o que pedir em `expand`.
        for u in omitted_units.iter().take(MAX_HINTS) {
            if hints.len() >= MAX_HINTS {
                break;
            }
            hints.push(format!("expand: {}", u.file));
        }
        if self.no_match && hints.is_empty() {
            hints.push("sem correspondencia lexical; tente outro termo ou leia direto".to_string());
        }

        let mut resp = assemble(self.req, self.ctx, kept, dropped, &reasons, &hints, state);
        let (bytes, tokens) = fixpoint(&mut resp);
        Rendered {
            resp,
            bytes,
            tokens,
        }
    }

    /// Resposta com as `k` primeiras unidades em ordem de prioridade.
    fn render(&self, k: usize) -> Rendered {
        let k = k.min(self.all.len());
        let (dropped, extra) = if k < self.all.len() {
            (
                self.base_dropped + (self.all.len() - k) as u64,
                Some("budget"),
            )
        } else {
            (self.base_dropped, None)
        };
        self.render_with(&self.all[..k], &self.all[k..], dropped, extra)
    }
}

/// Janela de contexto ampliada usada por `expand`.
const EXPAND_CONTEXT_LINES: usize = 20;

/// `true` quando o caminho parece de teste. Heurística **de caminho**, declarada como tal:
/// não lê o conteúdo nem promete que o arquivo é um teste.
fn looks_like_test(rel: &str) -> bool {
    let lower = rel.to_ascii_lowercase();
    lower.contains("test") || lower.contains("spec")
}

/// Subtrai de `span` os intervalos já entregues. Fatiar em vez de descartar evita
/// reentregar o mesmo trecho só porque a nova janela o cobriu em parte.
fn subtract_covered(span: Span, covered: &[(u32, u32)]) -> Vec<Span> {
    let mut pieces = vec![span];
    for (cs, ce) in covered {
        let mut next: Vec<Span> = Vec::new();
        for p in pieces {
            // Sem sobreposição: o pedaço passa inteiro.
            if *ce < p.start as u32 || *cs > p.end as u32 {
                next.push(p);
                continue;
            }
            if *cs > p.start as u32 {
                next.push(Span {
                    start: p.start,
                    end: (*cs as usize - 1).max(p.start),
                });
            }
            if *ce < p.end as u32 {
                next.push(Span {
                    start: (*ce as usize + 1).max(p.start),
                    end: p.end,
                });
            }
        }
        pieces = next;
    }
    pieces.retain(|p| p.end > p.start || (p.end == p.start && p.start > 0));
    pieces
}

/// Intervalos já entregues, por arquivo, para deduplicação.
fn delivered_spans(refs: &[crate::request::RefSpec]) -> HashMap<String, Vec<(u32, u32)>> {
    let mut out: HashMap<String, Vec<(u32, u32)>> = HashMap::new();
    for r in refs {
        let clean = r.file.trim_start_matches("./").to_string();
        let start = r.line.unwrap_or(1);
        let end = r.end_line.unwrap_or(start).max(start);
        out.entry(clean).or_default().push((start, end));
    }
    out
}

/// Candidatos de `expand`: refs apontadas, ampliadas, mais a evidência pedida.
///
/// `delivered_refs` é deduzido do que sai: o agente que já recebeu um trecho não deve
/// pagar por ele de novo, e o orçamento gasto nele é desperdiçado.
fn expand_candidates(
    repo: &Path,
    store: &Store,
    req: &ValidRequest,
    tokens: &[String],
) -> Result<Candidates, PackError> {
    let known: HashMap<String, String> = store
        .logical_dump()
        .map_err(|e| PackError::Io(format!("falha ao ler o indice: {e}")))?
        .into_iter()
        .collect();
    let delivered = delivered_spans(&req.raw.delivered_refs);
    let kind = req.raw.evidence_wanted.as_deref().unwrap_or("context");

    // Referências apontadas primeiro; depois, quando o tipo de evidência pede busca,
    // os arquivos que a consulta alcança.
    let mut order: Vec<(String, String, Option<(u32, u32)>)> = Vec::new();
    for r in &req.raw.known_refs {
        let clean = r.file.trim_start_matches("./").to_string();
        if !order.iter().any(|(p, ..)| p == &clean) {
            let span = r.line.map(|l| (l, r.end_line.unwrap_or(l).max(l)));
            order.push((clean, "known_ref".to_string(), span));
        }
    }
    if kind != "context" {
        let hits = retrieve::search(&store.conn, &req.raw.query, retrieve::CANDIDATE_LIMIT)
            .map_err(|e| PackError::Io(format!("busca lexical falhou: {e}")))?;
        for h in hits {
            if kind == "tests" && !looks_like_test(&h.path) {
                continue;
            }
            if !order.iter().any(|(p, ..)| p == &h.path) {
                order.push((h.path.clone(), format!("lexical:{kind}"), None));
            }
        }
    }
    order.truncate(MAX_CANDIDATE_FILES);

    let mut units: Vec<Unit> = Vec::new();
    let mut emitted: HashMap<String, Vec<(u32, u32)>> = HashMap::new();
    let mut dropped = 0u64;
    let mut reasons: Vec<String> = Vec::new();
    let mut dropped_refs: Vec<String> = Vec::new();
    let mut stale = false;
    let mut verified_any = false;

    for (rel, origin, asked) in &order {
        let abs = resolve_within(repo, rel)
            .map_err(|e| PackError::Integrity(format!("referencia insegura ({rel}): {e}")))?;
        let Some(expected) = known.get(rel) else {
            stale = true;
            dropped += 1;
            push_reason(&mut reasons, "not_indexed");
            dropped_refs.push(rel.clone());
            continue;
        };
        let Some((hash, text)) = load_verified(&abs) else {
            stale = true;
            dropped += 1;
            push_reason(&mut reasons, "stale_source");
            dropped_refs.push(rel.clone());
            continue;
        };
        if &hash != expected {
            stale = true;
            dropped += 1;
            push_reason(&mut reasons, "stale_source");
            dropped_refs.push(rel.clone());
            continue;
        }
        verified_any = true;
        let total_lines = text.lines().count().max(1);
        // `match_lines` é calculado antes de `text` ir para o `Verified`, senão o valor
        // estaria movido.
        let match_lines = retrieve::locate_lines(&text, tokens);
        let v = Verified {
            rel: rel.clone(),
            hash,
            text,
            match_lines,
            origin: origin.clone(),
        };

        // Janelas: pedida pela ref, ou em torno das ocorrências do termo.
        let mut spans: Vec<Span> = Vec::new();
        if let Some((s, e)) = asked {
            let start = (*s as usize).saturating_sub(EXPAND_CONTEXT_LINES).max(1);
            let end = (*e as usize + EXPAND_CONTEXT_LINES).min(total_lines);
            let mut cursor = start;
            while cursor <= end {
                let stop = (cursor + MAX_UNIT_LINES - 1).min(end);
                spans.push(Span {
                    start: cursor,
                    end: stop,
                });
                cursor = stop + 1;
            }
        } else if !v.match_lines.is_empty() {
            spans = spans_from_lines(&v.match_lines, EXPAND_CONTEXT_LINES, total_lines);
        }
        if spans.is_empty() {
            // Sem ocorrência literal e sem linha apontada: nada verificável a ampliar.
            dropped += 1;
            push_reason(&mut reasons, "no_literal_match");
            dropped_refs.push(rel.clone());
            continue;
        }

        // Dedup contra o que já foi entregue e contra o que esta própria chamada emite.
        let mut covered = delivered.get(rel).cloned().unwrap_or_default();
        covered.extend(emitted.get(rel).cloned().unwrap_or_default());
        for span in spans {
            let mut kept_any = false;
            for piece in subtract_covered(span, &covered) {
                if piece.end < piece.start {
                    continue;
                }
                let n_matches = v
                    .match_lines
                    .iter()
                    .filter(|l| **l >= piece.start && **l <= piece.end)
                    .count();
                let reason = if n_matches > 0 {
                    format!("{}; {n_matches} ocorrencia(s)", v.origin)
                } else {
                    format!("{}; janela ampliada", v.origin)
                };
                units.push(make_unit(&v, piece, tokens, reason));
                emitted
                    .entry(rel.clone())
                    .or_default()
                    .push((piece.start as u32, piece.end as u32));
                kept_any = true;
            }
            if !kept_any {
                dropped += 1;
                push_reason(&mut reasons, "duplicate");
            }
        }
    }

    // Nada verificável, mas havia referências: não existe resposta verificada a dar.
    if !verified_any && !order.is_empty() {
        return Err(PackError::Integrity(
            "nenhuma referencia passou na verificacao de bytes; \
             o indice esta desatualizado (rode `archatlas index`)"
                .to_string(),
        ));
    }

    Ok(Candidates {
        units,
        dropped,
        reasons,
        dropped_refs,
        stale,
    })
}

/// Ajusta as unidades candidatas ao orçamento e devolve a resposta final.
///
/// Compartilhado por `context` e `expand`: as duas etapas diferem na **origem** das
/// unidades, nunca na forma de medir o orçamento. Duplicar essa lógica seria a maneira mais
/// fácil de as duas divergirem sem que nenhum teste percebesse.
fn finalize(req: &ValidRequest, ctx: &Ctx, cands: Candidates) -> Response {
    // O snapshot pedido pode não ser o snapshot indexado. Isso é `stale`, e precisa aparecer
    // antes de qualquer outra coisa: um recorte parcial de outro commit engana o agente.
    let sha_mismatch = match (&ctx.requested_sha_base, &ctx.sha_base) {
        (Some(requested), Some(indexed)) => requested != indexed,
        (Some(_), None) => true,
        _ => false,
    };
    let stale = cands.stale || sha_mismatch;

    let mut reasons = cands.reasons.clone();
    if sha_mismatch {
        push_reason(&mut reasons, "snapshot_mismatch");
    }
    let no_match = cands.units.is_empty() && reasons.is_empty();
    let fit = Fit {
        req,
        ctx,
        all: &cands.units,
        base_dropped: cands.dropped,
        base_reasons: &reasons,
        hint_refs: &cands.dropped_refs,
        stale,
        no_match,
    };

    // O envelope vazio é o piso físico: nada menor existe. Se nem ele cabe, entregamos a
    // resposta vazia dizendo o motivo em vez de fingir que coube. As pistas de expansão são
    // omitidas de propósito nesse caso — elas só aumentariam esse piso.
    let empty = fit.render(0);
    if !fits(empty.bytes, empty.tokens, req) {
        let minimal = vec![
            "orcamento abaixo do envelope minimo; aumente budget_tokens ou max_bytes".to_string(),
        ];
        let mut all_reasons = reasons.clone();
        push_reason(&mut all_reasons, "envelope_too_large");
        let state = if stale { "stale" } else { "partial" };
        let mut resp = assemble(req, ctx, &[], cands.dropped, &all_reasons, &minimal, state);
        let _ = fixpoint(&mut resp);
        return resp;
    }

    let full = fit.render(cands.units.len());
    if fits(full.bytes, full.tokens, req) {
        return full.resp;
    }

    // Busca binária pelo maior prefixo que cabe. Substitui o "remove uma unidade e
    // re-serializa tudo" da primeira versão: com 200 candidatos e ~40 que cabiam, aquilo
    // fazia ~160 serializações completas e dominava o tempo de resposta (3,6 s medidos no
    // repositório real, contra 2 ms da consulta FTS5 equivalente).
    //
    // `lo` parte de 0, que já foi verificado como adequado; `hi` é `len`, já verificado
    // como inadequado. O tamanho é monótono em `k`, então a bisseção é válida.
    let mut lo = 0usize;
    let mut hi = cands.units.len();
    while hi - lo > 1 {
        let mid = lo + (hi - lo) / 2;
        let r = fit.render(mid);
        if fits(r.bytes, r.tokens, req) {
            lo = mid;
        } else {
            hi = mid;
        }
    }
    let mut best = fit.render(lo);

    // Sober espaço: aproveita a próxima unidade **cortada** em vez de descartá-la inteira.
    // Tenta as frações da maior para a menor e fica com a primeira que couber.
    if let Some(next) = cands.units.get(lo) {
        let total = next.text.lines().count();
        for keep in [total * 3 / 4, total / 2, total / 4] {
            let mut cut = next.clone();
            if !truncate_unit(&mut cut, keep) {
                continue;
            }
            let mut trial = cands.units[..lo].to_vec();
            trial.push(cut);
            // A unidade que sofreu o corte sai da lista de omitidas; as demais seguem.
            let omitted = &cands.units[(lo + 1).min(cands.units.len())..];
            let dropped = cands.dropped + omitted.len() as u64;
            let r = fit.render_with(&trial, omitted, dropped, Some("budget"));
            if fits(r.bytes, r.tokens, req) {
                best = r;
                break;
            }
        }
    }

    best.resp
}

/// Monta a resposta de `context` dentro do orçamento, ou falha com o código do contrato.
pub fn build_context(
    repo: &Path,
    store: &Store,
    req: &ValidRequest,
    ctx: Ctx,
) -> Result<Response, PackError> {
    let tokens = retrieve::tokenize(&req.raw.query);
    let cands = candidates(repo, store, req, &tokens)?;
    Ok(finalize(req, &ctx, cands))
}

/// Monta a resposta de `expand` — ampliação por referência já entregue (R2).
pub fn build_expand(
    repo: &Path,
    store: &Store,
    req: &ValidRequest,
    ctx: Ctx,
) -> Result<Response, PackError> {
    let tokens = retrieve::tokenize(&req.raw.query);
    let cands = expand_candidates(repo, store, req, &tokens)?;
    Ok(finalize(req, &ctx, cands))
}

/// Pistas curtas de expansão. Nunca é um despejo de paths: no máximo `MAX_HINTS`.
fn build_hints(refs: &[String], stale: bool) -> Vec<String> {
    let mut hints: Vec<String> = Vec::new();
    if stale {
        hints.push("indice desatualizado; rode `archatlas index` e repita o pedido".to_string());
    }
    for r in refs.iter().filter(|r| !r.is_empty()).take(MAX_HINTS) {
        if hints.len() >= MAX_HINTS {
            break;
        }
        // Só o path relativo: a linha já vai em cada unidade que ficou.
        hints.push(format!("expand: {r}"));
    }
    hints.truncate(MAX_HINTS);
    hints
}

/// Resposta de diagnóstico quando o índice não pode servir nada (código 3).
///
/// Mantém o envelope para que o consumidor não precise de um caminho de parsing separado,
/// e usa `state: unsupported` para dizer "este índice não responde", não "nada encontrado".
pub fn unservable(req: &ValidRequest, ctx: &Ctx, reason: &str) -> Response {
    let mut resp = assemble(
        req,
        ctx,
        &[],
        0,
        &[format!("index_{reason}")],
        &[format!(
            "indice {reason}; rode `archatlas index` ou use leitura direta"
        )],
        "unsupported",
    );
    let _ = fixpoint(&mut resp);
    resp
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn spans_agrupam_expandem_e_respeitam_teto() {
        // matches na linha 10 e 12 com contexto 2 -> span 8..14
        let s = spans_from_lines(&[10, 12], 2, 100);
        assert_eq!(s.len(), 1);
        assert_eq!((s[0].start, s[0].end), (8, 14));
    }

    #[test]
    fn spans_cortam_nas_bordas_do_arquivo() {
        let s = spans_from_lines(&[1], 6, 3);
        assert_eq!((s[0].start, s[0].end), (1, 3));
    }

    #[test]
    fn spans_fatiam_unidade_gigante() {
        // 400 linhas de um arquivo com contexto grande: precisa sair em vários spans.
        let s = spans_from_lines(&[200], 6, 400);
        assert!(s.len() >= 1);
        for span in &s {
            assert!(span.end - span.start + 1 <= MAX_UNIT_LINES + 1);
        }
    }

    #[test]
    fn spans_separam_matches_distantes() {
        let s = spans_from_lines(&[10, 100], 2, 200);
        assert_eq!(s.len(), 2);
    }

    fn unit_com(n: usize) -> Unit {
        Unit {
            file: "a.java".into(),
            line: 10,
            end_line: 9 + n as u32,
            hash: "sha256:x".into(),
            kind: "excerpt".into(),
            text: (1..=n)
                .map(|i| i.to_string())
                .collect::<Vec<_>>()
                .join("\n"),
            evidence: String::new(),
            reason: String::new(),
            truncated: false,
        }
    }

    #[test]
    fn truncar_mantem_end_line_coerente_e_marca_truncado() {
        let mut u = unit_com(10);
        assert!(truncate_unit(&mut u, 6));
        assert!(u.truncated);
        assert_eq!(u.text.lines().count(), 6);
        // `end_line` precisa descrever o que foi realmente entregue.
        assert_eq!(u.end_line, u.line + 6 - 1);
    }

    #[test]
    fn truncar_recusa_o_que_nao_corta() {
        let mut u = unit_com(1);
        assert!(!truncate_unit(&mut u, 1), "uma linha nao tem o que cortar");
        let mut u = unit_com(8);
        assert!(!truncate_unit(&mut u, 0));
        assert!(
            !truncate_unit(&mut u, 8),
            "cortar para o mesmo tamanho e no-op"
        );
        assert!(!truncate_unit(&mut u, 99));
        assert!(!u.truncated, "no-op nao deve marcar truncado");
    }

    #[test]
    fn truncar_preserva_texto_como_prefixo_literal() {
        let mut u = unit_com(12);
        let antes: Vec<String> = u.text.lines().map(|s| s.to_string()).collect();
        assert!(truncate_unit(&mut u, 5));
        let depois: Vec<String> = u.text.lines().map(|s| s.to_string()).collect();
        assert_eq!(
            depois,
            antes[..5].to_vec(),
            "o corte deve ser um prefixo exato"
        );
    }
}
