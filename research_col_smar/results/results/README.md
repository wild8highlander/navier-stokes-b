# `research_col_smar/results/results/` — the raw laboratory records

> **Navigation:** [repository root](../../../README.md) › [research_col_smar](../../README.md) › [results](../README.md) › **`results`**

![Records](https://img.shields.io/badge/Records-162_files-2B579A?style=flat-square)
![Format](https://img.shields.io/badge/Formats-JSON_·_TXT_·_CSV-2EA043?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

---

The **raw verdict layer** of the NSB-96 laboratories: 162 timestamped
records (JSON verdicts, plain-text run logs, verdict CSVs) produced by
[`tools/`](../../tools/README.md) on 2026-09-30 … 2026-10-01. Every
number quoted in [`reports/`](../../reports/README.md) traces to one of
these files, and the `*_latest.json` / `*_latest.txt` pointers make the
"latest run of each lab" resolution deterministic for scripts.

## Naming convention

```text
<lab>_<timestamp>.json   the machine-readable verdict record of one run
<lab>_<timestamp>.txt    the verbatim console log of the same run
<lab>_verdicts_<ts>.csv  the per-test verdict table (test, value, verdict, note)
<lab>_latest.json|txt    the stable pointer to the most recent run of <lab>
```

Laboratory prefixes: `matrix112` (L1), `kdv`/`kdv_improved` (L2),
`smoke48` (L3), `main96` (L4), `dns112` (L5), `bfamily96` (L6),
`bprotocol96` (L7), `match` (L8), `extra11_gradstats` (L11),
`extra12_flux` (L12), `extra13_kdvb` (L13), `extra16_convergence` (L16),
`extra17_phiaudit` (L17), plus the packaging records
(`lab_bfamily_96.csv`, `lab_A96_trajectory.csv`, `lab_A112_trajectory.csv`)
and the Julia cross-check (`extra17_julia_crosscheck.json`).

## An example record

`main96_latest.json` (lab L4) records, among the full diagnostic table:

```json
{
  "lab": "main96",
  "grid": 96,
  "Omega_max": 1.299664,
  "I_BKM_T": 17.878641,
  "E_final": 0.122627,
  "verdicts": { "48→96 Omega_max": "WIN", "...": "..." }
}
```

— the values the monograph's chapter 15 and the
[NSB report](../../reports/NSB_LAB_REPORT.md) print verbatim.

## How the layer is verified

- the repository auditor
  ([`verification/repo_integrity/`](../../../verification/repo_integrity/README.md),
  group E) checks the presence of the key `*_latest.json` pointers and the
  extra-lab records on every run;
- the aggregate scoreboards in
  [`reports/NSB_LAB_REPORT.md`](../../reports/NSB_LAB_REPORT.md)
  (`WIN 39 · DRAW 2 · LOSS 0`) and
  [`reports/EXTRA_RESEARCH_REPORT.md`](../../reports/EXTRA_RESEARCH_REPORT.md)
  (L17 `WIN 13 · DRAW 0 · LOSS 2`) are cross-checked against the same
  records;
- the tree-level sha256 ledger is [`MANIFEST.json`](../../../MANIFEST.json).

Reproduce a record with the documented commands in
[`tools/`](../../tools/README.md) — the timestamps in the filenames are
the only thing that may (and should) differ.

## License

Part of **navier-stokes-b**, license IPL-RP-1.0 ([LICENSE.md](../../../LICENSE.md)).
