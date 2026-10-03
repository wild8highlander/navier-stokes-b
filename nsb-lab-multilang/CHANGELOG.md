# Changelog

All notable changes to the NSB Lab polyglot repository are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/1.1.0/) and
the project adheres to semantic versioning.

## [2.1.0] — 2026-10-03 — the polyglot edition

The self-contained Julia lab (v2.0.1 reference) is ported, verified and
packaged into a GitHub-ready repository with eight editions.

### Added
- **Seven new editions** of the same laboratory: Python (numpy-vectorised
  in-house FFT), C99, C++17 (std::thread-parallel FFT), Rust (pure std,
  scope-parallel FFT, no unsafe in the physics), Go (goroutine FFT, stdlib
  image/png), PHP 8 (no extensions), and a single-file Web app
  (Web-Worker pseudospectral solver, viridis canvas, CSV/JSON/PNG export).
- **Web app**: two tabs (Laboratory / About), 2-D β-plane real-time
  turbulence and a 3-D Taylor–Green mini-run with a one-line HTML progress
  bar; **six UI languages** (ru/en/es/de/fr/zh) with auto-detection.
- **One-line progress bar** in every edition: single `\r` redraw, measured
  ETA and rate, UTF-8 gradient blocks with ASCII fallback (`--ascii` /
  `NSB_ASCII=1`), and throttled 10% markers in non-TTY logs.
- **`--selftest` flag** in every CLI edition (FFT vs naive DFT, round-trips,
  measured RK4 order, Leray machine-level divergence, isometry/relabeling
  audit, writer signatures).
- **`--list-flows` flag** printing the 20-flow summary table.
- GitHub Actions CI building and self-testing all CLI editions, plus a
  physics job asserting the Taylor–Green verdict JSON.
- Root `Makefile` (`all`, `smoke`, per-edition targets, `clean`).
- `scripts/build_all.sh` and `scripts/termux_setup_and_push.sh` — the
  one-shot Termux toolchain installer + GitHub push helper.
- Encyclopedia-grade English README for every edition (3000+ words each)
  plus shared `docs/` (PHYSICS, PORTING, I18N).

### Changed
- Julia reference updated **2.0.1 → 2.1.0** (documented, surgical changes):
  ASCII progress-bar fallback, `--selftest`/`--list-flows` CLI actions,
  batch-mode progress de-duplication. Physics untouched.

### Verified
- Cross-language agreement: TG N=16 ν=0.02 T=0.6 gives sup|ω| = 1.7795 and
  dλ/dt = −0.416 (R² = 1.00) in Python, C, C++, Rust, Go and PHP.
- Self-tests: Python 12/12, C 10/10, C++ 10/10, Rust 10/10, Go 10/10,
  PHP 8/8, Julia --selftest PASS (real Julia 1.10.9 run).
- Web app: headless-Chromium run of both modes, 6-language switching,
  PNG/CSV/JSON exports.

## [2.0.1] — upstream
The original self-contained Julia lab (`julia/nsb_lab_standalone.jl`):
in-house FFT, 3-D pseudospectral NS/Euler, 2-D β-plane, BKM diagnostics,
20 real flows, own PNG/PDF/GIF, RU/EN TUI, checkpoints, adaptive CFL, K41.
