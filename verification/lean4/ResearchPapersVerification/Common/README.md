# 🧱 Lean 4 · Common — the Shared Foundation Module

> **Navigation:** [`verification`](../../../README.md) › [`lean4`](../../README.md) › [`ResearchPapersVerification`](../README.md) › **`Common`**

![Lean 4](https://img.shields.io/badge/Lean%204-v4.14-informational?style=flat-square&logo=leanpub&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **foundation module** of the Lean 4 library: `Foundation.lean` defines the objects every section reuses — most importantly the polarization correction `bCorrection := π / (4·π² + 2·π·√3)` together with its machine-proved bounds `bCorrection_pos : 0 < bCorrection` and `bCorrection_lt_one : bCorrection < 1`. Sections import this file instead of restating the constant, which guarantees that all six research sections reason about *the same* number.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`Foundation.lean`](Foundation.lean) | 879 B | shared definitions and base lemmas — bCorrection, bounds, common structures (~1 KB) |

## 🔗 Cross-References

- [Library root](../README.md)
- [Lean layer](../../README.md)

## 🇷🇺 Brief Summary (Russian Summary)

The shared base of the Lean library: the closed-form definition of bCorrection and the machine-proved bounds 0 < b < 1 — a single foundation for all six sections.

---

<div align="center">

**[⬆ Back to top](#-lean-4--common--the-shared-foundation-module)** · 
**[Repository root](../../../README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>
<!-- doc-enhancer:block v1 (auto-generated block; license files are not affected) -->

---

## 🧭 Navigation and Quick Links (auto)

- 🏠 [Repository root](../../../../../README.md)
- 📖 [How the claims are verified](../../../../../verification/README.md)
- 📄 [Papers (PDF)](../../../../../papers/README.md) · 📚 [Monographs](../../../../../docs/README.md) · 🧾 [LaTeX](../../../../../src/README.md)
- ⚖️ [IPL-RP-1.0 License](../../../../../LICENSE.md) — viewing, a single backup copy, and citation with attribution are permitted; everything else — only with the author's written consent.

*Block added automatically (`doc-enhancer v1`); it is unrelated to the license and does not modify it. Re-running the script does not duplicate the block.*

