// SPDX-License-Identifier: Apache-2.0
//! Snapshot: hash de conteúdo, caminhos relativos seguros e identidade da raiz.
//!
//! Duas regras do contrato vivem aqui:
//! 1. Todo `file` publicado é relativo à raiz e nunca contém `..` (§5).
//! 2. Texto só é entregue depois de re-lido e re-hasheado (§2).

use anyhow::{anyhow, Context, Result};
use sha2::{Digest, Sha256};
use std::io::Read;
use std::path::{Component, Path, PathBuf};

/// Tamanho do buffer de hash. 64 KiB é múltiplo de página e evita alocação grande por arquivo.
const HASH_BUF: usize = 64 * 1024;

/// Hash sha256 de um arquivo, lendo em blocos (não carrega o arquivo inteiro em RAM).
pub fn sha256_file(path: &Path) -> Result<String> {
    let mut f = std::fs::File::open(path)
        .with_context(|| format!("nao foi possivel abrir {}", path.display()))?;
    let mut hasher = Sha256::new();
    let mut buf = vec![0u8; HASH_BUF];
    loop {
        let n = f.read(&mut buf)?;
        if n == 0 {
            break;
        }
        hasher.update(&buf[..n]);
    }
    Ok(hex(&hasher.finalize()))
}

/// Hash sha256 de bytes já em memória (usado para geração do índice e do manifesto).
pub fn sha256_bytes(bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    hex(&hasher.finalize())
}

fn hex(digest: &[u8]) -> String {
    let mut s = String::with_capacity(digest.len() * 2);
    for b in digest {
        s.push_str(&format!("{b:02x}"));
    }
    s
}

/// Converte um caminho absoluto em caminho relativo à raiz, com separador `/`.
///
/// Devolve `None` quando o caminho escapa da raiz ou não é representável em UTF-8.
/// Componentes `.` são removidos; `..` em qualquer posição **invalida** o caminho em vez
/// de ser normalizado, porque normalizar mascararia uma tentativa de escape.
pub fn rel_path(root: &Path, abs: &Path) -> Option<String> {
    let rel = abs.strip_prefix(root).ok()?;
    let mut parts: Vec<&str> = Vec::new();
    for comp in rel.components() {
        match comp {
            Component::Normal(os) => parts.push(os.to_str()?),
            Component::CurDir => {}
            // `..`, raiz e prefixo não pertencem a um caminho relativo seguro.
            Component::ParentDir | Component::RootDir | Component::Prefix(_) => return None,
        }
    }
    if parts.is_empty() {
        return None;
    }
    Some(parts.join("/"))
}

/// Resolve um caminho relativo vindo de fora (pedido, `--ref`) contra a raiz.
///
/// Rejeita absolutos, `..`, e prefixos de Windows. O resultado é conferido contra a raiz
/// canonizada, o que cobre symlink apontando para fora — o contrato exige código 5 neste caso.
pub fn resolve_within(root: &Path, candidate: &str) -> Result<PathBuf> {
    let raw = Path::new(candidate);
    if raw.is_absolute() {
        return Err(anyhow!("caminho absoluto nao e aceito: {candidate}"));
    }
    for comp in raw.components() {
        match comp {
            Component::Normal(_) | Component::CurDir => {}
            _ => return Err(anyhow!("caminho relativo invalido: {candidate}")),
        }
    }
    let joined = root.join(raw);
    let canon_root = root
        .canonicalize()
        .with_context(|| format!("raiz inacessivel: {}", root.display()))?;
    let canon = joined
        .canonicalize()
        .with_context(|| format!("caminho inacessivel: {candidate}"))?;
    if !canon.starts_with(&canon_root) {
        return Err(anyhow!("caminho fora da raiz do repo: {candidate}"));
    }
    Ok(canon)
}

/// Identificador curto e estável da raiz do repo.
///
/// Existe para detectar índice apontando para outro checkout **sem** publicar o caminho
/// absoluto: o JSON alimenta o contexto do modelo, e repetir `/home/...` só gasta tokens
/// e expõe a máquina. O primeiro 12 caracteres do sha256 bastam para comparar.
pub fn root_id(root: &Path) -> String {
    let canon = root.canonicalize().unwrap_or_else(|_| root.to_path_buf());
    let bytes = canon.to_string_lossy();
    sha256_bytes(bytes.as_bytes())[..12].to_string()
}

