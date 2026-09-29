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

// --- ocorrências fora da janela num arquivo já citado --------------------------------

/// Arquivo com a mesma ocorrência do termo em duas pontas, longe uma da outra.
fn fixture_duas_ocorrencias(tag: &str) -> (PathBuf, PathBuf) {
    let d = tmp(tag);
    let repo = d.join("repo");
    let mut linhas = vec!["public class Longe {".to_string()];
    for i in 0..18 {
        linhas.push(format!("  private int inicio{i};"));
    }
    linhas.push("  public Long alvotoken() { return 1L; }".to_string());
    for i in 0..150 {
        linhas.push(format!("  private int meio{i};"));
    }
    linhas.push("  public void usaDeNovo() { alvotoken(); }".to_string());
    for i in 0..20 {
        linhas.push(format!("  private int fim{i};"));
    }
    linhas.push("}".to_string());
    write(&repo.join("src/Longe.java"), &(linhas.join("\n") + "\n"));
    write(
        &repo.join("src/Outro.java"),
        "public class Outro {\n  void usa() { alvotoken(); }\n}\n",
    );
    let index = d.join("idx.sqlite");
    (repo, index)
}

/// Intervalos entregues por uma resposta, por arquivo.
fn intervalos(v: &Value) -> Vec<(String, u64, u64)> {
    v["units"]
        .as_array()
        .unwrap()
        .iter()
        .map(|u| {
            (
                u["file"].as_str().unwrap().to_string(),
                u["line"].as_u64().unwrap(),
                u["end_line"].as_u64().unwrap(),
            )
        })
        .collect()
}

fn sobrepoe(a: (u64, u64), b: (u64, u64)) -> bool {
    a.0 <= b.1 && b.0 <= a.1
}

/// O defeito medido no ensaio: `known_refs` vindo do `context` são **os próprios arquivos**
/// que a busca alcança (70/70 pares), então o único material novo que `references` pode
/// trazer é ocorrência **fora da janela** de um arquivo já citado. Antes, um arquivo de
/// `known_refs` só produzia a janela pedida — o segundo grupo de spans não existia.
#[test]
fn expand_traz_ocorrencia_fora_da_janela_do_arquivo_ja_citado() {
    let (repo, index) = fixture_duas_ocorrencias("ocorrencias");
    let rs = repo.to_str().unwrap();
    let is = index.to_str().unwrap();
    run(&["index", "--repo", rs, "--index", is]);

    // Setup: o `context` entrega o arquivo com a ocorrência do termo.
    let cp = req(
        &repo,
        "ctx.json",
        r#"{"schema_version":1,"intent":"localizar","query":"alvotoken",
            "budget_tokens":2000,"max_bytes":8000,"policy":"CTX-RS"}"#,
    );
    let ctx = run(&[
        "context",
        "--repo",
        rs,
        "--index",
        is,
        "--request",
        cp.to_str().unwrap(),
    ]);
    assert_eq!(ctx.code, 0, "stderr={}", ctx.stderr);
    let entregue = intervalos(&ctx.json());
    assert!(
        entregue.iter().any(|(f, _, _)| f == "src/Longe.java"),
        "o setup precisa entregar o arquivo da ocorrencia: {entregue:?}"
    );
    let known: Vec<Value> = ctx.json()["units"]
        .as_array()
        .unwrap()
        .iter()
        .map(|u| {
            serde_json::json!({"file": u["file"], "line": u["line"], "end_line": u["end_line"]})
        })
        .collect();

    let body = serde_json::json!({
        "schema_version": 1, "intent": "localizar", "query": "alvotoken",
        "known_refs": known, "delivered_refs": known,
        "evidence_wanted": "references",
        "budget_tokens": 2000, "max_bytes": 8000, "policy": "CTX-RS",
    });
    let ep = req(&repo, "exp.json", &body.to_string());
    let exp = run(&[
        "expand",
        "--repo",
        rs,
        "--index",
        is,
        "--request",
        ep.to_str().unwrap(),
    ]);
    assert_eq!(exp.code, 0, "stderr={}", exp.stderr);
    let v = exp.json();

    // A segunda ocorrência do termo no MESMO arquivo precisa chegar, e ela está fora de
    // qualquer janela da primeira (linha 20 contra linha ~171).
    let lexicais_longe: Vec<(u64, u64)> = v["units"]
        .as_array()
        .unwrap()
        .iter()
        .filter(|u| {
            u["file"] == "src/Longe.java" && u["reason"].as_str().unwrap().starts_with("lexical")
        })
        .map(|u| (u["line"].as_u64().unwrap(), u["end_line"].as_u64().unwrap()))
        .collect();
    assert!(
        lexicais_longe.iter().any(|(_, e)| *e >= 171),
        "a ocorrencia fora da janela deveria vir: {} {lexicais_longe:?}",
        v["units"]
    );

    // Nada do que já foi entregue volta, e a própria resposta não se sobrepõe.
    let novos = intervalos(&v);
    for (f, s, e) in &novos {
        for (df, ds, de) in &entregue {
            assert!(
                f != df || !sobrepoe((*s, *e), (*ds, *de)),
                "unidade {f}:{s}-{e} sobrepoe o que ja foi entregue: {df}:{ds}-{de}"
            );
        }
    }
    for i in 0..novos.len() {
        for j in (i + 1)..novos.len() {
            let (fa, sa, ea) = novos[i].clone();
            let (fb, sb, eb) = novos[j].clone();
            assert!(
                fa != fb || !sobrepoe((sa, ea), (sb, eb)),
                "a propria resposta se sobrepoe: {fa}:{sa}-{ea} e {fb}:{sb}-{eb}"
            );
        }
    }

    std::fs::remove_dir_all(repo.parent().unwrap()).ok();
}

