# Ⓜ️ Haskell · Section 1 — Correction b

> **Navigation:** [`verification`](../../README.md) › [`haskell`](../README.md) › **`Section1_CorrectionB`**

![Haskell](https://img.shields.io/badge/Haskell-9.4-informational?style=flat-square&logo=haskell&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![Section](https://img.shields.io/badge/Section-1-blue?style=flat-square)

The **Haskell port of Section 1** — Correction b — the Universal Polarization Constant. This folder is the section's slot in the Haskell layer of the framework: the file below states exactly the assertions the Python reference makes, in Haskell idiom — GHC implementation using `Double` arithmetic with `Text.Printf` output matching the common contract.

The folder pairs the section folder with its `src/` sibling holding `Main.hs` — the Cabal project registers each as an executable.

## 🔬 Section Context — Where This Port Sits

**Where it sits.** Section 1 of the framework covers **the universal polarization correction derived from the Kirchhoff point-vortex system**. Its central quantities are b = π / (4·π² + 2·π·√3) ≈ 0.0785, the rotation angle θ_b = arcsin(b) ≈ 7.07°, and the stabilisation identity cos²θ_b + sin²θ_b = 1; what this port asserts (or proves) is 0 < b < 1 (both bounds), sin θ_b = b, cos²θ_b + sin²θ_b = 1, and the reference interval 0.07 < b < 0.08 against the published value 0.0785. The same assertions exist in every peer language of the matrix, each in its own idiom: [Python](../../section1_correction_b/python/README.md) · [Lean 4](../../lean4/ResearchPapersVerification/Section1_CorrectionB/README.md) · [Coq/Rocq](../../coq/section1_correction_b/README.md) · [Isabelle-HOL](../../isabelle/Section1_CorrectionB/README.md) · [Agda](../../agda/Section1_CorrectionB/README.md) · [C++](../../cpp/section1_correction_b/README.md) · [Rust](../../rust/section1_correction_b/README.md). Agreement between all ports is enforced by the cross-language validator (`../../tests/`) and the `ci-cross-language.yml` workflow.

**What you will see.** Run this port and you get: a banner identifying the section and language; the computed values printed at full precision; one `[PASS]`/`[FAIL]` line per assertion; and a final `JSON: {"section": 1, "language": "haskell", "values": {…}, "all_passed": …}` verdict line. Exit status is 0 only when every assertion passed — CI treats anything else as a failure.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`Section1_CorrectionB.cabal`](Section1_CorrectionB.cabal) | 355 B | Cabal package definition |
| [`src/`](src/) | — | subdirectory with 2 files (see its own README) |

## 🗂 Directory Layout

```
Section1_CorrectionB/
├── src/   # 2 files
│   ├── Main.hs
│   └── README.md  (this file)
├── README.md  (this file)
└── Section1_CorrectionB.cabal
```

## ▶️ How to Run

```bash
cd verification/haskell && cabal build && cabal run <section>
```

## 🔗 Cross-References

- [Haskell layer README](../README.md)
- [Python reference for this section](../../section1_correction_b/python/README.md)
- [Framework root](../../README.md)

## 🇷🇺 Краткое резюме (Russian Summary)

Порт раздела 1 на Haskell: один файл с теоремами/проверками раздела «Correction b»; контекст раздела — в одноимённом блоке; сборка и вывод — как в README слоя Haskell.

---

<div align="center">

**[⬆ Back to top](#-haskell--section-1--correction-b)** · 
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

