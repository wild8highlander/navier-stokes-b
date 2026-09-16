# Security Policy

## Supported versions

The `main` branch is the only supported line. Every push to `main` is re-checked by CI
(lint, pytest, verification smoke, and the sha256 manifest integrity job), so the
latest commit is always the reference for integrity questions.

| Scope | Status |
|---|---|
| `main` | ✅ supported |
| tags `v*` (GitHub Releases) | ✅ supported (pinned archives + SHA256SUMS) |
| other branches / forks | ❌ not supported |

## What counts as a security issue here

This repository contains research code, not a production service. The following are
treated as security-relevant:

1. **Supply-chain integrity** — any way for a third party to alter `MANIFEST.json`,
   `SHA256SUMS`, release archives, or the CI workflows so that verification silently
   passes on modified content.
2. **Injection in the REST API** (`verification/api/`) and the web dashboard
   (`verification/web-dashboard/`) if they are run outside an isolated environment.
3. **Container escape or privilege escalation** in `verification/docker/`.
4. **Malicious content in notebooks** (`verification/notebooks/`).

## How to report

- Use GitHub **private vulnerability reporting**:
  <https://github.com/wild8highlander/navier-stokes-b/security/advisories/new>
- Alternatively contact the author directly through the GitHub profile
  [wild8highlander](https://github.com/wild8highlander).
- Please do **not** open a public issue for security reports.

Include: affected path, commit hash, reproduction steps, and impact assessment.

## What to expect

- Acknowledgment within **7 days**.
- A fix or mitigation, or a reasoned decision not to fix, within **30 days** for
  non-critical findings. Critical supply-chain issues are handled immediately
  (rotating tokens, re-pinning manifests, re-signing releases).

## Verification etiquette

If you discover that a published checksum does not match a file, verify your copy
first (`make verify-manifest`, compare `sha256sum` against `MANIFEST.json`), then
report. A mismatch between the manifest and GitHub `main` is always worth reporting.

---
© 2026 Isaev Iskhak Khamzatovich (wild8highlander). All Rights Reserved.
