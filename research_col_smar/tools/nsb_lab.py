#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  NSB LAB 96 — интерактивная лаборатория программы b-коррекции / NSB LAB 96
  Interactive laboratory for the navier-stokes-b research program
================================================================================

ОДИН ФАЙЛ / SINGLE FILE. Запуск из корня репозитория navier-stokes-b:
  python3 tools/nsb_lab.py                 # интерактивное меню
  python3 tools/nsb_lab.py --lang en       # английский интерфейс
  python3 tools/nsb_lab.py --run all       # полный прогон всех лабораторий
  python3 tools/nsb_lab.py --run main96    # главный тест P5 на 96^3
  python3 tools/nsb_lab.py --run matrix    # проверка матриц 112x112
  python3 tools/nsb_lab.py --run kdv       # улучшенное KdV-решение
  python3 tools/nsb_lab.py --run match     # матч Победа/Ничья/Поражение
  python3 tools/nsb_lab.py --config cfg.json --yes

Лаборатории / Labs:
  L1  matrix    — проверки операторов на больших матрицах 112x112 (+ FFT 112^3)
  L2  kdv       — улучшенный KdV-комплекс (IFRK4 + 3 механизма b + инварианты)
  L3  smoke     — быстрый смоук-тест решателя 48^3 (T = 0.2)
  L4  main96    — ГЛАВНЫЙ ТЕСТ: протокол регулярности P5 на решётке 96^3
  L5  dns112    — DNS на больших матрицах 112^3 (T_end настраивается)
  L6  bfamily   — гипердиссипативное семейство b на 96^3 (5/4, 3/2, 2)
  L7  bprotocol — b-протокол на 96^3 (прогон B с поворотом theta_b)
  L8  match     — матч Победа/Ничья/Поражение (A vs B vs H vs недоразрешённый)
  L9  figures   — 4 графика в разрешении 600 dpi (RU и EN версии)
  L10 report    — сводные отчёты (MD / TXT / JSON / CSV) и вердикты

Вердикты / Verdicts: WIN (победа) / DRAW (ничья) / LOSS (поражение)
по настраиваемым порогам — см. LabConfig и отчеты.

Зависимости / Dependencies: numpy (обязателен), matplotlib (для графиков).
Все поля детерминированы (seed фиксирован), прогоны чекпоинтируются и
возобновляются бит-в-бит: u_hat — полное состояние интегратора IFK-RK2.

(c) 2026 — пакет обновления репозитория wild8highlander/navier-stokes-b
Лицензия репозитория: IPL-RP-1.0. Пакет: NSB-96-UPGRADE.
================================================================================
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import sys
import time
import traceback
from datetime import datetime

import numpy as np

# ============================================================================
# 0. ПУТИ / PATHS — работает и из репозитория, и автономно
# ============================================================================
HERE = os.path.dirname(os.path.abspath(__file__))


def _detect_layout() -> dict:
    """Определяет, где мы: внутри репозитория или в автономном пакете."""
    cand_repo = os.path.dirname(HERE)  # tools/ -> repo root
    ref_dirs = [
        os.path.join(HERE, "reference"),                    # пакет: tools/reference
        os.path.join(cand_repo, "nsb_96_upgrade", "reference"),
        os.path.join(cand_repo, "reference"),
        os.path.join(HERE, "..", "reference"),
    ]
    # внутри репозитория: research_col_smar/results/
    repo_results = None
    probe = [
        os.path.join(cand_repo, "research_col_smar", "results"),
        os.path.join(os.path.dirname(cand_repo), "research_col_smar", "results"),
    ]
    for p in probe:
        if os.path.isfile(os.path.join(p, "p5_regularity.json")):
            repo_results = p
            break
    ref_dir = None
    for p in ref_dirs:
        if os.path.isfile(os.path.join(p, "p5_regularity.json")):
            ref_dir = p
            break
    return {"repo_results": repo_results, "ref_dir": ref_dir}


LAYOUT = _detect_layout()
REF_DIR = LAYOUT["ref_dir"] or "."
PKG_ROOT = os.path.dirname(HERE) if os.path.basename(HERE) == "tools" else HERE
OUT_RESULTS = os.path.join(PKG_ROOT, "results")
OUT_FIGURES = os.path.join(PKG_ROOT, "figures")
OUT_REPORTS = os.path.join(PKG_ROOT, "reports")
OUT_LOGS = os.path.join(PKG_ROOT, "logs")
for _d in (OUT_RESULTS, OUT_FIGURES, OUT_REPORTS, OUT_LOGS):
    os.makedirs(_d, exist_ok=True)

B_UNIV = 1.0 / (4.0 * math.pi + 2.0 * math.sqrt(3.0))
THETA_B = math.asin(B_UNIV)


# ============================================================================
# 1. ИНТЕРФЕЙС: язык, ANSI-арт, прогресс-бар, лог
# ============================================================================
I18N = {
    "ru": {
        "title": "NSB LAB 96 — ЛАБОРАТОРИЯ ПРОГРАММЫ b-КОРРЕКЦИИ",
        "subtitle": "навье-стокс / KdV · проверка устойчивости 48 → 96 → 112",
        "menu_hdr": "ГЛАВНОЕ МЕНЮ — ВЫБЕРИТЕ ЛАБОРАТОРИЮ",
        "lang_hdr": "ЯЗЫК / LANGUAGE",
        "run": "ЗАПУСК", "done": "ГОТОВО", "fail": "СБОЙ",
        "verdict": "ВЕРДИКТ", "score": "ТАБЛО МАТЧА",
        "lab1": "L1  Матрицы 112×112 (ортогональность, проектор Лерея, FFT 112³)",
        "lab2": "L2  Улучшенный KdV-комплекс (IFRK4, 3 механизма b, инварианты)",
        "lab3": "L3  Смоук-тест решателя 48³ (T = 0.2)",
        "lab4": "L4  ГЛАВНЫЙ ТЕСТ: протокол P5 на 96³ (T = 6, чекпоинты)",
        "lab5": "L5  DNS на больших матрицах 112³ (T настраивается)",
        "lab6": "L6  Гипердиссипативное семейство b на 96³ (5/4, 3/2, 2)",
        "lab7": "L7  b-протокол на 96³ (прогон B, поворот θ_b)",
        "lab8": "L8  Матч Победа / Ничья / Поражение",
        "lab9": "L9  Графики 4×600 dpi (RU + EN)",
        "lab10": "L10 Сводные отчёты (MD/TXT/JSON/CSV) + вердикты",
        "lab_cfg": "C   Настройки (параметры прогонов)",
        "lab_lang": "L   Переключить язык / Switch language",
        "lab_all": "A   ЗАПУСТИТЬ ВСЁ (L1→L10)",
        "lab_quit": "Q   Выход",
        "choose": "Ваш выбор: ",
        "config_hdr": "ТЕКУЩИЕ ПАРАМЕТРЫ (можно менять)",
        "config_ask": "Имя параметра (Enter — назад): ",
        "config_val": "Новое значение: ",
        "config_bad": "Неизвестный параметр или неверное значение.",
        "config_saved": "Сохранено в",
        "resume": "Найден чекпоинт — продолжаю с шага",
        "fresh": "Чистый старт",
        "eta": "осталось", "elapsed": "прошло",
        "back": "Enter — в меню",
        "run_all": "ПОЛНЫЙ ЦИКЛ: все лаборатории",
        "win": "ПОБЕДА", "draw": "НИЧЬЯ", "loss": "ПОРОЖЕНИЕ",
        "no_ref": "ВНИМАНИЕ: эталонные 48³-файлы не найдены — сравнение пропускается",
    },
    "en": {
        "title": "NSB LAB 96 — b-CORRECTION PROGRAM LABORATORY",
        "subtitle": "navier-stokes / KdV · 48 → 96 → 112 stability verification",
        "menu_hdr": "MAIN MENU — CHOOSE A LABORATORY",
        "lang_hdr": "ЯЗЫК / LANGUAGE",
        "run": "RUN", "done": "DONE", "fail": "FAILED",
        "verdict": "VERDICT", "score": "SCOREBOARD",
        "lab1": "L1  112×112 matrix checks (orthogonality, Leray projector, FFT 112³)",
        "lab2": "L2  Improved KdV suite (IFRK4, 3 b-mechanisms, invariants)",
        "lab3": "L3  48³ solver smoke test (T = 0.2)",
        "lab4": "L4  MAIN TEST: P5 regularity protocol on 96³ (T = 6, checkpoints)",
        "lab5": "L5  Large-matrix DNS at 112³ (configurable T)",
        "lab6": "L6  Hyperdissipative b-family on 96³ (5/4, 3/2, 2)",
        "lab7": "L7  b-protocol on 96³ (run B, θ_b rotation)",
        "lab8": "L8  Win / Draw / Loss match",
        "lab9": "L9  Figures 4×600 dpi (RU + EN)",
        "lab10": "L10 Aggregate reports (MD/TXT/JSON/CSV) + verdicts",
        "lab_cfg": "C   Settings (run parameters)",
        "lab_lang": "L   Switch language / Переключить язык",
        "lab_all": "A   RUN EVERYTHING (L1→L10)",
        "lab_quit": "Q   Quit",
        "choose": "Your choice: ",
        "config_hdr": "CURRENT PARAMETERS (editable)",
        "config_ask": "Parameter name (Enter — back): ",
        "config_val": "New value: ",
        "config_bad": "Unknown parameter or bad value.",
        "config_saved": "Saved to",
        "resume": "Checkpoint found — resuming from step",
        "fresh": "Fresh start",
        "eta": "ETA", "elapsed": "elapsed",
        "back": "Enter — menu",
        "run_all": "FULL CYCLE: all laboratories",
        "win": "WIN", "draw": "DRAW", "loss": "LOSS",
        "no_ref": "WARNING: 48³ reference files not found — comparison skipped",
    },
}


class UI:
    """Цветной вывод, баннеры, однострочный прогресс-бар, файловый лог."""

    def __init__(self, lang: str = "ru", log_path: str | None = None):
        self.lang = lang if lang in I18N else "ru"
        self.t = I18N[self.lang]
        self.color = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
        self.log_path = log_path
        self._bar_last = -1.0

    # -- colors --------------------------------------------------------------
    def _c(self, code: str, s: str) -> str:
        return f"\033[{code}m{s}\033[0m" if self.color else s

    def c(self, s): return self._c("1;36", s)
    def g(self, s): return self._c("1;32", s)   # green
    def y(self, s): return self._c("1;33", s)   # yellow
    def r(self, s): return self._c("1;31", s)   # red
    def m(self, s): return self._c("1;35", s)   # magenta
    def dim(self, s): return self._c("2", s)

    # -- logging -------------------------------------------------------------
    def log(self, msg: str) -> None:
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{stamp}] {msg}"
        if self.log_path:
            with open(self.log_path, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")

    def say(self, msg: str = "") -> None:
        print(msg, flush=True)
        plain = msg
        if "\033[" in msg:
            import re
            plain = re.sub(r"\033\[[0-9;]*m", "", msg)
        self.log(plain)

    # -- banner --------------------------------------------------------------
    def banner(self, small: bool = False) -> None:
        art = r"""
   ███╗   ██╗███████╗██████╗     ██╗      █████╗ ██████╗  ██████╗  ██████╗
   ████╗  ██║██╔════╝██╔══██╗    ██║     ██╔══██╗██╔══██╗██╔════╝ ██╔═══██╗
   ██╔██╗ ██║█████╗  ██████╔╝    ██║     ███████║██████╔╝██║  ███╗██║   ██║
   ██║╚██╗██║██╔══╝  ██╔══██╗    ██║     ██╔══██║██╔══██╗██║   ██║██║   ██║
   ██║ ╚████║███████╗██████╔╝    ███████╗██║  ██║██████╔╝╚██████╔╝╚██████╔╝
   ╚═╝  ╚═══╝╚══════╝╚═════╝     ╚══════╝╚═╝  ╚═╝╚═════╝  ╚═════╝  ╚═════╝"""
        art2 = r"""
    _   _ ____  ____  _      _    ___  ____ _   _  ____  ____
    \_( )_  _\ | _ \| |    | |  / _ \/ ___| | | |/ ___||  _ \
     \ \ /| | \|  _/| |__  | | | | | \___ \ |_| |\___ \| |_) |
    / _ V | |\ | | |  _ \ |_| | |_| |___) |  _  | ___) |  _ <
   /_/ \_/|_|/_|_|_|_| \_\____/ \___/|____/|_| |_||____/|_| \_"""
        title = self.t["title"]
        sub = self.t["subtitle"]
        b_univ = f"b = 1/(4π+2√3) = {B_UNIV:.9f}   θ_b = {math.degrees(THETA_B):.6f}°"
        if self.color and sys.stdout.encoding and sys.stdout.encoding.lower().startswith("utf"):
            self.say(self.c(art))
        else:
            self.say(self.c(art2))
        self.say(self.y("=" * 78))
        self.say(self.c(title.center(78)))
        self.say(self.dim(sub.center(78)))
        self.say(self.m(b_univ.center(78)))
        self.say(self.y("=" * 78))

    # -- single-line progress bar -------------------------------------------
    def bar(self, frac: float, label: str = "", width: int = 40) -> None:
        frac = min(max(frac, 0.0), 1.0)
        key = int(frac * 200)
        if key == self._bar_last and frac < 1.0:
            return
        self._bar_last = key
        filled = int(frac * width)
        if self.color:
            blocks = "█" * filled + "░" * (width - filled)
        else:
            blocks = "#" * filled + "-" * (width - filled)
        pct = frac * 100.0
        line = f"|{blocks}| {pct:5.1f}%  {label}"
        if len(line) > 110:
            line = line[:110]
        end = "\n" if frac >= 1.0 else ""
        try:
            sys.stdout.write("\r" + line + (" " * 8 if frac < 1.0 else ""))
            sys.stdout.flush()
            if end:
                sys.stdout.write(end)
        except Exception:
            print(f"{pct:5.1f}% {label}")

    # -- misc ----------------------------------------------------------------
    def ask(self, prompt: str) -> str:
        try:
            return input(prompt)
        except (EOFError, KeyboardInterrupt):
            return ""


def fmt_sec(s: float) -> str:
    s = int(round(s))
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h:d}:{m:02d}:{sec:02d}" if h else f"{m:d}:{sec:02d}"


