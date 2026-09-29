// SPDX-License-Identifier: Apache-2.0
//! Testes de R2: `expand`, `verify` e o filtro de corpus `--include`.
//!
//! Separados de `contract.rs` porque cobrem uma etapa diferente do plano, mas com o mesmo
//! método: spawnar o binário real e conferir o processo — código de saída, um JSON em
//! stdout, orçamento aplicado.

use serde_json::Value;
use std::path::{Path, PathBuf};
use std::process::Command;

const BIN: &str = env!("CARGO_BIN_EXE_archatlas");

struct Out {
    code: i32,
    stdout: String,
    stderr: String,
}

impl Out {
    fn json(&self) -> Value {
        serde_json::from_str(&self.stdout)
            .unwrap_or_else(|e| panic!("stdout nao e um JSON unico: {e}\nstdout={}", self.stdout))
    }
}

fn run(args: &[&str]) -> Out {
    let o = Command::new(BIN)
        .args(args)
        .output()
        .unwrap_or_else(|e| panic!("falha ao executar {BIN}: {e}"));
    Out {
        code: o.status.code().unwrap_or(-1),
        stdout: String::from_utf8_lossy(&o.stdout).into_owned(),
        stderr: String::from_utf8_lossy(&o.stderr).into_owned(),
    }
}

fn tmp(tag: &str) -> PathBuf {
    use std::sync::atomic::{AtomicU32, Ordering};
    static N: AtomicU32 = AtomicU32::new(0);
    let n = N.fetch_add(1, Ordering::SeqCst);
    let d = std::env::temp_dir().join(format!("atlas-r2-{tag}-{}-{}", std::process::id(), n));
    let _ = std::fs::remove_dir_all(&d);
    std::fs::create_dir_all(&d).unwrap();
    d
}

fn write(path: &Path, body: &str) {
    std::fs::create_dir_all(path.parent().unwrap()).unwrap();
    std::fs::write(path, body).unwrap();
}

/// Repositório com um arquivo longo (para exercitar janela e dedup), um arquivo que cita o
/// símbolo e um teste.
fn fixture(tag: &str) -> (PathBuf, PathBuf) {
    let d = tmp(tag);
    let repo = d.join("repo");

    let mut longo = String::from("public class Alvo {\n");
    for i in 0..60 {
        longo.push_str(&format!("  private int campo{i};\n"));
    }
    longo.push_str("  public Long alvotoken() { return 1L; }\n");
    for i in 0..40 {
        longo.push_str(&format!("  private int cauda{i};\n"));
    }
    longo.push_str("}\n");
    write(&repo.join("src/Alvo.java"), &longo);

    write(
        &repo.join("src/Consumidor.java"),
        "public class Consumidor {\n\
         \x20 void usa() { alvotoken(); }\n\
         }\n",
    );
    write(
        &repo.join("src/AlvoTest.java"),
        "public class AlvoTest {\n\
         \x20 void testa() { alvoTokenCheck(); }\n\
         }\n",
    );
    write(&repo.join("config.properties"), "chave=alvotoken\n");
    let index = d.join("idx.sqlite");
    (repo, index)
}

fn req(dir: &Path, name: &str, body: &str) -> PathBuf {
    let p = dir.join(name);
    std::fs::write(&p, body).unwrap();
    p
}

// --- verify -------------------------------------------------------------------------

