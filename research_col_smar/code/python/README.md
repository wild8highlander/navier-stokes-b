# `code/python/` — The Executable Program (P1-P5)

| File | Stage | What it does |
|---|---|---|
| `sk_core.py` | library | conventions, Lilly relation, Heisenberg/Pao closures, fits |
| `p1_lilly.py` | P1 | master relation C_s(C_K), three filter families, Pao-tail sensitivity |
| `p2_closures.py` | P2 | Heisenberg closed-form spectrum, calibration alpha(C_K), Pao beta |
| `p3_synthetic_apriori.py` | P3 | Monte-Carlo spectral verification on 96^3 K41 fields |
| `p4_dns_les.py` | P4 | 3D pseudo-spectral DNS 48^3, a priori + dynamic Smagorinsky tests |
| `p5_regularity.py` | P5 | 3D smoothness: TG 48^3 BKM/LPS diagnostics, b-protocol, hyperdissipative family, spectral certificate; `--mini` writes the 16^3 cross-language run |
| `p5b_resolution_96.py` | P5-B | resolution study: run A + H2 (b=2) repeated at 96^3, checkpointed; pairwise 48^3 ↔ 96^3 convergence of every diagnostic |
| `p5c_stretch_ensemble.py` | P5-C | vortex stretching statistics: GAU(32) / SUR(8) / DNS(3) families at 96^3; `--export-tensors` writes the point-tensor artifacts for C++/Julia |
| `p5_crosscheck.py` | P5 | three-language cross-validation verdict (`p5_cross_language.json`), incl. the P5-C tensor-statistics block |
| `p5d_qr_ensemble.py` | P5-D | extended ensemble + Q-R topology: 16 perturbed-TG DNS (64^3, 8 seeds x 2 nu) + 96^3 check, GAU2(64)/SUR2(16), Chong-Perry-Cantwell invariants, Vieillefosse tail; phases dns/gausur/qr96/protocol, shardable, JSONL checkpoints |
| `p5d_crosscheck.py` | P5-D | three-language cross-validation on the P5-D tensor dump (`p5d_cross_language.json`) |
| `figures.py` | figures | all monograph figures, `python3 figures.py ru|en` |
| `run_all.py` | driver | `python3 run_all.py [p1 p2 p3 p4 p5 figures]` |
| `requirements.txt` | — | numpy, scipy, matplotlib |

Every stage writes a pinned JSON protocol (parameters + convention
statement + numbers + SHA-256 of its own source) into `../../results/`.
RNG seeds are fixed: P3 seed 20260929, P4 seed 424242, P5-C seeds
20260929 (reference field), 20260930 (Gaussian ensemble), 20261001
(surrogates); P5-D seeds 20261101-20261108 (DNS ensemble), 20261201
(GAU2), 20261202 (SUR2).
