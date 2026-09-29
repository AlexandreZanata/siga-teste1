// SPDX-License-Identifier: Apache-2.0
//! Entrada do binário: repassa argv para `cli::run` e traduz o resultado em código de saída.
//!
//! O `return` do processo é o único lugar que decide o status; `cli` nunca chama `exit`,
//! o que mantém os códigos do contrato testáveis por integração.

use std::io::Write;

fn main() {
    let args: Vec<std::ffi::OsString> = std::env::args_os().collect();
    let code = archatlas::cli::run(args);
    // Drena stderr explicitamente: sem isto uma mensagem de diagnóstico pode se perder
    // quando o processo termina logo depois de escrever.
    let _ = std::io::stderr().flush();
    std::process::exit(code);
}
