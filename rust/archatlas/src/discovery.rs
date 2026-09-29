// SPDX-License-Identifier: Apache-2.0
//! Descoberta de arquivos: respeita exclusões, classifica e **conta** o que descarta.
//!
//! Nada é descartado em silêncio. Arquivo binário, grande demais ou fora da cobertura
//! declarada vira contagem publicada em `index`/`doctor`, porque o plano proíbe cumprir
//! meta de tempo ou memória ignorando arquivos sem registrar.

use crate::languages;
use crate::snapshot::{is_binary, rel_path};
use anyhow::{Context, Result};
use ignore::WalkBuilder;
use std::path::{Path, PathBuf};

/// Limite padrão por arquivo. Acima disto o arquivo é **contado** como `too_large` e não indexado.
pub const DEFAULT_MAX_FILE_BYTES: u64 = 2 * 1024 * 1024;

/// Diretórios de build/vendor que não têm valor de contexto e inflam o índice.
const PRUNE_DIRS: &[&str] = &["target", "node_modules", "dist", "build", ".venv"];

/// Um arquivo elegível, já classificado.
#[derive(Debug, Clone)]
pub struct Discovered {
    pub abs: PathBuf,
    pub rel: String,
    pub lang: &'static str,
    pub size: u64,
}

/// Resultado da varredura, com os descartes contabilizados.
#[derive(Debug, Default)]
pub struct Discovery {
    pub files: Vec<Discovered>,
    pub unsupported: u64,
    /// Reconhecido, mas fora do filtro `--include`. Contado, nunca descartado em silêncio.
    pub excluded_by_filter: u64,
    pub binary: u64,
    pub too_large: u64,
    pub unreadable: u64,
    /// `None` = não medido. O walker poda entradas ignoradas antes de reportá-las, então
    /// contar exigiria uma segunda varredura sem filtro. Reportamos `null` com motivo em
    /// vez de publicar um número que não medimos.
    pub ignored: Option<u64>,
}

impl Discovery {
    pub fn ignored_reason() -> &'static str {
        "walker poda entradas ignoradas antes de reportar; contagem exigiria varredura sem filtro"
    }
}

