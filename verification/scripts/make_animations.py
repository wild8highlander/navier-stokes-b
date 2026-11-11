#!/usr/bin/env python3
"""make_animations.py — регенератор слоя движущихся фигур assets/animations/.

Каждая анимация производится реальной математикой, а не иллюстрацией:

  anim_b_rotation          точная форма Родрига: поле на сфере поворачивается
                           пошагово на θ_b = arcsin(b) вокруг ω̂ = ẑ;
                           ‖u′‖ = ‖u‖ на каждом шаге (энергетическая нейтральность);
  anim_kdv_collision       точное двухсолитонное решение Хироты KdV
                           u = 2 ∂²ₓ ln F, столкновение без изменения формы;
  anim_taylor_green        реальный псевдоспектральный решатель verification/
                           code/tg2d_core.py (N = 96, ν = 10⁻³, RK4, 2/3 через
                           3/2-паддинг, проекция Лерэ) — затухание решётки
                           Тейлора–Грина, цвет = завихренность;
  anim_spectrum_cascade    оболочечный спектр E(k, t) того же прогона против
                           референсных наклонов k⁻⁵/³ и k⁻³;
  anim_rayleigh_benard     конвекция Рэлея–Бенара на ядре verification/code/
                           p3_buoyancy.py (те же уравнения P3: ψ–ω, Буссинеск,
                           свободное скольжение, Gr·Pr = 7.1·10⁵) в
                           визуальном разрешении; цвет = температура, живой
                           счётчик Nu_hot;
  anim_vortex_filaments    вихревые филаменты (§27b): сегментный Био–Савар с
                           блоб-ядром ε² = ε₀² + 4νt, RK4, прыжки двух колец
                           друг сквозь друга (leapfrog);
  anim_layered_braking     слоистое торможение (§27): dΓ_i/dt = −b_i Γ_i / T,
                           τ = −Σ b_i Γ_i, лог-декремент против mean(b).

Все прогоны детерминированы (фиксированные зерна), идемпотентны и
перезаписывают свои файлы. Рендер — matplotlib + PillowWriter (GIF89a),
без внешних зависимостей сверх scientific stack из environment.yml.

Использование:
    python3 make_animations.py                    # все анимации
    python3 make_animations.py --only b_rotation,kdv_collision
    python3 make_animations.py --list
    python3 make_animations.py --outdir /tmp/anim --fps 10

Выход: [PASS]/[FAIL] на каждую анимацию (кадры, размер, небелая доля) и
финальная строка `JSON: {...}`; код возврата 0 только при полном успехе.
"""
import argparse
import json
import math
import sys
import time
from pathlib import Path

import matplotlib
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.colors import LinearSegmentedColormap

matplotlib.use("Agg")

HERE = Path(__file__).resolve().parent          # verification/scripts/
VER = HERE.parent                               # verification/
REPO = VER.parent                               # repository root
CODE = VER / "code"
sys.path.insert(0, str(CODE))

OUT_DEFAULT = REPO / "assets" / "animations"

# ── палитра репозитория (тёмная тема charts/brand) ────────────────────────
BG    = "#0d1117"
PANEL = "#161b22"
FG    = "#e6edf3"
GRID  = "#30363d"
BLUE, AMBER, GREEN, PURPLE, RED, CYAN = (
    "#58a6ff", "#ffb13b", "#3fb950", "#bc8cff", "#f85149", "#39c5cf")

fm.fontManager.addfont("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")

plt.rcParams.update({
    "font.sans-serif": ["DejaVu Sans"], "text.color": FG,
    "axes.edgecolor": GRID, "axes.labelcolor": FG, "axes.facecolor": PANEL,
    "xtick.color": FG, "ytick.color": FG, "grid.color": GRID,
    "figure.facecolor": BG, "savefig.facecolor": BG,
    "axes.grid": False, "mathtext.fontset": "dejavusans",
})

CMAP_VORT = LinearSegmentedColormap.from_list(
    "nsb_div", [BLUE, "#0d1117", AMBER])
CMAP_TEMP = LinearSegmentedColormap.from_list(
    "nsb_heat", ["#1a1040", "#7c3aed", AMBER, "#ffe8b0"])


