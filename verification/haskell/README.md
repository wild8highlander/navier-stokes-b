# Ⓜ️ `haskell/` — the Haskell Numerical Verification Layer

> **Navigation:** [`verification`](../README.md) › **`haskell`**

![Haskell](https://img.shields.io/badge/Haskell-GHC_9.4-5E5086?style=flat-square&logo=haskell&logoColor=white)
![Sections](https://img.shields.io/badge/Sections-6-9558B2?style=flat-square)
![Purity](https://img.shields.io/badge/Code-pure_no_FFI-2EA043?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

This directory carries the **Haskell (GHC 9.4) numerical-verification
layer**: a Cabal project with one module per research section under
`SectionN_*/src/`, registered in [`cabal.project`](cabal.project). The
ports mirror the framework contract — `Text.Printf`-formatted output at
15-digit precision, per-assertion PASS/FAIL lines and the final JSON
verdict — while keeping the implementations idiomatic and short.

Section 1 defines `bCorrection = pi / (4·pi² + 2·pi·√3)` as a top-level
`Double` binding and prints it with `printf "b = %.15e"`, exactly matching
the values the other languages assert (the closed form is algebraically
identical to `1/(4π + 2√3)` = 0.06238119…); later sections exercise the
functional style on the spectral and dynamical scaffolding. GHC's purity
makes these ports particularly readable as *executable specifications* of
the claims.

## The six section ports

| Package | Directory | Section | Notes |
|---|---|---|---|
| `section1-correction-b` | [`Section1_CorrectionB/`](Section1_CorrectionB/README.md) | 1 | pure closed-form evaluation |
| `section2-preprint-nse` | [`Section2_PreprintNSE/`](Section2_PreprintNSE/README.md) | 2 | rotation chain in pure functions |
| `section3-ab-cloud` | [`Section3_ABCloud/`](Section3_ABCloud/README.md) | 3 | structural Hofstadter checks |
| `section4-kdv` | [`Section4_KdV/`](Section4_KdV/README.md) | 4 | symbolic-then-numeric conservation |
| `section5-klein-attractor` | [`Section5_KleinAttractor/`](Section5_KleinAttractor/README.md) | 5 | ergodic statistics over the reference ensemble |
| `section6-riemann-zeros` | [`Section6_RiemannZeros/`](Section6_RiemannZeros/README.md) | 6 | spacing diagnostics |

Package names use dashes (Cabal convention) while directories use
underscores — the mapping table above is the bridge. Each section folder
carries its own `src/` with the executable's `Main.hs` (and a README).

## Contents

| File | Description |
|---|---|
| [`cabal.project`](cabal.project) | registers all six section packages; keeps the resolver stable |

## How to run

```bash
cd verification/haskell
cabal update                     # once; stale indexes produce resolver noise
cabal build                      # all six packages
cabal run section1-correction-b  # one section
cabal run section4-kdv           # …any other
```

GHC 9.4 is the pinned toolchain (ghcup). CI builds the project in the
extended-languages workflow; the pinned Docker image lives at
[`docker/haskell/`](../docker/README.md).

## 🎯 What Haskell contributes

The Haskell ports are the **pure-functional witness**: the section
contracts expressed as types and pure functions, auditable end-to-end by
reading. The implementations are pure — no `unsafe`, no FFI — which makes
them the easiest full-source audit of the computational tier. Where C++
shows the contract survives performance engineering, Haskell shows it
survives paradigm distance — which is itself a theorem of the framework's
portability claim: the same assertions, written in a language with no
loops and no mutation, still produce the same numbers to 15 digits.

## 🔗 See also

- [the framework hub](../README.md) — the two-tier picture and the
  contract;
- [`rust/`](../rust/README.md) — the std-only comparison point;
- [`cpp/`](../cpp/README.md) — the BLAS-backed counterpart;
- [`tests/`](../tests/README.md) — the validator that consumes these
  ports' JSON verdicts.


## Precision and formatting, exactly

The ports print with `printf "%.15e"`-style formatting at 15 significant
digits — the same precision discipline as the C++ and Rust ports, so the
validator can diff the textual values without per-language formats. The
`Double` type is the contract; where a section needs extended precision
(the L1-class constants), that is the Python/mpmath chain's job, and the
Haskell ports assert the double-precision echo of it.

## Adding a section port in Haskell

1. `mkdir Section7_*/src` with a `Main.hs` implementing the contract
   (banner → assertions → one `JSON:` line → exit code);
2. a `.cabal` file with an executable target; register it in
   [`cabal.project`](cabal.project);
3. extend the [validator](../tests/README.md) matrix in the same commit;
4. update this README and the section's reference README — documentation
   moves with the port, atomically.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| resolver noise on build | stale cabal index | `cabal update` once |
| `cabal run section1-correction-b` not found | package not in cabal.project | check the registration line |
| output differs in the last digit | a `Double` expression reordered | match the port's expression order; the validator tolerance covers formatting, not reassociation |

---

Navigation: [verification](../README.md) · [repository root](../../README.md) · [IPL-RP-1.0](../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) — © 2026 Isaev Iskhak Khamzatovich, all rights reserved.*
