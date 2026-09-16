# 📗 Papers · KdV — Soliton Interactions under the b-Correction (Chapter 16, EN + RU)

> **Navigation:** [`papers`](../README.md) › **`kdv`**

![Papers](https://img.shields.io/badge/Content-Research%20Papers-blue?style=flat-square&logo=adobeacrobatreader&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![RU](https://img.shields.io/badge/RU-Summary-blue?style=flat-square)

This folder contains the **book chapter on the Korteweg–de Vries equation** in two full language editions: `KdV_b_correction_Chapter16_EN.pdf` (7.2 MB) and `KdV_b_correction_Chapter16_RU.pdf` (7.4 MB). The chapter is the largest single document in the papers collection and studies how the universal polarization correction *b* ≈ 0.0785 — the same constant derived from Kirchhoff vortices in the correction-b paper — manifests itself in **soliton interactions** of the integrable KdV hierarchy.

The two editions are produced from a common source but are independent, complete publications: the EN edition serves the international reader, the RU edition is the author's native-language exposition. Word versions of the same chapter are archived in [`docs/kdv/`](../../docs/kdv/README.md) (one `.docx` per language) for editorial provenance.

On the verification side, the KdV program is Section 4 of the framework: the pseudospectral treatment has a C++ port in [`verification/cpp/section4_kdv/`](../../verification/cpp/section4_kdv/README.md), with formal scaffolding in the four proof assistants and the standard-library Python reference in [`verification/section4_kdv/`](../../verification/section4_kdv/README.md). The conservation-law identities checked across these ports back the numeric stability claims of the chapter.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`KdV_b_correction_Chapter16_EN.pdf`](KdV_b_correction_Chapter16_EN.pdf) | 6.9 MB | chapter 16 — English edition, ~7.2 MB, figure-rich typesetting |
| [`KdV_b_correction_Chapter16_RU.pdf`](KdV_b_correction_Chapter16_RU.pdf) | 7.0 MB | chapter 16 — Russian edition, ~7.4 MB, complete independent publication |

## 🔗 Cross-References

- [Word editions — docs/kdv/](../../docs/kdv/README.md)
- [Section 4 verification — C++ port](../../verification/cpp/section4_kdv/README.md)
- [Section 4 verification — Python reference](../../verification/section4_kdv/README.md)
- [Root README — Research Programs](../../README.md)

## 🇷🇺 Brief Summary

**papers/kdv/** — chapter 16 on the Korteweg–de Vries (KdV) equation: how the universal correction *b* ≈ 0.0785 manifests itself in the interactions of solitons of the integrable KdV hierarchy. Two complete editions: English (7.2 MB) and Russian (7.4 MB). Word versions — in `docs/kdv/`; numerical verification — Section 4 of the verification framework (`verification/cpp/section4_kdv/` — the C++ pseudospectral port).

---

<div align="center">

**[⬆ Back to top](#-papers--kdv--soliton-interactions-under-the-b-correction-chapter-16-en--ru)** · 
**[Repository root](../README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>


---

## 🔍 About This Chapter

*KdV_b_correction_Chapter16* extends the polarization correction *b* into **integrable systems territory**: the Korteweg–de Vries equation, the canonical model of shallow-water solitons. The chapter's argument arc:

1. **Setup.** The two-soliton sector of KdV, its standard interaction phenomenology (elastic collisions, phase shifts), and the pseudospectral machinery used to compute it.
2. **The correction.** How the *b*-correction enters the soliton sector — as a modulation of the interaction phase — and why the integrable structure survives it.
3. **The numerics.** FFT-based pseudospectral evolution with the conserved quantities (mass, momentum, energy) tracked across interactions; the port in [`verification/cpp/section4_kdv/`](../../verification/cpp/section4_kdv/README.md) reproduces the conservation checks to machine precision.
4. **The bridge.** What the result says about the universality of the polarization mechanism — the same constant that stabilises Navier–Stokes reappears as a phase modulation in an integrable model.

## 🌐 Two Genuine Language Editions

Unlike the correction-b pair (byte-identical twins), the KdV chapter ships as **two independently typeset editions**: English (7.2 MB) and Russian (7.4 MB). The content is the same; the typesetting, hyphenation and figure captions are native to each language. Cite the edition you actually read.

## 🧪 Verification Behind This Chapter

| Claim | Where it is checked |
|---|---|
| Conserved quantities across soliton interaction | C++ port `section4_kdv` (mass/momentum/energy errors at machine precision) |
| Two-soliton closed-form agreement | Python port `verification/section4_kdv/` |
| Formal treatment of the recursions | proof-assistant tier, Section 4 files (Lean/Coq/Isabelle/Agda) |

## 🗺 Where to Go Next

- Word edition for annotation: [`../../docs/kdv/`](../../docs/kdv/README.md);
- the C++ pseudospectral port: [`../../verification/cpp/section4_kdv/`](../../verification/cpp/section4_kdv/README.md);
- the flagship paper whose constant this chapter reuses: [`../correction-b/`](../correction-b/README.md).

<!-- doc-enhancer:block v1 (automatic block; license files are not affected) -->

---

## 🧭 Navigation and Quick Links (auto)

- 🏠 [Repository root](../../../README.md)
- 📖 [How claims are verified](../../../verification/README.md)
- 📄 [Papers (PDF)](../../../papers/README.md) · 📚 [Monographs](../../../docs/README.md) · 🧾 [LaTeX](../../../src/README.md)
- ⚖️ [IPL-RP-1.0 License](../../../LICENSE.md) — viewing, one backup copy and citation with attribution are permitted; anything else only with the author's written consent.

*Block added automatically (`doc-enhancer v1`); it is not related to the license and does not modify it. Re-running the script does not duplicate the block.*
