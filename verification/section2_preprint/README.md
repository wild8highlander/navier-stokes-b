# 🐍 Section 2 — Preprint NSE — the Regularity Argument Chain (Python Reference)

> **Navigation:** [`verification`](../README.md) › **`section2_preprint`**

![Python](https://img.shields.io/badge/Python-3.10–3.12-informational?style=flat-square&logo=python&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![Section](https://img.shields.io/badge/Section-2-blue?style=flat-square)

This directory is the **Python reference implementation** of research Section 2 — the second section of the framework, covering the analytical chain behind global regularity of the 3D Navier–Stokes equations. Within the framework's layout it is the *numerical reference tier*: the simplest, dependency-free port that every other language port can be diffed against.

The implementation is intentionally minimal — pure standard library (`math` only), a single `verify.py` entry point, and the framework's uniform output contract: the computed quantities are printed, each expected property is asserted with a `[PASS]` line, and the run ends with the `JSON:` verdict. For Section 2 the quantities are the stabilisation mechanism induced by θ_b ≈ 7.07° and the 3.5× reduction of the BKM blow-up criterion integral; the assertions exercise structural lemmas of the preprint: positivity and scale of the correction, unit-norm rotation axis, and the energy-estimate scaffolding.

Run it with `python3 python/verify.py` — total runtime is well under a second. The same section exists in the formal tier ([`lean4`](../lean4/README.md), [`coq`](../coq/README.md), [`isabelle`](../isabelle/README.md), [`agda`](../agda/README.md)) and in the extended computational ports ([`cpp`](../cpp/README.md), [`rust`](../rust/README.md), [`haskell`](../haskell/README.md)); CI runs them all in [`ci-cross-language.yml`](../../.github/workflows/README.md).

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`python/`](python/) | — | the Python reference port — single verify.py entry point |

## 🗂 Directory Layout

```
section2_preprint/
├── python/   # 2 files
│   ├── README.md  (this file)
│   └── verify.py
└── README.md  (this file)
```

## ▶️ How to Run

```bash
python3 python/verify.py
```

## 🔗 Cross-References

- [Framework root](../README.md)
- [Root README — verification matrix](../README.md)

## 🇷🇺 Краткое резюме (Russian Summary)

**verification/section2_preprint/** — Python-референс раздела 2 (Preprint NSE — the Regularity Argument Chain): чистый stdlib, один verify.py, вывод PASS/JSON; результат — the stabilisation mechanism induced by θ_b ≈ 7.07° and the 3.5× reduction of the BKM blow-up criterion integral.

---

<div align="center">

**[⬆ Back to top](#-section-2--preprint-nse--the-regularity-argument-chain-python-reference)** · 
**[Repository root](../README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>

---
## 🔬 Deep Dive — Section 2

**What is verified here.** the NSE regularity chain of the preprint: twist unitarity, the BKM bound under the twist, and the ordering of the estimates that leads to regularity. The Python port constructs the Rodrigues rotation for θ_b, verifies its unitarity numerically, and asserts the 3.5× BKM reduction; the formal tier compiles the chain as ordered lemmas so each step's dependencies are explicit.

**Reference command.**

```bash
`python3 verification/section2_preprint/python/verify.py`
```

**Formal counterparts.** The structural statements live in the four proof assistants: `../../lean4/ResearchPapersVerification/Section2_PreprintNSE/` · `../../coq/section2_preprint/` · `../../isabelle/Section2_PreprintNSE/` · `../../agda/Section2_PreprintNSE/` — with lemma names mirroring the computational assertions (see the root README's [formal deep dive](../../README.md#-appendix-w--formal-verification-deep-dive) for the Lean anatomy).

**Where it appears in the papers.** Each section maps onto a specific document layer: the preprint for the chain-type claims, the flagship paper for the constant's consequences, the KdV chapter for the integrable-systems results, the Klein-attractor reports for the dynamical-systems content, and the AB-Cloud monographs for the spectral programme. The mapping table is in the root README's [Section-by-Section Guide](../../README.md#-section-by-section-verification-guide).

**Contract reminder.** The port prints a banner, per-assertion `[PASS]/[FAIL]` lines, and the JSON verdict; exit code 0 only on full success. The cross-language validator consumes that JSON mechanically — any disagreement across languages fails CI.

---
The chain here is ordered by design: each assertion depends only on earlier ones, so a failure names the first broken link — not a symptom somewhere downstream. The 3.5× reduction check is the section's empirical headline; treat it as the canary for any change to the rotation construction.

---
## 🔗 Cross-Links

Formal: [lean4](../lean4/README.md) · [coq](../coq/README.md) · [isabelle](../isabelle/README.md) · [agda](../agda/README.md) · Papers: [preprint](../../papers/preprint/README.md) · [correction-b](../../papers/correction-b/README.md) · Related section: [Section 5 (bridge)](../section5_klein_attractor/README.md).

<!-- doc-enhancer:block v1 (автоматический блок; файлы лицензии не затрагиваются) -->

---

## 🧭 Навигация и быстрые ссылки (auto)

- 🏠 [Корень репозитория](../../../README.md)
- 📖 [Как верифицируются утверждения](../../../verification/README.md)
- 📄 [Статьи (PDF)](../../../papers/README.md) · 📚 [Монографии](../../../docs/README.md) · 🧾 [LaTeX](../../../src/README.md)
- ⚖️ [Лицензия IPL-RP-1.0](../../../LICENSE.md) — просмотр, одна резервная копия и цитирование с атрибуцией разрешены; остальное — только с письменного согласия автора.

*Блок добавлен автоматически (`doc-enhancer v1`); к лицензии отношения не имеет и её не изменяет. Повторный запуск скрипта блок не дублирует.*

