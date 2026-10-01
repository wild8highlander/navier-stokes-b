# `docker/lean4/` — the Lean 4 + Mathlib 4 (v4.14.0 pinned) image

> **Navigation:** [repository root](../../../README.md) › [verification](../../verification/README.md) › [docker](../README.md) › **`lean4`**

![Image](https://img.shields.io/badge/lean4-2B579A?style=flat-square) ![Toolchain](https://img.shields.io/badge/Lean_4_+_Mathlib_4_(v4.14.0_pinned)-informational?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

The pinned environment for the lean4 tier of the verification matrix. The
image installs exactly the toolchain the framework expects — nothing more,
so the build is the environment statement.

```bash
docker build -t nsb-verify-lean4 .
docker run --rm -v "$PWD/../../..:/repo" -w /repo nsb-verify-lean4 bash -lc "lake build && lake exe check"
```

Inside the container, the working command for this tier is:

```bash
lake build && lake exe check
```

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../../../LICENSE.md)).
