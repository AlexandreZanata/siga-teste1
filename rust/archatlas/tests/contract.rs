// SPDX-License-Identifier: Apache-2.0
//! Contrato exercitado pelo binário real, não pela biblioteca.
//!
//! Estes testes spawnam `archatlas` como o agente faria, e é por isso que existem: os
//! critérios de aceite de R1 são sobre o processo (código de saída, stdout com um JSON só,
//! orçamento efetivamente aplicado), não sobre funções internas.

use serde_json::Value;
use sha2::{Digest, Sha256};
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
    let d = std::env::temp_dir().join(format!("atlas-it-{tag}-{}-{}", std::process::id(), n));
    let _ = std::fs::remove_dir_all(&d);
    std::fs::create_dir_all(&d).unwrap();
    d
}

fn write(path: &Path, body: &str) {
    std::fs::create_dir_all(path.parent().unwrap()).unwrap();
    std::fs::write(path, body).unwrap();
}

fn sha256(text: &str) -> String {
    let mut h = Sha256::new();
    h.update(text.as_bytes());
    format!("{:x}", h.finalize())
}

/// Repositório fixture com dois arquivos Java.
fn fixture(tag: &str) -> (PathBuf, PathBuf) {
    let d = tmp(tag);
    let repo = d.join("repo");
    write(
        &repo.join("src/ExMovimentacao.java"),
        "public class ExMovimentacao {\n\
         \x20 public Long getId() { return id; }\n\
         \x20 private Long id;\n\
         \x20 public void setId(Long v) { this.id = v; }\n\
         }\n",
    );
    write(
        &repo.join("src/Outro.java"),
        "public class Outro {\n\
         \x20 void usa(ExMovimentacao m) { m.setId(1L); }\n\
         }\n",
    );
    let index = d.join("idx.sqlite");
    (repo, index)
}

fn req_file(dir: &Path, body: &str) -> PathBuf {
    let p = dir.join("pedido.json");
    std::fs::write(&p, body).unwrap();
    p
}

fn basic_req(policy: &str, budget: u64, max_bytes: u64) -> String {
    format!(
        r#"{{"schema_version":1,"intent":"localizar","query":"ExMovimentacao",
            "budget_tokens":{budget},"max_bytes":{max_bytes},"policy":"{policy}"}}"#
    )
}

// --- aceite central: fonte verificada, orcamento contado, caminho relativo -------------

#[test]
fn ponta_a_ponta_entrega_fonte_verificada_e_relativa() {
    let (repo, index) = fixture("e2e");
    let rs = repo.to_str().unwrap();
    let is = index.to_str().unwrap();

    let idx = run(&["index", "--repo", rs, "--index", is]);
    assert_eq!(idx.code, 0, "stderr={}", idx.stderr);
    assert_eq!(idx.json()["counts"]["discovered"], 2);

    let rp = req_file(&repo, &basic_req("CTX-RS", 2000, 20000));
    let ctx = run(&[
        "context",
        "--repo",
        rs,
        "--index",
        is,
        "--request",
        rp.to_str().unwrap(),
    ]);
    assert_eq!(ctx.code, 0, "stderr={}", ctx.stderr);
    let v = ctx.json();
    assert_eq!(v["schema"], "atlas-context/1");
    assert!(["ok", "partial"].contains(&v["state"].as_str().unwrap()));

    let units = v["units"].as_array().unwrap();
    assert!(!units.is_empty(), "esperava unidades: {v}");

    for u in units {
        let rel = u["file"].as_str().unwrap();
        // Caminho relativo: sem barra inicial, sem `..`, sem a raiz absoluta do temp.
        assert!(!rel.starts_with('/'), "caminho absoluto vazou: {rel}");
        assert!(!rel.contains(".."), "caminho com parent vazou: {rel}");
        assert!(!ctx
            .stdout
            .contains(repo.to_str().unwrap().trim_end_matches('/')));

        // Fonte citada corresponde aos bytes do snapshot: o hash da unidade tem que ser
        // o sha256 do arquivo real no disco.
        let disk = std::fs::read_to_string(repo.join(rel)).unwrap();
        assert_eq!(
            u["hash"].as_str().unwrap(),
            format!("sha256:{}", sha256(&disk)),
            "hash da unidade nao corresponde ao arquivo"
        );
        // E o texto entregue tem que ser um recorte literal do arquivo.
        let text = u["text"].as_str().unwrap();
        for line in text.lines() {
            assert!(
                disk.lines().any(|d| d == line),
                "linha entregue nao existe no arquivo: {line:?}"
            );
        }
    }

    std::fs::remove_dir_all(repo.parent().unwrap()).ok();
}

