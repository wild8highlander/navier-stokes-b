# 🧾 src · preprint — the NSE Preprint Source

> **Navigation:** [`src`](../README.md) › **`preprint`**

![Format](https://img.shields.io/badge/Format-LaTeX-008080?style=flat-square&logo=latex) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

LaTeX source of the **compact NSE regularity preprint** — the typeset original of the ~120 KB PDFs in [`papers/preprint/`](../../papers/preprint/README.md). The `      itle` line matches the published preprint verbatim: *"Correction b as Polarization Twisting: Analytical Proof of 3D Navier–Stokes Regularity without Dissipation"*, authored by Iskhak Hamzatovich Isaev, dated 2026.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`preprint.tex`](preprint.tex) | 11.8 KB | LaTeX source of the preprint — title, abstract and the full compact argument (~12 KB) |

## 🔗 Cross-References

- [Typeset PDFs](../../papers/preprint/README.md)
- [Parent folder](../README.md)

## 🇷🇺 Brief Summary

Source of the compact preprint on NSE regularity (~12 KB); the PDF is in papers/preprint/.

---

<div align="center">

**[⬆ Back to top](#-src--preprint--the-nse-preprint-source)** · 
**[Repository root](../README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>


---

## 📄 The Preprint Source

`preprint.tex` — the single-file LaTeX source of the compact NSE regularity preprint. Its compiled form is the ~120 KB PDF in [`papers/preprint/`](../../papers/preprint/README.md) (identical as v1 and v2).

**Compiling:**

```bash
pdflatex preprint.tex
pdflatex preprint.tex
```

**Why a separate preprint exists.** The full paper is ~2.3 MB with the complete derivation apparatus; the preprint compresses the argument to four moves (constant → twist → BKM reduction → regularity) for readers who need the claim and its structure in one sitting. The source mirrors that compression: same notation as the paper, minimal preamble, no figure dependencies.

**The title page claim** — *"Correction b as Polarization Twisting: Analytical Proof of 3D Navier–Stokes Regularity without Dissipation"* — is the shortest formal statement of Program 1, and Section 2 of the verification framework mirrors it: run `python3 verification/section2_preprint/python/verify.py` to see the chain asserted numerically.

<!-- doc-enhancer:block v1 (automatic block; license files are not affected) -->

---

## 🧭 Navigation and Quick Links (auto)

- 🏠 [Repository root](../../../README.md)
- 📖 [How claims are verified](../../../verification/README.md)
- 📄 [Papers (PDF)](../../../papers/README.md) · 📚 [Monographs](../../../docs/README.md) · 🧾 [LaTeX](../../../src/README.md)
- ⚖️ [IPL-RP-1.0 License](../../../LICENSE.md) — viewing, one backup copy and citation with attribution are permitted; anything else only with the author's written consent.

*Block added automatically (`doc-enhancer v1`); it is not related to the license and does not modify it. Re-running the script does not duplicate the block.*
