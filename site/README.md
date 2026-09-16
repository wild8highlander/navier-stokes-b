# `site/` — GitHub Pages Project Site

The tabbed project website served at
<https://wild8highlander.github.io/navier-stokes-b/> (deployed automatically by
[`.github/workflows/pages.yml`](../.github/workflows/pages.yml) on every push that
touches `site/` or `assets/`).

## Tabs

| Tab | Content |
|---|---|
| **Home** | one-screen pitch, key constants, entry points to the papers and quick start |
| **Results** | the headline table P1–P7 with the recorded numbers and the 50-digit constants |
| **Verification** | the seven verification methods and the 11-language matrix |
| **License** | the plain-terms summary of IPL-RP-1.0 with links to the authoritative texts |

## Files

| File | Purpose |
|---|---|
| `index.html` | the whole site — static, dependency-free, dark theme, keyboard-accessible tabs |
| `logo.svg` | the square mark (copy of [`assets/logo.svg`](../assets/README.md)) |
| `favicon.svg` | browser favicon |

## Local preview

Open `index.html` directly in a browser, or serve the folder:

```bash
python3 -m http.server 8000 --directory site
# open http://localhost:8000
```

Enabling Pages once: **Settings → Pages → Source: GitHub Actions**. The workflow
`pages.yml` then deploys on every push to `main`.

---
Navigation: [repository root](../README.md) · [assets](../assets/README.md) · [IPL-RP-1.0](../LICENSE.md)
