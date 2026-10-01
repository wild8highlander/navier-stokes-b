# `research_col_smar/tools/` — the NSB-96 laboratory suite

> **Navigation:** [repository root](../../README.md) › [research_col_smar](../README.md) › **`tools`**

![Labs](https://img.shields.io/badge/Labs-L1%E2%80%93L17-2B579A?style=flat-square)
![Languages](https://img.shields.io/badge/Python_·_Julia_·_C%2B%2B-9558B2?style=flat-square)
![Determinism](https://img.shields.io/badge/Runs-seeded_·_checkpointed-2EA043?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

---

The executable layer of the **NSB-96-UPGRADE** package: two
single-file laboratories (plus their language twins and a launcher) that
generate every number, verdict and report quoted in
[`reports/`](../reports/README.md) and pinned in
[`results/`](../results/README.md). Everything is deterministic — fixed
seeds, checkpointed and bit-resumable runs — and everything runs from the
repository root on a laptop or an Android phone (Termux).

## The tools

| File | What it is |
|---|---|
| `nsb_lab.py` | the main laboratory (**L1–L10**): one interactive file with the matrix battery, the KdV complex, the 48³/96³/112³ DNS protocols, the b-family, the b-protocol, the match scoreboard, the figure factory and the report generator. EN/RU interface (`--lang en`), CLI or menu driven, `--config`/`--yes` for unattended runs |
| `nsb_lab.jl` | the Julia twin of the main laboratory (cross-language reproduction) |
| `nsb_lab.cpp` | the C++ twin (single-file, no dependencies beyond the standard library) |
| `nsb_lab.sh` | the universal launcher: picks Python → Julia → C++ depending on what is installed; `--run all`, `--lang julia`, `--help` |
| `nsb_extra_research.py` | the extension laboratory (**L11–L17**): gradient statistics and intermittency, spectral flux, the hyperdissipative KdV family, the self-convergence scans, and the φ-monograph audit |
| `nsb_extra_research.jl` | the Julia twin of the extension lab (the L17 cross-check runs 24/24 PASS, drift `1.9×10⁻¹⁴`) |
| `Makefile` | `make lab`, `make extra`, `make all` shortcuts for the suite |

## The laboratory map

| Lab | Command (`--run …`) | What it establishes | Scoreboard |
|---|---|---|---|
| L1 `matrix` | `matrix` | block-diagonal orthogonality of the b-rotation (112×112), Leray idempotence, KdV unitarity, NSE contraction, FFT round-trip, Parseval, TG divergence-free IC | WIN 8 · 0 · 0 |
| L2 `kdv` | `kdv` | the improved KdV complex: IFRK4 + 2/3-dealiasing, three b-mechanisms, Hirota benchmark, spectral convergence | WIN 7 · 1 · 0 |
| L3 `smoke` | `smoke` | 48³ energy/enstrophy balances of the IFK-RK2 solver | WIN 2 · 0 · 0 |
| L4 `main96` | `main96` | **the headline protocol at 96³**: P5 regularity quantities vs the 48³ record | WIN 8 · 1 · 0 |
| L5 `dns112` | `dns112` | 112³ DNS balances and the early-time match to 96³ | WIN 3 · 0 · 0 |
| L6 `bfamily` | `bfamily` | the hyperdissipative b-family at 96³ (5/4, 3/2, 2): `k_max/η_b` doubling, universal-peak collapse | WIN 6 · 0 · 0 |
| L7 `bprotocol` | `bprotocol` | the b-rotation isometry protocol at 96³ (run B vs run A) | WIN 2 · 0 · 0 |
| L8 `match` | `match` | the cross-configuration match: A vs B (isometry), H2 (resolved margin), U32 (balance parity) | WIN 3 · 0 · 0 |
| L9 `figures` | `figures` | the 600 dpi figure set (RU + EN editions) | — |
| L10 `report` | `report` | the aggregate reports (MD / TXT / JSON / CSV) | WIN 39 · 2 · 0 total |
| L11–L17 | `nsb_extra_research.py --run all` | gradient statistics, flux cascade, hyper-KdV, self-convergence, φ-audit | 28 WIN · 5 DRAW · 2 LOSS |

## Run

```bash
# from the repository root
python3 research_col_smar/tools/nsb_lab.py --run all        # the main suite
python3 research_col_smar/tools/nsb_lab.py --lang en        # English interface
python3 research_col_smar/tools/nsb_extra_research.py --run all   # L11–L17
bash research_col_smar/tools/nsb_lab.sh --run all           # language auto-pick
julia research_col_smar/tools/nsb_extra_research.jl phi17   # the Julia φ-cross-check
```

Dependencies: `numpy` (mandatory), `matplotlib` (figures only). Wall
clock: the full main suite ~10 min on two cores; the φ-audit ~3 s; the
extension labs ~10 min combined.

## Outputs

| Destination | Content |
|---|---|
| [`results/results/`](results/results/README.md) | per-run JSON records + verdict CSVs (`*_latest.json` / `*_latest.txt` pointers) |
| [`reports/`](../reports/README.md) | the human-readable aggregate reports |
| [`../reference/`](../reference/README.md) | the heavy pinned states and curves |

## License

Part of **navier-stokes-b**, license IPL-RP-1.0 ([LICENSE.md](../../LICENSE.md)).
