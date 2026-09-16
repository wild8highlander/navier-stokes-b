# 🐳 docker · Coq/Rocq — Pinned Toolchain Image

> **Navigation:** [`verification`](../../README.md) › [`docker`](../README.md) › **`coq`**

![Type](https://img.shields.io/badge/Type-Dockerfile-2496ED?style=flat-square&logo=docker&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **Dockerfile pinning the Coq/Rocq (8.18) environment** for this framework layer. The image installs the toolchain (coq_makefile or per-file coqc as the in-container flow), copies the verification sources, and defaults to running the Coq/Rocq verification — so `docker run` reproduces exactly what CI runs, byte-for-byte at toolchain level.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`Dockerfile`](Dockerfile) | 179 B | Coq/Rocq 8.18 environment — install + source copy + verification entrypoint |

## ▶️ How to Run

```bash
docker build -t rp-coq verification/docker/coq
docker run --rm rp-coq
```

## 🔗 Cross-References

- [Docker layer](../README.md)
- [Language layer](../../coq/README.md)

## 🇷🇺 Краткое резюме (Russian Summary)

Dockerfile со средой Coq/Rocq 8.18: установка тулчейна + запуск верификации по умолчанию.

---

<div align="center">

**[⬆ Back to top](#-docker--coqrocq--pinned-toolchain-image)** · 
**[Repository root](../../README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>
<!-- doc-enhancer:block v1 (автоматический блок; файлы лицензии не затрагиваются) -->

---

## 🧭 Навигация и быстрые ссылки (auto)

- 🏠 [Корень репозитория](../../../../README.md)
- 📖 [Как верифицируются утверждения](../../../../verification/README.md)
- 📄 [Статьи (PDF)](../../../../papers/README.md) · 📚 [Монографии](../../../../docs/README.md) · 🧾 [LaTeX](../../../../src/README.md)
- ⚖️ [Лицензия IPL-RP-1.0](../../../../LICENSE.md) — просмотр, одна резервная копия и цитирование с атрибуцией разрешены; остальное — только с письменного согласия автора.

*Блок добавлен автоматически (`doc-enhancer v1`); к лицензии отношения не имеет и её не изменяет. Повторный запуск скрипта блок не дублирует.*