#[test]
fn verify_confirma_citacao_valida() {
    let (repo, index) = fixture("v-ok");
    let rs = repo.to_str().unwrap();
    let is = index.to_str().unwrap();
    run(&["index", "--repo", rs, "--index", is]);

    // Linha 62 é a do `alvotoken()` (1-based: 1 é a declaração da classe).
    let o = run(&[
        "verify",
        "--repo",
        rs,
        "--index",
        is,
        "--ref",
        "src/Alvo.java:62",
    ]);
    assert_eq!(o.code, 0, "stderr={}", o.stderr);
    let v = o.json();
    assert_eq!(v["schema"], "atlas-verify/1");
    assert_eq!(v["state"], "ok");
    assert_eq!(v["checks"]["inside_root"], true);
    assert_eq!(v["checks"]["file_exists"], true);
    assert_eq!(v["checks"]["registered_in_index"], true);
    assert_eq!(v["checks"]["hash_matches_index"], true);
    assert_eq!(v["checks"]["line_in_range"], true);
    assert_eq!(
        v["checks"]["name_on_line"],
        Value::Null,
        "nao inventar nome"
    );
    // A linha citada volta como unidade, para o chamador conferir sem reler.
    let units = v["units"].as_array().unwrap();
    assert_eq!(units.len(), 1);
    assert!(units[0]["text"].as_str().unwrap().contains("alvotoken"));
    // E o orçamento publicado descreve a própria resposta.
    assert_eq!(
        v["budget"]["used_bytes"].as_u64().unwrap() as usize,
        o.stdout.len() - 1
    );

    std::fs::remove_dir_all(repo.parent().unwrap()).ok();
}

#[test]
fn verify_conferindo_hash_fornecido() {
    let (repo, index) = fixture("v-hash");
    let rs = repo.to_str().unwrap();
    let is = index.to_str().unwrap();
    run(&["index", "--repo", rs, "--index", is]);

    // Hash correto: aceito.
    let live = {
        use sha2::{Digest, Sha256};
        let mut h = Sha256::new();
        h.update(std::fs::read(repo.join("src/Alvo.java")).unwrap());
        format!("{:x}", h.finalize())
    };
    let o = run(&[
        "verify",
        "--repo",
        rs,
        "--index",
        is,
        "--ref",
        &format!("src/Alvo.java:62@{live}"),
    ]);
    assert_eq!(o.code, 0, "stderr={}", o.stderr);
    assert_eq!(o.json()["checks"]["hash_matches_arg"], true);

    // Hash divergente: recusado, com motivo agregado.
    let o = run(&[
        "verify",
        "--repo",
        rs,
        "--index",
        is,
        "--ref",
        "src/Alvo.java:62@0000000000000000000000000000000000000000000000000000000000000000",
    ]);
    assert_eq!(
        o.code, 5,
        "hash divergente precisa falhar; stderr={}",
        o.stderr
    );
    let v = o.json();
    assert_eq!(v["checks"]["hash_matches_arg"], false);
    assert!(v["omitted"]["reasons"]
        .as_array()
        .unwrap()
        .iter()
        .any(|r| r == "hash_divergent"));

    std::fs::remove_dir_all(repo.parent().unwrap()).ok();
}

#[test]
fn verify_recusa_linha_fora_do_arquivo_e_caminho_fora_da_raiz() {
    let (repo, index) = fixture("v-ruim");
    let rs = repo.to_str().unwrap();
    let is = index.to_str().unwrap();
    run(&["index", "--repo", rs, "--index", is]);

    let o = run(&[
        "verify",
        "--repo",
        rs,
        "--index",
        is,
        "--ref",
        "src/Alvo.java:99999",
    ]);
    assert_eq!(o.code, 5, "linha inexistente precisa falhar");
    assert_eq!(o.json()["checks"]["line_in_range"], false);

    let o = run(&[
        "verify",
        "--repo",
        rs,
        "--index",
        is,
        "--ref",
        "src/NaoExiste.java:1",
    ]);
    assert_eq!(o.code, 5);
    assert_eq!(o.json()["checks"]["file_exists"], false);

    // Fora da raiz: recusado sem nem tentar ler.
    let o = run(&[
        "verify",
        "--repo",
        rs,
        "--index",
        is,
        "--ref",
        "../fora.java:1",
    ]);
    assert_eq!(o.code, 5, "stderr={}", o.stderr);
    assert_eq!(o.json()["checks"]["inside_root"], false);
    assert!(o.json()["omitted"]["reasons"]
        .as_array()
        .unwrap()
        .iter()
        .any(|r| r == "outside_root"));

    // Absoluto também.
    let o = run(&[
        "verify",
        "--repo",
        rs,
        "--index",
        is,
        "--ref",
        "/etc/passwd:1",
    ]);
    assert_eq!(o.code, 5);

    std::fs::remove_dir_all(repo.parent().unwrap()).ok();
}

