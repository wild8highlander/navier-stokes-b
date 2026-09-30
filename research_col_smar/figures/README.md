# `figures/` — Monograph Figure Editions

`ru/` and `en/` contain the Russian and English editions of the same
fourteen figures (300 dpi PNG, palette-consistent with the monograph).
Regenerate with `python3 code/python/figures.py ru|en`.

The P5-D additions are `fig13_qr_topology.png` (joint PDF of the
normalized Q-R invariants with the Vieillefosse tail: DNS 96^3 vs the
pooled Gaussian ensemble vs the pooled 64^3 DNS ensemble) and
`fig14_ensemble_ext.png` (enstrophy ensemble band for the two viscosity
levels; geometry invariants versus the Taylor-microscale Reynolds
number). Both read `results/p5d_qr_topology.json` and
`results/p5d_ensemble_dns.json`.
