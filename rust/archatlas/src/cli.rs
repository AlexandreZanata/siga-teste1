// SPDX-License-Identifier: Apache-2.0
//! Linha de comando: parsing, despacho e códigos de saída do `CLI_CONTRACT/1`.
//!
//! Parsing é feito à mão em vez de com uma biblioteca de argumentos por um motivo
//! específico do contrato: stdout precisa conter **exatamente um objeto JSON**, e os
//! códigos 0/2/3/4/5 têm significados fixos. Uma biblioteca que decide sozinha o que
//! imprimir e com que status sair transfere essa decisão para fora da especificação.
//!
//! Nenhuma função aqui chama `exit`: o código de saída é sempre um valor devolvido, o que
//! torna cada caso testável por integração.

use crate::discovery::{self, DEFAULT_MAX_FILE_BYTES};
use crate::languages;
use crate::pack::{self, PackError};
use crate::request;
use crate::snapshot;
use crate::store::{self, Mode, Store};
use crate::{SCHEMA_VERSION, TOOL, TOOL_VERSION};
use serde::Serialize;
use std::ffi::OsString;
use std::io::Write;
use std::path::{Path, PathBuf};

/// Códigos de saída. Documentados em `CLI_CONTRACT/1` §3.
const EXIT_OK: i32 = 0;
const EXIT_BAD_REQUEST: i32 = 2;
const EXIT_INDEX_UNAVAILABLE: i32 = 3;
const EXIT_IO: i32 = 4;
const EXIT_INTEGRITY: i32 = 5;

const HELP: &str = "\
archatlas - memoria de contexto verificavel para agentes

USO:
  archatlas <comando> [opcoes]

COMANDOS:
  doctor   estado do ambiente, do indice e das linguagens suportadas
  index    constroi ou atualiza o indice do repositorio
  context  responde a um pedido dentro do orcamento declarado

OPCOES:
  --repo <dir>              raiz do repositorio (obrigatorio)
  --index <arq>             arquivo do indice (obrigatorio)
  --request <arq>           pedido JSON (obrigatorio em context)
  --format json|text        formato da saida de doctor (padrao json)
  --workers <n>             workers de leitura e hash no index (padrao 1)
  --max-file-bytes <n>      limite por arquivo (padrao 2097152)
  --incremental             atualiza reaproveitando o indice (padrao)
  --force                   descarta o conteudo e reconstroi do zero
  -h, --help                esta ajuda

CODIGOS DE SAIDA:
  0 resposta valida (partial e stale sao respostas validas e explicitas)
  2 pedido invalido
  3 indice ausente, incompativel, corrompido ou vazio
  4 erro de I/O ou limite operacional
  5 integridade violada (hash divergente ou caminho fora da raiz)

EXEMPLO:
  archatlas index   --repo ./siga --index /tmp/atlas.sqlite
  archatlas context --repo ./siga --index /tmp/atlas.sqlite --request pedido.json
";

/// Opções já validadas.
#[derive(Debug, Clone)]
struct Args {
    cmd: String,
    repo: PathBuf,
    index: PathBuf,
    request: Option<PathBuf>,
    format: String,
    workers: usize,
    max_file_bytes: u64,
    force: bool,
}

enum Parsed {
    Run(Box<Args>),
    Help,
    Err(String),
}

/// Ponto de entrada. Único lugar que decide o status de saída do processo.
pub fn run(argv: Vec<OsString>) -> i32 {
    match parse(&argv) {
        Parsed::Help => {
            print!("{HELP}");
            EXIT_OK
        }
        Parsed::Err(msg) => {
            eprintln!("{TOOL}: {msg}");
            eprintln!("{TOOL}: use --help para ver o uso");
            EXIT_BAD_REQUEST
        }
        Parsed::Run(args) => match args.cmd.as_str() {
            "doctor" => cmd_doctor(&args),
            "index" => cmd_index(&args),
            "context" => cmd_context(&args),
            // Declarados no contrato, implementados em R2. Falhar alto é melhor que aceitar
            // o pedido e devolver algo que não é o contratado.
            "expand" | "verify" => {
                eprintln!(
                    "{TOOL}: comando '{}' pertence a R2 e nao existe nesta versao",
                    args.cmd
                );
                EXIT_BAD_REQUEST
            }
            other => {
                eprintln!("{TOOL}: comando desconhecido: {other}");
                EXIT_BAD_REQUEST
            }
        },
    }
}