/// Regressão direta do defeito medido em `BASELINE.md` §4: o `used` declarado tem que ser
/// o tamanho da resposta realmente emitida, e nada pode exceder o teto declarado.
#[test]
fn orcamento_e_contado_sobre_a_serializacao_final() {
    let (repo, index) = fixture("orcamento");
    let rs = repo.to_str().unwrap();
    let is = index.to_str().unwrap();
    run(&["index", "--repo", rs, "--index", is]);

    for budget in [600u64, 1000, 2000, 8000] {
        let rp = req_file(&repo, &basic_req("CTX-RS", budget, 20000));
        let ctx = run(&[
            "context",
            "--repo",
            rs,
            "--index",
            is,
            "--request",
            rp.to_str().unwrap(),
        ]);
        assert_eq!(ctx.code, 0, "budget={budget} stderr={}", ctx.stderr);
        let v = ctx.json();

        let emmited = ctx.stdout.len() - 1; // menos o '\n' final
        let used_bytes = v["budget"]["used_bytes"].as_u64().unwrap();
        let used_tokens = v["budget"]["used_tokens"].as_u64().unwrap();

        assert_eq!(
            used_bytes as usize, emmited,
            "budget={budget}: used_bytes tem que ser o tamanho real do stdout"
        );
        assert_eq!(
            used_tokens,
            used_bytes / 4,
            "budget={budget}: used_tokens tem que derivar da serializacao final"
        );
        assert!(
            used_bytes <= v["budget"]["max_bytes"].as_u64().unwrap(),
            "budget={budget}: ultrapassou max_bytes"
        );
        assert!(
            used_tokens <= v["budget"]["requested_tokens"].as_u64().unwrap(),
            "budget={budget}: ultrapassou budget_tokens"
        );
        // Estimativa, nunca alegacao de exatidao: nao ha tokenizer do modelo aqui.
        assert_eq!(v["budget"]["tokenizer_is_exact"], false);
        assert_eq!(v["budget"]["unit"], "byte");
    }
    std::fs::remove_dir_all(repo.parent().unwrap()).ok();
}

#[test]
fn orcamento_menor_que_o_envelope_vira_partial_explicito() {
    let (repo, index) = fixture("envelope");
    let rs = repo.to_str().unwrap();
    let is = index.to_str().unwrap();
    run(&["index", "--repo", rs, "--index", is]);

    let rp = req_file(&repo, &basic_req("CTX-RS", 1, 40));
    let ctx = run(&[
        "context",
        "--repo",
        rs,
        "--index",
        is,
        "--request",
        rp.to_str().unwrap(),
    ]);
    assert_eq!(ctx.code, 0, "envelope apertado e resposta valida, nao erro");
    let v = ctx.json();
    // Nenhuma unidade é entregue: nenhum trecho pode estourar o teto.
    assert_eq!(v["state"], "partial");
    assert_eq!(v["units"].as_array().unwrap().len(), 0);
    let reasons = v["omitted"]["reasons"].as_array().unwrap();
    assert!(
        reasons.iter().any(|r| r == "envelope_too_large"),
        "esperava envelope_too_large, veio {reasons:?}"
    );
    assert!(v["hints"][0].as_str().unwrap().contains("envelope minimo"));
    // O envelope vazio é o piso físico da resposta: não existe JSON menor que isto. O
    // contrato pede resposta vazia explícita, e é o que se mede aqui — `used_bytes`
    // reporta o tamanho real, mesmo quando ele excede um teto impossível de cumprir.
    let usado = v["budget"]["used_bytes"].as_u64().unwrap() as usize;
    assert_eq!(usado, ctx.stdout.len() - 1);
    assert!(
        usado > 40,
        "o piso do envelope deve ser reportado honestamente, nao escondido"
    );
    std::fs::remove_dir_all(repo.parent().unwrap()).ok();
}

