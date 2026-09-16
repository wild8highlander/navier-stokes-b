# Ⓜ️ Isabelle-HOL · Section 6 — Riemann Zeros

> **Navigation:** [`verification`](../../README.md) › [`isabelle`](../README.md) › **`Section6_RiemannZeros`**

![Isabelle-HOL](https://img.shields.io/badge/Isabelle-HOL-2024-informational?style=flat-square&logo=isamars&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![Section](https://img.shields.io/badge/Section-6-blue?style=flat-square)

The **Isabelle-HOL port of Section 6** — Riemann Zeros — the Hilbert–Pólya Programme. This folder is the section's slot in the Isabelle-HOL layer of the framework: the file below states exactly the assertions the Python reference makes, in Isabelle-HOL idiom — proofs stated over `Complex_Main`; each section is a standalone theory.

## 🔬 Section Context — Where This Port Sits

**Where it sits.** Section 6 of the framework covers **the spectral correspondence between the AB-Cloud and the non-trivial zeros of the Riemann zeta function**. Its central quantities are the Hilbert–Pólya realisation, the Montgomery–Dyson GUE correspondence and the statistical identity of the two spectra; what this port asserts (or proves) is spectral-correspondence identities and the statistical machinery (⟨r⟩, KS, permutation tests) in constructive and classical form. The same assertions exist in every peer language of the matrix, each in its own idiom: [Python](../../section6_riemann_zeros/python/README.md) · [Lean 4](../../lean4/ResearchPapersVerification/Section6_RiemannZeros/README.md) · [Coq/Rocq](../../coq/section6_riemann_zeros/README.md) · [Agda](../../agda/Section6_RiemannZeros/README.md) · [C++](../../cpp/section6_riemann_zeros/README.md) · [Rust](../../rust/section6_riemann_zeros/README.md) · [Haskell](../../haskell/Section6_RiemannZeros/README.md). Agreement between all ports is enforced by the cross-language validator (`../../tests/`) and the `ci-cross-language.yml` workflow.

**What you will see.** Run this port and you get: a banner identifying the section and language; the computed values printed at full precision; one `[PASS]`/`[FAIL]` line per assertion; and a final `JSON: {"section": 6, "language": "isabelle", "values": {…}, "all_passed": …}` verdict line. Exit status is 0 only when every assertion passed — CI treats anything else as a failure.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`RiemannZeros.thy`](RiemannZeros.thy) | 525 B | Section 6 Isabelle theory — Riemann Zeros — the Hilbert–Pólya Programme (Complex_Main, Isar proofs) |

## ▶️ How to Run

```bash
cd verification/isabelle && isabelle build -D .      # whole session
```

## 🔗 Cross-References

- [Isabelle-HOL layer README](../README.md)
- [Python reference for this section](../../section6_riemann_zeros/python/README.md)
- [Framework root](../../README.md)

## 🇷🇺 Краткое резюме (Russian Summary)

Порт раздела 6 на Isabelle-HOL: один файл с теоремами/проверками раздела «Riemann Zeros»; контекст раздела — в одноимённом блоке; сборка и вывод — как в README слоя Isabelle-HOL.

---

<div align="center">

**[⬆ Back to top](#-isabelle-hol--section-6--riemann-zeros)** · 
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