// --- reserva de evidência (Q7 de R2) -------------------------------------------------

/// Pedido de `expand` com a ref que cobre o arquivo inteiro e, opcionalmente, a reserva.
///
/// O teto de 3000 bytes é escolhido para que ele **vincule**: as duas janelas de 60 linhas do
/// `Alvo.java` gastam ~2875 bytes sozinhas, então sem reserva não sobra nada para a busca. Com
/// reserva de 50% o teto das janelas é 1500 bytes: a primeira janela (~2147) já não cabe
/// inteira e a segunda não cabe — a busca entra no espaço liberado.
fn expand_com_reserva(repo: &Path, index: &Path, nome: &str, reserve: Option<u8>) -> Out {
    let campo = match reserve {
        Some(pct) => format!(",\"evidence_reserve_pct\":{pct}"),
        None => String::new(),
    };
    let body = format!(
        r#"{{"schema_version":1,"intent":"impacto","query":"alvotoken",
            "evidence_wanted":"references",
            "known_refs":[{{"file":"src/Alvo.java","line":1,"end_line":103}}]{campo},
            "budget_tokens":1000,"max_bytes":3000,"policy":"CTX-RS"}}"#
    );
    let p = req(repo, nome, &body);
    run(&[
        "expand",
        "--repo",
        repo.to_str().unwrap(),
        "--index",
        index.to_str().unwrap(),
        "--request",
        p.to_str().unwrap(),
    ])
}

/// Quantas unidades vieram da busca lexical (em oposição às janelas de `known_refs`).
fn lexicais(v: &Value) -> usize {
    v["units"]
        .as_array()
        .unwrap()
        .iter()
        .filter(|u| u["reason"].as_str().unwrap_or("").starts_with("lexical"))
        .count()
}

