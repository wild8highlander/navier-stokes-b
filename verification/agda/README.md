# Ⓜ️ Agda — Formal/Numerical Verification Layer

> **Navigation:** [`verification`](../README.md) › **`agda`**

![Agda](https://img.shields.io/badge/Agda-2.6-informational?style=flat-square&logo=agda&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![Sections](https://img.shields.io/badge/Sections-6-blue?style=flat-square)

This directory carries the **Agda (2.6) formal-verification layer**: a dependently-typed, constructive development with one module per research section, compiled with `--safe`. Agda's contribution to the framework is the **minimal trust base**: π and √3 are explicit `postulate`s rather than library imports, so the axioms a reader must accept are visible in the first lines of each file.

The modules define `b-correction` as a rational-expression division over `Data.Rational`, carry postulated positivity/bound lemmas (`b-pos`, `b-lt-one`), and develop the per-section constructions (PSL(2,7) proof chain in Section 2, Hofstadter scaffolding in Section 3, and so on). The `agda.agda-lib` file registers the include roots so `agda` resolves `SectionN_*` modules from anywhere.

Check any module with `agda Section1_CorrectionB/CorrectionB.agda` (or `--safe` for the CI configuration). CI type-checks the modules in `ci-extended-languages.yml`.

## 🗂 The Six Section Ports

- [`Section1_CorrectionB/`](Section1_CorrectionB/README.md) — Correction b — the Universal Polarization Constant
- [`Section2_PreprintNSE/`](Section2_PreprintNSE/README.md) — Preprint NSE — the Regularity Argument Chain
- [`Section3_ABCloud/`](Section3_ABCloud/README.md) — AB-Cloud — the Non-Hermitian Hofstadter Hamiltonian
- [`Section4_KdV/`](Section4_KdV/README.md) — KdV — Soliton Interactions under the b-Correction
- [`Section5_KleinAttractor/`](Section5_KleinAttractor/README.md) — Klein Attractor — Ergodic Dynamics and the NSE Bridge
- [`Section6_RiemannZeros/`](Section6_RiemannZeros/README.md) — Riemann Zeros — the Hilbert–Pólya Programme

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`Section1_CorrectionB/`](Section1_CorrectionB/) | — | Section 1 port — Correction b — the Universal Polarization Constant |
| [`Section2_PreprintNSE/`](Section2_PreprintNSE/) | — | Section 2 port — Preprint NSE — the Regularity Argument Chain |
| [`Section3_ABCloud/`](Section3_ABCloud/) | — | Section 3 port — AB-Cloud — the Non-Hermitian Hofstadter Hamiltonian |
| [`Section4_KdV/`](Section4_KdV/) | — | Section 4 port — KdV — Soliton Interactions under the b-Correction |
| [`Section5_KleinAttractor/`](Section5_KleinAttractor/) | — | Section 5 port — Klein Attractor — Ergodic Dynamics and the NSE Bridge |
| [`Section6_RiemannZeros/`](Section6_RiemannZeros/) | — | Section 6 port — Riemann Zeros — the Hilbert–Pólya Programme |
| [`agda.agda-lib`](agda.agda-lib) | 60 B | Agda library file — include roots and module list |

## 🗂 Directory Layout

```
agda/
├── Section1_CorrectionB/   # 2 files
│   ├── CorrectionB.agda
│   └── README.md  (this file)
├── Section2_PreprintNSE/   # 2 files
│   ├── ProofChain.agda
│   └── README.md  (this file)
├── Section3_ABCloud/   # 2 files
│   ├── Hofstadter.agda
│   └── README.md  (this file)
├── Section4_KdV/   # 2 files
│   ├── KdV.agda
│   └── README.md  (this file)
├── Section5_KleinAttractor/   # 2 files
│   ├── Klein.agda
│   └── README.md  (this file)
├── Section6_RiemannZeros/   # 2 files
│   ├── README.md  (this file)
│   └── RiemannZeros.agda
├── agda.agda-lib
└── README.md  (this file)
```

## ▶️ How to Run

```bash
cd verification/agda
agda <Module>.agda
```
Build step: `agda --safe <Module>.agda`.

## 🇷🇺 Brief Summary (Russian Summary)

**verification/agda/** — the Agda (2.6) verification layer: a dependently-typed constructive development; π and √3 are explicit postulates. Six per-section ports (1: Correction b, 2: Preprint NSE, 3: AB-Cloud, 4: KdV, 5: Klein Attractor, 6: Riemann Zeros); a uniform PASS/JSON contract; build commands are in the How to Run section.

---

<div align="center">

**[⬆ Back to top](#-agda--formalnumerical-verification-layer)** · 
**[Repository root](../README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>

---
## 🧱 Development Anatomy

Six modules, dependently typed:

| Module | Section | Notes |
|---|---|---|
| `Section1_CorrectionB/CorrectionB.agda` | 1 | π and √3 postulated explicitly |
| `Section2_PreprintNSE/ProofChain.agda` | 2 | chain as indexed structure |
| `Section3_ABCloud/Hofstadter.agda` | 3 | flux structure as inductive data |
| `Section4_KdV/KdV.agda` | 4 | conservation as type-level identity |
| `Section5_KleinAttractor/Klein.agda` | 5 | contraction statements |
| `Section6_RiemannZeros/RiemannZeros.agda` | 6 | embedding compatibility |

## 🔬 The Minimal Trust Base

The Agda development's defining choice is the **explicit postulation policy**: π and √3 enter as postulates at the top of each development, with their essential properties (positivity, the needed bounds) stated — and everything else is constructed. This keeps the trust base *visible and enumerable*: a reviewer can read the postulate block and know exactly what is being taken on faith. The repository's philosophy is that an honest, two-line trust base beats an implicit one; the same policy is why the gap ledger of the Lean development is public (see the root README's [deep dive](../README.md#-appendix-w--formal-verification-deep-dive)).

## 🐳 Running Agda Without Installing It

```bash
docker build -t rp-agda verification/docker/agda
docker run --rm -v "$PWD":/work rp-agda agda verification/agda/Section1_CorrectionB/CorrectionB.agda
```

Run from the repository root or set the include path per `agda.agda-lib`.

---
## 🎯 What Agda Proves About the Trust Base

Because π and √3 are the only postulates, everything else in the Agda development is *constructed* — including the order relations and the algebraic identities other systems get from their standard libraries. Reading the Agda files is therefore the fastest way to see exactly which properties of π and √3 the whole framework's formal layer actually needs: read the postulate block, and you have enumerated the formal trust base.

---
## 🔗 See Also

- the postulate blocks in each module — the enumerated trust base;
- [`agda.agda-lib`](agda.agda-lib) — include-path configuration;
- the formal deep dive in the root README for the cross-system comparison table.

<!-- doc-enhancer:block v1 (automatic block; license files are not affected) -->

---

## 🧭 Navigation and Quick Links (auto)

- 🏠 [Repository root](../../../README.md)
- 📖 [How the claims are verified](../../../verification/README.md)
- 📄 [Papers (PDF)](../../../papers/README.md) · 📚 [Monographs](../../../docs/README.md) · 🧾 [LaTeX](../../../src/README.md)
- ⚖️ [IPL-RP-1.0 License](../../../LICENSE.md) — viewing, a single backup copy, and citation with attribution are permitted; anything else requires the author's written consent.

*This block was added automatically (`doc-enhancer v1`); it is unrelated to the license and does not modify it. Re-running the script does not duplicate the block.*

