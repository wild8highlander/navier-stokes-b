# 🎩 `haskell/…/Section6_RiemannZeros/src/` — the Executable Source

> **Navigation:** [`haskell`](../../README.md) › [`Section6_RiemannZeros`](../README.md) › **`src`**

![Haskell](https://img.shields.io/badge/Haskell-GHC_9.4-5E5086?style=flat-square&logo=haskell&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **`Main.hs` of the Section 6 Haskell port** — Riemann Zeros — the Hilbert–Pólya Programme. One pure
module: it computes the section's quantities from closed forms, asserts the
properties via `printf`-formatted PASS/FAIL lines at 15-digit precision,
and emits the framework's `JSON:` verdict.

| File | Description |
|---|---|
| [`Main.hs`](Main.hs) | the executable's single module — the section contract as types and pure functions |

## Run

```bash
cd verification/haskell
cabal run section6-riemann-zeros
```

No `unsafe`, no FFI — the file is readable end-to-end in one sitting, which
is the point of the Haskell witness. Peers of this port:
[Python](../../../section6_riemann_zeros/README.md) · [Lean 4](../../../lean4/ResearchPapersVerification/Section6_RiemannZeros/README.md) · [Coq/Rocq](../../../coq/section6_riemann_zeros/README.md) · [Isabelle-HOL](../../../isabelle/Section6_RiemannZeros/README.md) · [Agda](../../../agda/Section6_RiemannZeros/README.md) · [C++](../../../cpp/section6_riemann_zeros/README.md) · [Rust](../../../rust/section6_riemann_zeros/README.md).

---

---

Navigation: [section 6](../README.md) · [haskell layer](../../README.md) · [IPL-RP-1.0](../../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

