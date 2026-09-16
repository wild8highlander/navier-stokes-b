# `data/` — Results and Plots of the Executed Program

The provenance layer of the repository: everything produced by the runs in
[`code/`](../code/README.md), preserved exactly as recorded on 2026-09-16.

| Directory | Contents |
|---|---|
| [`results/`](results/README.md) | JSON run protocols P1–P6, the summary of all numbers, `baseline/` for the L1–L5 chain |
| [`plots/`](plots/README.md) | 5 publication-grade plots at 300 dpi |

## Reading order

1. [`results/summary_numbers.json`](results/summary_numbers.json) — every quoted number in one file;
2. the per-run JSON next to it (`p1_…json` … `p6_…json`) — commands, parameters, tolerances;
3. [`results/baseline/`](results/baseline/README.md) — the pinned L1–L5 verdicts.

## Contract

These files are **immutable evidence**: the documentation quotes them, the manifest
pins their sha256 ([`MANIFEST.json`](../MANIFEST.json)), and CI checks that nothing
drifts. Regenerating them is allowed only together with a re-run of `code/` and a
matching documentation update in the same change.

---
Navigation: [repository root](../README.md) · [code](../code/README.md) · [IPL-RP-1.0](../LICENSE.md)
