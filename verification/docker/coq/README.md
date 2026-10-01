# `docker/coq/` — the Coq/Rocq 8.18 with Reals + lra image

> **Navigation:** [repository root](../../../README.md) › [verification](../../verification/README.md) › [docker](../README.md) › **`coq`**

![Image](https://img.shields.io/badge/coq-2B579A?style=flat-square) ![Toolchain](https://img.shields.io/badge/Coq/Rocq_8.18_with_Reals_+_lra-informational?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

The pinned environment for the coq tier of the verification matrix. The
image installs exactly the toolchain the framework expects — nothing more,
so the build is the environment statement.

```bash
docker build -t nsb-verify-coq .
docker run --rm -v "$PWD/../../..:/repo" -w /repo nsb-verify-coq bash -lc "coq_makefile -f _CoqProject -o Makefile && make"
```

Inside the container, the working command for this tier is:

```bash
coq_makefile -f _CoqProject -o Makefile && make
```

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../../../LICENSE.md)).
