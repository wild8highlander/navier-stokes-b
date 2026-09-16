# Ⓜ️ Haskell · Section 1 · src — the Section Binary

> **Navigation:** [`verification`](../../../README.md) › [`haskell`](../../README.md) › [`Section1_CorrectionB`](../README.md) › **`src`**

![Haskell](https://img.shields.io/badge/Haskell-9.4-informational?style=flat-square&logo=haskell&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **source folder of the Section 1 Haskell binary** — the executable module that prints the section banner, computes the section's quantities, asserts its properties with `[PASS]`/`[FAIL]` lines, and ends with the framework's `JSON:` verdict. Written in idiomatic, dependency-free Haskell (9.4); the parent folder holds the build wiring.

## 🔬 Section Context — Where This Port Sits

**Where it sits.** Section 1 of the framework covers **the universal polarization correction derived from the Kirchhoff point-vortex system**. Its central quantities are b = π / (4·π² + 2·π·√3) ≈ 0.0785, the rotation angle θ_b = arcsin(b) ≈ 7.07°, and the stabilisation identity cos²θ_b + sin²θ_b = 1; what this port asserts (or proves) is 0 < b < 1 (both bounds), sin θ_b = b, cos²θ_b + sin²θ_b = 1, and the reference interval 0.07 < b < 0.08 against the published value 0.0785. The same assertions exist in every peer language of the matrix, each in its own idiom: [Python](../../../section1_correction_b/python/README.md) · [Lean 4](../../../lean4/ResearchPapersVerification/Section1_CorrectionB/README.md) · [Coq/Rocq](../../../coq/section1_correction_b/README.md) · [Isabelle-HOL](../../../isabelle/Section1_CorrectionB/README.md) · [Agda](../../../agda/Section1_CorrectionB/README.md) · [C++](../../../cpp/section1_correction_b/README.md) · [Rust](../../../rust/section1_correction_b/README.md). Agreement between all ports is enforced by the cross-language validator (`../../../tests/`) and the `ci-cross-language.yml` workflow.

**What you will see.** Run this port and you get: a banner identifying the section and language; the computed values printed at full precision; one `[PASS]`/`[FAIL]` line per assertion; and a final `JSON: {"section": 1, "language": "haskell", "values": {…}, "all_passed": …}` verdict line. Exit status is 0 only when every assertion passed — CI treats anything else as a failure.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`Main.hs`](Main.hs) | 266 B | Section 1 Haskell source — the complete section verifier |

## ▶️ How to Run

```bash
cd verification/haskell && cabal build && cabal run <section>
```

## 🔗 Cross-References

- [Section folder](../README.md)
- [Haskell layer](../../README.md)

## 🇷🇺 Краткое резюме (Russian Summary)

Исходник бинарника раздела 1 на Haskell (Main.hs); контракт PASS/JSON как во всех портах.

---

<div align="center">

**[⬆ Back to top](#-haskell--section-1--src--the-section-binary)** · 
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

