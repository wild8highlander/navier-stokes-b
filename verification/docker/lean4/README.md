# 🐳 docker · Lean 4 — Pinned Toolchain Image

> **Navigation:** [`verification`](../../README.md) › [`docker`](../README.md) › **`lean4`**

![Type](https://img.shields.io/badge/Type-Dockerfile-2496ED?style=flat-square&logo=docker&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **Dockerfile pinning the Lean 4 (v4.14) environment** for this framework layer. The image installs the toolchain (lake build as the in-container flow), copies the verification sources, and defaults to running the Lean 4 verification — so `docker run` reproduces exactly what CI runs, byte-for-byte at toolchain level.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`Dockerfile`](Dockerfile) | 147 B | Lean 4 v4.14 environment — install + source copy + verification entrypoint |

## ▶️ How to Run

```bash
docker build -t rp-lean4 verification/docker/lean4
docker run --rm rp-lean4
```

## 🔗 Cross-References

- [Docker layer](../README.md)
- [Language layer](../../lean4/README.md)

## 📝 Summary

Dockerfile with the Lean 4 v4.14 environment: toolchain installation + verification run as the default command.

---

<div align="center">

**[⬆ Back to top](#-docker--lean-4--pinned-toolchain-image)** · 
**[Repository root](../../README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>
<!-- doc-enhancer:block v1 (auto-generated block; license files are not touched) -->

---

## 🧭 Navigation and Quick Links (auto)

- 🏠 [Repository root](../../../../README.md)
- 📖 [How the claims are verified](../../../../verification/README.md)
- 📄 [Papers (PDF)](../../../../papers/README.md) · 📚 [Monographs](../../../../docs/README.md) · 🧾 [LaTeX](../../../../src/README.md)
- ⚖️ [IPL-RP-1.0 License](../../../../LICENSE.md) — viewing, a single backup copy, and citation with attribution are permitted; everything else requires the author's written permission.

*Block added automatically (`doc-enhancer v1`); it is unrelated to the license and does not modify it. Re-running the script does not duplicate the block.*

