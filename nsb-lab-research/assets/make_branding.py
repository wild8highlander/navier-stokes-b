#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_branding.py — logo + hero banner for the b-volume research repo."""

import math
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch

OUT = "/home/z/my-project/download/nsb-lab-research/assets"
os.makedirs(OUT, exist_ok=True)

C_DARK = "#121210"
C_GOLD = "#d5c080"
C_C1 = "#0F2440"
C_C2 = "#C25E00"
C_C3 = "#5B7C99"
C_C4 = "#3aa0c2"


def spiral(ax, cx, cy, r0, turns=2.6, color=C_GOLD, lw=2.2, alpha=1.0,
           n=400, phase=0.0):
    t = np.linspace(0, turns * 2 * math.pi, n)
    r = r0 * (0.16 + 0.84 * t / t.max())
    ax.plot(cx + r * np.cos(t + phase), cy + r * np.sin(t + phase),
            color=color, lw=lw, alpha=alpha, solid_capstyle="round")


def make_logo(path_svg=None, path_png=None):
    fig, ax = plt.subplots(figsize=(6.4, 6.4), constrained_layout=True)
    fig.patch.set_facecolor(C_DARK)
    ax.set_facecolor(C_DARK)
    ax.set_xlim(-1.15, 1.15)
    ax.set_ylim(-1.15, 1.15)
    ax.set_aspect("equal")
    ax.axis("off")
    # outer ring (the torus)
    ax.add_patch(Circle((0, 0), 1.0, fill=False, ec=C_C3, lw=3.0, alpha=0.9))
    ax.add_patch(Circle((0, 0), 0.865, fill=False, ec=C_C3, lw=1.0, alpha=0.45))
    # vortex spiral (the correction carrier)
    spiral(ax, 0, 0, 0.78, turns=2.7, color=C_GOLD, lw=3.0)
    spiral(ax, 0, 0, 0.60, turns=2.2, color=C_C2, lw=1.8, alpha=0.85,
           phase=math.pi * 0.8)
    # b-axis arrow through the vortex
    ax.add_patch(FancyArrowPatch((-0.95, -0.62), (0.95, 0.62),
                                 arrowstyle="-|>", mutation_scale=22,
                                 color=C_C4, lw=2.4, alpha=0.9))
    ax.annotate("", xy=(-0.95, -0.62), xytext=(-0.80, -0.52),
                arrowprops=dict(arrowstyle="-|>", color=C_C4, lw=2.4))
    # center glyph
    ax.text(0, 0.055, "b", ha="center", va="center", fontsize=64,
            color=C_DARK, fontweight="bold", family="DejaVu Serif",
            bbox=dict(boxstyle="circle,pad=0.28", fc=C_GOLD, ec=C_C3, lw=2.0))
    ax.text(0, -0.985, "θb = 3.5765°  ·  V₁ = 4π+2√3", ha="center", va="top",
            fontsize=10.5, color=C_GOLD, family="DejaVu Sans")
    if path_png:
        fig.savefig(path_png, dpi=200, facecolor=C_DARK)
    if path_svg:
        fig.savefig(path_svg, facecolor=C_DARK)
    plt.close(fig)


def make_banner(path):
    fig = plt.figure(figsize=(15.0, 5.0), constrained_layout=True)
    fig.patch.set_facecolor(C_DARK)
    ax = fig.add_subplot(111)
    ax.set_facecolor(C_DARK)
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 5)
    ax.axis("off")
    # left: vortex emblem
    ax.add_patch(Circle((2.2, 2.5), 1.55, fill=False, ec=C_C3, lw=2.6, alpha=0.9))
    spiral(ax, 2.2, 2.5, 1.2, turns=2.6, color=C_GOLD, lw=2.6)
    ax.text(2.2, 2.56, "b", ha="center", va="center", fontsize=42,
            color=C_DARK, fontweight="bold", family="DejaVu Serif",
            bbox=dict(boxstyle="circle,pad=0.22", fc=C_GOLD, ec=C_C3, lw=1.6))
    # right: title block
    ax.text(4.55, 3.72, "The b-Correction & the Vortex Volume",
            fontsize=27, color="#e2e1df", fontweight="bold",
            family="DejaVu Serif", va="center")
    ax.text(4.55, 2.95, "Поправка «б» и объём вихря — research monographs (RU · EN)",
            fontsize=13.5, color=C_GOLD, va="center")
    ax.text(4.55, 2.28,
            "What volume of water carries ONE b-correction?   "
            "b-charge B = ∫|n_b·ω|dV   ·   one kick flux Q_b = θ_b·B",
            fontsize=11.5, color="#8b8881", va="center")
    # key-result chips
    chips = [("12 experiments", "all PASS"),
             ("monitor Q/(θ_b·B)", "1 + O(θ_b)"),
             ("exact identity", "R² = 1.00000000"),
             ("Hou–Luo dynamics", "merge ↔ annihilate")]
    x = 4.55
    for big, small in chips:
        w = 2.42
        ax.add_patch(plt.Rectangle((x, 0.85), w, 1.0,
                                   fc="#1d1c18", ec=C_C3, lw=1.2))
        ax.text(x + w / 2, 1.52, big, fontsize=10.5, color=C_GOLD,
                ha="center", va="center")
        ax.text(x + w / 2, 1.10, small, fontsize=9.5, color="#8b8881",
                ha="center", va="center")
        x += w + 0.22
    fig.savefig(path, dpi=140, facecolor=C_DARK)
    plt.close(fig)


make_logo(os.path.join(OUT, "logo.svg"), os.path.join(OUT, "logo.png"))
make_banner(os.path.join(OUT, "banner.png"))
print("branding OK:", os.listdir(OUT))
