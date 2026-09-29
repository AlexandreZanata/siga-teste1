// SPDX-License-Identifier: Apache-2.0
//! Índice SQLite com schema próprio versionado e geração consistente.
//!
//! Decisões herdadas do plano (§3) e materializadas aqui:
//! - **Um escritor por índice**: a escrita acontece numa única conexão, numa transação.
//! - **Leitores não misturam gerações**: `journal_mode=WAL` dá isolamento de snapshot.
//! - **Schema próprio**: nunca abre nem migra o DB da referência Python.
//! - **Incremental ≡ rebuild**: a geração é função do conjunto de `(path, hash)`, então
//!   atualizar em passos e reconstruir do zero produzem o mesmo estado lógico.

use crate::discovery::Discovered;
use crate::snapshot::{read_text, sha256_bytes, sha256_file};
use anyhow::{Context, Result};
use rusqlite::{params, Connection, OpenFlags};
use std::path::{Path, PathBuf};
use std::time::Duration;

/// Versão do schema do índice. Vive em `PRAGMA user_version`.
pub const INDEX_SCHEMA_VERSION: i64 = 1;

/// Schema da geração 1: metadados, arquivos e corpo textual para busca FTS5.
const SCHEMA: &str = r#"
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS files(
    path TEXT PRIMARY KEY,
    content_hash TEXT NOT NULL,
    size INTEGER NOT NULL,
    lang TEXT NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(path UNINDEXED, body, tokenize='porter');
"#;

/// Estado do índice, na forma que `doctor` publica.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum IndexState {
    Ok,
    Missing,
    Corrupt,
    Incompatible,
    Empty,
}

impl IndexState {
    pub fn as_str(self) -> &'static str {
        match self {
            IndexState::Ok => "ok",
            IndexState::Missing => "missing",
            IndexState::Corrupt => "corrupt",
            IndexState::Incompatible => "incompatible",
            IndexState::Empty => "empty",
        }
    }

    /// Conselho de recuperação. Índice indisponível nunca deve parecer resposta vazia.
    pub fn advice(self) -> Option<&'static str> {
        match self {
            IndexState::Ok => None,
            IndexState::Missing => {
                Some("rode `archatlas index`; ou use leitura e busca diretas no repo")
            }
            IndexState::Empty => {
                Some("indice sem arquivos; rode `archatlas index` na raiz correta")
            }
            IndexState::Corrupt => {
                Some("arquivo nao e um indice valido; apague o indice e reindexe")
            }
            IndexState::Incompatible => {
                Some("versao de schema divergente; reindexe do zero com esta versao")
            }
        }
    }

    /// Só `ok` permite responder `context`; todo o resto bloqueia com código 3.
    pub fn can_serve(self) -> bool {
        matches!(self, IndexState::Ok)
    }
}

/// Modo de indexação pedido na linha de comando.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Mode {
    /// Atualiza em passos: reaproveita o que já está no índice e remove o que sumiu.
    Incremental,
    /// Descarta o conteúdo e reconstrói do zero.
    Rebuild,
}

impl Mode {
    pub fn as_str(self) -> &'static str {
        match self {
            Mode::Incremental => "incremental",
            Mode::Rebuild => "rebuild",
        }
    }
}

/// Armazém aberto para escrita.
pub struct Store {
    pub conn: Connection,
    path: PathBuf,
}

/// Leitura do índice **somente leitura**, para `doctor` e para carimbar respostas.
///
/// Existe separado de [`Store::open`] de propósito: `Store::open` garante o schema e
/// portanto **escreve**. `doctor` precisa diagnosticar sem tocar no arquivo, inclusive
/// quando ele está em disco somente leitura ou pertence a outro usuário.
#[derive(Debug, Clone)]
pub struct IndexSnapshot {
    pub state: IndexState,
    pub files: Option<u64>,
    pub generation: Option<String>,
    pub sha_base: Option<String>,
    /// `None` quando não dá para comparar (índice vazio ou sem marca de raiz).
    pub root_matches: Option<bool>,
}