#[test]
fn verify_recusa_ref_malformado_e_sem_indice() {
    let (repo, index) = fixture("v-sintaxe");
    let rs = repo.to_str().unwrap();
    let is = index.to_str().unwrap();

    // Sem índice: código 3, porque não há hash registrado para comparar.
    let o = run(&[
        "verify",
        "--repo",
        rs,
        "--index",
        is,
        "--ref",
        "src/Alvo.java:1",
    ]);
    assert_eq!(o.code, 3);

    run(&["index", "--repo", rs, "--index", is]);
    for spec in [
        "sem_linha.java",
        "src/Alvo.java:0",
        "src/Alvo.java:abc",
        ":5",
    ] {
        let o = run(&["verify", "--repo", rs, "--index", is, "--ref", spec]);
        assert_eq!(o.code, 2, "esperava 2 para {spec:?}; stderr={}", o.stderr);
    }
    // Opção ausente também é pedido inválido.
    assert_eq!(run(&["verify", "--repo", rs, "--index", is]).code, 2);

    std::fs::remove_dir_all(repo.parent().unwrap()).ok();
}

#[test]
fn verify_denuncia_indice_desatualizado_para_o_arquivo() {
    let (repo, index) = fixture("v-stale");
    let rs = repo.to_str().unwrap();
    let is = index.to_str().unwrap();
    run(&["index", "--repo", rs, "--index", is]);

    // Edita sem reindexar: o hash do índice deixa de descrever o disco.
    let mut body = std::fs::read_to_string(repo.join("src/Alvo.java")).unwrap();
    body.push_str("// alterado\n");
    std::fs::write(repo.join("src/Alvo.java"), body).unwrap();

    let o = run(&[
        "verify",
        "--repo",
        rs,
        "--index",
        is,
        "--ref",
        "src/Alvo.java:62",
    ]);
    assert_eq!(o.code, 5, "stderr={}", o.stderr);
    let v = o.json();
    assert_eq!(v["checks"]["hash_matches_index"], false);
    assert!(v["hints"]
        .as_array()
        .unwrap()
        .iter()
        .any(|h| h.as_str().unwrap().contains("desatualizado")));

    std::fs::remove_dir_all(repo.parent().unwrap()).ok();
}

// --- expand -------------------------------------------------------------------------

fn ctx_units(repo: &Path, index: &Path, query: &str, policy: &str) -> Vec<Value> {
    let body = format!(
        r#"{{"schema_version":1,"intent":"localizar","query":"{query}",
            "budget_tokens":4000,"max_bytes":40000,"policy":"{policy}"}}"#
    );
    let p = req(repo, "ctx.json", &body);
    let o = run(&[
        "context",
        "--repo",
        repo.to_str().unwrap(),
        "--index",
        index.to_str().unwrap(),
        "--request",
        p.to_str().unwrap(),
    ]);
    assert_eq!(o.code, 0, "stderr={}", o.stderr);
    o.json()["units"].as_array().unwrap().clone()
}