// --- codigos de saida do contrato -----------------------------------------------------

#[test]
fn codigo_2_para_pedido_invalido() {
    let (repo, index) = fixture("c2");
    let rs = repo.to_str().unwrap();
    let is = index.to_str().unwrap();
    run(&["index", "--repo", rs, "--index", is]);

    let casos = [
        ("{nao json", "json malformado"),
        (&basic_req("AUTO", 2000, 20000)[..], "policy desconhecida"),
        (
            r#"{"schema_version":9,"intent":"localizar","query":"x","budget_tokens":1,"max_bytes":1,"policy":"CTX-RS"}"#,
            "schema desconhecida",
        ),
        (
            r#"{"schema_version":1,"intent":"localizar","query":"x","budget_tokens":1,"max_bytes":1,"policy":"CTX-RS","extra":1}"#,
            "campo desconhecido",
        ),
    ];
    for (body, motivo) in casos {
        let p = repo.join("bad.json");
        std::fs::write(&p, body).unwrap();
        let o = run(&[
            "context",
            "--repo",
            rs,
            "--index",
            is,
            "--request",
            p.to_str().unwrap(),
        ]);
        assert_eq!(o.code, 2, "esperava 2 para {motivo}; stderr={}", o.stderr);
        assert!(
            o.stdout.is_empty(),
            "pedido invalido nao deve produzir stdout"
        );
    }

    // Opcao desconhecida e opcao sem valor tambem sao pedido invalido.
    assert_eq!(run(&["context", "--repo", rs, "--index", is]).code, 2);
    assert_eq!(
        run(&["doctor", "--repo", rs, "--index", is, "--turbo"]).code,
        2
    );

    std::fs::remove_dir_all(repo.parent().unwrap()).ok();
}

#[test]
fn codigo_3_para_indice_ausente_corrompido_e_vazio() {
    let (repo, index) = fixture("c3");
    let rs = repo.to_str().unwrap();
    let is = index.to_str().unwrap();
    let rp = req_file(&repo, &basic_req("CTX-RS", 2000, 20000));

    // Ausente: contexto com diagnostico em stdout, sem lista vazia fingida.
    let o = run(&[
        "context",
        "--repo",
        rs,
        "--index",
        is,
        "--request",
        rp.to_str().unwrap(),
    ]);
    assert_eq!(o.code, 3, "stderr={}", o.stderr);
    let v = o.json();
    assert_eq!(v["state"], "unsupported");
    assert_eq!(v["units"].as_array().unwrap().len(), 0);

    // doctor tambem sai 3 e continua diagnosticando.
    let d = run(&["doctor", "--repo", rs, "--index", is]);
    assert_eq!(d.code, 3);
    assert_eq!(d.json()["index"]["state"], "missing");
    assert!(d.json()["index"]["advice"]
        .as_str()
        .unwrap()
        .contains("index"));

    // Corrompido: arquivo que nao e SQLite.
    std::fs::write(&index, b"isto nao e um sqlite").unwrap();
    let d = run(&["doctor", "--repo", rs, "--index", is]);
    assert_eq!(d.code, 3);
    assert_eq!(d.json()["index"]["state"], "corrupt");

    // Vazio: schema valido, zero arquivos. Indexar nada deixa o indice sem resposta util.
    let empty_repo = repo.parent().unwrap().join("vazio");
    std::fs::create_dir_all(&empty_repo).unwrap();
    let ei = repo.parent().unwrap().join("vazio.sqlite");
    assert_eq!(
        run(&[
            "index",
            "--repo",
            empty_repo.to_str().unwrap(),
            "--index",
            ei.to_str().unwrap()
        ])
        .code,
        0
    );
    assert_eq!(
        run(&["doctor", "--repo", rs, "--index", ei.to_str().unwrap()]).code,
        3
    );

    std::fs::remove_dir_all(repo.parent().unwrap()).ok();
}

