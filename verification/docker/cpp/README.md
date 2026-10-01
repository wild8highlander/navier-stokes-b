# `docker/cpp/` — the gcc C++17 + CMake (+ BLAS/LAPACK) image

> **Navigation:** [repository root](../../../README.md) › [verification](../../verification/README.md) › [docker](../README.md) › **`cpp`**

![Image](https://img.shields.io/badge/cpp-2B579A?style=flat-square) ![Toolchain](https://img.shields.io/badge/gcc_C++17_+_CMake_(+_BLAS/LAPACK)-informational?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

The pinned environment for the cpp tier of the verification matrix. The
image installs exactly the toolchain the framework expects — nothing more,
so the build is the environment statement.

```bash
docker build -t nsb-verify-cpp .
docker run --rm -v "$PWD/../../..:/repo" -w /repo nsb-verify-cpp bash -lc "cmake .. && make -j$(nproc)"
```

Inside the container, the working command for this tier is:

```bash
cmake .. && make -j$(nproc)
```

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../../../LICENSE.md)).
