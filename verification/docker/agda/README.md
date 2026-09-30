# 🐳 docker · agda — Pinned Toolchain Image

> **Navigation:** [`verification`](../../../verification/README.md) › [`docker`](../README.md) › **`agda`**

![Type](https://img.shields.io/badge/Type-Dockerfile-2496ED?style=flat-square&logo=docker&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **Dockerfile pinning the Agda (2.6) environment** for the verification
framework. The image installs Agda via cabal, copies the verification sources, and type-checks every module with `--safe` — so `docker run` reproduces exactly what CI
runs, byte-for-byte at the toolchain level. the stdlib dependency is minimal; the `--safe` flag is the CI configuration

## 📂 Contents

| File | Description |
|---|---|
| [`Dockerfile`](Dockerfile) | the Agda (2.6) environment — install + source copy + verification entrypoint |

## ▶️ How to run

```bash
docker build -t rp-agda verification/docker/agda
docker run --rm -v "$PWD":/work rp-agda agda --safe verification/agda/Section1_CorrectionB/CorrectionB.agda
```

The bind-mount (`-v "$PWD":/work`) lets you verify the repository you are
standing in rather than the copy baked into the image; omit it to run the
pinned snapshot.

## 🔗 Cross-references

- [Docker layer](../README.md) — the full image table and the compose flow
- [Agda (2.6) language layer](../../../verification/agda/README.md)
- [Verification contract](../../../verification/README.md)

---

---

Navigation: [docker](../README.md) · [verification](../../../verification/README.md) · [IPL-RP-1.0](../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