/// O ponto de `expand`: ampliar sem repetir o que o agente já recebeu.
#[test]
fn expand_amplia_e_nao_repete_trecho_ja_entregue() {
    let (repo, index) = fixture("e-dedup");
    let rs = repo.to_str().unwrap();
    let is = index.to_str().unwrap();
    run(&["index", "--repo", rs, "--index", is]);

    let units = ctx_units(&repo, &index, "alvotoken", "CTX-RS");
    let alvo = units
        .iter()
        .find(|u| u["file"] == "src/Alvo.java")
        .expect("o contexto deve entregar o arquivo alvo");
    let (dl, de) = (
        alvo["line"].as_u64().unwrap(),
        alvo["end_line"].as_u64().unwrap(),
    );

    let body = format!(
        r#"{{"schema_version":1,"intent":"editar","query":"alvotoken",
            "known_refs":[{{"file":"src/Alvo.java","line":{dl}}}],
            "delivered_refs":[{{"file":"src/Alvo.java","line":{dl},"end_line":{de}}}],
            "evidence_wanted":"context",
            "budget_tokens":4000,"max_bytes":40000,"policy":"CTX-RS"}}"#
    );
    let p = req(&repo, "exp.json", &body);
    let o = run(&[
        "expand",
        "--repo",
        rs,
        "--index",
        is,
        "--request",
        p.to_str().unwrap(),
    ]);
    assert_eq!(o.code, 0, "stderr={}", o.stderr);
    let v = o.json();
    assert_eq!(v["schema"], "atlas-context/1");
    let novos = v["units"].as_array().unwrap();
    assert!(!novos.is_empty(), "expand deveria ampliar a janela: {v}");

    for u in novos {
        let s = u["line"].as_u64().unwrap();
        let e = u["end_line"].as_u64().unwrap();
        // Nenhum trecho novo pode invadir o intervalo já entregue.
        assert!(
            e < dl || s > de,
            "trecho reentregue: [{s},{e}] colide com o entregue [{dl},{de}]"
        );
    }
    // E a ampliação é maior que a janela do contexto.
    let maior = novos
        .iter()
        .map(|u| u["end_line"].as_u64().unwrap() - u["line"].as_u64().unwrap() + 1)
        .max()
        .unwrap_or(0);
    assert!(
        maior >= 10,
        "a janela ampliada deveria ser maior: {maior} linhas"
    );

    std::fs::remove_dir_all(repo.parent().unwrap()).ok();
}

#[test]
fn expand_references_alcanca_outros_arquivos() {
    let (repo, index) = fixture("e-refs");
    let rs = repo.to_str().unwrap();
    let is = index.to_str().unwrap();
    run(&["index", "--repo", rs, "--index", is]);

    let body = r#"{"schema_version":1,"intent":"impacto","query":"alvotoken",
        "evidence_wanted":"references",
        "budget_tokens":4000,"max_bytes":40000,"policy":"CTX-RS"}"#;
    let p = req(&repo, "refs.json", body);
    let o = run(&[
        "expand",
        "--repo",
        rs,
        "--index",
        is,
        "--request",
        p.to_str().unwrap(),
    ]);
    assert_eq!(o.code, 0, "stderr={}", o.stderr);
    let v = o.json();
    let arquivos: Vec<&str> = v["units"]
        .as_array()
        .unwrap()
        .iter()
        .map(|u| u["file"].as_str().unwrap())
        .collect();
    assert!(
        arquivos.contains(&"src/Consumidor.java"),
        "deveria alcancar o consumidor: {arquivos:?}"
    );
    // Cada unidade precisa carregar a evidência de por que foi escolhida.
    for u in v["units"].as_array().unwrap() {
        assert!(u["reason"].as_str().unwrap().contains("lexical:references"));
    }

    std::fs::remove_dir_all(repo.parent().unwrap()).ok();
}

#[test]
fn expand_tests_filtra_por_caminho_de_teste() {
    let (repo, index) = fixture("e-tests");
    let rs = repo.to_str().unwrap();
    let is = index.to_str().unwrap();
    run(&["index", "--repo", rs, "--index", is]);

    let body = r#"{"schema_version":1,"intent":"testar","query":"alvo",
        "evidence_wanted":"tests",
        "budget_tokens":4000,"max_bytes":40000,"policy":"CTX-RS"}"#;
    let p = req(&repo, "tests.json", body);
    let o = run(&[
        "expand",
        "--repo",
        rs,
        "--index",
        is,
        "--request",
        p.to_str().unwrap(),
    ]);
    assert_eq!(o.code, 0, "stderr={}", o.stderr);
    let v = o.json();
    let arquivos: Vec<&str> = v["units"]
        .as_array()
        .unwrap()
        .iter()
        .map(|u| u["file"].as_str().unwrap())
        .collect();
    assert!(
        arquivos
            .iter()
            .all(|f| f.to_ascii_lowercase().contains("test")),
        "evidence_wanted=tests so pode devolver caminho de teste: {arquivos:?}"
    );
    if !arquivos.is_empty() {
        assert!(arquivos.iter().any(|f| f.contains("AlvoTest")));
    }

    std::fs::remove_dir_all(repo.parent().unwrap()).ok();
}

