# `tests/` — the pytest layer of the verification framework

> **Navigation:** [repository root](../../README.md) › [verification](../README.md) › **`tests`**

![pytest](https://img.shields.io/badge/pytest-verified-0A9EDC?style=flat-square&logo=pytest&logoColor=white)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

---

Fast, toolchain-free consistency tests that bind the three layers of the
framework together. They run in CI on every push (`pytest verification/tests/`)
and take a few seconds: no Lean build, no 3D solver, no network.

| File | What it binds |
|---|---|
| [`test_lean_core.py`](test_lean_core.py) | the Lean core's structure: all six core modules present, no `sorry`/`admit`, no project axioms, every local `import` resolves to a real file, no legacy-direction references, `totalVerifiedTheorems` in `Main.lean` equals the actual `theorem` count, and [`Tests/AxiomAudit.lean`](../lean4/Tests/AxiomAudit.lean) prints ≥ 20 axiom bases. The full `lake env lean Tests/AxiomAudit.lean` check auto-runs only when `lake` is installed, otherwise it skips honestly. |
| [`test_numerical_consistency.py`](test_numerical_consistency.py) | the numbers behind the formal statements: `b = 1/(4π+2√3)` at 50 digits (mpmath) against the pinned string, the Lean-bound window `0.062 < b < 0.063`, the KdV soliton residual `u''' − c·u' + 6·u·u'` at machine zero (analytic derivatives), the pinned Smagorinsky–Kolmogorov `C_s`, and an end-to-end run of monolith task 9 (`verify_ns_full.py --task 9`). |

## Run

```bash
python -m pytest verification/tests/ -v            # from the repository root
cd verification && make test                       # same thing via the Makefile
```

## Contract

Every test here is deterministic and side-effect-free (the monolith task
writes its run directory under `verification/results/`, which is
git-ignored). A failure means one of three things, in order of likelihood:
a formal module was edited without updating its count/audit, a pinned
string drifted from the closed form, or a numerical identity regressed.
All three are release blockers by the repository's own policy.

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../../LICENSE.md)).
