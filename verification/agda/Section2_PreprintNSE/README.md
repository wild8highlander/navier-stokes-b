# Ⓜ️ Agda · Section 2 — Preprint NSE

> **Navigation:** [`verification`](../../README.md) › [`agda`](../README.md) › **`Section2_PreprintNSE`**

![Agda](https://img.shields.io/badge/Agda-2.6-informational?style=flat-square&logo=agda&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![Section](https://img.shields.io/badge/Section-2-blue?style=flat-square)

The **Agda port of Section 2** — Preprint NSE — the Regularity Argument Chain. This folder is the section's slot in the Agda layer of the framework: the file below states exactly the assertions the Python reference makes, in Agda idiom — dependently-typed constructive development; π and √3 are explicit postulates, keeping the trust base minimal and visible.

## 🔬 Section Context — Where This Port Sits

**Where it sits.** Section 2 of the framework covers **the analytical chain behind global regularity of the 3D Navier–Stokes equations**. Its central quantities are the stabilisation mechanism induced by θ_b ≈ 7.07° and the 3.5× reduction of the BKM blow-up criterion integral; what this port asserts (or proves) is structural lemmas of the preprint: positivity and scale of the correction, unit-norm rotation axis, and the energy-estimate scaffolding. The same assertions exist in every peer language of the matrix, each in its own idiom: [Python](../../section2_preprint/python/README.md) · [Lean 4](../../lean4/ResearchPapersVerification/Section2_PreprintNSE/README.md) · [Coq/Rocq](../../coq/section2_preprint/README.md) · [Isabelle-HOL](../../isabelle/Section2_PreprintNSE/README.md) · [C++](../../cpp/section2_preprint/README.md) · [Rust](../../rust/section2_preprint/README.md) · [Haskell](../../haskell/Section2_PreprintNSE/README.md). Agreement between all ports is enforced by the cross-language validator (`../../tests/`) and the `ci-cross-language.yml` workflow.

**What you will see.** Run this port and you get: a banner identifying the section and language; the computed values printed at full precision; one `[PASS]`/`[FAIL]` line per assertion; and a final `JSON: {"section": 2, "language": "agda", "values": {…}, "all_passed": …}` verdict line. Exit status is 0 only when every assertion passed — CI treats anything else as a failure.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`ProofChain.agda`](ProofChain.agda) | 151 B | Section 2 Agda module — Preprint NSE — the Regularity Argument Chain (--safe, explicit postulates) |

## ▶️ How to Run

```bash
cd verification/agda && agda --safe <Module>.agda   # per module
```

## 🔗 Cross-References

- [Agda layer README](../README.md)
- [Python reference for this section](../../section2_preprint/python/README.md)
- [Framework root](../../README.md)

## 🇷🇺 Краткое резюме (Russian Summary)

Порт раздела 2 на Agda: один файл с теоремами/проверками раздела «Preprint NSE»; контекст раздела — в одноимённом блоке; сборка и вывод — как в README слоя Agda.

---

<div align="center">

**[⬆ Back to top](#-agda--section-2--preprint-nse)** · 
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