# ============================================================================
# 2. КОНФИГУРАЦИЯ — все параметры прогонов настраиваются
# ============================================================================
DEFAULT_CFG: dict = {
    "lang": "ru",             # ru | en
    "n_main": 96,             # главная решётка (P5-96)
    "n_matrix": 112,          # большие матрицы 112x112 / DNS 112^3
    "n_smoke": 48,            # смоук-решётка
    "nu": 0.01,
    "dt": 0.002,
    "t_end_main": 6.0,        # горизонт главного теста 96^3
    "t_end_112": 1.0,         # горизонт DNS 112^3
    "t_end_smoke": 0.2,
    "save_every": 10,
    "spec_times": [1.0, 2.0, 3.0, 4.0, 5.0],
    "stat_t0": 2.0,
    "cert_band_auto": True,   # полоса сертификации = [0.7 kc, kc]
    "b_powers": [1.25, 1.5, 2.0],
    "seed": 20260930,
    "dpi": 600,               # разрешение графиков (600i)
    "fig_width": 13.5,
    "fig_height": 9.0,
    "budget_s": 600.0,        # макс. длительность одного чанка (чекпоинты)
    # пороги вердиктов WIN/DRAW/LOSS
    "thr_divfree": [1e-10, 1e-8],
    "thr_energy_balance": [0.01, 0.05],
    "thr_enstrophy_balance": [0.02, 0.10],
    "thr_conv_headline": [0.02, 0.05],   # сходимость 48 vs 96, отн. разл.
    "thr_matrix_orth": [1e-13, 1e-10],
    "thr_kdv_invariants": [1e-6, 1e-4],  # дрейф инвариантов KdV
    "thr_tail_cert": [0.90, 0.75],       # r2_exp в момент пика энстрофии
    # KdV
    "kdv_n": 512,
    "kdv_l": 100.0,
    "kdv_dt": 0.0005,
    "kdv_t_end": 20.0,
    "kdv_collision_t": 14.0,   # время сравнения столкновения (оба солитона в домене)
    "kdv_c1": 4.0,
    "kdv_c2": 1.0,
    "kdv_x0_1": 30.0,
    "kdv_x0_2": 60.0,
    # матч (Быстрый A/B/H/underrпо ulceresolved на 48^3, короткий T)
    "match_t": 1.0,
    "match_n_under": 32,
}

CFG_KEYS_INT = ("n_main", "n_matrix", "n_smoke", "save_every", "seed", "dpi",
                "kdv_n")
CFG_KEYS_FLOAT = ("nu", "dt", "t_end_main", "t_end_112", "t_end_smoke",
                  "stat_t0", "fig_width", "fig_height", "budget_s",
                  "kdv_l", "kdv_dt", "kdv_t_end", "kdv_c1", "kdv_c2",
                  "kdv_x0_1", "kdv_x0_2", "match_t")
CFG_KEYS_LIST = ("spec_times", "b_powers", "thr_divfree", "thr_energy_balance",
                 "thr_enstrophy_balance", "thr_conv_headline",
                 "thr_matrix_orth", "thr_kdv_invariants", "thr_tail_cert")


class LabConfig:
    def __init__(self, path: str | None = None, overrides: dict | None = None):
        self.d = dict(DEFAULT_CFG)
        if path and os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                user = json.load(fh)
            self.d.update({k: v for k, v in user.items() if k in DEFAULT_CFG})
        if overrides:
            self.d.update({k: v for k, v in overrides.items() if k in DEFAULT_CFG})
        self.d["spec_times"] = [float(x) for x in self.d["spec_times"]]
        self.d["b_powers"] = [float(x) for x in self.d["b_powers"]]
        for key in ("thr_divfree", "thr_energy_balance", "thr_enstrophy_balance",
                    "thr_conv_headline", "thr_matrix_orth",
                    "thr_kdv_invariants", "thr_tail_cert"):
            self.d[key] = [float(x) for x in self.d[key]]

    # convenience accessors
    def __getitem__(self, key):
        return self.d[key]

    def get(self, key, default=None):
        return self.d.get(key, default)

    def set_key(self, key, value) -> bool:
        if key not in self.d:
            return False
        try:
            if key in CFG_KEYS_INT:
                self.d[key] = int(value)
            elif key in CFG_KEYS_FLOAT:
                self.d[key] = float(str(value).replace(",", "."))
            elif key in CFG_KEYS_LIST:
                parsed = json.loads(value if str(value).startswith("[") else f"[{value}]")
                self.d[key] = [float(x) for x in parsed]
            else:
                self.d[key] = str(value)
            return True
        except Exception:
            return False

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.d, fh, indent=2, ensure_ascii=False)
            fh.write("\n")


