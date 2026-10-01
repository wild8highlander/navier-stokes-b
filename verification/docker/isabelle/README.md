# `docker/isabelle/` — the Isabelle-HOL 2024 with Complex_Main image

> **Navigation:** [repository root](../../../README.md) › [verification](../../verification/README.md) › [docker](../README.md) › **`isabelle`**

![Image](https://img.shields.io/badge/isabelle-2B579A?style=flat-square) ![Toolchain](https://img.shields.io/badge/Isabelle-HOL_2024_with_Complex_Main-informational?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

The pinned environment for the isabelle tier of the verification matrix. The
image installs exactly the toolchain the framework expects — nothing more,
so the build is the environment statement.

```bash
docker build -t nsb-verify-isabelle .
docker run --rm -v "$PWD/../../..:/repo" -w /repo nsb-verify-isabelle bash -lc "isabelle build -D ."
```

Inside the container, the working command for this tier is:

```bash
isabelle build -D .
```

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../../../LICENSE.md)).
