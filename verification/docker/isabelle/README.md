# 🐳 docker · isabelle — Pinned Toolchain Image

> **Navigation:** [`verification`](../../../verification/README.md) › [`docker`](../README.md) › **`isabelle`**

![Type](https://img.shields.io/badge/Type-Dockerfile-2496ED?style=flat-square&logo=docker&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **Dockerfile pinning the Isabelle-HOL (2024) environment** for the verification
framework. The image installs Isabelle with HOL, copies the verification sources, and defaults to `isabelle build -D .` — so `docker run` reproduces exactly what CI
runs, byte-for-byte at the toolchain level. budget for a long first build (heap images); later builds are incremental

## 📂 Contents

| File | Description |
|---|---|
| [`Dockerfile`](Dockerfile) | the Isabelle-HOL (2024) environment — install + source copy + verification entrypoint |

## ▶️ How to run

```bash
docker build -t rp-isabelle verification/docker/isabelle
docker run --rm -v "$PWD":/work rp-isabelle isabelle build -D verification/isabelle
```

The bind-mount (`-v "$PWD":/work`) lets you verify the repository you are
standing in rather than the copy baked into the image; omit it to run the
pinned snapshot.

## 🔗 Cross-references

- [Docker layer](../README.md) — the full image table and the compose flow
- [Isabelle-HOL (2024) language layer](../../../verification/isabelle/README.md)
- [Verification contract](../../../verification/README.md)

---

---

Navigation: [docker](../README.md) · [verification](../../../verification/README.md) · [IPL-RP-1.0](../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

