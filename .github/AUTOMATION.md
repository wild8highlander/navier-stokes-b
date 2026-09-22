# `.github/` — Repository Automation and Community Files

Everything GitHub-specific: CI workflows, issue/PR templates, community health files
and the small verification scripts CI relies on.

| Path | Purpose |
|---|---|
| [`workflows/ci.yml`](workflows/README.md) | lint + pytest matrix + verification smoke + sha256 manifest integrity |
| [`workflows/pages.yml`](workflows/README.md) | deploys [`site/`](../site/README.md) to GitHub Pages |
| [`workflows/release.yml`](workflows/README.md) | on tags `v*`: regenerates the manifest, packs full/light archives, publishes a draft release with `SHA256SUMS.txt` |
| [`ISSUE_TEMPLATE/`](ISSUE_TEMPLATE/) | bug report, feature request and verification request forms |
| [`PULL_REQUEST_TEMPLATE.md`](PULL_REQUEST_TEMPLATE.md) | the reproducibility checklist every PR must satisfy |
| [`CODEOWNERS`](CODEOWNERS) | default reviewer (@wild8highlander) |
| [`dependabot.yml`](dependabot.yml) | monthly dependency updates (pip, cargo, GitHub Actions) |
| [`FUNDING.yml`](FUNDING.yml) | sponsor links and author profiles |
| [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) | Minimal Meritocracy code of conduct |
| [`scripts/`](scripts/README.md) | `verify_manifest.py`, `regen_manifest.py`, `check_readmes.py` |

Enable once after the first push: **Settings → Actions → General** (allow Actions),
**Settings → Pages → Source: GitHub Actions**, and **Settings → General → Discussions**
if the community tab is desired.

---
Navigation: [repository root](../README.md) · [VERIFICATION.md](../VERIFICATION.md) · [IPL-RP-1.0](../LICENSE.md)
