# 🐍 Section 5 · python — the Reference Port

> **Navigation:** [`verification`](../../README.md) › [`section5_klein_attractor`](../README.md) › **`python`**

![Python](https://img.shields.io/badge/Python-3.10–3.12-informational?style=flat-square&logo=python&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **pure-Python port** of Section 5 — Klein Attractor — Ergodic Dynamics and the NSE Bridge. A single ~25-line `verify.py` using only the standard `math` module: it computes the attractor's invariant-measure behaviour and the bridge connecting its dynamics back to the Navier–Stokes setting, asserts ergodicity scaffolding, invariant-measure identities and the structural lemmas of the Klein–NS bridge, and prints the framework's JSON verdict. This is the port CI runs first (job `ci-python.yml`) and the one new toolchain ports are compared against.

## 🔬 Section Context — Where This Port Sits

**Where it sits.** Section 5 of the framework covers **the Klein attractor dynamical system with ergodic-theoretic structure**. Its central quantities are the attractor's invariant-measure behaviour and the bridge connecting its dynamics back to the Navier–Stokes setting; what this port asserts (or proves) is ergodicity scaffolding, invariant-measure identities and the structural lemmas of the Klein–NS bridge. The same assertions exist in every peer language of the matrix, each in its own idiom: [Lean 4](../../lean4/ResearchPapersVerification/Section5_KleinAttractor/README.md) · [Coq/Rocq](../../coq/section5_klein_attractor/README.md) · [Isabelle-HOL](../../isabelle/Section5_KleinAttractor/README.md) · [Agda](../../agda/Section5_KleinAttractor/README.md) · [C++](../../cpp/section5_klein_attractor/README.md) · [Rust](../../rust/section5_klein_attractor/README.md) · [Haskell](../../haskell/Section5_KleinAttractor/README.md). Agreement between all ports is enforced by the cross-language validator (`../../tests/`) and the `ci-cross-language.yml` workflow.

**What you will see.** Run this port and you get: a banner identifying the section and language; the computed values printed at full precision; one `[PASS]`/`[FAIL]` line per assertion; and a final `JSON: {"section": 5, "language": "python", "values": {…}, "all_passed": …}` verdict line. Exit status is 0 only when every assertion passed — CI treats anything else as a failure.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`verify.py`](verify.py) | 319 B | Section 5 reference verifier — prints values, asserts, JSON verdict (~25 lines) |

## ▶️ How to Run

```bash
python3 verify.py          # from this folder
# or from the repo root:
python3 verification/section5_klein_attractor/python/verify.py
```

## 🔗 Cross-References

- [Section parent](../README.md)
- [Framework root](../../README.md)

## 🇷🇺 Краткое резюме (Russian Summary)

Питон-порт раздела 5: один файл, чистый stdlib, PASS/JSON за долю секунды; результат — the attractor's invariant-measure behaviour and the bridge connecting its dynamics back to the Navier–Stokes setting.

---

<div align="center">

**[⬆ Back to top](#-section-5--python--the-reference-port)** · 
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