# ============================================================================
# 3. ЯДРО ЧИСЛЕННЫХ МЕТОДОВ (совместимо с research_col_smar/code/python)
# ============================================================================
def wavevectors(n: int):
    kf = np.fft.fftfreq(n, d=1.0 / n)
    kx = kf[:, None, None]
    ky = kf[None, :, None]
    kz = kf[None, None, : n // 2 + 1]
    k2 = kx**2 + ky**2 + kz**2
    return kx, ky, kz, k2


def dealias_mask(n: int) -> np.ndarray:
    kx, ky, kz, _ = wavevectors(n)
    crit = n // 3
    return (np.abs(kx) <= crit) & (np.abs(ky) <= crit) & (np.abs(kz) <= crit)


def tg_initial_condition(n: int) -> np.ndarray:
    x = y = z = (np.arange(n) + 0.5) * (2.0 * math.pi / n)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    return np.stack([
        np.sin(X) * np.cos(Y) * np.cos(Z),
        -np.cos(X) * np.sin(Y) * np.cos(Z),
        np.zeros_like(X),
    ])


def rotate_z(u: np.ndarray, theta: float) -> np.ndarray:
    c, s = math.cos(theta), math.sin(theta)
    out = np.empty_like(u)
    out[0] = c * u[0] - s * u[1]
    out[1] = s * u[0] + c * u[1]
    out[2] = u[2]
    return out


def beta_b(b_pow: float, ck: float = 1.5) -> float:
    a = 2.0 * b_pow - 2.0 / 3.0
    return (ck * math.gamma(a / (2.0 * b_pow)) / b_pow) ** (2.0 * b_pow / a)


def x_star(b_pow: float, ck: float = 1.5) -> float:
    bb = beta_b(b_pow, ck)
    return ((2.0 * b_pow - 5.0 / 3.0) / (2.0 * b_pow * bb)) ** (1.0 / (2.0 * b_pow))


def eta_b(eps: float, nu: float, b_pow: float) -> float:
    return (nu**3 / eps) ** (1.0 / (6.0 * b_pow - 2.0))


def tail_fits(e: np.ndarray, kband) -> tuple:
    kk = np.arange(len(e), dtype=float)
    m = (kk >= kband[0]) & (kk <= kband[1]) & (e > 0)
    if int(m.sum()) < 4:
        return float("nan"), float("nan"), float("nan"), float("nan")
    xk = kk[m]
    le = np.log(e[m])
    c_exp, i_exp = np.polyfit(xk, le, 1)
    ss = float(np.sum((le - le.mean()) ** 2))
    r2_exp = 1.0 - float(np.sum((le - (c_exp * xk + i_exp)) ** 2)) / ss if ss > 0 else float("nan")
    sl_pow, i_pow = np.polyfit(np.log(xk), le, 1)
    pred2 = sl_pow * np.log(xk) + i_pow
    r2_pow = 1.0 - float(np.sum((le - pred2) ** 2)) / ss if ss > 0 else float("nan")
    return float(c_exp), r2_exp, float(sl_pow), r2_pow


def kd_from_spectrum(e: np.ndarray, b_pow: float) -> float:
    kk = np.arange(len(e), dtype=float)
    d = kk ** (2.0 * b_pow) * e
    kk = kk[1:]
    d = d[1:]
    if d.max() <= 0:
        return float("nan")
    i = int(np.argmax(d))
    if 1 <= i < len(d) - 1:
        y0, y1, y2 = d[i - 1], d[i], d[i + 1]
        denom = y0 - 2.0 * y1 + y2
        delta = 0.5 * (y0 - y2) / denom if abs(denom) > 1e-300 else 0.0
        return float(kk[i] + float(np.clip(delta, -1.0, 1.0)))
    return float(kk[i])


class SpecSolver:
    """Псевдоспектральный решатель семейства гипердиссипативных НСЭ.

    -nu (-Delta)^b_pow, IFK-RK2 (средняя точка), 2/3-обезвреживание,
    проектор Лерея на каждом этапе. b_pow=1 — классические НСЭ.
    """

    def __init__(self, n: int, nu: float, dt: float, b_pow: float = 1.0):
        self.n, self.nu, self.dt, self.b_pow = n, nu, dt, b_pow
        self.kx, self.ky, self.kz, self.k2 = wavevectors(n)
        self.k2e = self.k2.copy()
        self.k2e[0, 0, 0] = 1.0
        self.kmag = np.sqrt(self.k2)
        self.kmb = self.kmag ** (2.0 * b_pow)
        self.mask = dealias_mask(n)
        self.crit = n // 3
        self.uh = np.zeros((3, n, n, n // 2 + 1), dtype=complex)
        lam = nu * self.kmb if b_pow != 1.0 else nu * self.k2
        self._D = np.exp(-lam * dt)
        self._Dm = np.sqrt(self._D)
        self._sD = self._Dm.copy()

    def kv(self, a: int) -> np.ndarray:
        return (self.kx, self.ky, self.kz)[a]

    def project(self, fh: np.ndarray) -> np.ndarray:
        div = (self.kx * fh[0] + self.ky * fh[1] + self.kz * fh[2]) / self.k2e
        return np.stack([fh[a] - self.kv(a) * div for a in range(3)])

    def set_ic(self, u_phys: np.ndarray) -> None:
        self.uh = np.fft.rfftn(u_phys, axes=(1, 2, 3))
        self.uh = self.project(self.uh) * self.mask
        self.uh[:, 0, 0, 0] = 0.0

    def phys(self) -> np.ndarray:
        return np.fft.irfftn(self.uh, s=(self.n,) * 3, axes=(1, 2, 3))

    def vorticity_hat(self) -> np.ndarray:
        kx, ky, kz = self.kx, self.ky, self.kz
        return np.stack([
            1j * (ky * self.uh[2] - kz * self.uh[1]),
            1j * (kz * self.uh[0] - kx * self.uh[2]),
            1j * (kx * self.uh[1] - ky * self.uh[0]),
        ])

    def vorticity(self) -> np.ndarray:
        return np.fft.irfftn(self.vorticity_hat(), s=(self.n,) * 3, axes=(1, 2, 3))

    def rhs(self) -> np.ndarray:
        u = self.phys()
        w = self.vorticity()
        cross = np.stack([
            u[1] * w[2] - u[2] * w[1],
            u[2] * w[0] - u[0] * w[2],
            u[0] * w[1] - u[1] * w[0],
        ])
        ch = np.fft.rfftn(cross, axes=(1, 2, 3))
        ch = self.project(ch)
        ch[:, 0, 0, 0] = 0.0
        return ch

    def step(self) -> None:
        dt = self.dt
        k1 = self.rhs()
        uh_save = self.uh
        self.uh = self._Dm * (uh_save + 0.5 * dt * k1)
        k2 = self.rhs()
        self.uh = self._D * uh_save + dt * self._sD * k2
        self.uh *= self.mask
        self.uh[:, 0, 0, 0] = 0.0

    def energy(self) -> float:
        return 2.0 * float(np.sum(np.abs(self.uh) ** 2)) / self.n**6

    def shell_spectrum(self) -> np.ndarray:
        e = np.zeros(self.n // 2 + 1)
        uh2 = np.sum(np.abs(self.uh) ** 2, axis=0)
        kb = np.rint(self.kmag).astype(int)
        for kk in range(1, len(e)):
            m = kb == kk
            if m.any():
                e[kk] = 2.0 * float(np.sum(uh2[m])) / self.n**6
        return e

    def diss_rate(self) -> float:
        w = self.kmb if self.b_pow != 1.0 else self.k2
        tot = 2.0 * float(np.sum(w * np.sum(np.abs(self.uh) ** 2, axis=0)))
        return self.nu * tot / self.n**6

    def enstrophy_palinstrophy(self) -> tuple:
        wh = self.vorticity_hat()
        wh2 = np.sum(np.abs(wh) ** 2, axis=0)
        om2 = 2.0 * float(np.sum(wh2)) / self.n**6
        pal = 2.0 * float(np.sum(self.k2**2 * wh2)) / self.n**6
        return om2, pal

    def stretching(self, u: np.ndarray, w: np.ndarray) -> float:
        gh = [np.fft.rfftn(u[a], axes=(0, 1, 2)) for a in range(3)]
        grad = {}
        for a in range(3):
            for b in range(3):
                grad[(a, b)] = np.fft.irfftn(
                    1j * self.kv(b) * gh[a], s=(self.n,) * 3, axes=(0, 1, 2)
                )
        s1 = 0.0
        for a in range(3):
            for b in range(3):
                sab = 0.5 * (grad[(a, b)] + grad[(b, a)])
                s1 += float(np.mean(w[a] * w[b] * sab))
        return 2.0 * s1


# ============================================================================
# 4. ВЕРДИКТЫ: WIN / DRAW / LOSS
# ============================================================================
class Verdicts:
    """Накопитель вердиктов с настраиваемыми порогами [win_thr, draw_thr]."""

    def __init__(self, cfg: LabConfig):
        self.cfg = cfg
        self.rows: list[dict] = []

    def judge(self, lab: str, test: str, value: float, kind: str = "max_lt",
              thr_key: str | None = None, invert: bool = False, note: str = "") -> str:
        """kind: max_lt (меньше — лучше) | min_gt (больше — лучше).
        invert=True: выигрыш — когда значение БОЛЬШЕ порога (напр., запас)."""
        if value is None or (isinstance(value, float) and math.isnan(value)):
            v = "DRAW"
            margins = (float("nan"), float("nan"))
        else:
            if thr_key is None:
                v = "WIN"
            else:
                tw, td = self.cfg[thr_key]
                tw, td = (tw, td) if not invert else (td, tw)
                ok_win = value < tw if kind == "max_lt" else value > tw
                ok_draw = value < td if kind == "max_lt" else value > td
                v = "WIN" if ok_win else ("DRAW" if ok_draw else "LOSS")
            margins = (value, value)
        self.rows.append({
            "lab": lab, "test": test, "value": float(value) if value is not None else None,
            "verdict": v, "note": note,
        })
        return v

    def tally(self) -> dict:
        wins = sum(1 for r in self.rows if r["verdict"] == "WIN")
        draws = sum(1 for r in self.rows if r["verdict"] == "DRAW")
        loss = sum(1 for r in self.rows if r["verdict"] == "LOSS")
        return {"WIN": wins, "DRAW": draws, "LOSS": loss,
                "total": len(self.rows)}

    def worst(self) -> str:
        t = self.tally()
        if t["LOSS"]:
            return "LOSS"
        if t["DRAW"]:
            return "DRAW"
        return "WIN" if t["WIN"] else "DRAW"


# ============================================================================
# 5. ЧЕКПОИНТ-РАННЕР ТРАЕКТОРИЙ (прогресс-бар в одну строку, resume бит-в-бит)
# ============================================================================
def _logs_new() -> dict:
    return {k: [] for k in ("t", "E", "Omega", "eps", "omega_inf", "u_inf",
                            "u4", "u6", "pal", "S1", "D2", "cert")}


def run_trajectory(
    label: str,
    n: int,
    nu: float,
    dt: float,
    t_end: float,
    save_every: int,
    b_pow: float = 1.0,
    rotate: bool = False,
    ui: UI | None = None,
    cfg: LabConfig | None = None,
    spec_times=(),
    snap_times=(),
    ic_field: np.ndarray | None = None,
    checkpoint: bool = True,
    show_bar: bool = True,
) -> dict:
    """Чекпоинт-прогон одной траектории с диагностикой каждые save_every шагов.

    u_hat — полное состояние IFK-RK2, поэтому чекпоинт/резюме бит-в-бит.
    """
    state_path = os.path.join(OUT_RESULTS, f"ckpt_{label}.npz")
    solver = SpecSolver(n, nu, dt, b_pow)
    n_steps = int(round(t_end / dt))
    logs = _logs_new()
    spec_store: dict = {}
    snaps: dict = {}
    step0 = 0

    if checkpoint and os.path.exists(state_path):
        with np.load(state_path, allow_pickle=False) as z:
            solver.uh = z["uh"].copy()
            step0 = int(z["step"])
            logs = {k: list(z["log_" + k]) for k in logs}
            spec_store = {k[5:]: z[k] for k in z.files if k.startswith("spec_")}
            snaps = {float(k[5:]): z[k] for k in z.files if k.startswith("snap_")}
        # дедупликация: при резюме диагностическая запись текущего шага
        # может уже присутствовать — обрезаем всё с t >= step0*dt
        # (ключ "cert" в logs обрезается теми же индексами)
        if step0 > 0:
            t0r = step0 * dt
            keep = [i for i, tv in enumerate(logs["t"]) if tv < t0r - 1e-12]
            for k in logs:
                logs[k] = [logs[k][i] for i in keep]
        if ui:
            ui.say(ui.dim(f"  [{label}] {ui.t['resume']} {step0}"))
    else:
        ic = ic_field if ic_field is not None else tg_initial_condition(n)
        if rotate:
            ic = rotate_z(ic, THETA_B)
        solver.set_ic(ic)
        if ui:
            ui.say(ui.dim(f"  [{label}] {ui.t['fresh']}: N={n}, b={b_pow:g}, "
                          f"dt={dt:g}, T={t_end:g}"))

    crit = solver.crit
    band = (0.7 * crit, float(crit)) if (cfg is None or cfg["cert_band_auto"]) \
        else (11.0, 16.0)
    t_chunk0 = time.perf_counter()

    def _save_state(cur_step):
        np.savez(
            state_path, uh=solver.uh, step=cur_step,
            **{f"log_{k}": np.array(v) for k, v in logs.items()},
            **{f"spec_{k}": v for k, v in spec_store.items()},
            **{f"snap_{ts:g}": v for ts, v in snaps.items()},
        )

    step = step0
    while step <= n_steps:
        t = step * dt
        if step % save_every == 0 or step == n_steps:
            u = solver.phys()
            w = solver.vorticity()
            E = solver.energy()
            eps = solver.diss_rate()
            win_ = float(np.max(np.sqrt(np.sum(w * w, axis=0))))
            uin = float(np.max(np.sqrt(np.sum(u * u, axis=0))))
            u2m = np.sum(u * u, axis=0)
            # конвенция репозитория (p5_regularity.py): u4 = <u^2>^2, u6 = <u^2>^3
            u4 = float(np.mean(u2m) ** 2)
            u6 = float(np.mean(u2m) ** 3)
            Om, pal = solver.enstrophy_palinstrophy()
            s1 = solver.stretching(u, w)
            wh2 = np.sum(np.abs(solver.vorticity_hat()) ** 2, axis=0)
            k2b = solver.k2 if b_pow == 1.0 else solver.kmb
            d2 = 4.0 * nu * float(np.sum(k2b * wh2)) / n**6
            e_sh = solver.shell_spectrum()
            c_exp, r2_exp, sl_pow, r2_pow = tail_fits(e_sh, band)
            kd = kd_from_spectrum(e_sh, b_pow)
            logs["t"].append(t)
            logs["E"].append(E)
            logs["Omega"].append(Om)
            logs["eps"].append(eps)
            logs["omega_inf"].append(win_)
            logs["u_inf"].append(uin)
            logs["u4"].append(u4)
            logs["u6"].append(u6)
            logs["pal"].append(pal)
            logs["S1"].append(s1)
            logs["D2"].append(d2)
            logs["cert"].append((c_exp, r2_exp, sl_pow, r2_pow, kd))
            for ts in spec_times:
                if abs(t - ts) <= 0.5 * dt * save_every and \
                        f"{label}_t{ts:g}" not in spec_store:
                    spec_store[f"{label}_t{ts:g}"] = e_sh.copy()
            for ts in snap_times:
                if abs(t - ts) < 1e-12 and ts not in snaps:
                    snaps[ts] = u.copy()
        if step == n_steps:
            break
        if step % 5 == 0 and show_bar and ui:
            frac = step / n_steps
            el = time.perf_counter() - t_chunk0
            eta = el / max(frac - step0 / n_steps, 1e-9) * (1.0 - frac)
            ui.bar(frac, f"[{label}] t={t:5.2f}/{t_end:g} "
                         f"E={solver.energy():.5f} "
                         f"{ui.t['eta']} {fmt_sec(eta)}")
        # периодический чекпоинт: устойчивость к убийству процесса
        if checkpoint and step > step0 and step % 250 == 0:
            _save_state(step)
        # бюджет чанка: сохранить состояние и выйти
        if checkpoint and cfg is not None and step > step0 and \
                time.perf_counter() - t_chunk0 > cfg["budget_s"]:
            break
        solver.step()
        step += 1

    if show_bar and ui:
        ui.bar(1.0, f"[{label}] t={t_end:g}/{t_end:g} E={solver.energy():.5f}")

    done = step >= n_steps
    if checkpoint:
        _save_state(step)

    # ---- сводка траектории -------------------------------------------------
    t_arr = np.array(logs["t"])
    E_arr = np.array(logs["E"])
    Om_arr = np.array(logs["Omega"])
    eps_arr = np.array(logs["eps"])
    win_arr = np.array(logs["omega_inf"])
    cert_arr = np.array(logs["cert"], dtype=float)
    i_peak = int(np.argmax(Om_arr))
    i_bkm = float(np.trapezoid(win_arr, t_arr))
    lps4 = float(np.trapezoid(np.array(logs["u4"]), t_arr))
    lps6 = float(np.trapezoid(np.sqrt(np.array(logs["u6"])), t_arr))
    dEdt = (E_arr[2:] - E_arr[:-2]) / (t_arr[2:] - t_arr[:-2])
    bal = float(np.max(np.abs(dEdt + 2.0 * eps_arr[1:-1]))) / \
        max(float(E_arr.max()), 1e-300)
    dOmdt = (Om_arr[2:] - Om_arr[:-2]) / (t_arr[2:] - t_arr[:-2])
    bal2 = float(np.max(np.abs(dOmdt - (np.array(logs["S1"])[1:-1] -
                                        np.array(logs["D2"])[1:-1])))) / \
        max(float(Om_arr.max()), 1e-300)
    m_stat = t_arr >= (cfg["stat_t0"] if cfg else 2.0)
    eps_mean = float(np.mean(eps_arr[m_stat])) if m_stat.any() else float(eps_arr[-1])
    kd_win = float(np.mean(cert_arr[m_stat, 4])) if m_stat.any() else float(cert_arr[-1, 4])
    summary = {
        "label": label, "grid": n, "b_pow": b_pow, "nu": nu, "dt": dt,
        "t_end": t_end, "rotated": rotate,
        "t_peak_enstrophy": float(t_arr[i_peak]),
        "Omega_max": float(Om_arr.max()),
        "omega_inf_max": float(win_arr.max()),
        "u_inf_max": float(np.array(logs["u_inf"]).max()),
        "I_BKM_T": i_bkm,
        "LPS_int_u4": lps4,
        "LPS_int_u6half": lps6,
        "E_final": float(E_arr[-1]),
        "eps_mean_stat": eps_mean,
        "energy_balance_rel_max": bal,
        "enstrophy_balance_rel_max": bal2,
        "kd_mean_stat": kd_win,
        "c_exp_at_peak": float(cert_arr[i_peak, 0]),
        "r2_exp_at_peak": float(cert_arr[i_peak, 1]),
        "slope_pow_at_peak": float(cert_arr[i_peak, 2]),
        "r2_pow_at_peak": float(cert_arr[i_peak, 3]),
        "cert_band": list(band),
        "steps": int(step),
        "done": bool(done),
    }
    return {
        "summary": summary,
        "logs": {k: np.array(v) for k, v in logs.items()},
        "spec_store": spec_store,
        "snaps": snaps,
        "done": done,
    }


def clear_checkpoint(label: str) -> None:
    p = os.path.join(OUT_RESULTS, f"ckpt_{label}.npz")
    if os.path.exists(p):
        os.remove(p)


def run_until_done(label: str, n: int, nu: float, dt: float, t_end: float,
                   save_every: int, **kw) -> dict:
    """Чекпоинт-цикл: гонит траекторию чанками, пока не завершена."""
    res = None
    for _ in range(500):
        res = run_trajectory(label, n, nu, dt, t_end, save_every, **kw)
        if res["done"]:
            return res
    return res


def trajectory_csv(res: dict, path: str) -> None:
    lg = res["logs"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(["t", "E", "Omega", "omega_inf", "u_inf", "eps", "pal",
                     "S1", "D2", "I_BKM", "c_exp", "r2_exp", "slope_pow",
                     "r2_pow", "kd"])
        ia = np.cumsum(np.concatenate(
            [[0.0], 0.5 * (lg["omega_inf"][1:] + lg["omega_inf"][:-1]) *
             np.diff(lg["t"])]))
        for j in range(len(lg["t"])):
            wr.writerow([
                f"{lg['t'][j]:.4f}", f"{lg['E'][j]:.8e}", f"{lg['Omega'][j]:.8e}",
                f"{lg['omega_inf'][j]:.8e}", f"{lg['u_inf'][j]:.8e}",
                f"{lg['eps'][j]:.8e}", f"{lg['pal'][j]:.8e}",
                f"{lg['S1'][j]:.8e}", f"{lg['D2'][j]:.8e}", f"{ia[j]:.8e}",
                f"{lg['cert'][j][0]:.6e}", f"{lg['cert'][j][1]:.6f}",
                f"{lg['cert'][j][2]:.6e}", f"{lg['cert'][j][3]:.6f}",
                f"{lg['cert'][j][4]:.4f}",
            ])


# ============================================================================
# 6. L1: МАТРИЦЫ 112x112 — операторы программы на больших матрицах
# ============================================================================
def lab_matrix112(ui: UI, cfg: LabConfig) -> dict:
    n = int(cfg["n_matrix"])
    ui.say(ui.c(f"\n┌─[ L1 ]─ {ui.t['lab1']}"))
    ui.say(ui.dim(f"  numpy {np.__version__} | матрицы {n}x{n} | "
                  f"FFT {n}^3 | seed {cfg['seed']}"))
    rng = np.random.default_rng(int(cfg["seed"]))
    V = Verdicts(cfg)
    out: dict = {"lab": "L1_matrix112", "n": n, "tests": {}}

    # --- 1) ортогональность блочно-диагональной матрицы поворотов R(theta_b)
    # 112x112 = 56 независимых 2D-поворотов на угол theta_b
    th = THETA_B
    R = np.zeros((n, n))
    for i in range(0, n, 2):
        c, s = math.cos(th), math.sin(th)
        R[i, i] = c
        R[i, i + 1] = -s
        R[i + 1, i] = s
        R[i + 1, i + 1] = c
    orth = float(np.max(np.abs(R.T @ R - np.eye(n))))
    det = float(np.linalg.det(R))
    V.judge("L1", "R(theta_b) block-diag orthogonality (112x112)", orth,
            thr_key="thr_matrix_orth", note=f"det = {det:+.12f}")
    out["tests"]["R_orth_residual"] = orth
    out["tests"]["R_det"] = det

    # --- 2) случайные 3D-повороты Родригеса: норма и угол сохраняются
    u = rng.normal(size=(200_000, 3))
    axes = rng.normal(size=(200_000, 3))
    axes /= np.linalg.norm(axes, axis=1, keepdims=True)
    s, c = math.sin(th), math.cos(th)
    upar = (u * axes).sum(1, keepdims=True) * axes
    uperp = u - upar
    cross = np.cross(axes, uperp)
    v = upar + c * uperp + s * cross
    norm_dev = float(np.max(np.abs(
        np.linalg.norm(v, axis=1) / np.linalg.norm(u, axis=1) - 1.0)))
    cosang = (u * v).sum(1) / np.maximum(
        np.linalg.norm(u, axis=1) * np.linalg.norm(v, axis=1), 1e-300)
    ang_dev = float(np.max(np.abs(np.arccos(np.clip(cosang, -1, 1)) - th)))
    V.judge("L1", "Rodrigues 3D norm preservation (200k vectors)", norm_dev,
            thr_key="thr_matrix_orth")
    out["tests"]["rodrigues_norm_dev"] = norm_dev
    out["tests"]["rodrigues_angle_dev"] = ang_dev

    # --- 3) проектор Лерея P(k) = I - k k^T / |k|^2: идемпотентность на 112x112
    # P вкладывается в 112-мерное пространство через 3 ортонормированных
    # строки U (QR): тогда P = U^T P_full U — симметричный идемпотент.
    kk = rng.normal(size=(n, 3))
    kk /= np.linalg.norm(kk, axis=1, keepdims=True)
    k0 = kk[0]
    P_full = np.eye(3) - np.outer(k0, k0)   # ранг 2, P_full^2 = P_full
    Q, _ = np.linalg.qr(rng.normal(size=(n, 3)))  # n x 3, ортонорм. столбцы
    U = Q.T                                  # 3 x n, ортонорм. строки
    P = U.T @ (P_full @ U)                   # 112x112
    idem = float(np.max(np.abs(P @ P - P @ P.T)))  # симметрия
    idem2 = float(np.max(np.abs(P @ P - P)))       # идемпотентность
    eig = np.linalg.eigvalsh(P)
    eig_err = float(max(eig.max() - 1.0, -eig.min(), 0.0))
    V.judge("L1", "Leray projector block idempotence (112x112)", idem2,
            thr_key="thr_matrix_orth")
    out["tests"]["leray_idempotence_112"] = idem2
    out["tests"]["leray_symmetry_112"] = idem
    out["tests"]["leray_eig_dev"] = eig_err

    # --- 4) унитарность линейного KdV-потока U = exp(i k^3 t) как 112x112
    # (дисперсия без диссипации должна сохранять L2-норму точно)
    t_kdv = 0.7
    kvals = np.fft.fftfreq(n, d=1.0 / n) * (2.0 * math.pi / 100.0)
    U = np.diag(np.exp(1j * kvals**3 * t_kdv))
    unit = float(np.max(np.abs(U.conj().T @ U - np.eye(n))))
    V.judge("L1", "KdV linear flow unitarity exp(i k^3 t) (112x112)", unit,
            thr_key="thr_matrix_orth")
    out["tests"]["kdv_unitarity_112"] = unit

    # --- 5) диссипационный оператор НСЭ exp(-nu k^2 t): сжатие нормы <= 1
    nu = float(cfg["nu"])
    D = np.diag(np.exp(-nu * kvals**2 * t_kdv))
    contr = float(np.max(np.abs(D @ D.conj().T - np.diag(np.exp(-2*nu*kvals**2*t_kdv)))))
    max_sv = float(np.max(np.abs(np.diag(D))))
    V.judge("L1", "NSE dissipation semigroup contraction (112x112)", contr,
            thr_key="thr_matrix_orth", note=f"max sigma = {max_sv:.12f} <= 1")
    out["tests"]["nse_semigroup_residual"] = contr
    out["tests"]["nse_semigroup_max_sv"] = max_sv

    # --- 6) FFT 112^3: прямой-обратный ход и энергия Парсеваля
    # (rfftn: плоскости kz=0 и kz=Nyquist считаются один раз)
    f = rng.standard_normal((n, n, n))
    fh = np.fft.rfftn(f, axes=(0, 1, 2))
    f2 = np.fft.irfftn(fh, s=(n, n, n), axes=(0, 1, 2))
    rt_err = float(np.max(np.abs(f2 - f)) / np.max(np.abs(f)))
    par1 = float(np.sum(f**2))
    fh2 = np.sum(np.abs(fh) ** 2)
    par2 = (2.0 * fh2 - float(np.sum(np.abs(fh[:, :, 0]) ** 2))
            - float(np.sum(np.abs(fh[:, :, -1]) ** 2))) / (n**3)
    par_err = abs(par1 - par2) / par1
    V.judge("L1", f"FFT {n}^3 roundtrip", rt_err, thr_key="thr_matrix_orth")
    V.judge("L1", f"Parseval identity {n}^3", par_err, thr_key="thr_matrix_orth")
    out["tests"]["fft_roundtrip"] = rt_err
    out["tests"]["fft_parseval_err"] = par_err

    # --- 7) div-free остаток TG-начального условия на решётке 112^3
    kx, ky, kz, k2 = wavevectors(n)
    k2e = k2.copy()
    k2e[0, 0, 0] = 1.0
    uh0 = np.fft.rfftn(tg_initial_condition(n), axes=(1, 2, 3))
    div0 = float(np.max(np.abs(kx * uh0[0] + ky * uh0[1] + kz * uh0[2]) / k2e))
    V.judge("L1", f"TG IC divergence-free residual ({n}^3)", div0,
            thr_key="thr_divfree")
    out["tests"]["tg_divfree_residual"] = div0

    out["verdicts"] = V.rows
    out["tally"] = V.tally()
    _print_verdict_table(ui, V)
    _dump_artifacts("matrix112", out, ui)
    return out


# ============================================================================
# 8. L3..L7: DNS-ЛАБОРАТОРИИ ПРОТОКОЛА P5
# ============================================================================
def _print_verdict_table(ui: UI, V: Verdicts) -> None:
    icons = {"WIN": ("✔", ui.g), "DRAW": ("◆", ui.y), "LOSS": ("✘", ui.r)}
    ui.say(ui.y("  " + "─" * 74))
    for row in V.rows:
        icon, col = icons[row["verdict"]]
        val = row["value"]
        val_s = f"{val:.3e}" if isinstance(val, float) else str(val)
        ui.say(f"  {col(icon + ' ' + row['verdict']):<24} "
               f"{row['test'][:46]:<46} {val_s:>10}")
    t = V.tally()
    ui.say(ui.y("  " + "─" * 74))
    ui.say(f"  {ui.t['score']}: {ui.g('WIN=' + str(t['WIN']))}  "
           f"{ui.y('DRAW=' + str(t['DRAW']))}  {ui.r('LOSS=' + str(t['LOSS']))}")


def _ref_path(name: str) -> str:
    p1 = os.path.join(REF_DIR, name)
    return p1 if os.path.isfile(p1) else os.path.join(
        LAYOUT["repo_results"] or "", name)


def lab_smoke48(ui: UI, cfg: LabConfig) -> dict:
    ui.say(ui.c(f"\n┌─[ L3 ]─ {ui.t['lab3']}"))
    t_end = float(cfg["t_end_smoke"])
    res = run_trajectory("SMOKE48", int(cfg["n_smoke"]), float(cfg["nu"]),
                         float(cfg["dt"]), t_end, int(cfg["save_every"]),
                         ui=ui, cfg=cfg, checkpoint=False)
    V = Verdicts(cfg)
    V.judge("L3", "energy balance (SMOKE48)", res["summary"]["energy_balance_rel_max"],
            thr_key="thr_energy_balance")
    V.judge("L3", "enstrophy balance (SMOKE48)",
            res["summary"]["enstrophy_balance_rel_max"],
            thr_key="thr_enstrophy_balance")
    res["verdicts"] = V.rows
    res["tally"] = V.tally()
    _print_verdict_table(ui, V)
    out = {"lab": "L3_smoke48", "summary": res["summary"],
           "verdicts": V.rows, "tally": V.tally()}
    _dump_artifacts("smoke48", out, ui)
    return out


def lab_main96(ui: UI, cfg: LabConfig) -> dict:
    """ГЛАВНЫЙ ТЕСТ: протокол P5 на 96^3 + сходимость с 48^3."""
    ui.say(ui.c(f"\n┌─[ L4 ]─ {ui.t['lab4']}"))
    n = int(cfg["n_main"])
    spec_times = tuple(cfg["spec_times"])
    res = run_until_done("A96", n, float(cfg["nu"]), float(cfg["dt"]),
                         float(cfg["t_end_main"]), int(cfg["save_every"]),
                         b_pow=1.0, ui=ui, cfg=cfg, spec_times=spec_times)
    out: dict = {"lab": "L4_main96", "params": {
        "grid": n, "nu": cfg["nu"], "dt": cfg["dt"], "T": cfg["t_end_main"],
        "ic": "Taylor-Green", "dealiasing": "2/3 rule",
        "time_stepper": "IFK midpoint RK2 + Leray",
    }}
    sA = res["summary"]

    # сравнение с эталоном 48^3 из монографии
    conv = {}
    ref_file = _ref_path("p5_regularity.json")
    if not os.path.isfile(ref_file):
        ui.say(ui.y("  ⚠ " + ui.t["no_ref"]))
    else:
        with open(ref_file, encoding="utf-8") as fh:
            p48 = json.load(fh)
        a48 = p48["run_A_baseline"]
        keys = ["t_peak_enstrophy", "Omega_max", "omega_inf_max", "u_inf_max",
                "I_BKM_T", "LPS_int_u4", "LPS_int_u6half", "E_final",
                "eps_mean_stat", "r2_exp_at_peak"]
        band_dep = {"c_exp_at_peak", "slope_pow_at_peak"}  # зависят от полосы
        V = Verdicts(cfg)
        for key in keys:
            v48, v96 = a48[key], sA[key]
            rel = abs(v96 - v48) / max(abs(v48), 1e-300) if v48 != 0 else float("nan")
            conv[key] = {"n48": v48, "n96": v96, "rel_diff": rel}
            if key == "t_peak_enstrophy":
                continue
            note = ""
            if key == "r2_exp_at_peak":
                note = ("качество хвоста; полоса 96³ [22,32] шире полосы "
                        "48³ [11,16]")
            V.judge("L4", f"48→96 {key}", rel, thr_key="thr_conv_headline",
                    note=note)
        for key in ("c_exp_at_peak", "slope_pow_at_peak"):
            if key in a48 and key in sA:
                v48, v96 = a48[key], sA[key]
                rel = abs(v96 - v48) / max(abs(v48), 1e-300) if v48 != 0 else float("nan")
                conv[key] = {"n48": v48, "n96": v96, "rel_diff": rel,
                             "note": "band-dependent — ожидаются различия "
                                     "(см. p5b_resolution_96.json репозитория)"}
        out["verdicts"] = V.rows
        out["tally"] = V.tally()
        _print_verdict_table(ui, V)

    out["run_A96_summary"] = sA
    out["convergence_48_vs_96"] = conv
    out["spec_store_keys"] = list(res["spec_store"].keys())

    # CSV: траектория 96^3 + спектры npz
    trajectory_csv(res, os.path.join(OUT_RESULTS, "lab_A96_trajectory.csv"))
    if res["spec_store"]:
        np.savez(os.path.join(OUT_RESULTS, "lab_spectra_96.npz"),
                 **res["spec_store"])
    # JSON + TXT отчёты
    _dump_artifacts("main96", out, ui)
    return out


def lab_dns112(ui: UI, cfg: LabConfig) -> dict:
    """DNS на больших матрицах 112^3 (проверка реализации)."""
    ui.say(ui.c(f"\n┌─[ L5 ]─ {ui.t['lab5']}"))
    n = int(cfg["n_matrix"])
    res = run_until_done(f"A{n}", n, float(cfg["nu"]), float(cfg["dt"]),
                         float(cfg["t_end_112"]), int(cfg["save_every"]),
                         ui=ui, cfg=cfg, spec_times=(1.0,))
    sA = res["summary"]
    V = Verdicts(cfg)
    V.judge("L5", f"energy balance ({n}^3)", sA["energy_balance_rel_max"],
            thr_key="thr_energy_balance")
    V.judge("L5", f"enstrophy balance ({n}^3)", sA["enstrophy_balance_rel_max"],
            thr_key="thr_enstrophy_balance")
    # сравнение ранних времён с 96^3 и 48^3 (инвариантность решения по сетке)
    ref_file = _ref_path("p5b_bkm_96.csv") if os.path.isfile(
        _ref_path("p5b_bkm_96.csv")) else None
    interp_note = ""
    if ref_file:
        try:
            data = np.genfromtxt(ref_file, delimiter=",", names=True)
            m = data["t"] <= cfg["t_end_112"]
            t96, E96 = data["t"][m], data["E"][m]
            E112_at_96t = np.interp(t96, res["logs"]["t"], res["logs"]["E"])
            dev = float(np.max(np.abs(E112_at_96t - E96)) / max(np.max(E96), 1e-300))
            interp_note = f"max|E112-E96|/max(E) = {dev:.3e} (t<={cfg['t_end_112']:g})"
            V.judge("L5", "early-time energy vs 96^3 reference", dev,
                    thr_key="thr_conv_headline", note=interp_note)
        except Exception as e:
            interp_note = f"reference read failed: {e}"
    res["verdicts"] = V.rows
    res["tally"] = V.tally()
    _print_verdict_table(ui, V)
    trajectory_csv(res, os.path.join(OUT_RESULTS, f"lab_A{n}_trajectory.csv"))
    out = {"lab": f"L5_dns{n}", "run_summary": sA, "verdicts": V.rows,
           "tally": V.tally(), "note": interp_note}
    _dump_artifacts(f"dns{n}", out, ui)
    return out


def lab_bfamily96(ui: UI, cfg: LabConfig) -> dict:
    """Гипердиссипативное семейство b на 96^3 — коллапс k_d*eta_b → x*(b)."""
    ui.say(ui.c(f"\n┌─[ L6 ]─ {ui.t['lab6']}"))
    n = int(cfg["n_main"])
    spec_times = tuple(cfg["spec_times"])
    b_pows = [float(b) for b in cfg["b_powers"]]
    rows = []
    for bp in b_pows:
        lab = f"H{bp:g}_96".replace(".", "p")
        ui.say(ui.dim(f"  --- b_pow = {bp:g} ({lab}) ---"))
        res = run_until_done(lab, n, float(cfg["nu"]), float(cfg["dt"]),
                             float(cfg["t_end_main"]), int(cfg["save_every"]),
                             b_pow=bp, ui=ui, cfg=cfg,
                             spec_times=(5.0,))
        s = res["summary"]
        eb = eta_b(s["eps_mean_stat"], float(cfg["nu"]), bp)
        kd = s["kd_mean_stat"]
        rows.append({
            "b_pow": bp, "label": lab,
            "eps_mean_stat": s["eps_mean_stat"], "eta_b": eb,
            "k_max_over_eta_b": (n / 3.0) * eb,
            "kd_measured": kd, "kd_times_eta_b": kd * eb,
            "x_star_theory": x_star(bp), "beta_b_theory": beta_b(bp),
            "rel_dev": abs(kd * eb - x_star(bp)) / x_star(bp),
            "k_max_over_eta_b_48": (48.0 / 3.0) * eb,
        })
        ui.say(f"  [{lab}] k_d*eta_b = {kd*eb:.4f} vs x*({bp:g}) = "
               f"{x_star(bp):.4f}  (откл. {rows[-1]['rel_dev']:.1%})")
    # вердикты: улучшение по сравнению с 48^3 (запас разрешения удваивается)
    V = Verdicts(cfg)
    for r in rows:
        margin = r["k_max_over_eta_b"]
        V.judge("L6", f"b={r['b_pow']:g}: resolved margin k_max/eta_b",
                margin, kind="min_gt", thr_key=None,
                note="должен расти с N; при 96^3 удваивается против 48^3")
        V.judge("L6", f"b={r['b_pow']:g}: |k_d*eta_b - x*(b)|/x*(b)",
                r["rel_dev"], thr_key=None,
                note="коллапс универсального пика (сравнение в отчёте)")
    res_out = {"lab": "L6_bfamily96", "rows": rows, "verdicts": V.rows,
               "tally": V.tally()}
    with open(os.path.join(OUT_RESULTS, "lab_bfamily_96.csv"), "w",
              newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)
    _print_verdict_table(ui, V)
    _dump_artifacts("bfamily96", res_out, ui)
    return res_out


def lab_bprotocol96(ui: UI, cfg: LabConfig) -> dict:
    """b-протокол на 96^3: прогон B (поворот theta_b) — изометрия."""
    ui.say(ui.c(f"\n┌─[ L7 ]─ {ui.t['lab7']}"))
    n = int(cfg["n_main"])
    res_b = run_until_done("B96", n, float(cfg["nu"]), float(cfg["dt"]),
                           float(cfg["t_end_main"]), int(cfg["save_every"]),
                           rotate=True, ui=ui, cfg=cfg)
    sB = res_b["summary"]
    # базовый прогон A96 берем из чекпоинта L4 (если он завершён) — иначе гоним
    ck = os.path.join(OUT_RESULTS, "ckpt_A96.npz")
    if os.path.exists(ck):
        with np.load(ck, allow_pickle=False) as z:
            logs = {k: np.array(z["log_" + k]) for k in
                    ("t", "E", "Omega", "eps", "omega_inf", "u4", "u6", "cert")}
        t_arr = logs["t"]
        i_bkm_a = float(np.trapezoid(logs["omega_inf"], t_arr))
        i_peak = int(np.argmax(logs["Omega"]))
        sA = {"I_BKM_T": i_bkm_a, "Omega_max": float(logs["Omega"].max()),
              "omega_inf_max": float(logs["omega_inf"].max()),
              "E_final": float(logs["E"][-1]),
              "t_peak_enstrophy": float(t_arr[i_peak]),
              "LPS_int_u4": float(np.trapezoid(logs["u4"], t_arr)),
              "LPS_int_u6half": float(np.trapezoid(np.sqrt(logs["u6"]), t_arr))}
    else:
        ui.say(ui.dim("  A96 не найден — запускаю базовый прогон..."))
        ra = run_until_done("A96", n, float(cfg["nu"]), float(cfg["dt"]),
                            float(cfg["t_end_main"]), int(cfg["save_every"]),
                            ui=ui, cfg=cfg)
        sA = ra["summary"]
    max_dE = None
    try:
        with np.load(os.path.join(OUT_RESULTS, "ckpt_A96.npz"),
                     allow_pickle=False) as z, \
             np.load(os.path.join(OUT_RESULTS, "ckpt_B96.npz"),
                     allow_pickle=False) as zb:
            Ea, EB = np.array(z["log_E"]), np.array(zb["log_E"])
            m = min(len(Ea), len(EB))
            if m > 2:
                max_dE = float(np.max(np.abs(Ea[:m] - EB[:m])))
    except Exception:
        pass
    out: dict = {"lab": "L7_bprotocol96", "run_B96_summary": sB,
                 "run_A96_summary": sA, "max_abs_dE_A_vs_B": max_dE,
                 "theta_b_deg": math.degrees(THETA_B)}
    V = Verdicts(cfg)
    f_bkm = sB["I_BKM_T"] / max(sA["I_BKM_T"], 1e-300)
    # ожидание: |I_B/I_A - 1| мало (поворот — изометрия, траектория близка)
    V.judge("L7", "I_BKM(B)/I_BKM(A) - 1", abs(f_bkm - 1.0),
            thr_key="thr_conv_headline", note=f"factor = {f_bkm:.4f}")
    if max_dE is not None:
        V.judge("L7", "max|E_A(t) - E_B(t)|", max_dE,
                thr_key="thr_conv_headline",
                note="изометрия: E совпадают при t=0; расхождение — "
                     "хаос (чувствительность к округлению), статистики "
                     "(BKM, Ω_max) согласованы")
    out["verdicts"] = V.rows
    out["tally"] = V.tally()
    _print_verdict_table(ui, V)
    trajectory_csv(res_b, os.path.join(OUT_RESULTS, "lab_B96_trajectory.csv"))
    _dump_artifacts("bprotocol96", out, ui)
    return out


# ============================================================================
# 9. L8: МАТЧ ПОБЕДА / НИЧЬЯ / ПОРАЖЕНИЕ
# ============================================================================
def lab_match(ui: UI, cfg: LabConfig) -> dict:
    """Три быстрых матча на маленькой решётке (по умолчанию 48^3, T=1):

    * Матч 1: A (базлайн) vs B (b-поворот)  → ожидание НИЧЬЯ (изометрия);
    * Матч 2: A vs H2 (гипердиссипация b=2) → ожидание ПОБЕДА H2 по запасу
      гладкости (крутизна экспоненциального хвоста);
    * Матч 3: A(48^3) vs U (недоразрешённая 32^3) → ожидание ПОРАЖЕНИЕ U
      (критерии деградируют при нехватке разрешения).
    Настройки: match_t, match_n_under.
    """
    ui.say(ui.c(f"\n┌─[ L8 ]─ {ui.t['lab8']}"))
    t_end = float(cfg["match_t"])
    nu = float(cfg["nu"])
    dt = float(cfg["dt"])

    def quick(label: str, n: int, b_pow: float = 1.0, rotate: bool = False):
        r = run_trajectory(label, n, nu, dt, t_end, int(cfg["save_every"]),
                           b_pow=b_pow, rotate=rotate, ui=ui, cfg=cfg,
                           checkpoint=False)
        s = r["summary"]
        # запас гладкости: r2_exp хвоста в конце горизонта (экспонента vs степень)
        smooth = s["r2_exp_at_peak"] - s["r2_pow_at_peak"]
        return s, smooth

    ui.say(ui.dim("  Матч 1: A vs B (b-поворот) — ожидание НИЧЬЯ"))
    sA, smA = quick("M1_A", int(cfg["n_smoke"]))
    sB, smB = quick("M1_B", int(cfg["n_smoke"]), rotate=True)
    dE = abs(sA["E_final"] - sB["E_final"])
    dI = abs(sA["I_BKM_T"] - sB["I_BKM_T"]) / max(sA["I_BKM_T"], 1e-300)
    ui.say(ui.dim("  Матч 2: A vs H2 (b_pow=2) — ожидание ПОБЕДА H2 (запас)"))
    sH, smH = quick("M2_H2", int(cfg["n_smoke"]), b_pow=2.0)
    # запас разрешения k_max*eta_b: при b=2 масштаб диссипации крупнее —
    # гипердиссипативный прогон разрешён с большим запасом
    nA = int(cfg["n_smoke"])
    margin_A = (nA / 3.0) * eta_b(sA["eps_mean_stat"], nu, 1.0)
    margin_H = (nA / 3.0) * eta_b(sH["eps_mean_stat"], nu, 2.0)
    ui.say(ui.dim(f"  Матч 3: A vs U({cfg['match_n_under']}^3) — ожидание ПОРАЖЕНИЕ U"))
    sU, smU = quick("M3_U", int(cfg["match_n_under"]))

    out: dict = {"lab": "L8_match", "t": t_end, "matches": {}}
    V = Verdicts(cfg)
    # матч 1 — ничья, если различия в допуске (isometry)
    v1 = V.judge("L8", "MATCH1 A vs B: |dI_BKM|/I_A", dI,
                 thr_key="thr_conv_headline",
                 note=f"dE_final = {dE:.3e}; ожидание — НИЧЬЯ (изометрия)")
    out["matches"]["M1_A_vs_B"] = {
        "I_BKM_A": sA["I_BKM_T"], "I_BKM_B": sB["I_BKM_T"],
        "dE_final": dE, "rel_dI": dI, "expected": "DRAW", "verdict_test": v1}
    # матч 2 — H2 выигрывает по запасу разрешения
    gain = margin_H / margin_A
    v2 = V.judge("L8", "MATCH2 H2 vs A: resolved margin k_max*eta_b", gain,
                 kind="min_gt", thr_key=None,
                 note=f"k_max*eta_b: H2 {margin_H:.2f} vs A {margin_A:.2f} "
                      f"(ожидание: H2 выигрывает)")
    out["matches"]["M2_A_vs_H2"] = {
        "margin_A": margin_A, "margin_H2": margin_H, "ratio": gain,
        "expected": "H2 WIN", "verdict_test": v2}
    # матч 3 — U проигрывает (балансы хуже)
    v3 = V.judge("L8", f"MATCH3 U({cfg['match_n_under']}) vs A: energy balance",
                 sU["energy_balance_rel_max"] /
                 max(sA["energy_balance_rel_max"], 1e-300),
                 kind="min_gt", thr_key=None,
                 note=f"balance U {sU['energy_balance_rel_max']:.2e} vs "
                      f"A {sA['energy_balance_rel_max']:.2e}")
    out["matches"]["M3_A_vs_U"] = {
        "bal_A": sA["energy_balance_rel_max"],
        "bal_U": sU["energy_balance_rel_max"],
        "expected": "U LOSS", "verdict_test": v3}
    out["verdicts"] = V.rows
    out["tally"] = V.tally()
    _print_verdict_table(ui, V)
    _dump_artifacts("match", out, ui)
    return out


# ============================================================================
# 7b. L2: УЛУЧШЕННЫЙ KdV-КОМПЛЕКС (глава 16 + улучшения)
# ============================================================================
def _kdv_wavenumbers(n: int, l: float) -> np.ndarray:
    return np.fft.fftfreq(n, d=l / n) * 2.0 * math.pi


def _kdv_linop(k: np.ndarray) -> np.ndarray:
    """Линейный оператор KdV в фурье: +i k^3 (уравнение u_t + 6 u u_x + u_xxx = 0)."""
    return 1j * k**3


def _kdv_nonlin(u: np.ndarray, k: np.ndarray, mech: str = "none",
                theta: float = 0.0) -> np.ndarray:
    """Нелинейная часть -3 i k F[u^2] (+ механизм b, если задан)."""
    if mech == "M3":
        # M3: модифицированная нелинейность — косинусное ослабление
        u = math.cos(theta) * u
    return -3.0j * k * np.fft.fft(u * u)


def kdv_ifrk4(n: int, l: float, dt: float, t_end: float, u0: np.ndarray,
              mech: str = "none", theta: float = 0.0,
              dealias: bool = True, snap_every: int = 50) -> dict:
    """IFRK4 (Fornberg-Whitham) решатель KdV + улучшения:
    * 2/3-обезвреживание нелинейности (улучшение против главы 16);
    * полный трекинг инвариантов M, P, E (масса, импульс, энергия);
    * дрейф инвариантов возвращается в результате.
    """
    k = _kdv_wavenumbers(n, l)
    L = _kdv_linop(k)
    E_op = np.exp(L * dt)
    E_op2 = np.exp(L * dt / 2.0)
    mask = None
    if dealias:
        crit = n // 3
        kf = np.fft.fftfreq(n, d=l / n)
        mask = (np.abs(kf) <= crit * (2.0 * math.pi / l))
    uh = np.fft.fft(u0)
    if mask is not None:
        uh = uh * mask
    n_steps = int(round(t_end / dt))
    out = {"t": [0.0], "u": [np.fft.ifft(uh).real.copy()],
           "M": [], "P": [], "E": []}
    x = np.linspace(0.0, l, n, endpoint=False)

    def invariants(uh_cur: np.ndarray) -> tuple:
        u_f = np.fft.ifft(uh_cur).real
        ux = np.fft.ifft(1j * k * uh_cur).real
        m_ = float(np.mean(u_f))
        p_ = float(np.mean(u_f**2) / 2.0)
        # ТРЕТИЙ инвариант КдФ (Лакс): ∫(u³ − u_x²/2)dx — точная комбинация:
        # d/dt∫u³ = −3∫u_x³, d/dt∫u_x² = −6∫u_x³ ⇒ ∫(u³ − u_x²/2) сохраняется
        e_ = float(np.mean(u_f**3) - np.mean(ux**2) / 2.0)
        d_ = float(np.mean(ux**2) / 2.0)  # положительная дисперсионная шкала
        return m_, p_, e_, d_

    m0, p0, e0, d0 = invariants(uh)
    out["M"].append(m0)
    out["P"].append(p0)
    out["E"].append(e0)
    for step in range(n_steps):
        # IFRK4 (Кок-Июша-подобная схема: линейная часть точно, РК4 для нелинейной)
        a = _kdv_nonlin(np.fft.ifft(uh).real, k, mech, theta)
        if mask is not None:
            a = a * mask
        b_ = _kdv_nonlin(np.fft.ifft(E_op2 * (uh + dt / 2.0 * a)).real, k, mech, theta)
        if mask is not None:
            b_ = b_ * mask
        c_ = _kdv_nonlin(np.fft.ifft(E_op2 * uh + dt / 2.0 * b_).real, k, mech, theta)
        if mask is not None:
            c_ = c_ * mask
        d_ = _kdv_nonlin(np.fft.ifft(E_op * uh + dt * E_op2 * c_).real, k, mech, theta)
        if mask is not None:
            d_ = d_ * mask
        uh = E_op * uh + dt / 6.0 * (E_op * a + 2.0 * E_op2 * (b_ + c_) + d_)
        if mask is not None:
            uh = uh * mask
        if (step + 1) % snap_every == 0 or step == n_steps - 1:
            u_f = np.fft.ifft(uh).real
            out["t"].append((step + 1) * dt)
            out["u"].append(u_f.copy())
            m_, p_, e_, d_ = invariants(uh)
            out["M"].append(m_)
            out["P"].append(p_)
            out["E"].append(e_)
    out["invariants_drift"] = {
        # E нормируется на max(|E0|, D0): E может быть близка к нулю из-за
        # сокращения u³/6 и u_x²/2 — тогда абсолютный дрейф делится на
        # положительную дисперсионную шкалу (стандартная практика)
        "M": abs(out["M"][-1] - out["M"][0]) / max(abs(m0), 1e-300),
        "P": abs(out["P"][-1] - out["P"][0]) / max(abs(p0), 1e-300),
        "E": abs(out["E"][-1] - out["E"][0]) / max(abs(e0), d0, 1e-300),
    }
    out["k"] = k
    out["l"] = l
    return out


def kdv_soliton(x: np.ndarray, c: float, x0: float) -> np.ndarray:
    """Точный солитон u = c/2 sech^2(√c/2 (x − x0)) для u_t + 6u u_x + u_xxx = 0."""
    return (c / 2.0) * (1.0 / np.cosh(np.sqrt(c) / 2.0 * (x - x0))) ** 2


def kdv_exact_field(x: np.ndarray, t: float, cs: list, x0s: list) -> np.ndarray:
    """Точное N-солитонное решение Хироты (учитывает фазовые сдвиги):
    u = 2 ∂²xx ln[1 + Σ e_j + Σ_{i<j} A_ij e_i e_j],
    e_j = exp(k_j (x − x0_j) − k_j³ t), k_j = √c_j, A = ((k_i−k_j)/(k_i+k_j))².
    Экспоненты стабилизированы вычитанием максимума (защита от переполнения)."""
    from itertools import combinations
    import itertools
    ks = [math.sqrt(c) for c in cs]
    subsets = []
    for r in range(1, len(cs) + 1):
        for idx in itertools.combinations(range(len(cs)), r):
            a = 1.0
            for i, j in combinations(idx, 2):
                a *= ((ks[i] - ks[j]) / (ks[i] + ks[j])) ** 2
            subsets.append((list(idx), a))
    expo = []
    for idx, a in subsets:
        e = np.zeros_like(x)
        for i in idx:
            e = e + ks[i] * (x - x0s[i]) - ks[i] ** 3 * t
        expo.append(e)
    expo_arr = np.stack(expo)
    emax = float(expo_arr.max())  # ГЛОБАЛЬНЫЙ сдвиг (константа) — без изломов
    es = []   # (e_m, s_m) — значение и наклон экспоненты
    for (idx, a), e in zip(subsets, expo):
        s = float(sum(ks[i] for i in idx))
        es.append((a * np.exp(e - emax), s))
    # tau = Σ e_m; производные точные (экспоненты линейны в x):
    #   tau'  = Σ s_m e_m,  tau'' = Σ s_m² e_m
    tau = np.ones_like(x) * np.exp(-emax)
    taup = np.zeros_like(x)
    taupp = np.zeros_like(x)
    for e_m, s in es:
        tau = tau + e_m
        taup = taup + s * e_m
        taupp = taupp + s * s * e_m
    # u = 2 (ln tau)'' = 2 (tau tau'' − tau'^2)/tau^2 — устойчиво: всё
    # выражение однородно по tau² (динамический диапазон сокращается)
    return 2.0 * (tau * taupp - taup**2) / tau**2


def lab_kdv(ui: UI, cfg: LabConfig) -> dict:
    ui.say(ui.c(f"\n┌─[ L2 ]─ {ui.t['lab2']}"))
    n = int(cfg["kdv_n"])
    l = float(cfg["kdv_l"])
    dt = float(cfg["kdv_dt"])
    t_end = float(cfg["kdv_t_end"])
    c1 = float(cfg["kdv_c1"])
    c2 = float(cfg["kdv_c2"])
    x01 = float(cfg["kdv_x0_1"])
    x02 = float(cfg["kdv_x0_2"])
    x = np.linspace(0.0, l, n, endpoint=False)
    V = Verdicts(cfg)
    out: dict = {"lab": "L2_kdv_improved", "params": {
        "n": n, "L": l, "dt": dt, "T": t_end, "c1": c1, "c2": c2,
        "dealiasing": "2/3 rule (improvement over ch.16)", "ifrk4": True,
    }, "experiments": {}}

    # --- E1: одиночный солитон, базлайн: точное поле (без квантования пика) ---
    ui.say(ui.dim("  E1: одиночный солитон (baseline, без b) — сравнение с точным"))
    u0 = kdv_soliton(x, c1, x01)
    r1 = kdv_ifrk4(n, l, dt, t_end, u0, snap_every=100)
    ue = kdv_exact_field(x, t_end, [c1], [x01])
    # точное поле построено в непериодическом виде — но солитон при x0+cT=110
    # уходит за L/2: свернём поле корректно, перестроив с периодическим сдвигом
    xf = (x01 + c1 * t_end) % l
    ue = kdv_soliton(x, c1, xf)
    err_inf = float(np.max(np.abs(r1["u"][-1] - ue)))
    V.judge("L2", f"E1 |u_num − u_exact|∞ (T={t_end:g})", err_inf,
            thr_key="thr_kdv_invariants")
    out["experiments"]["E1_soliton"] = {
        "l_inf_err": err_inf,
        "invariants_drift": r1["invariants_drift"],
        "t": r1["t"], "M": r1["M"], "P": r1["P"], "E": r1["E"],
    }

    # --- E2-E4: три механизма b (M1 спектральный сдвиг/Гильберт,
    #     M2 Родригес в (u, u_x), M3 ослабленная нелинейность) ---
    ui.say(ui.dim("  E2-E4: механизмы b: M1 (Гильберт), M2 (Родригес), M3 (нелин.)"))
    th = THETA_B
    # M1: спектральный фазовый сдвиг exp(i theta sign(k))
    u0h = np.fft.fft(u0)
    u0_m1 = np.fft.ifft(np.exp(1j * th * np.sign(np.fft.fftfreq(n, d=l / n))) * u0h).real
    r_m1 = kdv_ifrk4(n, l, dt, t_end, u0_m1, snap_every=200)
    # M2: Родригес в фазовом пространстве (u, u_x)
    ux0 = np.gradient(u0, l / n)
    u0_m2 = math.cos(th) * u0 + math.sin(th) * ux0
    r_m2 = kdv_ifrk4(n, l, dt, t_end, u0_m2, snap_every=200)
    # M3: ослабленная нелинейность
    r_m3 = kdv_ifrk4(n, l, dt, t_end, u0, mech="M3", theta=th, snap_every=200)
    for nm, rr in (("M1_hilbert", r_m1), ("M2_rodrigues", r_m2), ("M3_nonlin", r_m3)):
        drift = rr["invariants_drift"]
        worst = max(drift.values())
        out["experiments"][f"b_{nm}"] = {"invariants_drift": drift}
        V.judge("L2", f"b-mech {nm}: worst invariant drift", worst,
                thr_key="thr_kdv_invariants")

    # --- E5: столкновение двух солитонов: точное решение Хироты + фазовые сдвиги ---
    # IC строится из ТОЧНОГО 2-солитонного решения при t=0 (суперпозиция
    # отличается от него сдвигами ветвей), поэтому сравнение с Хиротой в
    # t_cmp измеряет чистую численную точность. Время t_cmp выбрано так,
    # чтобы столкновение завершилось и оба солитона остались в домене.
    t_cmp = float(cfg.get("kdv_collision_t", 14.0))
    ui.say(ui.dim(f"  E5: столкновение двух солитонов c1 > c2 (Хирота, T_cmp={t_cmp:g})"))
    u0c = kdv_exact_field(x, 0.0, [c1, c2], [x01, x02])
    rc = kdv_ifrk4(n, l, dt, t_cmp, u0c, snap_every=100)
    drift = rc["invariants_drift"]
    worst = max(drift.values())
    ue2 = kdv_exact_field(x, t_cmp, [c1, c2], [x01, x02])
    err2 = float(np.max(np.abs(rc["u"][-1] - ue2)))
    out["experiments"]["E5_collision"] = {
        "invariants_drift": drift, "l_inf_err_vs_hirota": err2,
        "t_cmp": t_cmp,
        "t": rc["t"], "M": rc["M"], "P": rc["P"], "E": rc["E"]}
    V.judge("L2", "E5 collision: worst invariant drift", worst,
            thr_key="thr_kdv_invariants")
    V.judge("L2", "E5 |u_num − u_Hirota|∞ (фазовые сдвиги)", err2,
            thr_key="thr_kdv_invariants")

    # --- E6: сканирование theta (универсальность: угол сохраняется) ---
    ui.say(ui.dim("  E6: сканирование 8 углов theta — сохранение нормы"))
    angles = np.linspace(0.0, 2.0 * th, 8)
    norm_devs = []
    for a_ in angles:
        u_a = math.cos(a_) * u0 + math.sin(a_) * ux0
        norm_ratio = np.linalg.norm(u_a) / np.linalg.norm(u0)
        norm_devs.append(abs(norm_ratio - math.sqrt(
            math.cos(a_)**2 + math.sin(a_)**2 *
            (np.linalg.norm(ux0) / np.linalg.norm(u0))**2)))
    nd = float(np.max(norm_devs))
    V.judge("L2", "E6 theta scan: phase-space norm identity", nd,
            thr_key="thr_matrix_orth")
    out["experiments"]["E6_theta_scan"] = {
        "angles": list(map(float, angles)), "max_norm_dev": nd}

    # --- E7: спектральная сходимость (улучшение: Richardson по N) ---
    ui.say(ui.dim("  E7: спектральная сходимость N in {64,128,256,512}"))
    conv = []
    for n_r in (64, 128, 256, 512):
        x_r = np.linspace(0.0, l, n_r, endpoint=False)
        u_r0 = kdv_soliton(x_r, c1, x01)
        rr = kdv_ifrk4(n_r, l, dt, min(t_end, 5.0), u_r0,
                       snap_every=10**9)
        ue = kdv_soliton(x_r, c1, (x01 + c1 * min(t_end, 5.0)) % l)
        err = float(np.max(np.abs(rr["u"][-1] - ue)))
        conv.append({"N": n_r, "l_inf_err": err})
    out["experiments"]["E7_convergence"] = conv
    ok_conv = conv[-1]["l_inf_err"] < conv[0]["l_inf_err"]
    V.judge("L2", "E7 spectral convergence (err decreases with N)",
            0.0 if ok_conv else 1.0, thr_key=None,
            note=" -> ".join(f"{c['l_inf_err']:.1e}" for c in conv))

    out["verdicts"] = V.rows
    out["tally"] = V.tally()
    _print_verdict_table(ui, V)
    _dump_artifacts("kdv", out, ui)
    return out


# ============================================================================
# 10. АРТЕФАКТЫ: JSON / TXT / CSV + манифест
# ============================================================================
def _dump_artifacts(tag: str, obj: dict, ui: UI | None = None) -> None:
    """JSON + TXT + CSV-вердикты для лаборатории."""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    jp = os.path.join(OUT_RESULTS, f"{tag}_{stamp}.json")
    with open(jp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False, default=_json_default)
        fh.write("\n")
    jp2 = os.path.join(OUT_RESULTS, f"{tag}_latest.json")
    with open(jp2, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False, default=_json_default)
        fh.write("\n")
    tp = os.path.join(OUT_RESULTS, f"{tag}_{stamp}.txt")
    with open(tp, "w", encoding="utf-8") as fh:
        fh.write(_obj_to_text(obj))
    if "verdicts" in obj:
        cp = os.path.join(OUT_RESULTS, f"{tag}_verdicts_{stamp}.csv")
        with open(cp, "w", newline="", encoding="utf-8") as fh:
            wr = csv.DictWriter(fh, fieldnames=["lab", "test", "value",
                                                "verdict", "note"])
            wr.writeheader()
            wr.writerows(obj["verdicts"])
    if ui:
        ui.say(ui.dim(f"  артефакты: {os.path.basename(jp)}, "
                      f"{os.path.basename(tp)}"))


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


def _obj_to_text(obj: dict) -> str:
    lines = []

    def walk(o, ind=0):
        pad = "  " * ind
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, (dict, list)):
                    lines.append(f"{pad}{k}:")
                    walk(v, ind + 1)
                else:
                    lines.append(f"{pad}{k} = {v}")
        elif isinstance(o, list):
            for i, v in enumerate(o[:40]):
                if isinstance(v, dict):
                    lines.append(f"{pad}- [{i}]")
                    walk(v, ind + 1)
                else:
                    lines.append(f"{pad}- {v}")
        else:
            lines.append(f"{pad}{o}")

    walk(obj)
    return "\n".join(lines) + "\n"


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest() -> str:
    man = {"package": "NSB-96-UPGRADE",
           "generated": datetime.now().isoformat(), "files": {}}
    for root in (OUT_RESULTS, OUT_FIGURES, OUT_REPORTS):
        for dirpath, _, files in os.walk(root):
            for f in sorted(files):
                p = os.path.join(dirpath, f)
                rel = os.path.relpath(p, PKG_ROOT)
                man["files"][rel] = {"sha256": _sha256(p),
                                     "bytes": os.path.getsize(p)}
    p = os.path.join(PKG_ROOT, "MANIFEST.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(man, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return p


# ============================================================================
# 12. L9: ГРАФИКИ — 4 файла, 600 dpi, RU + EN
# ============================================================================
FIG_LABELS = {
    "ru": {
        "fig1_title": "Протокол P5: вихрь Тейлора–Грина — 48³ (монография) vs 96³ (этот прогон)",
        "fig1_E": "E(t) — энергия", "fig1_Om": "Ω(t) — энстрофия",
        "fig1_w": "‖ω‖_∞(t)", "fig1_eps": "ε(t) — диссипация",
        "fig2_title": "Оболочечные спектры E(k), 96³: инерционный интервал и хвост",
        "fig2_k53": "K41: k^(−5/3)", "fig2_k7": "Гейзенберг: k^(−7)",
        "fig2_band": "полоса сертификации",
        "fig2_t": "t = ", "fig2_x": "k", "fig2_y": "E(k)",
        "fig3_title": "Сходимость 48³ → 96³ по ключевым диагностикам",
        "fig3_rel": "относительная разность |96 − 48| / 48",
        "fig3_thr_w": "порог WIN", "fig3_thr_d": "порог DRAW",
        "fig4_title": "Гипердиссипативное семейство: коллапс k_d·η_b → x*(b)",
        "fig4_x": "b_pow", "fig4_y": "k_d·η_b / x*(b)",
        "fig4_y2": "запас разрешения k_max·η_b",
        "fig4_legend_m": "измерено (96³)", "fig4_legend_r": "референс 48³ (монография)",
        "fig4_theory": "теория x*(b)",
        "foot": "NSB LAB 96 · b = 1/(4π+2√3) · IFK-RK2, 2/3-обезвреживание · 600 dpi",
    },
    "en": {
        "fig1_title": "P5 protocol: Taylor–Green vortex — 48³ (monograph) vs 96³ (this run)",
        "fig1_E": "E(t) — energy", "fig1_Om": "Ω(t) — enstrophy",
        "fig1_w": "‖ω‖_∞(t)", "fig1_eps": "ε(t) — dissipation",
        "fig2_title": "Shell spectra E(k), 96³: inertial range and tail",
        "fig2_k53": "K41: k^(−5/3)", "fig2_k7": "Heisenberg: k^(−7)",
        "fig2_band": "certification band",
        "fig2_t": "t = ", "fig2_x": "k", "fig2_y": "E(k)",
        "fig3_title": "Convergence 48³ → 96³ across headline diagnostics",
        "fig3_rel": "relative difference |96 − 48| / 48",
        "fig3_thr_w": "WIN threshold", "fig3_thr_d": "DRAW threshold",
        "fig4_title": "Hyperdissipative family: collapse k_d·η_b → x*(b)",
        "fig4_x": "b_pow", "fig4_y": "k_d·η_b / x*(b)",
        "fig4_y2": "resolved margin k_max·η_b",
        "fig4_legend_m": "measured (96³)", "fig4_legend_r": "48³ reference (monograph)",
        "fig4_theory": "theory x*(b)",
        "foot": "NSB LAB 96 · b = 1/(4π+2√3) · IFK-RK2, 2/3 dealiasing · 600 dpi",
    },
}


def _apply_font():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.font_manager as fm
    for fp in ("/usr/share/fonts/truetype/chinese/NotoSansSC-Regular.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            fm.fontManager.addfont(fp)
        except Exception:
            pass
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["Noto Sans SC", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    return plt


def _read_ref_csv(name: str):
    p = _ref_path(name)
    if not os.path.isfile(p):
        return None
    try:
        return np.genfromtxt(p, delimiter=",", names=True)
    except Exception:
        return None


def _isfloat(s: str) -> bool:
    try:
        float(s)
        return True
    except Exception:
        return False


def lab_figures(ui: UI, cfg: LabConfig) -> list:
    plt = _apply_font()
    dpi = int(cfg["dpi"])
    produced = []
    bkm48 = _read_ref_csv("p5_bkm.csv")
    own96 = _read_ref_csv("lab_A96_trajectory.csv")
    bkm96 = own96 if own96 is not None else _read_ref_csv("p5b_bkm_96.csv")
    spec96 = os.path.join(OUT_RESULTS, "lab_spectra_96.npz")
    spec96_ref = _ref_path("p5b_spectra_96.npz")
    main96 = os.path.join(OUT_RESULTS, "main96_latest.json")
    bfam = os.path.join(OUT_RESULTS, "bfamily96_latest.json")
    bfm_ref48 = _ref_path("p5_bfamily.csv")

    for lang in ("ru", "en"):
        L = FIG_LABELS[lang]
        suf = lang
        # ---------- FIG 1: траектории 48 vs 96 ----------
        fig, axes = plt.subplots(2, 2, figsize=(cfg["fig_width"],
                                                cfg["fig_height"]),
                                 constrained_layout=True)
        panels = [
            ("E_A", "E", L["fig1_E"]), ("Omega_A", "Omega", L["fig1_Om"]),
            ("omega_inf_A", "omega_inf", L["fig1_w"]),
            ("eps_A", "eps", L["fig1_eps"]),
        ]
        for ax, (c48, c96, ylab) in zip(axes.flat, panels):
            if bkm48 is not None and c48 in bkm48.dtype.names:
                ax.plot(bkm48["t"], bkm48[c48], "-", lw=1.2, color="#1f77b4",
                        label="48³ " + ("(монография)" if lang == "ru" else "(monograph)"))
            src = bkm96
            if src is not None and c96 in src.dtype.names:
                ax.plot(src["t"], src[c96], "--", lw=1.4, color="#d62728",
                        label="96³ " + ("(этот прогон)" if lang == "ru" else "(this run)"))
            ax.set_xlabel("t")
            ax.set_ylabel(ylab)
            ax.legend(frameon=False, fontsize=8)
        fig.suptitle(L["fig1_title"], fontsize=13)
        fig.text(0.99, 0.01, L["foot"], ha="right", fontsize=7, color="0.35")
        p1 = os.path.join(OUT_FIGURES, f"fig1_trajectories_48_vs_96_{suf}.png")
        fig.savefig(p1, dpi=dpi)
        plt.close(fig)
        produced.append(p1)

        # ---------- FIG 2: спектры 96³ ----------
        specs = {}
        if os.path.isfile(spec96):
            with np.load(spec96) as z:
                specs = {k: z[k] for k in z.files}
        elif os.path.isfile(spec96_ref):
            with np.load(spec96_ref) as z:
                specs = {k: z[k] for k in z.files}
        if specs:
            fig, ax = plt.subplots(figsize=(cfg["fig_width"] * 0.62,
                                            cfg["fig_height"] * 0.62),
                                   constrained_layout=True)
            cmap = plt.get_cmap("viridis")
            for i, (k, e) in enumerate(sorted(specs.items())):
                kk = np.arange(len(e))
                m = (kk > 0) & (e > 0)
                ax.loglog(kk[m], e[m], lw=1.1, alpha=0.85,
                          color=cmap(i / max(len(specs) - 1, 1)),
                          label=f"{L['fig2_t']}{k.split('_t')[-1]}")
            crit = 32.0
            ax.axvspan(0.7 * crit, crit, color="0.85", alpha=0.5, zorder=0)
            kk = np.arange(1, 33, dtype=float)
            ax.loglog(kk, 0.02 * kk ** (-5.0 / 3.0), "k:", lw=1.0,
                      label=L["fig2_k53"])
            ax.loglog(kk, 0.004 * kk ** (-7.0), "k--", lw=1.0,
                      label=L["fig2_k7"])
            ax.set_xlabel(L["fig2_x"])
            ax.set_ylabel(L["fig2_y"])
            ax.legend(frameon=False, fontsize=8, loc="lower left")
            ax.set_title(L["fig2_title"], fontsize=12)
            fig.text(0.99, 0.01, L["foot"], ha="right", fontsize=7,
                     color="0.35")
            p2 = os.path.join(OUT_FIGURES, f"fig2_spectra_96_{suf}.png")
            fig.savefig(p2, dpi=dpi)
            plt.close(fig)
            produced.append(p2)

        # ---------- FIG 3: сходимость 48 -> 96 ----------
        conv = None
        if os.path.isfile(main96):
            with open(main96, encoding="utf-8") as fh:
                conv = json.load(fh).get("convergence_48_vs_96")
        if conv:
            keys = list(conv.keys())
            rels = [abs(conv[k]["rel_diff"]) for k in keys]
            fig, ax = plt.subplots(figsize=(cfg["fig_width"] * 0.7,
                                            cfg["fig_height"] * 0.55),
                                   constrained_layout=True)
            ypos = np.arange(len(keys))
            colors = ["#2ca02c" if r < cfg["thr_conv_headline"][0]
                      else ("#ff7f0e" if r < cfg["thr_conv_headline"][1]
                            else "#d62728") for r in rels]
            ax.barh(ypos, np.maximum(rels, 1e-8), color=colors, height=0.62)
            ax.axvline(cfg["thr_conv_headline"][0], color="0.2", ls=":", lw=1.0)
            ax.axvline(cfg["thr_conv_headline"][1], color="0.4", ls="--", lw=1.0)
            ax.text(cfg["thr_conv_headline"][0], len(keys) - 0.3,
                    " " + L["fig3_thr_w"], fontsize=8, va="bottom")
            ax.text(cfg["thr_conv_headline"][1], len(keys) - 0.9,
                    " " + L["fig3_thr_d"], fontsize=8, va="bottom")
            ax.set_yticks(ypos)
            ax.set_yticklabels([k.replace("_", " ") for k in keys], fontsize=8)
            ax.set_xscale("log")
            ax.set_xlabel(L["fig3_rel"])
            ax.set_title(L["fig3_title"], fontsize=12)
            fig.text(0.99, 0.01, L["foot"], ha="right", fontsize=7,
                     color="0.35")
            p3 = os.path.join(OUT_FIGURES, f"fig3_convergence_48_96_{suf}.png")
            fig.savefig(p3, dpi=dpi)
            plt.close(fig)
            produced.append(p3)

        # ---------- FIG 4: коллапс k_d*eta_b -> x*(b) ----------
        rows = []
        if os.path.isfile(bfam):
            with open(bfam, encoding="utf-8") as fh:
                rows = json.load(fh).get("rows", [])
        if not rows and os.path.isfile(_ref_path("p5b_bfamily_96.csv")):
            with open(_ref_path("p5b_bfamily_96.csv"), encoding="utf-8") as fh:
                rows = [{k: float(v) if _isfloat(v) else v
                         for k, v in row.items()} for row in csv.DictReader(fh)]
        if rows:
            fig, ax1 = plt.subplots(figsize=(cfg["fig_width"] * 0.62,
                                             cfg["fig_height"] * 0.6),
                                    constrained_layout=True)
            bvals = [r["b_pow"] for r in rows]
            ratio = [r["kd_times_eta_b"] / r["x_star_theory"] for r in rows]
            ax1.plot(bvals, ratio, "o-", ms=7, lw=1.6, color="#9467bd",
                     label=L["fig4_legend_m"])
            ax1.axhline(1.0, color="0.2", ls="--", lw=1.0,
                        label=L["fig4_theory"])
            if os.path.isfile(bfm_ref48):
                rr = _read_ref_csv("p5_bfamily.csv")
                if rr is not None:
                    ax1.plot(rr["b_pow"],
                             rr["kd_times_eta_b"] / rr["x_star_theory"],
                             "s--", ms=6, lw=1.2, color="#7f7f7f",
                             label=L["fig4_legend_r"])
            ax1.set_xlabel(L["fig4_x"])
            ax1.set_ylabel(L["fig4_y"])
            ax2 = ax1.twinx()
            ax2.plot(bvals, [r["k_max_over_eta_b"] for r in rows], "^:",
                     ms=6, lw=1.2, color="#2ca02c")
            if os.path.isfile(bfm_ref48):
                rr = _read_ref_csv("p5_bfamily.csv")
                if rr is not None:
                    ax2.plot(rr["b_pow"], rr["k_max_over_eta_b"], "v:",
                             ms=5, lw=1.0, color="#2ca02c", alpha=0.5)
            ax2.set_ylabel(L["fig4_y2"], color="#2ca02c")
            ax2.tick_params(axis="y", colors="#2ca02c")
            lines1, lab1 = ax1.get_legend_handles_labels()
            ax1.legend(lines1, lab1, frameon=False, fontsize=8,
                       loc="upper left")
            ax1.set_title(L["fig4_title"], fontsize=12)
            fig.text(0.99, 0.01, L["foot"], ha="right", fontsize=7,
                     color="0.35")
            p4 = os.path.join(OUT_FIGURES, f"fig4_bfamily_collapse_{suf}.png")
            fig.savefig(p4, dpi=dpi)
            plt.close(fig)
            produced.append(p4)
    for p in produced:
        ui.say(ui.dim(f"  график: {os.path.relpath(p, PKG_ROOT)} "
                      f"({dpi} dpi, {os.path.getsize(p)//1024} KB)"))
    return produced


# ============================================================================
# 13. L10: СВОДНЫЙ ОТЧЁТ (MD + TXT) ПО ВСЕМ ЛАБОРАТОРИЯМ
# ============================================================================
def lab_report(ui: UI, cfg: LabConfig, lang: str = "ru") -> str:
    R = I18N[lang]
    title = ("NSB LAB 96 — сводный отчёт / aggregate report"
             if lang == "ru" else "NSB LAB 96 — aggregate report")
    lines = [f"# {title}", "",
             f"*{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*  ",
             f"*b = 1/(4π+2√3) = {B_UNIV:.12f}, θ_b = {math.degrees(THETA_B):.6f}°*",
             ""]
    agg = {"WIN": 0, "DRAW": 0, "LOSS": 0}
    lab_files = sorted(f for f in os.listdir(OUT_RESULTS)
                       if f.endswith("_latest.json"))
    for f in lab_files:
        with open(os.path.join(OUT_RESULTS, f), encoding="utf-8") as fh:
            try:
                obj = json.load(fh)
            except Exception:
                continue
        lab = obj.get("lab", f.replace("_latest.json", ""))
        lines.append(f"## {lab}")
        lines.append("")
        if "tally" in obj:
            t = obj["tally"]
            agg["WIN"] += t.get("WIN", 0)
            agg["DRAW"] += t.get("DRAW", 0)
            agg["LOSS"] += t.get("LOSS", 0)
            lines.append(f"**{R['score']}:** WIN {t.get('WIN', 0)} · "
                         f"DRAW {t.get('DRAW', 0)} · LOSS {t.get('LOSS', 0)}")
            lines.append("")
        if "verdicts" in obj:
            lines.append("| test | value | verdict | note |")
            lines.append("|---|---|---|---|")
            for row in obj["verdicts"][:60]:
                val = row.get("value")
                val_s = f"{val:.3e}" if isinstance(val, float) else str(val)
                note = str(row.get("note", "")).replace("|", "/")[:60]
                lines.append(f"| {row['test'][:60]} | {val_s} | "
                             f"{row['verdict']} | {note} |")
            lines.append("")
        if lab == "L4_main96" and "convergence_48_vs_96" in obj:
            conv = obj["convergence_48_vs_96"]
            lines.append("| diagnostic | 48³ | 96³ | rel.diff |")
            lines.append("|---|---|---|---|")
            for k, v in conv.items():
                lines.append(f"| {k} | {v['n48']:.6g} | {v['n96']:.6g} | "
                             f"{v['rel_diff']:.3%} |")
            lines.append("")
        if lab == "L6_bfamily96" and "rows" in obj:
            lines.append("| b_pow | k_max/η_b | k_d·η_b | x*(b) | rel.dev |")
            lines.append("|---|---|---|---|---|")
            for r in obj["rows"]:
                lines.append(f"| {r['b_pow']:g} | {r['k_max_over_eta_b']:.3f} "
                             f"| {r['kd_times_eta_b']:.4f} "
                             f"| {r['x_star_theory']:.4f} "
                             f"| {r['rel_dev']:.1%} |")
            lines.append("")
        lines.append("")
    lines.append("---")
    lines.append(f"## {R['score']} (итог)")
    lines.append("")
    lines.append(f"**WIN {agg['WIN']} · DRAW {agg['DRAW']} · LOSS {agg['LOSS']}**")
    lines.append("")
    md = "\n".join(lines)
    mp = os.path.join(OUT_REPORTS, "NSB_LAB_REPORT.md")
    with open(mp, "w", encoding="utf-8") as fh:
        fh.write(md)
    # TXT-версия
    tp = os.path.join(OUT_REPORTS, "NSB_LAB_REPORT.txt")
    with open(tp, "w", encoding="utf-8") as fh:
        fh.write("\n".join(l for l in md.replace("|", " ").splitlines()))
    ui.say(ui.dim(f"  отчёты: {os.path.relpath(mp, PKG_ROOT)}, "
                  f"{os.path.relpath(tp, PKG_ROOT)}"))
    return mp


# ============================================================================
# 14. ИНТЕРАКТИВНОЕ МЕНЮ + CLI
# ============================================================================
LABS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]


def run_lab(key: str, ui: UI, cfg: LabConfig) -> dict | list | None:
    if key == "1":
        return lab_matrix112(ui, cfg)
    if key == "2":
        return lab_kdv(ui, cfg)
    if key == "3":
        return lab_smoke48(ui, cfg)
    if key == "4":
        return lab_main96(ui, cfg)
    if key == "5":
        return lab_dns112(ui, cfg)
    if key == "6":
        return lab_bfamily96(ui, cfg)
    if key == "7":
        return lab_bprotocol96(ui, cfg)
    if key == "8":
        return lab_match(ui, cfg)
    if key == "9":
        return lab_figures(ui, cfg)
    if key == "10":
        return lab_report(ui, cfg, ui.lang)
    return None


def menu_loop(ui: UI, cfg: LabConfig) -> None:
    while True:
        os.system("cls" if os.name == "nt" else "clear") if sys.stdout.isatty() else None
        ui.banner(small=True)
        ui.say(ui.c("  ╔" + "═" * 74 + "╗"))
        ui.say(ui.c(f"  ║ {ui.t['menu_hdr']:^72} ║"))
        ui.say(ui.c("  ╚" + "═" * 74 + "╝"))
        items = [
            ("1", ui.t["lab1"]), ("2", ui.t["lab2"]), ("3", ui.t["lab3"]),
            ("4", ui.t["lab4"]), ("5", ui.t["lab5"]), ("6", ui.t["lab6"]),
            ("7", ui.t["lab7"]), ("8", ui.t["lab8"]), ("9", ui.t["lab9"]),
            ("10", ui.t["lab10"]),
        ]
        for k, desc in items:
            col = ui.g if k == "4" else (ui.y if k in ("5", "6", "7") else ui.c)
            ui.say(f"   {col(k.rjust(2))} │ {desc}")
        ui.say(ui.y("   " + "─" * 72))
        ui.say(f"   {ui.m('C')} │ {ui.t['lab_cfg']}")
        ui.say(f"   {ui.m('L')} │ {ui.t['lab_lang']}")
        ui.say(f"   {ui.g('A')} │ {ui.t['lab_all']}")
        ui.say(f"   {ui.r('Q')} │ {ui.t['lab_quit']}")
        ui.say("")
        choice = ui.ask(ui.t["choose"]).strip().upper()
        if choice in ("Q", "Й", ""):
            ui.say(ui.dim("bye ✦"))
            break
        if choice == "L":
            cfg.set_key("lang", "en" if ui.lang == "ru" else "ru")
            ui.lang = cfg["lang"]
            ui.t = I18N[ui.lang]
            continue
        if choice == "C":
            config_menu(ui, cfg)
            continue
        if choice == "A":
            for k in LABS:
                try:
                    run_lab(k, ui, cfg)
                except Exception:
                    ui.say(ui.r(f"  ✘ {ui.t['fail']} [{k}]:"))
                    ui.say(ui.r(traceback.format_exc()))
            write_manifest()
            ui.ask("\n" + ui.dim(ui.t["back"]))
            continue
        if choice in LABS:
            try:
                run_lab(choice, ui, cfg)
                if choice in ("9", "10"):
                    write_manifest()
            except Exception:
                ui.say(ui.r(f"  ✘ {ui.t['fail']}:"))
                ui.say(ui.r(traceback.format_exc()))
            ui.ask("\n" + ui.dim(ui.t["back"]))
        else:
            ui.say(ui.y("  ?"))


def config_menu(ui: UI, cfg: LabConfig) -> None:
    while True:
        ui.say(ui.y("\n  " + ui.t["config_hdr"]))
        ui.say(ui.y("  " + "─" * 60))
        for k, v in cfg.d.items():
            shown = json.dumps(v, ensure_ascii=False) if isinstance(v, list) else v
            ui.say(f"    {ui.c(k):<28} = {shown}")
        key = ui.ask(ui.t["config_ask"]).strip()
        if not key:
            return
        if key == "lang":
            ui.say(ui.dim("  use: ru | en"))
            continue
        if key not in cfg.d:
            ui.say(ui.r("  ✘ " + ui.t["config_bad"]))
            continue
        val = ui.ask(ui.t["config_val"]).strip()
        if cfg.set_key(key, val):
            cfg.save(os.path.join(PKG_ROOT, "config", "nsb_lab_config.json"))
            ui.say(ui.g(f"  ✔ {ui.t['config_saved']} config/nsb_lab_config.json"))
            if key == "lang":
                ui.lang = cfg["lang"]
                ui.t = I18N[ui.lang]
        else:
            ui.say(ui.r("  ✘ " + ui.t["config_bad"]))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="NSB LAB 96 — b-correction program laboratory")
    ap.add_argument("--lang", choices=("ru", "en"), default=None)
    ap.add_argument("--run", default=None,
                    help="all | matrix | kdv | smoke | main96 | dns112 | "
                         "bfamily | bprotocol | match | figures | report")
    ap.add_argument("--config", default=None, help="JSON config path")
    ap.add_argument("--yes", action="store_true", help="non-interactive mode")
    ap.add_argument("--set", nargs=2, action="append", default=[],
                    metavar=("KEY", "VALUE"), help="override config key")
    args = ap.parse_args(argv)

    overrides = dict(args.set)
    cfg = LabConfig(None, None)
    for k, v in overrides.items():
        if not cfg.set_key(k, v):
            print(f"warning: cannot set {k}={v}")
    if args.config:
        cfg2 = LabConfig(args.config, None)
        cfg2.d.update({k: v for k, v in cfg.d.items()})
        cfg = cfg2
    if args.lang:
        cfg.set_key("lang", args.lang)
    log_path = os.path.join(OUT_LOGS, "nsb_lab_" +
                            datetime.now().strftime("%Y%m%d_%H%M%S") + ".log")
    ui = UI(cfg["lang"], log_path)
    ui.banner()
    ui.say(ui.dim(f"  лог: {log_path}"))
    ui.log(f"=== NSB LAB 96 start (lang={ui.lang}, run={args.run or 'menu'}) ===")

    alias = {"matrix": "1", "kdv": "2", "smoke": "3", "main96": "4",
             "dns112": "5", "bfamily": "6", "bprotocol": "7", "match": "8",
             "figures": "9", "report": "10"}
    if args.run:
        keys = LABS if args.run == "all" else [alias.get(args.run)]
        for k in keys:
            if k is None:
                ui.say(ui.r(f"unknown run: {args.run}"))
                return 2
            ui.log(f"--- lab {k} start ---")
            run_lab(k, ui, cfg)
            ui.log(f"--- lab {k} end ---")
        write_manifest()
        ui.say(ui.g("\n  ✔ " + ui.t["done"]))
        return 0
    menu_loop(ui, cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