def _style_ax(ax):
    ax.set_facecolor(PANEL)
    for s in ax.spines.values():
        s.set_color(GRID)


def _footer(fig, text):
    fig.text(0.5, 0.012, text, ha="center", fontsize=7.5, color="#8b949e")


def _save_gif(fig, anim, path: Path, fps: int) -> None:
    anim.save(path, writer=PillowWriter(fps=fps))
    plt.close(fig)


def _check_gif(path: Path) -> tuple[bool, str]:
    """Кадры, длительность кадра, размер и небелая доля первого кадра."""
    from PIL import Image
    im = Image.open(path)
    n = getattr(im, "n_frames", 1)
    im.seek(0)
    g = im.convert("L")
    h = g.histogram()
    nonwhite = 1 - h[255] / max(sum(h), 1)
    ok = n > 0 and path.stat().st_size > 10_000 and nonwhite > 0.05
    return ok, f"frames={n}, bytes={path.stat().st_size}, non-white={nonwhite:.2f}"


# ═══════════════════════════════════════════════════════════════════════════
# 1. Точное вращение Родрига на θ_b
# ═══════════════════════════════════════════════════════════════════════════
def anim_b_rotation(outdir: Path, fps: int = 12, steps: int = 40):
    b = 1.0 / (4 * math.pi + 2 * math.sqrt(3))
    theta_b = math.asin(b)
    rng = np.random.default_rng(20260916)
    # точки на сфере + тангенциальные поля (perp к радиусу)
    n_pts = 220
    v = rng.normal(size=(n_pts, 3))
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    tang = rng.normal(size=(n_pts, 3))
    tang -= v * (v * tang).sum(1, keepdims=True)
    tang /= np.linalg.norm(tang, axis=1, keepdims=True)

    def rodrigues(u, th):
        """u' = u cosθ + (ω̂×u) sinθ + ω̂(ω̂·u)(1−cosθ), ω̂ = ẑ — точная форма."""
        x, y, z = u[:, 0], u[:, 1], u[:, 2]
        wxu = np.stack([-y, x, np.zeros_like(x)], axis=1)
        wz = np.stack([np.zeros_like(x), np.zeros_like(x), z], axis=1)
        return u * math.cos(th) + wxu * math.sin(th) + wz * (1 - math.cos(th))

    frames, errs, angles = [], [], []
    base_pts, base_vec = v.copy(), tang.copy()
    for k in range(steps + 1):
        ang = k * theta_b
        pts, vecs = rodrigues(base_pts, ang), rodrigues(base_vec, ang)
        rel = np.abs(np.linalg.norm(vecs, axis=1) - 1).max()
        frames.append((pts.copy(), vecs.copy(), ang))
        errs.append(rel)
        angles.append(ang)

    fig = plt.figure(figsize=(8.6, 5.4), dpi=110)
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor(BG)
    txt1 = ax.text2D(0.02, 0.95, "", transform=ax.transAxes, fontsize=11,
                     family="monospace", color=AMBER)
    txt2 = ax.text2D(0.02, 0.90, "", transform=ax.transAxes, fontsize=9,
                     family="monospace", color=GREEN)
    ax.set_axis_off()
    ax.set_box_aspect((1, 1, 1))

    # каркас сферы
    ph = np.linspace(0, 2 * np.pi, 40)
    for zz in (-0.6, -0.2, 0.2, 0.6):
        r = math.sqrt(max(1 - zz * zz, 0))
        ax.plot(r * np.cos(ph), r * np.sin(ph), zz, color=GRID, lw=0.6,
                alpha=0.6, zorder=1)
    ax.text2D(0.72, 0.04, "ω̂ = ẑ", transform=ax.transAxes,
              fontsize=10, color=CYAN)

    pts0, vecs0, _ = frames[0]
    q = ax.quiver(pts0[:, 0], pts0[:, 1], pts0[:, 2], vecs0[:, 0],
                  vecs0[:, 1], vecs0[:, 2], color=BLUE, lw=1.1, zorder=3)
    sc = ax.scatter(pts0[:, 0], pts0[:, 1], pts0[:, 2], c=np.ones(len(pts0)),
                    cmap="viridis", s=6, zorder=2)

    def update(i):
        pts, vecs, ang = frames[i]
        segs = [((p[0], p[1], p[2]),
                 (p[0] + 0.22 * v[0], p[1] + 0.22 * v[1], p[2] + 0.22 * v[2]))
                for p, v in zip(pts, vecs)]
        q.set_segments(segs)
        sc._offsets3d = (pts[:, 0], pts[:, 1], pts[:, 2])
        sc.set_array(np.linalg.norm(vecs, axis=1))
        k = i
        txt1.set_text(f"step {k:02d} · Σθ = {math.degrees(angles[k]):7.3f}°"
                      f" = {k} × θ_b")
        txt2.set_text(f"max |‖u′‖ − ‖u‖| = {errs[k]:.1e}")
        return q, sc, txt1, txt2

    anim = FuncAnimation(fig, update, frames=len(frames), blit=False,
                         interval=1000 // fps)
    path = outdir / "anim_b_rotation.gif"
    _save_gif(fig, anim, path, fps)
    return path, (f"exact Rodrigues form, {steps} steps of "
                  f"θ_b = {math.degrees(theta_b):.7f}°, seed 20260916")


# ═══════════════════════════════════════════════════════════════════════════
# 2. Точное столкновение двух солитонов КдВ (Хирота)
# ═══════════════════════════════════════════════════════════════════════════
def anim_kdv_collision(outdir: Path, fps: int = 16, n_frames: int = 96):
    k1, k2 = 2.0, 1.0            # быстрые высокие против медленных низких
    d1, d2 = -34.0, -12.0
    a12 = ((k1 - k2) / (k1 + k2)) ** 2

    def u_exact(x, t):
        e1 = np.exp(k1 * (x - k1 * k1 * t) + d1)
        e2 = np.exp(k2 * (x - k2 * k2 * t) + d2)
        f = 1 + e1 + e2 + a12 * e1 * e2
        # u = 2 (ln F)'' — через численно точную вторую производную по x:
        # ln F = ln F; (ln F)' = F'/F; (ln F)'' = F''/F − (F'/F)²
        e1x, e2x = k1 * e1, k2 * e2
        fx, fxx = e1x + e2x, k1 * e1x + k2 * e2x
        return 2 * (fxx / f - (fx / f) ** 2)

    x = np.linspace(-30, 30, 1200)
    t_max = 15.0
    ts = np.linspace(0, t_max, n_frames)

    fig, ax = plt.subplots(figsize=(8.6, 5.0), dpi=110)
    fig.subplots_adjust(bottom=0.16, top=0.9, left=0.09, right=0.97)
    _style_ax(ax)
    ax.set_xlim(x[0], x[-1])
    ax.set_ylim(-0.35, 3.0)
    ax.set_xlabel("x")
    ax.set_ylabel("u(x, t)")
    ax.grid(alpha=0.35, lw=0.4)
    (line,) = ax.plot([], [], color=AMBER, lw=2.0)
    txt = ax.text(0.02, 0.93, "", transform=ax.transAxes, fontsize=10,
                  family="monospace")
    ax.axhline(0.0, color=GRID, lw=0.6)
    ax.text(0.985, 0.86, "u = 2 ∂²ₓ ln F\nF = 1 + e^{η₁} + e^{η₂} + A₁₂e^{η₁+η₂}",
            transform=ax.transAxes, ha="right", fontsize=8.5, color="#8b949e")

    def update(i):
        t = ts[i]
        u = u_exact(x, t)
        line.set_data(x, u)
        amp1 = k1 * k1 / 2
        amp2 = k2 * k2 / 2
        x1 = k1 * k1 * t - d1 / k1
        x2 = k2 * k2 * t - d2 / k2
        txt.set_text(f"t = {t:5.2f}   peaks: {amp1:.1f} @ x≈{x1:6.1f}, "
                     f"{amp2:.1f} @ x≈{x2:6.1f}  (амплитуды неизменны)")
        return line, txt

    anim = FuncAnimation(fig, update, frames=n_frames, blit=False,
                         interval=1000 // fps)
    path = outdir / "anim_kdv_collision.gif"
    _save_gif(fig, anim, path, fps)
    return path, ("exact Hirota two-soliton of KdV, closed form "
                  "u = 2 ∂²ₓ ln F, 96 frames")


# ═══════════════════════════════════════════════════════════════════════════
# 3–4. Тейлор–Грин (реальный решатель tg2d_core) + спектр того же прогона
# ═══════════════════════════════════════════════════════════════════════════
def _tg_run(n=96, nu=1e-3, dt=0.01, t_end=4.0, cb_every=10):
    from tg2d_core import TG2D
    solver = TG2D(n, nu, dt, b_rotation=False)
    wh = solver.init_taylor_green()
    vort_frames, t_list, e_list, wh_frames = [], [], [], []

    def cb(wh_now, t_now):
        om = np.fft.irfftn(solver.curl_h(wh_now), s=(n, n))
        vort_frames.append(om)
        t_list.append(t_now)
        e_list.append(0.5 * float((np.fft.irfftn(wh_now, s=(n, n)) ** 2).sum()) / n**2)
        wh_frames.append(wh_now.copy())

    solver.integrate(wh, t_end, callback=cb, cb_every=cb_every)
    return vort_frames, t_list, e_list, wh_frames, solver


def anim_taylor_green(vort_frames, t_list, e_list, n, outdir: Path,
                      fps: int = 10):
    fig, ax = plt.subplots(figsize=(7.4, 6.0), dpi=100)
    fig.subplots_adjust(left=0.06, right=0.88, top=0.9, bottom=0.08)
    om0 = vort_frames[0]
    vmax = float(np.abs(om0).max())
    im = ax.imshow(om0.T, origin="lower", cmap=CMAP_VORT, vmin=-vmax,
                   vmax=vmax, extent=[0, 2 * np.pi, 0, 2 * np.pi],
                   interpolation="bilinear")
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
    cb.set_label("vorticity ω", color=FG)
    cb.ax.yaxis.set_tick_params(color=FG)
    plt.setp(cb.ax.get_yticklabels(), color=FG)
    txt = ax.text(0.03, 0.955, "", transform=ax.transAxes, fontsize=10.5,
                  family="monospace", color=FG,
                  bbox=dict(boxstyle="round", fc=BG, ec=GRID, alpha=0.85))
    ax.set_title("2D Taylor–Green decay — pseudo-spectral solver tg2d_core.py"
                 f" (N = {n}, ν = 10⁻³, RK4, 2/3 dealiasing, Leray)",
                 fontsize=10, color=FG, pad=10)

    def update(i):
        im.set_data(vort_frames[i].T)
        txt.set_text(f"t = {t_list[i]:5.2f}    E = {e_list[i]:.5f}")
        return im, txt

    anim = FuncAnimation(fig, update, frames=len(vort_frames), blit=False,
                         interval=1000 // fps)
    path = outdir / "anim_taylor_green.gif"
    _save_gif(fig, anim, path, fps)
    return path, (f"real pseudo-spectral solver (N = {n}, ν = 10⁻³, RK4, "
                  f"2/3-dealiasing, Leray projection), {len(vort_frames)} frames")


def anim_spectrum_cascade(wh_frames, t_list, solver, outdir: Path,
                          fps: int = 12):
    k0, k1 = solver.k0, solver.k1
    kk = np.sqrt(k0**2 + k1**2)
    n = wh_frames[0].shape[1]
    kb = np.arange(1, n // 2)
    idx = np.digitize(kk.ravel(), kb)

    def shell(wh):
        e2 = 0.5 * (np.abs(wh[0]) ** 2 + np.abs(wh[1]) ** 2) / n**2
        cnt = np.bincount(idx, minlength=len(kb) + 1)
        tot = np.bincount(idx, weights=e2.ravel(), minlength=len(kb) + 1)
        return kb, np.where(cnt > 0, tot / np.maximum(cnt, 1), np.nan)[1:]

    fig, ax = plt.subplots(figsize=(8.6, 5.4), dpi=110)
    fig.subplots_adjust(bottom=0.14, top=0.9, left=0.09, right=0.97)
    _style_ax(ax)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(1, n // 2)
    ax.set_ylim(1e-12, 1e1)
    ax.set_xlabel("wavenumber k")
    ax.set_ylabel("E(k, t)")
    ax.grid(alpha=0.35, lw=0.4, which="both")
    kk_ref = np.array([2.0, 24.0])
    ax.plot(kk_ref, 0.35 * kk_ref ** (-5 / 3), "--", color=GREEN, lw=1.2,
            label="k⁻⁵ᐟ³ (Kolmogorov)")
    ax.plot(kk_ref, 0.02 * kk_ref ** (-3), "--", color=PURPLE, lw=1.2,
            label="k⁻³ (2D enstrophy)")
    sel = list(range(0, len(wh_frames), 4))   # плотнее: цикл заметно длиннее
    if sel[-1] != len(wh_frames) - 1:
        sel.append(len(wh_frames) - 1)
    lines = []
    for j, i in enumerate(sel):
        (ln,) = ax.plot([], [], lw=1.4,
                        color=plt.cm.cool(j / max(len(sel) - 1, 1)))
        lines.append(ln)
    txt = ax.text(0.02, 0.93, "", transform=ax.transAxes, fontsize=10,
                  family="monospace")
    ax.legend(loc="lower left", fontsize=8.5, framealpha=0.15,
              labelcolor=FG)

    def update(j):
        kbv, ev = shell(wh_frames[sel[j]])
        for m, ln in enumerate(lines):
            if m <= j:
                kbm, evm = shell(wh_frames[sel[m]])
                ln.set_data(kbm, evm)
        txt.set_text(f"t = {t_list[sel[j]]:5.2f}")
        return *lines, txt

    anim = FuncAnimation(fig, update, frames=len(sel), blit=False,
                         interval=1000 // fps)
    path = outdir / "anim_spectrum_cascade.gif"
    _save_gif(fig, anim, path, fps)
    return path, ("shell spectrum E(k, t) of the same tg2d_core run against "
                  "the k⁻⁵ᐟ³ and k⁻³ reference slopes")


# ═══════════════════════════════════════════════════════════════════════════
# 5. Рэлей–Бенар (реальное ядро p3_buoyancy, визуальное разрешение)
# ═══════════════════════════════════════════════════════════════════════════
def anim_rayleigh_benard(outdir: Path, fps: int = 12, n_frames: int = 72):
    import p3_buoyancy as p3
    # параметры зарегистрированного протокола P3 (уравнения те же):
    # Gr·Pr = 7.1e5, Pr = 0.71, Nz = 144 (dz ≈ 0.007 — тепловой погранслой
    # δ ≈ Ra^(-1/3) ≈ 0.011 разрешён), dt = 1.5e-6, гипервязкость против
    # алиасинга; NX умеренный ради скорости рендера
    p3.NX, p3.NZ, p3.DT, p3.NU4 = 48, 144, 1.5e-6, 3.0e-6
    steps_per_frame = 700                    # 72 кадра × 700 = T ≈ 0.0756
    rb = p3.RB(b_rotation=False, seed=7)
    frames = [(rb.th.copy(), rb.nusselt_hot())]
    steps_total = n_frames * steps_per_frame
    rb.step(0)                               # старт Эйлером (по протоколу P3)
    for s in range(1, steps_total + 1):
        rb.step(s)
        if s % steps_per_frame == 0:
            frames.append((rb.th.copy(), rb.nusselt_hot()))
    cfl = rb.cfl_max

    fig, ax = plt.subplots(figsize=(8.6, 5.2), dpi=110)
    fig.subplots_adjust(left=0.06, right=0.88, top=0.88, bottom=0.1)
    th0, nu0 = frames[0]
    im = ax.imshow(th0.T, origin="lower", cmap=CMAP_TEMP, vmin=0, vmax=1,
                   extent=[0, 2.0, 0, 1.0], aspect="auto",
                   interpolation="bilinear")
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
    cb.set_label("temperature θ", color=FG)
    plt.setp(cb.ax.get_yticklabels(), color=FG)
    txt = ax.text(0.02, 0.93, "", transform=ax.transAxes, fontsize=10.5,
                  family="monospace", color=AMBER,
                  bbox=dict(boxstyle="round", fc=BG, ec=GRID, alpha=0.85))
    ax.set_title("Rayleigh–Bénard convection — the P3 equations "
                 "(ψ–ω Boussinesq, free-slip, Gr·Pr = 7.1·10⁵, Pr = 0.71)",
                 fontsize=10, color=FG, pad=10)
    ax.set_xlabel("x")
    ax.set_ylabel("z")

    def update(i):
        th, nu = frames[i]
        im.set_data(th.T)
        txt.set_text(f"t = {i * steps_per_frame * p3.DT:7.4f}    "
                     f"Nu_hot = {nu:6.3f}    CFL ≤ {cfl:.3f}")
        return im, txt

    anim = FuncAnimation(fig, update, frames=len(frames), blit=False,
                         interval=1000 // fps)
    path = outdir / "anim_rayleigh_benard.gif"
    _save_gif(fig, anim, path, fps)
    return path, ("the registered P3 equations (ψ–ω Boussinesq, AB2+Euler, "
                  "free-slip, Nz = 144, dt = 1.5e-6), "
                  f"{len(frames)} frames, CFL ≤ {cfl:.3f}")


# ═══════════════════════════════════════════════════════════════════════════
# 6. Вихревые филаменты (§27b): сегментный Био–Савар + RK4, leapfrog колец
# ═══════════════════════════════════════════════════════════════════════════
def anim_vortex_filaments(outdir: Path, fps: int = 12, n_frames: int = 64,
                          n_nodes: int = 24):
    nu = 2.0e-3
    eps0 = 0.15
    dt = 0.02
    gamma = 1.0
    t_end = n_frames * 4 * dt          # кадр каждые 4 шага

    # два кольца радиуса 1 в плоскости y–z, ось x, начальный разнос ±0.6
    phi = np.linspace(0, 2 * np.pi, n_nodes, endpoint=False)
    ring = np.stack([np.zeros_like(phi), np.cos(phi), np.sin(phi)], axis=1)
    x1 = ring.copy()
    x1[:, 0] += 0.6
    x2 = ring.copy()
    x2[:, 0] -= 0.6
    filaments = [x1, x2]

    def biot_savart(points, segs_all, eps2):
        """u(p) = Γ/(4π) Σ dl×r/(|r|²+ε²)^{3/2}; сегменты без самовлияния
        собственного узла (ближайший сегмент исключается по индексу)."""
        vel = np.zeros_like(points)
        for f_idx, segs in enumerate(segs_all):
            a = segs
            b = np.roll(segs, -1, axis=0)
            dl = b - a
            mid = 0.5 * (a + b)
            for i, p in enumerate(points):
                r = p - mid
                r2 = (r * r).sum(1) + eps2
                same = np.zeros(len(mid), bool)
                same[(i - 1) % len(mid)] = True   # два сегмента у этого узла
                same[i] = True
                cross = np.cross(dl, r)
                vel[i] += np.where(same[:, None], 0.0,
                                   gamma / (4 * np.pi) * cross
                                   / (r2 ** 1.5)[:, None]).sum(0)
        return vel

    def rhs(state, t):
        eps2 = eps0**2 + 4 * nu * t
        segs = [f for f in state]
        return [biot_savart(f, segs, eps2) for f in state]

    def rk4_step(state, t, h):
        k1 = rhs(state, t)
        k2 = rhs([f + 0.5 * h * k1[i] for i, f in enumerate(state)], t + h / 2)
        k3 = rhs([f + 0.5 * h * k2[i] for i, f in enumerate(state)], t + h / 2)
        k4 = rhs([f + h * k3[i] for i, f in enumerate(state)], t + h)
        return [f + h / 6 * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i])
                for i, f in enumerate(state)]

    frames = [([f.copy() for f in filaments], 0.0, eps0)]
    t = 0.0
    n_steps = int(round(t_end / dt))
    for s in range(1, n_steps + 1):
        filaments = rk4_step(filaments, t, dt)
        t += dt
        if s % 4 == 0:
            eps = math.sqrt(eps0**2 + 4 * nu * t)
            frames.append(([f.copy() for f in filaments], t, eps))

    fig = plt.figure(figsize=(8.6, 5.6), dpi=110)
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.04, right=0.97, top=0.88, bottom=0.08)
    ax.set_facecolor(BG)
    ax.set_xlim(-2.6, 2.6)
    ax.set_ylim(-1.7, 1.7)
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.text(2.05, -1.5, "→ x (ring axis)", fontsize=9, color="#8b949e")
    txt = ax.text(0.02, 0.965, "", transform=ax.transAxes, fontsize=10,
                  family="monospace", color=FG,
                  bbox=dict(boxstyle="round", fc=BG, ec=GRID, alpha=0.85))
    ax.set_title("Vortex-filament leapfrog (§27b): segment Biot–Savart with a "
                 "blob core, RK4", fontsize=10, color=FG, pad=10)
    l1, = ax.plot([], [], color=AMBER, lw=2.4)
    l2, = ax.plot([], [], color=BLUE, lw=2.4)
    s1 = ax.scatter([], [], s=10, color=AMBER, zorder=3)
    s2 = ax.scatter([], [], s=10, color=BLUE, zorder=3)

    def oblique(f):
        """Косоугольная проекция: X = x + 0.55·y, Y = z + 0.32·y — видна
        и форма кольца (плоскость y–z), и разлёт вдоль оси x."""
        fc = np.vstack([f, f[:1]])          # замкнуть контур кольца
        return fc[:, 0] + 0.55 * fc[:, 1], fc[:, 2] + 0.32 * fc[:, 1]

    def update(i):
        (f1, f2), t, eps = frames[i]
        x1p, y1p = oblique(f1)
        x2p, y2p = oblique(f2)
        l1.set_data(x1p, y1p)
        l2.set_data(x2p, y2p)
        s1.set_offsets(np.column_stack([x1p, y1p]))
        s2.set_offsets(np.column_stack([x2p, y2p]))
        sep = float(f1[:, 0].mean() - f2[:, 0].mean())
        txt.set_text(f"t = {t:5.2f}   separation Δx = {sep:+.3f}   "
                     f"ε(t) = √(ε₀²+4νt) = {eps:.3f}")
        return l1, l2, s1, s2, txt

    anim = FuncAnimation(fig, update, frames=len(frames), blit=False,
                         interval=1000 // fps)
    path = outdir / "anim_vortex_filaments.gif"
    _save_gif(fig, anim, path, fps)
    return path, ("segment Biot–Savart with blob core ε² = ε₀²+4νt, RK4, "
                  f"two rings ({n_nodes} nodes each) leapfrogging")


# ═══════════════════════════════════════════════════════════════════════════
# 7. Слоистое торможение (§27): dΓ/dt = −b Γ / T, τ = −Σ b_i Γ_i
# ═══════════════════════════════════════════════════════════════════════════
def anim_layered_braking(outdir: Path, fps: int = 12, n_frames: int = 80):
    b = 1.0 / (4 * math.pi + 2 * math.sqrt(3))
    theta_b = math.degrees(math.asin(b))
    n_layers = 12
    t_layer = 1.0
    b_i = b * (1.0 + 0.4 * np.arange(n_layers) / n_layers)   # профиль слоёв
    dz = 1.0 / n_layers
    g0 = 1.0 - 0.03 * np.arange(n_layers)

    ts = np.linspace(0, 6.0, n_frames)
    g_amp = g0[None, :] * np.exp(-np.outer(ts, b_i) / t_layer)
    tau = -(b_i * g_amp * dz).sum(1)                    # τ = −Σ b_i Γ_i Δz
    log_dec = -np.log(np.maximum(g_amp[-1] / g_amp[0], 1e-30)) / ts[-1] * t_layer

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.4, 4.9), dpi=110,
                                   gridspec_kw={"width_ratios": [1.15, 1]})
    fig.subplots_adjust(left=0.07, right=0.97, top=0.86, bottom=0.13,
                        wspace=0.28)
    for a in (ax1, ax2):
        _style_ax(a)
    ax1.set_title("layer circulations Γᵢ(t)", fontsize=10, color=FG)
    ax2.set_title("braking torque τ(t)", fontsize=10, color=FG)
    ax1.set_xlabel("t / T")
    ax1.set_ylabel("Γᵢ")
    ax2.set_xlabel("t / T")
    ax2.set_ylabel("τ")
    ax1.grid(alpha=0.3, lw=0.4)
    ax2.grid(alpha=0.3, lw=0.4)
    bars = ax1.bar(np.arange(n_layers), g_amp[0], color=BLUE, width=0.8)
    line, = ax2.plot([], [], color=AMBER, lw=2.2)
    txt = fig.text(0.5, 0.945, "", ha="center", fontsize=10,
                   family="monospace", color=FG)

    def update(i):
        for rect, h in zip(bars, g_amp[i]):
            rect.set_height(h)
        line.set_data(ts[: i + 1], tau[: i + 1])
        ax2.set_xlim(0, ts[-1])
        ax2.set_ylim(tau.min() * 1.1, 0.05)
        txt.set_text(f"dΓᵢ/dt = −bᵢΓᵢ/T · τ = −Σ bᵢΓᵢΔz · θ_b = {theta_b:.4f}°"
                     f" · log-decrement vs mean(b): "
                     f"{np.abs(log_dec - b_i.mean()).max():.2e}")
        return *bars, line, txt

    anim = FuncAnimation(fig, update, frames=n_frames, blit=False,
                         interval=1000 // fps)
    path = outdir / "anim_layered_braking.gif"
    _save_gif(fig, anim, path, fps)
    return path, ("exact solution of the layered braking model dΓᵢ/dt = "
                  "−bᵢΓᵢ/T with τ = −Σ bᵢΓᵢΔz (§27, Braking2D/VortexTube)")


# ═══════════════════════════════════════════════════════════════════════════
BUILDERS = {
    "b_rotation": anim_b_rotation,
    "kdv_collision": anim_kdv_collision,
    "taylor_green": None,          # специальный конвейер (общий прогон с каскадом)
    "spectrum_cascade": None,
    "rayleigh_benard": anim_rayleigh_benard,
    "vortex_filaments": anim_vortex_filaments,
    "layered_braking": anim_layered_braking,
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", default="", help="comma list of animations")
    ap.add_argument("--outdir", default=str(OUT_DEFAULT))
    ap.add_argument("--fps", type=int, default=12)
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()
    if args.list:
        for name in BUILDERS:
            print(name)
        return 0
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    wanted = args.only.split(",") if args.only else list(BUILDERS)

    results, t0 = {}, time.time()
    tg_data = None
    for name in wanted:
        if name not in BUILDERS:
            print(f"[FAIL] {name}: unknown animation")
            results[name] = False
            continue
        try:
            if name in ("taylor_green", "spectrum_cascade"):
                if tg_data is None:
                    print("── tg2d_core run (N=96, ν=1e-3, T=4) shared by "
                          "taylor_green + spectrum_cascade")
                    tg_data = _tg_run()
                vort, t_list, e_list, wh_frames, solver = tg_data
                if name == "taylor_green":
                    path, note = anim_taylor_green(vort, t_list, e_list,
                                                   solver.N, outdir, args.fps)
                else:
                    path, note = anim_spectrum_cascade(wh_frames, t_list,
                                                       solver, outdir,
                                                       fps=max(5, args.fps // 2))
            else:
                path, note = BUILDERS[name](outdir, fps=args.fps)
            ok, detail = _check_gif(path)
            try:
                rel = path.relative_to(REPO)
            except ValueError:
                rel = path
            print(f"[{'PASS' if ok else 'FAIL'}] {name}  ({detail}) -> {rel}")
            print(f"        {note}")
            results[name] = ok
        except Exception as exc:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            print(f"[FAIL] {name}: {exc.__class__.__name__}: {exc}")
            results[name] = False

    verdict = {"animations": results, "outdir": str(outdir),
               "all_passed": all(results.values()),
               "wall_time_s": round(time.time() - t0, 1)}
    print(f"JSON: {json.dumps(verdict)}")
    return 0 if verdict["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
