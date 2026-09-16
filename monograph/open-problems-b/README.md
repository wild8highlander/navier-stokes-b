# open-problems — the open-problems program of b-mechanics (NSE / microphysics / protocols)

**Repository:** `wild8highlander/navier-stokes-b` · **Branch:** `main`
**Constant:** b = 1/(4π+2√3) = 0.06238119412102822754633967163940208118699…
**Angle:** θ_b = arcsin(b) = 3.5765013142837216°
**Base chain status:** L1–L5 — PASS (see `../verification/`, recorded runs:
L4 — the b-rotation identities with residuals 7.1e-14 … 1.2e-16; L5 — the 3D Taylor–Green BKM run,
I_BKM = 9.3560 (NSE) / 9.6758 (b-rotation), factor 0.96695).

---

## What lives here

| File | Purpose |
|---|---|
| `OPEN_PROBLEMS_EXT_B.md` | **Master document**: the full protocol, mathematics, criteria, and the results of P5-b and P4-b |
| `p5b_b_protocol_duplex.py` | P5-b: the b-protocol over a duplex link — exact Weyl–Dirichlet sums + Monte Carlo BER |
| `p4b_ensemble_T8.py` | P4-b: the T=8 ensemble at Re=2000 — kinematic simulation + paired check of the b-rotation |
| `results_p5b.json` | P5-b results (a real run, timestamped) |
| `results_p4b.json` | P4-b results — the main run (real, timestamped) |
| `results_p4b_fine.json` | The P4-b fine chain: 8 seeds at dt=0.002 (ensemble convergence K3) |
| `fig_p5b_sync.png` | Weyl–Dirichlet sums + autocorrelation of the b-chirp |
| `fig_p5b_duplex.png` | Duplex: BER and goodput |
| `fig_p4b_ensemble.png` | The T=8 ensemble: σ_y, b-invariance, 1/√T convergence |
| `push_open_problems.sh` | Publishing this folder to GitHub (Termux/POSIX) |

## How to reproduce

```bash
python3 open-problems/p5b_b_protocol_duplex.py     # ~1 s
python3 open-problems/p4b_ensemble_T8.py           # ~6–10 min, 2 cores
```

Each script prints the protocol, checks the registered success criteria,
and rewrites its own JSON + figures. All numbers in the documents come
from these runs — there are no hand-entered values.

## How to publish

```bash
bash open-problems/push_open_problems.sh
```

## Problem line-up

- **P1** — the 3D microphysics run (priority #1 of the line-up; a separate package)
- **P4** → **P4-b** — ensemble averaging of σ_y at Re=2000: T≥2 → **T=8**
  with a paired check of invariance under the exact b-rotation ✅ done
- **P5** → **P5-b** — the b-communication protocol: one direction → **full duplex**
  mode with decoupled directions and pilotless phase synchronization ✅ done
- Next: P6 (the next-level program) — see `OPEN_PROBLEMS_EXT_B.md`, Section 5.
