# 🐳 docker · coq — Pinned Toolchain Image

> **Navigation:** [`verification`](../../../verification/README.md) › [`docker`](../README.md) › **`coq`**

![Type](https://img.shields.io/badge/Type-Dockerfile-2496ED?style=flat-square&logo=docker&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **Dockerfile pinning the Coq/Rocq (8.18) environment** for the verification
framework. The image installs the Coq compiler via opam, copies the verification sources, and compiles every `.v` file from `_CoqProject` — so `docker run` reproduces exactly what CI
runs, byte-for-byte at the toolchain level. the `Compute` calls in the sources print values during the build

## 📂 Contents

| File | Description |
|---|---|
| [`Dockerfile`](Dockerfile) | the Coq/Rocq (8.18) environment — install + source copy + verification entrypoint |

## ▶️ How to run

```bash
docker build -t rp-coq verification/docker/coq
docker run --rm -v "$PWD":/work rp-coq coqc verification/coq/section1_correction_b/CorrectionB.v
```

The bind-mount (`-v "$PWD":/work`) lets you verify the repository you are
standing in rather than the copy baked into the image; omit it to run the
pinned snapshot.

## 🔗 Cross-references

- [Docker layer](../README.md) — the full image table and the compose flow
- [Coq/Rocq (8.18) language layer](../../../verification/coq/README.md)
- [Verification contract](../../../verification/README.md)

---

---

Navigation: [docker](../README.md) · [verification](../../../verification/README.md) · [IPL-RP-1.0](../../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

