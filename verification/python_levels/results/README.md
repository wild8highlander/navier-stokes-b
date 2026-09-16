# `verification/python_levels/results/` — Recorded Outputs of the L1–L5 Chain

Reference outputs of the Python verification chain
([`../README.md`](../README.md), entry point `verify_all.py`), recorded on
2026-09-16 and mirrored at [`data/results/baseline/`](../../data/results/baseline/README.md).

| File | Level | Content |
|---|---|---|
| `l1_exact_constants.json` | L1 | exact constants: b, θ_b, cos θ_b |
| `l2_rotation_algebra.json` | L2 | Rodrigues rotation identities |
| `l3_kirchhoff_vortices.json` | L3 | Kirchhoff vortex system → b |

These copies exist so that each verification level is self-contained: a reader who
runs a single level can diff their output against the recorded verdict without
touching the data tree. The authoritative copies live in `data/results/baseline/` and
are pinned by [`MANIFEST.json`](../../MANIFEST.json).

---
Navigation: [python_levels](../README.md) · [baseline (authoritative)](../../data/results/baseline/README.md) · [IPL-RP-1.0](../../LICENSE.md)
