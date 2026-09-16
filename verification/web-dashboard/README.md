# 📊 `verification/web-dashboard/` — the Dashboard Package Manifest

> **Navigation:** [`verification`](../README.md) › **`web-dashboard`**

![Type](https://img.shields.io/badge/Type-JS_package-CB3837?style=flat-square&logo=npm&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The package manifest of the JS dashboard — the browser front-end that
visualises verification verdicts (per-section, per-language OK/FAIL
matrix, value tables). This directory pins the package; the dashboard
consumes the same JSON verdicts as the
[validator](../tests/README.md), so what the browser shows is what CI
asserted.

## Contents

| File | Description |
|---|---|
| [`package.json`](package.json) | the npm manifest — name, scripts, dependencies |

## Usage

```bash
cd verification/web-dashboard
npm install        # or: npm ci
npm run build
```

`make install` at the repository root runs the npm step for you
(`cd verification/web-dashboard && npm ci || true`) — the dashboard is an
optional surface; the CLI and the [API](../api/README.md) do not depend on
it.

---

---

Navigation: [repository root](../../README.md) · [api](../api/README.md) · [tests](../tests/README.md) · [IPL-RP-1.0](../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

