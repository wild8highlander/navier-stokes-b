# 🎩 `haskell/…/Section1_CorrectionB/src/` — the Executable Source

> **Navigation:** [`haskell`](../../README.md) › [`Section1_CorrectionB`](../README.md) › **`src`**

![Haskell](https://img.shields.io/badge/Haskell-GHC_9.4-5E5086?style=flat-square&logo=haskell&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **`Main.hs` of the Section 1 Haskell port** — Correction b — the Universal Polarization Constant. One pure
module: it computes the section's quantities from closed forms, asserts the
properties via `printf`-formatted PASS/FAIL lines at 15-digit precision,
and emits the framework's `JSON:` verdict.

| File | Description |
|---|---|
| [`Main.hs`](Main.hs) | the executable's single module — the section contract as types and pure functions |

## Run

```bash
cd verification/haskell
cabal run section1-correction-b
```

No `unsafe`, no FFI — the file is readable end-to-end in one sitting, which
is the point of the Haskell witness. Peers of this port:
[Python](../../../section1_correction_b/README.md) · [Lean 4](../../../lean4/ResearchPapersVerification/Section1_CorrectionB/README.md) · [Coq/Rocq](../../../coq/section1_correction_b/README.md) · [Isabelle-HOL](../../../isabelle/Section1_CorrectionB/README.md) · [Agda](../../../agda/Section1_CorrectionB/README.md) · [C++](../../../cpp/section1_correction_b/README.md) · [Rust](../../../rust/section1_correction_b/README.md).

---

---

Navigation: [section 1](../README.md) · [haskell layer](../../README.md) · [IPL-RP-1.0](../../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

