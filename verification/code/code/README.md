<!-- nsb-brand:v1 -->
<p align="center">
  <img src="../../assets/brand/header_verification.svg" alt="verification matrix — cells lighting up" width="100%"/>
</p>

# `code/code/` — the constants suite and the formal drafts

> **Navigation:** [repository root](../../../README.md) › [verification](../../README.md) › [code](../README.md) › **`code`**

![Suite](https://img.shields.io/badge/exact_constants-13_checks_PASS-2EA043?style=flat-square)
![Status](https://img.shields.io/badge/drafts-openly_marked-FF8C00?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

---

A mixed layer with two kinds of content, kept apart by status labels.

**Working code (executed by `make verify-code`):**

| File | Role |
|---|---|
| [`config.py`](config.py) | the exact closed forms: `b = π/(4π² + 2π√3) = 1/(4π + 2√3)`, `β_K = 5/3`, the Klein closure `exp(b·β_K·L_min)` — every value from a form, none fitted |
| [`exact_constants.py`](exact_constants.py) | 13 checks at 50 digits (mpmath) + float64 cross-checks; writes its JSON protocol to `results/` on every run |
| [`verify_all.py`](verify_all.py) | the suite runner: exact constants + the Lean-core audit ([`tools/audit/audit_lean.py`](../../tools/audit/audit_lean.py)) with a JSON verdict |

**Formal companions and drafts (Lean/Julia, not executed by CI):**

| File | Status |
|---|---|
| [`KdV.lean`](KdV.lean) | self-contained Mathlib module on the KdV one-soliton (296 lines); the former `axiom KdV`/`sorry` stubs are removed and the removal is documented in the header |
| [`SmagorinskyKolmogorov.lean`](SmagorinskyKolmogorov.lean) | the master relation `C_s = 1/(π(3C_K/2)^{3/4})` — header states it is fully proved, no `sorry` |
| [`SlaterDiag_work_in_progress.lean`](SlaterDiag_work_in_progress.lean) | a large (2.4k lines) determinants/Slater-diagonal development with **three explicit `sorry`s** — exactly what the name says |
| [`slater_diag_batch4a_draft.lean`](slater_diag_batch4a_draft.lean) | a 132-line batch fragment, header states it was **not compiler-checked** (the original environment is gone) and gives the re-integration recipe |
| [`Main.lean`](Main.lean) | a draft entry point importing a `Verification` module that **does not exist in this tree** — kept for reference, not buildable here |
| [`smagorinsky_kolmogorov.jl`](smagorinsky_kolmogorov.jl) | the Julia recomputation of the master relation (companion of `scripts/julia_levels/l7_*.jl`) |
| [`verify_ns_full.py`](verify_ns_full.py) · [`verify_ns_full.jl`](verify_ns_full.jl) | byte-identical copies of the monolithic verifiers at the `verification/` root — provenance duplicates, see the [hub README](../../README.md) |

The draft rule of this repository: a `sorry`, an axiom or an unchecked
fragment may live only in a file whose *name or header* says so — the
auditors enforce exactly that for the formal core (`lean4/`), and this
directory follows the same policy voluntarily.

## Run

```bash
python3 verify_all.py        # exact constants (13 checks) + Lean audit → JSON verdict
python3 exact_constants.py   # the constants suite alone; JSON lands in results/
```

`results/` is generated output (git-ignored): each run overwrites its own
protocol, storing the command, the tolerances and the wall-clock time.

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../../../LICENSE.md)).
