# Ⓜ️ Rust · Section 6 — Riemann Zeros

> **Navigation:** [`verification`](../../README.md) › [`rust`](../README.md) › **`section6_riemann_zeros`**

![Rust](https://img.shields.io/badge/Rust-1.75+-informational?style=flat-square&logo=rust&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![Section](https://img.shields.io/badge/Section-6-blue?style=flat-square)

The **Rust port of Section 6** — Riemann Zeros — the Hilbert–Pólya Programme. This folder is the section's slot in the Rust layer of the framework: the file below states exactly the assertions the Python reference makes, in Rust idiom — memory-safe port using `std` only; the crate builds each section as its own binary.

The folder pairs the manifest with `src/` (see sibling folder) — Cargo expects the binary source under `src/main.rs`; the parent crate's `Cargo.toml` wires it as a section binary.

## 🔬 Section Context — Where This Port Sits

**Where it sits.** Section 6 of the framework covers **the spectral correspondence between the AB-Cloud and the non-trivial zeros of the Riemann zeta function**. Its central quantities are the Hilbert–Pólya realisation, the Montgomery–Dyson GUE correspondence and the statistical identity of the two spectra; what this port asserts (or proves) is spectral-correspondence identities and the statistical machinery (⟨r⟩, KS, permutation tests) in constructive and classical form. The same assertions exist in every peer language of the matrix, each in its own idiom: [Python](../../section6_riemann_zeros/python/README.md) · [Lean 4](../../lean4/ResearchPapersVerification/Section6_RiemannZeros/README.md) · [Coq/Rocq](../../coq/section6_riemann_zeros/README.md) · [Isabelle-HOL](../../isabelle/Section6_RiemannZeros/README.md) · [Agda](../../agda/Section6_RiemannZeros/README.md) · [C++](../../cpp/section6_riemann_zeros/README.md) · [Haskell](../../haskell/Section6_RiemannZeros/README.md). Agreement between all ports is enforced by the cross-language validator (`../../tests/`) and the `ci-cross-language.yml` workflow.

**What you will see.** Run this port and you get: a banner identifying the section and language; the computed values printed at full precision; one `[PASS]`/`[FAIL]` line per assertion; and a final `JSON: {"section": 6, "language": "rust", "values": {…}, "all_passed": …}` verdict line. Exit status is 0 only when every assertion passed — CI treats anything else as a failure.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`Cargo.toml`](Cargo.toml) | 146 B | [package] name = "section6_riemann_zeros" version = "2.0.0" edition = "2021" [[bin]] name = "verify_section6_riemann_zeros" path = "src/main.rs" |
| [`src/`](src/) | — | subdirectory with 2 files (see its own README) |

## 🗂 Directory Layout

```
section6_riemann_zeros/
├── src/   # 2 files
│   ├── main.rs
│   └── README.md  (this file)
├── Cargo.toml
└── README.md  (this file)
```

## ▶️ How to Run

```bash
cargo run --release --manifest-path verification/rust/Cargo.toml --bin <section>
```

## 🔗 Cross-References

- [Rust layer README](../README.md)
- [Python reference for this section](../../section6_riemann_zeros/python/README.md)
- [Framework root](../../README.md)

## 🇷🇺 Краткое резюме (Russian Summary)

Порт раздела 6 на Rust: один файл с теоремами/проверками раздела «Riemann Zeros»; контекст раздела — в одноимённом блоке; сборка и вывод — как в README слоя Rust.

---

<div align="center">

**[⬆ Back to top](#-rust--section-6--riemann-zeros)** · 
**[Repository root](../../README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>
<!-- doc-enhancer:block v1 (автоматический блок; файлы лицензии не затрагиваются) -->

---

## 🧭 Навигация и быстрые ссылки (auto)

- 🏠 [Корень репозитория](../../../../README.md)
- 📖 [Как верифицируются утверждения](../../../../verification/README.md)
- 📄 [Статьи (PDF)](../../../../papers/README.md) · 📚 [Монографии](../../../../docs/README.md) · 🧾 [LaTeX](../../../../src/README.md)
- ⚖️ [Лицензия IPL-RP-1.0](../../../../LICENSE.md) — просмотр, одна резервная копия и цитирование с атрибуцией разрешены; остальное — только с письменного согласия автора.

*Блок добавлен автоматически (`doc-enhancer v1`); к лицензии отношения не имеет и её не изменяет. Повторный запуск скрипта блок не дублирует.*

