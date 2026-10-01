# `docker/agda/` — the Agda 2.6 with the standard library image

> **Navigation:** [repository root](../../../README.md) › [verification](../../verification/README.md) › [docker](../README.md) › **`agda`**

![Image](https://img.shields.io/badge/agda-2B579A?style=flat-square) ![Toolchain](https://img.shields.io/badge/Agda_2.6_with_the_standard_library-informational?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

The pinned environment for the agda tier of the verification matrix. The
image installs exactly the toolchain the framework expects — nothing more,
so the build is the environment statement.

```bash
docker build -t nsb-verify-agda .
docker run --rm -v "$PWD/../../..:/repo" -w /repo nsb-verify-agda bash -lc "agda --safe Section1_CorrectionB/CorrectionB.agda"
```

Inside the container, the working command for this tier is:

```bash
agda --safe Section1_CorrectionB/CorrectionB.agda
```

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../../../LICENSE.md)).
