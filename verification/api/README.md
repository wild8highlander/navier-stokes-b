# 🌐 verification · api — the REST Verification API

> **Navigation:** [`verification`](../README.md) › **`api`**

![Type](https://img.shields.io/badge/Type-REST%20API-6BA539?style=flat-square) ![Python](https://img.shields.io/badge/Python-3.10–3.12-informational?style=flat-square&logo=python&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

A **REST API wrapper** around the verification framework: `server.py` (Flask) exposes the section verifiers over HTTP so audits can be scripted from any language or CI job without installing the toolchains locally. Each endpoint runs the corresponding verifier, captures its PASS ledger and JSON verdict, and returns them as a structured response — the exact same contract the CLI ports print to the console.

Start the server with the pinned requirements (`requirements.txt`), then query the section endpoints; the response contains the section number, the computed values and the `all_passed` flag, so a monitoring job can assert on it directly. The API reuses [`common/`](../common/README.md) for the verifier protocol and is exercised by [`scripts/start_api.sh`](../scripts/README.md).

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`requirements.txt`](requirements.txt) | 31 B | pinned Python dependencies for the API service |
| [`server.py`](server.py) | 412 B | Flask application — section endpoints returning PASS ledgers + JSON verdicts |

## ▶️ How to Run

```bash
pip install -r verification/api/requirements.txt
python verification/api/server.py
# then query the section endpoints over HTTP
```

## 🔗 Cross-References

- [Shared utilities](../common/README.md)
- [Bootstrap script](../scripts/README.md)

## 🇷🇺 Brief Summary (Russian Summary)

**verification/api/** — a REST wrapper (Flask) around the verifiers: the section endpoints return the PASS log and the JSON verdict; convenient for scripted audits without local toolchains. Start it with scripts/start_api.sh.

---

<div align="center">

**[⬆ Back to top](#-verification--api--the-rest-verification-api)** · 
**[Repository root](../README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>
<!-- doc-enhancer:block v1 (auto-generated block; license files are not affected) -->

---

## 🧭 Navigation and Quick Links (auto)

- 🏠 [Repository root](../../../README.md)
- 📖 [How the claims are verified](../../../verification/README.md)
- 📄 [Papers (PDF)](../../../papers/README.md) · 📚 [Monographs](../../../docs/README.md) · 🧾 [LaTeX](../../../src/README.md)
- ⚖️ [IPL-RP-1.0 License](../../../LICENSE.md) — viewing, a single backup copy, and citation with attribution are permitted; everything else — only with the author's written consent.

*Block added automatically (`doc-enhancer v1`); it is unrelated to the license and does not modify it. Re-running the script does not duplicate the block.*

