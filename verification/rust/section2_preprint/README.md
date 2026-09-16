# Ⓜ️ Rust · Section 2 — Preprint NSE

> **Navigation:** [`verification`](../../README.md) › [`rust`](../README.md) › **`section2_preprint`**

![Rust](https://img.shields.io/badge/Rust-1.75+-informational?style=flat-square&logo=rust&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![Section](https://img.shields.io/badge/Section-2-blue?style=flat-square)

The **Rust port of Section 2** — Preprint NSE — the Regularity Argument Chain. This folder is the section's slot in the Rust layer of the framework: the file below states exactly the assertions the Python reference makes, in Rust idiom — memory-safe port using `std` only; the crate builds each section as its own binary.

The folder pairs the manifest with `src/` (see sibling folder) — Cargo expects the binary source under `src/main.rs`; the parent crate's `Cargo.toml` wires it as a section binary.

## 🔬 Section Context — Where This Port Sits

**Where it sits.** Section 2 of the framework covers **the analytical chain behind global regularity of the 3D Navier–Stokes equations**. Its central quantities are the stabilisation mechanism induced by θ_b ≈ 7.07° and the 3.5× reduction of the BKM blow-up criterion integral; what this port asserts (or proves) is structural lemmas of the preprint: positivity and scale of the correction, unit-norm rotation axis, and the energy-estimate scaffolding. The same assertions exist in every peer language of the matrix, each in its own idiom: [Python](../../section2_preprint/python/README.md) · [Lean 4](../../lean4/ResearchPapersVerification/Section2_PreprintNSE/README.md) · [Coq/Rocq](../../coq/section2_preprint/README.md) · [Isabelle-HOL](../../isabelle/Section2_PreprintNSE/README.md) · [Agda](../../agda/Section2_PreprintNSE/README.md) · [C++](../../cpp/section2_preprint/README.md) · [Haskell](../../haskell/Section2_PreprintNSE/README.md). Agreement between all ports is enforced by the cross-language validator (`../../tests/`) and the `ci-cross-language.yml` workflow.

**What you will see.** Run this port and you get: a banner identifying the section and language; the computed values printed at full precision; one `[PASS]`/`[FAIL]` line per assertion; and a final `JSON: {"section": 2, "language": "rust", "values": {…}, "all_passed": …}` verdict line. Exit status is 0 only when every assertion passed — CI treats anything else as a failure.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`Cargo.toml`](Cargo.toml) | 136 B | [package] name = "section2_preprint" version = "2.0.0" edition = "2021" [[bin]] name = "verify_section2_preprint" path = "src/main.rs" |
| [`src/`](src/) | — | subdirectory with 2 files (see its own README) |

## 🗂 Directory Layout

```
section2_preprint/
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
- [Python reference for this section](../../section2_preprint/python/README.md)
- [Framework root](../../README.md)

## 🇷🇺 Краткое резюме (Russian Summary)

Порт раздела 2 на Rust: один файл с теоремами/проверками раздела «Preprint NSE»; контекст раздела — в одноимённом блоке; сборка и вывод — как в README слоя Rust.

---

<div align="center">

**[⬆ Back to top](#-rust--section-2--preprint-nse)** · 
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

