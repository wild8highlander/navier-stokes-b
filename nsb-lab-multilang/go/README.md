# NSB Go Lab — the goroutine-parallel, stdlib-only edition

**`go/main.go`** — the Navier–Stokes b-Laboratory in ~2 000 lines of Go
with **only the standard library**. The 3-D FFT axis passes fan out to
goroutines (`sync.WaitGroup`, disjoint slice windows, no channels on the
hot path), the PNG writer uses stdlib `image/png` — the *only* edition
whose heat maps are truly DEFLATE-compressed without any hand-rolled
deflate — and the GIF89a encoder carries the uncompressed-LZW packer. It
passes the same self-test suite and reproduces the same physics
handshake numbers as every other edition.

* **Language**: Go ≥ 1.21 (`go.mod` included; no module downloads)
* **Dependencies**: none — `bufio, compress-free PNG via image/png,
  image, math, math/cmplx, sync, time, ...` all stdlib
* **Build**: `cd go && go build -o nsb_lab .` (also `go vet`-clean)

---

## Table of contents

1. [Quick start](#quick-start)
2. [The goroutine-parallel FFT](#the-goroutine-parallel-fft)
3. [Why stdlib image/png matters](#why-stdlib-png)
4. [CLI reference](#cli-reference)
5. [The self-test](#the-self-test)
6. [Physics fidelity](#physics-fidelity)
7. [The 2-D flow runner and GIF capture](#the-2-d-flow-runner)
8. [i18n and progress](#i18n-and-progress)
9. [Performance](#performance)
10. [Termux notes](#termux-notes)
11. [Troubleshooting](#troubleshooting)

## Quick start

```bash
cd go && go build -o nsb_lab .
./nsb_lab --selftest                       # 10 checks, ≈6 s
./nsb_lab --quick --lang en
./nsb_lab --experiment tg --n 32 --t 2
./nsb_lab --flow katrina --gif 1
./nsb_lab --roadmap
./nsb_lab                                  # interactive TUI
go vet ./...                               # clean
```

Results land in `~/nsb_lab_results/{logs,data,plots,reports}`.

## The goroutine-parallel FFT

The 3-D transform decomposes into three axis passes. The contiguous
axis transforms `n²` lines; `fftLinesPar` splits the line range across
`runtime.GOMAXPROCS(0)` goroutines with disjoint index windows — each
goroutine owns `buf[line*P.N : (line+1)*P.N]` slices, which are provably
disjoint, so there is no synchronisation beyond the `WaitGroup`. The
two strided axes use the **gather → parallel transform → scatter**
pattern (serial permutation into a temp buffer, parallel line
transforms, serial scatter back): two extra memory passes per strided
axis, in exchange for completely race-free parallelism with no locks
and no channels on the hot path. This is the same trade as the C++/
Rust editions; the Go version's worker windows are slices, so the
disjointness is visible in the types.

The plan caches twiddles and the bit-reversal table per size; the
butterfly loop is the textbook DIT, reading `math/cmplx` for `Exp` and
`Conj`.

## Why stdlib PNG matters

Every other CLI edition hand-rolls its PNG (stored-DEFLATE blocks +
CRC32) to keep the zero-dependency property. Go is the exception that
proves the rule: `image/png` *is* the standard library, so this
edition's heat maps are **real DEFLATE-compressed PNGs** (a 236×252
plot is ≈3.8 KB instead of ≈179 KB) while remaining dependency-free.
`heatPngWrite` builds an `image.RGBA`, plots the viridis-mapped field
nearest-neighbour ×6 into a dark frame, and lets `png.Encode` do the
compression. The result decodes everywhere by construction — and the
selftest still checks the signature, because habits die hard.

## CLI reference

Shared grammar (root README §5): `--quick --suite normal|hard
--experiment tg|abc|houluo|baudit --flow <id|all|list> --roadmap
--selftest --list-flows --report --n --nu --dt --t --cfl --gif --lang
--out --seed --no-color --ascii --help --version`. TUI as everywhere.
(Checkpoints accepted and ignored — documented deviation, same as
C++/Rust.)

## The self-test

Ten checks, ≈6 s: FFT vs naive DFT (3e-15), 1-D round-trip (2e-16), 3-D
round-trip (5e-16), RK4 order from the dt-ladder (`p = 4.125`), Leray
divergence on a random field (3.3e-16), energy non-increase, b-rotation
isometry (8e-15), full-symmetry relabeling (1.5e-15), PNG signature,
GIF signature. Go's GC needs a moment on the N=16 ladders; release
builds are recommended (`go build` produces them by default).

## Physics fidelity

Handshake numbers reproduce the reference: `sup|ω|(T=0.6) = 1.7795`,
`dλ/dt = −0.416 (R² = 1.00)`. The full experiment set, the 2-D barotropic
runner with b-kicks and GIF capture, the 20-flow table with DNS
feasibility and the wave audits are ported. One porting trap worth
highlighting (documented in `../docs/PORTING.md` §4): the time-series
struct must initialise *all* arrays with the same leading sample — the
first draft seeded only `T` and `Bkm`, and the λ-scanner panicked three
windows later with an index desync, far from the cause.

## The 2-D flow runner

The flow runner reuses one `BaroBufs` per run (spectral velocity
buffers, physical u/v/w/dxw/dyw work arrays), steps the β-plane RK4,
schedules the pointwise b-kicks every `t_adv` (measure injected RMS
divergence in spectral space, Leray-reproject, rebuild ω̂), captures 24
vorticity frames for the GIF, samples `max|u|` for the verdict checks,
and writes the final field's row profile CSV. The 20 flows carry their
documented parameters (NHC/JTWC reports, Voyager/Cassini/Juno, Reynolds
1883, Taylor 1923, Thorpe 1968, …) verbatim from the Julia reference.

## i18n and progress

RU/EN dictionaries mirror the shared key set; menu item 9 toggles live.
The one-line progress bar is `\r`-redrawn with the UTF-8 gradient bar
(ASCII with `--ascii`), measured rate and ETA; non-TTY output prints
throttled 10% markers. Colours honour `NO_COLOR` and TTY detection.

## Performance

Reference machine (8 cores): selftest ≈ 6 s; TG N=16 T=0.6 ≈ 3 s;
TG N=32 T=2 ≈ 55 s; flow run 64² ≈ 2 s. GC pressure is bounded (all
work buffers are preallocated; the per-step allocations are the small
`nl` slice in the 2-D RHS and the series appends). `--roadmap` reports
the machine's parallel GFLOP/s and the N→cost table.

## Termux notes

`pkg install golang` and the build line work on aarch64; `GOMAXPROCS`
defaults to the phone's core count and the FFT workers spread across
clusters. For long runs: `termux-wake-lock`. The static binary is
self-contained (≈3 MB) and can be moved anywhere on the device.

## Troubleshooting

* **`invalid operation: float64 * complex128`** — Go, like C++, refuses
  implicit scalar-complex multiplies; wrap the scalar
  (`complex(dt, 0) * k1[i]`). All instances in this file are patched;
  new code must follow the same rule.
* **Index panic deep in the λ-scanner** — your series arrays desynced;
  initialise every series with the same leading sample (see §7 and
  `../docs/PORTING.md` §4).
* **PNG is 179 KB, not 4 KB** — you replaced the stdlib writer with a
  stored-block writer; nothing is wrong, the stdlib path simply
  compresses better.
* **`go vet` complains about the TUI loop** — it doesn't; but if you
  refactor, keep the `reader.ReadString` error handling or EOF will
  spin the menu.