#[test]
fn codigo_4_para_io_e_codigo_5_para_integridade() {
    let (repo, index) = fixture("c45");
    let rs = repo.to_str().unwrap();
    let is = index.to_str().unwrap();
    run(&["index", "--repo", rs, "--index", is]);

    // Pedido apontando para arquivo inexistente: erro de I/O.
    let o = run(&[
        "context",
        "--repo",
        rs,
        "--index",
        is,
        "--request",
        repo.parent()
            .unwrap()
            .join("nao_existe.json")
            .to_str()
            .unwrap(),
    ]);
    assert_eq!(o.code, 4, "stderr={}", o.stderr);

    // Referencia escapando da raiz: integridade violada.
    let p = req_file(
        &repo,
        r#"{"schema_version":1,"intent":"editar","query":"getId",
            "known_refs":[{"file":"../fora.java"}],
            "budget_tokens":2000,"max_bytes":20000,"policy":"CTX-RS"}"#,
    );
    let o = run(&[
        "context",
        "--repo",
        rs,
        "--index",
        is,
        "--request",
        p.to_str().unwrap(),
    ]);
    assert_eq!(o.code, 5, "stderr={}", o.stderr);
    assert!(o.stderr.contains("insegura") || o.stderr.contains("integridade"));

    // Caminho absoluto tambem e recusado com 5.
    let p = req_file(
        &repo,
        r#"{"schema_version":1,"intent":"editar","query":"getId",
            "known_refs":[{"file":"/etc/passwd"}],
            "budget_tokens":2000,"max_bytes":20000,"policy":"CTX-RS"}"#,
    );
    let o = run(&[
        "context",
        "--repo",
        rs,
        "--index",
        is,
        "--request",
        p.to_str().unwrap(),
    ]);
    assert_eq!(o.code, 5, "stderr={}", o.stderr);

    std::fs::remove_dir_all(repo.parent().unwrap()).ok();
}

/// Se o arquivo mudou depois da indexação, não existe fonte verificável a entregar.
#[test]
fn codigo_5_quando_nada_e_verificavel_apos_edicao() {
    let (repo, index) = fixture("c5stale");
    let rs = repo.to_str().unwrap();
    let is = index.to_str().unwrap();
    run(&["index", "--repo", rs, "--index", is]);

    // Edita o arquivo que casa com a consulta, sem reindexar: hashes divergem.
    write(
        &repo.join("src/ExMovimentacao.java"),
        "public class ExMovimentacao { /* mudou */ }\n",
    );
    write(&repo.join("src/Outro.java"), "public class Outro {}\n");

    let rp = req_file(&repo, &basic_req("CTX-RS", 2000, 20000));
    let o = run(&[
        "context",
        "--repo",
        rs,
        "--index",
        is,
        "--request",
        rp.to_str().unwrap(),
    ]);
    assert_eq!(o.code, 5, "stderr={}", o.stderr);
    assert!(
        o.stdout.is_empty(),
        "sem fonte verificada nao pode haver resposta JSON de sucesso"
    );

    // Depois de reindexar, a mesma consulta volta a responder.
    run(&["index", "--repo", rs, "--index", is]);
    let o = run(&[
        "context",
        "--repo",
        rs,
        "--index",
        is,
        "--request",
        rp.to_str().unwrap(),
    ]);
    assert_eq!(o.code, 0, "stderr={}", o.stderr);

    std::fs::remove_dir_all(repo.parent().unwrap()).ok();
}

