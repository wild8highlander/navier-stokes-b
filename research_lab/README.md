# `research_lab/` — the dynamical research laboratory

> **Navigation:** [repository root](../README.md) › **`research_lab`**

**Language: EN** | [RU — Русская версия](README.ru.md)

![status](https://img.shields.io/badge/CI-lab--smoke-blue?style=flat-square)
![numpy](https://img.shields.io/badge/stack-numpy%20only-9cf?style=flat-square)

---

This directory extends the repository's algebraic verifiers (sections 1–7)
with a **dynamical layer**: a dealiased 3D pseudospectral Navier–Stokes
solver on the torus, singularity diagnostics (the Beale–Kato–Majda monitor
family), and a resolution-extrapolation protocol. It exists to answer, in a
falsifiable way, the question the whole repository circles around:

> *Can the smoothness of Navier–Stokes solutions be checked "all the way to
> infinity"?*

The honest headline answer is below, in Part I. Short version: **not as a
proof, and no finite computation will ever settle the Clay question — but
three specific extrapolations (dt → 0, N → ∞, and bounded-horizon growth of
the BKM integral) are meaningful, implementable, and implemented here**, and
a laboratory built around them can genuinely falsify or support claims.

---

## Part I — What numerics can and cannot verify

### The problem, precisely

The Clay Millennium problem asks: for smooth divergence-free initial data
u₀ on ℝ³ (or the torus T³), does the 3D Navier–Stokes equation

    ∂u/∂t + (u·∇)u = −∇p + νΔu,   div u = 0

possess a unique smooth solution for all time t > 0, or does some datum
develop a singularity at finite time? A prize is offered for *either*
answer. The repository's stated program claims the first branch (global
regularity, with the b-correction mechanism as its pillar).

### Why no computation can decide it

Three obstructions are fundamental, not technical:

1. **The datum space is infinite-dimensional.** A computation tests one
   initial field (or a finite family) in one domain at one viscosity. The
   quantifier structure of the problem — *for all* u₀ — is unreachable by
   any finite enumeration. This alone is decisive.
2. **Singularities can hide.** If a blow-up exists, nothing prevents it from
   being self-similar with support shrinking faster than any fixed grid can
   track, or starting after any fixed horizon. T. Tao's 2016 blow-up for the
   *averaged* Navier–Stokes model demonstrates that the borderline is sharp
   precisely because the averaging kills the transport that protects real
   solutions — a caution against reading smooth computed evolutions as
   evidence for all data.
3. **Floating point cannot distinguish a singularity from an unresolved
   steep gradient.** Both produce large gradients at the grid scale. Only
   rigorous a-posteriori error control (interval/Taylor-model computer-
   assisted proof) turns numerics into theorems — and even that certifies
   *one solution*, not the solution map.

### What "extrapolation to infinity" honestly means here

The laboratory implements three extrapolations that **are** meaningful,
each with an explicit error bar and an explicit scope:

| Extrapolation | Protocol | What it certifies | What it does not |
|---|---|---|---|
| **dt → 0** | dt-halving ladder; observed order must recover the RK4 order 4; Richardson extrapolation of the monitor | the monitor value of the *computed solution* at dt = 0, with error bar | nothing about other data or PDE singularities |
| **N → ∞** | spectral resolution ladder; the energy at the dealiasing cutoff must stay negligible vs the spectral peak; monitor gaps across N are the spatial error bar | that the computed solution is spectrally *resolved* — a prerequisite for any claim | that the PDE solution is smooth (that is the *assumption* being tested for consistency) |
| **T growth** | BKM integral BKM(T)=∫₀ᵀ supₓ\|ω\| ds kept bounded while the horizon extends; self-similar fits Ω ~ (T−t)^(−α) reported when the tail supports one | window-limited absence of near-singularity indicators (or their presence — a falsification) | global regularity (the window is always finite) |

The Beale–Kato–Majda theorem (1984) is the bridge that makes the third
ladder scientifically meaningful: if a solution loses smoothness at time T,
then BKM(T) = ∞. So a *bounded, converged* BKM monitor over an extended
horizon is positive evidence for smoothness *of that solution on that
horizon* — and a diverging monitor with a clean self-similar fit is exactly
how the community has learned to smell candidate blow-ups (the Hou–Luo
scenario is the textbook case).

### The two scientific lines of this lab

* **Falsification line** (ABC hunt, Hou–Luo tubes): try hard to *break*
  smoothness inside the accessible window. A credible negative result —
  bounded BKM, stabilizing monitors, exponentially empty spectral tails —
  is the strongest statement numerics can make.
* **Mechanism-audit line** (b-correction stress): test the repository's own
  regularity mechanism on evolved fields. Part IV reports the first audit;
  its result is a precise, uncomfortable, and useful zero.

---

## Part II — Architecture

```
research_lab/
├── solver.py            SpectralNSE3D: dealiased pseudospectral NSE on T³,
│                        RK4 with projection at every sub-stage (div-free
│                        to roundoff along the whole run)
├── diagnostics.py       energy, enstrophy, palinstrophy, dissipation,
│                        sup|ω|, BKM running integral, shell spectra,
│                        cutoff-tail resolution monitor, divergence (Parseval)
├── initial_conditions.py  Taylor–Green, ABC, Hou–Luo-type tubes (periodic
│                        adaptation, documented difference from the slab
│                        original), deterministic random field; b-rotation
│                        transforms (pointwise / full symmetry)
├── constants.py         b = 1/(4π+2√3), θ_b = arcsin b, Rodrigues matrices
├── extrapolate.py       dt-ladder (observed order + Richardson), N-ladder
├── i18n.py              the language button (EN/RU output strings)
├── run_lab.py           CLI entry (python -m research_lab.run_lab)
├── experiments/         taylor_green · abc_blowup_hunt · hou_luo_tubes ·
│                        bcorrection_stress
└── tests/               10 fast deterministic unit tests (CI-safe, N=16)
```

**Numerical method.** Velocity form with the Leray projection; the
nonlinearity is evaluated as P[curl u × u] (the gradient part of
(u·∇)u is annihilated by the projector); 2/3 dealiasing; classical RK4.
Incompressibility is enforced to roundoff at every sub-stage — measured
max |div u| along runs is ~1e-17. Temporal order is verified, not assumed:
the dt-ladder recovers observed order 4.0 (see Part IV).

**Output contract.** Identical to the repository verifiers:
banner → per-assertion `[PASS]`/`[FAIL]` → `JSON: {...}` verdict line →
exit code. JSON keys are English always (machine contract); human-readable
text follows the language button.

**Verdict semantics (important).** `all_passed: true` means *the computation
is internally consistent* (orders recovered, incompressibility held,
resolution adequate, monitors finite). For the hunting experiments an
additional boolean `blowup_suspected` carries the scientific signal.
Both outcomes are valid results; neither is a proof.

---

## Part III — Running

```bash
pip install numpy                     # the only dependency

python -m research_lab.run_lab --list
python -m research_lab.run_lab --experiment taylor_green --preset smoke    # ~5 s
python -m research_lab.run_lab --experiment taylor_green --preset default  # ~80 s
python -m research_lab.run_lab --experiment abc_blowup_hunt --preset default
python -m research_lab.run_lab --experiment hou_luo_tubes  --preset default
python -m research_lab.run_lab --experiment bcorrection_stress --preset deep

# the language button:
python -m research_lab.run_lab --experiment taylor_green --preset smoke --lang ru
NSB_LAB_LANG=ru python -m research_lab.run_lab --experiment taylor_green --preset smoke

python -m pytest research_lab/tests -q     # the lab's own test suite
```

Presets: `smoke` (N=16, CI job `lab-smoke`, ~10 s total), `default`
(N=32, workstation), `deep` (N=64+, long runs). Every parameter can be
overridden on the command line (`--N 96 --T 5 --nu 0.005 --dt 0.001`).

CI integration: the `lab-smoke` job in `.github/workflows/ci.yml` runs all
four experiments in smoke mode (EN for three, RU for one — exercising both
languages) plus the unit tests, so the CI badge now also guarantees that
the laboratory itself stays working.

---

## Part IV — First results (v0.1.0, smoke/default presets)

| Quantity | Value | Meaning |
|---|---|---|
| max \|div u\| along runs | 1.4e-17 | incompressibility at roundoff |
| observed RK4 order (dt-ladder) | 4.03 (smoke), 3.95 (default) | temporal convergence verified, not assumed |
| Ω(t=1; dt→0), Richardson | 0.21306349 (smoke cfg) | the extrapolated monitor value with error bar |
| cutoff spectral tail (default cfg) | 8.0e-07 of peak | the run is spectrally resolved |
| full-rotation symmetry vs control | identical to 4.4e-16 | the exact symmetry is a relabeling: **changes nothing** |
| pointwise b-rotation: energy | preserved (0.0e+00 drift) | isometry — true of *any* rotation |
| pointwise b-rotation: div u | broken, \|div\| = 3.8e-2 | **not** an incompressible operation |
| effect of periodic b-kicks on sup\|ω\| | +0.99 % | **no detectable regularizing effect** |

Interpretation, stated as carefully as the measurements allow: the *full*
form u′(x) = R u(R⁻¹x) of the b-rotation is an exact symmetry of the torus
problem and therefore cannot influence the blow-up question at all — the
laboratory confirms identity of diagnostics to 16 digits. The *pointwise*
form u′(x) = R u(x), which is the form used across the repository's
verifiers, preserves energy (as any rotation does) but is not incompressible;
applied periodically to an evolving field and then reprojected, it behaves
as an uncontrolled O(1)-divergence perturbation whose net effect on the
vorticity maximum is at the 1 % level — no regularization mechanism is
detectable within the tested window. This does not disprove any claim about
the constant b itself; it does mean that, as currently formulated, the
mechanism has no dynamical content that a relabeling (or a small perturbation)
would not already have. Any stronger claim needs a modified evolution law
plus a proof — which is precisely what the roadmap's computer-assisted
branch is for.

---

## Part V — Roadmap

1. **v0.2 — deeper windows.** N=128–256 deep runs of the hunting
   experiments; ν → 0 sequences at fixed data; self-similar collapse
   fitting (Ω, palinstrophy, sup|ω| vs (T−t)) as a first-class module with
   fitted-exponent error bars.
2. **v0.3 — more dangerous data.** Kida-Pelz symmetric junctions;
   vortex-blob dipoles; stochastic initial-data families with stratified
   sampling instead of single fields (still not "all data", but
   systematic coverage of the dangerous similarity classes).
3. **v0.4 — cross-language ports.** Rust/C++ ports of the solver following
   the repository's port discipline (identical JSON verdicts), enabling
   longer horizons and independent-arithmetic cross-checks (different
   compilers/arithmetic catching different roundoff paths).
4. **v0.5 — the rigorous branch.** Computer-assisted proof skeleton:
   interval-arithmetic (Taylor models) enclosure of the self-similar
   profile equations; a-posteriori validation of computed profiles. This is
   the only route from numerics toward an actual theorem, one solution at
   a time.
5. **Continuous.** Publish negative results with the same rigor as
   positive ones; every experiment's JSON verdict is archiveable by the
   repository manifest discipline.

## Part VI — Relation to sections 1–7

Sections 1–7 verify algebraic identities and pinned constants — they are
pointwise facts, valuable and cheap. This laboratory adds the dimension
those verifiers deliberately do not touch: *dynamics*. The b-rotation
constants enter the lab through `constants.py` unchanged; the lab's
contribution is to test what those constants *do* to evolving fields, with
error bars, in both the falsification and the audit lines. The whitepaper
(`docs/whitepapers/`, RU and EN) develops the feasibility analysis of
Part I at full length with references.

## References

1. Beale, Kato, Majda (1984) — BKM blow-up criterion, Comm. Math. Phys. 94.
2. Caffarelli, Kohn, Nirenberg (1982) — partial regularity, Comm. Pure Appl. Math. 35.
3. Escauriaza, Seregin, Šverák (2003) — L∞(L³) regularity criterion, Russ. Math. Surv. 58.
4. Koch, Tataru (2001) — BMO⁻¹ small-data global regularity, Adv. Math. 157.
5. Tao (2016) — finite-time blowup for an averaged three-dimensional Navier–Stokes equation, J. AMS 29.
6. Hou, Luo (2013) — potential singularity for 3D Euler with boundary, Int. Math. Res. Notices.
7. Brachet et al. (1983) — Taylor–Green vortex at high Reynolds number, J. Méc. Théor. Appl.
8. Lilly (1966) — the Smagorinsky constant, Mon. Wea. Rev. 94 (see section 7).
9. Albritton, Brué, Colombo (2022) — non-uniqueness of Leray solutions, Ann. Math. 196.

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../LICENSE.md)).
