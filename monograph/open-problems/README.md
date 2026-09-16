# open-problems — 7 Base Problems + Extension Line (P1-b, P4-b, P4-c, P5-b, P5-c)

**RU.** The open-problems package of the b = 1/(4π+2√3) program. Master document: [`OPEN_PROBLEMS_7.md`](OPEN_PROBLEMS_7.md) (bilingual RU/EN). Every number comes from real runs of 2026-09-16 (scripts in `code/`, raw results in `results/` (JSON), figures in `figures/`). Provenance and honesty rules — §0 of the master document.

**EN.** The open-problems package of the b = 1/(4π+2√3) program. Master document: [`OPEN_PROBLEMS_7.md`](OPEN_PROBLEMS_7.md) (bilingual RU/EN). Every number comes from real runs of 2026-09-16 (scripts in `code/`, raw results in `results/` (JSON), figures in `figures/`). Provenance and honesty rules — §0 of the master document.

## Layout

```
open-problems/
├── OPEN_PROBLEMS_7.md          master document (RU+EN)
├── README.md                   this file
├── code/                       9 runnable scripts (fixed seeds)
├── results/                    8 JSON files — every number of the doc
├── figures/                    5 figures generated from the JSONs
└── push_open_problems.sh       Termux push script (see below)
```

## One command

```bash
python3 code/run_all.py      # runs everything, ~10 min, regenerates JSONs
python3 code/make_figures.py # regenerates the 5 figures from the JSONs
```

## Push to GitHub from Termux

```bash
bash push_open_problems.sh
```

Requirements: `git` + PAT (classic) saved once via
`git config --global credential.helper store` (login: wild8highlander).
