# Ⓜ️ Haskell — Formal/Numerical Verification Layer

> **Navigation:** [`verification`](../README.md) › **`haskell`**

![Haskell](https://img.shields.io/badge/Haskell-9.4-informational?style=flat-square&logo=haskell&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![Sections](https://img.shields.io/badge/Sections-6-blue?style=flat-square)

This directory carries the **Haskell (GHC 9.4) numerical-verification layer**: a Cabal project with one module per research section under `SectionN_*/src/`, registered in `cabal.project`. The ports mirror the framework contract — `Text.Printf`-formatted output at 15-digit precision, per-assertion PASS/FAIL lines and the final JSON verdict — while keeping the implementations idiomatic and short.

Section 1 (`Section1_CorrectionB/src`) defines `bCorrection = pi / (4·pi² + 2·pi·√3)` as a top-level `Double` binding and prints it with `printf "b = %.15e"`, exactly matching the values the other languages assert; later sections exercise the functional style on the spectral and dynamical scaffolding. GHC's purity makes these ports particularly readable as *executable specifications* of the claims.

Build with `cabal build` and run per-section executables with `cabal run`. CI builds the project in `ci-extended-languages.yml`.

Each section folder carries its own `src/` with the executable's `Main.hs`.

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
| [`cabal.project`](cabal.project) | 128 B | Cabal project file — registers all section packages |

## 🗂 Directory Layout

```
haskell/
├── Section1_CorrectionB/   # 4 files
│   ├── src/   # 2 files
│   │   ├── Main.hs
│   │   └── README.md  (this file)
│   ├── README.md  (this file)
│   └── Section1_CorrectionB.cabal
├── Section2_PreprintNSE/   # 4 files
│   ├── src/   # 2 files
│   │   ├── Main.hs
│   │   └── README.md  (this file)
│   ├── README.md  (this file)
│   └── Section2_PreprintNSE.cabal
├── Section3_ABCloud/   # 4 files
│   ├── src/   # 2 files
│   │   ├── Main.hs
│   │   └── README.md  (this file)
│   ├── README.md  (this file)
│   └── Section3_ABCloud.cabal
├── Section4_KdV/   # 4 files
│   ├── src/   # 2 files
│   │   ├── Main.hs
│   │   └── README.md  (this file)
│   ├── README.md  (this file)
│   └── Section4_KdV.cabal
├── Section5_KleinAttractor/   # 4 files
│   ├── src/   # 2 files
│   │   ├── Main.hs
│   │   └── README.md  (this file)
│   ├── README.md  (this file)
│   └── Section5_KleinAttractor.cabal
├── Section6_RiemannZeros/   # 4 files
│   ├── src/   # 2 files
│   │   ├── Main.hs
│   │   └── README.md  (this file)
│   ├── README.md  (this file)
│   └── Section6_RiemannZeros.cabal
├── cabal.project
└── README.md  (this file)
```

## ▶️ How to Run

```bash
cd verification/haskell
cabal build && cabal run <section>
```
Build step: `cabal build`.

## 📝 Summary

**verification/haskell/** — the Haskell (9.4) verification layer: a GHC implementation on Double with Text.Printf output under the common contract. Six per-section ports (1: Correction b, 2: Preprint NSE, 3: AB-Cloud, 4: KdV, 5: Klein Attractor, 6: Riemann Zeros); the uniform PASS/JSON contract; build commands — see the How to Run section.

---

<div align="center">

**[⬆ Back to top](#-haskell--formalnumerical-verification-layer)** · 
**[Repository root](../README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>

---
## 🏡 Package Anatomy

Six Cabal packages under one [`cabal.project`](cabal.project):

| Package | Section | Notes |
|---|---|---|
| `Section1_CorrectionB` | 1 | pure closed-form evaluation |
| `Section2_PreprintNSE` | 2 | rotation chain in pure functions |
| `Section3_ABCloud` | 3 | structural Hofstadter checks |
| `Section4_KdV` | 4 | symbolic-then-numeric conservation |
| `Section5_KleinAttractor` | 5 | ergodic statistics over the reference ensemble |
| `Section6_RiemannZeros` | 6 | spacing diagnostics |

GHC 9.4 is the pinned toolchain (ghcup); `cabal.project` keeps the resolver stable. The implementations are pure — no `unsafe`, no FFI — which makes the Haskell ports the easiest full-source audit of the computational tier.

## 🔁 Running Patterns

```bash
cabal update                     # once; stale indexes produce resolver noise
cabal build                      # all six packages
cabal run section1-correction-b  # one section
```

Package names use dashes (Cabal convention) while directories use underscores — the mapping table above is the bridge.

---
## 🎯 What Haskell Contributes

The Haskell ports are the pure-functional witness: the section contracts expressed as types and pure functions, auditable end-to-end by reading. Where C++ shows the contract survives performance engineering, Haskell shows it survives paradigm distance — a theorem of the framework's own portability claim.

---
## 🔗 See Also

- [`cabal.project`](cabal.project) — the resolver pin;
- the naming bridge table (dashes vs underscores);
- the [verification contract](../README.md#-the-verification-contract) — what `cabal run` must print.

<!-- doc-enhancer:block v1 (auto-inserted block; license files are not touched) -->

---

## 🧭 Navigation and Quick Links (auto)

- 🏠 [Repository root](../../../README.md)
- 📖 [How the claims are verified](../../../verification/README.md)
- 📄 [Papers (PDF)](../../../papers/README.md) · 📚 [Monographs](../../../docs/README.md) · 🧾 [LaTeX](../../../src/README.md)
- ⚖️ [IPL-RP-1.0 License](../../../LICENSE.md) — viewing, one backup copy and citation with attribution are allowed; everything else only with the Author's written consent.

*Block inserted automatically (`doc-enhancer v1`); it is not part of the license and does not modify it. Re-running the script does not duplicate the block.*

