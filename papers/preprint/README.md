# 📃 Papers · Preprint — Correction b as Polarization Twisting (NSE Regularity, v1 + v2)

> **Navigation:** [`papers`](../README.md) › **`preprint`**

![Papers](https://img.shields.io/badge/Content-Research%20Papers-blue?style=flat-square&logo=adobeacrobatreader&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![RU](https://img.shields.io/badge/RU-Summary-blue?style=flat-square)

This folder holds the **compact preprint** stating the Navier–Stokes regularity result end-to-end in minimal form: *"Correction b as Polarization Twisting: Analytical Proof of 3D Navier–Stokes Regularity without Dissipation"* (author: Iskhak Hamzatovich Isaev, 2026). At roughly 120 KB per copy it is the **smallest complete document** in the repository and the recommended fifteen-minute entry point before the full paper in [`correction-b/`](../correction-b/README.md).

Two byte-identical copies are kept (`preprint_v1.pdf`, `preprint_v2.pdf`) so that links written against either filename keep working; both are the same final revision. The LaTeX source of exactly this text lives in [`src/preprint/preprint.tex`](../../src/preprint/README.md) — the `      itle` line there matches the title above, which makes the folder a convenient reference pair (typeset PDF + compilable source).

The preprint corresponds to **Section 2** of the verification framework: the argument chain (positivity and scale of *b*, the rotation mechanism, the BKM reduction) is exercised by every language port, and its structural lemmas are the ones machine-checked in Lean 4, Coq, Isabelle and Agda.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`preprint_v1.pdf`](preprint_v1.pdf) | 117.0 KB | the NSE regularity preprint — final revision (~120 KB) |
| [`preprint_v2.pdf`](preprint_v2.pdf) | 117.0 KB | byte-identical twin of preprint_v1.pdf kept under a version-stamped name |

## 🔗 Cross-References

- [LaTeX source — src/preprint/](../../src/preprint/README.md)
- [Full paper — papers/correction-b/](../correction-b/README.md)
- [Section 2 verification framework](../../verification/README.md)

## 🇷🇺 Brief Summary

**papers/preprint/** — the compact preprint *"Correction b as Polarization Twisting: Analytical Proof of 3D Navier–Stokes Regularity without Dissipation"* (~120 KB). The shortest complete document in the repository — the recommended first paper. Two files — identical copies of one edition; LaTeX source — `src/preprint/preprint.tex`; verification — Section 2 (`verification/`).

---

<div align="center">

**[⬆ Back to top](#-papers--preprint--correction-b-as-polarization-twisting-nse-regularity-v1--v2)** · 
**[Repository root](../README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>


---

## 🔍 About This Preprint

The preprint is the **shortest complete statement** of the NSE regularity result — roughly 120 KB, a fifteen-minute read, and the best possible entry point into the repository. Its title says the claim outright: *"Correction b as Polarization Twisting: Analytical Proof of 3D Navier–Stokes Regularity without Dissipation"*.

In four moves it covers what the flagship paper develops at full length:

1. the constant *b* = π/(4π² + 2π√3) and its Kirchhoff origin;
2. the polarization twist θ_b ≈ 7.07° and the Rodrigues rotation R_b;
3. the 3.5× reduction of the BKM blow-up integral;
4. the regularity conclusion and where the full derivation lives.

## 📄 v1 vs v2

`preprint_v1.pdf` and `preprint_v2.pdf` are identical — the same final revision under two filenames, kept for linking convenience. Either may be cited; `v2` is the name used in the repository's documentation.

## 🧪 Verification Behind This Preprint

The preprint's chain is Section 2 of the verification framework: the twist unitarity, the BKM bound, the chain of estimates from twist to regularity — structurally compiled in the four proof assistants, numerically echoed in every computational port. See [`verification/section2_preprint/`](../../verification/section2_preprint/README.md) and the formal deep dive in the root README.

## 🗺 Where to Go Next

- the LaTeX source: [`../../src/preprint/preprint.tex`](../../src/preprint/README.md);
- the full paper: [`../correction-b/`](../correction-b/README.md);
- run the Section 2 port: `python3 verification/section2_preprint/python/verify.py` (from the repository root).

<!-- doc-enhancer:block v1 (automatic block; license files are not affected) -->

---

## 🧭 Navigation and Quick Links (auto)

- 🏠 [Repository root](../../../README.md)
- 📖 [How claims are verified](../../../verification/README.md)
- 📄 [Papers (PDF)](../../../papers/README.md) · 📚 [Monographs](../../../docs/README.md) · 🧾 [LaTeX](../../../src/README.md)
- ⚖️ [IPL-RP-1.0 License](../../../LICENSE.md) — viewing, one backup copy and citation with attribution are permitted; anything else only with the author's written consent.

*Block added automatically (`doc-enhancer v1`); it is not related to the license and does not modify it. Re-running the script does not duplicate the block.*
