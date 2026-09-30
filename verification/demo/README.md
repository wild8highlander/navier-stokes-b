# 🖥️ `verification/demo/` — Interactive Gradio & Streamlit Front-ends

> **Navigation:** [`verification`](../README.md) › **`demo`**

![Gradio](https://img.shields.io/badge/UI-Gradio-FF4B4B?style=flat-square&logo=gradio&logoColor=white)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

Two **click-through front-ends** over the same verifiers the CLI uses —
pick a section, press run, watch the PASS ledger and the JSON verdict
appear. Ideal for a reviewer who wants to *see* the framework work before
reading a single line of the contract, and for classroom demonstrations of
the cross-language matrix.

## Contents

| File | Description |
|---|---|
| [`gradio_app.py`](gradio_app.py) | the Gradio front-end — section picker, live output pane |
| [`streamlit_app.py`](streamlit_app.py) | the Streamlit front-end — same verifiers, dashboard layout |
| [`requirements.txt`](requirements.txt) | pinned dependencies for both apps |

## How to run

```bash
pip install -r verification/demo/requirements.txt

gradio verification/demo/gradio_app.py        # or: python verification/demo/gradio_app.py
streamlit run verification/demo/streamlit_app.py
```

Both apps call the verifiers through
[`common/`](../common/README.md) — the same base class the
[REST API](../api/README.md) uses — so what you see in the browser is
byte-for-byte what CI asserts.

---

---

Navigation: [repository root](../../README.md) · [api](../api/README.md) · [common](../common/README.md) · [IPL-RP-1.0](../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

