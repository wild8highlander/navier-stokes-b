# `scripts/` — shell entry points

> **Navigation:** [repository root](../README.md) › [verification](../README.md) › **`scripts`**

![Shell](https://img.shields.io/badge/bash-4EAA25?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

| Script | Effect |
|---|---|
| `run_cross_validation.sh` | runs the cross-validation battery: the section ports and the comparison report |
| `start_api.sh` | installs the API requirements (if needed) and launches `uvicorn` on the verification API |

Both scripts are idempotent and safe to re-run; they are the non-Makefile
entry points for environments where `make` is unavailable (Termux ships
make, but a bare busybox may not).

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../LICENSE.md)).
