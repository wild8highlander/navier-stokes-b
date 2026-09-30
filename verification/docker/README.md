# 🐳 `verification/docker/` — Pinned Toolchain Images

> **Navigation:** [`verification`](../README.md) › **`docker`**

![Docker](https://img.shields.io/badge/Images-7-2496ED?style=flat-square&logo=docker&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

One pinned container per formal/extended toolchain, so container runs are
the closest match to CI: the images pin the toolchain versions, copy the
verification sources, and default to running the verification — `docker
run` reproduces exactly what CI runs, byte-for-byte at the toolchain level.

## The images

| Folder | Toolchain | Default entrypoint |
|---|---|---|
| [`agda/`](agda/README.md) | Agda (2.6) | `agda --safe verification/agda/Section1_CorrectionB/CorrectionB.agda` |
| [`coq/`](coq/README.md) | Coq/Rocq (8.18) | `coqc verification/coq/section1_correction_b/CorrectionB.v` |
| [`cpp/`](cpp/README.md) | C++17 + CMake | `./build/section1_correction_b` |
| [`haskell/`](haskell/README.md) | Haskell (GHC 9.4) | `cabal run section1-correction-b` |
| [`isabelle/`](isabelle/README.md) | Isabelle-HOL (2024) | `isabelle build -D verification/isabelle` |
| [`lean4/`](lean4/README.md) | Lean 4 (v4.14) | `lake exe check` |
| [`rust/`](rust/README.md) | Rust (1.75+) | `cargo run --release --manifest-path verification/rust/Cargo.toml` |

## Build and run everything

```bash
make docker-build     # all 7 toolchain images
make docker-up        # run the verification services (docker compose)
make docker-down      # stop them again
```

or per image (from the repository root):

```bash
docker build -t rp-lean4 verification/docker/lean4
docker run --rm -v "$PWD":/work rp-lean4 lake exe check
```

## Why pinned images matter

A formal proof is only as reproducible as its kernel version; a numerical
verdict only as reproducible as its libm. Pinning the toolchain turns
"works on my machine" into a byte-level property, and lets the CI matrix
and any external audit execute the *same* environment. When a toolchain
upstream changes, the fix is a one-line base-image bump plus a re-run —
see the [hub's maintenance map](../README.md).

---

---

Navigation: [repository root](../../README.md) · [extended-languages notes](../docs/extended-languages/README.md) · [IPL-RP-1.0](../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

