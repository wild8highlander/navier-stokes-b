# `demo/` — interactive front-ends

> **Navigation:** [repository root](../README.md) › [verification](../README.md) › **`demo`**

![Gradio](https://img.shields.io/badge/gradio_app.py-FF4B4B?style=flat-square) ![Streamlit](https://img.shields.io/badge/streamlit_app.py-FF4B4B?style=flat-square) ![Sections](https://img.shields.io/badge/1%E2%80%937-2B579A?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

Two thin interactive front-ends over the same verifiers — pick a section,
press run, watch the real `[PASS]`/`[FAIL]` lines and the JSON verdict
arrive from the actual subprocess. They are honest wrappers: nothing is
pre-computed, nothing is cached, every click re-runs the port.

| File | Stack | Run |
|---|---|---|
| `gradio_app.py` | Gradio | `pip install -r requirements.txt && python gradio_app.py` |
| `streamlit_app.py` | Streamlit | `pip install -r requirements.txt && streamlit run streamlit_app.py` |

Both expose the section registry 1–7 (including the Smagorinsky–Kolmogorov
master relation) and print the contract output verbatim.

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../LICENSE.md)).
