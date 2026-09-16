# `.github/workflows/` — CI/CD Workflows

| Workflow | Trigger | What it does |
|---|---|---|
| [`ci.yml`](ci.yml) | push / PR to `main` | 4 jobs: **Lint (ruff)** — advisory; **Tests** — pytest on Python 3.11 & 3.12 (toolchain-locked tests auto-skip); **Verification smoke** — section 1 Python verification; **Manifest integrity** — sha256 of the whole tree against `MANIFEST.json` |
| [`pages.yml`](pages.yml) | push touching `site/` or `assets/` | deploys the tabbed project site to GitHub Pages |
| [`release.yml`](release.yml) | tag `v*` | regenerates `MANIFEST.json`, packs `navier-stokes-b-full.zip` and `-light.zip`, computes `SHA256SUMS.txt`, opens a draft GitHub release |

Badges for the first two are embedded in the root README; they go green on the first
push after enabling Actions (**Settings → Actions → General → Allow all actions**).

## Concurrency and caching

CI cancels superseded runs per ref (`concurrency.group = ci-${{ github.ref }}`); the
Pages workflow serializes deployments. No runner-side caches are required — the
scientific stack installs in under a minute.

---
Navigation: [.github](../README.md) · [repository root](../../README.md) · [IPL-RP-1.0](../../LICENSE.md)
