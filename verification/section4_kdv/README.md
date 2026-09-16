# 🐍 Section 4 — KdV — Soliton Interactions under the b-Correction (Python Reference)

> **Navigation:** [`verification`](../README.md) › **`section4_kdv`**

![Python](https://img.shields.io/badge/Python-3.10–3.12-informational?style=flat-square&logo=python&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![Section](https://img.shields.io/badge/Section-4-blue?style=flat-square)

This directory is the **Python reference implementation** of research Section 4 — the fourth section of the framework, covering the Korteweg–de Vries equation and its soliton interactions. Within the framework's layout it is the *numerical reference tier*: the simplest, dependency-free port that every other language port can be diffed against.

The implementation is intentionally minimal — pure standard library (`math` only), a single `verify.py` entry point, and the framework's uniform output contract: the computed quantities are printed, each expected property is asserted with a `[PASS]` line, and the run ends with the `JSON:` verdict. For Section 4 the quantities are pseudospectral treatment of the KdV hierarchy and the manifestation of the polarization correction in soliton collision dynamics; the assertions exercise conservation-law identities of the integrable KdV hierarchy and the numeric stability of the pseudospectral scheme.

Run it with `python3 python/verify.py` — total runtime is well under a second. The same section exists in the formal tier ([`lean4`](../lean4/README.md), [`coq`](../coq/README.md), [`isabelle`](../isabelle/README.md), [`agda`](../agda/README.md)) and in the extended computational ports ([`cpp`](../cpp/README.md), [`rust`](../rust/README.md), [`haskell`](../haskell/README.md)); CI runs them all in [`ci-cross-language.yml`](../../.github/workflows/README.md).

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`python/`](python/) | — | the Python reference port — single verify.py entry point |

## 🗂 Directory Layout

```
section4_kdv/
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

## 🇷🇺 Brief Summary (Russian Summary)

**verification/section4_kdv/** — the Python reference of Section 4 (KdV — Soliton Interactions under the b-Correction): pure stdlib, a single verify.py, PASS/JSON output; result — pseudospectral treatment of the KdV hierarchy and the manifestation of the polarization correction in soliton collision dynamics.

---

<div align="center">

**[⬆ Back to top](#-section-4--kdv--soliton-interactions-under-the-b-correction-python-reference)** · 
**[Repository root](../README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>

---
## 🔬 Deep Dive — Section 4

**What is verified here.** KdV soliton interactions under the b-correction: the pseudospectral machinery, conservation of mass/momentum/energy across interactions, and the closed-form two-soliton agreement. The C++ port is the computational workhorse; the formal tier treats the integrability identities.

**Reference command.**

```bash
`python3 verification/section4_kdv/python/verify.py`
```

**Formal counterparts.** The structural statements live in the four proof assistants: `../../lean4/ResearchPapersVerification/Section4_KdV/` · `../../coq/section4_kdv/` · `../../isabelle/Section4_KdV/` · `../../agda/Section4_KdV/` — with lemma names mirroring the computational assertions (see the root README's [formal deep dive](../../README.md#-appendix-w--formal-verification-deep-dive) for the Lean anatomy).

**Where it appears in the papers.** Each section maps onto a specific document layer: the preprint for the chain-type claims, the flagship paper for the constant's consequences, the KdV chapter for the integrable-systems results, the Klein-attractor reports for the dynamical-systems content, and the AB-Cloud monographs for the spectral programme. The mapping table is in the root README's [Section-by-Section Guide](../../README.md#-section-by-section-verification-guide).

**Contract reminder.** The port prints a banner, per-assertion `[PASS]/[FAIL]` lines, and the JSON verdict; exit code 0 only on full success. The cross-language validator consumes that JSON mechanically — any disagreement across languages fails CI.

---
Conservation is the contract here: mass, momentum, energy across the interaction, plus the closed-form two-soliton agreement. The C++ port's FFT machinery is the performance-critical piece; the Python port is the definitional check. A drift in conserved quantities is always a discretisation or a correction-parameter bug — both fail here first.

---
## 🔗 Cross-Links

Workhorse: [cpp Section4](../cpp/README.md) · Formal: [lean4](../lean4/README.md) · [coq](../coq/README.md) · Papers: [kdv chapter](../../papers/kdv/README.md) · Word edition: [docs/kdv](../../docs/kdv/README.md).

<!-- doc-enhancer:block v1 (automatic block; license files are not affected) -->

---

## 🧭 Navigation and Quick Links (auto)

- 🏠 [Repository root](../../../README.md)
- 📖 [How the claims are verified](../../../verification/README.md)
- 📄 [Papers (PDF)](../../../papers/README.md) · 📚 [Monographs](../../../docs/README.md) · 🧾 [LaTeX](../../../src/README.md)
- ⚖️ [IPL-RP-1.0 License](../../../LICENSE.md) — viewing, a single backup copy, and citation with attribution are permitted; anything else requires the author's written consent.

*This block was added automatically (`doc-enhancer v1`); it is unrelated to the license and does not modify it. Re-running the script does not duplicate the block.*