#[test]
fn expand_recusa_context_sem_known_refs_e_respeita_orcamento() {
    let (repo, index) = fixture("e-regras");
    let rs = repo.to_str().unwrap();
    let is = index.to_str().unwrap();
    run(&["index", "--repo", rs, "--index", is]);

    // context mode sem referência: não há o que ampliar.
    let body = r#"{"schema_version":1,"intent":"editar","query":"alvotoken",
        "evidence_wanted":"context",
        "budget_tokens":4000,"max_bytes":40000,"policy":"CTX-RS"}"#;
    let p = req(&repo, "sem_ref.json", body);
    let o = run(&[
        "expand",
        "--repo",
        rs,
        "--index",
        is,
        "--request",
        p.to_str().unwrap(),
    ]);
    assert_eq!(o.code, 2, "stderr={}", o.stderr);

    // evidence_wanted desconhecido é pedido inválido.
    let body = body.replace("\"context\"", "\"adivinhar\"");
    let p = req(&repo, "kind_ruim.json", &body);
    let o = run(&[
        "expand",
        "--repo",
        rs,
        "--index",
        is,
        "--request",
        p.to_str().unwrap(),
    ]);
    assert_eq!(o.code, 2);
    assert!(o.stdout.is_empty());

    // Orçamento apertado: nada estoura o teto.
    for mb in [700u64, 1500, 12000] {
        let body = format!(
            r#"{{"schema_version":1,"intent":"editar","query":"alvotoken",
                "known_refs":[{{"file":"src/Alvo.java","line":62}}],
                "evidence_wanted":"context",
                "budget_tokens":300,"max_bytes":{mb},"policy":"CTX-RS"}}"#
        );
        let p = req(&repo, "apertado.json", &body);
        let o = run(&[
            "expand",
            "--repo",
            rs,
            "--index",
            is,
            "--request",
            p.to_str().unwrap(),
        ]);
        assert_eq!(o.code, 0, "stderr={}", o.stderr);
        let v = o.json();
        assert_eq!(
            v["budget"]["used_bytes"].as_u64().unwrap() as usize,
            o.stdout.len() - 1,
            "max_bytes={mb}"
        );
        assert!(o.stdout.len() as u64 <= mb + 1, "max_bytes={mb} estourou");
        assert!(v["budget"]["used_tokens"].as_u64().unwrap() <= 300);
    }

    std::fs::remove_dir_all(repo.parent().unwrap()).ok();
}

// --- filtro de corpus ------------------------------------------------------------------

/// Sem corpus idêntico, comparar duas implementações mede tamanho de repositório em vez de
/// desempenho. `--include` é o que torna a comparação de R2 admissível.
#[test]
fn include_restaura_corpus_exato_e_reporta_o_descarte() {
    let (repo, index) = fixture("include");
    let rs = repo.to_str().unwrap();
    let is = index.to_str().unwrap();

    let sem_filtro = run(&["index", "--repo", rs, "--index", is]).json();
    assert!(
        sem_filtro["counts"]["discovered"].as_u64().unwrap() >= 4,
        "sem filtro, o .properties tambem entra"
    );

    let com_filtro = run(&[
        "index",
        "--repo",
        rs,
        "--index",
        is,
        "--include",
        "java",
        "--force",
    ])
    .json();
    assert_eq!(com_filtro["counts"]["discovered"], 3, "so os .java");
    assert_eq!(com_filtro["counts"]["excluded_by_filter"], 1);
    assert_eq!(com_filtro["counts"]["include"][0], "java");

    // Lista invalida e item vazio sao recusados antes de tocar o indice.
    assert_eq!(
        run(&["index", "--repo", rs, "--index", is, "--include", "klingon"]).code,
        2
    );
    assert_eq!(
        run(&["index", "--repo", rs, "--index", is, "--include", "java,"]).code,
        2
    );

    std::fs::remove_dir_all(repo.parent().unwrap()).ok();
}
