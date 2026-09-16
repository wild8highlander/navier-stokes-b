# Ⓜ️ Isabelle-HOL · Section 5 — Klein Attractor

> **Navigation:** [`verification`](../../README.md) › [`isabelle`](../README.md) › **`Section5_KleinAttractor`**

![Isabelle-HOL](https://img.shields.io/badge/Isabelle-HOL-2024-informational?style=flat-square&logo=isamars&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![Section](https://img.shields.io/badge/Section-5-blue?style=flat-square)

The **Isabelle-HOL port of Section 5** — Klein Attractor — Ergodic Dynamics and the NSE Bridge. This folder is the section's slot in the Isabelle-HOL layer of the framework: the file below states exactly the assertions the Python reference makes, in Isabelle-HOL idiom — proofs stated over `Complex_Main`; each section is a standalone theory.

## 🔬 Section Context — Where This Port Sits

**Where it sits.** Section 5 of the framework covers **the Klein attractor dynamical system with ergodic-theoretic structure**. Its central quantities are the attractor's invariant-measure behaviour and the bridge connecting its dynamics back to the Navier–Stokes setting; what this port asserts (or proves) is ergodicity scaffolding, invariant-measure identities and the structural lemmas of the Klein–NS bridge. The same assertions exist in every peer language of the matrix, each in its own idiom: [Python](../../section5_klein_attractor/python/README.md) · [Lean 4](../../lean4/ResearchPapersVerification/Section5_KleinAttractor/README.md) · [Coq/Rocq](../../coq/section5_klein_attractor/README.md) · [Agda](../../agda/Section5_KleinAttractor/README.md) · [C++](../../cpp/section5_klein_attractor/README.md) · [Rust](../../rust/section5_klein_attractor/README.md) · [Haskell](../../haskell/Section5_KleinAttractor/README.md). Agreement between all ports is enforced by the cross-language validator (`../../tests/`) and the `ci-cross-language.yml` workflow.

**What you will see.** Run this port and you get: a banner identifying the section and language; the computed values printed at full precision; one `[PASS]`/`[FAIL]` line per assertion; and a final `JSON: {"section": 5, "language": "isabelle", "values": {…}, "all_passed": …}` verdict line. Exit status is 0 only when every assertion passed — CI treats anything else as a failure.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`Klein.thy`](Klein.thy) | 457 B | Isabelle theory |

## ▶️ How to Run

```bash
cd verification/isabelle && isabelle build -D .      # whole session
```

## 🔗 Cross-References

- [Isabelle-HOL layer README](../README.md)
- [Python reference for this section](../../section5_klein_attractor/python/README.md)
- [Framework root](../../README.md)

## 🇷🇺 Краткое резюме (Russian Summary)

Порт раздела 5 на Isabelle-HOL: один файл с теоремами/проверками раздела «Klein Attractor»; контекст раздела — в одноимённом блоке; сборка и вывод — как в README слоя Isabelle-HOL.

---

<div align="center">

**[⬆ Back to top](#-isabelle-hol--section-5--klein-attractor)** · 
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

