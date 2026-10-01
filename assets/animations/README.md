# `assets/animations/` — the physics animation set

> **Navigation:** [repository root](../README.md) › [assets](../README.md) › **`animations`**

![Count](https://img.shields.io/badge/Animations-4_GIF-2EA043?style=flat-square)
![Renders](https://img.shields.io/badge/GitHub-native--rendering-2B579A?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

---

GitHub renders GIF files natively in Markdown, so this directory is the
repository's **moving-figure layer**: four animations, each produced by a
real solver or an exact solution, embedded in the root README so that the
physics can be *watched*, not just asserted.

| Animation | What you see | How it is produced |
|---|---|---|
| [`anim_b_rotation.gif`](anim_b_rotation.gif) | a vector field on a shell rotated **stepwise by `θ_b` = 3.5765013°** about the vortex axis `ω̂`; the cumulative angle counter climbs one θ_b per frame while `‖u′‖ = ‖u‖` holds at every step — the energy-neutrality statement made visible | the exact Rodrigues form, 40 steps, deterministic seed 20260916 |
| [`anim_kdv_collision.gif`](anim_kdv_collision.gif) | the **exact Hirota two-soliton collision** of the KdV equation: the tall and the shallow soliton approach, pass through each other, and separate with unchanged shapes — the §16.29 benchmark in one loop | the closed-form Hirota solution `u = 2 ∂²ₓ ln F`, 96 frames |
| [`anim_taylor_green.gif`](anim_taylor_green.gif) | the **2D Taylor–Green decay** — the symmetric vortex lattice of the L4/L5 protocols dissolving under viscosity, colored by vorticity, with live `t` and `E` readouts | a real pseudo-spectral solver (N = 96, ν = 10⁻³, RK2, 2/3-dealiasing, Leray projection) |
| [`anim_spectrum_cascade.gif`](anim_spectrum_cascade.gif) | the **angle-averaged spectrum `E(k, t)`** of the same run: the energy migrating downscale, the spectral slopes emerging against the k⁻⁵/³ and k⁻³ reference lines | the shell spectrum of the same solver's frames |

## Relation to the pinned protocols

The animations are *illustrative physics*, computed with the same
numerical ideas as the pinned protocols (pseudo-spectral discretization,
2/3 dealiasing, Leray projection) but at visual-grade parameters — they
are not the protocols themselves, and the repository is careful about the
distinction: the auditable numbers live in
[`data/results/`](../../data/results/README.md) and
[`research_col_smar/results/`](../../research_col_smar/results/README.md);
these GIFs exist so a reader can *see* the mechanisms those numbers
describe.

## Technical notes

- Format: GIF 8 fps-ish (`PillowWriter`), sizes 0.3–1.6 MB, loop forever.
- Deterministic: fixed seeds, no random palettes — a regeneration run
  reproduces the files.
- The static companion set is [`assets/figures/`](../figures/README.md).

## License

Part of **navier-stokes-b**, license IPL-RP-1.0 ([LICENSE.md](../../LICENSE.md)).
