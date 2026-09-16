# 🐍 Section 6 — Riemann Zeros — the Hilbert–Pólya Programme (Python Reference)

> **Navigation:** [`verification`](../README.md) › **`section6_riemann_zeros`**

![Python](https://img.shields.io/badge/Python-3.10–3.12-informational?style=flat-square&logo=python&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![Section](https://img.shields.io/badge/Section-6-blue?style=flat-square)

This directory is the **Python reference implementation** of research Section 6 — the sixth section of the framework, covering the spectral correspondence between the AB-Cloud and the non-trivial zeros of the Riemann zeta function. Within the framework's layout it is the *numerical reference tier*: the simplest, dependency-free port that every other language port can be diffed against.

The implementation is intentionally minimal — pure standard library (`math` only), a single `verify.py` entry point, and the framework's uniform output contract: the computed quantities are printed, each expected property is asserted with a `[PASS]` line, and the run ends with the `JSON:` verdict. For Section 6 the quantities are the Hilbert–Pólya realisation, the Montgomery–Dyson GUE correspondence and the statistical identity of the two spectra; the assertions exercise spectral-correspondence identities and the statistical machinery (⟨r⟩, KS, permutation tests) in constructive and classical form.

Run it with `python3 python/verify.py` — total runtime is well under a second. The same section exists in the formal tier ([`lean4`](../lean4/README.md), [`coq`](../coq/README.md), [`isabelle`](../isabelle/README.md), [`agda`](../agda/README.md)) and in the extended computational ports ([`cpp`](../cpp/README.md), [`rust`](../rust/README.md), [`haskell`](../haskell/README.md)); CI runs them all in [`ci-cross-language.yml`](../../.github/workflows/README.md).

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`python/`](python/) | — | the Python reference port — single verify.py entry point |

## 🗂 Directory Layout

```
section6_riemann_zeros/
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

**verification/section6_riemann_zeros/** — the Python reference of Section 6 (Riemann Zeros — the Hilbert–Pólya Programme): pure stdlib, a single verify.py, PASS/JSON output; result — the Hilbert–Pólya realisation, the Montgomery–Dyson GUE correspondence and the statistical identity of the two spectra.

---

<div align="center">

**[⬆ Back to top](#-section-6--riemann-zeros--the-hilbertpólya-programme-python-reference)** · 
**[Repository root](../README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>

---
## 🔬 Deep Dive — Section 6

**What is verified here.** the Riemann-zeros correspondence: embedding of the frozen ζ-zero dataset, GUE-class gap statistics, and the long-range diagnostics (Σ²(L)) that operationalise the Hilbert–Pólya compatibility structure. The full-scale statistical case is the AB-Cloud suite's; this section checks the structural skeleton with the same frozen data.

**Reference command.**

```bash
`python3 verification/section6_riemann_zeros/python/verify.py`
```

**Formal counterparts.** The structural statements live in the four proof assistants: `../../lean4/ResearchPapersVerification/Section6_RiemannZeros/` · `../../coq/section6_riemann_zeros/` · `../../isabelle/Section6_RiemannZeros/` · `../../agda/Section6_RiemannZeros/` — with lemma names mirroring the computational assertions (see the root README's [formal deep dive](../../README.md#-appendix-w--formal-verification-deep-dive) for the Lean anatomy).

**Where it appears in the papers.** Each section maps onto a specific document layer: the preprint for the chain-type claims, the flagship paper for the constant's consequences, the KdV chapter for the integrable-systems results, the Klein-attractor reports for the dynamical-systems content, and the AB-Cloud monographs for the spectral programme. The mapping table is in the root README's [Section-by-Section Guide](../../README.md#-section-by-section-verification-guide).

**Contract reminder.** The port prints a banner, per-assertion `[PASS]/[FAIL]` lines, and the JSON verdict; exit code 0 only on full success. The cross-language validator consumes that JSON mechanically — any disagreement across languages fails CI.

---
The frozen ζ-zero table is an input here — do not regenerate it. The section's GUE-class gap assertions and Σ²(L) diagnostics are the structural skeleton of the Hilbert–Pólya compatibility; the full-scale statistical case is the AB-Cloud suite's. Diffing this section across languages is the cheapest whole-framework sanity check, since it exercises data loading plus statistics in one port.

---
## 🔗 Cross-Links

Formal: [lean4](../lean4/README.md).

<!-- doc-enhancer:block v1 (automatic block; license files are not affected) -->

---

## 🧭 Navigation and Quick Links (auto)

- 🏠 [Repository root](../../../README.md)
- 📖 [How the claims are verified](../../../verification/README.md)
- 📄 [Papers (PDF)](../../../papers/README.md) · 📚 [Monographs](../../../docs/README.md) · 🧾 [LaTeX](../../../src/README.md)
- ⚖️ [IPL-RP-1.0 License](../../../LICENSE.md) — viewing, a single backup copy, and citation with attribution are permitted; anything else requires the author's written consent.

*This block was added automatically (`doc-enhancer v1`); it is unrelated to the license and does not modify it. Re-running the script does not duplicate the block.*

