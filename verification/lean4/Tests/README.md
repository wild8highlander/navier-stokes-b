# `lean4/Tests/` — the axiom-audit module

> **Navigation:** [repository root](../../../README.md) › [verification](../../README.md) › [lean4](../README.md) › **`Tests`**

![Role](https://img.shields.io/badge/Role-trust_base_audit-FF8C00?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

[`AxiomAudit.lean`](AxiomAudit.lean) prints `#print axioms` for 30 central
theorems of the core — the constant, the Rodrigues algebra, the braking
protocol, the γ_eff limits, the vortex-tube identities, the proof chain
and the Klein bridge. Allowed dependencies are only Lean/Mathlib's
standard axioms (`propext`, `Quot.sound`, `Classical.choice`,
`Lean.ofReduceBool`).

Run it with the toolchain:

```bash
cd verification/lean4 && lake env lean Tests/AxiomAudit.lean
```

or let the automation do it: `verification/tests/test_lean_core.py`
executes this file through `lake` when available and fails on any axiom
outside the allowed set; [`tools/audit/audit_lean.py`](../../tools/audit/audit_lean.py)
checks the static invariants (counts, imports, no `sorry`) without any
toolchain.

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../../../LICENSE.md)).