/// Inspeciona o índice sem escrever nada. Nunca cria o arquivo.
pub fn inspect(path: &Path, repo: Option<&Path>) -> IndexSnapshot {
    let state = probe(path);
    let mut out = IndexSnapshot {
        state,
        files: None,
        generation: None,
        sha_base: None,
        root_matches: None,
    };
    if !matches!(state, IndexState::Ok | IndexState::Empty) {
        return out;
    }
    let Ok(conn) = Connection::open_with_flags(
        path,
        OpenFlags::SQLITE_OPEN_READ_ONLY | OpenFlags::SQLITE_OPEN_NO_MUTEX,
    ) else {
        return out;
    };
    let read_meta = |key: &str| -> Option<String> {
        conn.query_row("SELECT value FROM meta WHERE key=?1", [key], |r| {
            r.get::<_, String>(0)
        })
        .ok()
    };
    out.files = conn
        .query_row("SELECT COUNT(*) FROM files", [], |r| r.get::<_, i64>(0))
        .ok()
        .map(|n| n as u64);
    out.generation = read_meta("generation");
    out.sha_base = read_meta("sha_base").filter(|v| !v.is_empty());
    if let (Some(r), Some(stored)) = (repo, read_meta("root_id")) {
        out.root_matches = Some(crate::snapshot::root_id(r) == stored);
    }
    out
}

/// Estado lógico publicado depois de uma indexação.
#[derive(Debug, Clone)]
pub struct SyncReport {
    pub mode: &'static str,
    pub indexed: u64,
    pub skipped: u64,
    pub pruned_files: u64,
    pub generation: String,
    pub sha_base: Option<String>,
    pub total_files: u64,
}

/// Sonda o índice sem criar nada. Distingue ausente, corrompido, incompatível e vazio.
pub fn probe(path: &Path) -> IndexState {
    if !path.exists() {
        return IndexState::Missing;
    }
    let Ok(conn) = Connection::open_with_flags(
        path,
        OpenFlags::SQLITE_OPEN_READ_ONLY | OpenFlags::SQLITE_OPEN_NO_MUTEX,
    ) else {
        return IndexState::Corrupt;
    };
    let tables: rusqlite::Result<Vec<String>> = {
        let mut stmt = match conn.prepare("SELECT name FROM sqlite_master WHERE type='table'") {
            Ok(s) => s,
            Err(_) => return IndexState::Corrupt,
        };
        stmt.query_map([], |r| r.get::<_, String>(0))
            .and_then(|rows| rows.collect())
    };
    let Ok(tables) = tables else {
        return IndexState::Corrupt;
    };
    // As tabelas do índice precisam existir; um SQLite válido de outro produto não serve.
    for required in ["meta", "files"] {
        if !tables.iter().any(|t| t == required) {
            return IndexState::Corrupt;
        }
    }
    let version: i64 = match conn.pragma_query_value(None, "user_version", |r| r.get(0)) {
        Ok(v) => v,
        Err(_) => return IndexState::Corrupt,
    };
    if version != INDEX_SCHEMA_VERSION {
        return IndexState::Incompatible;
    }
    match conn.query_row("SELECT COUNT(*) FROM files", [], |r| r.get::<_, i64>(0)) {
        Ok(0) => IndexState::Empty,
        Ok(_) => IndexState::Ok,
        Err(_) => IndexState::Corrupt,
    }
}

impl Store {
    /// Abre (criando se preciso) e garante o schema. Exige que o diretório exista.
    pub fn open(path: &Path) -> Result<Store> {
        if let Some(parent) = path.parent() {
            if !parent.as_os_str().is_empty() && !parent.exists() {
                return Err(anyhow::anyhow!(
                    "diretorio do indice nao existe: {}",
                    parent.display()
                ));
            }
        }
        let conn = Connection::open(path)
            .with_context(|| format!("nao foi possivel abrir o indice {}", path.display()))?;
        // WAL dá isolamento de leitura durante escrita; se o filesystem recusar, seguimos
        // no modo padrão em vez de falhar a indexação por um detalhe de performance.
        let _ = conn.query_row("PRAGMA journal_mode=WAL", [], |r| r.get::<_, String>(0));
        conn.execute_batch("PRAGMA synchronous=NORMAL;")?;
        conn.busy_timeout(Duration::from_millis(5000))?;
        conn.execute_batch(SCHEMA)?;
        conn.pragma_update(None, "user_version", INDEX_SCHEMA_VERSION)?;
        Ok(Store {
            conn,
            path: path.to_path_buf(),
        })
    }

    /// Abre o índice em **somente leitura**, sem garantir schema e sem criar arquivo.
    ///
    /// Usado por `context`: responder não pode escrever no índice, nem para "consertar"
    /// o schema. Reindexar é `index`, pedido explicitamente pelo operador.
    pub fn open_readonly(path: &Path) -> Result<Store> {
        let conn = Connection::open_with_flags(
            path,
            OpenFlags::SQLITE_OPEN_READ_ONLY | OpenFlags::SQLITE_OPEN_NO_MUTEX,
        )
        .with_context(|| format!("nao foi possivel abrir o indice {}", path.display()))?;
        conn.busy_timeout(Duration::from_millis(5000))?;
        Ok(Store {
            conn,
            path: path.to_path_buf(),
        })
    }