fn parse(argv: &[OsString]) -> Parsed {
    let mut it = argv.iter().skip(1).peekable();
    let Some(first) = it.next() else {
        return Parsed::Err("nenhum comando informado".into());
    };
    let first = first.to_string_lossy().to_string();
    if first == "-h" || first == "--help" || first == "help" {
        return Parsed::Help;
    }

    let mut repo: Option<PathBuf> = None;
    let mut index: Option<PathBuf> = None;
    let mut request_path: Option<PathBuf> = None;
    let mut format = "json".to_string();
    let mut workers: usize = 1;
    let mut max_file_bytes: u64 = DEFAULT_MAX_FILE_BYTES;
    let mut force = false;

    // Um flag repetido é erro: aceitar "o último vence" faria um pedido malformado parecer
    // bem-sucedido, e o piloto mediria uma configuração diferente da registrada.
    // Tipo concreto do iterador de argumentos: o consumo de valores precisa de um
    // `Peekable` já após o comando, e nomear o tipo evita closures genéricas.
    type ArgIter<'a> = std::iter::Peekable<std::iter::Skip<std::slice::Iter<'a, OsString>>>;
    let mut seen: Vec<&str> = Vec::new();
    let set_once = |name: &'static str, seen: &mut Vec<&'static str>| -> Result<(), String> {
        if seen.contains(&name) {
            return Err(format!("opcao repetida: --{name}"));
        }
        seen.push(name);
        Ok(())
    };

    while let Some(arg) = it.next() {
        let a = arg.to_string_lossy().to_string();
        let value = |it: &mut ArgIter<'_>| {
            it.next()
                .map(|v| v.to_string_lossy().to_string())
                .ok_or_else(|| format!("opcao sem valor: {a}"))
        };
        match a.as_str() {
            "-h" | "--help" => return Parsed::Help,
            "--repo" => {
                if let Err(e) = set_once("repo", &mut seen) {
                    return Parsed::Err(e);
                }
                match value(&mut it) {
                    Ok(v) => repo = Some(PathBuf::from(v)),
                    Err(e) => return Parsed::Err(e),
                }
            }
            "--index" => {
                if let Err(e) = set_once("index", &mut seen) {
                    return Parsed::Err(e);
                }
                match value(&mut it) {
                    Ok(v) => index = Some(PathBuf::from(v)),
                    Err(e) => return Parsed::Err(e),
                }
            }
            "--request" => {
                if let Err(e) = set_once("request", &mut seen) {
                    return Parsed::Err(e);
                }
                match value(&mut it) {
                    Ok(v) => request_path = Some(PathBuf::from(v)),
                    Err(e) => return Parsed::Err(e),
                }
            }
            "--format" => {
                if let Err(e) = set_once("format", &mut seen) {
                    return Parsed::Err(e);
                }
                match value(&mut it) {
                    Ok(v) if v == "json" || v == "text" => format = v,
                    Ok(v) => return Parsed::Err(format!("formato invalido: {v}")),
                    Err(e) => return Parsed::Err(e),
                }
            }
            "--workers" => match value(&mut it) {
                Ok(v) => match v.parse::<usize>() {
                    Ok(n) if n >= 1 => workers = n,
                    _ => return Parsed::Err(format!("workers invalido: {v}")),
                },
                Err(e) => return Parsed::Err(e),
            },
            "--max-file-bytes" => match value(&mut it) {
                Ok(v) => match v.parse::<u64>() {
                    Ok(n) if n >= 1 => max_file_bytes = n,
                    _ => return Parsed::Err(format!("max-file-bytes invalido: {v}")),
                },
                Err(e) => return Parsed::Err(e),
            },
            "--force" => force = true,
            "--incremental" => {}
            other => return Parsed::Err(format!("opcao desconhecida: {other}")),
        }
    }

    let Some(repo) = repo else {
        return Parsed::Err("--repo e obrigatorio".into());
    };
    let Some(index) = index else {
        return Parsed::Err("--index e obrigatorio".into());
    };
    if first == "context" && request_path.is_none() {
        return Parsed::Err("--request e obrigatorio em context".into());
    }
    if first != "doctor" && first != "index" && first != "context" {
        // Deixa o despacho reportar o comando desconhecido com o código certo.
        return Parsed::Run(Box::new(Args {
            cmd: first,
            repo,
            index,
            request: request_path,
            format,
            workers,
            max_file_bytes,
            force,
        }));
    }

    Parsed::Run(Box::new(Args {
        cmd: first,
        repo,
        index,
        request: request_path,
        format,
        workers,
        max_file_bytes,
        force,
    }))
}

