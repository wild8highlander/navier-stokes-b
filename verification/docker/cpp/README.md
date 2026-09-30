# 🐳 docker · cpp — Pinned Toolchain Image

> **Navigation:** [`verification`](../../../verification/README.md) › [`docker`](../README.md) › **`cpp`**

![Type](https://img.shields.io/badge/Type-Dockerfile-2496ED?style=flat-square&logo=docker&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **Dockerfile pinning the C++17 + CMake environment** for the verification
framework. The image installs the GCC toolchain with OpenBLAS/LAPACK, copies the verification sources, and builds all six section targets — so `docker run` reproduces exactly what CI
runs, byte-for-byte at the toolchain level. the BLAS provider is detected at configure time and printed

## 📂 Contents

| File | Description |
|---|---|
| [`Dockerfile`](Dockerfile) | the C++17 + CMake environment — install + source copy + verification entrypoint |

## ▶️ How to run

```bash
docker build -t rp-cpp verification/docker/cpp
docker run --rm -v "$PWD":/work rp-cpp ./build/section1_correction_b
```

The bind-mount (`-v "$PWD":/work`) lets you verify the repository you are
standing in rather than the copy baked into the image; omit it to run the
pinned snapshot.

## 🔗 Cross-references

- [Docker layer](../README.md) — the full image table and the compose flow
- [C++17 + CMake language layer](../../../verification/cpp/README.md)
- [Verification contract](../../../verification/README.md)

---

---

Navigation: [docker](../README.md) · [verification](../../../verification/README.md) · [IPL-RP-1.0](../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

