# 🎩 `haskell/…/Section5_KleinAttractor/src/` — the Executable Source

> **Navigation:** [`haskell`](../../README.md) › [`Section5_KleinAttractor`](../README.md) › **`src`**

![Haskell](https://img.shields.io/badge/Haskell-GHC_9.4-5E5086?style=flat-square&logo=haskell&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **`Main.hs` of the Section 5 Haskell port** — Klein Attractor — Ergodic Dynamics and the NSE Bridge. One pure
module: it computes the section's quantities from closed forms, asserts the
properties via `printf`-formatted PASS/FAIL lines at 15-digit precision,
and emits the framework's `JSON:` verdict.

| File | Description |
|---|---|
| [`Main.hs`](Main.hs) | the executable's single module — the section contract as types and pure functions |

## Run

```bash
cd verification/haskell
cabal run section5-klein-attractor
```

No `unsafe`, no FFI — the file is readable end-to-end in one sitting, which
is the point of the Haskell witness. Peers of this port:
[Python](../../../section5_klein_attractor/README.md) · [Lean 4](../../../lean4/ResearchPapersVerification/Section5_KleinAttractor/README.md) · [Coq/Rocq](../../../coq/section5_klein_attractor/README.md) · [Isabelle-HOL](../../../isabelle/Section5_KleinAttractor/README.md) · [Agda](../../../agda/Section5_KleinAttractor/README.md) · [C++](../../../cpp/section5_klein_attractor/README.md) · [Rust](../../../rust/section5_klein_attractor/README.md).

---

---

Navigation: [section 5](../README.md) · [haskell layer](../../README.md) · [IPL-RP-1.0](../../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

