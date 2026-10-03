# NSB Rust Lab — the safe-systems edition (zero crates)

**`rust/src/main.rs`** — the Navier–Stokes b-Laboratory in ~2 800 lines of
Rust with **zero external crates**: pure `std`. The FFT axis passes are
parallelised with `std::thread::scope`, the complex arithmetic is a
19-line `Cx` struct with the full operator set, and the *physics code
contains no `unsafe` blocks at all* — the compiler, not the tester,
proves the absence of data races and UB. It passes the same self-test
suite and reproduces the same physics handshake numbers as every other
edition.

* **Language**: Rust (edition 2021, stable ≥ 1.70; `IsTerminal` needs 1.70)
* **Dependencies**: none. `Cargo.toml` has an empty `[dependencies]`
  section — the build works fully offline.
* **Build**: `cargo build --release` (or `rustc -O src/main.rs`)

---

## Table of contents

1. [Quick start](#quick-start)
2. [Why this edition matters: safety as a physics invariant](#why-safety)
3. [The `Cx` complex type](#the-cx-complex-type)
4. [The scope-parallel FFT](#the-scope-parallel-fft)
5. [Borrow-checker-driven design decisions](#borrow-checker-design)
6. [The deterministic RNG](#the-deterministic-rng)
7. [CLI reference](#cli-reference)
8. [The self-test](#the-self-test)
9. [Physics fidelity](#physics-fidelity)
10. [The writers](#the-writers)
11. [Performance](#performance)
12. [Termux notes](#termux-notes)
13. [Troubleshooting for Rust newcomers](#troubleshooting)

## Quick start

```bash
cargo run --release --manifest-path rust/Cargo.toml -- --selftest
cargo run --release --manifest-path rust/Cargo.toml -- --quick --lang en
cargo run --release --manifest-path rust/Cargo.toml -- --flow katrina --gif 1
cargo run --release --manifest-path rust/Cargo.toml -- --roadmap
cargo run --release --manifest-path rust/Cargo.toml      # TUI
# or without cargo:
rustc -O rust/src/main.rs -o nsb_rs && ./nsb_rs --selftest
```

Results land in `~/nsb_lab_results/{logs,data,plots,reports}` as in every
edition.

## Why safety

Numerical codes are a notorious `unsafe`-adjacent genre: raw index
arithmetic into big buffers, hand-rolled parallel transforms, `memcpy`
orchestras. This edition demonstrates that *none of it is necessary*:
every index access is bounds-checked (and branch-predicted away in
release mode — the physics numbers are identical to the C edition's to
≈1e-12), the parallel FFT shares data through scoped borrows that the
compiler verifies as disjoint, and the whole file has exactly two
`unsafe` blocks, both confined to the config/session *globals* at the
top (`static mut` accessors) — the physics functions below them are
safe Rust. The payoff is the strongest debugging statement a numerical
repo can make: **if it compiles, the transform parallelism has no data
races**, and the self-test only has to verify the *mathematics*.

## The `Cx` complex type

`std` has no complex numbers, so the file defines `Cx { re: f64, im:
f64 }` with `Add/AddAssign/Sub/SubAssign/Mul/MulAssign/Neg`, `scale`,
`conj`, `norm2`, `abs`, and the two float-multiplication impls
(`Cx * f64`, `f64 * Cx`) that keep the solver expressions close to the
Julia originals (`d += kx as f64 * inp[0][i]`). The multiplication
implements `(a+bi)(c+di)` directly; there is no FMA trickery — fidelity
over speed, matching the reference's arithmetic order.

## The scope-parallel FFT

The design is **gather → parallel transform → scatter**:

1. the contiguous axis (k) transforms in place: the flat buffer is
   chunked into disjoint `&mut [[Cx; n]]` slices via
   `split_at_mut` in a loop, each worker owns one chunk;
2. each strided axis (j, i) first serially gathers its lines into a
   contiguous temp `Vec<Cx>` (line = (i,k) or (j,k) minor order), runs
   the same parallel line-transformer, and scatters back;
3. workers are spawned with `std::thread::scope` so all borrows are
   compile-time-verified disjoint; the worker count is
   `std::thread::available_parallelism()`.

The extra two full-array passes per strided axis cost ≈10–15% at
N ≥ 64 and buy lock-free, race-free parallelism with no `unsafe`
anywhere. This is the same trade documented for the C++ edition; the
Rust version additionally proves it with the type system.

## Borrow-checker-driven design

The Julia pattern `rhs!(du, uhat, s, W)` — output and work-struct
borrowing the same object — is illegal in safe Rust when `du` is a
field of `W`. The port resolves it structurally (see
`../docs/PORTING.md` §4 for the full story):

* `rhs3(wk, s, slot: KSlot, uhat)` writes `wk.k1..k4` selected by the
  slot enum, computes the projection into a *fresh* local `Field3` and
  moves it into the slot at the end — one `&mut wk` at a time;
* stage inputs (`T1`) are cloned before the next `rhs3` call (≈2%
  runtime, ≈1.5 MB per clone at N=32);
* `step_rk4_3d(wk, s, uhat, dt)` writes the result into `wk.t2`; the
  runner clones it out;
* rotations (`rotate_pointwise3`, `rotate_full_symmetry3`) write
  `wk.t3`; the caller clones, masks, and swaps;
* `project3(s, out, inp)` is standalone (allocates its `kd` scratch
  locally) — used by the solver, the IC preparation, the reprojection
  audit and the self-test alike.

The lesson for porters: *the borrow checker forces the same
buffer-hygiene the C/C++ editions need for correctness* — dedicated
transform scratch, no aliasing between stages — and the resulting
design is cleaner, not slower.

## The deterministic RNG

`rand` is an external crate, so the file carries a 15-line **xorshift64\***
generator (`Rng`) with a Box–Muller `normal()` — enough for the random
IC and the self-test oracles, deterministic across platforms (same seed
→ same field), and completely dependency-free. The IC uses
`seed | 1` to avoid the xorshift zero fixed-point.

## CLI reference

Shared grammar (root README §5): `--quick --suite normal|hard
--experiment tg|abc|houluo|baudit --flow <id|all|list> --roadmap
--selftest --list-flows --report --n --nu --dt --t --cfl --gif --lang
--out --seed --no-color --ascii --help --version`. TUI as everywhere.
(Checkpoints are accepted and ignored — documented deviation; adaptive
CFL is fully ported.)

## The self-test

Ten checks, ≈ 7 s in release mode: FFT vs naive DFT (6e-15), 1-D
round-trip (4e-16), 3-D round-trip (6e-16), RK4 order from the dt-ladder
(`p = 4.125`), Leray divergence on a random field (3.6e-16), energy
non-increase, b-rotation isometry (1.4e-15), full-symmetry relabeling
(6e-16), PNG signature, GIF signature. The sparkline-glyph table has
*eight* entries — the first draft had seven and panicked on the 8th
level; the fix is immortalised in `../docs/PORTING.md` §4.

## Physics fidelity

Handshake numbers reproduce the reference: `sup|ω|(T=0.6) = 1.7795`,
`dλ/dt = −0.416 (R² = 1.00)`. Full experiment set (TG with hard ladder,
ABC Euler, Hou–Luo with Biot–Savart, b-audit with reprojection), the 2-D
barotropic runner with b-kicks and 24-frame GIF capture, the 20-flow
table, and the wave audits are ported. Deviations documented in
`../docs/PORTING.md` §3 (checkpoints stubbed).

## The writers

Same zero-dependency stack as the C edition in idiomatic Rust: CRC32 in
a `OnceLock` table, Adler-32 over the raw scanlines, stored-DEFLATE
zlib stream, chunk assembly with `to_be_bytes`; the GIF encoder with
the 9-bit packer, Clear-every-≤253 literals, EOI and the ≤255-byte
sub-block layer. Both verified by PIL/browser decoding in the
repository's verification pass.

## Performance

Reference machine (8 cores): selftest ≈ 6 s; TG N=16 T=0.6 ≈ 3.5 s;
TG N=32 T=2 ≈ 60 s; flow run 64² ≈ 2.5 s. Release profile sets
`opt-level = 3`, `codegen-units = 1`. The `--roadmap` benchmark reports
the machine's GFLOP/s and the N→cost table.

## Termux notes

`pkg install rust` (Termux ships a recent stable rustc); the empty
dependencies section means `cargo build --release` works offline on the
phone — no registry access, no vendored sources. For long runs:
`termux-wake-lock`. The binary is self-contained and can be copied to
`~/.local/bin` for daily use.

## Troubleshooting

* **`error[E0502]: cannot borrow ...`** — you are passing `&mut wk` and
  `&wk.field` together; follow the `KSlot` pattern in §5.
* **`static mut` warnings** — the config/session globals use
  `&raw mut`/`&raw const` (Rust ≥ 1.82). On older toolchains replace
  with `addr_of_mut!`/`addr_of!` or a `Mutex`-free `Cell`-based
  singleton; the physics code does not touch them.
* **`p ≈ 0.94` in selftest** — your FFT helpers are aliasing the RK4
  stage arrays; give them their own scratch (§5).
* **Slower than expected** — you built in debug mode; the release
  profile matters (×20 on the solver).
