// SPDX-License-Identifier: Apache-2.0
//! Capacidades por linguagem, declaradas sem prometer mais do que R1 entrega.
//!
//! R1 é **lexical**: indexa e busca texto, sem extrair símbolos nem resolver tipos.
//! A referência Python declara Java como `structural` porque tem um extrator por regex
//! auditado; esta fatia Rust **não** tem esse extrator, então declara `lexical` para tudo.
//! Declarar `structural` aqui seria a mesma troca de rótulo que a auditoria já condenou.

use std::path::Path;

/// Nível de capacidade. Congelado em R1; `structural` só entra com extrator medido.
pub const LEXICAL: &str = "lexical";

/// Linguagens que a descoberta reconhece como texto indexável.
///
/// Ordem determinística (alfabética) — `doctor` publica esta lista e o runner pode
/// comparar entre versões. Cada entrada é `(linguagem, extensões)`.
pub const RECOGNIZED: &[(&str, &[&str])] = &[
    ("c", &["c", "h"]),
    ("config", &["cfg", "conf", "ini", "properties"]),
    ("cpp", &["cc", "cpp", "cxx", "hh", "hpp", "hxx"]),
    ("java", &["java"]),
    ("javascript", &["cjs", "js", "jsx", "mjs", "ts", "tsx"]),
    ("json", &["json"]),
    ("markdown", &["markdown", "md"]),
    ("markup", &["htm", "html", "jsp", "xhtml", "xml"]),
    ("python", &["py", "pyi"]),
    ("rust", &["rs"]),
    ("shell", &["bash", "sh"]),
    ("sql", &["sql"]),
    ("toml", &["toml"]),
    ("yaml", &["yaml", "yml"]),
];

/// Classifica um caminho pela extensão. `None` significa "fora da cobertura declarada".
///
/// Não usa o conteúdo: classificar por heurística de conteúdo tornaria o índice
/// dependente de leitura prévia e mudaria com o arquivo, quebrando o determinismo.
pub fn classify(path: &Path) -> Option<&'static str> {
    let ext = path.extension()?.to_str()?.to_ascii_lowercase();
    RECOGNIZED
        .iter()
        .find(|(_, exts)| exts.contains(&ext.as_str()))
        .map(|(lang, _)| *lang)
}

/// Nível e nota de suporte para uma linguagem classificada.
pub fn support(lang: &str) -> (&'static str, &'static str) {
    if RECOGNIZED.iter().any(|(l, _)| *l == lang) {
        (
            LEXICAL,
            "busca textual com trecho verificado; sem extrator de simbolos em R1",
        )
    } else {
        (
            LEXICAL,
            "cobertura textual generica; linguagem nao declarada",
        )
    }
}

/// Todas as linguagens reconhecidas, com o suporte declarado. Usado por `doctor`.
pub fn declared() -> Vec<(&'static str, &'static str, &'static str)> {
    RECOGNIZED
        .iter()
        .map(|(lang, _)| {
            let (level, note) = support(lang);
            (*lang, level, note)
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    #[test]
    fn classifica_extensoes_conhecidas() {
        assert_eq!(
            classify(&PathBuf::from("a/b/ExMovimentacao.java")),
            Some("java")
        );
        assert_eq!(classify(&PathBuf::from("x.PY")), Some("python"));
        assert_eq!(classify(&PathBuf::from("x.yaml")), Some("yaml"));
        assert_eq!(classify(&PathBuf::from("x.yml")), Some("yaml"));
    }

    #[test]
    fn rejeita_desconhecidas_e_sem_extensao() {
        assert_eq!(classify(&PathBuf::from("Makefile")), None);
        assert_eq!(classify(&PathBuf::from("a.bin")), None);
        assert_eq!(classify(&PathBuf::from("sem_ponto")), None);
    }

    #[test]
    fn r1_nao_declara_estrutural() {
        // Guarda contra regressão de rótulo: se alguém promover Java a `structural`
        // sem extrator, este teste falha e obriga a discutir a alegação.
        for (_, level, _) in declared() {
            assert_eq!(level, LEXICAL);
        }
    }

    #[test]
    fn lista_declarada_e_ordenada_e_sem_duplicata() {
        let langs: Vec<&str> = declared().iter().map(|(l, _, _)| *l).collect();
        let mut sorted = langs.clone();
        sorted.sort_unstable();
        sorted.dedup();
        assert_eq!(langs, sorted);
    }
}