    pub fn path(&self) -> &Path {
        &self.path
    }

    pub fn meta(&self, key: &str) -> Result<Option<String>> {
        let mut stmt = self.conn.prepare("SELECT value FROM meta WHERE key=?1")?;
        let mut rows = stmt.query(params![key])?;
        Ok(match rows.next()? {
            Some(row) => Some(row.get::<_, String>(0)?),
            None => None,
        })
    }

    fn set_meta(&self, key: &str, value: &str) -> Result<()> {
        self.conn.execute(
            "INSERT INTO meta(key, value) VALUES (?1, ?2)
             ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            params![key, value],
        )?;
        Ok(())
    }

    /// Geração atual gravada no índice (`null` se nunca indexado).
    pub fn generation(&self) -> Result<Option<String>> {
        self.meta("generation")
    }

    /// Pares `(path, hash)` ordenados. É o estado lógico usado nos testes de equivalência.
    pub fn logical_dump(&self) -> Result<Vec<(String, String)>> {
        let mut stmt = self
            .conn
            .prepare("SELECT path, content_hash FROM files ORDER BY path")?;
        let rows = stmt.query_map([], |r| Ok((r.get::<_, String>(0)?, r.get::<_, String>(1)?)))?;
        Ok(rows.collect::<rusqlite::Result<Vec<_>>>()?)
    }

    pub fn file_count(&self) -> Result<u64> {
        Ok(self
            .conn
            .query_row("SELECT COUNT(*) FROM files", [], |r| r.get::<_, i64>(0))? as u64)
    }

    /// Descarta o conteúdo para reconstruir do zero, preservando o arquivo e o schema.
    fn reset(&mut self) -> Result<()> {
        self.conn.execute_batch(
            "DROP TABLE IF EXISTS docs;
             DROP TABLE IF EXISTS files;
             DELETE FROM meta;
             CREATE TABLE IF NOT EXISTS files(
                 path TEXT PRIMARY KEY,
                 content_hash TEXT NOT NULL,
                 size INTEGER NOT NULL,
                 lang TEXT NOT NULL
             );
             CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(path UNINDEXED, body, tokenize='porter');",
        )?;
        Ok(())
    }