// --- estados: stale, determinismo, isolamento ----------------------------------------

#[test]
fn snapshot_pedido_diferente_do_indexado_vira_stale() {
    let (repo, index) = fixture("stale");
    let rs = repo.to_str().unwrap();
    let is = index.to_str().unwrap();
    run(&["index", "--repo", rs, "--index", is]);

    let rp = req_file(
        &repo,
        r#"{"schema_version":1,"intent":"localizar","query":"ExMovimentacao",
            "snapshot":{"sha_base":"deadbeef"},
            "budget_tokens":2000,"max_bytes":20000,"policy":"CTX-RS"}"#,
    );
    let o = run(&[
        "context",
        "--repo",
        rs,
        "--index",
        is,
        "--request",
        rp.to_str().unwrap(),
    ]);
    assert_eq!(o.code, 0, "stale e resposta valida; stderr={}", o.stderr);
    let v = o.json();
    assert_eq!(v["state"], "stale");
    assert!(v["omitted"]["reasons"]
        .as_array()
        .unwrap()
        .iter()
        .any(|r| r == "snapshot_mismatch"));
    assert!(v["hints"]
        .as_array()
        .unwrap()
        .iter()
        .any(|h| h.as_str().unwrap().contains("index")));

    std::fs::remove_dir_all(repo.parent().unwrap()).ok();
}

#[test]
fn stdout_e_deterministico_entre_execucoes() {
    let (repo, index) = fixture("det");
    let rs = repo.to_str().unwrap();
    let is = index.to_str().unwrap();
    run(&["index", "--repo", rs, "--index", is]);
    let rp = req_file(&repo, &basic_req("CTX-RS", 2000, 20000));
    let args = [
        "context",
        "--repo",
        rs,
        "--index",
        is,
        "--request",
        rp.to_str().unwrap(),
    ];
    let a = run(&args);
    let b = run(&args);
    assert_eq!(a.stdout, b.stdout, "resposta deve ser byte-identica");
    assert_eq!(a.code, b.code);

    // A indexacao tambem: mesma geracao em execucoes separadas.
    let g1 = run(&["index", "--repo", rs, "--index", is]).json();
    let g2 = run(&["index", "--repo", rs, "--index", is]).json();
    assert_eq!(g1["index"]["generation"], g2["index"]["generation"]);
    std::fs::remove_dir_all(repo.parent().unwrap()).ok();
}

#[test]
fn incremental_equivale_a_rebuild_apos_mutacao() {
    let (repo, index) = fixture("equiv");
    let rs = repo.to_str().unwrap();
    let is = index.to_str().unwrap();
    run(&["index", "--repo", rs, "--index", is]);

    // edita, apaga e renomeia
    write(
        &repo.join("src/ExMovimentacao.java"),
        "public class ExMovimentacao { Long id; Long getId() { return id; } }\n",
    );
    std::fs::remove_file(repo.join("src/Outro.java")).unwrap();
    write(
        &repo.join("src/Novo.java"),
        "public class Novo { Long getId() { return 1L; } }\n",
    );

    let inc = run(&["index", "--repo", rs, "--index", is]);
    assert_eq!(inc.code, 0);
    let v = inc.json();
    assert_eq!(v["counts"]["pruned_files"], 1, "Outro.java sumiu do disco");
    assert_eq!(v["counts"]["mode"], "incremental");
    let gen_inc = v["index"]["generation"].clone();
    let files_inc = v["index"]["files"].clone();

    // Rebuild do zero no mesmo caminho tem que chegar ao mesmo estado logico.
    let reb = run(&["index", "--repo", rs, "--index", is, "--force"]);
    assert_eq!(reb.code, 0);
    let v2 = reb.json();
    assert_eq!(v2["counts"]["mode"], "rebuild");
    assert_eq!(gen_inc, v2["index"]["generation"], "incremental != rebuild");
    assert_eq!(files_inc, v2["index"]["files"]);

    std::fs::remove_dir_all(repo.parent().unwrap()).ok();
}