/// Lê um arquivo como texto tolerante a UTF-8 inválido.
///
/// Bytes inválidos viram U+FFFD em vez de erro: código-fonte legado em latin-1 deve ser
/// indexável, e o hash publicado continua sendo o do arquivo cru.
pub fn read_text(path: &Path) -> Result<String> {
    let raw = std::fs::read(path).with_context(|| format!("falha ao ler {}", path.display()))?;
    Ok(String::from_utf8_lossy(&raw).into_owned())
}

/// Detecta conteúdo binário pela presença de NUL nos primeiros 8 KiB.
///
/// Heurística declarada, não classificador: é a mesma que ferramentas de busca usam, e o
/// viés é conhecido (texto UTF-16 aparece como binário). Arquivos assim são contados e
/// reportados, nunca descartados em silêncio.
pub fn is_binary(sample: &[u8]) -> bool {
    sample.iter().take(8192).any(|b| *b == 0)
}

/// SHA abreviado do HEAD do git, quando existir.
///
/// Usa `git` como subprocesso — não é Python, e é a forma confiável de resolver branch,
/// worktree e `detached HEAD`. Falha aqui **não** é erro fatal: um repo sem git continua
/// indexável e o `sha_base` sai `null` com o motivo registrado, em vez de inventar valor.
pub fn git_sha(root: &Path) -> Option<String> {
    let out = std::process::Command::new("git")
        .arg("-C")
        .arg(root)
        .args(["rev-parse", "--short", "HEAD"])
        .output()
        .ok()?;
    if !out.status.success() {
        return None;
    }
    let sha = String::from_utf8_lossy(&out.stdout).trim().to_string();
    if sha.is_empty() {
        None
    } else {
        Some(sha)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rel_path_rejeita_escape_e_absoluto() {
        let root = Path::new("/repo");
        assert_eq!(
            rel_path(root, Path::new("/repo/a/b.java")).as_deref(),
            Some("a/b.java")
        );
        assert_eq!(
            rel_path(root, Path::new("/repo/./a/b.java")).as_deref(),
            Some("a/b.java")
        );
        assert_eq!(rel_path(root, Path::new("/repo/../etc/passwd")), None);
        assert_eq!(rel_path(root, Path::new("/outro/a.java")), None);
        assert_eq!(rel_path(root, Path::new("/repo")), None);
    }

    #[test]
    fn resolve_within_nega_absoluto_e_parent() {
        let tmp = std::env::temp_dir().join(format!("atlas-snap-{}", std::process::id()));
        std::fs::create_dir_all(&tmp).unwrap();
        std::fs::write(tmp.join("ok.java"), b"class A {}").unwrap();
        assert!(resolve_within(&tmp, "ok.java").is_ok());
        assert!(resolve_within(&tmp, "/etc/passwd").is_err());
        assert!(resolve_within(&tmp, "../x").is_err());
        assert!(resolve_within(&tmp, "nao_existe.java").is_err());
        std::fs::remove_dir_all(&tmp).ok();
    }

    #[test]
    fn root_id_e_estavel_e_nao_vaza_caminho() {
        let tmp = std::env::temp_dir();
        let a = root_id(&tmp);
        let b = root_id(&tmp);
        assert_eq!(a, b);
        assert_eq!(a.len(), 12);
        assert!(!a.contains('/'));
    }

    #[test]
    fn detecta_binario_e_texto() {
        assert!(!is_binary(b"public class A {}"));
        assert!(is_binary(&[0x50, 0x4b, 0x00, 0x01]));
    }

    #[test]
    fn sha256_bytes_confere_com_vetor_conhecido() {
        // SHA-256 de "abc" — valor publicado, serve de âncora contra regressão de hex().
        assert_eq!(
            sha256_bytes(b"abc"),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        );
    }
}
