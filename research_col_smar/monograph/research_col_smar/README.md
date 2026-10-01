# `research_col_smar/monograph/research_col_smar/` — the constants monograph (updated editions)

> **Navigation:** [repository root](../../../README.md) › [research_col_smar](../../README.md) › [monograph](../README.md) › **`research_col_smar`**

![Edition](https://img.shields.io/badge/Edition-96%C2%B3--updated-2B579A?style=flat-square)
![Languages](https://img.shields.io/badge/Languages-RU_·_EN-1284BA?style=flat-square)
![Formats](https://img.shields.io/badge/Formats-DOCX-2EA043?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

---

The **updated DOCX editions of the Smagorinsky–Kolmogorov monograph**
("The Smagorinsky and Kolmogorov constants…"), carrying the NSB-96-UPGRADE
results: the original structure — styles, chapter numbering, appendices —
is preserved exactly; the new chapter 15 and the updated abstract,
introduction, chapter 12, conclusion and code map reflect the
doubled-resolution reproduction program.

## The files

| File | Language | Content |
|---|---|---|
| `MONOGRAPH_RU.docx` | Russian | the full monograph with chapter 15 "Reproduction at doubled resolution: 48³ → 96³, 112³ and the 112×112 matrices" (§15.1–15.5, figures 11–14) |
| `MONOGRAPH_EN.docx` | English | the identical English edition |

The typeset PDF editions and the deployment targets are documented in the
[parent README](../README.md); the PDFs of the same editions live at the
monograph level.

## What the 96³ edition adds

| Addition | Where | Numbers |
|---|---|---|
| chapter 15 — the doubled-resolution reproduction (§15.1–15.5) | the NSB-96 labs L1–L8 | 96³ headline test: **WIN 8 / DRAW 1 / LOSS 0** (Ω_max 1.299654, I_BKM 17.878641); b-protocol at 96³: `I_BKM(B)/I_BKM(A) − 1 = 2.4×10⁻³`; b-family: `k_max·η_b` doubled, collapse band 10.9–11.1 %; 112×112 matrix checks WIN 8/8; 112³ DNS energy balance `9.9×10⁻⁵` |
| updated abstract, introduction, chapter 12, conclusion, code map | the NSB-96 narrative | the honest re-attribution of the spatial vs temporal error (L16) |

The KdV chapter's §16.29 and the φ-audit corrections (I1–I4) are
documented separately — see
[`papers/kdv/`](../../../papers/kdv/README.md) and
[`reports/PHI_FORMULA_FIXES.md`](../../reports/PHI_FORMULA_FIXES.md).

## Related layers

| Layer | Location |
|---|---|
| the core figure families of the monograph | [`../../figures/`](../../figures/README.md) · the NSB-96 additions in [`../../figures/figures/`](../../figures/figures/README.md) |
| the formula plates (F1–F28) used by both editions | [`../assets/`](../assets/README.md) |
| the pinned numbers behind every table | [`../../results/`](../../results/README.md) · [`../../reference/`](../../reference/README.md) |

## License

Part of **navier-stokes-b**, license IPL-RP-1.0 ([LICENSE.md](../../../LICENSE.md)).