#[test]
fn arquivo_apagado_deixa_de_ser_entregue() {
    let (repo, index) = fixture("delete");
    let rs = repo.to_str().unwrap();
    let is = index.to_str().unwrap();
    run(&["index", "--repo", rs, "--index", is]);
    std::fs::remove_file(repo.join("src/Outro.java")).unwrap();
    run(&["index", "--repo", rs, "--index", is]);

    let rp = req_file(&repo, &basic_req("CTX-RS", 4000, 40000));
    let o = run(&[
        "context",
        "--repo",
        rs,
        "--index",
        is,
        "--request",
        rp.to_str().unwrap(),
    ]);
    assert_eq!(o.code, 0, "stderr={}", o.stderr);
    let v = o.json();
    for u in v["units"].as_array().unwrap() {
        assert_ne!(
            u["file"], "src/Outro.java",
            "arquivo apagado ainda entregue"
        );
    }
    std::fs::remove_dir_all(repo.parent().unwrap()).ok();
}

#[test]
fn indices_isolados_nao_se_misturam() {
    let a = fixture("iso-a");
    let b = fixture("iso-b");
    write(
        &b.0.join("src/SoNoB.java"),
        "public class SoNoB { Long getId() { return 2L; } }\n",
    );
    run(&[
        "index",
        "--repo",
        a.0.to_str().unwrap(),
        "--index",
        a.1.to_str().unwrap(),
    ]);
    run(&[
        "index",
        "--repo",
        b.0.to_str().unwrap(),
        "--index",
        b.1.to_str().unwrap(),
    ]);

    let rp = req_file(&a.0, &basic_req("CTX-RS", 4000, 40000));
    let o = run(&[
        "context",
        "--repo",
        a.0.to_str().unwrap(),
        "--index",
        a.1.to_str().unwrap(),
        "--request",
        rp.to_str().unwrap(),
    ]);
    assert_eq!(o.code, 0);
    let v = o.json();
    for u in v["units"].as_array().unwrap() {
        assert_ne!(
            u["file"], "src/SoNoB.java",
            "indice A devolveu arquivo do repo B"
        );
    }
    // E o indice de B continua intocado pelo uso de A.
    let d = run(&[
        "doctor",
        "--repo",
        b.0.to_str().unwrap(),
        "--index",
        b.1.to_str().unwrap(),
    ]);
    assert_eq!(d.code, 0);
    assert_eq!(d.json()["index"]["files"], 3);

    std::fs::remove_dir_all(a.0.parent().unwrap()).ok();
    std::fs::remove_dir_all(b.0.parent().unwrap()).ok();
}

/// `doctor` é diagnóstico: não pode escrever no índice que está inspecionando.
#[test]
fn doctor_nao_modifica_o_indice() {
    let (repo, index) = fixture("ro");
    let rs = repo.to_str().unwrap();
    let is = index.to_str().unwrap();
    run(&["index", "--repo", rs, "--index", is]);

    let before = std::fs::read(&index).unwrap();
    assert_eq!(run(&["doctor", "--repo", rs, "--index", is]).code, 0);
    let after = std::fs::read(&index).unwrap();
    assert_eq!(before, after, "doctor alterou o arquivo do indice");

    // E context tambem nao: responder nao reindexa.
    let rp = req_file(&repo, &basic_req("CTX-RS", 2000, 20000));
    run(&[
        "context",
        "--repo",
        rs,
        "--index",
        is,
        "--request",
        rp.to_str().unwrap(),
    ]);
    assert_eq!(
        before,
        std::fs::read(&index).unwrap(),
        "context alterou o indice"
    );

    std::fs::remove_dir_all(repo.parent().unwrap()).ok();
}

