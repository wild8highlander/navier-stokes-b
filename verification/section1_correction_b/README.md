# 🐍 Section 1 — Correction b — the Universal Polarization Constant (Python Reference)

> **Navigation:** [`verification`](../README.md) › **`section1_correction_b`**

![Python](https://img.shields.io/badge/Python-3.10–3.12-informational?style=flat-square&logo=python&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![Section](https://img.shields.io/badge/Section-1-blue?style=flat-square)

This directory is the **Python reference implementation** of research Section 1 — the first section of the framework, covering the universal polarization correction derived from the Kirchhoff point-vortex system. Within the framework's layout it is the *numerical reference tier*: the simplest, dependency-free port that every other language port can be diffed against.

The implementation is intentionally minimal — pure standard library (`math` only), a single `verify.py` entry point, and the framework's uniform output contract: the computed quantities are printed, each expected property is asserted with a `[PASS]` line, and the run ends with the `JSON:` verdict. For Section 1 the quantities are b = π / (4·π² + 2·π·√3) ≈ 0.0785, the rotation angle θ_b = arcsin(b) ≈ 7.07°, and the stabilisation identity cos²θ_b + sin²θ_b = 1; the assertions exercise 0 < b < 1 (both bounds), sin θ_b = b, cos²θ_b + sin²θ_b = 1, and the reference interval 0.07 < b < 0.08 against the published value 0.0785.

Run it with `python3 python/verify.py` — total runtime is well under a second. The same section exists in the formal tier ([`lean4`](../lean4/README.md), [`coq`](../coq/README.md), [`isabelle`](../isabelle/README.md), [`agda`](../agda/README.md)) and in the extended computational ports ([`cpp`](../cpp/README.md), [`rust`](../rust/README.md), [`haskell`](../haskell/README.md)); CI runs them all in [`ci-cross-language.yml`](../../.github/workflows/README.md).

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`python/`](python/) | — | the Python reference port — single verify.py entry point |

## 🗂 Directory Layout

```
section1_correction_b/
├── python/   # 2 files
│   ├── README.md  (this file)
│   └── verify.py
└── README.md  (this file)
```

## ▶️ How to Run

```bash
python3 python/verify.py
```

## 🔗 Cross-References

- [Framework root](../README.md)
- [Root README — verification matrix](../README.md)

## 🇷🇺 Brief Summary (Russian Summary)

**verification/section1_correction_b/** — the Python reference of Section 1 (Correction b — the Universal Polarization Constant): pure stdlib, a single verify.py, PASS/JSON output; result — b = π / (4·π² + 2·π·√3) ≈ 0.0785, the rotation angle θ_b = arcsin(b) ≈ 7.07°, and the stabilisation identity cos²θ_b + sin²θ_b = 1.

---

<div align="center">

**[⬆ Back to top](#-section-1--correction-b--the-universal-polarization-constant-python-reference)** · 
**[Repository root](../README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>

---
## 🧪 The Port Family

| Port | Path | Command | Time |
|---|---|---|---|
| Python (reference) | `python/verify.py` | `python3 verification/section1_correction_b/python/verify.py` | < 1 s |
| Rust | `../../rust/section1_correction_b/` | `cargo run --release -p section1_correction_b` | < 1 s |
| C++ | `../../cpp/section1_correction_b/` | via the CMake project (see its README) | < 1 s |
| Haskell | `../../haskell/Section1_CorrectionB/` | `cabal run section1-correction-b` | < 1 s |
| Lean 4 | `../../lean4/ResearchPapersVerification/Section1_CorrectionB/` | `lake build && lake exe check` | min (cached s) |
| Coq | `../../coq/section1_correction_b/` | `coqc CorrectionB.v` | s |
| Isabelle | `../../isabelle/Section1_CorrectionB/` | `isabelle build -D .` | min (first) |
| Agda | `../../agda/Section1_CorrectionB/` | `agda CorrectionB.agda` | s |

## 📋 What Is Asserted

1. **b well-defined and positive** — the closed form evaluates and satisfies 0 < b;
2. **b < 1** — the twist stays within the physical range;
3. **sin θ_b = b** with θ_b = arcsin b — the trigonometric bridge;
4. **rotation sanity** — the associated Rodrigues rotation is orthogonal with det 1 (numeric echo of the formal `R_b_orthogonal`/`R_b_det_one`).

## 🔍 Sample Output

```text
$ python3 verification/section1_correction_b/python/verify.py
=== Section 1 ===
b = 0.062381194121028
PASS
```

Exit code 0 = all assertions passed. The formal counterparts of exactly these four facts are the lemmas catalogued in the root README's [formal deep dive](../../README.md#-appendix-w--formal-verification-deep-dive).

---
Section 1 is the framework's keystone: every other section references the constant it fixes. Its four assertions are the minimal complete characterisation of *b* for the framework's purposes — anything more belongs to the papers, anything less breaks the chain. When porting to a new language, Section 1 is the correct first target: fastest to write, easiest to diff, and it immediately joins the new language into the validator's matrix.

---
## 🔗 Cross-Links

Formal: [lean4 Section1](../lean4/README.md) · [coq](../coq/README.md) · [isabelle](../isabelle/README.md) · [agda](../agda/README.md) · Computational: [cpp](../cpp/README.md) · [rust](../rust/README.md) · [haskell](../haskell/README.md) · Papers: [correction-b](../../papers/correction-b/README.md) · [preprint](../../papers/preprint/README.md).

<!-- doc-enhancer:block v1 (automatic block; license files are not affected) -->

---

## 🧭 Navigation and Quick Links (auto)

- 🏠 [Repository root](../../../README.md)
- 📖 [How the claims are verified](../../../verification/README.md)
- 📄 [Papers (PDF)](../../../papers/README.md) · 📚 [Monographs](../../../docs/README.md) · 🧾 [LaTeX](../../../src/README.md)
- ⚖️ [IPL-RP-1.0 License](../../../LICENSE.md) — viewing, a single backup copy, and citation with attribution are permitted; anything else requires the author's written consent.

*This block was added automatically (`doc-enhancer v1`); it is unrelated to the license and does not modify it. Re-running the script does not duplicate the block.*

