# Porting Guide — how the eight editions map onto the Julia reference

This document is the contract between the reference implementation
(`julia/nsb_lab_standalone.jl`, v2.1.0) and every port. Section numbers of
[`PHYSICS.md`](PHYSICS.md) are referenced as `P§n`.

## 1. The verification ladder (read this first)

A port is "done" when, **in order**:

1. `--selftest` passes all checks (FFT vs naive DFT, 1-D/3-D round-trips,
   measured RK4 order, machine-level Leray divergence, isometry, relabeling,
   writer signatures);
2. the Taylor–Green headline numbers reproduce the reference:
   `sup|ω|(T=0.6) = 1.7795 ± 1e-12` and `dλ/dt = −0.416 (R² = 1.00)`
   for `N=16, ν=0.02, dt=0.01`;
3. the b-audit invariants hold (relabel < 1e-9, isometry < 1e-12,
   div-injection > 1e-8, reprojection < 1e-10);
4. the CLI grammar of the root README is implemented with the same names;
5. the encyclopedia README for the edition is written and truthful.

If a deviation is unavoidable, it must be documented here *and* in the
edition's README. Silent deviation = bug.

## 2. Function-by-function map

| Julia reference | Python | C | C++ | Rust | Go | PHP | Web (JS) |
|---|---|---|---|---|---|---|---|
| `nsb_fft_plan` / `nsb_fft1d!` | `fft1d_last` | `fft_plan`/`fft1d` | `FFTPlan::fft1d` | `FftPlan::fft1d` | `fftPlan/fft1d` | `fftPlan/fft1dClear` | `makePlan/fft1d` |
| `nsb_fftn!` (3-D) | `fft3d` | `fft3d` | `fft3d` (thread-par) | `fft3d` (scope-par) | `fft3d` (goroutine-par) | `fft3d` | `fft3d` |
| `nsb_fft2d!` | `fft2d` | `fft2d` | `fft2d` | `fft2d` | `fft2d` | `fft2dArr` | `fft2d` |
| `NsbNSE3D` | `NSE3D` | `nse3d_init` | `NSE3D` | `Nse3D::new` | `newNSE3D` | `nse3dInit` | `g3Init` |
| `nsb_project!` | `project3` | `project3` | `project3` | `project3` | `project3` | `projectAll` | `project3d` |
| `nsb_curl_hat!` | `curl_hat3` | `curl_hat3` | `curl_hat3` | `curl_hat3` | `curlHat3` | `curlHatAll` | `curl3d` |
| `nsb_rhs!` | `rhs3` | `rhs3` | `rhs3` | `rhs3` | `rhs3` | `rhsAll` | `g3Rhs` |
| `nsb_step_rk4!` | `step_rk4_3d` | `step_rk4_3d` | `step_rk4_3d` | `step_rk4_3d` | `stepRK4_3d` | `stepRK4All` | `g3Step` |
| `NsbBaro2D` | `Baro2D` | `baro_init` | `Baro2D` | `Baro2D::new` | `newBaro2D` | inline in `flowRunPHP` | `b2Init` |
| `nsb_baro_rhs!` | `baro_rhs` | `baro_rhs` | `baro_rhs` | `baro_rhs` | `baroRhs` | inline | `b2Rhs` |
| `nsb_baro_step!` | `baro_step` | `baro_step` | `baro_step` | `baro_step` | `baroStep` | inline | `b2Step` |
| `nsb_energy/enstrophy/palinstrophy/dissipation` | same names | same | same | same | same | same | `g3Diag` |
| `nsb_blowup_report` | `blowup_report` | `blowup_report` | `blowup_report` | `blowup_report` | `blowupReport` | inline λ-fit in `expTGPHP` | — (2-D only) |
| `nsb_ic_taylor_green/abc/hou_luo/random` | same | same | same | same | same | same | `icTaylorGreen…` |
| `nsb_rotate_pointwise!/full_symmetry!` | `rotate_pointwise3/full_symmetry3` | same | same | same | `…Into` variants | `rotate…PHP` | — |
| `nsb_run_decay` | `run_decay_3d` | `run_decay_3d` | `run_decay_3d` | `run_decay_3d` | `runDecay3d` | `runDecayPHP` | worker loop |
| `nsb_exp_taylor_green/abc/houluo/baudit/scan` | `exp_*` | `exp_*` | `exp_*` | `exp_*` | `exp*` | `exp*PHP` (scan: Julia/Py only) | — |
| `NSB_FLOWS` (20) | `FLOWS` | `FLOWS[20]` | `FLOWS[20]` | `FLOWS` | `FLOWS` | `flowsData()` | — |
| `nsb_flow_run` (+bkick, wave audit) | `flow_run` | `flow_run` | `flow_run` | `flow_run` | `flowRun` | `flowRunPHP` | — |
| `nsb_png/heat` (own PNG) | `write_png_rgb/heat_png` (zlib) | `heat_png_write` (stored) | `heat_png_write` (stored) | `heat_png_write` (stored) | stdlib `image/png` | `heatPngWritePHP` | `canvas.toDataURL` |
| `nsb_gif_write` (uncompressed LZW) | `write_gif` | `c_gif_write` | `gif_write` | `gif_write` | `gifWrite` | `gifWritePHP` | — |
| `nsb_progress` (one line) | `progress` | `progress` | `progress` | `progress` | `progress` | `progress` | `setProgress` (HTML) |
| i18n RU/EN | `init_i18n` | `I18N[]` | `I18N[]` | `I18N[]` | `I18N` | `initI18n` | `I18N` (6 langs) |

