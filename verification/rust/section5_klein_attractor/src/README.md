# Ⓜ️ Haskell · Section 5 · src — the Section Binary

> **Navigation:** [`verification`](../../../README.md) › [`rust`](../../README.md) › [`section5_klein_attractor`](../README.md) › **`src`**

![Rust](https://img.shields.io/badge/Rust-1.75+-informational?style=flat-square&logo=rust&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **source folder of the Section 5 Haskell binary** — the executable module that prints the section banner, computes the section's quantities, asserts its properties with `[PASS]`/`[FAIL]` lines, and ends with the framework's `JSON:` verdict. Written in idiomatic, dependency-free Haskell (1.75+); the parent folder holds the build wiring.

## 🔬 Section Context — Where This Port Sits

**Where it sits.** Section 5 of the framework covers **the Klein attractor dynamical system with ergodic-theoretic structure**. Its central quantities are the attractor's invariant-measure behaviour and the bridge connecting its dynamics back to the Navier–Stokes setting; what this port asserts (or proves) is ergodicity scaffolding, invariant-measure identities and the structural lemmas of the Klein–NS bridge. The same assertions exist in every peer language of the matrix, each in its own idiom: [Python](../../../section5_klein_attractor/python/README.md) · [Lean 4](../../../lean4/ResearchPapersVerification/Section5_KleinAttractor/README.md) · [Coq/Rocq](../../../coq/section5_klein_attractor/README.md) · [Isabelle-HOL](../../../isabelle/Section5_KleinAttractor/README.md) · [Agda](../../../agda/Section5_KleinAttractor/README.md) · [C++](../../../cpp/section5_klein_attractor/README.md) · [Haskell](../../../haskell/Section5_KleinAttractor/README.md). Agreement between all ports is enforced by the cross-language validator (`../../../tests/`) and the `ci-cross-language.yml` workflow.

**What you will see.** Run this port and you get: a banner identifying the section and language; the computed values printed at full precision; one `[PASS]`/`[FAIL]` line per assertion; and a final `JSON: {"section": 5, "language": "rust", "values": {…}, "all_passed": …}` verdict line. Exit status is 0 only when every assertion passed — CI treats anything else as a failure.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`main.rs`](main.rs) | 768 B | Section 5 Haskell source — the complete section verifier |

## ▶️ How to Run

```bash
cargo run --release --manifest-path verification/rust/Cargo.toml --bin <section>
```

## 🔗 Cross-References

- [Section folder](../README.md)
- [Haskell layer](../../README.md)

## 🇷🇺 Краткое резюме (Russian Summary)

Исходник бинарника раздела 5 на Haskell (main.rs); контракт PASS/JSON как во всех портах.

---

<div align="center">

**[⬆ Back to top](#-haskell--section-5--src--the-section-binary)** · 
**[Repository root](../../../README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>
<!-- doc-enhancer:block v1 (автоматический блок; файлы лицензии не затрагиваются) -->

---

## 🧭 Навигация и быстрые ссылки (auto)

- 🏠 [Корень репозитория](../../../../../README.md)
- 📖 [Как верифицируются утверждения](../../../../../verification/README.md)
- 📄 [Статьи (PDF)](../../../../../papers/README.md) · 📚 [Монографии](../../../../../docs/README.md) · 🧾 [LaTeX](../../../../../src/README.md)
- ⚖️ [Лицензия IPL-RP-1.0](../../../../../LICENSE.md) — просмотр, одна резервная копия и цитирование с атрибуцией разрешены; остальное — только с письменного согласия автора.

*Блок добавлен автоматически (`doc-enhancer v1`); к лицензии отношения не имеет и её не изменяет. Повторный запуск скрипта блок не дублирует.*

