# `code/python/` — The Executable Program (P1-P5)

| File | Stage | What it does |
|---|---|---|
| `sk_core.py` | library | conventions, Lilly relation, Heisenberg/Pao closures, fits |
| `p1_lilly.py` | P1 | master relation C_s(C_K), three filter families, Pao-tail sensitivity |
| `p2_closures.py` | P2 | Heisenberg closed-form spectrum, calibration alpha(C_K), Pao beta |
| `p3_synthetic_apriori.py` | P3 | Monte-Carlo spectral verification on 96^3 K41 fields |
| `p4_dns_les.py` | P4 | 3D pseudo-spectral DNS 48^3, a priori + dynamic Smagorinsky tests |
| `p5_regularity.py` | P5 | 3D smoothness: TG 48^3 BKM/LPS diagnostics, b-protocol, hyperdissipative family, spectral certificate; `--mini` writes the 16^3 cross-language run |
| `p5_crosscheck.py` | P5 | three-language cross-validation verdict (`p5_cross_language.json`) |
| `figures.py` | figures | all monograph figures, `python3 figures.py ru|en` |
| `run_all.py` | driver | `python3 run_all.py [p1 p2 p3 p4 p5 figures]` |
| `requirements.txt` | — | numpy, scipy, matplotlib |

Every stage writes a pinned JSON protocol (parameters + convention
statement + numbers + SHA-256 of its own source) into `../../results/`.
RNG seeds are fixed: P3 seed 20260929, P4 seed 424242.
