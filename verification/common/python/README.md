# 🧰 common · python — the Utility Package

> **Navigation:** [`verification`](../../README.md) › [`common`](../README.md) › **`python`**

![Python](https://img.shields.io/badge/Python-3.10–3.12-informational?style=flat-square&logo=python&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **utility package** itself: four modules totalling ~2 KB. `verifier_base.py` (the heart) implements the shared verifier protocol; `config.py` the settings; `main.py` the aggregate CLI; `__init__.py` the exports. Imported by the API, the demos and the notebooks — see the parent README for the design notes.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`__init__.py`](__init__.py) | 48 B | package exports |
| [`config.py`](config.py) | 766 B | central configuration — section paths, tolerances, output options |
| [`main.py`](main.py) | 617 B | aggregate CLI — runs multiple sections through the shared base |
| [`verifier_base.py`](verifier_base.py) | 714 B | base verifier class — banner, assertion ledger, JSON verdict emission |

## 🔗 Cross-References

- [Parent — common/](../README.md)
- [Framework root](../../README.md)

## 🇷🇺 Краткое резюме (Russian Summary)

Пакет утилит: verifier_base (протокол верификатора), config, main (агрегатор CLI), __init__.

---

<div align="center">

**[⬆ Back to top](#-common--python--the-utility-package)** · 
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

