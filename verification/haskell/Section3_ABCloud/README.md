# `Section3_ABCloud` — AB-Cloud — the Hofstadter Hamiltonian (Haskell)

> **Navigation:** [repository root](../../README.md) › [verification](../../verification/README.md) › [haskell](../README.md) › **section 3**

![Section](https://img.shields.io/badge/S3-2B579A?style=flat-square) ![Language](https://img.shields.io/badge/Haskell_·_GHC_9.4-5e5075-informational?style=flat-square) ![Contract](https://img.shields.io/badge/PASS_%2B_JSON-FF8C00?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

**What this port recomputes:** Hermiticity and trace zero of the flux-lattice Hamiltonian, the butterfly slice identities `Σ E_j = −2`, `Σ E_j² = 2q − 4`, and the framework-constant cross-link.

The claims are *defined* by the Python reference port
([`verification/section3_ab_cloud/python/verify.py`](../../verification/section3_ab_cloud/python/README.md));
this Haskell binary must reproduce the same verdict — same
assertions, same tolerances, different arithmetic and toolchain. Any
disagreement is a CI failure by construction.

## How to build & run

```bash
cd verification/haskell && cabal build all

cabal run verify_section3_ab_cloud
```

## Files

| File | Role |
|---|---|
| `Main.hs` | the Haskell port of section 3 |
| `src/README.md` | notes on the source module |
| `Cargo.toml` / `.cabal` | the build manifest |

Every port follows the repository-wide output contract: banner → compute
from the closed forms (no data files) → one `[PASS]`/`[FAIL]` line per
assertion with the measured residual → exactly one `JSON: {"section": N,
"language": "...", "values": {...}, "all_passed": bool}` verdict line →
exit `0` only if everything passed. The cross-language validator in
[`verification/tests/`](../tests/README.md) (or
[`../..`](../tests/README.md) from nested directories) fails CI on any
disagreement between ports.

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../../LICENSE.md)).
