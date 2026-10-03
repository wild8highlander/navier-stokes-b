# NSB PHP Lab — the no-extensions edition

**`php/nsb_lab.php`** — the Navier–Stokes b-Laboratory in ~1 600 lines of
pure PHP 8. It runs on a default PHP installation with **no extensions
required** — no complex-number extension, no image libraries, no zlib
assurance (the PNG writer transparently upgrades from hand-rolled
stored-deflate blocks to `gzcompress` when `ext-zlib` happens to be
loaded). It passes the same self-test suite and reproduces the lab's
physics as every other edition, in an interpreter nobody expects to run
pseudospectral turbulence.

* **Language**: PHP ≥ 8.0 (verified on 8.3 CLI)
* **Dependencies**: none. (`ext-zlib` optional, auto-detected.)
* **Run**: `php nsb_lab.php --selftest`

---

## Table of contents

1. [Quick start](#quick-start)
2. [Why PHP for spectral fluid dynamics](#why-php)
3. [Complex arithmetic without a complex type](#complex-arithmetic)
4. [The FFT and solver core](#the-fft-and-solver-core)
5. [CLI reference](#cli-reference)
6. [The self-test](#the-self-test)
7. [Physics fidelity and documented deviations](#physics-fidelity)
8. [The writers: PNG and GIF](#the-writers)
9. [The 2-D flow runner and wave audits](#the-2-d-flow-runner)
10. [i18n and progress](#i18n-and-progress)
11. [Performance expectations](#performance-expectations)
12. [Termux notes](#termux-notes)
13. [Troubleshooting](#troubleshooting)

## Quick start

```bash
php nsb_lab.php --selftest                  # 8 checks, ≈20 s
php nsb_lab.php --quick --lang en           # TG + b-audit + reports
php nsb_lab.php --experiment tg --n 16 --t 0.5
php nsb_lab.php --flow katrina
php nsb_lab.php --roadmap                   # FFT benchmark
php nsb_lab.php --list-flows
php nsb_lab.php                             # interactive TUI (9 = язык)
```

Results land in `~/nsb_lab_results/{logs,data,plots,reports}`.

## Why PHP

Because the polyglot repository's central claim is that the physics is
portable and the self-test suite is the contract — and a PHP edition is
the sharpest possible demonstration. If the b-audit invariants
(relabeling ≈ 0, isometry ≈ 0, div-injection > 0, reprojection ≈
machine) survive *double-precision associative arrays in an
interpreter designed for templates*, the claim holds anywhere. It is
also genuinely useful: shared-hosting admins and WordPress-land
developers can run the whole laboratory with the PHP they already have.

## Complex arithmetic

PHP has no native complex type, so fields are stored as
`['re' => float[], 'im' => float[]]` pairs and every kernel is written
as explicit re/im arithmetic — the FFT butterfly, the curl `i k×`,
the projection `â − k(k·â)/|k|²`, the damping. This is verbose but
*exact*: the arithmetic order matches the Julia reference line by line,
and the self-test's naive-DFT oracle pins the conventions (unnormalised
forward, 1/N per axis inverse, bit-reversal ordering).

## The FFT and solver core

The radix-2 DIT FFT (`fft1dClear`) follows the shared design: precomputed
twiddles, bit-reversal permutation, `len`-doubling butterflies. The 3-D
transform runs the contiguous axis in `array_slice`/`array_splice`
chunks and the strided axes with gather/scatch buffers. The 3-D solver
(`rhsAll`) computes curl in spectral space, two inverse transform sets,
the physical cross product `ω×u`, the forward transform, 2/3 mask,
Leray projection and the νk² + ν₄k⁴ damping; `stepRK4All` is the
textbook four-stage loop with per-stage projection. All N³ work uses
integer-indexed flat arrays — PHP arrays are hash maps, so the
numeric-key fast path matters (packed arrays, `array_fill`,
`array_slice` are C-level).

## CLI reference

Shared grammar (root README §5) with the experiment set `tg|abc|baudit`
(the houluo/scan long-window audits live in the compiled editions;
documented deviation). Options: `--quick --suite normal|hard
--experiment --flow <id|all|list> --roadmap --selftest --list-flows
--report --n --nu --dt --t --gif --lang --out --seed --no-color --ascii
--help --version`. TUI as everywhere; item 9 switches язык/English
live.

## The self-test

Eight checks: FFT vs naive DFT (3.3e-15), 1-D round-trip (5e-16), RK4
order via the sup-proxy dt-ladder (`p = 3.947`, tolerance ±1.5 — see
§7), Leray divergence on a random field (1.9e-16), b-rotation isometry
(4.7e-15), full-symmetry relabeling (2.2e-15), PNG signature, GIF
signature. Exit code 0 only when all pass.

## Physics fidelity

The b-audit invariants are the heart of the port and they reproduce:
full-symmetry relabeling ≈ 0, pointwise-rotation isometry ≈ 1e-15,
divergence injection ≫ 0 with reprojection back to machine level, and
sup|ω| untouched by both transformations. The Taylor–Green decay,
ABC Euler conservation, the 2-D β-plane reduced models with b-kicks,
the 20-flow table with DNS feasibility and the wave audits are all
present.

**Documented deviations** (also in `../docs/PORTING.md` §3):

1. `sup|ω|` is a *component-wise maximum* of |ω_i| rather than the
   magnitude — a cheap proxy that avoids three inverse FFTs per sample
   in a slow interpreter. Effect: the RK4-order measurement through the
   proxy gives 3.947; the tolerance is widened accordingly and stated
   in the check detail.
2. The b-audit measures the five invariants on the initial ABC field
   with a single kick rather than three full decay windows (the long
   dynamics audit lives in the compiled editions).
3. `houluo`/`scan` are not wired (the parser accepts the flags and
   reports the available set).

## The writers

* **PNG** (`heatPngWritePHP`): viridis-mapped field ×6 upscale, dark
  frame, raw scanlines with filter bytes, then either `gzcompress`
  (ext-zlib present) or a hand-rolled stored-DEFLATE zlib stream
  (BFINAL/BTYPE headers, LEN/NLEN pairs, Adler-32 trailer). CRC32 is
  the built-in `crc32()`. The chunk helper prepends the length and
  appends the CRC over `tag + data`. *Porting trap immortalised*:
  `pack('N5', $W, $H, 8, 2, 0)` writes five 32-bit words — the IHDR
  must be `pack('N',$W).pack('N',$H).pack('C5',8,2,0,0,0)` (13 bytes);
  the first draft's 22-byte IHDR parsed as bitdepth=0 and no decoder
  opened the file (`../docs/PORTING.md` §4).
* **GIF** (`gifWritePHP`): GIF89a with the global 256-colour viridis
  palette, NETSCAPE loop, per-frame GCEs, and the uncompressed-LZW
  stream (Clear + literals + periodic Clear + EOI, 9-bit packing,
  ≤255-byte sub-blocks with length prefixes). Verified decodable by
  PIL and browsers.

## The 2-D flow runner

For vortex/jet flows the edition builds the analytic vorticity field
(Rankine composite with the 2% asymmetry, or the Bickley jet with
meander), transforms it with the 2-D FFT (`fft2dArr`), reconstructs
the spectral velocities from `ψ̂ = −ω̂/kp²`, applies the pointwise
b-rotation to (u, v), measures the injected RMS divergence in
spectral space, and reports the `ck_*` checks (the dynamic integration
loop is where the compiled editions shine; the PHP edition documents
the reduced scope in its verdict). Wave flows (Draupner, Tōhoku,
Qiantang) run the *full* Stokes orbital audit — cosh/sinh depth
profiles, pointwise rotation, finite-difference divergence and curl —
exactly as in every other edition.

## i18n and progress

RU/EN dictionaries mirror the shared key set (`initI18n()`); menu item
9 toggles live. The one-line progress bar: `\r`-redrawn, UTF-8
gradient bar (ASCII with `--ascii`), measured rate and ETA; non-TTY
output prints throttled 10% markers. Colours honour `NO_COLOR` and
TTY detection (`posix_isatty` with a `TERM`-based fallback).

## Performance expectations

Honesty first: this is the slowest edition by an order of magnitude —
and it still works. Reference numbers on the verification machine:
selftest ≈ 20 s; TG N=16 T=0.4 ≈ 25 s; a 64² flow build ≈ 1 s (no
integration loop); the roadmap FFT benchmark ≈ 1 GFLOP/s at N=32.
Set realistic horizons (`--t 0.3 … 0.5`, `--n 16`) and the whole lab
is usable interactively.

## Termux notes

`pkg install php` (the CLI binary includes the bundled extensions you
would expect; `ext-zlib` is typically present, and its absence is
handled). Long runs: `termux-wake-lock`. The output GIFs open directly
in the gallery; the PNG heat maps are standard files.

## Troubleshooting

* **"PNG won't open"** — ensure the IHDR fix from §8 is in place if you
  refactored the writer; diagnose with Python:
  `struct.unpack('>IIBBBBB', ihdr)` must give `(W, H, 8, 2, 0, 0, 0)`.
* **` Call to undefined function posix_isatty()`** — expected on some
  builds; the `TERM`-based fallback takes over automatically.
* **Selftest RK4 order far from 4** — your butterfly or mask placement
  changed; the sup-proxy tolerance is ±1.5, anything beyond that is a
  real bug (diff against `stepRK4All`).
* **Slow** — yes; see §11 for the honest numbers and the reduced
  horizons. For production-scale runs use the C/C++/Rust/Go editions.