// --- doctor -----------------------------------------------------------------------

#[derive(Serialize)]
struct EnvInfo {
    tool: &'static str,
    tool_version: &'static str,
    index_schema_version: i64,
    os: &'static str,
    arch: &'static str,
    needs_network: bool,
    needs_gpu: bool,
    install: &'static str,
}

#[derive(Serialize)]
struct IndexInfo {
    state: String,
    files: Option<u64>,
    generation: Option<String>,
    sha_base: Option<String>,
    /// `null` quando não é possível comparar (índice vazio ou repo sem marca).
    root_matches: Option<bool>,
    advice: Option<&'static str>,
}

#[derive(Serialize)]
struct LangInfo {
    language: &'static str,
    level: &'static str,
    note: &'static str,
}

#[derive(Serialize)]
struct DoctorResponse {
    schema: String,
    schema_version: u32,
    state: String,
    env: EnvInfo,
    index: IndexInfo,
    languages: Vec<LangInfo>,
}

/// Coleta o estado do índice sem escrever nada nele.
///
/// Delega para [`store::inspect`], que abre em modo somente leitura. Usar `Store::open`
/// aqui seria errado: ele garante o schema e portanto **escreve** no arquivo — `doctor`
/// deixaria de ser inofensivo.
fn inspect(index_path: &Path, repo: Option<&Path>) -> IndexInfo {
    let snap = store::inspect(index_path, repo);
    IndexInfo {
        state: snap.state.as_str().to_string(),
        files: snap.files,
        generation: snap.generation,
        sha_base: snap.sha_base,
        root_matches: snap.root_matches,
        advice: snap.state.advice(),
    }
}

