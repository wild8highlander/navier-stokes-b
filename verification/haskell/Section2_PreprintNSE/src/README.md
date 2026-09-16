# 🎩 `haskell/…/Section2_PreprintNSE/src/` — the Executable Source

> **Navigation:** [`haskell`](../../../verification/haskell/README.md) › [`Section2_PreprintNSE`](../README.md) › **`src`**

![Haskell](https://img.shields.io/badge/Haskell-GHC_9.4-5E5086?style=flat-square&logo=haskell&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **`Main.hs` of the Section 2 Haskell port** — Preprint NSE — the Regularity Argument Chain. One pure
module: it computes the section's quantities from closed forms, asserts the
properties via `printf`-formatted PASS/FAIL lines at 15-digit precision,
and emits the framework's `JSON:` verdict.

| File | Description |
|---|---|
| [`Main.hs`](Main.hs) | the executable's single module — the section contract as types and pure functions |

## Run

```bash
cd verification/haskell
cabal run section2-preprint-nse
```

No `unsafe`, no FFI — the file is readable end-to-end in one sitting, which
is the point of the Haskell witness. Peers of this port:
[Python](../../../../../verification/section2_preprint/README.md) · [Lean 4](../../../../../verification/lean4/ResearchPapersVerification/Section2_PreprintNSE/README.md) · [Coq/Rocq](../../../../../verification/coq/section2_preprint/README.md) · [Isabelle-HOL](../../../../../verification/isabelle/Section2_PreprintNSE/README.md) · [Agda](../../../../../verification/agda/Section2_PreprintNSE/README.md) · [C++](../../../../../verification/cpp/section2_preprint/README.md) · [Rust](../../../../../verification/rust/section2_preprint/README.md).

---

---

Navigation: [section 2](../README.md) · [haskell layer](../../../verification/haskell/README.md) · [IPL-RP-1.0](../../../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

