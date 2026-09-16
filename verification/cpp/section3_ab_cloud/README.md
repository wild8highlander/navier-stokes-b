# Ⓜ️ C++ · Section 3 — AB-Cloud

> **Navigation:** [`verification`](../../README.md) › [`cpp`](../README.md) › **`section3_ab_cloud`**

![C++](https://img.shields.io/badge/C%2B%2B-C++17-informational?style=flat-square&logo=cplusplus&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![Section](https://img.shields.io/badge/Section-3-blue?style=flat-square)

The **C++ port of Section 3** — AB-Cloud — the Non-Hermitian Hofstadter Hamiltonian. This folder is the section's slot in the C++ layer of the framework: the file below states exactly the assertions the Python reference makes, in C++ idiom — header-light C++17 with a uniform check() harness printing PASS/FAIL per assertion and a JSON verdict.

## 🔬 Section Context — Where This Port Sits

**Where it sits.** Section 3 of the framework covers **the 36³ non-Hermitian Hofstadter Hamiltonian with Aharonov–Bohm vortex fluxes**. Its central quantities are spectral construction with σ = 0.5 non-Hermiticity, α = 2.0 AB flux, disorder W = 1.0 and 5 000 embedded Riemann zeta zeros; what this port asserts (or proves) is GUE-consistency of the spectrum (⟨r⟩ gap statistics), gauge invariance of the vortex decoration, and spectral stability under perturbations. The same assertions exist in every peer language of the matrix, each in its own idiom: [Python](../../section3_ab_cloud/python/README.md) · [Lean 4](../../lean4/ResearchPapersVerification/Section3_ABCloud/README.md) · [Coq/Rocq](../../coq/section3_ab_cloud/README.md) · [Isabelle-HOL](../../isabelle/Section3_ABCloud/README.md) · [Agda](../../agda/Section3_ABCloud/README.md) · [Rust](../../rust/section3_ab_cloud/README.md) · [Haskell](../../haskell/Section3_ABCloud/README.md). Agreement between all ports is enforced by the cross-language validator (`../../tests/`) and the `ci-cross-language.yml` workflow.

**What you will see.** Run this port and you get: a banner identifying the section and language; the computed values printed at full precision; one `[PASS]`/`[FAIL]` line per assertion; and a final `JSON: {"section": 3, "language": "cpp", "values": {…}, "all_passed": …}` verdict line. Exit status is 0 only when every assertion passed — CI treats anything else as a failure.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`main.cpp`](main.cpp) | 783 B | include <cmath> include <iostream> |

## ▶️ How to Run

```bash
cmake -S verification/cpp -B build && cmake --build build && ./build/<section>  # per section
```

## 🔗 Cross-References

- [C++ layer README](../README.md)
- [Python reference for this section](../../section3_ab_cloud/python/README.md)
- [Framework root](../../README.md)

## 🇷🇺 Краткое резюме (Russian Summary)

Порт раздела 3 на C++: один файл с теоремами/проверками раздела «AB-Cloud»; контекст раздела — в одноимённом блоке; сборка и вывод — как в README слоя C++.

---

<div align="center">

**[⬆ Back to top](#-c--section-3--ab-cloud)** · 
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

