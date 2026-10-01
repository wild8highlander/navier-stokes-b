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

A ready-to-run starter notebook is included:
[`quickstart.ipynb`](quickstart.ipynb) runs the Section 1 verifier,
parses its JSON verdict, recomputes the constant `b` locally and plots
its geometric meaning. It locates the repository root automatically, so
it works no matter where Jupyter was launched from.

Suggested first cells:

```python
import subprocess, sys
r = subprocess.run([sys.executable,
    "verification/section1_correction_b/python/verify.py", "--preset", "default"],
    capture_output=True, text=True)
print(r.stdout)
```

(Or simply open `quickstart.ipynb`, which does this and more.)

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../LICENSE.md)).