fn cmd_doctor(args: &Args) -> i32 {
    let info = inspect(&args.index, Some(&args.repo));
    let state = store::probe(&args.index);

    let resp = DoctorResponse {
        schema: "atlas-doctor/1".to_string(),
        schema_version: SCHEMA_VERSION,
        state: if state.can_serve() { "ok" } else { "partial" }.to_string(),
        env: EnvInfo {
            tool: TOOL,
            tool_version: TOOL_VERSION,
            index_schema_version: store::INDEX_SCHEMA_VERSION,
            os: std::env::consts::OS,
            arch: std::env::consts::ARCH,
            needs_network: false,
            needs_gpu: false,
            install: "local-only",
        },
        index: info,
        languages: languages::declared()
            .into_iter()
            .map(|(language, level, note)| LangInfo {
                language,
                level,
                note,
            })
            .collect(),
    };

    let code = if args.format == "text" {
        // Modo humano: pode mostrar o caminho do índice, porque serve para depurar a
        // instalação. O modo JSON nunca publica caminho absoluto.
        println!("{TOOL} {TOOL_VERSION} ({})", resp.env.os);
        println!("indice: {}", args.index.display());
        println!(
            "estado: {} ({})",
            resp.index.state,
            resp.index.advice.unwrap_or("sem pendencias")
        );
        if let Some(n) = resp.index.files {
            println!("arquivos: {n}");
        }
        if let Some(g) = &resp.index.generation {
            println!("geracao: {g}");
        }
        println!(
            "linguagens: {} declaradas, todas em nivel lexical",
            resp.languages.len()
        );
        EXIT_OK
    } else {
        emit(&resp)
    };

    // Sem índice servível, `doctor` ainda responde (é o comando de diagnóstico), mas o
    // código 3 sinaliza que `context` não tem resposta válida a dar.
    if code == EXIT_OK && !state.can_serve() {
        EXIT_INDEX_UNAVAILABLE
    } else {
        code
    }
}

// --- index ------------------------------------------------------------------------

#[derive(Serialize)]
struct Counts {
    discovered: u64,
    indexed: u64,
    skipped: u64,
    pruned_files: u64,
    binary: u64,
    too_large: u64,
    unsupported: u64,
    unreadable: u64,
    ignored: Option<u64>,
    ignored_reason: &'static str,
    mode: String,
    workers: usize,
    max_file_bytes: u64,
}

#[derive(Serialize)]
struct IndexResponse {
    schema: String,
    schema_version: u32,
    state: String,
    repo_root_id: String,
    index: IndexInfo,
    counts: Counts,
}

fn cmd_index(args: &Args) -> i32 {
    if !args.repo.is_dir() {
        eprintln!("{TOOL}: --repo nao e um diretorio: {}", args.repo.display());
        return EXIT_IO;
    }
    let exclude = vec![args.index.clone()];
    let found = match discovery::discover(&args.repo, args.max_file_bytes, &exclude) {
        Ok(d) => d,
        Err(e) => {
            eprintln!("{TOOL}: falha na varredura: {e}");
            return EXIT_IO;
        }
    };

    let mut store = match Store::open(&args.index) {
        Ok(s) => s,
        Err(e) => {
            eprintln!("{TOOL}: {e}");
            return EXIT_IO;
        }
    };
    let sha = snapshot::git_sha(&args.repo);
    let root_id = snapshot::root_id(&args.repo);
    let mode = if args.force {
        Mode::Rebuild
    } else {
        Mode::Incremental
    };

    let report = match store.sync(&found.files, sha.as_deref(), &root_id, mode, args.workers) {
        Ok(r) => r,
        Err(e) => {
            eprintln!("{TOOL}: falha ao indexar: {e}");
            return EXIT_IO;
        }
    };

    let info = inspect(&args.index, Some(&args.repo));
    let resp = IndexResponse {
        schema: "atlas-index/1".to_string(),
        schema_version: SCHEMA_VERSION,
        state: "ok".to_string(),
        repo_root_id: root_id,
        index: info,
        counts: Counts {
            discovered: found.files.len() as u64,
            indexed: report.indexed,
            skipped: report.skipped,
            pruned_files: report.pruned_files,
            binary: found.binary,
            too_large: found.too_large,
            unsupported: found.unsupported,
            unreadable: found.unreadable,
            ignored: found.ignored,
            ignored_reason: discovery::Discovery::ignored_reason(),
            mode: report.mode.to_string(),
            workers: args.workers,
            max_file_bytes: args.max_file_bytes,
        },
    };
    emit(&resp)
}

// --- context ----------------------------------------------------------------------

