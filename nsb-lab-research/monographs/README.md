# 📚 `monographs/` — the b-volume research monographs (RU · EN · PDF · DOCX)

Four complete documents, **one shared verified content tree**: the full
theory of the b-charge — derivations, all twelve experiments, the
limitations-turned-into-checks chapter, the Kolmogorov bridge to real water
and the master table of numbers.

| Language | PDF | DOCX |
|---|---|---|
| 🇷🇺 **Русская** | [`Монография_Поправка_б_и_объём_вихря_RU.pdf`](RU/Монография_Поправка_б_и_объём_вихря_RU.pdf) | [`Монография_Поправка_б_и_объём_вихря_RU.docx`](RU/Монография_Поправка_б_и_объём_вихря_RU.docx) |
| 🇬🇧 **English** | [`Monograph_b_correction_and_vortex_volume_EN.pdf`](EN/Monograph_b_correction_and_vortex_volume_EN.pdf) | [`Monograph_b_correction_and_vortex_volume_EN.docx`](EN/Monograph_b_correction_and_vortex_volume_EN.docx) |

---

## What is inside (13 chapters + 2 appendices)

| § | Chapter (RU / EN) | Highlights |
|---|---|---|
| 1 | Введение / Introduction | the hypothesis → an operational theory; the headline numbers |
| 2 | Точная математика поправки / Exact mathematics | Rodrigues, Leray, and the **exact flux identity** with the +sin θ_b sign |
| 3 | Б-заряд / The b-charge | B = ∫\|n_b·ω\|dV, Q_b = θ_b·B, the monitor and its rigorous bound |
| 4 | Элементарный б-объём / Elementary b-volume | V₁ = 4π+2√3 ≈ 16.02 = 6.46% of the box; projected tube volume |
| 5 | Алгебра слияния / The merging algebra | additivity, annihilation, the L¹/L² orientation pair, SO(3) composition |
| 6 | Численная лаборатория / The numerical laboratory | pseudo-spectral RK4 + Leray + 2/3; determinism; the Julia mirror |
| 7 | Базовая серия / The base series | experiments T–F with verdicts |
| 8 | Расширенная батарея H/I/J/K / The extended battery | cross channels, convergence ladder, anchors, **Hou–Luo dynamics** |
| 9 | Монитор в аудит лаборатории / The monitor in the lab audit | v2.2.0 patches, self-test values, the i-factor trap |
| 10 | Мост к реальной воде / The bridge to real water | tea, pipe, Draupner, Katrina; three vorticity anchors |
| 11 | Ограничения → проверки / Limitations → checks | every limitation of v1 turned into a verification |
| 12 | Обсуждение / Discussion | superfluid circulation-quantization analogy; four testable predictions |
| 13 | Выводы / Conclusions | six numbered conclusions |
| A–B | Приложения / Appendices | reproducibility commands; the master table of all numbers |

**Specs**: A4, dark scholarly cover, clickable TOC, 13 figures, 11 tables,
~30 pages (PDF); the DOCX is generated from the *same* content blocks with
Word-native heading styles (refresh the TOC field on first open), tables and
embedded figures.

## Key numbers (identical in all four files)

```text
b  = 0.06238119412102824        θ_b = 3.5765°
V₁ = 4π + 2√3 ≈ 16.02  (6.4626% of the box)
B(Taylor–Green) = 118.638640    monitor = 0.999688
exact identity regression:  R² = 1.00000000  (5 states)
2-D dynamic monitor: 1.230112 (theory) = 1.230116 (measured)
Hou–Luo: dipole keeps 28.78% of B, co-rotating pair 62.96%
12/12 experiments PASS · seed 20260103 · Python + Julia
```

## Rebuild

```bash
python3 scripts/generate_monograph.py --lang both   # PDF + DOCX, RU + EN
```

The generator lives in the parent project's `scripts/` archive; it renders
the PDF body with ReportLab (TocDocTemplate + multiBuild), the cover with
the validated html2poster pipeline, and the DOCX with python-docx — all from
the two content modules `mono_<lang>_a.py` / `mono_<lang>_b.py`.
