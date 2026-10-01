# `docker/haskell/` — the GHC 9.4 + Cabal image

> **Navigation:** [repository root](../../../README.md) › [verification](../../verification/README.md) › [docker](../README.md) › **`haskell`**

![Image](https://img.shields.io/badge/haskell-2B579A?style=flat-square) ![Toolchain](https://img.shields.io/badge/GHC_9.4_+_Cabal-informational?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

The pinned environment for the haskell tier of the verification matrix. The
image installs exactly the toolchain the framework expects — nothing more,
so the build is the environment statement.

```bash
docker build -t nsb-verify-haskell .
docker run --rm -v "$PWD/../../..:/repo" -w /repo nsb-verify-haskell bash -lc "cabal build all"
```

Inside the container, the working command for this tier is:

```bash
cabal build all
```

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../../../LICENSE.md)).