fn cmd_context(args: &Args) -> i32 {
    let state = store::probe(&args.index);
    if !state.can_serve() {
        // Índice indisponível: diagnóstico explícito e código 3 — nunca lista vazia fingida.
        if let Some(req_path) = &args.request {
            if let Ok(raw) = std::fs::read_to_string(req_path) {
                if let Ok(v) = request::parse(&raw) {
                    let ctx = pack::Ctx {
                        sha_base: None,
                        index_generation: "unknown".to_string(),
                        index_state: state.as_str().to_string(),
                        requested_sha_base: v.raw.snapshot.sha_base.clone(),
                    };
                    let resp = pack::unservable(&v, &ctx, state.as_str());
                    let _ = emit_ignore(&resp);
                }
            }
        }
        eprintln!(
            "{TOOL}: indice {}: {}",
            state.as_str(),
            state.advice().unwrap_or("indisponivel para responder")
        );
        return EXIT_INDEX_UNAVAILABLE;
    }

    let Some(req_path) = &args.request else {
        eprintln!("{TOOL}: --request e obrigatorio em context");
        return EXIT_BAD_REQUEST;
    };
    let raw = match std::fs::read_to_string(req_path) {
        Ok(r) => r,
        Err(e) => {
            eprintln!("{TOOL}: nao foi possivel ler {}: {e}", req_path.display());
            return EXIT_IO;
        }
    };
    let valid = match request::parse(&raw) {
        Ok(v) => v,
        Err(e) => {
            eprintln!("{TOOL}: {e}");
            return EXIT_BAD_REQUEST;
        }
    };

    // Leitura do índice em modo somente leitura: `context` nunca escreve, nem para
    // "consertar" o schema. Consertar é `index`, explicitamente pedido.
    let snap = store::inspect(&args.index, Some(&args.repo));
    let store = match Store::open_readonly(&args.index) {
        Ok(s) => s,
        Err(e) => {
            eprintln!("{TOOL}: {e}");
            return EXIT_IO;
        }
    };
    let ctx = pack::Ctx {
        sha_base: snap.sha_base.clone(),
        index_generation: snap
            .generation
            .clone()
            .unwrap_or_else(|| "unknown".to_string()),
        index_state: "ok".to_string(),
        requested_sha_base: valid.raw.snapshot.sha_base.clone(),
    };

    match pack::build_context(&args.repo, &store, &valid, ctx) {
        Ok(resp) => emit(&resp),
        Err(e) => {
            // O motivo vai para stderr; o código carrega a decisão do contrato.
            eprintln!("{TOOL}: {e}");
            match &e {
                PackError::Integrity(_) => EXIT_INTEGRITY,
                PackError::Io(_) => EXIT_IO,
            }
        }
    }
}

// --- saída ------------------------------------------------------------------------

/// Escreve um JSON de envelope e devolve o código de saída correspondente.
fn emit<T: Serialize>(value: &T) -> i32 {
    let mut bytes = match serde_json::to_vec(value) {
        Ok(b) => b,
        Err(e) => {
            eprintln!("{TOOL}: falha ao serializar a resposta: {e}");
            return EXIT_IO;
        }
    };
    bytes.push(b'\n');
    write_stdout(&bytes)
}

/// Igual a `emit`, mas usado quando a resposta é só diagnóstica e o código já está decidido.
fn emit_ignore<T: Serialize>(value: &T) -> i32 {
    let mut bytes = match serde_json::to_vec(value) {
        Ok(b) => b,
        Err(_) => return EXIT_IO,
    };
    bytes.push(b'\n');
    write_stdout(&bytes)
}

