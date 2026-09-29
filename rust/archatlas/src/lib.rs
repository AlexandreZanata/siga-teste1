// SPDX-License-Identifier: Apache-2.0
//! Núcleo da CLI Rust `archatlas` — fatia R1.
//!
//! Implementa `doctor`, `index` e `context` conforme `research/rust/CLI_CONTRACT.md`
//! (`CLI_CONTRACT/1`). O caminho de execução não chama Python.
//!
//! Invariantes que valem para todo o crate:
//! - `file` em qualquer resposta é **relativo à raiz do repo**; nunca absoluto, nunca `..`.
//! - Orçamento é medido sobre a **serialização final**, não sobre a soma dos itens (contrato §6).
//! - Nenhum comando devolve JSON de sucesso quando não há resposta verificada.
//! - Tempo decorrido **não** entra no JSON: stdout precisa ser determinístico para replay.

pub mod cli;
pub mod discovery;
pub mod languages;
pub mod pack;
pub mod request;
pub mod retrieve;
pub mod snapshot;
pub mod store;

/// Nome do executável, usado em `env.tool` e nas mensagens de stderr.
pub const TOOL: &str = "archatlas";

/// Versão do binário. Vem do `Cargo.toml`; sai em `doctor` para o runner registrar.
pub const TOOL_VERSION: &str = env!("CARGO_PKG_VERSION");

/// Versão do schema de pedido/resposta. Divergência no pedido é erro de cliente (código 2).
pub const SCHEMA_VERSION: u32 = 1;

/// Estimativa declarada de tokens, usada **somente** quando não há tokenizer exato.
///
/// Aplicada à serialização final — nunca a itens isolados. O contrato exige
/// `tokenizer_is_exact: false` sempre que este caminho é usado, para que o piloto
/// não registre uma alegação de orçamento rígido em tokens sem tokenizer correspondente.
#[inline]
pub fn token_estimate(bytes: usize) -> u64 {
    (bytes as u64) / 4
}
