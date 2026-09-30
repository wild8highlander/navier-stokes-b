# `results/` — Pinned Protocols and Data

Every program writes a JSON protocol: full parameters, the convention
statement, headline numbers, per-sample rows and the SHA-256 of its own
source (`integrity.sha256_of_code`).

| File | Producer | Content |
|---|---|---|
| `p1_lilly.json` | Python P1 | master relation, filter family, Pao-tail sensitivity |
| `p1_lilly_table.csv` | Python P1 | C_s(C_K) table, three filters |
| `p2_closures.json` | Python P2 | Heisenberg calibration + Pao normalization |
| `p2_spectra.csv` | Python P2 | model spectra in Kolmogorov units |
| `p3_synthetic_apriori.json` | Python P3 | synthetic-field verification protocol |
| `p3_apriori.csv` | Python P3 | per-realization rows |
| `p1_cpp.json`, `p2_cpp.json`, `p3_cpp.json` | C++ track | cross-language references |
| `p1_p2_julia.json` | Julia track | cross-language reference |
| `p4_dns_les.json` | Python P4 | DNS protocol, Re_lambda, a priori + dynamic C_s |
| `p4_dns_spectrum.csv` | Python P4 | time-averaged DNS spectrum |
| `p4_apriori.csv` | Python P4 | per-snapshot a priori C_s |
| `p4_spectrum.npy`, `p4_vorticity_slice.npy` | Python P4 | figure data |
| `p5_regularity.json` | Python P5 | smoothness protocol: runs A/B, self-verification, b-family, b-protocol effect |
| `p5_bkm.csv` | Python P5 | E, Omega, ||w||_inf, I_BKM time series (runs A and B) |
| `p5_certificate.csv` | Python P5 | exponential/power-law tail fits + k_d per save point |
| `p5_bfamily.csv` | Python P5 | beta_b, eta_b, k_d*eta_b vs x*(b) table |
| `p5_spectra.npz` | Python P5 | shell spectra at t = 1..5 for fig9/fig10 |
| `p5_snapshot_u.f64`, `p5_snapshot_w.f64` | Python P5 | raw (u, omega) snapshot at T_end of run A |
| `p5_mini_python.json` | Python P5 | miniature 16^3 run for the cross-language check |
| `p5_cpp.json` | C++ track | P5 analytic block + snapshot diagnostics + mini-DNS |
| `p5_julia.json` | Julia track | P5 analytic block + snapshot diagnostics + mini-DNS |
| `p5_cross_language.json` | Python P5 | three-language verdict (analytic/snapshot/mini, PASS) |

Conventions (see parent README section 11): E(k) is the kinetic-energy
spectrum (int E dk = 1/2 <u^2>); the shell variance energy is e_shell =
2 E(k); eps = 2 nu int k^2 E dk = nu <omega^2>. The P5 protocol reports
E in the program convention E = sum e_shell = <u^2> = 2 E_kin (energy
balance dE/dt = -2 eps); the miniature cross-language runs use the
bias-free full-grid normalization (the kz = 0 plane counted once).
