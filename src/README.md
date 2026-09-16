# 🧾 src — LaTeX Sources of the Papers

> **Navigation:** **`src`**

![Format](https://img.shields.io/badge/Format-LaTeX-008080?style=flat-square&logo=latex) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![Repo](https://img.shields.io/badge/Repo-wild8highlander%2Fnavier--stokes--b-181717?style=flat-square&logo=github&logoColor=white)

This directory holds the **compilable LaTeX sources** behind the PDFs published in [`papers/`](../papers/README.md). Two groups live here:

- **[`main/`](main/README.md)** — the source of the full correction-b paper: `main.tex` (~55 KB, the primary document) and `main_v2.tex` (the revision-stamped copy), complete with a custom accent-coloured sectioning setup (`        itleformat` with the `accent` colour) and running headers;
- **[`preprint/`](preprint/README.md)** — `preprint.tex`, the source of the compact NSE regularity preprint whose title page reads *"Correction b as Polarization Twisting: Analytical Proof of 3D Navier–Stokes Regularity without Dissipation"*.

The sources are the authoritative textual record: any wording in the PDFs can be traced, diffed and quoted against them. They are intentionally plain LaTeX — no exotic packages beyond standard formatting needs — so the documents compile in any modern TeX distribution. The monograph figures referenced by the manuscripts are preserved with the Word editions in [`docs/`](../docs/README.md), and the two-language NS package monograph with the open-problems annexes lives in [`monograph/`](../monograph/).

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`main/`](main/) | — | source of the full correction-b paper (main.tex + main_v2.tex) |
| [`preprint/`](preprint/) | — | source of the NSE preprint |

## 🗂 Directory Layout

```
src/
├── main/   # 3 files
│   ├── main.tex
│   ├── main_v2.tex
│   └── README.md  (this file)
├── preprint/   # 2 files
│   ├── preprint.tex
│   └── README.md  (this file)
└── README.md  (this file)
```

## 🇷🇺 Brief Summary

**src/** — the compilable LaTeX sources of the papers: `main/` — the full paper on the b-correction (main.tex ~55 KB + main_v2.tex) and `preprint/` — the preprint on NSE regularity (preprint.tex). They make it possible to trace and quote any wording from the PDFs.

---

<div align="center">

**[⬆ Back to top](#-src--latex-sources-of-the-papers)** · 
**[Repository root](README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>


---

## 🧭 Working With the LaTeX Sources

### Compilation

The sources are intentionally plain LaTeX — standard article class plus common formatting packages, no exotic dependencies — so any modern TeX distribution (TeX Live, MiKTeX, MacTeX, or Overleaf) compiles them without surprises:

```bash
# Full paper (correction-b)
cd src/main
pdflatex main.tex && pdflatex main.tex     # two passes for references

# Preprint
cd src/preprint
pdflatex preprint.tex && pdflatex preprint.tex
```

Two passes are needed for cross-references and running headers (the sources define an accent-coloured sectioning setup with `titleformat` and running heads via `fancyhdr`).

### What Each Subfolder Contains

**[`main/`](main/README.md)** — the full correction-b paper source: `main.tex` (~55 KB, the primary document) and `main_v2.tex` (the revision-stamped copy matching `papers/correction-b/main_v2.pdf`). The custom accent colour, the sectioning setup and the headers are defined in the preamble of the document itself — no external style files to install.

**[`preprint/`](preprint/README.md)** — `preprint.tex`, the compact NSE regularity preprint source; compiles to the ~120 KB PDF in [`papers/preprint/`](../papers/preprint/README.md).

### Why Sources Matter

The LaTeX sources are the **authoritative textual record** of the papers: any wording in a PDF can be traced, diffed and quoted against them. For citation disputes, for translation work, and for quoting with precision, the source is the ground truth. The two-language NS package monograph (RU/EN × DOCX/PDF) with the open-problems packages is kept in [`monograph/`](../monograph/).

### Relationship Map

| Layer | Directory | Format | Role |
|---|---|---|---|
| Final papers | [`papers/`](../papers/README.md) | PDF | what to cite |
| **Compilable sources** | **`src/` (this directory)** | `.tex` | what to diff and quote |
| Manuscripts | [`docs/`](../docs/README.md) | `.docx` | what was circulated |
| Verification | [`verification/`](../verification/README.md) | code | what backs the numbers |

---
## 🧩 Typography and Layout Conventions

Both documents share a house typographic setup that a future revision should preserve:

- **accent-coloured sectioning** — `titleformat` with a custom `accent` colour for section headings, giving the papers their visual identity;
- **running headers** via `fancyhdr` — paper title on even pages, section on odd;
- **standard math environments** — no custom theorem styles beyond basics, keeping the sources portable across TeX engines;
- **two-pass compilation** — cross-references and headers settle on the second `pdflatex` pass.

## 📏 Diffing the Two main.tex Files

`main.tex` and `main_v2.tex` are intentionally near-identical — the revision stamp is the meaningful delta. To see it:

```bash
diff src/main/main.tex src/main/main_v2.tex
```

Expected: the revision banner and any stamp metadata differ; the mathematical content is the same. If a future revision introduces real content changes, the convention is a *new* filename (v3), never a silent edit of the existing pair — the published PDFs must remain traceable to the exact source that produced them.

## 🔗 From Source to Claim to Verification

A worked example of the traceability chain, starting from raw LaTeX:

1. The source contains the constant's closed form in the derivation section;
2. the same closed form is `bCorrection` in [`verification/lean4/.../Foundation.lean`](../verification/lean4/README.md) — compiled with `bCorrection_pos` and `bCorrection_lt_one`;
3. the same number is printed by every Section 1 port (`python3 verification/section1_correction_b/python/verify.py` …);
4. the value appears in the root README's results table (row 1) with a link to the section directory.

Four representations — prose, theorem, computation, table — of one mathematical object, all inside one repository. That is the standard every claim here is held to.

<!-- doc-enhancer:block v1 (automatic block; license files are not affected) -->

---

## 🧭 Navigation and Quick Links (auto)

- 🏠 [Repository root](../../README.md)
- 📖 [How claims are verified](../../verification/README.md)
- 📄 [Papers (PDF)](../../papers/README.md) · 📚 [Monographs](../../docs/README.md) · 🧾 [LaTeX](../../src/README.md)
- ⚖️ [IPL-RP-1.0 License](../../LICENSE.md) — viewing, one backup copy and citation with attribution are permitted; anything else only with the author's written consent.

*Block added automatically (`doc-enhancer v1`); it is not related to the license and does not modify it. Re-running the script does not duplicate the block.*
