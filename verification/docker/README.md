# `docker/` — one pinned container per toolchain

> **Navigation:** [repository root](../README.md) › [verification](../README.md) › **`docker`**

![Images](https://img.shields.io/badge/7-2B579A?style=flat-square) ![Purpose](https://img.shields.io/badge/reproducible--CI-2EA043?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

The formal and extended toolchains are pinned as container images so that
`make docker-build && make docker-up` reproduces the CI environment
locally, byte for byte. Each subdirectory carries one `Dockerfile` and its
README.

| Image | Toolchain | What runs inside |
|---|---|---|
| [`lean4/`](lean4/README.md) | Lean 4 + Mathlib 4 (v4.14.0 pinned) | `lake build && lake exe check` |
| [`coq/`](coq/README.md) | Coq/Rocq 8.18 with Reals + lra | `coq_makefile -f _CoqProject -o Makefile && make` |
| [`isabelle/`](isabelle/README.md) | Isabelle-HOL 2024 with Complex_Main | `isabelle build -D .` |
| [`agda/`](agda/README.md) | Agda 2.6 with the standard library | `agda --safe Section1_CorrectionB/CorrectionB.agda` |
| [`cpp/`](cpp/README.md) | gcc C++17 + CMake (+ BLAS/LAPACK) | `cmake .. && make -j$(nproc)` |
| [`rust/`](rust/README.md) | Rust stable (edition 2021) | `cargo build --release` |
| [`haskell/`](haskell/README.md) | GHC 9.4 + Cabal | `cabal build all` |

## Run

```bash
make docker-build     # build every image
make docker-up        # start the compose services
make docker-down      # stop
```

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../LICENSE.md)).
