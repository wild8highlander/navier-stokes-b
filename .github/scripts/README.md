# `.github/scripts/` — Repository Verification Scripts

Small dependency-free Python 3 scripts used by the Makefile and by CI.

| Script | Called by | Purpose |
|---|---|---|
| [`verify_manifest.py`](verify_manifest.py) | `make verify-manifest`, CI job *Manifest integrity* | recomputes sha256 of every file listed in `MANIFEST.json`; exit 1 on any missing/mismatched entry |
| [`regen_manifest.py`](regen_manifest.py) | `make manifest` | rewrites `MANIFEST.json` for the current tree (metadata preserved, `date` refreshed); run only after legit content changes |
| [`check_readmes.py`](check_readmes.py) | `make check-readmes` | docs hygiene: every directory has a README and no README contains Cyrillic (English-only policy) |

All three resolve paths relative to their own location, so they work from any working
directory and on any platform (Linux, macOS, Windows, Termux).

---
Navigation: [.github](../README.md) · [VERIFICATION.md](../../VERIFICATION.md) · [repository root](../../README.md) · [IPL-RP-1.0](../../LICENSE.md)
