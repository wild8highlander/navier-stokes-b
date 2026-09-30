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
| `p5_cross_language.json` | Python P5 | three-language verdict (analytic/snapshot/mini/P5-C stats, PASS) |
| `p5b_resolution_96.json` | Python P5-B | 96³ resolution study: convergence 48³ ↔ 96³, A96/H2-96 summaries, self-verification |
| `p5b_bkm_96.csv` | Python P5-B | E, Omega, \|\|w\|\|_inf, I_BKM time series at 96³ (runs A and H2) |
| `p5b_certificate_96.csv` | Python P5-B | exponential/power-law tail fits at 96³ (band [22, 32]) |
| `p5b_bfamily_96.csv` | Python P5-B | b = 2 row at 96³: k_d·η_b vs x*(b), k_max/η_b = 12.4 |
| `p5b_spectra_96.npz` | Python P5-B | 96³ shell spectra at t = 1..5 (fig11) |
| `p5b_snap_u_t4/t5/t6.f64`, `p5b_snap_u_t5_f32.npz` | Python P5-B | raw 96³ snapshots (DNS family of P5-C) + f32 pipeline check |
| `p5c_stretch_ensemble.json` | Python P5-C | stretching statistics: GAU(32)/SUR(8)/DNS families, verifications, cross-language reference |
| `p5c_pdfs.csv` | Python P5-C | PDFs of α and cos²θ_i per family (fig12) |
| `p5c_summary.csv` | Python P5-C | per-family scalar summary (⟨α⟩, β_S, cos²θ_i) |
| `p5c_gauss_ref_u.f64` | Python P5-C | raw Gaussian reference field 48³ (seed 20260929) |
| `p5c_tensors_dns.f64`, `p5c_tensors_gauss.f64` | Python P5-C | point-tensor artifacts (9 channels × 48³ f64) for C++/Julia |
| `p5c_cpp.json` | C++ track | P5-C tensor statistics recomputed in long double + GOE Monte-Carlo |
| `p5d_ensemble_dns.json` | Python P5-D | DNS ensemble protocol: 16 perturbed-TG runs (8 seeds x nu in {0.01, 0.005}, 64^3) + 96^3 resolution check, balances, aggregates |
| `p5d_ensemble_traces.csv` | Python P5-D | per-run traces (t, E, Omega, eps, \|\|w\|\|_inf, palinstrophy) of all 17 runs |
| `p5d_qr_topology.json` | Python P5-D | Q-R plane protocol: definitions, pooled joint PDFs per family, per-run scalar masses |
| `p5d_qr_pdfs.csv` | Python P5-D | pooled (r*, q*) joint PDFs per family (fig13) |
| `p5d_gau_sur_ext.json` | Python P5-D | GAU2 (M=64) + SUR2 (M=16) extension; pooled M=96 combination with P5-C |
| `p5d_tensors_dns.f64` | Python P5-D | point-tensor dump (9 channels x 64^3 f64) of the primary run for C++/Julia |
| `p5d_cpp.json` | C++ track | P5-D tensor statistics (strain block + Q-R block) recomputed in long double |
| `p5d_julia.json` | Julia track | P5-D tensor statistics recomputed in Julia |
| `p5d_cross_language.json` | cross-check | Python/C++/Julia deviations on the P5-D artifact, PASS/FAIL |
| `p5d_snap_u_<nu>_s<seed>_t5.npz` | Python P5-D | f32 t=5 snapshots of the 64^3 ensemble (16 files) |
| `p5d_trace_<tag>.npz`, `p5d_shard<k>.jsonl` | Python P5-D | per-run trace archives and shard checkpoints (regeneration support) |
| `p5c_julia.json` | Julia track | P5-C tensor statistics recomputed in Julia + GOE Monte-Carlo |

Conventions (see parent README section 11): E(k) is the kinetic-energy
spectrum (int E dk = 1/2 <u^2>); the shell variance energy is e_shell =
2 E(k); eps = 2 nu int k^2 E dk = nu <omega^2>. The P5 protocol reports
E in the program convention E = sum e_shell = <u^2> = 2 E_kin (energy
balance dE/dt = -2 eps); the miniature cross-language runs use the
bias-free full-grid normalization (the kz = 0 plane counted once).

Point-tensor artifacts (`p5c_tensors_*.f64`) are POINT-major C-order
`(n, n, n, 9)` with channels [Sxx, Syy, Szz, Sxy, Sxz, Syz, wx, wy, wz],
i.e. flat offset = channel + 9*point — C++ reads it row-major, Julia must
reshape `(9, N, N, N)` (column-major), not `(N, N, N, 9)`.
