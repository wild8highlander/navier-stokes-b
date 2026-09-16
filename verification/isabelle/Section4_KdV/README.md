# Ⓜ️ Isabelle-HOL · Section 4 — KdV

> **Navigation:** [`verification`](../../README.md) › [`isabelle`](../README.md) › **`Section4_KdV`**

![Isabelle-HOL](https://img.shields.io/badge/Isabelle-HOL-2024-informational?style=flat-square&logo=isamars&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![Section](https://img.shields.io/badge/Section-4-blue?style=flat-square)

The **Isabelle-HOL port of Section 4** — KdV — Soliton Interactions under the b-Correction. This folder is the section's slot in the Isabelle-HOL layer of the framework: the file below states exactly the assertions the Python reference makes, in Isabelle-HOL idiom — proofs stated over `Complex_Main`; each section is a standalone theory.

## 🔬 Section Context — Where This Port Sits

**Where it sits.** Section 4 of the framework covers **the Korteweg–de Vries equation and its soliton interactions**. Its central quantities are pseudospectral treatment of the KdV hierarchy and the manifestation of the polarization correction in soliton collision dynamics; what this port asserts (or proves) is conservation-law identities of the integrable KdV hierarchy and the numeric stability of the pseudospectral scheme. The same assertions exist in every peer language of the matrix, each in its own idiom: [Python](../../section4_kdv/python/README.md) · [Lean 4](../../lean4/ResearchPapersVerification/Section4_KdV/README.md) · [Coq/Rocq](../../coq/section4_kdv/README.md) · [Agda](../../agda/Section4_KdV/README.md) · [C++](../../cpp/section4_kdv/README.md) · [Rust](../../rust/section4_kdv/README.md) · [Haskell](../../haskell/Section4_KdV/README.md). Agreement between all ports is enforced by the cross-language validator (`../../tests/`) and the `ci-cross-language.yml` workflow.

**What you will see.** Run this port and you get: a banner identifying the section and language; the computed values printed at full precision; one `[PASS]`/`[FAIL]` line per assertion; and a final `JSON: {"section": 4, "language": "isabelle", "values": {…}, "all_passed": …}` verdict line. Exit status is 0 only when every assertion passed — CI treats anything else as a failure.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`KdV.thy`](KdV.thy) | 442 B | Section 4 Isabelle theory — KdV — Soliton Interactions under the b-Correction (Complex_Main, Isar proofs) |

## ▶️ How to Run

```bash
cd verification/isabelle && isabelle build -D .      # whole session
```

## 🔗 Cross-References

- [Isabelle-HOL layer README](../README.md)
- [Python reference for this section](../../section4_kdv/python/README.md)
- [Framework root](../../README.md)

## 🇷🇺 Краткое резюме (Russian Summary)

Порт раздела 4 на Isabelle-HOL: один файл с теоремами/проверками раздела «KdV»; контекст раздела — в одноимённом блоке; сборка и вывод — как в README слоя Isabelle-HOL.

---

<div align="center">

**[⬆ Back to top](#-isabelle-hol--section-4--kdv)** · 
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