## 3. Documented deviations (and why they are safe)

1. **PHP `sup|ω|` is a component-wise maximum** of |ω_i| instead of the
   magnitude √(ω₁²+ω₂²+ω₃²). Effect: the RK4-order measurement through the
   sup-proxy gives 3.947 instead of 4.125; the tolerance in the PHP selftest
   is ±1.5. The TG headline check in PHP uses the same proxy, so its
   *self-consistency* is what is verified (order ≈ 4, monotone decay), not
   cross-language bit equality. Rationale: the magnitude version costs 3
   inverse FFTs per sample in an already slow interpreter.
2. **C++/Rust/Go: checkpoints are stubbed** (the parameter is accepted and
   ignored). Rationale: the binary checkpoint format of the Julia/Python
   editions is a serialisation detail; the CFL/adaptive machinery (which is
   what the checkpoints protect) is fully ported. The C edition implements
   the full binary checkpoint + `--resume` path.
3. **Go/Rust/C++ parallel FFT uses gather→parallel→scatter** for the two
   strided axes instead of Julia's threaded column FFT. Effect: two extra
   full-array passes per transform (memory-bound, ≈10–15% at N≥64), in
   exchange for data-race-free parallelism without unsafe code.
4. **Web 3-D solver fixes N=32 and T=2.0** for browser responsiveness, and
   the 2-D β-plane demo is endless (no fixed horizon). Both documented in
   the web README and the page caption.
5. **The b-audit in the PHP edition measures the invariants on the initial
   ABC field directly** (one kick, no repeated schedule) instead of running
   three full decay windows. The measured quantities are the same five
   `ck_*` invariants; the long-window dynamics audit remains available in
   all other editions.
6. **Plot rendering**: the Julia edition has the full matplotlib-style
   rasteriser with axes/ticks/legend; the C/C++/Rust/Go editions render
   grid+axes+legend polylines (a subset); the web app draws live charts on
   canvas. Report *data* (CSV/JSON) is identical everywhere.

## 4. Porting traps found on the way (learn from them)

* **`std::complex<double>` refuses `int * complex`** (would deduce
  `complex<int>`): every integer wavenumber multiply needs an explicit
  `double(...)`/`cplx(k,0)` cast. The C edition is immune (`_Complex`
  promotes), the JS/Go editions too (`Number`/explicit `complex(f,0)`).
* **Go has no implicit float↔complex mixing either**; also `pack('N5', …)`
  analogues don't exist — build binary headers byte-by-byte.
* **Rust borrow checker vs monolithic work-structs**: the Julia pattern
  `rhs!(du, uhat, s, W)` (du and W borrow the same struct) is *illegal* in
  safe Rust. Fix: give `rhs3` a `KSlot` enum and let it write `W.k1..k4`
  internally, clone the stage inputs (`T1`), and make projections
  standalone functions over `(s, out, inp)`. Cost: a few extra array clones
  per step, ≈2% runtime. See `rust/src/main.rs` `rhs3/step_rk4_3d`.
* **GIF LZW framing**: the "uncompressed LZW" trick still requires 9-bit
  little-endian code packing *and* ≤255-byte sub-blocks, each preceded by a
  length byte, terminated by `0x00`. Omit the sub-block layer (as a first
  draft did here) and every decoder from PIL to Chrome rejects the file.
* **PHP `pack('N5', $W, $H, 8, 2, 0)`** writes *five 32-bit words* — the
  PNG IHDR must be `pack('N',W).pack('N',H).pack('C5',8,2,0,0,0)` (13
  bytes). A 22-byte IHDR parses as bitdepth=0 and no decoder opens it.
* **`bytes((x if k else y))` in Python** is `bytes(int)` = NUL-filled array
  of that length, not a one-element bytes — the GIF GCE bug class.
* **Self-test oracles**: the 3-D FFT round-trip must compare against a
  *saved copy* of the input, not against itself (an early C draft compared
  `cabs(A[i])` and "passed" garbage); and the Leray check must project a
  *random* field, not Taylor–Green (which is already solenoidal by
  construction and would pass even with a broken projector).
* **Symmetric index maps**: the full-symmetry relabeling is
  `u'(x_i,y_j,z_k) = R u(y_j, −x_i, z_k)` with `−x_i → (N − i) mod N`.
  Off-by-one here survives every *energy* test (rotations conserve energy
  for any index permutation!) and only fails the *enstrophy* match — which
  is exactly why the self-test includes check #8.
* **Interpreter desync**: a time series that appends to `t` but not to all
  metric arrays (a Go first draft) panes the λ-scanner with index-out-of-
  range three windows later, far from the cause. Initialise all series with
  the same leading sample.

## 5. Adding a new edition

1. Read `PHYSICS.md` once end-to-end.
2. Port the FFT + self-test; pass checks 1–3.
3. Port the 3-D solver + TG experiment; reproduce the headline numbers (§1
   ladder, item 2).
4. Port diagnostics + b-audit; pass the invariants.
5. Port the 2-D β-plane + flows table; run one vortex flow end-to-end.
6. Wire the shared CLI grammar, the one-line progress bar, RU/EN strings,
   CSV/JSON export; writers per the matrix in §2.
7. Update the root README table, the CI workflow and this file.