    /// Sincroniza o índice com o disco.
    ///
    /// Três fases, com o paralelismo onde ele paga e a escrita onde ela é segura:
    /// 1. hash de todos os arquivos, em paralelo (streaming, RAM baixa);
    /// 2. leitura e escrita dos que mudaram, uma transação, uma conexão;
    /// 3. poda dos paths que sumiram do disco.
    pub fn sync(
        &mut self,
        discovered: &[Discovered],
        sha_base: Option<&str>,
        root_id: &str,
        mode: Mode,
        workers: usize,
    ) -> Result<SyncReport> {
        if mode == Mode::Rebuild {
            self.reset()?;
        }

        // --- Fase 1: hash paralelo -------------------------------------------------
        let hashes: Vec<(String, String, u64, &'static str, PathBuf)> = {
            use rayon::prelude::*;
            let work = |f: &Discovered| -> (String, String, u64, &'static str, PathBuf) {
                // Hash por streaming: o arquivo inteiro não entra em RAM aqui.
                let hash = sha256_file(&f.abs).unwrap_or_default();
                (f.rel.clone(), hash, f.size, f.lang, f.abs.clone())
            };
            if workers > 1 {
                let pool = rayon::ThreadPoolBuilder::new()
                    .num_threads(workers)
                    .build()
                    .context("nao foi possivel criar o pool de workers")?;
                pool.install(|| discovered.par_iter().map(work).collect())
            } else {
                discovered.iter().map(work).collect()
            }
        };

        // --- Fase 2: escrita serial -------------------------------------------------
        let mut indexed = 0u64;
        let mut skipped = 0u64;
        {
            let tx = self.conn.transaction()?;
            {
                // Statements preparados uma vez. Preparar dentro do laço custava uma
                // compilação de SQL por arquivo.
                let mut sel = tx.prepare_cached("SELECT content_hash FROM files WHERE path=?1")?;
                let mut del_docs = tx.prepare_cached("DELETE FROM docs WHERE path=?1")?;
                let mut del_files = tx.prepare_cached("DELETE FROM files WHERE path=?1")?;
                let mut ins_files = tx.prepare_cached(
                    "INSERT INTO files(path, content_hash, size, lang) VALUES (?1,?2,?3,?4)",
                )?;
                let mut ins_docs =
                    tx.prepare_cached("INSERT INTO docs(path, body) VALUES (?1, ?2)")?;

                for (rel, hash, size, lang, abs) in &hashes {
                    let existing: Option<String> = {
                        let mut rows = sel.query(params![rel])?;
                        rows.next()?.map(|r| r.get::<_, String>(0)).transpose()?
                    };
                    if existing.as_deref() == Some(hash.as_str()) {
                        // Conteúdo idêntico: nada a reescrever. É o ganho real do incremental.
                        skipped += 1;
                        continue;
                    }
                    let body = read_text(abs).unwrap_or_default();
                    // O DELETE só é necessário se a linha existe. `docs` é FTS5 com `path`
                    // UNINDEXED, então apagar varre a tabela inteira: fazer isso num índice
                    // novo custava O(n²) — medido em 110s para 6.916 arquivos contra 0,32s
                    // nos mesmos 511 arquivos Java quando o DELETE é evitado.
                    if existing.is_some() {
                        del_docs.execute(params![rel])?;
                        del_files.execute(params![rel])?;
                    }
                    ins_files.execute(params![rel, hash, *size as i64, *lang])?;
                    ins_docs.execute(params![rel, body])?;
                    indexed += 1;
                }
            }
            tx.commit()?;
        }

        // --- Fase 3: poda do que sumiu (delete e rename caem aqui) -------------------
        let desired: std::collections::HashSet<&str> =
            hashes.iter().map(|(rel, ..)| rel.as_str()).collect();
        let stored: Vec<String> = {
            let mut stmt = self.conn.prepare("SELECT path FROM files ORDER BY path")?;
            let rows = stmt.query_map([], |r| r.get::<_, String>(0))?;
            rows.collect::<rusqlite::Result<Vec<_>>>()?
        };
        let gone: Vec<String> = stored
            .into_iter()
            .filter(|p| !desired.contains(p.as_str()))
            .collect();
        if !gone.is_empty() {
            let tx = self.conn.transaction()?;
            for p in &gone {
                tx.execute("DELETE FROM docs WHERE path=?1", params![p])?;
                tx.execute("DELETE FROM files WHERE path=?1", params![p])?;
            }
            tx.commit()?;
        }

        // --- Fase 4: geração e metadados --------------------------------------------
        let generation = generation_of(&hashes);
        let total = hashes.len() as u64;
        self.set_meta("generation", &generation)?;
        self.set_meta("sha_base", sha_base.unwrap_or(""))?;
        self.set_meta("root_id", root_id)?;
        self.set_meta("tool_version", crate::TOOL_VERSION)?;
        self.set_meta("index_schema_version", &INDEX_SCHEMA_VERSION.to_string())?;
        self.conn.execute_batch("PRAGMA optimize;")?;

        Ok(SyncReport {
            mode: mode.as_str(),
            indexed,
            skipped,
            pruned_files: gone.len() as u64,
            generation,
            sha_base: sha_base.map(|s| s.to_string()),
            total_files: total,
        })
    }
}

