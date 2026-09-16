# Ⓜ️ Agda · Section 1 — Correction b

> **Navigation:** [`verification`](../../README.md) › [`agda`](../README.md) › **`Section1_CorrectionB`**

![Agda](https://img.shields.io/badge/Agda-2.6-informational?style=flat-square&logo=agda&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![Section](https://img.shields.io/badge/Section-1-blue?style=flat-square)

The **Agda port of Section 1** — Correction b — the Universal Polarization Constant. This folder is the section's slot in the Agda layer of the framework: the file below states exactly the assertions the Python reference makes, in Agda idiom — dependently-typed constructive development; π and √3 are explicit postulates, keeping the trust base minimal and visible.

## 🔬 Section Context — Where This Port Sits

**Where it sits.** Section 1 of the framework covers **the universal polarization correction derived from the Kirchhoff point-vortex system**. Its central quantities are b = π / (4·π² + 2·π·√3) ≈ 0.0785, the rotation angle θ_b = arcsin(b) ≈ 7.07°, and the stabilisation identity cos²θ_b + sin²θ_b = 1; what this port asserts (or proves) is 0 < b < 1 (both bounds), sin θ_b = b, cos²θ_b + sin²θ_b = 1, and the reference interval 0.07 < b < 0.08 against the published value 0.0785. The same assertions exist in every peer language of the matrix, each in its own idiom: [Python](../../section1_correction_b/python/README.md) · [Lean 4](../../lean4/ResearchPapersVerification/Section1_CorrectionB/README.md) · [Coq/Rocq](../../coq/section1_correction_b/README.md) · [Isabelle-HOL](../../isabelle/Section1_CorrectionB/README.md) · [C++](../../cpp/section1_correction_b/README.md) · [Rust](../../rust/section1_correction_b/README.md) · [Haskell](../../haskell/Section1_CorrectionB/README.md). Agreement between all ports is enforced by the cross-language validator (`../../tests/`) and the `ci-cross-language.yml` workflow.

**What you will see.** Run this port and you get: a banner identifying the section and language; the computed values printed at full precision; one `[PASS]`/`[FAIL]` line per assertion; and a final `JSON: {"section": 1, "language": "agda", "values": {…}, "all_passed": …}` verdict line. Exit status is 0 only when every assertion passed — CI treats anything else as a failure.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`CorrectionB.agda`](CorrectionB.agda) | 323 B | Section 1 Agda module — Correction b — the Universal Polarization Constant (--safe, explicit postulates) |

## ▶️ How to Run

```bash
cd verification/agda && agda --safe <Module>.agda   # per module
```

## 🔗 Cross-References

- [Agda layer README](../README.md)
- [Python reference for this section](../../section1_correction_b/python/README.md)
- [Framework root](../../README.md)

## 🇷🇺 Краткое резюме (Russian Summary)

Порт раздела 1 на Agda: один файл с теоремами/проверками раздела «Correction b»; контекст раздела — в одноимённом блоке; сборка и вывод — как в README слоя Agda.

---

<div align="center">

**[⬆ Back to top](#-agda--section-1--correction-b)** · 
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

