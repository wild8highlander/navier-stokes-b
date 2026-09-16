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
| Formal facts | `b_pos`, `b_lt_one`, `sin_θ_b_eq_b`, … | `verification/{lean4,coq,isabelle,agda}/` |
| Open gaps | 13 sorry + 12 axioms + 4 open | [`OPEN_PROBLEMS_7.md`](OPEN_PROBLEMS_7.md), [`verification/lean4/TODO_sorry.md`](verification/lean4/TODO_sorry.md) |

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
python3 verification/python_levels/verify_all.py    # ~20 min on 2 cores
```

Expected: L1–L4 residuals 10⁻¹⁶–10⁻¹⁴; L5 emits the recorded
`data/results/baseline/l5_nse_3d_bkm.json` verdict.

## 4. Cross-language re-derivation

Seven computational languages recompute the same numbers from one contract:

```bash
make verify-python            # reference implementation
make verify-extended          # C++17, Rust, Haskell + Lean/Coq builds
```

Per-section ports live in `verification/section1_correction_b/ … section6/` — each one
prints line-by-line `[PASS]/[FAIL]` and a final `JSON: {...}` verdict with a non-zero
exit code on any mismatch.

## 5. Formal proofs

```bash
make verify-lean              # lake build     (Lean 4 + Mathlib4)
make verify-coq               # coq_makefile + make
make verify-isabelle          # isabelle build
make verify-agda              # agda --compile
```

Known `sorry`/axiom inventory with the closing plan:
[`verification/lean4/TODO_sorry.md`](verification/lean4/TODO_sorry.md).

## 6. Containers

```bash
make docker-build             # all 7 toolchain images
make docker-up                # run the verification services
```

Images pin the toolchain versions, so container runs are the closest match to CI.

## 7. Continuous integration

The [CI workflow](https://github.com/wild8highlander/navier-stokes-b/actions/workflows/ci.yml)
runs on every push:

1. **Lint (ruff)** — advisory pass over the legacy research code;
2. **Tests (pytest)** — Python 3.11 + 3.12 matrix, toolchain-locked tests auto-skip;
3. **Verification smoke** — section 1 Python verification;
4. **Manifest integrity** — sha256 check of the whole tree.

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
