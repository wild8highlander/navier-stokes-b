# `tools/` — support tooling of the verification framework

> **Navigation:** [repository root](../../README.md) › [verification](../README.md) › **`tools`**

![Tooling](https://img.shields.io/badge/Role-support_tooling-FF8C00?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

Supporting tools that operate *on* the verification framework rather than
re-deriving physics. Today it holds one subpackage:

- [`audit/`](audit/README.md) — the repository-integrity auditors
  (`audit_lean.py`, `verify_repo.py`), invoked by `make verify-repo` and
  by CI.

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../../LICENSE.md)).
