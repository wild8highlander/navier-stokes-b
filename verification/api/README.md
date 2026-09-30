# 🌐 `verification/api/` — the REST Verification API

> **Navigation:** [`verification`](../README.md) › **`api`**

![Type](https://img.shields.io/badge/Type-REST_API-6BA539?style=flat-square)
![Framework](https://img.shields.io/badge/Framework-Flask-000000?style=flat-square&logo=flask&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

A **REST API wrapper** around the verification framework:
[`server.py`](server.py) (Flask) exposes the section verifiers over HTTP so
audits can be scripted from any language or CI job without installing the
toolchains locally. Each endpoint runs the corresponding verifier, captures
its PASS ledger and JSON verdict, and returns them as a structured response
— the exact same contract the CLI ports print to the console.

## Contents

| File | Description |
|---|---|
| [`server.py`](server.py) | the Flask application — section endpoints returning PASS ledgers + JSON verdicts |
| [`requirements.txt`](requirements.txt) | pinned Python dependencies for the API service |

## How to run

```bash
pip install -r verification/api/requirements.txt
python verification/api/server.py
# then query the section endpoints over HTTP:
curl http://127.0.0.1:5000/section/1
```

The response contains the section number, the computed values and the
`all_passed` flag, so a monitoring job can assert on it directly. The API
reuses [`common/`](../common/README.md) for the verifier protocol and is
bootstrapped by [`scripts/start_api.sh`](../scripts/README.md).

## Use cases

- **Scheduled audits** — a cron/CI job hits the endpoints and alerts on any
  `all_passed: false`;
- **cross-language dashboards** — the [demos](../demo/README.md) and the
  [web-dashboard](../web-dashboard/README.md) consume the same endpoints;
- **third-party verification** — an external reviewer can trigger the
  verifiers without installing Lean/Coq/Isabelle/Agda.

---

---

Navigation: [repository root](../../README.md) · [common](../common/README.md) · [demos](../demo/README.md) · [IPL-RP-1.0](../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

