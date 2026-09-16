# Ⓜ️ Lean 4 · Section 6 — Riemann Zeros

> **Navigation:** [`verification`](../../../README.md) › [`lean4`](../../README.md) › [`ResearchPapersVerification`](../README.md) › **`Section6_RiemannZeros`**

![Lean 4](https://img.shields.io/badge/Lean%204-v4.14-informational?style=flat-square&logo=leanpub&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![Section](https://img.shields.io/badge/Section-6-blue?style=flat-square)

The **Lean 4 port of Section 6** — Riemann Zeros — the Hilbert–Pólya Programme. This folder is the section's slot in the Lean 4 layer of the framework: the file below states exactly the assertions the Python reference makes, in Lean 4 idiom — machine-checked proofs on the Mathlib4 foundation with custom definitions layered on top.

## 🔬 Section Context — Where This Port Sits

**Where it sits.** Section 6 of the framework covers **the spectral correspondence between the AB-Cloud and the non-trivial zeros of the Riemann zeta function**. Its central quantities are the Hilbert–Pólya realisation, the Montgomery–Dyson GUE correspondence and the statistical identity of the two spectra; what this port asserts (or proves) is spectral-correspondence identities and the statistical machinery (⟨r⟩, KS, permutation tests) in constructive and classical form. The same assertions exist in every peer language of the matrix, each in its own idiom: [Python](../../../section6_riemann_zeros/python/README.md) · [Coq/Rocq](../../../coq/section6_riemann_zeros/README.md) · [Isabelle-HOL](../../../isabelle/Section6_RiemannZeros/README.md) · [Agda](../../../agda/Section6_RiemannZeros/README.md) · [C++](../../../cpp/section6_riemann_zeros/README.md) · [Rust](../../../rust/section6_riemann_zeros/README.md) · [Haskell](../../../haskell/Section6_RiemannZeros/README.md). Agreement between all ports is enforced by the cross-language validator (`../../../tests/`) and the `ci-cross-language.yml` workflow.

**What you will see.** Run this port and you get: a banner identifying the section and language; the computed values printed at full precision; one `[PASS]`/`[FAIL]` line per assertion; and a final `JSON: {"section": 6, "language": "lean4", "values": {…}, "all_passed": …}` verdict line. Exit status is 0 only when every assertion passed — CI treats anything else as a failure.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`HilbertPolya.lean`](HilbertPolya.lean) | 624 B | Lean 4 module |

## ▶️ How to Run

```bash
cd verification/lean4 && lake build && lake exe check   # whole library
```

## 🔗 Cross-References

- [Lean 4 layer README](../README.md)
- [Python reference for this section](../../../section6_riemann_zeros/python/README.md)
- [Framework root](../../../README.md)

## 🇷🇺 Краткое резюме (Russian Summary)

Порт раздела 6 на Lean 4: один файл с теоремами/проверками раздела «Riemann Zeros»; контекст раздела — в одноимённом блоке; сборка и вывод — как в README слоя Lean 4.

---

<div align="center">

**[⬆ Back to top](#-lean-4--section-6--riemann-zeros)** · 
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

