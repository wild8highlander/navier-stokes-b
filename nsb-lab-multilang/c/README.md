# NSB C Lab — the zero-dependency C99 edition

**`nsb_lab.c`** — the complete Navier–Stokes b-Laboratory in ~2 700 lines of
C99 that compile with a single `cc` invocation and **no external libraries
whatsoever** — not even zlib or libm beyond the standard math. The FFT is
hand-written over C99 `_Complex double`, the PNG encoder implements its own
CRC32/Adler32 and stored-deflate zlib streams, the GIF89a encoder carries
the uncompressed-LZW bit packer, and the whole thing still passes the same
self-test suite as every other edition in this repository.

* **Language**: C99 (tested with gcc 14 and clang; Termux clang works)
* **Dependencies**: libc, libm. Nothing else.
* **Build**: `cc -O2 -std=c99 c/nsb_lab.c -o nsb_lab -lm`

---

## Table of contents

1. [Quick start](#quick-start)
2. [Design goals and what "zero dependencies" buys](#design-goals)
3. [Build system notes](#build-system-notes)
4. [CLI reference](#cli-reference)
5. [Memory layout and the solver core](#memory-layout)
6. [The hand-rolled PNG encoder](#the-hand-rolled-png-encoder)
7. [The GIF encoder and the LZW sub-block rule](#the-gif-encoder)
8. [Checkpoints and resume](#checkpoints-and-resume)
9. [i18n, colours, progress bar](#i18n-colours-progress)
10. [Self-test: what it proves](#self-test)
11. [Physics fidelity against Julia](#physics-fidelity)
12. [Performance](#performance)
13. [Termux notes](#termux-notes)
14. [Troubleshooting](#troubleshooting)

## Quick start

```bash
cc -O2 -std=c99 c/nsb_lab.c -o nsb_lab -lm
./nsb_lab --selftest                      # 10 checks, ≈8 s
./nsb_lab --quick --lang en               # TG + b-audit + reports
./nsb_lab --experiment tg --n 32 --t 2
./nsb_lab --flow katrina --gif 1
./nsb_lab --roadmap                       # FFT benchmark + cost table
./nsb_lab --list-flows
./nsb_lab                                 # interactive TUI (RU/EN, 9 = toggle)
```

Results land in `~/nsb_lab_results/{logs,data,plots,reports}`.

## Design goals

1. **One file, one command build.** A numerical lab that a student can
   compile on whatever machine they touch — including Android/Termux,
   hobby SBCs and locked-down cluster nodes — without a package manager.
2. **No heap surprises.** All work buffers (`Work3D`: spectral states,
   RK4 stages, scratch triples, transform plans) are allocated once at
   startup and reused; the RHS is allocation-free. Sizes are `size_t`
   throughout; N³ indexing is centralised in `IDX3`.
3. **Same physics as Julia.** Every constant, every index map, every
   tolerance comes from the reference. The cross-language handshake
   (Taylor–Green `sup|ω|(0.6) = 1.7795`) reproduces to ≈1e-12.
4. **Readability over cleverness.** The FFT is the textbook iterative
   DIT loop; the solvers read like the equations. The one non-obvious
   area — the deflate/GIF bit packers — is commented line by line.

## Build system notes

The file is strict C99 with two pragmatics: `_POSIX_C_SOURCE` for
`sysconf`/`isatty`/`localtime_r`, and C99 `_Complex` for the spectral
arithmetic (complex multiplication, `conj`, `cabs` come from
`<complex.h>`; the compiler lowers them to plain float ops).

* **gcc**: `cc -O2 -std=c99 -Wall c/nsb_lab.c -o nsb_lab -lm`
* **clang**: identical.
* **tcc**: works (`tcc -run c/nsb_lab.c --version`) for quick probes.
* **MSVC**: not supported (no `_Complex`); use the C++ edition with
  `/std:c++17` if you are on Windows/MSVC — same feature set.
* Warning hygiene: builds clean at `-Wall`; the remaining warnings under
  `-Wextra` are the deliberate `if (x<0) x=0; if (x>1) x=1;` clamp style.

## CLI reference

The shared grammar (root README §5) minus `--fft` (the C edition has only
the in-house backend): `--quick --suite normal|hard --experiment
tg|abc|houluo|baudit --flow <id|all|list> --roadmap --selftest
--list-flows --report --n --nu --nu4 --dt --t --cfl --ckpt --gif --lang
--out --seed --no-color --ascii --help --version`. Interactive TUI when
launched without arguments: menu items 1–8, item 9 toggles RU/EN live,
item 0 exits with the uptime summary.

## Memory layout

All 3-D fields are flat `double complex` arrays of size N³ in row-major
order `(i·N + j)·N + k`; the wavenumber triples `kx/ky/kz`, the squared
moduli `ksq/ksq2`, the safe divisor `k2safe` and the 2/3 `mask` are
materialised once in `nse3d_init`. The operator (`rhs3`) walks index
`i` over all N³ points with pure pointer arithmetic — no per-point
function calls. The RK4 stages `K1..K4, T1, T2, T3` live in `Work3D` and
are allocated once; `ifft_field3`/`fft_field3` use the dedicated `nlhat`
scratch (never touching the stage arrays — the bug class that the C++
edition's first draft hit, documented in `../docs/PORTING.md` §4).

The 2-D barotropic solver follows the same pattern with its own buffer
struct; the flow runner reuses it across the 20 flows.

## The hand-rolled PNG encoder

PNG requires a zlib stream; zlib requires DEFLATE. The edition emits
**stored (uncompressed) DEFLATE blocks**: `BFINAL/BTYPE=00` header bytes,
LEN/NLEN little-endian pairs, raw bytes, and the Adler-32 trailer — a
~40-line zlib stream with zero dependencies, decodable by every PNG
consumer (verified: Python `zlib.decompress`, PIL, Chrome, `pngcheck`).
The trade-off is file size (a 236×252 plot ≈ 178 KB raw → the stored
stream is ≈ 179 KB where a real deflate would give ≈ 2 KB). For heat
maps that is fine; if you want compressed output without losing the
zero-dependency property, the fixed-Huffman encoder from the Julia
edition ports in ≈ 150 lines.

Chunking, CRC32 (the standard reflected table), and the signature are
shared helpers; `heat_png_write` maps a field through the shared 17-stop
viridis table, upscales ×6, frames it, and writes the chunks.

## The GIF encoder

`c_gif_write` produces GIF89a with a global 256-colour viridis palette,
a NETSCAPE looping extension, per-frame Graphic Control Extensions, and
the **uncompressed-LZW** stream: only literal codes 0–255 are emitted,
with a Clear code (256) injected every ≤253 literals so the LZW code
space never grows past the 9-bit window, terminated by EOI (257). The
bit packer is the subtle part and is worth reading:

* codes are 9-bit, packed little-endian into a byte buffer
  (`cur |= code << nb; nb += 9; while (nb >= 8) emit byte`);
* the byte stream is then split into **sub-blocks of ≤255 bytes, each
  prefixed by its length byte**, terminated by `0x00` — omit this layer
  and every decoder (PIL, Chrome, ImageMagick) rejects the file. The
  first draft of the Python edition made exactly this mistake; the rule
  is memorialised in `../docs/PORTING.md` §4.

Verified decodable by PIL (frame count, per-frame extrema) and browsers.

## Checkpoints and resume

`--ckpt N` writes a binary checkpoint every N steps
(`data/ckpt_<label>.bin`): magic `NSBC`, label, step, model time, N, the
three û arrays, and the full time series. `--resume` reloads a matching
checkpoint (label + N verified) and continues the loop with the sampled
history intact — the BKM integral and λ-scanner therefore continue
correctly instead of restarting. On successful completion the checkpoint
is deleted. This is the *full* checkpoint implementation that the C++/
Rust/Go editions stub out (documented deviation; the adaptive-CFL
machinery it protects is ported everywhere).

## i18n, colours, progress

The RU/EN dictionary is a static table (`I18N[]`) scanned by `L(key)`;
menu item 9 toggles live. Colours honour `NO_COLOR`, `TERM=dumb` and
TTY detection. The progress bar is the shared one-line design: `\r`
redraw, UTF-8 gradient `█░` (ASCII `#-` with `--ascii`), `step n/N`,
measured rate, monotonic-clock ETA; non-TTY output degrades to throttled
10% markers without a duplicate 100%.

## Self-test

`--selftest` (10 checks): FFT vs naive DFT, 1-D round-trip, 3-D
round-trip, RK4 order (ladder on TG, `p = 4.125` typical), Leray
divergence on a random field, energy non-increase, b-rotation isometry,
full-symmetry relabeling (enstrophy match — the test that catches
off-by-one index maps), PNG signature, GIF signature. Reference values
from the verification run:

```text
  ПРОЙДЕНО: FFT vs naive DFT      (3.28e-15)
  ПРОЙДЕНО: FFT roundtrip 3D      (2.00e-16)
  ПРОЙДЕНО: RK4 order 4           (p = 4.125)
  ПРОЙДЕНО: Leray div-free        (1.35e-16)
  ПРОЙДЕНО: b-rotation isometry   (1.76e-15)
  САМОТЕСТ: ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ
```

## Physics fidelity

The TG handshake numbers match Julia/Python/Rust/Go to ≈1e-12:
`sup|ω|(T=0.6) = 1.7795`, `dλ/dt = −0.416 (R² = 1.00)`. The full b-audit
(three decay windows with scheduled kicks) is ported; the 20-flow table,
cards, DNS feasibility, the reduced β-plane runs with b-kicks and GIF
frames, and the wave audits are all present. The only documented subset:
the final 3-D mid-plane terminal image is computed but the rasterised
line-plot writer of the Julia edition is reduced to the heat-map path
(CSV/JSON carry the same data; see `../docs/PORTING.md` §3.6).

## Performance

Single-threaded by design (purity over speed; the C++/Rust/Go editions
carry the parallel-FFT flag). Reference numbers on the verification
machine: 3-D FFT at N=32 ≈ 0.9 GFLOP/s; TG N=16 T=0.6 ≈ 4 s; TG N=32
T=2 ≈ 90 s; a full 64² flow run ≈ 3 s; the selftest ≈ 8 s. `--roadmap`
prints the machine-specific extrapolation table.

## Termux notes

`pkg install clang binutils` and the build line above just work (clang
with lld on aarch64 handles `_Complex` fine). For long runs add
`termux-wake-lock`. The binary is ≈ 100 KB static-ish; the results tree
lands in the Termux home as usual. If you want a smaller footprint, the
`--quick` path avoids the GIF encoder entirely with `--gif 0`.

## Troubleshooting

* **`undefined reference to cexp`** — you dropped `-lm`; the math library
  is required for the twiddles.
* **Checkpoint not found on `--resume`** — labels must match exactly
  (`TG N=32` vs `TG N=32 `); the runner prints the path it looks for.
* **GIF "unsupported" in some old viewer** — ensure your pipeline didn't
  strip the NETSCAPE block; all modern browsers/decoders are verified.
* **Non-ASCII verdicts garbled over serial console** — `--lang en` or
  `--ascii`; the UTF-8 glyphs need a UTF-8 locale.
