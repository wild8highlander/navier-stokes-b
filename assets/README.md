# `assets/` — Brand and Visual Assets

SVG artwork of the project. The vortex mark encodes the essence of the work: a
velocity field winding into a vortex, the amber sector marking the b-correction
rotation angle θ_b on the outer orbit, and the amber arrow showing the direction of
the Rodrigues rotation — with **no energy injected**.

| File | Purpose | Used by |
|---|---|---|
| [`logo.svg`](logo.svg) | square mark (512×512) | root README footer, GitHub social previews |
| [`banner.svg`](banner.svg) | hero banner (1600×400) | root README header, project site |
| [`favicon.svg`](favicon.svg) | compact mark (64×64) | [site/](../site/README.md) favicon |

The assets are plain, script-generated SVG (see the `scripts/make_logo_svg.py` in the
author's toolchain): no raster layers, no embedded fonts, and they render identically
in README `<img>` tags and on the Pages site.

---
Navigation: [repository root](../README.md) · [project site](../site/README.md) · [IPL-RP-1.0](../LICENSE.md)
