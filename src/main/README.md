# 🧾 src · main — the Correction-b Paper Source

> **Navigation:** [`src`](../README.md) › **`main`**

![Format](https://img.shields.io/badge/Format-LaTeX-008080?style=flat-square&logo=latex) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

LaTeX source of the **full correction-b paper** — the document typeset into the ~2.3 MB PDFs in [`papers/correction-b/`](../../papers/correction-b/README.md). Two files are kept: `main.tex` (the primary, ~55 KB) and `main_v2.tex` (the revision-stamped twin). The preamble sets up custom accent-coloured sectioning (`    itleformat{\section}{\Largebfseries\color{accent}}…`), running headers (the running-heads block), and the standard mathematical apparatus needed for the Kirchhoff-vortex derivation and the Navier–Stokes argument.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`main.tex`](main.tex) | 54.3 KB | primary LaTeX source of the paper (~55 KB, full document) |
| [`main_v2.tex`](main_v2.tex) | 54.3 KB | revision-stamped twin of main.tex (same text, versioned name) |

## 🔗 Cross-References

- [Typeset PDFs](../../papers/correction-b/README.md)
- [Parent folder](../README.md)

## 🇷🇺 Brief Summary

Source of the full paper (main.tex ~55 KB + the twin main_v2.tex); compiles with any modern TeX distribution.

---

<div align="center">

**[⬆ Back to top](#-src--main--the-correction-b-paper-source)** · 
**[Repository root](../README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>


---

## 📄 The Main Article Source

Two files, one content:

| File | Size | Role |
|---|---|---|
| `main.tex` | ~55 KB | the primary source document |
| `main_v2.tex` | ~55 KB | the revision-stamped copy matching `papers/correction-b/main_v2.pdf` |

**Structure of the document.** The preamble sets up the accent-coloured sectioning (`titleformat` with a custom `accent` colour), running headers (`fancyhdr`), and the mathematical apparatus. The body follows the paper's arc: the Kirchhoff derivation of *b*, the polarization twist construction (Rodrigues rotation about a unit axis), the BKM criterion reduction, the regularity proof, and the numerical stress-test section.

**Compiling:**

```bash
pdflatex main.tex
pdflatex main.tex        # second pass resolves cross-references
```

The document is self-contained — figures referenced by the Word edition live with the manuscripts in [`docs/correction-b/`](../../docs/correction-b/README.md); the PDF needs only standard packages.

**Tracing claims to verification.** While reading the source, the [Section × Language matrix](../../README.md#-verification-on-11-languages) is the companion: every quantitative statement in the text maps onto a section port or a formal lemma, and the root README's deep dive ([Appendix W](../../README.md#-appendix-w--formal-verification-deep-dive)) shows the Lean foundation that corresponds to §3–4 of this paper.

<!-- doc-enhancer:block v1 (automatic block; license files are not affected) -->

---

## 🧭 Navigation and Quick Links (auto)

- 🏠 [Repository root](../../../README.md)
- 📖 [How claims are verified](../../../verification/README.md)
- 📄 [Papers (PDF)](../../../papers/README.md) · 📚 [Monographs](../../../docs/README.md) · 🧾 [LaTeX](../../../src/README.md)
- ⚖️ [IPL-RP-1.0 License](../../../LICENSE.md) — viewing, one backup copy and citation with attribution are permitted; anything else only with the author's written consent.

*Block added automatically (`doc-enhancer v1`); it is not related to the license and does not modify it. Re-running the script does not duplicate the block.*