/// Varre `root` e devolve os arquivos elegíveis em ordem determinística.
///
/// `exclude_abs` recebe caminhos que nunca devem ser indexados — tipicamente o próprio
/// arquivo de índice quando o operador o coloca dentro do repo.
///
/// `include` restringe a cobertura a essas linguagens; vazio significa todas as
/// reconhecidas. O filtro existe para que seja possível indexar **exatamente** o mesmo
/// conjunto de arquivos que outra ferramenta, condição para comparar duas implementações
/// sem que a diferença de corpus se disfarce de diferença de desempenho.
pub fn discover(
    root: &Path,
    max_file_bytes: u64,
    exclude_abs: &[PathBuf],
    include: &[String],
) -> Result<Discovery> {
    let mut builder = WalkBuilder::new(root);
    // `hidden(true)` = pula dotfiles (inclui `.git`); gitignore/global/exclude ligados
    // reproduzem o comportamento de ferramentas de busca que o agente já usa.
    builder
        .hidden(true)
        .git_ignore(true)
        .git_global(true)
        .git_exclude(true)
        .parents(false)
        .follow_links(false)
        .require_git(false);

    let exclude_canon: Vec<PathBuf> = exclude_abs
        .iter()
        .map(|p| p.canonicalize().unwrap_or_else(|_| p.clone()))
        .collect();

    let mut out = Discovery {
        ignored: None,
        ..Default::default()
    };

    for entry in builder.build() {
        let entry = match entry {
            Ok(e) => e,
            // Erro de permissão num arquivo não deve derrubar a varredura inteira.
            Err(_) => {
                out.unreadable += 1;
                continue;
            }
        };
        if !entry.file_type().map(|t| t.is_file()).unwrap_or(false) {
            continue;
        }
        let abs = entry.path().to_path_buf();

        // Podas explícitas: o índice não pode engolir o próprio diretório de build nem a si mesmo.
        if abs.components().any(|c| {
            c.as_os_str()
                .to_str()
                .map(|s| PRUNE_DIRS.contains(&s))
                .unwrap_or(false)
        }) {
            continue;
        }
        let canon = abs.canonicalize().unwrap_or_else(|_| abs.clone());
        if exclude_canon.contains(&canon) {
            continue;
        }

        let Some(rel) = rel_path(root, &abs) else {
            continue;
        };
        let Some(lang) = languages::classify(&abs) else {
            out.unsupported += 1;
            continue;
        };
        if !include.is_empty() && !include.iter().any(|l| l == lang) {
            out.excluded_by_filter += 1;
            continue;
        }
        let size = entry.metadata().map(|m| m.len()).unwrap_or(0);
        if size > max_file_bytes {
            out.too_large += 1;
            continue;
        }
        // Amostra só para decidir binário; o índice lê o arquivo de novo depois.
        let sample = std::fs::read(&abs)
            .with_context(|| format!("falha ao amostrar {}", rel))
            .unwrap_or_default();
        if is_binary(&sample) {
            out.binary += 1;
            continue;
        }

        out.files.push(Discovered {
            abs,
            rel,
            lang,
            size,
        });
    }

    // Ordem estável: o índice, a geração e os testes dependem disto.
    out.files.sort_by(|a, b| a.rel.cmp(&b.rel));
    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn tmpdir(tag: &str) -> PathBuf {
        let d = std::env::temp_dir().join(format!("atlas-disc-{tag}-{}", std::process::id()));
        let _ = std::fs::remove_dir_all(&d);
        std::fs::create_dir_all(&d).unwrap();
        d
    }

    #[test]
    fn descobre_e_classifica_em_ordem() {
        let d = tmpdir("ordem");
        std::fs::create_dir_all(d.join("sub")).unwrap();
        std::fs::write(d.join("b.java"), b"class B {}").unwrap();
        std::fs::write(d.join("sub/a.java"), b"class A {}").unwrap();
        std::fs::write(d.join("nota.md"), b"# nota").unwrap();

        let got = discover(&d, DEFAULT_MAX_FILE_BYTES, &[], &[]).unwrap();
        let rels: Vec<&str> = got.files.iter().map(|f| f.rel.as_str()).collect();
        assert_eq!(rels, vec!["b.java", "nota.md", "sub/a.java"]);
        std::fs::remove_dir_all(&d).ok();
    }

    #[test]
    fn filtro_include_restaura_corpus_exato() {
        let d = tmpdir("include");
        std::fs::write(d.join("a.java"), b"class A {}").unwrap();
        std::fs::write(d.join("b.properties"), b"x=1").unwrap();
        std::fs::write(d.join("c.xml"), b"<a/>").unwrap();

        let so_java = discover(&d, DEFAULT_MAX_FILE_BYTES, &[], &["java".to_string()]).unwrap();
        let rels: Vec<&str> = so_java.files.iter().map(|f| f.rel.as_str()).collect();
        assert_eq!(rels, vec!["a.java"], "o filtro deve excluir o resto");
        // Excluído pelo filtro é contado, para não virar descarte silencioso.
        assert_eq!(so_java.excluded_by_filter, 2);
        assert_eq!(so_java.unsupported, 0);

        let tudo = discover(&d, DEFAULT_MAX_FILE_BYTES, &[], &[]).unwrap();
        assert_eq!(tudo.files.len(), 3);
        std::fs::remove_dir_all(&d).ok();
    }

    #[test]
    fn descarta_e_conta_binario_desconhecido_e_grande() {
        let d = tmpdir("descarte");
        std::fs::write(d.join("ok.java"), b"class Ok {}").unwrap();
        std::fs::write(d.join("bin.java"), b"class B {}\x00\x01\x02").unwrap();
        std::fs::write(d.join("x.unknownext"), b"generico").unwrap();
        std::fs::write(d.join("grande.java"), vec![b'a'; 4096]).unwrap();

        let got = discover(&d, 1024, &[], &[]).unwrap();
        assert_eq!(got.files.len(), 1);
        assert_eq!(got.files[0].rel, "ok.java");
        assert_eq!(got.binary, 1);
        assert_eq!(got.unsupported, 1);
        assert_eq!(got.too_large, 1);
        assert!(got.ignored.is_none());
        std::fs::remove_dir_all(&d).ok();
    }

    #[test]
    fn exclui_diretorios_de_build_e_o_proprio_indice() {
        let d = tmpdir("exclui");
        std::fs::create_dir_all(d.join("target")).unwrap();
        std::fs::write(d.join("target/gen.java"), b"class G {}").unwrap();
        std::fs::write(d.join("i.sqlite"), b"").unwrap();
        std::fs::write(d.join("ok.java"), b"class Ok {}").unwrap();

        let excl = vec![d.join("i.sqlite")];
        let got = discover(&d, DEFAULT_MAX_FILE_BYTES, &excl, &[]).unwrap();
        let rels: Vec<&str> = got.files.iter().map(|f| f.rel.as_str()).collect();
        assert_eq!(
            rels,
            vec!["ok.java"],
            "target/ e o proprio indice devem sair"
        );
        std::fs::remove_dir_all(&d).ok();
    }
}