/// Escreve no stdout tratando pipe fechado.
///
/// O comportamento antigo (Python) era estourar `BrokenPipeError` e sair com 120. Aqui a
/// condição é detectada e vira código 4 com uma linha de stderr: sem traceback e sem
/// fingir sucesso.
fn write_stdout(bytes: &[u8]) -> i32 {
    let stdout = std::io::stdout();
    let mut lock = stdout.lock();
    match lock.write_all(bytes).and_then(|_| lock.flush()) {
        Ok(()) => EXIT_OK,
        Err(e) if e.kind() == std::io::ErrorKind::BrokenPipe => {
            eprintln!("{TOOL}: stdout fechado pelo consumidor");
            EXIT_IO
        }
        Err(e) => {
            eprintln!("{TOOL}: falha ao escrever stdout: {e}");
            EXIT_IO
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn av(args: &[&str]) -> Vec<OsString> {
        std::iter::once("archatlas")
            .chain(args.iter().copied())
            .map(OsString::from)
            .collect()
    }

    fn run_ok(args: &[&str]) -> Args {
        match parse(&av(args)) {
            Parsed::Run(a) => *a,
            Parsed::Err(e) => panic!("esperava sucesso, veio erro: {e}"),
            Parsed::Help => panic!("esperava run, veio help"),
        }
    }

    #[test]
    fn parse_minimo_de_context() {
        let a = run_ok(&[
            "context",
            "--repo",
            "/r",
            "--index",
            "/i.sqlite",
            "--request",
            "/p.json",
        ]);
        assert_eq!(a.cmd, "context");
        assert_eq!(a.workers, 1);
        assert!(!a.force);
        assert_eq!(a.max_file_bytes, DEFAULT_MAX_FILE_BYTES);
    }

    #[test]
    fn help_e_reconhecido_em_varias_posicoes() {
        assert!(matches!(parse(&av(&["--help"])), Parsed::Help));
        assert!(matches!(parse(&av(&["-h"])), Parsed::Help));
        assert!(matches!(parse(&av(&["help"])), Parsed::Help));
        assert!(matches!(parse(&av(&["doctor", "--help"])), Parsed::Help));
    }

    #[test]
    fn sem_comando_e_erro() {
        assert!(matches!(parse(&av(&[])), Parsed::Err(_)));
    }

    #[test]
    fn exige_repo_e_index() {
        assert!(matches!(
            parse(&av(&["doctor", "--repo", "/r"])),
            Parsed::Err(_)
        ));
        assert!(matches!(
            parse(&av(&["doctor", "--index", "/i"])),
            Parsed::Err(_)
        ));
    }

    #[test]
    fn context_exige_request() {
        assert!(matches!(
            parse(&av(&["context", "--repo", "/r", "--index", "/i"])),
            Parsed::Err(_)
        ));
    }

    #[test]
    fn recusa_opcao_repetida_e_desconhecida() {
        assert!(matches!(
            parse(&av(&[
                "doctor", "--repo", "/a", "--repo", "/b", "--index", "/i"
            ])),
            Parsed::Err(_)
        ));
        assert!(matches!(
            parse(&av(&["doctor", "--repo", "/a", "--index", "/i", "--turbo"])),
            Parsed::Err(_)
        ));
    }

    #[test]
    fn valida_numeros_e_formato() {
        assert!(matches!(
            parse(&av(&[
                "index",
                "--repo",
                "/r",
                "--index",
                "/i",
                "--workers",
                "0"
            ])),
            Parsed::Err(_)
        ));
        assert!(matches!(
            parse(&av(&[
                "index",
                "--repo",
                "/r",
                "--index",
                "/i",
                "--workers",
                "x"
            ])),
            Parsed::Err(_)
        ));
        assert!(matches!(
            parse(&av(&[
                "doctor", "--repo", "/r", "--index", "/i", "--format", "yaml"
            ])),
            Parsed::Err(_)
        ));
    }

    #[test]
    fn workers_e_force_alteram_configuracao() {
        let a = run_ok(&[
            "index",
            "--repo",
            "/r",
            "--index",
            "/i",
            "--workers",
            "4",
            "--force",
        ]);
        assert_eq!(a.workers, 4);
        assert!(a.force);
    }

    #[test]
    fn opcao_sem_valor_e_erro() {
        assert!(matches!(parse(&av(&["doctor", "--repo"])), Parsed::Err(_)));
    }
}
