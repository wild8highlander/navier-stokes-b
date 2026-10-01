# `notebooks/` — the Jupyter entry point

> **Navigation:** [repository root](../README.md) › [verification](../README.md) › **`notebooks`**

![Jupyter](https://img.shields.io/badge/interactive-F37626?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

The interactive-exploration corner of the framework: launch Jupyter from
the repository root and import any reference port — the verifiers are
plain importable modules with a `main()` returning the exit code, so a
notebook cell can run a section and dissect its values.

```bash
pip install -r requirements.txt
jupyter lab
```

Suggested first cells:

```python
import subprocess, sys
r = subprocess.run([sys.executable,
    "verification/section7_smagorinsky_kolmogorov/python/verify.py"],
    capture_output=True, text=True)
print(r.stdout)
```

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../LICENSE.md)).
