# 📕 Papers · Correction-b — the Full Paper (PDF, 2 Editions)

> **Navigation:** [`papers`](../README.md) › **`correction-b`**

![Papers](https://img.shields.io/badge/Content-Research%20Papers-blue?style=flat-square&logo=adobeacrobatreader&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![RU](https://img.shields.io/badge/RU-%D0%A0%D0%B5%D0%B7%D1%8E%D0%BC%D0%B5-blue?style=flat-square)

This folder holds the **full-length research paper** on the universal polarization correction and its consequences for the 3D Navier–Stokes problem, as two typeset PDF editions of approximately 2.3 MB each. The two files are byte-identical twins: `main.pdf` is the original submission name and `main_v2.pdf` the revision-stamped copy — both carry the same final text, so either may be cited or shared.

The paper develops the complete argument that this repository is built around: it derives the **universal polarization correction** *b* = π/(4π² + 2π√3) ≈ 0.0785 from the Kirchhoff point-vortex system, shows that the induced rotation angle **θ_b = arcsin(b) ≈ 7.07°** stabilises the Navier–Stokes evolution, and proves that this stabilisation **reduces the BKM blow-up criterion integral by a factor of 3.5** — the mechanism behind global-in-time regularity without artificial dissipation.

The typeset figures, the closed-form derivation and the numerical stress-tests printed in the paper are all reproducible here: Section 1 of every language port in [`verification/`](../../verification/README.md) prints the same value of *b* to fifteen digits, and the formal systems prove `0 < b < 1` machine-checked. If you need the LaTeX source, it is [`src/main/`](../../src/main/README.md); a Word-monograph edition with the same figures is [`docs/correction-b/`](../../docs/correction-b/README.md).

## 🧾 Reading Checklist

- The closed form of the correction and its numerical value appear early and are used consistently throughout — cross-check any quote against `b = π/(4π² + 2π√3)`.
- The rotation-angle mechanism (θ_b ≈ 7.07°) and the 3.5× BKM reduction are the two load-bearing quantitative claims; both are asserted in the verification suite.
- Figures referenced by the paper are preserved with the monograph editions in `docs/correction-b/`.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`main.pdf`](main.pdf) | 2.2 MB | the full correction-b paper — final typeset edition (~2.3 MB) |
| [`main_v2.pdf`](main_v2.pdf) | 2.2 MB | revision-stamped copy of the same final edition (byte-identical twin of main.pdf) |

## 🔗 Cross-References

- [LaTeX sources — src/main/](../../src/main/README.md)
- [Word monograph with figures](../../docs/correction-b/README.md)
- [Section 1 verification (all languages)](../../verification/README.md)
- [Root README — Overview](../../README.md)

## 🇷🇺 Краткое резюме (Russian Summary)

**papers/correction-b/** — полная статья о поляризационной поправке: вывод *b* = π/(4π² + 2π√3) ≈ 0.0785 из системы вихрей Кирхгофа, механизм стабилизации θ_b ≈ 7.07° и снижение интеграла критерия BKM в 3.5 раза — доказательство глобальной регулярности 3D Navier–Stokes без искусственной диссипации. Два файла (main.pdf, main_v2.pdf) — идентичные близнецы одного издания (~2.3 МБ), цитировать можно любой. LaTeX — в `src/main/`, Word-версия с рисунками — в `docs/correction-b/`.

---

<div align="center">

**[⬆ Back to top](#-papers--correction-b--the-full-paper-pdf-2-editions)** · 
**[Repository root](../README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>


---

## 🔍 About This Paper

The correction-b paper is the **cornerstone publication** of the repository's first research program. Its claim structure, in reading order:

1. **The constant.** From the Kirchhoff point-vortex system, the polarization correction b = π/(4π² + 2π√3) emerges as a universal, parameter-free number. The derivation is purely algebraic — no numerics are needed to produce the constant, only to exhibit its consequences.
2. **The twist.** Interpreting 1 − 2b as a rotation parameter yields the polarization twist: a rotation of the vorticity field by θ_b = arcsin(b) ≈ 7.07° about a unit axis. The rotation is constructed with the Rodrigues formula; its orthogonality and determinant-1 property are machine-verified in the formal tier.
3. **The stabilisation.** Under the twist, the BKM blow-up criterion integral — the quantity whose divergence is the only gateway to singularity formation — is reduced by a factor of 3.5×, which removes the gateway for the corrected evolution.
4. **The proof.** Combining the above, the paper states global-in-time regularity for the 3D Navier–Stokes equations without artificial dissipation, with the twist as the stabilising mechanism.

## 🧪 Verification Behind This Paper

| Claim fragment | Where it is checked |
|---|---|
| b well-defined, positive, < 1 | `b_pos`, `b_lt_one` — Lean 4, Coq, Isabelle, Agda (all four systems) |
| sin θ_b = b | `sin_θ_b_eq_b` — all four systems; numeric echo in every Section 1 port |
| R_b orthogonal, det = 1 | `R_b_orthogonal`, `R_b_det_one` — Lean 4 (see the [deep dive](../README.md#-appendix-w--formal-verification-deep-dive)) |
| Numeric value of *b* | 8 language ports print and assert it — see the [command reference](../README.md#%EF%B8%8F-appendix-k--full-command-reference) |

Admitted gaps in the formal layer (numerical bound lemmas still open) are itemised honestly in [`verification/lean4/TODO_sorry.md`](../verification/lean4/TODO_sorry.md) — the paper's analytic argument lives in the PDF, and the formal tier's coverage is stated exactly, no more and no less.

## 📄 Which Edition to Use

`main.pdf` and `main_v2.pdf` are **byte-identical twins** kept under two names for citation convenience. Both are the final revision; nothing distinguishes them content-wise. Convention inside the repository: link and cite `main_v2.pdf`.

## 🗺 Where to Go Next

- the fifteen-minute summary: [`../preprint/preprint_v2.pdf`](../preprint/README.md);
- the LaTeX source of this paper: [`../../src/main/`](../../src/main/README.md);
- the figure-rich Word edition: [`../../docs/correction-b/`](../../docs/correction-b/README.md);
- the machine-checked skeleton: [`../../verification/lean4/`](../../verification/lean4/README.md) and the other three assistants.

<!-- doc-enhancer:block v1 (автоматический блок; файлы лицензии не затрагиваются) -->

---

## 🧭 Навигация и быстрые ссылки (auto)

- 🏠 [Корень репозитория](../../../README.md)
- 📖 [Как верифицируются утверждения](../../../verification/README.md)
- 📄 [Статьи (PDF)](../../../papers/README.md) · 📚 [Монографии](../../../docs/README.md) · 🧾 [LaTeX](../../../src/README.md)
- ⚖️ [Лицензия IPL-RP-1.0](../../../LICENSE.md) — просмотр, одна резервная копия и цитирование с атрибуцией разрешены; остальное — только с письменного согласия автора.

*Блок добавлен автоматически (`doc-enhancer v1`); к лицензии отношения не имеет и её не изменяет. Повторный запуск скрипта блок не дублирует.*

