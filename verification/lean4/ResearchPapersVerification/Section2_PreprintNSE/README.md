# Ⓜ️ Lean 4 · Section 2 — Preprint NSE

> **Navigation:** [`verification`](../../../README.md) › [`lean4`](../../README.md) › [`ResearchPapersVerification`](../README.md) › **`Section2_PreprintNSE`**

![Lean 4](https://img.shields.io/badge/Lean%204-v4.14-informational?style=flat-square&logo=leanpub&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![Section](https://img.shields.io/badge/Section-2-blue?style=flat-square)

The **Lean 4 port of Section 2** — Preprint NSE — the Regularity Argument Chain. This folder is the section's slot in the Lean 4 layer of the framework: the file below states exactly the assertions the Python reference makes, in Lean 4 idiom — machine-checked proofs on the Mathlib4 foundation with custom definitions layered on top.

## 🔬 Section Context — Where This Port Sits

**Where it sits.** Section 2 of the framework covers **the analytical chain behind global regularity of the 3D Navier–Stokes equations**. Its central quantities are the stabilisation mechanism induced by θ_b ≈ 7.07° and the 3.5× reduction of the BKM blow-up criterion integral; what this port asserts (or proves) is structural lemmas of the preprint: positivity and scale of the correction, unit-norm rotation axis, and the energy-estimate scaffolding. The same assertions exist in every peer language of the matrix, each in its own idiom: [Python](../../../section2_preprint/python/README.md) · [Coq/Rocq](../../../coq/section2_preprint/README.md) · [Isabelle-HOL](../../../isabelle/Section2_PreprintNSE/README.md) · [Agda](../../../agda/Section2_PreprintNSE/README.md) · [C++](../../../cpp/section2_preprint/README.md) · [Rust](../../../rust/section2_preprint/README.md) · [Haskell](../../../haskell/Section2_PreprintNSE/README.md). Agreement between all ports is enforced by the cross-language validator (`../../../tests/`) and the `ci-cross-language.yml` workflow.

**What you will see.** Run this port and you get: a banner identifying the section and language; the computed values printed at full precision; one `[PASS]`/`[FAIL]` line per assertion; and a final `JSON: {"section": 2, "language": "lean4", "values": {…}, "all_passed": …}` verdict line. Exit status is 0 only when every assertion passed — CI treats anything else as a failure.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`ProofChain.lean`](ProofChain.lean) | 1.0 KB | Lean 4 module |

## ▶️ How to Run

```bash
cd verification/lean4 && lake build && lake exe check   # whole library
```

## 🔗 Cross-References

- [Lean 4 layer README](../README.md)
- [Python reference for this section](../../../section2_preprint/python/README.md)
- [Framework root](../../../README.md)

## 🇷🇺 Краткое резюме (Russian Summary)

Порт раздела 2 на Lean 4: один файл с теоремами/проверками раздела «Preprint NSE»; контекст раздела — в одноимённом блоке; сборка и вывод — как в README слоя Lean 4.

---

<div align="center">

**[⬆ Back to top](#-lean-4--section-2--preprint-nse)** · 
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