#[test]
fn workers_nao_mudam_o_estado_logico() {
    let (repo, index) = fixture("workers");
    let rs = repo.to_str().unwrap();
    // Índices separados, a partir do zero cada um: comparar duas execuções no MESMO índice
    // mediria o reaproveitamento do incremental, não o efeito do paralelismo.
    let a = index.with_extension("w1.sqlite");
    let b = index.with_extension("w4.sqlite");
    let one = run(&[
        "index",
        "--repo",
        rs,
        "--index",
        a.to_str().unwrap(),
        "--workers",
        "1",
    ])
    .json();
    let four = run(&[
        "index",
        "--repo",
        rs,
        "--index",
        b.to_str().unwrap(),
        "--workers",
        "4",
    ])
    .json();
    assert_eq!(one["index"]["generation"], four["index"]["generation"]);
    assert_eq!(one["counts"]["indexed"], four["counts"]["indexed"]);
    assert_eq!(one["counts"]["discovered"], four["counts"]["discovered"]);
    assert_eq!(one["counts"]["skipped"], 0);
    assert_eq!(four["counts"]["skipped"], 0);
    std::fs::remove_dir_all(repo.parent().unwrap()).ok();
}

// --- politicas ------------------------------------------------------------------------

/// A divergência entre as duas políticas é o objeto de comparação de R2, então precisa
/// existir de fato: LEX-RS entrega uma unidade por arquivo; CTX-RS limita por arquivo e
/// por isso distribui melhor.
#[test]
fn politicas_lex_e_ctx_diferem_na_diversidade() {
    let d = tmp("politicas");
    let repo = d.join("repo");
    // Um arquivo com ocorrências **separadas por mais que a janela de contexto** e outro
    // com uma só. O espaçamento importa: o CTX-RS agrupa matches próximos num único
    // trecho, então matches adjacentes não exercitam o teto por arquivo. Sem teto, o
    // arquivo grande consumiria o orçamento inteiro — o defeito medido em BASELINE.md §4.
    // 6 ocorrências a 30 linhas de distância: bem acima de 2*contexto+1 = 13.
    let mut grande = String::from("public class Grande {\n");
    for i in 0..6 {
        for j in 0..29 {
            grande.push_str(&format!("  int filler{i}_{j};\n"));
        }
        grande.push_str(&format!("  Long getId{i}() {{ return marcadortoken; }}\n"));
    }
    grande.push_str("}\n");
    write(&repo.join("Grande.java"), &grande);
    write(
        &repo.join("Pequeno.java"),
        "public class Pequeno { Long getId() { return marcadortoken; } }\n",
    );
    let index = d.join("i.sqlite");
    let rs = repo.to_str().unwrap();
    let is = index.to_str().unwrap();
    run(&["index", "--repo", rs, "--index", is]);

    let body = |policy: &str| {
        format!(
            r#"{{"schema_version":1,"intent":"localizar","query":"marcadortoken",
                "budget_tokens":8000,"max_bytes":200000,"policy":"{policy}"}}"#
        )
    };

    let p = req_file(&repo, &body("LEX-RS"));
    let lex = run(&[
        "context",
        "--repo",
        rs,
        "--index",
        is,
        "--request",
        p.to_str().unwrap(),
    ])
    .json();
    let lex_files: Vec<&str> = lex["units"]
        .as_array()
        .unwrap()
        .iter()
        .map(|u| u["file"].as_str().unwrap())
        .collect();

    let p = req_file(&repo, &body("CTX-RS"));
    let ctx = run(&[
        "context",
        "--repo",
        rs,
        "--index",
        is,
        "--request",
        p.to_str().unwrap(),
    ])
    .json();
    let ctx_units = ctx["units"].as_array().unwrap();

    // LEX-RS: exatamente uma unidade por arquivo, sem diversidade nem contexto.
    let mut uniq = lex_files.clone();
    uniq.sort_unstable();
    uniq.dedup();
    assert_eq!(
        uniq.len(),
        lex_files.len(),
        "LEX-RS deve ter 1 unidade/arquivo"
    );
    assert_eq!(lex_files.len(), 2, "LEX-RS entrega os dois arquivos");
    // CTX-RS entrega mais trechos do mesmo corpus porque fatia o arquivo grande.
    assert!(
        ctx_units.len() > lex_files.len(),
        "CTX-RS deveria entregar mais trechos: {}",
        ctx_units.len()
    );

    // CTX-RS: teto por arquivo respeitado e efetivamente atingido (é o defeito de
    // diversidade corrigido). Se o teto nunca morde, o teste não prova nada.
    let n_grande = ctx_units
        .iter()
        .filter(|u| u["file"] == "Grande.java")
        .count();
    let n_pequeno = ctx_units
        .iter()
        .filter(|u| u["file"] == "Pequeno.java")
        .count();
    assert_eq!(
        n_grande, 3,
        "CTX-RS deve cortar o arquivo grande no teto de 3"
    );
    assert_eq!(
        n_pequeno, 1,
        "o arquivo pequeno nao tem por que ser cortado"
    );
    assert!(
        ctx["omitted"]["reasons"]
            .as_array()
            .unwrap()
            .iter()
            .any(|r| r == "diversity_cap"),
        "o corte por diversidade precisa ser reportado, nao silencioso"
    );

    std::fs::remove_dir_all(&d).ok();
}

