# 🎛 verification · demo — Interactive Front-Ends (Gradio + Streamlit)

> **Navigation:** [`verification`](../README.md) › **`demo`**

![Type](https://img.shields.io/badge/Type-Interactive%20Demo-FF4B4B?style=flat-square) ![Python](https://img.shields.io/badge/Python-3.10–3.12-informational?style=flat-square&logo=python&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

Two **interactive front-ends** over the verification framework, for human exploration instead of scripted audits: `streamlit_app.py` (Streamlit) and `gradio_app.py` (Gradio). Both let you pick a research section, run its verifier live in the browser, and see the assertion ledger and JSON verdict rendered as UI — the same output the CLI prints, but navigable.

The demos import the shared utilities from [`common/`](../common/README.md) and call the same section verifiers the API exposes, so what you see interactively is exactly what CI tests. `requirements.txt` pins the (deliberately small) front-end dependencies. Neither demo is part of the release pipeline; they exist to make the framework tangible in a talk or classroom setting.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`gradio_app.py`](gradio_app.py) | 306 B | Gradio front-end — same contract in a Gradio Blocks layout |
| [`requirements.txt`](requirements.txt) | 30 B | pinned front-end dependencies (streamlit, gradio) |
| [`streamlit_app.py`](streamlit_app.py) | 213 B | Streamlit front-end — section picker, live run, rendered PASS/JSON |

## ▶️ How to Run

```bash
pip install -r verification/demo/requirements.txt
streamlit run verification/demo/streamlit_app.py
# or:
gradio verification/demo/gradio_app.py
```

## 🔗 Cross-References

- [Shared utilities](../common/README.md)
- [REST API alternative](../api/README.md)

## 🇷🇺 Brief Summary (Russian Summary)

**verification/demo/** — two interactive interfaces (Streamlit and Gradio): pick a section, run it in the browser, render PASS/JSON. They use the same verifiers as CI — ideal for demonstrations.

---

<div align="center">

**[⬆ Back to top](#-verification--demo--interactive-front-ends-gradio--streamlit)** · 
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

