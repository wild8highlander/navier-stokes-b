# 🎩 `haskell/…/Section4_KdV/src/` — the Executable Source

> **Navigation:** [`haskell`](../../../verification/haskell/README.md) › [`Section4_KdV`](../README.md) › **`src`**

![Haskell](https://img.shields.io/badge/Haskell-GHC_9.4-5E5086?style=flat-square&logo=haskell&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **`Main.hs` of the Section 4 Haskell port** — KdV — Soliton Interactions under the b-Correction. One pure
module: it computes the section's quantities from closed forms, asserts the
properties via `printf`-formatted PASS/FAIL lines at 15-digit precision,
and emits the framework's `JSON:` verdict.

| File | Description |
|---|---|
| [`Main.hs`](Main.hs) | the executable's single module — the section contract as types and pure functions |

## Run

```bash
cd verification/haskell
cabal run section4-kdv
```

No `unsafe`, no FFI — the file is readable end-to-end in one sitting, which
is the point of the Haskell witness. Peers of this port:
[Python](../../../../../verification/section4_kdv/README.md) · [Lean 4](../../../../../verification/lean4/ResearchPapersVerification/Section4_KdV/README.md) · [Coq/Rocq](../../../../../verification/coq/section4_kdv/README.md) · [Isabelle-HOL](../../../../../verification/isabelle/Section4_KdV/README.md) · [Agda](../../../../../verification/agda/Section4_KdV/README.md) · [C++](../../../../../verification/cpp/section4_kdv/README.md) · [Rust](../../../../../verification/rust/section4_kdv/README.md).

---

---

Navigation: [section 4](../README.md) · [haskell layer](../../../verification/haskell/README.md) · [IPL-RP-1.0](../../../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