// --- repositorio real ----------------------------------------------------------------

/// Smoke no repositório real quando ele existe. Pular não é falhar: o dataset é entrada
/// externa e um checkout sem ele não deve quebrar a suíte.
#[test]
fn repositorio_real_siga_quando_disponivel() {
    let ds = std::env::var("ARCHATLAS_DATASET")
        .map(PathBuf::from)
        .unwrap_or_else(|_| {
            Path::new(env!("CARGO_MANIFEST_DIR"))
                .join("../../..")
                .join("siga")
        });
    if !ds.join("siga-ex/src/main/java").is_dir() {
        eprintln!("dataset ausente em {}; teste pulado", ds.display());
        return;
    }
    let d = tmp("real");
    let index = d.join("siga.sqlite");
    let rs = ds.to_str().unwrap();
    let is = index.to_str().unwrap();

    let idx = run(&["index", "--repo", rs, "--index", is]);
    assert_eq!(idx.code, 0, "stderr={}", idx.stderr);
    let v = idx.json();
    assert!(
        v["counts"]["discovered"].as_u64().unwrap() > 100,
        "esperava centenas de arquivos Java: {v}"
    );
    assert_eq!(v["counts"]["binary"], 0);

    let rp = req_file(&d, &basic_req("CTX-RS", 2000, 20000));
    let o = run(&[
        "context",
        "--repo",
        rs,
        "--index",
        is,
        "--request",
        rp.to_str().unwrap(),
    ]);
    assert_eq!(o.code, 0, "stderr={}", o.stderr);
    let c = o.json();
    assert!(!c["units"].as_array().unwrap().is_empty());
    let emmited = o.stdout.len() - 1;
    assert_eq!(
        c["budget"]["used_bytes"].as_u64().unwrap() as usize,
        emmited
    );
    for u in c["units"].as_array().unwrap() {
        let rel = u["file"].as_str().unwrap();
        assert!(
            !rel.starts_with('/') && !rel.contains(".."),
            "path ruim: {rel}"
        );
        assert!(
            ds.join(rel).exists(),
            "unidade aponta para arquivo inexistente: {rel}"
        );
    }

    std::fs::remove_dir_all(&d).ok();
}
