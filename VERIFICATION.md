# Verification & Provenance

This repository is engineered around one principle: **every claim must be checkable
without trusting the author**. This document is the hub of all verification entry
points — integrity, numerics, cross-language re-derivation, formal proofs, containers,
and continuous integration.

---

## 0. The claim inventory

| Family | Claims | Authoritative records |
|---|---|---|
| Constant b | b = 1/(4π+2√3), θ_b = arcsin(b) | `data/results/summary_numbers.json`, §1 of the root README |
| Chain L1–L5 | residuals 10⁻¹⁶–10⁻¹⁴, RK4 order 4.0008, I_BKM values | `data/results/baseline/*.json` |
| Runs P1–P6 | the headline table in the root README | `data/results/p*.json`, plots in `data/plots/` |
| Formal facts | `b_pos`, `b_lt_one`, `sin_θ_b_eq_b`, the Rodrigues algebra, `γ = b` | [`verification/lean4/`](verification/lean4/README.md) — 72 theorems, 0 `sorry`, 0 project axioms |
| Trust base | 30 axiom prints, allowed set `propext`/`Quot.sound`/`Classical.choice` | [`verification/lean4/Tests/AxiomAudit.lean`](verification/lean4/Tests/AxiomAudit.lean) |

If a number in documentation disagrees with a JSON protocol, **the JSON is
authoritative** — please open a [verification request](https://github.com/wild8highlander/navier-stokes-b/issues/new?template=verification_request.yml).

---

## 1. Integrity — sha256 manifest

`MANIFEST.json` pins the sha256 and byte size of every file in the build.

```bash
make verify-manifest          # human-readable PASS/FAIL
```

or manually:

```bash
python3 - <<'PY'
import hashlib, json, pathlib
m = json.loads(pathlib.Path("MANIFEST.json").read_text(encoding="utf-8"))
bad = 0
for rel, meta in m["files"].items():
    p = pathlib.Path(rel)
    if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != meta["sha256"]:
        print("FAIL", rel); bad += 1
print("ALL OK" if not bad else f"{bad} mismatches")
PY
```

**Regenerating the manifest** (only after *legit* content changes):

```bash
make manifest                 # rewrites MANIFEST.json in place
git add MANIFEST.json && git commit -m "data: regenerate MANIFEST.json"
```

The CI job *Manifest integrity* performs exactly this check on every push.

---

## 2. Numerics — the physics runs (P1–P6)

```bash
cd code && ./run_all.sh       # full chain; P3 ~15 min on 2 cores
python3 code/p2_grid_convergence.py   # single run
```

Each program writes a JSON protocol to `data/results/` and prints the values quoted in
the README. Compare your output keys (`F`, `Nu`, `S_min`, …) against
`data/results/summary_numbers.json`.

## 3. The L1–L5 verification chain

```bash
NSE3D_SKIP=1 python3 verification/scripts/python_levels/verify_all.py  # ~8 s
python3 verification/scripts/python_levels/verify_all.py               # ~20 min with L5
```

Expected: L1–L4 residuals 10⁻¹⁶–10⁻¹⁴; L5 emits the recorded
`data/results/baseline/l5_nse_3d_bkm.json` verdict.

## 4. Cross-language re-derivation

Two independent arithmetics recompute the same numbers from one contract —
Python (the reference chain) and Julia (stdlib-only, own FFT):

```bash
make verify-python            # the aggregate runner over every suite (~30 s)
make verify-levels            # the L1–L5 chain (from verification/)
make verify-monolith          # the 22-task monolith, CI preset (~100 s)
```

Every suite prints line-by-line `[PASS]/[FAIL]` and a final
`JSON: {...}` verdict with a non-zero exit code on any mismatch. The
suite registry and presets live in
[`verification/common/python/`](verification/common/README.md).

## 5. Formal proofs

```bash
make verify-lean              # lake build + Tests/AxiomAudit.lean (needs elan/lake)
```

The Lean 4 core (`verification/lean4/`, Mathlib v4.14.0) carries 72
theorems with zero `sorry`, zero project axioms and a fully resolving
import graph; the axiom dependencies of 30 central theorems are printed
by [`Tests/AxiomAudit.lean`](verification/lean4/Tests/AxiomAudit.lean)
and re-checked statically by
[`tools/audit/audit_lean.py`](verification/tools/audit/README.md) —
that one needs no toolchain at all.

## 6. Containers

Removed with the restructuring: the verification framework no longer
ships Docker images or service containers. CI runs the same checks on
pinned `ubuntu-24.04` runners instead (see §7), which keeps one
environment authoritative.

## 7. Continuous integration

The [CI workflow](https://github.com/wild8highlander/navier-stokes-b/actions/workflows/ci.yml)
runs on every push:

1. **Lint (ruff)** — style gate over the Python code;
2. **Tests (pytest)** — Python 3.11 + 3.12 matrix over `verification/tests/`;
3. **Verification smoke** — the aggregate runner over all suites (quick preset);
4. **Verification monolith** — `verify_ns_full.py --ci` (tasks 1–15, two-pass);
5. **Verification tree audit** — `tools/audit/verify_repo.py`, 5 evidence groups;
6. **Research lab smoke** — the four lab experiments at N = 16;
7. **Manifest integrity** — sha256 check of the whole tree.

A green badge ⇔ the tree on `main` matches its manifest and the core checks pass.

---

## 8. Provenance chain

```
wild8highlander/research-papers  (origin, 2026-09-16)
        └── navier-stokes-b      (this repository)
              ├── MANIFEST.json            sha256 of every file
              ├── CITATION.cff             citable metadata + Zenodo DOI
              ├── Zenodo 10.5281/zenodo.21825394   versioned archive
              └── GitHub Releases (tags v*)        SHA256SUMS.txt per release
```

- **Origin:** <https://github.com/wild8highlander/research-papers>
- **DOI (version):** <https://zenodo.org/records/21825394>
- **DOI (concept):** <https://doi.org/10.5281/zenodo.21825393>
- **Author:** Isaev Iskhak Khamzatovich —
  ORCID [0009-0003-7299-0701](https://orcid.org/0009-0003-7299-0701)

## 9. How to dispute a number

1. Reproduce with the entry point above and capture the full stdout.
2. Note your commit (`git rev-parse HEAD`), platform and toolchain versions.
3. Open a [verification request](https://github.com/wild8highlander/navier-stokes-b/issues/new?template=verification_request.yml)
   with the artifacts. Reproduction failures are treated as high-priority bugs.
