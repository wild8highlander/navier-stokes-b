"""make_formulas.py — render display formulas as PNGs (shared RU/EN).

Uses matplotlib mathtext (DejaVu) at 300 dpi with tight bounding boxes.
Output: monograph/assets/formula_<key>.png
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "monograph", "assets")
os.makedirs(OUT, exist_ok=True)

FORMULAS = {
    "f1_nse": r"\frac{\partial u_i}{\partial t} + \frac{\partial (u_i u_j)}{\partial x_j} = -\frac{1}{\rho}\frac{\partial p}{\partial x_i} + \nu \nabla^2 u_i, \qquad \frac{\partial u_i}{\partial x_i} = 0",  # noqa: E501
    "f2_k41": r"E(k) = C_K\, \varepsilon^{2/3}\, k^{-5/3}",
    "f3_four5": r"\langle (\delta u_L)^3 \rangle = -\frac{4}{5}\, \varepsilon\, r",
    "f4_eta": r"\eta = \left(\frac{\nu^3}{\varepsilon}\right)^{1/4}, \qquad k_\eta = \frac{1}{\eta}",  # noqa: E501
    "f5_nut": r"\nu_t = (C_s \Delta)^2\, |\bar{S}|, \qquad |\bar{S}| = (2\, \bar{S}_{ij}\bar{S}_{ij})^{1/2}",  # noqa: E501
    "f6_germano": r"L_{ij} = \widetilde{\overline{u}_i \overline{u}_j} - \widetilde{\overline{u}}_i\, \widetilde{\overline{u}}_j",  # noqa: E501
    "f7_eps_sgs": r"\varepsilon_{sgs} = -\langle \tau_{ij} \bar{S}_{ij} \rangle = (C_s \Delta)^2\, \langle |\bar{S}|^3 \rangle",  # noqa: E501
    "f8_strain_id": r"\langle |\bar{S}|^2 \rangle = 2 \int_0^{k_c} k^2 E(k)\, G^2(k)\, dk",
    "f9_strain_sharp": r"\langle |\bar{S}|^2 \rangle = \frac{3}{2}\, C_K\, \varepsilon^{2/3}\, k_c^{4/3}, \qquad k_c = \frac{\pi}{\Delta}",  # noqa: E501
    "f10_master": r"C_s \;=\; \frac{1}{\pi \, (3 C_K / 2)^{3/4}}",
    "f11_master_num": r"C_s = \frac{1}{\pi\,(3 \cdot 1.50/2)^{3/4}} = 0.17327",
    "f12_gauss": r"C_s = \left( C_K\, \Gamma\left(\frac{2}{3}\right) 12^{2/3} \right)^{-3/4} = 0.16967",  # noqa: E501
    "f13_heis_nut": r"\nu_T(k) = \alpha \int_k^{\infty} \sqrt{\frac{E(q)}{q^3}}\, dq",
    "f14_heis_bal": r"\varepsilon = 2\left(\nu + \nu_T(k)\right) \int_0^k q^2 E(q)\, dq",
    "f15_heis_spec": r"E_H(k) = \frac{\alpha^2}{4}\, \varepsilon^{1/4} \nu^{5/4}\, \chi^{-7} \left[1 + \frac{3\alpha^2}{8}\, \chi^{-4}\right]^{-4/3}, \quad \chi = k\eta",  # noqa: E501
    "f16_heis_ck": r"C_K(\alpha) = \left(\frac{8}{9\alpha}\right)^{2/3}, \qquad \alpha = \frac{8}{9\, C_K^{3/2}} = 0.4838",  # noqa: E501
    "f17_pao": r"E_P(k) = C_K\, \varepsilon^{2/3}\, k^{-5/3} \exp\left(-\beta (k\eta)^2\right), \qquad \beta = \left(C_K\, \Gamma\left(\frac{2}{3}\right)\right)^{3/2} = 2.895",  # noqa: E501
    "f18_apriori": r"C_s^2 = \frac{-\langle L_{ij} \bar{S}_{ij} \rangle}{\Delta^2\, \langle |\bar{S}|^3 \rangle}",  # noqa: E501
    "f19_dynamic": r"M_{ij} = 2\bar{\Delta}^2\left(\widetilde{|\bar{S}|\bar{S}_{ij}} - \alpha_d^2 |\tilde{S}|\tilde{S}_{ij}\right), \qquad C_s^2(x,t) = \frac{\langle L_{ij} M_{ij} \rangle}{\langle M_{ij} M_{ij} \rangle}",  # noqa: E501
    "f20_bcorr": r"b = \frac{1}{4\pi + 2\sqrt{3}} = 0.062381194\ldots",
    "f21_gauss_zero": r"\langle L_{ij} \bar{S}_{ij} \rangle = 0 \quad \mathrm{for\ Gaussian\ fields}",  # noqa: E501
    "f22_ek_int": r"\int_0^{\infty} E(k)\, dk = \frac{1}{2}\langle u_i u_i \rangle, \qquad \varepsilon = 2\nu \int_0^{\infty} k^2 E(k)\, dk",  # noqa: E501
    "f23_lps": r"\frac{2}{p} + \frac{3}{q} \leq 1, \quad u \in L^p_t L^q_x \;\Rightarrow\; \mathrm{regularity}",  # noqa: E501
    "f24_bkm": r"I_{BKM}(t) = \int_0^t \|\omega(\cdot, s)\|_{\infty}\, ds < \infty \;\Rightarrow\; \mathrm{regularity}",  # noqa: E501
    "f25_vort": r"\frac{d\Omega}{dt} = 2\langle \omega_i S_{ij} \omega_j \rangle - 2\nu \langle |\nabla \omega|^2 \rangle",  # noqa: E501
    "f26_etab": r"\eta_b = \left(\frac{\nu^3}{\varepsilon}\right)^{\frac{1}{6b-2}}, \qquad \beta_b = \left(\frac{C_K\, \Gamma\!\left(1 - \frac{1}{3b}\right)}{b}\right)^{\frac{b}{b - 1/3}}",  # noqa: E501
    "f27_xstar": r"k_d\, \eta_b = x^*(b) = \left[\frac{2b - 5/3}{2b\, \beta_b}\right]^{\frac{1}{2b}}",  # noqa: E501
    "f28_cert": r"E(k, t) \simeq A(t)\, e^{-c(t)\, k} \;\;\Rightarrow\;\; \mathrm{analytic\ smoothness}",  # noqa: E501
}


def render(key: str, latex: str) -> None:
    fig = plt.figure(figsize=(0.1, 0.1))
    fig.text(0.5, 0.5, f"${latex}$", fontsize=15, ha="center", va="center",
             color="#151513")
    path = os.path.join(OUT, f"formula_{key}.png")
    fig.savefig(path, dpi=300, bbox_inches="tight", pad_inches=0.06,
                facecolor="white", transparent=False)
    plt.close(fig)
    print(f"[formula] {path}")


if __name__ == "__main__":
    for k, v in FORMULAS.items():
        render(k, v)
    print(f"[formulas] {len(FORMULAS)} rendered -> {OUT}")
