# 🧪 verification · tests — Cross-Language Integration Tests

> **Navigation:** [`verification`](../README.md) › **`tests`**

![Python](https://img.shields.io/badge/Python-3.10–3.12-informational?style=flat-square&logo=python&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **integration-test layer** of the framework: the tests that guard the *contract* between languages, not just individual implementations. `extended_cross_language_validator.py` runs the extended-language ports and asserts their verdict JSON matches the Python reference to tolerance — this is the automated form of the [Section × Language matrix](../../README.md#-верификация-на-11-языках). `test_extended_languages.py` carries the pytest suite for the extended toolchains themselves (availability, build, run, verdict shape), so a toolchain regression is caught by tests rather than by a silently skipped CI job.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`extended_cross_language_validator.py`](extended_cross_language_validator.py) | 700 B | runs extended ports, diffs verdict JSON against the Python reference |
| [`test_extended_languages.py`](test_extended_languages.py) | 2.5 KB | pytest suite — toolchain availability, builds, verdict-shape checks |

## ▶️ How to Run

```bash
python verification/tests/extended_cross_language_validator.py
pytest verification/tests/test_extended_languages.py
```

## 🔗 Cross-References

- [CI extended languages](../../.github/workflows/README.md)
- [Framework root](../README.md)

## 🇷🇺 Краткое резюме (Russian Summary)

Интеграционные тесты контракта: валидатор сверяет JSON-вердикты расширенных портов с Python-референсом; pytest-набор проверяет доступность и сборку тулчейнов.

---

<div align="center">

**[⬆ Back to top](#-verification--tests--cross-language-integration-tests)** · 
**[Repository root](../README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>
<!-- doc-enhancer:block v1 (автоматический блок; файлы лицензии не затрагиваются) -->

---

## 🧭 Навигация и быстрые ссылки (auto)

- 🏠 [Корень репозитория](../../../README.md)
- 📖 [Как верифицируются утверждения](../../../verification/README.md)
- 📄 [Статьи (PDF)](../../../papers/README.md) · 📚 [Монографии](../../../docs/README.md) · 🧾 [LaTeX](../../../src/README.md)
- ⚖️ [Лицензия IPL-RP-1.0](../../../LICENSE.md) — просмотр, одна резервная копия и цитирование с атрибуцией разрешены; остальное — только с письменного согласия автора.

*Блок добавлен автоматически (`doc-enhancer v1`); к лицензии отношения не имеет и её не изменяет. Повторный запуск скрипта блок не дублирует.*

