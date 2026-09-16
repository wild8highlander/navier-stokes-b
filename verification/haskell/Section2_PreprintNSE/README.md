# Ⓜ️ Haskell · Section 2 — Preprint NSE

> **Navigation:** [`verification`](../../README.md) › [`haskell`](../README.md) › **`Section2_PreprintNSE`**

![Haskell](https://img.shields.io/badge/Haskell-9.4-informational?style=flat-square&logo=haskell&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![Section](https://img.shields.io/badge/Section-2-blue?style=flat-square)

The **Haskell port of Section 2** — Preprint NSE — the Regularity Argument Chain. This folder is the section's slot in the Haskell layer of the framework: the file below states exactly the assertions the Python reference makes, in Haskell idiom — GHC implementation using `Double` arithmetic with `Text.Printf` output matching the common contract.

The folder pairs the section folder with its `src/` sibling holding `Main.hs` — the Cabal project registers each as an executable.

## 🔬 Section Context — Where This Port Sits

**Where it sits.** Section 2 of the framework covers **the analytical chain behind global regularity of the 3D Navier–Stokes equations**. Its central quantities are the stabilisation mechanism induced by θ_b ≈ 7.07° and the 3.5× reduction of the BKM blow-up criterion integral; what this port asserts (or proves) is structural lemmas of the preprint: positivity and scale of the correction, unit-norm rotation axis, and the energy-estimate scaffolding. The same assertions exist in every peer language of the matrix, each in its own idiom: [Python](../../section2_preprint/python/README.md) · [Lean 4](../../lean4/ResearchPapersVerification/Section2_PreprintNSE/README.md) · [Coq/Rocq](../../coq/section2_preprint/README.md) · [Isabelle-HOL](../../isabelle/Section2_PreprintNSE/README.md) · [Agda](../../agda/Section2_PreprintNSE/README.md) · [C++](../../cpp/section2_preprint/README.md) · [Rust](../../rust/section2_preprint/README.md). Agreement between all ports is enforced by the cross-language validator (`../../tests/`) and the `ci-cross-language.yml` workflow.

**What you will see.** Run this port and you get: a banner identifying the section and language; the computed values printed at full precision; one `[PASS]`/`[FAIL]` line per assertion; and a final `JSON: {"section": 2, "language": "haskell", "values": {…}, "all_passed": …}` verdict line. Exit status is 0 only when every assertion passed — CI treats anything else as a failure.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`Section2_PreprintNSE.cabal`](Section2_PreprintNSE.cabal) | 355 B | Cabal package definition |
| [`src/`](src/) | — | subdirectory with 2 files (see its own README) |

## 🗂 Directory Layout

```
Section2_PreprintNSE/
├── src/   # 2 files
│   ├── Main.hs
│   └── README.md  (this file)
├── README.md  (this file)
└── Section2_PreprintNSE.cabal
```

## ▶️ How to Run

```bash
cd verification/haskell && cabal build && cabal run <section>
```

## 🔗 Cross-References

- [Haskell layer README](../README.md)
- [Python reference for this section](../../section2_preprint/python/README.md)
- [Framework root](../../README.md)

## 🇷🇺 Краткое резюме (Russian Summary)

Порт раздела 2 на Haskell: один файл с теоремами/проверками раздела «Preprint NSE»; контекст раздела — в одноимённом блоке; сборка и вывод — как в README слоя Haskell.

---

<div align="center">

**[⬆ Back to top](#-haskell--section-2--preprint-nse)** · 
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

