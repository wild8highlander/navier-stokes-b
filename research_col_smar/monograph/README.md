# `research_col_smar/monograph/` — the updated monographs (the 96³ edition)

> **Navigation:** [repository root](../../README.md) › [research_col_smar](../README.md) › **`monograph`**

![Edition](https://img.shields.io/badge/Edition-96%C2%B3--updated-2B579A?style=flat-square)
![Languages](https://img.shields.io/badge/Languages-RU_·_EN-1284BA?style=flat-square)
![Formats](https://img.shields.io/badge/Formats-PDF_·_DOCX-2EA043?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

---

All monograph files of the satellite program, updated by the
**NSB-96-UPGRADE** package. The structure of the originals is preserved
exactly — same styles, same chapter numbering, same appendices; only new
sections and figures reflecting the doubled-resolution computations were
added.

## The Smagorinsky–Kolmogorov constants monograph

| File | Language | Format | What is new |
|---|---|---|---|
| `MONOGRAPH_RU.pdf` | Russian | PDF | chapter 15 "Reproduction at doubled resolution: 48³ → 96³, 112³ and the 112×112 matrices" (§15.1–15.5, figures 11–14); updated abstract, introduction (§1), chapter 12, conclusion and code map |
| `MONOGRAPH_RU.docx` | Russian | DOCX | the same content, identical |
| `MONOGRAPH_EN.pdf` | English | PDF | ch. 15 "Reproduction at doubled resolution: 48³ → 96³, 112³ and 112×112 matrices" |
| `MONOGRAPH_EN.docx` | English | DOCX | the same content, identical |

The editable masters of this edition live in
[`research_col_smar/`](research_col_smar/README.md) (DOCX + formula
plates); the `cover_ru.html` / `cover_en.html` at the satellite root are
the cover sources.

## The numbers pinned in the new sections

* 96³, the main P5 test: **WIN 8 / DRAW 1 / LOSS 0** — convergence to 48³
  within `1.1×10⁻⁴ … 1.9×10⁻²` (Ω_max 1.299654, I_BKM 17.878641);
* the b-protocol at 96³: `I_BKM(B)/I_BKM(A) − 1 = 2.4×10⁻³` (WIN);
* the b-family at 96³ (5/4, 3/2, 2): `k_max·η_b` doubled, the collapse
  `k_d·η_b → x*(b)` with the same 10.9–11.1 % systematics as at 48³;
* the 112×112 matrix checks: WIN 8/8; the 112³ DNS: energy balance
  `9.9×10⁻⁵`;
* the error attribution (L16): the 48³↔96³ divergence is spectral-tail
  resolution, not the time step (spatial/temporal error ratio ×6…×52).

Every number is reproduced by the tools of the package
([`tools/`](../tools/README.md)) and cross-checked against the references
in [`reference/`](../reference/README.md) and
[`results/`](../results/README.md).

## Deployment in the repository

| Monograph | PDF | DOCX masters |
|---|---|---|
| the constants monograph (this directory) | `MONOGRAPH_{RU,EN}.pdf` | [`research_col_smar/`](research_col_smar/README.md) |
| the KdV chapter 16 | [`../../papers/kdv/`](../../papers/kdv/README.md) | [`../../docs/kdv/{ru,en}/`](../../docs/kdv/README.md) |
| the root b-correction monograph | [`../../monograph/`](../../monograph/README.md) | — |

## License

Part of **navier-stokes-b**, license IPL-RP-1.0 ([LICENSE.md](../../LICENSE.md)).
