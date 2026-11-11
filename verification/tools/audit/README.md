# `tools/audit/` — repository-integrity auditors

> **Navigation:** [repository root](../../README.md) › [verification](../README.md) › **`tools`** › **`audit`**

![Audit](https://img.shields.io/badge/Audit-deterministic-2EA043?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

---

Two stdlib-only Python auditors that re-derive the health of the
verification framework from the tree itself — no cached state, no trust
in documentation:

| Script | Scope | Run |
|---|---|---|
| [`audit_lean.py`](audit_lean.py) | the Lean core only: file/theorem/def counts, zero `sorry`/`admit`, zero project axioms, every `import` resolves to a real file, no legacy-direction imports | `python3 tools/audit/audit_lean.py` |
| [`verify_repo.py`](verify_repo.py) | the whole `verification/` tree in five evidence groups — structure, trust base, Lean core, the numerical chain (live `L1–L4` run), Makefile hygiene | `make verify-repo` (from `verification/`) or `python3 tools/audit/verify_repo.py` |

Both print `[PASS]`/`[FAIL]` per group, end with one machine-readable
`JSON: {…}` verdict and exit non-zero on any failure — the same output
contract as every other verifier in this framework.

`verify_repo.py` is what CI and `make verify-repo` invoke; a red group
names the exact missing file, stale count or forbidden import, so a
failure is actionable without reading the script.

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../../../LICENSE.md)).