/// Geração = sha256 do conjunto ordenado de `(path, hash)`.
///
/// É independente da ordem de escrita e do modo (incremental ou rebuild), o que é
/// exatamente o que torna a equivalência lógica verificável por igualdade de string.
fn generation_of(hashes: &[(String, String, u64, &'static str, PathBuf)]) -> String {
    let mut lines: Vec<&(String, String, u64, &'static str, PathBuf)> = hashes.iter().collect();
    lines.sort_by(|a, b| a.0.cmp(&b.0));
    let mut buf = String::new();
    for (rel, hash, size, lang, _) in lines {
        buf.push_str(rel);
        buf.push('\u{0}');
        buf.push_str(hash);
        buf.push('\u{0}');
        buf.push_str(&size.to_string());
        buf.push('\u{0}');
        buf.push_str(lang);
        buf.push('\n');
    }
    sha256_bytes(buf.as_bytes())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    fn tmpdir(tag: &str) -> PathBuf {
        let d = std::env::temp_dir().join(format!("atlas-store-{tag}-{}", std::process::id()));
        let _ = std::fs::remove_dir_all(&d);
        std::fs::create_dir_all(&d).unwrap();
        d
    }

    fn disc(root: &Path, name: &str) -> Discovered {
        let abs = root.join(name);
        Discovered {
            rel: name.to_string(),
            abs,
            lang: "java",
            size: std::fs::metadata(root.join(name))
                .map(|m| m.len())
                .unwrap_or(0),
        }
    }

    #[test]
    fn probe_distingue_ausente_corrompido_incompativel_e_vazio() {
        let d = tmpdir("probe");
        assert_eq!(probe(&d.join("nope.sqlite")), IndexState::Missing);

        let bad = d.join("bad.sqlite");
        std::fs::write(&bad, b"nao sou sqlite").unwrap();
        assert_eq!(probe(&bad), IndexState::Corrupt);

        let other = d.join("other.sqlite");
        let c = Connection::open(&other).unwrap();
        c.execute_batch("CREATE TABLE x(a INTEGER); PRAGMA user_version=99;")
            .unwrap();
        drop(c);
        // SQLite válido, mas sem as tabelas do índice: corrompido do ponto de vista do produto.
        assert_eq!(probe(&other), IndexState::Corrupt);

        let empty = d.join("empty.sqlite");
        {
            let s = Store::open(&empty).unwrap();
            assert_eq!(s.file_count().unwrap(), 0);
        }
        assert_eq!(probe(&empty), IndexState::Empty);

        std::fs::remove_dir_all(&d).ok();
    }

    #[test]
    fn rebuild_e_incremental_produzem_a_mesma_geracao() {
        let d = tmpdir("ger");
        std::fs::write(d.join("a.java"), b"class A {}").unwrap();
        std::fs::write(d.join("b.java"), b"class B {}").unwrap();
        let files = vec![disc(&d, "a.java"), disc(&d, "b.java")];

        let inc = d.join("inc.sqlite");
        let mut s = Store::open(&inc).unwrap();
        let r1 = s
            .sync(&files, Some("e3be22828"), "root", Mode::Incremental, 1)
            .unwrap();
        drop(s);

        // Segunda passada: nada mudou, tudo reutilizado.
        let mut s = Store::open(&inc).unwrap();
        let r2 = s
            .sync(&files, Some("e3be22828"), "root", Mode::Incremental, 1)
            .unwrap();
        assert_eq!(r2.indexed, 0);
        assert_eq!(r2.skipped, 2);
        drop(s);

        let reb = d.join("reb.sqlite");
        let mut s = Store::open(&reb).unwrap();
        let r3 = s
            .sync(&files, Some("e3be22828"), "root", Mode::Rebuild, 1)
            .unwrap();
        drop(s);

        assert_eq!(r1.generation, r2.generation);
        assert_eq!(
            r1.generation, r3.generation,
            "reconstruir deve dar a mesma geracao"
        );

        std::fs::remove_dir_all(&d).ok();
    }

    #[test]
    fn incremental_equivale_a_rebuild_apos_edicao_delete_e_rename() {
        let d = tmpdir("equiv");
        std::fs::write(d.join("a.java"), b"class A {}").unwrap();
        std::fs::write(d.join("b.java"), b"class B {}").unwrap();
        std::fs::write(d.join("c.java"), b"class C {}").unwrap();

        let inc = d.join("inc.sqlite");
        let mut s = Store::open(&inc).unwrap();
        s.sync(
            &[disc(&d, "a.java"), disc(&d, "b.java"), disc(&d, "c.java")],
            Some("sha1"),
            "root",
            Mode::Incremental,
            1,
        )
        .unwrap();
        drop(s);

        // Mutação: edita a, apaga b, renomeia c -> z
        std::fs::write(d.join("a.java"), b"class A { int x; }").unwrap();
        std::fs::remove_file(d.join("b.java")).unwrap();
        std::fs::rename(d.join("c.java"), d.join("z.java")).unwrap();

        let after = vec![disc(&d, "a.java"), disc(&d, "z.java")];
        let mut s = Store::open(&inc).unwrap();
        let r = s
            .sync(&after, Some("sha1"), "root", Mode::Incremental, 2)
            .unwrap();
        assert_eq!(r.indexed, 2, "a mudou e z e novo");
        assert_eq!(r.pruned_files, 2, "b sumiu e c virou z");
        let dump_inc = s.logical_dump().unwrap();
        let gen_inc = r.generation;
        drop(s);

        let reb = d.join("reb.sqlite");
        let mut s = Store::open(&reb).unwrap();
        let r2 = s
            .sync(&after, Some("sha1"), "root", Mode::Rebuild, 1)
            .unwrap();
        let dump_reb = s.logical_dump().unwrap();
        drop(s);

        assert_eq!(dump_inc, dump_reb);
        assert_eq!(gen_inc, r2.generation);

        std::fs::remove_dir_all(&d).ok();
    }
}