/// Q7 de R2: as janelas de `known_refs` são geradas primeiro e, sem reserva, consomem o teto
/// inteiro — no ensaio isso aconteceu em 39 de 70 pares, e `references` devolvia exatamente o
/// mesmo que `context`. O teste mede a diferença em vez de confiar na intenção: mesmo pedido,
/// mesmo índice, mesmo teto, só a reserva muda.
#[test]
fn reserva_devolve_evidencia_lexical_que_sem_ela_ficava_de_fora() {
    let (repo, index) = fixture("reserve-contra");
    run(&[
        "index",
        "--repo",
        repo.to_str().unwrap(),
        "--index",
        index.to_str().unwrap(),
    ]);

    let sem = expand_com_reserva(&repo, &index, "sem.json", None);
    assert_eq!(sem.code, 0, "stderr={}", sem.stderr);
    let vs = sem.json();
    assert_eq!(
        lexicais(&vs),
        0,
        "sem reserva a janela ocupa o teto e a busca fica de fora: {}",
        vs["units"]
    );

    let com = expand_com_reserva(&repo, &index, "com.json", Some(50));
    assert_eq!(com.code, 0, "stderr={}", com.stderr);
    let vc = com.json();
    assert!(
        lexicais(&vc) >= 1,
        "com reserva a busca precisa entrar: {}",
        vc["units"]
    );
    // A reserva **distribui** o teto, não troca as janelas pela busca: pelo menos uma janela de
    // `known_refs` continua na resposta.
    assert!(
        vc["units"]
            .as_array()
            .unwrap()
            .iter()
            .any(|u| u["reason"].as_str().unwrap().starts_with("known_ref")),
        "a reserva nao pode zerar as janelas: {}",
        vc["units"]
    );
    // A busca de fato alcança outro arquivo — não é uma unidade a mais da mesma janela.
    let arquivos: Vec<&str> = vc["units"]
        .as_array()
        .unwrap()
        .iter()
        .map(|u| u["file"].as_str().unwrap())
        .collect();
    assert!(
        arquivos.contains(&"src/Consumidor.java"),
        "a evidencia reservada deveria alcancar o consumidor: {arquivos:?}"
    );

    // O que foi barrado aparece declarado, e o motivo nomeia a reserva — barrado em silêncio
    // seria indistinguível de "não havia nada".
    let motivos: Vec<&str> = vc["omitted"]["reasons"]
        .as_array()
        .unwrap()
        .iter()
        .filter_map(|r| r.as_str())
        .collect();
    assert!(
        motivos.contains(&"evidence_reserved"),
        "o que a reserva barrou precisa aparecer declarado: {motivos:?}"
    );
    assert!(
        vc["omitted"]["n"].as_u64().unwrap() >= 1,
        "a contagem de omitidos nao pode ficar em zero com motivo declarado"
    );

    // E o teto continua valendo para o total, não só para as janelas: a reserva é uma fatia de
    // `max_bytes`, nunca uma licença para passar dele.
    assert_eq!(vc["budget"]["max_bytes"], 3000);
    // Mesma identidade que R1/R2 usam em toda parte: `used_bytes` é o JSON emitido, sem a
    // quebra de linha final.
    assert_eq!(
        vc["budget"]["used_bytes"].as_u64().unwrap() as usize,
        com.stdout.len() - 1,
        "o declarado tem de ser o entregue"
    );
    assert!(
        com.stdout.len() <= 3000,
        "entregou {} bytes",
        com.stdout.len()
    );

    std::fs::remove_dir_all(repo.parent().unwrap()).ok();
}

/// Ausente e zero são o mesmo pedido: a extensão é **aditiva**, e nenhuma rodada de R2
/// anterior a ela muda de resultado. Comparo os bytes de stdout em vez de confiar nisso.
#[test]
fn reserva_ausente_e_igual_a_zero() {
    let (repo, index) = fixture("reserve-zero");
    run(&[
        "index",
        "--repo",
        repo.to_str().unwrap(),
        "--index",
        index.to_str().unwrap(),
    ]);
    let ausente = expand_com_reserva(&repo, &index, "ausente.json", None);
    let zero = expand_com_reserva(&repo, &index, "zero.json", Some(0));
    assert_eq!(ausente.code, 0, "stderr={}", ausente.stderr);
    assert_eq!(zero.code, 0, "stderr={}", zero.stderr);
    assert_eq!(ausente.stdout, zero.stdout);
    std::fs::remove_dir_all(repo.parent().unwrap()).ok();
}

/// Reservar orçamento para uma busca que não vai acontecer é pedido incoerente: recusa em vez
/// de ignorar, porque ignorar em silêncio faria o chamador acreditar que reservou.
#[test]
fn reserva_incoerente_e_recusada() {
    let (repo, index) = fixture("reserve-erro");
    run(&[
        "index",
        "--repo",
        repo.to_str().unwrap(),
        "--index",
        index.to_str().unwrap(),
    ]);

    // `context` nao busca: reservar nao faz sentido.
    let body = r#"{"schema_version":1,"intent":"impacto","query":"alvotoken",
        "evidence_wanted":"context","evidence_reserve_pct":40,
        "known_refs":[{"file":"src/Alvo.java","line":62}],
        "budget_tokens":1000,"max_bytes":4000,"policy":"CTX-RS"}"#;
    let p = req(&repo, "ctx.json", body);
    let o = run(&[
        "expand",
        "--repo",
        repo.to_str().unwrap(),
        "--index",
        index.to_str().unwrap(),
        "--request",
        p.to_str().unwrap(),
    ]);
    assert_eq!(o.code, 2, "stderr={}", o.stderr);
    assert!(o.stderr.contains("evidence_reserve_pct"), "{}", o.stderr);

    // Fora de 0..100 idem, antes de tocar o indice.
    let fora = expand_com_reserva(&repo, &index, "fora.json", Some(101));
    assert_eq!(fora.code, 2, "stderr={}", fora.stderr);
    assert!(fora.stderr.contains("0..100"), "{}", fora.stderr);

    std::fs::remove_dir_all(repo.parent().unwrap()).ok();
}
