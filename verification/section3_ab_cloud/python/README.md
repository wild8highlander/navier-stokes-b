# 🐍 Section 3 · python — the Reference Port

> **Navigation:** [`verification`](../../README.md) › [`section3_ab_cloud`](../README.md) › **`python`**

![Python](https://img.shields.io/badge/Python-3.10–3.12-informational?style=flat-square&logo=python&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **pure-Python port** of Section 3 — AB-Cloud — the Non-Hermitian Hofstadter Hamiltonian. A single ~25-line `verify.py` using only the standard `math` module: it computes spectral construction with σ = 0.5 non-Hermiticity, α = 2.0 AB flux, disorder W = 1.0 and 5 000 embedded Riemann zeta zeros, asserts GUE-consistency of the spectrum (⟨r⟩ gap statistics), gauge invariance of the vortex decoration, and spectral stability under perturbations, and prints the framework's JSON verdict. This is the port CI runs first (job `ci-python.yml`) and the one new toolchain ports are compared against.

## 🔬 Section Context — Where This Port Sits

**Where it sits.** Section 3 of the framework covers **the 36³ non-Hermitian Hofstadter Hamiltonian with Aharonov–Bohm vortex fluxes**. Its central quantities are spectral construction with σ = 0.5 non-Hermiticity, α = 2.0 AB flux, disorder W = 1.0 and 5 000 embedded Riemann zeta zeros; what this port asserts (or proves) is GUE-consistency of the spectrum (⟨r⟩ gap statistics), gauge invariance of the vortex decoration, and spectral stability under perturbations. The same assertions exist in every peer language of the matrix, each in its own idiom: [Lean 4](../../lean4/ResearchPapersVerification/Section3_ABCloud/README.md) · [Coq/Rocq](../../coq/section3_ab_cloud/README.md) · [Isabelle-HOL](../../isabelle/Section3_ABCloud/README.md) · [Agda](../../agda/Section3_ABCloud/README.md) · [C++](../../cpp/section3_ab_cloud/README.md) · [Rust](../../rust/section3_ab_cloud/README.md) · [Haskell](../../haskell/Section3_ABCloud/README.md). Agreement between all ports is enforced by the cross-language validator (`../../tests/`) and the `ci-cross-language.yml` workflow.

**What you will see.** Run this port and you get: a banner identifying the section and language; the computed values printed at full precision; one `[PASS]`/`[FAIL]` line per assertion; and a final `JSON: {"section": 3, "language": "python", "values": {…}, "all_passed": …}` verdict line. Exit status is 0 only when every assertion passed — CI treats anything else as a failure.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`verify.py`](verify.py) | 319 B | Section 3 reference verifier — prints values, asserts, JSON verdict (~25 lines) |

## ▶️ How to Run

```bash
python3 verify.py          # from this folder
# or from the repo root:
python3 verification/section3_ab_cloud/python/verify.py
```

## 🔗 Cross-References

- [Section parent](../README.md)
- [Framework root](../../README.md)

## 🇷🇺 Краткое резюме (Russian Summary)

Питон-порт раздела 3: один файл, чистый stdlib, PASS/JSON за долю секунды; результат — spectral construction with σ = 0.5 non-Hermiticity, α = 2.0 AB flux, disorder W = 1.0 and 5 000 embedded Riemann zeta zeros.

---

<div align="center">

**[⬆ Back to top](#-section-3--python--the-reference-port)** · 
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

