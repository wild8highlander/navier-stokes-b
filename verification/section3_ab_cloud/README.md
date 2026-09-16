# 🐍 Section 3 — AB-Cloud — the Non-Hermitian Hofstadter Hamiltonian (Python Reference)

> **Navigation:** [`verification`](../README.md) › **`section3_ab_cloud`**

![Python](https://img.shields.io/badge/Python-3.10–3.12-informational?style=flat-square&logo=python&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![Section](https://img.shields.io/badge/Section-3-blue?style=flat-square)

This directory is the **Python reference implementation** of research Section 3 — the third section of the framework, covering the 36³ non-Hermitian Hofstadter Hamiltonian with Aharonov–Bohm vortex fluxes. Within the framework's layout it is the *numerical reference tier*: the simplest, dependency-free port that every other language port can be diffed against.

The implementation is intentionally minimal — pure standard library (`math` only), a single `verify.py` entry point, and the framework's uniform output contract: the computed quantities are printed, each expected property is asserted with a `[PASS]` line, and the run ends with the `JSON:` verdict. For Section 3 the quantities are spectral construction with σ = 0.5 non-Hermiticity, α = 2.0 AB flux, disorder W = 1.0 and 5 000 embedded Riemann zeta zeros; the assertions exercise GUE-consistency of the spectrum (⟨r⟩ gap statistics), gauge invariance of the vortex decoration, and spectral stability under perturbations.

Run it with `python3 python/verify.py` — total runtime is well under a second. The same section exists in the formal tier ([`lean4`](../lean4/README.md), [`coq`](../coq/README.md), [`isabelle`](../isabelle/README.md), [`agda`](../agda/README.md)) and in the extended computational ports ([`cpp`](../cpp/README.md), [`rust`](../rust/README.md), [`haskell`](../haskell/README.md)); CI runs them all in [`ci-cross-language.yml`](../../.github/workflows/README.md).

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`python/`](python/) | — | the Python reference port — single verify.py entry point |

## 🗂 Directory Layout

```
section3_ab_cloud/
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

**verification/section3_ab_cloud/** — the Python reference of Section 3 (AB-Cloud — the Non-Hermitian Hofstadter Hamiltonian): pure stdlib, a single verify.py, PASS/JSON output; result — spectral construction with σ = 0.5 non-Hermiticity, α = 2.0 AB flux, disorder W = 1.0 and 5 000 embedded Riemann zeta zeros.

---

<div align="center">

**[⬆ Back to top](#-section-3--ab-cloud--the-non-hermitian-hofstadter-hamiltonian-python-reference)** · 
**[Repository root](../README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>

---
## 🔬 Deep Dive — Section 3

**What is verified here.** the AB-Cloud Hamiltonian's structural core: the Hofstadter skeleton with Aharonov–Bohm decoration at reduced scale, flux quantisation, Hermiticity of the reference operator, and the symmetry-class checks the heavy 36³ statistics presuppose. The heavy statistics live in the AB-Cloud suite; this section verifies the structure those runs stand on.

**Reference command.**

```bash
`python3 verification/section3_ab_cloud/python/verify.py`
```

**Formal counterparts.** The structural statements live in the four proof assistants: `../../lean4/ResearchPapersVerification/Section3_ABCloud/` · `../../coq/section3_ab_cloud/` · `../../isabelle/Section3_ABCloud/` · `../../agda/Section3_ABCloud/` — with lemma names mirroring the computational assertions (see the root README's [formal deep dive](../../README.md#-appendix-w--formal-verification-deep-dive) for the Lean anatomy).

**Where it appears in the papers.** Each section maps onto a specific document layer: the preprint for the chain-type claims, the flagship paper for the constant's consequences, the KdV chapter for the integrable-systems results, the Klein-attractor reports for the dynamical-systems content, and the AB-Cloud monographs for the spectral programme. The mapping table is in the root README's [Section-by-Section Guide](../../README.md#-section-by-section-verification-guide).

**Contract reminder.** The port prints a banner, per-assertion `[PASS]/[FAIL]` lines, and the JSON verdict; exit code 0 only on full success. The cross-language validator consumes that JSON mechanically — any disagreement across languages fails CI.

---
This section is deliberately *structural only*: it verifies what the heavy AB-Cloud statistics presuppose (flux quantisation, Hermiticity, symmetry classes) and leaves the statistics to the suite that owns the frozen tables. If you change the Hamiltonian construction anywhere, this section is the first gate the change must pass.

---
## 🔗 Cross-Links

Formal: [lean4](../lean4/README.md) · [coq](../coq/README.md) · [isabelle](../isabelle/README.md) · [agda](../agda/README.md).

<!-- doc-enhancer:block v1 (automatic block; license files are not affected) -->

---

## 🧭 Navigation and Quick Links (auto)

- 🏠 [Repository root](../../../README.md)
- 📖 [How the claims are verified](../../../verification/README.md)
- 📄 [Papers (PDF)](../../../papers/README.md) · 📚 [Monographs](../../../docs/README.md) · 🧾 [LaTeX](../../../src/README.md)
- ⚖️ [IPL-RP-1.0 License](../../../LICENSE.md) — viewing, a single backup copy, and citation with attribution are permitted; anything else requires the author's written consent.

*This block was added automatically (`doc-enhancer v1`); it is unrelated to the license and does not modify it. Re-running the script does not duplicate the block.*

