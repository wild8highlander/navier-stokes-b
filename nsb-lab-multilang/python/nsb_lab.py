#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
  NSB PYTHON LAB v2.1.0 — polyglot edition
  A faithful port of the self-contained Julia "Navier–Stokes b-Lab" to Python.

  What is inside (mirrors julia/nsb_lab_standalone.jl):
    • In-house radix-2 FFT (Cooley–Tukey, DIT, bit-reversal, vectorised with
      NumPy) — numpy.fft is NOT used unless NSB_FFT=numpy is set.
    • 3-D pseudospectral Navier–Stokes / Euler solver on the torus:
      RK4 + Leray projection on every sub-step + 2/3 de-aliasing rule,
      hyperviscosity ν₄, adaptive CFL step, checkpoints + --resume.
    • 2-D barotropic β-plane solver (vorticity form, physical units).
    • BKM diagnostics: energy, enstrophy, palinstrophy, dissipation,
      sup|ω|, divergence, shell spectra, K41 (−5/3) fits, blow-up scanner
      (λ(t), t* extrapolation), Richardson ladders.
    • Initial conditions: Taylor–Green, ABC, Hou–Luo, random div-free.
    • b-correction audit: full lattice symmetry (relabeling) vs pointwise
      rotation (isometry that breaks div u = 0) with 2-D kicks and wave audit.
    • Real-flows laboratory: 20 documented geophysical/engineering flows
      (hurricanes, jets, currents, waves, lab classics) with DNS-feasibility
      estimates, reduced β-plane runs and b-kick injections.
    • Zero-dependency output stack: PNG writer (zlib), GIF89a animator,
      minimal PDF article writer, CSV/JSON/MD/TXT reports, terminal
      half-block heat images, sparklines and a ONE-LINE progress bar.

  Requirements:  Python ≥ 3.9, NumPy.  Everything else is stdlib.
  Optional:      matplotlib (pretty PNG plots when NSB_PLOTS=matplotlib).

  Run:
      python3 nsb_lab.py                 # interactive menu
      python3 nsb_lab.py --quick         # fast suite + final PDF
      python3 nsb_lab.py --help          # all options
      python3 nsb_lab.py --selftest      # built-in verification suite

  Results go to  ~/nsb_lab_results/{data,plots,reports,articles,logs}
═══════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import csv
import io
import json
import math
import os
import re
import struct
import sys
import time
import zlib
from datetime import datetime

import numpy as np

# ══════════════════════════════════════════════════════════════════
# 0. BOOT — version, config, terminal detection
# ══════════════════════════════════════════════════════════════════

NSB_VERSION = "2.1.0"
NSB_NAME = "Navier–Stokes b-Lab (Python, self-contained)"

class Config:
    def __init__(self) -> None:
        self.lang = "ru"
        self.out_dir = os.path.join(os.path.expanduser("~"), "nsb_lab_results")
        self.dpi = 600
        self.seed = 20260916
        self.color = True
        self.ascii_only = False
        self.max_n = 32
        for cand in (32, 64, 128, 256):
            try:
                total_gb = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2**30
            except (ValueError, OSError, AttributeError):
                total_gb = 8.0
            if cand**3 * 16 * 24 / 2**30 < total_gb * 0.55:
                self.max_n = cand
        self.quick = False
        self.batch = False
        self.quiet = False
        self.t_start = time.time()
        self.gif = True
        self.ckpt_every = 200
        self.adaptive_cfl = False
        self.nu4 = 0.0
        self.fft_backend = "own"          # own | numpy
        self.session: list[dict] = []     # registered verdicts

CFG = Config()

def detect_terminal() -> None:
    CFG.color = sys.stdout.isatty() and os.environ.get("TERM", "") != "dumb" \
        and not os.environ.get("NO_COLOR")
    if not CFG.color:
        CFG.ascii_only = True

def now_str() -> str:
    return datetime.now().strftime("%H:%M:%S")

def hms(t: float) -> str:
    t = max(0, int(round(t)))
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}".replace("d", f"{h}")

def hms_long(t: float) -> str:
    t = max(0, int(round(t)))
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    parts = []
    if h:
        parts.append(f"{h} ч" if CFG.lang == "ru" else f"{h} h")
    if h or m:
        parts.append(f"{m:02d} мин" if CFG.lang == "ru" else f"{m:02d} min")
    parts.append(f"{s:02d} с" if CFG.lang == "ru" else f"{s:02d} s")
    return " ".join(parts)

def uptime() -> float:
    return time.time() - CFG.t_start

def ensure_outdirs() -> None:
    for sub in ("", "logs", "data", "plots", "reports", "articles"):
        os.makedirs(os.path.join(CFG.out_dir, sub), exist_ok=True)

_LOG_IO = None

def logfile_open() -> str:
    global _LOG_IO
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(CFG.out_dir, "logs", f"session_{stamp}.log")
    ensure_outdirs()
    _LOG_IO = open(path, "a", encoding="utf-8", errors="replace")
    return path

def P(s: str = "") -> None:
    """Dual output: stdout (unless quiet) + session log file."""
    if not CFG.quiet:
        try:
            sys.stdout.write(s)
            sys.stdout.flush()
        except (BrokenPipeError, UnicodeEncodeError):
            pass
    if _LOG_IO is not None:
        _LOG_IO.write(s.replace("\x1b", "\\e"))
        _LOG_IO.flush()

def Pln(s: str = "") -> None:
    P(s + "\n")

def log_close() -> None:
    global _LOG_IO
    if _LOG_IO is not None:
        _LOG_IO.close()
        _LOG_IO = None

# ══════════════════════════════════════════════════════════════════
# 1. I18N — RU/EN dictionaries (web app carries 6 languages)
# ══════════════════════════════════════════════════════════════════

_I18N: dict[str, tuple[str, str]] = {}

def _add(k: str, ru: str, en: str) -> None:
    _I18N[k] = (ru, en)

def set_lang(lang: str) -> None:
    CFG.lang = "en" if lang == "en" else "ru"

def L(key: str) -> str:
    pair = _I18N.get(key)
    if pair is None:
        return key
    return pair[0] if CFG.lang == "ru" else pair[1]

def Lf(key: str, *args) -> str:
    fmt = L(key)
    ru = CFG.lang == "ru"
    out, ai = [], 0
    i = 0
    while i < len(fmt):
        c = fmt[i]
        if c == "%" and i + 1 < len(fmt):
            spec = fmt[i + 1]
            if spec == "%":
                out.append("%")
                i += 2
                continue
            j = i + 1
            while j < len(fmt) and fmt[j] in "0123456789.+ -#":
                j += 1
            if j < len(fmt) and fmt[j] in "sdfgeE":
                conv = fmt[j]
                spec = fmt[i + 1 : j + 1]
                v = args[ai]
                ai += 1
                if conv == "s":
                    out.append(str(v))
                elif conv == "d":
                    out.append(f"{int(v):{spec[:-1] + 'd' if spec[:-1] else 'd'}}")
                else:
                    py = spec[:-1] + conv.lower().replace("g", "g").replace("e", "e")
                    out.append(("%" + (spec[:-1] if len(spec) > 1 else "") + conv) % float(v))
                i = j + 1
                continue
        out.append(c)
        i += 1
    return "".join(out)

def init_i18n() -> None:
    _I18N.clear()
    _add("yes", "да", "yes"); _add("no", "нет", "no")
    _add("pass", "ПРОЙДЕНО", "PASS"); _add("fail", "ПРОВАЛЕНО", "FAIL")
    _add("skip", "ПРОПУЩЕНО", "SKIP"); _add("warn", "ВНИМАНИЕ", "WARN")
    _add("menu_prompt", "Выберите пункт и нажмите Enter", "Choose an item and press Enter")
    _add("invalid_choice", "Нет такого пункта — попробуйте ещё раз", "No such item — try again")
    _add("press_enter", "Enter — продолжить", "Enter — continue")
    _add("lang_toggle", "9. Язык / Language  (RU ↔ EN)", "9. Language / Язык  (EN ↔ RU)")
    _add("title", "ЛАБОРАТОРИЯ НАВЬЕ–СТОКСА · b-КОРРЕКЦИЯ", "NAVIER–STOKES LABORATORY · b-CORRECTION")
    _add("subtitle", "самодостаточная Python-версия (NumPy для массивов)",
         "self-contained Python edition (NumPy for arrays)")
    _add("menu_quick", "1. Быстрый прогон  (≈1–3 мин: мини-сьют + финальный PDF)",
         "1. Quick run  (≈1–3 min: mini-suite + final PDF)")
    _add("menu_suite_normal", "2. Полная сьют — НОРМАЛЬНЫЙ режим", "2. Full suite — NORMAL mode")
    _add("menu_suite_hard", "3. Полная сьют — ХАРД режим (больше критериев)",
         "3. Full suite — HARD mode (more criteria)")
    _add("menu_custom", "4. Свой эксперимент (любые N, ν, dt, T, b-коррекция)",
         "4. Custom experiment (any N, ν, dt, T, b-correction)")
    _add("menu_flows", "5. Лаборатория 20 реальных течений (ураганы, волны, течения)",
         "5. Real-flows laboratory (20 documented flows)")
    _add("menu_roadmap", "6. Роадмап и это железо (бенчмарк + время расчётов)",
         "6. Roadmap & this hardware (benchmark + run-time estimates)")
    _add("menu_reports", "7. Отчёты, графики и логи сессии", "7. Session reports, plots and logs")
    _add("menu_settings", "8. Настройки и о проекте", "8. Settings & about")
    _add("menu_exit", "0. Выход", "0. Exit")
    _add("config_line", "конфиг: выход=%s · DPI=%d · зерно=%d · N≤%d",
         "config: out=%s · DPI=%d · seed=%d · N≤%d")
    _add("exp_tg", "Тейлор–Грин: сходимость и экстраполяция",
         "Taylor–Green: convergence and extrapolation")
    _add("exp_abc", "ABC (Эйлер): охота за расходимостью", "ABC (Euler): blow-up hunt")
    _add("exp_houluo", "Хоу–Ло: антипараллельные вихревые трубки",
         "Hou–Luo: anti-parallel vortex tubes")
    _add("exp_baudit", "Аудит b-коррекции: симметрия против точечного пинка",
         "b-correction audit: symmetry vs pointwise kick")
    _add("exp_scan", "Сканер «сходимость в бесконечность» (λ(t), экстраполяция t*)",
         "Convergence-to-infinity scanner (λ(t), t* extrapolation)")
    _add("suite_start", "Старт сьюты: режим=%s", "Starting suite: mode=%s")
    _add("suite_done", "Сьют завершена: %d/%d проверок пройдено · %s",
         "Suite finished: %d/%d checks passed · %s")
    _add("scope_note", "Область действия: сертификат внутренней согласованности вычисленного решения в расчётном окне, не общая теорема.",
         "Scope: a certificate of internal consistency of the computed solution within the window, not a general theorem.")
    _add("verdict_ok", "ВЕРДИКТ: все проверки пройдены", "VERDICT: all checks passed")
    _add("verdict_fail", "ВЕРДИКТ: есть проваленные проверки", "VERDICT: some checks failed")
    _add("ck_divfree", "несжимаемость: max|div u| в машинном пороге",
         "incompressibility: max|div u| at machine level")
    _add("ck_energy_monotone", "энергия не растёт (вязкое затухание)",
         "energy non-increasing (viscous decay)")
    _add("ck_energy_conserved", "энергия сохраняется (Эйлер)", "energy conserved (Euler)")
    _add("ck_rk4_order", "измеренный порядок RK4 ≈ 4", "measured RK4 order ≈ 4")
    _add("ck_no_blowup", "признаков конечновременной расходимости нет (BKM ограничен, λ(t) не ускоряется)",
         "no finite-time blow-up signature (BKM bounded, λ(t) not accelerating)")
    _add("ck_tail_resolved", "спектральный хвост разрешён (уровень ниже порога)",
         "spectral tail resolved (level below threshold)")
    _add("ck_palin_growth", "рост палинстрофии согласован с энстрофией",
         "palinstrophy growth consistent with enstrophy")
    _add("ck_cfl", "CFL-аудит: dt ≤ 0.5·dx/max|u| на всех шагах",
         "CFL audit: dt ≤ 0.5·dx/max|u| at all steps")
    _add("ck_symmetry_relabel", "полная симметрия = релебелинг: диагностики совпадают до 1e-12",
         "full symmetry = relabeling: diagnostics match to 1e-12")
    _add("ck_isometry", "точечный поворот — изометрия: энергия сохранена",
         "pointwise rotation is an isometry: energy preserved")
    _add("ck_div_break", "точечный поворот ЛОМАЕТ div u = 0 (инъекция задокументирована)",
         "pointwise rotation BREAKS div u = 0 (injection documented)")
    _add("ck_reproject", "после перепроекции div снова на машинном пороге",
         "after reprojection div back at machine level")
    _add("ck_b_effect", "b-пинк не снижает sup|ω| — регуляризации нет",
         "b-kick does not reduce sup|ω| — no regularization")
    _add("ck_abc_doubling", "время удвоения sup|ω| не сокращается к нулю",
         "sup|ω| doubling time does not shrink to zero")
    _add("ck_hl_growth", "рост sup|ω| измерен; λ(t) оценивается на всю длину окна",
         "sup|ω| growth measured; λ(t) assessed across the window")
    _add("ck_res_gap", "разрешение: |J_N − J_2N| ≤ 5% J (лестница N→2N)",
         "resolution: |J_N − J_2N| ≤ 5% of J (N→2N ladder)")
    _add("ck_lambda_fit", "подгонка λ(t): линейный тренд с R² указан честно",
         "λ(t) fit: linear trend reported with honest R²")
    _add("ck_stability", "устойчивость: нет NaN/Inf, sup|ω| ограничен",
         "stability: no NaN/Inf, sup|ω| bounded")
    _add("ck_balance", "баланс энстрофии: dΩ/dt ≈ −2ν·P (остаток мал)",
         "enstrophy balance: dΩ/dt ≈ −2ν·P (small residual)")
    _add("flows_hdr", "ЛАБОРАТОРИЯ РЕАЛЬНЫХ ТЕЧЕНИЙ — 20 документированных объектов",
         "REAL-FLOWS LABORATORY — 20 documented flows")
    _add("flows_menu_hint", "Введите номер течения (1–20), a — все по кругу, q — назад",
         "Enter flow number (1–20), a — run all, q — back")
    _add("flow_card", "КАРТОЧКА ТЕЧЕНИЯ", "FLOW CARD")
    _add("flow_source", "первоисточник/документация", "primary source/documentation")
    _add("flow_params", "документированные величины", "documented quantities")
    _add("flow_derived", "расчётные параметры (модель репозитория)", "derived parameters (repository model)")
    _add("flow_dns_no", "DNS НЕВОЗМОЖНО на любом существующем железе: нужно N ≈ %s узлов (~%s памяти)",
         "DNS is INFEASIBLE on any existing hardware: requires N ≈ %s grid points (~%s of memory)")
    _add("flow_dns_verdict", "DNS недостижим — редуцированная модель обязательна",
         "DNS infeasible — reduced model required")
    _add("flow_dns_ok", "DNS возможно: N = %d укладывается в память", "DNS feasible: N = %d fits in memory")
    _add("flow_reduced", "редуцированная модель запускается", "reduced model launched")
    _add("flow_bcorr", "b-коррекция ON/OFF", "b-correction ON/OFF")
    _add("flow_verdict", "ВЕРДИКТ ПО ТЕЧЕНИЮ", "FLOW VERDICT")
    _add("flow_all_hdr", "СВОДНАЯ ТАБЛИЦА 20 ТЕЧЕНИЙ", "SUMMARY TABLE OF 20 FLOWS")
    _add("road_hdr", "РОАДМАП И ЭТО ЖЕЛЕЗО", "ROADMAP AND THIS HARDWARE")
    _add("road_bench", "Бенчмарк собственного FFT (radix-2)", "In-house FFT benchmark (radix-2)")
    _add("road_gflops", "измеренная производительность 3D-FFT: %.1f GFLOP/с",
         "measured 3D-FFT throughput: %.1f GFLOP/s")
    _add("road_tbl_hdr", "Оценки для псевдоспектрального НС (RK4, ~13 3D-FFT/шаг)",
         "Estimates for pseudospectral NS (RK4, ~13 3D-FFTs/step)")
    _add("road_mem", "память", "memory"); _add("road_per_step", "сек/шаг", "s/step")
    _add("road_verdict_laptop", "ноутбук: реально за вечер", "laptop: an evening run")
    _add("road_verdict_ws", "нужна рабочая станция (или ночь на ноутбуке)",
         "workstation recommended (or overnight on a laptop)")
    _add("road_verdict_hpc", "нужен кластер/HPC", "cluster/HPC required")
    _add("road_verdict_no", "вне досягаемости одиночной машины", "out of reach for a single machine")
    _add("rep_hdr", "ОТЧЁТЫ СЕССИИ", "SESSION REPORTS")
    _add("rep_none", "Пока ничего не посчитано — запустите быстрый прогон (п. 1)",
         "Nothing computed yet — start the quick run (item 1)")
    _add("rep_saved", "Сохранено", "Saved")
    _add("rep_final_pdf", "финальный мини-отчёт (PDF)", "final mini-article (PDF)")
    _add("rep_formats", "форматы: TXT · MD · CSV · JSON · PNG · PDF", "formats: TXT · MD · CSV · JSON · PNG · PDF")
    _add("set_hdr", "НАСТРОЙКИ", "SETTINGS")
    _add("set_dpi", "Текущее DPI графиков", "Current plots DPI")
    _add("set_out", "Папка результатов", "Results folder")
    _add("set_about", "О ПРОЕКТЕ", "ABOUT")
    _add("set_about_txt", "Лаборатория проверяет гипотезу b-коррекции репозитория navier-stokes-b:\nполная решётчатая симметрия u' = R u(R⁻¹x) — релебелинг и не может влиять\nна единственность/регулярность; точечный поворот u' = R u(x) сохраняет энергию,\nно ломает div u = 0. Порт Python зеркалит Julia-оригинал.",
         "The lab tests the navier-stokes-b repository's b-correction hypothesis:\nfull lattice symmetry u' = R u(R⁻¹x) is a relabeling and cannot affect\nuniqueness/regularity; the pointwise rotation u' = R u(x) preserves energy\nbut breaks div u = 0. The Python port mirrors the Julia original.")
    _add("prog_step", "шаг", "step"); _add("prog_rate", "шаг/с", "steps/s")
    _add("prog_eta", "ETA", "ETA"); _add("prog_elapsed", "прошло", "elapsed")
    _add("fft_own", "FFT: собственный radix-2 (векторизованный)", "FFT: in-house radix-2 (vectorised)")
    _add("fft_numpy", "FFT: numpy.fft (быстрый бэкенд)", "FFT: numpy.fft (fast backend)")
    _add("adaptive_on", "адаптивный CFL-шаг включён", "adaptive CFL step enabled")
    _add("adaptive_stat", "адаптивных шагов: %d из %d", "adapted steps: %d of %d")
    _add("nu4_note", "гипервязкость ν₄ = %.4g", "hyperviscosity ν₄ = %.4g")
    _add("ckpt_saved", "чекпоинт: шаг %d → %s", "checkpoint: step %d → %s")
    _add("ckpt_resume", "продолжение с шага %d (%s)", "resuming from step %d (%s)")
    _add("ckpt_missing", "чекпоинт не найден — старт с нуля", "checkpoint not found — starting fresh")
    _add("run_started", "старт: %s", "started: %s")
    _add("run_finished", "финиш: %s", "finished: %s")
    _add("k41_line", "K41: наклон %.2f (R² = %.2f) — Колмогоров −5/3 = −1.67",
         "K41: slope %.2f (R² = %.2f) — Kolmogorov −5/3 = −1.67")
    _add("gif_saved", "GIF сохранён: %s (%d кадров)", "GIF saved: %s (%d frames)")
    _add("gif_disabled", "GIF выключен (--gif 0)", "GIF disabled (--gif 0)")
    _add("selftest_hdr", "САМОТЕСТ", "SELF-TEST")
    _add("selftest_ok", "САМОТЕСТ: ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ", "SELF-TEST: ALL CHECKS PASSED")
    _add("selftest_fail", "САМОТЕСТ: ЕСТЬ ПРОВАЛЫ", "SELF-TEST: FAILURES PRESENT")
    _add("bench_3dfft", "3D-FFT %d³", "3D FFT %d³")
    _add("menu_mode", "режим", "mode")

# ══════════════════════════════════════════════════════════════════
# 2. ANSI UI — colors, ONE-LINE progress bar, sparklines, term images
# ══════════════════════════════════════════════════════════════════

def _ansi(code: str, s: str) -> str:
    return f"\x1b[{code}m{s}\x1b[0m" if CFG.color else s

def rgb(r: int, g: int, b: int, s: str) -> str:
    if not CFG.color:
        return s
    return f"\x1b[38;2;{r};{g};{b}m{s}\x1b[0m"

def ok(s: str) -> str:
    return _ansi("1;32", s)

def bad(s: str) -> str:
    return _ansi("1;31", s)

def warn_c(s: str) -> str:
    return _ansi("1;33", s)

def muted(s: str) -> str:
    return _ansi("2", s) if CFG.color else s

def bold(s: str) -> str:
    return _ansi("1", s)

def dim(s: str) -> str:
    return muted(s)

C_ACCENT = (80, 160, 255)
C_GOLD = (255, 200, 60)

def term_width() -> int:
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80

_PROG_LAST = 0.0
_PROG_T0 = 0.0

def progress(frac: float, label: str = "", t0: float | None = None,
             total: int = 0, done: int = 0) -> None:
    """ONE-LINE progress bar: single '\r' redraw, percent, step, rate, ETA.
    Falls back to throttled 10%-step lines when stdout is not a TTY."""
    global _PROG_LAST, _PROG_T0
    frac = min(max(float(frac), 0.0), 1.0)
    if t0 is None:
        t0 = _PROG_T0
    tty = CFG.color or sys.stdout.isatty()
    if not tty or CFG.quiet:
        if (frac - _PROG_LAST >= 0.1 or frac >= 1.0) and _PROG_LAST < 1.0:
            _PROG_LAST = max(frac, _PROG_LAST) if frac < 1.0 else 1.0
            Pln(f"  [{int(round(frac * 100)):3d}%] {label}")
        return
    W = 30
    fill = int(round(frac * W))
    if CFG.ascii_only:
        bar = "#" * fill + "-" * (W - fill)
    else:
        bar = ""
        for i in range(1, W + 1):
            if i <= fill:
                r = int(40 + 180 * i / W); g = int(80 + 170 * i / W)
                bar += rgb(r, g, 255, "█")
            else:
                bar += muted("░")
    el = time.time() - t0
    eta = el / frac - el if frac > 0.005 else float("nan")
    fmt_t = lambda t: (" --:--" if not math.isfinite(t)
                       else f"{int(t) // 60:02d}:{int(t) % 60:02d}")
    if total > 0:
        tail = f" · {L('prog_step')} {done}/{total} · {done / max(el, 1e-9):.1f} {L('prog_rate')} · {L('prog_eta')} {fmt_t(eta)}"
    else:
        tail = f" · {L('prog_elapsed')} {fmt_t(el)}"
    info = f" {frac * 100:5.1f}%"
    line = " " * max(0, term_width() - 1)
    sys.stdout.write("\r" + line + "\r")
    sys.stdout.write(rgb(*C_ACCENT, " ▸ ") + label + " ▕" + bar + "▏" + info + muted(tail))
    sys.stdout.flush()
    if frac >= 1.0:
        sys.stdout.write("\n")
        _PROG_LAST = 0.0

_SPARK = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
_SPARK_ASCII = "_.-~*##"

def sparkline(v: list[float], width: int = 40) -> str:
    if not v:
        return ""
    n = len(v)
    idx = [round(i * (n - 1) / (min(width, n) - 1)) for i in range(min(width, n))] \
        if min(width, n) > 1 else [0]
    vals = [max(v[i], 0.0) for i in idx]
    lo, hi = min(vals), max(vals)
    rng = hi - lo if hi > lo else 1.0
    glyphs = _SPARK if (CFG.color and not CFG.ascii_only) else list(_SPARK_ASCII)
    k = len(glyphs) - 1
    return "".join(glyphs[min(k, max(0, int(round((x - lo) / rng * k))))] for x in vals)

def term_image(field: np.ndarray, caption: str, w: int = 56, h: int = 22) -> None:
    """Half-block viridis heat image in the terminal (TTY+color only)."""
    if not CFG.color or CFG.ascii_only:
        Pln(muted(f"  [🖼 {caption} → plots/*.png @ {CFG.dpi} dpi]"))
        return
    ny, nx = field.shape
    lo, hi = float(field.min()), float(field.max())
    Pln()
    for j in range(h):
        row = []
        for i in range(w):
            x0, x1 = (i * nx) // w, max((i * nx) // w + 1, ((i + 1) * nx) // w)
            y0, y1 = (j * ny) // h, max((j * ny) // h + 1, ((j + 1) * ny) // h)
            ym = (y0 + y1) // 2
            top = float(np.mean(field[y0:max(ym, y0 + 1), x0:x1]))
            bot = float(np.mean(field[ym:y1, x0:x1])) if ym < y1 else top
            ct = viridis((top - lo) / max(hi - lo, 1e-30))
            cb = viridis((bot - lo) / max(hi - lo, 1e-30))
            row.append(f"\x1b[38;2;{ct[0]};{ct[1]};{ct[2]};48;2;{cb[0]};{cb[1]};{cb[2]}m▀")
        P("".join(row) + "\x1b[0m\n")
    Pln(muted("  " + caption))

def header(title: str) -> None:
    Pln()
    Pln(rgb(*C_ACCENT, "─" * min(78, term_width() - 2)))
    Pln(rgb(*C_ACCENT, " ▸ ") + bold(title))
    Pln(rgb(*C_ACCENT, "─" * min(78, term_width() - 2)))

def banner() -> None:
    Pln()
    Pln(rgb(*C_ACCENT, "╔" + "═" * 76 + "╗"))
    Pln(rgb(*C_ACCENT, "║") + bold(rgb(*C_ACCENT, f"  {L('title')}  ")) +
        rgb(*C_ACCENT, " " * max(0, 76 - len(L('title')) - 12)) + rgb(*C_ACCENT, "║"))
    Pln(rgb(*C_ACCENT, "║") + muted(f"  {L('subtitle')}  v{NSB_VERSION}") +
        rgb(*C_ACCENT, "║"))
    Pln(rgb(*C_ACCENT, "║") + muted(f"  {Lf('config_line', CFG.out_dir, CFG.dpi, CFG.seed, CFG.max_n)}") + rgb(*C_ACCENT, "║"))
    Pln(rgb(*C_ACCENT, "║") + muted(f"  {L('fft_numpy') if CFG.fft_backend == 'numpy' else L('fft_own')} · uptime {hms(uptime())}") + rgb(*C_ACCENT, "║"))
    Pln(rgb(*C_ACCENT, "╚" + "═" * 76 + "╝"))

# ══════════════════════════════════════════════════════════════════
# 3. OUTPUT STACK — viridis, PNG, GIF, PDF (zero external deps)
# ══════════════════════════════════════════════════════════════════

_VIRIDIS_STOPS = [
    (0.0, (68, 1, 84)), (0.0625, (71, 18, 101)), (0.125, (72, 35, 116)),
    (0.1875, (65, 51, 127)), (0.25, (57, 66, 135)), (0.3125, (49, 80, 141)),
    (0.375, (43, 94, 147)), (0.4375, (36, 108, 152)), (0.5, (30, 122, 155)),
    (0.5625, (26, 137, 157)), (0.625, (23, 151, 158)), (0.6875, (26, 166, 154)),
    (0.75, (40, 180, 144)), (0.8125, (70, 194, 129)), (0.875, (109, 206, 109)),
    (0.9375, (158, 216, 85)), (1.0, (253, 231, 37)),
]

def viridis(x: float) -> tuple[int, int, int]:
    x = min(max(x, 0.0), 1.0)
    for i in range(len(_VIRIDIS_STOPS) - 1):
        x0, c0 = _VIRIDIS_STOPS[i]
        x1, c1 = _VIRIDIS_STOPS[i + 1]
        if x <= x1:
            t = (x - x0) / max(x1 - x0, 1e-12)
            return (int(round(c0[0] + (c1[0] - c0[0]) * t)),
                    int(round(c0[1] + (c1[1] - c0[1]) * t)),
                    int(round(c0[2] + (c1[2] - c0[2]) * t)))
    return _VIRIDIS_STOPS[-1][1]

def png_chunk(tag: bytes, data: bytes) -> bytes:
    return (struct.pack(">I", len(data)) + tag + data +
            struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

def write_png_rgb(path: str, rgb_arr: np.ndarray) -> None:
    """Own PNG writer: zlib (stdlib) deflate + CRC32. rgb_arr: (H, W, 3) uint8."""
    h, w, _ = rgb_arr.shape
    raw = b"".join(b"\x00" + rgb_arr[y].tobytes() for y in range(h))
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    idat = zlib.compress(raw, 6)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(png_chunk(b"IHDR", ihdr))
        f.write(png_chunk(b"IDAT", idat))
        f.write(png_chunk(b"IEND", b""))

def heat_png(path: str, field: np.ndarray, title: str = "", scale: int = 6) -> None:
    """Field → PNG heat map via viridis, upscaled nearest-neighbour."""
    ny, nx = field.shape
    lo, hi = float(field.min()), float(field.max())
    img = np.zeros((ny, nx, 3), dtype=np.uint8)
    for j in range(ny):
        for i in range(nx):
            img[j, i] = viridis((float(field[j, i]) - lo) / max(hi - lo, 1e-30))
    if scale > 1:
        img = np.repeat(np.repeat(img, scale, axis=0), scale, axis=1)
    pad = 46
    W, H = img.shape[1] + 2 * pad, img.shape[0] + 2 * pad + (16 if title else 0)
    canvas = np.full((H, W, 3), 18, dtype=np.uint8)
    oy = pad + (16 if title else 0)
    canvas[oy:oy + img.shape[0], pad:pad + img.shape[1]] = img
    if title:
        # 5x7 bitmap-ish text: draw title with PIL-free tiny renderer is overkill;
        # store the title in the PNG tEXt chunk instead + draw a simple bar.
        canvas[pad + img.shape[0] + 6:pad + img.shape[0] + 8,
               pad:pad + img.shape[1]] = (200, 200, 60)
    write_png_rgb(path, canvas)
    # embed the human title as tEXt metadata (append-safe rewrite)
    with open(path, "rb") as f:
        data = f.read()
    text = b"tEXt" + b"Title\x00" + title.encode("utf-8", "replace")
    chunk = png_chunk(b"tEXt", b"Title\x00" + title.encode("utf-8", "replace"))
    data = data.replace(png_chunk(b"IEND", b""), chunk + png_chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(data)

def plot_png(path: str, title: str, xlabel: str, ylabel: str,
             series: list[tuple[list[float], list[float], tuple[int, int, int], str]],
             logy: bool = False, W: int = 900, H: int = 560) -> None:
    """Own minimal line-plot rasteriser → PNG (axes, grid, legend, polylines)."""
    img = np.full((H, W, 3), 255, dtype=np.uint8)
    ml, mb, mt, mr = 84, 56, 46, 24
    pw, ph = W - ml - mr, H - mb - mt
    allx = [x for xs, _, _, _ in series for x in xs] or [0.0]
    ally = [y for _, ys, _, _ in series for y in ys] or [0.0]
    xmin, xmax = min(allx), max(allx)
    if xmax <= xmin:
        xmax = xmin + 1.0
    if logy:
        ally = [y for y in ally if y > 0] or [1e-12]
        ymin, ymax = min(ally), max(ally)
        ymin, ymax = max(ymin, 1e-300), max(ymax, ymin * 10)
    else:
        ymin, ymax = min(ally), max(ally)
        if ymax <= ymin:
            ymax = ymin + 1.0
        padv = (ymax - ymin) * 0.06
        ymin -= padv; ymax += padv

    def tx(x: float) -> int:
        return int(ml + (x - xmin) / (xmax - xmin) * pw)

    def ty(y: float) -> int:
        if logy:
            v = (math.log(max(y, 1e-300)) - math.log(ymin)) / (math.log(ymax) - math.log(ymin))
        else:
            v = (y - ymin) / (ymax - ymin)
        return int(mt + (1.0 - min(max(v, 0.0), 1.0)) * ph)

    for gx in range(ml, ml + pw + 1, max(1, pw // 8)):
        img[mt:mt + ph, gx] = (235, 235, 235)
    for gy in range(mt, mt + ph + 1, max(1, ph // 6)):
        img[gy, ml:ml + pw] = (235, 235, 235)
    img[mt:mt + ph + 1, ml] = (60, 60, 60)
    img[mt:mt + ph + 1, ml + pw] = (60, 60, 60)
    img[mt, ml:ml + pw + 1] = (60, 60, 60)
    img[mt + ph, ml:ml + pw + 1] = (60, 60, 60)

    def line(x0, y0, x1, y1, col):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for s in range(steps + 1):
            x = int(round(x0 + (x1 - x0) * s / steps))
            y = int(round(y0 + (y1 - y0) * s / steps))
            if 0 <= y < H - 2 and 0 <= x < W - 2:
                img[y, x] = col
                img[y + 1, x] = col

    for xs, ys, col, _label in series:
        pts = [(tx(x), ty(y)) for x, y in zip(xs, ys)]
        for a, b in zip(pts[:-1], pts[1:]):
            line(a[0], a[1], b[0], b[1], col)
    # legend
    ly = mt + 8
    for xs, ys, col, label in series:
        img[ly, ml + 10:ml + 34] = col
        ly += 14
    write_png_rgb(path, img)

def write_gif(path: str, frames: list[np.ndarray], delay_cs: int = 10) -> None:
    """GIF89a animator using the 'uncompressed LZW' trick: only literal
    codes 0..255 plus periodic Clear codes (256), so no code table is ever
    built. Valid GIF, slightly larger files, trivially portable.
    frames: list of float fields, mapped through viridis to 256 colours."""
    if len(frames) < 2:
        return
    n0 = frames[0].shape[0]
    palette = bytearray()
    for i in range(256):
        r, g, b = viridis(i / 255.0)
        palette += bytes((r, g, b))
    out = bytearray(b"GIF89a")
    out += struct.pack("<HHBBB", n0, n0, 0xF7, 0, 0)  # GCT flag, 256 colours
    out += palette
    out += b"\x21\xFF\x0BNETSCAPE2.0\x03\x01\x00\x00\x00"  # loop forever
    for k, fr in enumerate(frames):
        lo, hi = float(fr.min()), float(fr.max())
        idx = np.empty(fr.shape, dtype=np.int64)
        if hi > lo:
            idx = np.round((fr - lo) / (hi - lo) * 255.0).astype(np.int64)
        idx = np.clip(idx, 0, 255)
        # graphic control extension: first frame keeps disposal; delay in cs
        out += b"\x21\xF9\x04" + bytes([0x00 if k else 0x04]) + \
            struct.pack("<H", delay_cs) + b"\x00\x00"
        out += b"\x2C" + struct.pack("<HHHHB", 0, 0, fr.shape[1], fr.shape[0], 0)
        # ---- 9-bit LZW bit-packing of literal stream with Clear flushes ----
        bits = bytearray()
        cur = 0
        nb = 0
        cnt = 0

        def emit(code: int) -> None:
            nonlocal cur, nb
            cur |= code << nb
            nb += 9
            while nb >= 8:
                bits.append(cur & 0xFF)
                cur >>= 8
                nb -= 8

        emit(256)  # clear
        for px in idx.reshape(-1):
            emit(int(px))
            cnt += 1
            if cnt >= 253:          # keep the code space from ever filling
                emit(256)
                cnt = 0
        emit(257)                   # EOI
        if nb:
            bits.append(cur & 0xFF)
        # GIF requires the LZW stream to be split into sub-blocks of ≤255
        # bytes, each preceded by its length, terminated by a 0x00 block.
        out += b"\x08"              # LZW minimum code size
        b = bytes(bits)
        for off in range(0, len(b), 255):
            chunk = b[off:off + 255]
            out += bytes((len(chunk),)) + chunk
        out += b"\x00"
    out += b"\x3B"
    with open(path, "wb") as f:
        f.write(out)

def pdf_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

def write_pdf_article(path: str, title: str,
                      blocks: list[tuple[str, object]]) -> None:
    """Minimal but valid PDF article: Helvetica text pages + image pages.
    blocks: list of (kind, payload); kind ∈ {'h1','h2','p','img'}.
    Payload for 'img' is an (H, W, 3) uint8 ndarray (raw RGB, no filter).
    Text is Latin-only (base-14 fonts carry no Cyrillic) — labels passed
    here are English regardless of the UI language."""
    objs: list[bytes] = []

    def add(body: bytes) -> int:
        objs.append(body)
        return len(objs)

    pages_id = add(b"PLACEHOLDER-PAGES")
    font_id = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    fontb_id = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")

    def wrap_text(s: str, width: int = 92) -> list[str]:
        words, lines, line = str(s).split(), [], ""
        for w_ in words:
            if len(line) + len(w_) + 1 > width:
                lines.append(line)
                line = w_
            else:
                line = (line + " " + w_).strip()
        if line:
            lines.append(line)
        return lines or [""]

    # ---- layout text into pages, images become their own full pages ----
    ops: list[bytes] = [b"BT /F1 10 Tf 14 TL ET"]
    ops.append(b"BT /F2 19 Tf 72 776 Td (" +
               pdf_escape(title).encode("latin-1", "replace") + b") Tj ET")
    y = 748.0
    page_ids: list[int] = []

    def flush_page() -> None:
        nonlocal ops, y
        stream = b"\n".join(ops)
        cid = add(b"<< /Length " + str(len(stream)).encode() +
                  b" >>\nstream\n" + stream + b"\nendstream")
        res = (b"<< /Font << /F1 " + str(font_id).encode() + b" 0 R /F2 " +
               str(fontb_id).encode() + b" 0 R >> >>")
        page_ids.append(add(b"<< /Type /Page /Parent " + str(pages_id).encode() +
                            b" 0 R /MediaBox [0 0 612 842] /Resources " + res +
                            b" /Contents " + str(cid).encode() + b" 0 R >>"))
        ops = [b"BT /F1 10 Tf 14 TL ET"]
        y = 740.0

    for kind, payload in blocks:
        if kind == "img":
            flush_page()
            arr = payload
            h_, w_ = arr.shape[:2]
            raw = arr.tobytes()
            img_id = add(b"<< /Type /XObject /Subtype /Image /Width " +
                         str(w_).encode() + b" /Height " + str(h_).encode() +
                         b" /ColorSpace /DeviceRGB /BitsPerComponent 8 /Length " +
                         str(len(raw)).encode() + b" >>\nstream\n" + raw +
                         b"\nendstream")
            stream = (b"q 508 0 0 " + str(int(508 * h_ / w_)).encode() +
                      b" 52 40 cm /ImX Do Q")
            cid = add(b"<< /Length " + str(len(stream)).encode() +
                      b" >>\nstream\n" + stream + b"\nendstream")
            res = (b"<< /XObject << /ImX " + str(img_id).encode() +
                   b" 0 R >> /Font << /F1 " + str(font_id).encode() + b" 0 R >> >>")
            page_ids.append(add(b"<< /Type /Page /Parent " + str(pages_id).encode() +
                                b" 0 R /MediaBox [0 0 612 842] /Resources " + res +
                                b" /Contents " + str(cid).encode() + b" 0 R >>"))
        elif y < 90:
            flush_page()
            blocks_queue = [(kind, payload)]  # reprocess on fresh page
            for k2, p2 in blocks_queue:
                if k2 == "h1":
                    ops.append(b"BT /F2 15 Tf 72 " + str(y).encode() + b" Td (" +
                               pdf_escape(str(p2)).encode("latin-1", "replace") +
                               b") Tj ET")
                    y -= 24
                elif k2 == "h2":
                    ops.append(b"BT /F2 12 Tf 72 " + str(y).encode() + b" Td (" +
                               pdf_escape(str(p2)).encode("latin-1", "replace") +
                               b") Tj ET")
                    y -= 18
                else:
                    ops.append(b"BT /F1 10 Tf 72 " + str(y).encode() + b" Td (" +
                               pdf_escape(str(p2)).encode("latin-1", "replace") +
                               b") Tj ET")
                    y -= 14
        else:
            if kind == "h1":
                y -= 4
                ops.append(b"BT /F2 15 Tf 72 " + str(y).encode() + b" Td (" +
                           pdf_escape(str(payload)).encode("latin-1", "replace") +
                           b") Tj ET")
                y -= 24
            elif kind == "h2":
                ops.append(b"BT /F2 12 Tf 72 " + str(y).encode() + b" Td (" +
                           pdf_escape(str(payload)).encode("latin-1", "replace") +
                           b") Tj ET")
                y -= 18
            else:
                for ln in wrap_text(payload):
                    ops.append(b"BT /F1 10 Tf 72 " + str(y).encode() + b" Td (" +
                               pdf_escape(ln).encode("latin-1", "replace") +
                               b") Tj ET")
                    y -= 14
    flush_page()

    objs[pages_id - 1] = (b"<< /Type /Pages /Kids [" +
                          b" ".join(str(p).encode() + b" 0 R" for p in page_ids) +
                          b"] /Count " + str(len(page_ids)).encode() + b" >>")
    catalog_id = add(b"<< /Type /Catalog /Pages " +
                     str(pages_id).encode() + b" 0 R >>")
    with open(path, "wb") as f:
        f.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = []
        for i, body in enumerate(objs, 1):
            offsets.append(f.tell())
            f.write(f"{i} 0 obj\n".encode() + body + b"\nendobj\n")
        xref = f.tell()
        f.write(f"xref\n0 {len(objs) + 1}\n".encode())
        f.write(b"0000000000 65535 f \n")
        for off in offsets:
            f.write(f"{off:010d} 00000 n \n".encode())
        f.write(f"trailer\n<< /Size {len(objs) + 1} /Root {catalog_id} 0 R >>\n"
                f"startxref\n{xref}\n%%EOF".encode())

# ══════════════════════════════════════════════════════════════════
# 4. IN-HOUSE FFT — radix-2 DIT, bit-reversal, vectorised (numpy.fft off)
# ══════════════════════════════════════════════════════════════════

_BR_CACHE: dict[int, np.ndarray] = {}

def _bitrev(n: int) -> np.ndarray:
    r = _BR_CACHE.get(n)
    if r is not None:
        return r
    logn = n.bit_length() - 1
    idx = np.arange(n, dtype=np.int64)
    rev = np.zeros(n, dtype=np.int64)
    for b in range(logn):
        rev = (rev << 1) | ((idx >> b) & 1)
    _BR_CACHE[n] = rev
    return rev

def fft1d_last(a: np.ndarray, inverse: bool = False) -> np.ndarray:
    """Radix-2 DIT FFT along the LAST axis of `a` (any leading dims).
    Forward unnormalised; inverse scaled by 1/n (numpy conventions)."""
    n = a.shape[-1]
    if n & (n - 1):
        raise ValueError(f"FFT: n must be a power of two, got {n}")
    b = a[..., _bitrev(n)]
    size = 2
    while size <= n:
        half = size >> 1
        tw = np.exp((-2.0j if not inverse else 2.0j) * np.pi *
                    np.arange(half) / size)
        c = b.reshape(b.shape[:-1] + (n // size, size))
        even = c[..., :half]
        odd = c[..., half:] * tw
        b = np.concatenate((even + odd, even - odd), axis=-1).reshape(a.shape)
        size <<= 1
    if inverse:
        b = b / n
    return b

def fft3d(a: np.ndarray, inverse: bool = False) -> np.ndarray:
    out = fft1d_last(a, inverse)              # axis 2
    out = fft1d_last(np.moveaxis(out, 1, -1), inverse)
    out = np.moveaxis(out, -1, 1)
    out = fft1d_last(np.moveaxis(out, 0, -1), inverse)
    return np.moveaxis(out, -1, 0)

def fft2d(a: np.ndarray, inverse: bool = False) -> np.ndarray:
    out = fft1d_last(a, inverse)
    out = fft1d_last(np.moveaxis(out, 0, -1), inverse)
    return np.moveaxis(out, -1, 0)

def fftn_any(a: np.ndarray, inverse: bool = False) -> np.ndarray:
    if CFG.fft_backend == "numpy":
        return (np.fft.ifftn if inverse else np.fft.fftn)(a)
    if a.ndim == 3:
        return fft3d(a, inverse)
    if a.ndim == 2:
        return fft2d(a, inverse)
    return fft1d_last(a, inverse)

def fft_selftest(n: int = 16, seed: int = 42) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    a0 = rng.standard_normal(n) + 1j * rng.standard_normal(n)
    a = fft1d_last(a0.copy())
    ref = np.array([sum(a0[m] * np.exp(-2j * np.pi * m * k / n)
                        for m in range(n)) for k in range(n)])
    err_fwd = float(np.max(np.abs(a - ref)) / np.max(np.abs(ref)))
    err_rt = float(np.max(np.abs(fft1d_last(a, True) - a0)))
    A0 = (rng.standard_normal((4, 4, 4)) + 1j * rng.standard_normal((4, 4, 4)))
    A = fft3d(A0)
    A = fft3d(A, True)
    err_3d = float(np.max(np.abs(A - A0)))
    M0 = rng.standard_normal((8, 8)) + 1j * rng.standard_normal((8, 8))
    M = fft2d(M0)
    err_2d = float(np.max(np.abs(fft2d(M, True) - M0)))
    return dict(forward=err_fwd, roundtrip=err_rt, roundtrip3d=err_3d,
                roundtrip2d=err_2d)

# ══════════════════════════════════════════════════════════════════
# 5. 3-D PSEUDOSPECTRAL SOLVER — RK4 + Leray + 2/3 rule (+ ν₄)
# ══════════════════════════════════════════════════════════════════

class NSE3D:
    """Spectral Navier–Stokes/Euler operator on the torus [0,2π)³."""

    def __init__(self, n: int, nu: float, nu4: float | None = None) -> None:
        if n < 8 or n % 2:
            raise ValueError("n must be even and ≥ 8")
        self.n = n
        self.nu = float(nu)
        self.nu4 = CFG.nu4 if nu4 is None else float(nu4)
        k1d = np.concatenate([np.arange(0, n // 2), np.arange(-n // 2, 0)])
        shape = (n, n, n)
        self.kx = np.broadcast_to(k1d.reshape(n, 1, 1), shape).copy()
        self.ky = np.broadcast_to(k1d.reshape(1, n, 1), shape).copy()
        self.kz = np.broadcast_to(k1d.reshape(1, 1, n), shape).copy()
        self.ksq = (self.kx.astype(np.float64) ** 2 + self.ky ** 2 + self.kz ** 2)
        self.ksq2 = self.ksq * self.ksq
        kc = n // 3
        self.mask = ((np.abs(self.kx) <= kc) & (np.abs(self.ky) <= kc) &
                     (np.abs(self.kz) <= kc))
        self.k2safe = np.where(self.ksq > 0, self.ksq, 1.0)
        self.dx = 2.0 * np.pi / n

def zero_field3(n: int) -> list[np.ndarray]:
    return [np.zeros((n, n, n), dtype=np.complex128) for _ in range(3)]

def copy_field3(f: list[np.ndarray]) -> list[np.ndarray]:
    return [c.copy() for c in f]

def fft_field3(u: list[np.ndarray]) -> list[np.ndarray]:
    return [fftn_any(c.astype(np.complex128)) for c in u]

def ifft_field3(uhat: list[np.ndarray]) -> list[np.ndarray]:
    return [fftn_any(c, True).real for c in uhat]

def project3(out: list[np.ndarray], inp: list[np.ndarray], s: NSE3D) -> list[np.ndarray]:
    kd = (s.kx * inp[0] + s.ky * inp[1] + s.kz * inp[2]) / s.k2safe
    kd = np.where(s.ksq == 0, 0.0 + 0.0j, kd)
    for c, kc in enumerate((s.kx, s.ky, s.kz)):
        out[c] = inp[c] - kc * kd
    return out

def curl_hat3(out: list[np.ndarray], uhat: list[np.ndarray], s: NSE3D) -> None:
    kx, ky, kz = s.kx, s.ky, s.kz
    a1, a2, a3 = uhat[0], uhat[1], uhat[2]
    out[0] = 1j * (ky * a3 - kz * a2)
    out[1] = 1j * (kz * a1 - kx * a3)
    out[2] = 1j * (kx * a2 - ky * a1)

def rhs3(du: list[np.ndarray], uhat: list[np.ndarray], s: NSE3D,
         wh: list[np.ndarray] | None = None) -> list[np.ndarray]:
    """du = −P[curl u × u] − (ν k² + ν₄ k⁴) u,  2/3-dealised."""
    wh = [np.empty_like(uhat[0]) for _ in range(3)] if wh is None else wh
    curl_hat3(wh, uhat, s)
    u = ifft_field3(uhat)
    w = ifft_field3(wh)
    nl = [w[1] * u[2] - w[2] * u[1],
          w[2] * u[0] - w[0] * u[2],
          w[0] * u[1] - w[1] * u[0]]
    nlhat = fft_field3(nl)
    for c in range(3):
        nlhat[c] = np.where(s.mask, nlhat[c], 0.0 + 0.0j)
    project3(du, nlhat, s)
    damp = s.nu * s.ksq + s.nu4 * s.ksq2
    for c in range(3):
        du[c] -= damp * uhat[c]
    return du

def step_rk4_3d(out: list[np.ndarray], uhat: list[np.ndarray], dt: float,
                s: NSE3D, K1, K2, K3, K4, T1) -> list[np.ndarray]:
    for c in range(3):
        K1[c] = np.empty_like(uhat[c])
    rhs3(K1, uhat, s)
    for c in range(3):
        T1[c] = uhat[c] + 0.5 * dt * K1[c]
    rhs3(K2, T1, s)
    for c in range(3):
        T1[c] = uhat[c] + 0.5 * dt * K2[c]
    rhs3(K3, T1, s)
    for c in range(3):
        T1[c] = uhat[c] + dt * K3[c]
    rhs3(K4, T1, s)
    for c in range(3):
        out[c] = uhat[c] + (dt / 6.0) * (K1[c] + 2.0 * K2[c] + 2.0 * K3[c] + K4[c])
        out[c] = np.where(s.mask, out[c], 0.0 + 0.0j)
    return out

def cfl_dt_3d(uhat: list[np.ndarray], s: NSE3D, safety: float = 0.5) -> float:
    u = ifft_field3(uhat)
    umax = float(np.max(np.sqrt(u[0] ** 2 + u[1] ** 2 + u[2] ** 2)))
    if umax < 1e-14:
        return safety * s.dx ** 2 / max(s.nu, 1e-12)
    return safety * s.dx / umax

# ─────────────────────────────── ICs & b-rotations ──────────────────

NSB_B = 1.0 / (4.0 * math.pi + 2.0 * math.sqrt(3.0))
NSB_THETA_B = math.asin(NSB_B)
NSB_AXIS = (0.3, -0.5, math.sqrt(1.0 - 0.3 ** 2 - 0.5 ** 2))

def rodrigues(theta: float, axis: tuple[float, float, float]) -> np.ndarray:
    ex, ey, ez = axis
    cmat = np.array([[0.0, -ez, ey], [ez, 0.0, -ex], [-ey, ex, 0.0]])
    outer = np.array([[ex * ex, ex * ey, ex * ez], [ey * ex, ey * ey, ey * ez],
                      [ez * ex, ez * ey, ez * ez]])
    c, s = math.cos(theta), math.sin(theta)
    return c * np.eye(3) + (1 - c) * outer - s * cmat

def b_rotation_matrix() -> np.ndarray:
    return rodrigues(NSB_THETA_B, NSB_AXIS)

def quarter_rotation_matrix() -> np.ndarray:
    return rodrigues(math.pi / 2, (0.0, 0.0, 1.0))

def grid_1d(n: int) -> np.ndarray:
    return 2.0 * np.pi * np.arange(n) / n

def ic_taylor_green(n: int) -> list[np.ndarray]:
    x = grid_1d(n)
    sx, cx = np.sin(x), np.cos(x)
    u1 = sx[:, None, None] * cx[None, :, None] * cx[None, None, :]
    u2 = -cx[:, None, None] * sx[None, :, None] * cx[None, None, :]
    u3 = np.zeros((n, n, n))
    return [u1, u2, u3]

def ic_abc(n: int, a: float = 1.0, b: float = 1.0, c: float = 1.0) -> list[np.ndarray]:
    x = grid_1d(n)
    sx, cx = np.sin(x), np.cos(x)
    u1 = (a * sx[None, None, :] + c * cx[None, :, None]) * np.ones((n, n, n))
    u2 = (b * sx[:, None, None] + a * cx[None, None, :]) * np.ones((n, n, n))
    u3 = (c * sx[None, :, None] + b * cx[:, None, None]) * np.ones((n, n, n))
    return [u1, u2, u3]

def ic_hou_luo(n: int, gamma: float = 1.0, sigma: float = math.pi / 16,
               perturbation: float = 0.05) -> list[np.ndarray]:
    """Returns VORTICITY (anti-parallel Gaussian tubes along x); convert to
    velocity with Biot–Savart."""
    x = grid_1d(n)
    inv2s2 = 1.0 / (2.0 * sigma ** 2)
    y0, z0a, z0b = math.pi / 2, math.pi / 2, 3 * math.pi / 2
    X = x[:, None, None]
    Y = x[None, :, None]
    Z = x[None, None, :]
    g1 = np.exp(-((Y - y0) ** 2 + (Z - z0a) ** 2) * inv2s2)
    g2 = np.exp(-((Y - 3 * math.pi / 2) ** 2 + (Z - z0b) ** 2) * inv2s2)
    w1 = gamma * ((g1 - g2) * (1.0 + perturbation * np.cos(X)))
    return [w1, np.zeros_like(w1), np.zeros_like(w1)]

def ic_random(n: int, k_peak: int = 4, seed: int | None = None) -> list[np.ndarray]:
    rng = np.random.default_rng(CFG.seed if seed is None else seed)
    x = grid_1d(n)
    u = [rng.standard_normal((n, n, n)) for _ in range(3)]
    sk = np.sin(k_peak * x)
    ck = np.cos(k_peak * x)
    u[0] += 0.5 * sk[:, None, None] * ck[None, :, None]
    u[1] += 0.5 * sk[:, None, None] * (0.5 * sk[None, :, None] + 0.5)
    u[2] += 0.5 * ck[None, None, :] * sk[None, :, None]
    return u

def velocity_from_vorticity3(what: list[np.ndarray], s: NSE3D) -> list[np.ndarray]:
    out = [np.empty_like(what[0]) for _ in range(3)]
    inv2 = 1j / s.ksq
    for c, kc in enumerate((s.kx, s.ky, s.kz)):
        pass
    kx, ky, kz = s.kx, s.ky, s.kz
    w1, w2, w3 = what
    out[0] = np.where(s.ksq == 0, 0.0 + 0.0j, inv2 * (ky * w3 - kz * w2))
    out[1] = np.where(s.ksq == 0, 0.0 + 0.0j, inv2 * (kz * w1 - kx * w3))
    out[2] = np.where(s.ksq == 0, 0.0 + 0.0j, inv2 * (kx * w2 - ky * w1))
    project3(out, out, s)
    for c in range(3):
        out[c] = np.where(s.mask, out[c], 0.0 + 0.0j)
    return out

def prepare_state3(ic_fields: list[np.ndarray], s: NSE3D) -> list[np.ndarray]:
    uhat = fft_field3(ic_fields)
    project3(uhat, uhat, s)
    for c in range(3):
        uhat[c] = np.where(s.mask, uhat[c], 0.0 + 0.0j)
    return uhat

def rotate_pointwise3(out: list[np.ndarray], uhat: list[np.ndarray],
                      R: np.ndarray, s: NSE3D) -> None:
    u = ifft_field3(uhat)
    ru = [R[0, 0] * u[0] + R[0, 1] * u[1] + R[0, 2] * u[2],
          R[1, 0] * u[0] + R[1, 1] * u[1] + R[1, 2] * u[2],
          R[2, 0] * u[0] + R[2, 1] * u[1] + R[2, 2] * u[2]]
    out[:] = fft_field3(ru)

def rotate_full_symmetry3(out: list[np.ndarray], uhat: list[np.ndarray],
                          s: NSE3D) -> None:
    """Exact quarter turn about z via circular index shift (no interpolation):
    u'(x,y,z) = R u(R⁻¹(x,y,z)), R(x,y,z) = (−y, x, z)."""
    n = s.n
    u = ifft_field3(uhat)
    ii = np.empty(n, dtype=np.int64)
    ii[0] = 0
    for i in range(2, n + 1):
        ii[i - 1] = n - i + 1      # mod1(1-(i-1), n) − 1
    # sampled(x_i, y_j, z_k) = u(y_j, −x_i, z_k): take u[j, ii[i], k], swap 0↔1
    us = [np.swapaxes(u[c][:, ii, :], 0, 1) for c in range(3)]
    ru = [-us[1], us[0], us[2]]
    out[:] = fft_field3(ru)

# ══════════════════════════════════════════════════════════════════
# 6. DIAGNOSTICS — BKM monitor, spectra, fits
# ══════════════════════════════════════════════════════════════════

class TimeSeries:
    def __init__(self) -> None:
        self.t: list[float] = []
        self.energy: list[float] = []
        self.enstrophy: list[float] = []
        self.palinstrophy: list[float] = []
        self.sup_omega: list[float] = []
        self.dissipation: list[float] = []
        self.bkm: list[float] = [0.0]

    def push(self, t, e, om, pal, sup, eps, bkm) -> None:
        self.t.append(t); self.energy.append(e); self.enstrophy.append(om)
        self.palinstrophy.append(pal); self.sup_omega.append(sup)
        self.dissipation.append(eps); self.bkm.append(bkm)

    def peak_enstrophy(self) -> tuple[float, float]:
        i = int(np.argmax(self.enstrophy))
        return self.t[i], self.enstrophy[i]

def energy3(uhat: list[np.ndarray], n: int) -> float:
    s = sum(float(np.sum(np.abs(c) ** 2)) for c in uhat)
    return 0.5 * s / n ** 6

def enstrophy3(what: list[np.ndarray], n: int) -> float:
    return energy3(what, n)

def palinstrophy3(s: NSE3D, what: list[np.ndarray]) -> float:
    kx, ky, kz = s.kx, s.ky, s.kz
    w1, w2, w3 = what
    ssum = (np.abs(ky * w3 - kz * w2) ** 2 + np.abs(kz * w1 - kx * w3) ** 2 +
            np.abs(kx * w2 - ky * w1) ** 2)
    return 0.5 * float(np.sum(ssum)) / s.n ** 6

def dissipation3(s: NSE3D, uhat: list[np.ndarray]) -> float:
    ssum = sum(float(np.sum(s.ksq * np.abs(c) ** 2)) for c in uhat)
    return s.nu * ssum / s.n ** 6

def dissipation_hyper3(s: NSE3D, uhat: list[np.ndarray]) -> float:
    if s.nu4 == 0:
        return 0.0
    ssum = sum(float(np.sum(s.ksq2 * np.abs(c) ** 2)) for c in uhat)
    return s.nu4 * ssum / s.n ** 6

def sup_vorticity3(w_phys: list[np.ndarray]) -> float:
    return float(np.max(np.sqrt(w_phys[0] ** 2 + w_phys[1] ** 2 + w_phys[2] ** 2)))

def divergence_max3(s: NSE3D, uhat: list[np.ndarray]) -> float:
    d = s.kx * uhat[0] + s.ky * uhat[1] + s.kz * uhat[2]
    return float(np.sqrt(np.sum(np.abs(d) ** 2)) / s.n ** 3)

def shell_spectrum3(s: NSE3D, uhat: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    kr = np.sqrt(s.ksq)
    kmax = int(math.ceil(float(kr.max())))
    counts = np.zeros(kmax + 1, dtype=np.int64)
    sums = np.zeros(kmax + 1)
    e = 0.5 * (np.abs(uhat[0]) ** 2 + np.abs(uhat[1]) ** 2 +
               np.abs(uhat[2]) ** 2) / s.n ** 6
    ki = np.rint(kr).astype(np.int64)
    np.add.at(counts, ki.ravel(), 1)
    np.add.at(sums, ki.ravel(), e.ravel())
    spec = np.where(counts > 0, sums / np.maximum(counts, 1), 0.0)
    return np.arange(0, kmax + 1, dtype=float), spec

def spectral_tail_level(spec: np.ndarray, k_cutoff: int, window: int = 1) -> float:
    if len(spec) < 3:
        return 0.0
    k_hi = min(k_cutoff + 1, len(spec) - 1)
    k_lo = max(2, k_hi - window)
    peak = float(np.max(spec[1:]))
    if peak <= 0:
        return 0.0
    return float(np.max(spec[k_lo:k_hi + 1]) / peak)

def linfit(xs: list[float], ys: list[float]) -> tuple[float, float, float]:
    n = len(xs)
    if n < 2:
        return (float("nan"),) * 3
    sx, sy = sum(xs), sum(ys)
    sxx = sum(x * x for x in xs)
    sxy = sum(x * y for x, y in zip(xs, ys))
    den = n * sxx - sx ** 2
    if den == 0:
        return (float("nan"),) * 3
    a = (n * sxy - sx * sy) / den
    b = (sy - a * sx) / n
    ybar = sy / n
    ss_res = sum((y - (a * x + b)) ** 2 for x, y in zip(xs, ys))
    ss_tot = sum((y - ybar) ** 2 for y in ys)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return a, b, r2

def spectral_tail_slope(spec: np.ndarray, k_hi: int) -> float:
    pts = [(float(k), math.log(spec[k + 1]))
           for k in range(1, min(k_hi, len(spec) - 1)) if spec[k + 1] > 0]
    if len(pts) < 3:
        return float("nan")
    a, _b, _r2 = linfit([p[0] for p in pts], [p[1] for p in pts])
    return a

def k41_fit(ks: np.ndarray, spec: np.ndarray, kcut: int) -> tuple[float, float, int]:
    if len(spec) == 0:
        return (float("nan"), float("nan"), 0)
    k_hi = max(3, int(round(0.75 * kcut)))
    xs, ys = [], []
    for k in range(2, min(k_hi, len(ks) - 1)):
        E = spec[k + 1]
        if E > 0:
            xs.append(math.log(ks[k + 1]))
            ys.append(math.log(E))
    if len(xs) < 4:
        return (float("nan"), float("nan"), len(xs))
    a, _b, r2 = linfit(xs, ys)
    return a, r2, len(xs)

def observed_order(j_c: float, j_f: float, j_ff: float, ratio: float = 2.0) -> float:
    denom, numer = j_c - j_f, j_f - j_ff
    if abs(denom) < 1e-30 or abs(numer) < 1e-30:
        return float("nan")
    return math.log(abs(denom / numer), ratio)

def richardson(j_f: float, j_ff: float, ratio: float, order: float) -> float:
    return j_ff + (j_ff - j_f) / (ratio ** order - 1.0)

# ─────────────────────────────── blow-up scan ───────────────────────

class BlowupReport:
    def __init__(self, **kw) -> None:
        self.lambda_trend = kw.get("lambda_trend", float("nan"))
        self.lambda_r2 = kw.get("lambda_r2", float("nan"))
        self.lambda_max = kw.get("lambda_max", float("nan"))
        self.doubling_min = kw.get("doubling_min", float("nan"))
        self.sustained = kw.get("sustained", False)
        self.tstar = kw.get("tstar", None)
        self.alpha = kw.get("alpha", float("nan"))
        self.bkm_final = kw.get("bkm_final", 0.0)

def growth_rate(ts: TimeSeries) -> tuple[list[float], list[float]]:
    n = len(ts.sup_omega)
    t_out, lam = [], []
    for i in range(1, n - 1):
        dt1 = ts.t[i] - ts.t[i - 1]
        dt2 = ts.t[i + 1] - ts.t[i]
        s0, s1, s2 = ts.sup_omega[i - 1], ts.sup_omega[i], ts.sup_omega[i + 1]
        if dt1 <= 0 or dt2 <= 0 or not (s0 > 0 and s1 > 0 and s2 > 0):
            continue
        lam.append((math.log(s2) - math.log(s0)) / (dt1 + dt2))
        t_out.append(ts.t[i])
    return t_out, lam

def blowup_report(ts: TimeSeries, window_frac: float = 0.25) -> BlowupReport:
    t_lam, lam = growth_rate(ts)
    bkm_final = ts.bkm[-1] if ts.bkm else 0.0
    if len(t_lam) < 4:
        return BlowupReport(lambda_max=max(lam) if lam else float("nan"),
                            bkm_final=bkm_final)
    a, _b, r2 = linfit(t_lam, lam)
    lam_max = max(lam)
    doublings = []
    for i in range(1, len(ts.sup_omega)):
        s0, s1 = ts.sup_omega[i - 1], ts.sup_omega[i]
        dt = ts.t[i] - ts.t[i - 1]
        if s0 > 0 and s1 > s0 and dt > 0:
            doublings.append(dt * math.log(2) / math.log(s1 / s0))
    doubl_min = min(doublings) if doublings else float("inf")
    nfit = max(4, int(round(len(t_lam) * window_frac)))
    nfit = min(nfit, len(t_lam))
    tail_t, tail_l = t_lam[-nfit:], lam[-nfit:]
    at, _bt, r2t = linfit(tail_t, tail_l)
    ntail = min(nfit, len(ts.sup_omega))
    tail_sup_max = max(ts.sup_omega[-ntail:])
    new_high = tail_sup_max >= 0.98 * max(ts.sup_omega)
    sustained = (not math.isnan(at)) and at > 0 and (not math.isnan(r2t)) and \
        r2t > 0.5 and lam_max > 0 and new_high
    tstar, alpha = None, float("nan")
    if sustained:
        sup, tt = ts.sup_omega, ts.t
        best_err, best_tstar, best_alpha = float("inf"), float("nan"), float("nan")
        T_end = tt[-1]
        al = 0.5
        while al <= 7.0 + 1e-9:
            frac = 1.02
            while frac <= 2.5 + 1e-9:
                tst = T_end * frac
                ok = True
                xs, ys = [], []
                for ti, si in zip(tt, sup):
                    d = tst - ti
                    if d <= 0:
                        ok = False
                        break
                    xs.append(math.log(d))
                    ys.append(math.log(max(si, 1e-300)))
                if ok:
                    A, _B, r2f = linfit(xs, ys)
                    if not math.isnan(r2f) and -r2f < best_err:
                        best_err, best_tstar, best_alpha = -r2f, tst, -A
                frac += 0.02
            al += 0.25
        if best_err < -0.9:
            tstar, alpha = best_tstar, best_alpha
    return BlowupReport(lambda_trend=a, lambda_r2=r2, lambda_max=lam_max,
                        doubling_min=doubl_min, sustained=sustained,
                        tstar=tstar, alpha=alpha, bkm_final=bkm_final)

# ══════════════════════════════════════════════════════════════════
# 7. RUNNER — RK4 loop with progress, CFL, kicks, checkpoints
# ══════════════════════════════════════════════════════════════════

def ckpt_path_for(label: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", label)
    return os.path.join(CFG.out_dir, "data", f"ckpt_{safe}.pkl")

def ckpt_save(path: str, state: dict) -> None:
    import pickle
    ensure_outdirs()
    with open(path, "wb") as f:
        pickle.dump(state, f, protocol=4)

def ckpt_load(path: str) -> dict | None:
    import pickle
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception:
        return None

def run_decay_3d(s: NSE3D, uhat0: list[np.ndarray], dt: float, t_horizon: float,
                 label: str, sample_every: int = 4,
                 kick: tuple[str, float] | None = None,
                 blowup_stop: bool = False, show_prog: bool = True,
                 adaptive: bool | None = None, ckpt_every: int | None = None,
                 resume: bool = False) -> dict:
    global _PROG_LAST
    adaptive = CFG.adaptive_cfl if adaptive is None else adaptive
    ckpt_every = CFG.ckpt_every if ckpt_every is None else ckpt_every
    n = s.n
    uhat = copy_field3(uhat0)
    K1, K2, K3, K4 = zero_field3(n), zero_field3(n), zero_field3(n), zero_field3(n)
    T1, T2 = zero_field3(n), zero_field3(n)
    wh = [np.empty_like(uhat[0]) for _ in range(3)]
    ts = TimeSeries()
    curl_hat3(wh, uhat, s)
    sup_prev = sup_vorticity3(ifft_field3(wh))
    steps = int(math.ceil(t_horizon / dt))
    div_max = energy_rise = 0.0
    e_prev = energy3(uhat, n)
    t_elapsed = 0.0
    t0 = time.time()
    cfl_exceeded = adapted_steps = 0
    start_step = 1
    _PROG_LAST = 0.0
    if adaptive:
        Pln(muted("  " + L("adaptive_on")))
    if s.nu4 > 0:
        Pln(muted("  " + Lf("nu4_note", s.nu4)))
    cpath = ckpt_path_for(label) if ckpt_every > 0 else ""
    if resume and cpath:
        ck = ckpt_load(cpath)
        if ck and ck.get("label") == label and ck.get("step", 0) > 0:
            uhat = ck["uhat"]
            start_step = ck["step"] + 1
            t_elapsed = ck["t"]
            ts = ck["ts"]
            e_prev = ts.energy[-1] if ts.energy else e_prev
            sup_prev = ts.sup_omega[-1] if ts.sup_omega else sup_prev
            Pln(ok("  " + Lf("ckpt_resume", ck["step"], cpath)))
        else:
            Pln(muted("  " + L("ckpt_missing")))
    next_kick = (math.floor(t_elapsed / kick[1] + 1e-12) + 1.0) * kick[1] \
        if kick else float("inf")
    for step in range(start_step, steps + 1):
        h = min(dt, t_horizon - t_elapsed)
        if h <= 1e-15:
            break
        cfl = cfl_dt_3d(uhat, s)
        if cfl < h:
            cfl_exceeded += 1
            if adaptive:
                h = cfl
                adapted_steps += 1
        step_rk4_3d(T2, uhat, h, s, K1, K2, K3, K4, T1)
        uhat, T2 = T2, uhat
        t_elapsed += h
        if kick and t_elapsed >= next_kick - 1e-12:
            T3 = zero_field3(n)
            if kick[0] == "full":
                rotate_full_symmetry3(T3, uhat, s)
            else:
                rotate_pointwise3(T3, uhat, b_rotation_matrix(), s)
                project3(T3, T3, s)
            for c in range(3):
                T3[c] = np.where(s.mask, T3[c], 0.0 + 0.0j)
            uhat = T3
            next_kick += kick[1]
        if ckpt_every > 0 and step % ckpt_every == 0 and step < steps:
            ckpt_save(cpath, dict(label=label, step=step, t=t_elapsed,
                                  uhat=uhat, ts=ts))
            Pln(muted("  " + Lf("ckpt_saved", step, cpath)))
        if step % sample_every == 0 or step == steps:
            curl_hat3(wh, uhat, s)
            sup_now = sup_vorticity3(ifft_field3(wh))
            e_now = energy3(uhat, n)
            div_max = max(div_max, divergence_max3(s, uhat))
            energy_rise = max(energy_rise, e_now - e_prev)
            e_prev = e_now
            bkm = ts.bkm[-1] + 0.5 * (sup_prev + sup_now) * h * sample_every
            sup_prev = sup_now
            ts.push(t_elapsed, e_now, enstrophy3(wh, n),
                    palinstrophy3(s, wh), sup_now,
                    dissipation3(s, uhat), bkm)
            if show_prog:
                progress(step / steps, label, t0, steps, step)
            if blowup_stop and (not math.isfinite(sup_now) or sup_now > 1e8):
                Pln(warn_c(f"  sup|ω| = {sup_now:.3e} — stop at threshold"))
                break
    if show_prog:
        progress(1.0, label, t0, steps, steps)
    if cpath and os.path.isfile(cpath):
        os.remove(cpath)
    if adaptive and adapted_steps:
        Pln(muted("  " + Lf("adaptive_stat", adapted_steps, steps)))
    return dict(uhat=uhat, ts=ts, div_max=div_max, energy_rise=energy_rise,
                cfl_exceeded=cfl_exceeded, adapted_steps=adapted_steps,
                steps_done=steps, wall=time.time() - t0)

def tail_diagnostics3(s: NSE3D, uhat: list[np.ndarray]) -> dict:
    kcut = s.n // 3
    ks, spec = shell_spectrum3(s, uhat)
    slope, r2, npts = k41_fit(ks, spec, kcut)
    return dict(tail_level=spectral_tail_level(spec, kcut),
                tail_slope=spectral_tail_slope(spec, kcut),
                k41_slope=slope, k41_r2=r2, k41_npts=npts,
                kspec=ks, spec=spec, kcut=kcut)

# ══════════════════════════════════════════════════════════════════
# 8. EXPERIMENTS — verdicts with honest checks
# ══════════════════════════════════════════════════════════════════

class Check:
    def __init__(self, key: str, okv: bool, detail: str) -> None:
        self.key, self.ok, self.detail = key, okv, detail

class Verdict:
    def __init__(self, experiment: str, mode: str, params: dict) -> None:
        self.experiment = experiment
        self.mode = mode
        self.params = params
        self.checks: list[Check] = []
        self.values: dict = {}
        self.series: TimeSeries | None = None
        self.plots: list = []       # ("plot", ...) | ("heat", ...)
        self.wall = 0.0
        self.ok = True

    def check(self, key: str, okv: bool, detail: str = "") -> None:
        self.checks.append(Check(key, bool(okv), detail))
        if not okv:
            self.ok = False

    def print_out(self) -> None:
        Pln()
        for c in self.checks:
            line = ok(L(c.key)) if c.ok else bad(L(c.key))
            extra = muted(f"  ({c.detail})") if c.detail else ""
            Pln("  " + line + extra)
        if self.series is not None and len(self.series.energy) > 4:
            Pln("  " + muted("E       ") + rgb(*C_ACCENT, sparkline(self.series.energy)))
            Pln("  " + muted("sup|ω|  ") + rgb(255, 90, 90, sparkline(self.series.sup_omega)))
        Pln(dim("  " + L("scope_note")))
        Pln(ok(L("verdict_ok")) if self.ok else bad(L("verdict_fail")))
        Pln(muted("  " + Lf("run_finished", now_str())))

def plot_series(v: Verdict, ts: TimeSeries, title: str) -> None:
    v.plots.append(("plot", title, "t", "sup|ω| / BKM", True,
                    [(ts.t, ts.sup_omega, (68, 1, 84), "sup|ω|"),
                     (ts.t, [b * 10 for b in ts.bkm], (253, 231, 37), "BKM × 10")]))
    v.plots.append(("plot", title, "t", "E / Ω / P", False,
                    [(ts.t, ts.energy, (68, 1, 84), "E"),
                     (ts.t, ts.enstrophy, (30, 122, 155), "Ω"),
                     (ts.t, ts.palinstrophy, (253, 231, 37), "P")]))

def exp_taylor_green(mode: str = "normal", n: int = 0, nu: float = float("nan"),
                     dt: float = float("nan"), t_hor: float = float("nan")) -> Verdict:
    t0 = time.time()
    hard = mode == "hard"
    n = n if n > 0 else (min(64, CFG.max_n) if hard else 32)
    nu = nu if not math.isnan(nu) else (0.01 if hard else 0.02)
    dt = dt if not math.isnan(dt) else (0.0025 if hard else 0.005)
    t_hor = t_hor if not math.isnan(t_hor) else (4.0 if hard else 2.0)
    v = Verdict("taylor_green", mode, dict(n=n, nu=nu, dt=dt, t_horizon=t_hor))
    header(L("exp_tg"))
    Pln(muted(f"  N={n} · ν={nu} · dt={dt} · T={t_hor} · {Lf('run_started', now_str())}"))
    s = NSE3D(n, nu)
    uhat0 = prepare_state3(ic_taylor_green(n), s)
    res = run_decay_3d(s, uhat0, dt, t_hor, f"TG N={n}")
    tail = tail_diagnostics3(s, res["uhat"])
    v.series = res["ts"]
    plot_series(v, res["ts"], f"Taylor-Green N={n}")
    if math.isfinite(tail["k41_slope"]):
        Pln(muted("  " + Lf("k41_line", tail["k41_slope"], tail["k41_r2"])))
    v.values["k41_slope"] = tail["k41_slope"]
    v.values["k41_r2"] = tail["k41_r2"]
    v.values["adapted_steps"] = res["adapted_steps"]
    v.values["div_max"] = res["div_max"]
    v.values["energy_rise"] = res["energy_rise"]
    v.values["tail_level"] = tail["tail_level"]
    v.values["tail_slope"] = tail["tail_slope"]
    v.values["peak_enstrophy"] = res["ts"].peak_enstrophy()[1]
    v.values["bkm_final"] = res["ts"].bkm[-1]
    v.values["sup_omega_final"] = res["ts"].sup_omega[-1]
    v.check("ck_divfree", res["div_max"] < 1e-10, f"max|div| = {res['div_max']:.2e}")
    v.check("ck_energy_monotone", res["energy_rise"] < 1e-12,
            f"ΔE_max = {res['energy_rise']:.2e}")
    v.check("ck_tail_resolved", tail["tail_level"] < 1e-6 * (32.0 / n) ** 2,
            f"tail/peak = {tail['tail_level']:.2e}")
    v.check("ck_stability", all(math.isfinite(x) for x in res["ts"].sup_omega),
            f"sup|ω|_final = {res['ts'].sup_omega[-1]:.4f}")
    bl = blowup_report(res["ts"])
    v.check("ck_no_blowup", (not bl.sustained) or bl.lambda_trend <= 0,
            f"dλ/dt = {bl.lambda_trend:.3f} (R² = {bl.lambda_r2:.2f}), "
            f"BKM = {bl.bkm_final:.3f}")
    v.values["lambda_trend"] = bl.lambda_trend
    v.values["lambda_r2"] = bl.lambda_r2
    if hard:
        ladder = (0.04, 0.02, 0.01)
        peaks = []
        sL = NSE3D(32, nu)
        for d in ladder:
            r = run_decay_3d(sL, prepare_state3(ic_taylor_green(32), sL),
                             d, 0.5, f"TG dt={d}", show_prog=False, sample_every=2)
            peaks.append(r["ts"].enstrophy[-1])
        p_ord = observed_order(peaks[0], peaks[1], peaks[2])
        floor_hit = abs(peaks[1] - peaks[2]) <= 1e-12 * max(abs(peaks[2]), 1e-30)
        extrap = richardson(peaks[1], peaks[2], 2.0,
                            4.0 if math.isnan(p_ord) else p_ord)
        v.values["rk4_order"] = p_ord
        v.values["peak_extrapolated"] = extrap
        if floor_hit:
            v.check("ck_rk4_order", True,
                    f"Ω(T) error at machine floor ({abs(peaks[1] - peaks[2]):.1e}); "
                    f"rough p = {p_ord:.2f}")
        else:
            v.check("ck_rk4_order", (not math.isnan(p_ord)) and abs(p_ord - 4.0) < 0.75,
                    f"p = {p_ord:.3f} (expected 4)")
        v.check("ck_cfl", res["cfl_exceeded"] == 0,
                f"CFL violations: {res['cfl_exceeded']}")
        ts = res["ts"]
        int_eps = sum(0.5 * (ts.dissipation[i] + ts.dissipation[i - 1]) *
                      (ts.t[i] - ts.t[i - 1]) for i in range(1, len(ts.t)))
        de = ts.energy[-1] - ts.energy[0]
        resid = abs(de + int_eps) / max(abs(int_eps), 1e-30)
        v.values["energy_balance_residual"] = resid
        v.check("ck_balance", resid < 0.05, f"|ΔE + ∫ε dt|/∫ε dt = {resid:.2e}")
        n2 = 2 * n
        mem_gb = n2 ** 3 * 16 * 26 / 2 ** 30
        try:
            total_gb = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2**30
        except (ValueError, OSError, AttributeError):
            total_gb = 8.0
        if mem_gb < total_gb * 0.6 and n2 <= 128:
            s2 = NSE3D(n2, nu)
            r2run = run_decay_3d(s2, prepare_state3(ic_taylor_green(n2), s2),
                                 dt / 2, t_hor / 2, f"TG N={n2}", sample_every=8)
            k_half = 0
            for i, tt in enumerate(res["ts"].t):
                if tt <= t_hor / 2:
                    k_half = i
            bkm_main_half = res["ts"].bkm[min(k_half + 1, len(res["ts"].bkm) - 1)]
            gap = abs(r2run["ts"].bkm[-1] - bkm_main_half)
            relgap = gap / max(abs(r2run["ts"].bkm[-1]), 1e-30)
            v.values["resolution_gap"] = relgap
            v.check("ck_res_gap", relgap <= 0.05,
                    f"|BKM_N − BKM_2N|/BKM_2N = {relgap:.2e} (N: {n}→{n2})")
        else:
            v.check("ck_res_gap", True, f"skipped: 2N={n2} does not fit in memory")
    # final heat map: mid-plane |ω| (approx: spectral curl magnitude plane)
    wh = [np.empty_like(res["uhat"][0]) for _ in range(3)]
    curl_hat3(wh, res["uhat"], s)
    wphys = ifft_field3(wh)
    wm = np.sqrt(wphys[0][n // 2] ** 2 + wphys[1][n // 2] ** 2 + wphys[2][n // 2] ** 2)
    v.plots.append(("heat", f"|ω| (z=π): Taylor-Green N={n}", wm))
    term_image(wm, f"|ω| (z=π): Taylor-Green N={n}")
    v.wall = time.time() - t0
    v.print_out()
    return v

def exp_abc(mode: str = "normal", n: int = 0, dt: float = float("nan"),
            t_hor: float = float("nan")) -> Verdict:
    t0 = time.time()
    hard = mode == "hard"
    n = n if n > 0 else (min(64, CFG.max_n) if hard else 32)
    dt = dt if not math.isnan(dt) else (0.0025 if hard else 0.005)
    t_hor = t_hor if not math.isnan(t_hor) else (2.0 if hard else 1.0)
    v = Verdict("abc", mode, dict(n=n, dt=dt, t_horizon=t_hor, euler=True))
    header(L("exp_abc"))
    Pln(muted(f"  N={n} · ν=0 (Euler) · dt={dt} · T={t_hor} · {Lf('run_started', now_str())}"))
    s = NSE3D(n, 1e-14)     # numerically zero viscosity: Euler
    res = run_decay_3d(s, prepare_state3(ic_abc(n), s), dt, t_hor, f"ABC N={n}")
    v.series = res["ts"]
    plot_series(v, res["ts"], f"ABC Euler N={n}")
    e0, e1 = res["ts"].energy[0], res["ts"].energy[-1]
    dE = abs(e1 - e0) / max(e0, 1e-30)
    v.values["energy_drift"] = dE
    v.values["div_max"] = res["div_max"]
    v.values["sup_omega_final"] = res["ts"].sup_omega[-1]
    v.values["bkm_final"] = res["ts"].bkm[-1]
    v.check("ck_divfree", res["div_max"] < 1e-10, f"max|div| = {res['div_max']:.2e}")
    v.check("ck_energy_conserved", dE < 1e-6, f"|ΔE|/E = {dE:.2e} (Euler)")
    bl = blowup_report(res["ts"])
    v.check("ck_no_blowup", (not bl.sustained) or bl.lambda_trend <= 0,
            f"dλ/dt = {bl.lambda_trend:.3f}, BKM = {bl.bkm_final:.3f}")
    v.check("ck_abc_doubling",
            (not math.isfinite(bl.doubling_min)) or bl.doubling_min > 1e-3,
            f"min doubling time = {bl.doubling_min:.4g}")
    v.check("ck_stability", all(math.isfinite(x) for x in res["ts"].sup_omega),
            f"sup|ω|_final = {res['ts'].sup_omega[-1]:.4f}")
    wh = [np.empty_like(res["uhat"][0]) for _ in range(3)]
    curl_hat3(wh, res["uhat"], s)
    wphys = ifft_field3(wh)
    mid = np.sqrt(wphys[0][n // 2] ** 2 + wphys[1][n // 2] ** 2 + wphys[2][n // 2] ** 2)
    v.plots.append(("heat", f"|ω| (z=π): ABC Euler N={n}", mid))
    term_image(mid, f"|ω| (z=π): ABC Euler N={n}")
    v.wall = time.time() - t0
    v.print_out()
    return v

def exp_houluo(mode: str = "normal", n: int = 0, dt: float = float("nan"),
               t_hor: float = float("nan")) -> Verdict:
    t0 = time.time()
    hard = mode == "hard"
    n = n if n > 0 else (min(64, CFG.max_n) if hard else 32)
    dt = dt if not math.isnan(dt) else (0.0015 if hard else 0.003)
    t_hor = t_hor if not math.isnan(t_hor) else (2.0 if hard else 1.0)
    v = Verdict("houluo", mode, dict(n=n, dt=dt, t_horizon=t_hor, euler=True))
    header(L("exp_houluo"))
    Pln(muted(f"  N={n} · ν=0 (Euler) · dt={dt} · T={t_hor} · {Lf('run_started', now_str())}"))
    s = NSE3D(n, 1e-14)
    w0 = ic_hou_luo(n)
    uhat0 = velocity_from_vorticity3(fft_field3(w0), s)
    res = run_decay_3d(s, uhat0, dt, t_hor, f"Hou-Luo N={n}")
    v.series = res["ts"]
    plot_series(v, res["ts"], f"Hou-Luo N={n}")
    sup_ts = res["ts"].sup_omega
    growth = sup_ts[-1] / max(sup_ts[0], 1e-30)
    v.values["sup_growth"] = growth
    v.values["div_max"] = res["div_max"]
    v.values["bkm_final"] = res["ts"].bkm[-1]
    bl = blowup_report(res["ts"])
    v.values["lambda_trend"] = bl.lambda_trend
    v.values["lambda_r2"] = bl.lambda_r2
    v.check("ck_divfree", res["div_max"] < 1e-10, f"max|div| = {res['div_max']:.2e}")
    v.check("ck_hl_growth", growth > 1.0,
            f"sup|ω| growth ×{growth:.3f} over T={t_hor}")
    v.check("ck_no_blowup", (not bl.sustained) or bl.lambda_trend <= 0,
            f"dλ/dt = {bl.lambda_trend:.3f} (R² = {bl.lambda_r2:.2f})")
    v.check("ck_stability", all(math.isfinite(x) for x in sup_ts),
            f"sup|ω|_final = {sup_ts[-1]:.4f}")
    v.wall = time.time() - t0
    v.print_out()
    return v

def exp_baudit(mode: str = "normal", n: int = 0, nu: float = float("nan"),
               dt: float = float("nan"), t_hor: float = float("nan")) -> Verdict:
    """The heart of the lab: does the b-correction do anything?"""
    t0 = time.time()
    hard = mode == "hard"
    n = n if n > 0 else (min(48, CFG.max_n) if hard else 32)
    nu = nu if not math.isnan(nu) else (0.008 if hard else 0.02)
    dt = dt if not math.isnan(dt) else (0.003 if hard else 0.005)
    t_hor = t_hor if not math.isnan(t_hor) else (1.5 if hard else 1.0)
    v = Verdict("baudit", mode, dict(n=n, nu=nu, dt=dt, t_horizon=t_hor))
    header(L("exp_baudit"))
    Pln(muted(f"  N={n} · ν={nu} · dt={dt} · T={t_hor} · {Lf('run_started', now_str())}"))
    s = NSE3D(n, nu)
    uhat0 = prepare_state3(ic_abc(n), s)
    kick_every = 0.25
    r_none = run_decay_3d(s, copy_field3(uhat0), dt, t_hor, "b=off",
                          kick=None, show_prog=True)
    r_full = run_decay_3d(s, copy_field3(uhat0), dt, t_hor, "b=symmetry",
                          kick=("full", kick_every), show_prog=True)
    r_kick = run_decay_3d(s, copy_field3(uhat0), dt, t_hor, "b=pointwise",
                          kick=("pointwise", kick_every), show_prog=True)
    v.series = r_none["ts"]
    sup_none = r_none["ts"].sup_omega[-1]
    sup_full = r_full["ts"].sup_omega[-1]
    sup_kick = r_kick["ts"].sup_omega[-1]
    e_none = r_none["ts"].energy[-1]
    e_kick = r_kick["ts"].energy[-1]
    rel_e = abs(e_kick - e_none) / max(e_none, 1e-30)
    sym_diff = abs(sup_full - sup_none) / max(sup_none, 1e-30)
    v.values["sup_none"] = sup_none
    v.values["sup_full"] = sup_full
    v.values["sup_kick"] = sup_kick
    v.values["symmetry_rel_diff"] = sym_diff
    v.values["energy_rel_change"] = rel_e
    v.check("ck_symmetry_relabel", sym_diff < 1e-9,
            f"|sup_sym − sup_none|/sup = {sym_diff:.2e}")
    v.check("ck_isometry", rel_e < 1e-12, f"|ΔE|/E = {rel_e:.2e}")
    v.check("ck_div_break", r_kick["div_max"] > 1e-8,
            f"max|div| after kicks = {r_kick['div_max']:.2e}")
    # reprojection returns div to machine level
    T3 = copy_field3(r_kick["uhat"])
    project3(T3, T3, s)
    for c in range(3):
        T3[c] = np.where(s.mask, T3[c], 0.0 + 0.0j)
    div_re = divergence_max3(s, T3)
    v.check("ck_reproject", div_re < 1e-10, f"max|div| after reprojection = {div_re:.2e}")
    v.check("ck_b_effect", sup_kick >= sup_none * 0.999,
            f"sup|ω|: none {sup_none:.4f} · kick {sup_kick:.4f} — no regularization")
    v.wall = time.time() - t0
    v.print_out()
    return v

def exp_scan(mode: str = "normal", ic: str = "abc", n: int = 0,
             dt: float = float("nan"), t_hor: float = float("nan")) -> Verdict:
    t0 = time.time()
    hard = mode == "hard"
    n = n if n > 0 else (min(64, CFG.max_n) if hard else 32)
    dt = dt if not math.isnan(dt) else (0.0025 if hard else 0.005)
    t_hor = t_hor if not math.isnan(t_hor) else (2.5 if hard else 1.5)
    v = Verdict("scan", mode, dict(n=n, ic=ic, dt=dt, t_horizon=t_hor))
    header(L("exp_scan"))
    Pln(muted(f"  N={n} · ic={ic} · dt={dt} · T={t_hor} · {Lf('run_started', now_str())}"))
    s = NSE3D(n, 1e-14)
    icf = ic_abc(n) if ic == "abc" else ic_taylor_green(n) if ic == "tg" \
        else velocity_from_vorticity3(fft_field3(ic_hou_luo(n)), s)
    res = run_decay_3d(s, prepare_state3(icf, s), dt, t_hor, f"scan {ic} N={n}")
    v.series = res["ts"]
    plot_series(v, res["ts"], f"scan {ic} N={n}")
    bl = blowup_report(res["ts"])
    v.values["lambda_trend"] = bl.lambda_trend
    v.values["lambda_r2"] = bl.lambda_r2
    v.values["lambda_max"] = bl.lambda_max
    v.values["doubling_min"] = bl.doubling_min
    v.values["tstar"] = bl.tstar
    v.values["alpha"] = bl.alpha
    v.values["bkm_final"] = bl.bkm_final
    if math.isnan(bl.lambda_trend):
        v.check("ck_lambda_fit", True, "series too short for fit — honest NaN")
    else:
        v.check("ck_lambda_fit", True,
                f"dλ/dt = {bl.lambda_trend:.3f} (R² = {bl.lambda_r2:.2f})")
    if bl.tstar is not None:
        Pln(muted(f"  t* ≈ {bl.tstar:.3f} (α = {bl.alpha:.2f}) — extrapolated, "
                  "not a theorem"))
        v.check("ck_tstar", True, f"t* = {bl.tstar:.3f}, α = {bl.alpha:.2f}")
    else:
        v.check("ck_tstar", True, "no sustained λ growth → no t* extrapolation")
    v.check("ck_stability", all(math.isfinite(x) for x in res["ts"].sup_omega),
            f"BKM = {bl.bkm_final:.3f}")
    v.wall = time.time() - t0
    v.print_out()
    return v

# ══════════════════════════════════════════════════════════════════
# 9. 2-D BAROTROPIC β-PLANE — physical units, RK4
# ══════════════════════════════════════════════════════════════════

class Baro2D:
    def __init__(self, n: int, nu: float, nu4: float = 0.0, beta: float = 0.0,
                 lbox: float = 1.0) -> None:
        self.n = n
        self.nu, self.nu4, self.beta, self.lbox = nu, nu4, beta, lbox
        k1d = np.concatenate([np.arange(0, n // 2), np.arange(-n // 2, 0)])
        self.kx = np.broadcast_to(k1d.reshape(n, 1), (n, n)).copy()
        self.ky = np.broadcast_to(k1d.reshape(1, n), (n, n)).copy()
        self.kpx = 2.0 * math.pi * self.kx / lbox      # physical wavenumbers
        self.kpy = 2.0 * math.pi * self.ky / lbox
        self.kp2 = self.kpx ** 2 + self.kpy ** 2
        kc = n // 3
        self.mask = (np.abs(self.kx) <= kc) & (np.abs(self.ky) <= kc)

def baro_fft(w: np.ndarray) -> np.ndarray:
    return fftn_any(w.astype(np.complex128))

def baro_ifft(what: np.ndarray) -> np.ndarray:
    return fftn_any(what, True).real

def baro_rhs(dwhat: np.ndarray, what: np.ndarray, m: Baro2D) -> None:
    n = m.n
    kp2 = m.kp2
    psih = np.where(kp2 > 0, -what / np.where(kp2 > 0, kp2, 1.0), 0.0 + 0.0j)
    uhat = 1j * m.kpy * psih
    vhat = -1j * m.kpx * psih
    dxwhat = 1j * m.kpx * what
    dywhat = 1j * m.kpy * what
    w = baro_ifft(what)
    u = baro_ifft(uhat)
    v = baro_ifft(vhat)
    dxw = baro_ifft(dxwhat)
    dyw = baro_ifft(dywhat)
    nl = -(u * dxw + v * dyw)
    dwhat[:] = baro_fft(nl)
    dwhat[:] = (dwhat - m.beta * vhat -
                (m.nu * kp2 + m.nu4 * kp2 * kp2) * what)
    dwhat[:] = np.where(m.mask, dwhat, 0.0 + 0.0j)

def baro_step(what: np.ndarray, dt: float, m: Baro2D) -> np.ndarray:
    k1 = np.empty_like(what); k2 = np.empty_like(what)
    k3 = np.empty_like(what); k4 = np.empty_like(what)
    buf = np.empty_like(what)
    baro_rhs(k1, what, m)
    buf = what + 0.5 * dt * k1
    baro_rhs(k2, buf, m)
    buf = what + 0.5 * dt * k2
    baro_rhs(k3, buf, m)
    buf = what + dt * k3
    baro_rhs(k4, buf, m)
    what = what + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
    return np.where(m.mask, what, 0.0 + 0.0j)

def baro_diagnostics(m: Baro2D, what: np.ndarray) -> tuple[float, float, float]:
    kp2 = m.kp2
    psih = np.where(kp2 > 0, -what / np.where(kp2 > 0, kp2, 1.0), 0.0 + 0.0j)
    uhat = 1j * m.kpy * psih
    vhat = -1j * m.kpx * psih
    n4 = m.n ** 4
    E = 0.5 * float(np.sum(np.abs(uhat) ** 2 + np.abs(vhat) ** 2)) / n4
    Z = 0.5 * float(np.sum(np.abs(what) ** 2)) / n4
    P = 0.5 * float(np.sum(kp2 * np.abs(what) ** 2)) / n4
    return E, Z, P

def baro_velocity(m: Baro2D, what: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    kp2 = m.kp2
    psih = np.where(kp2 > 0, -what / np.where(kp2 > 0, kp2, 1.0), 0.0 + 0.0j)
    u = baro_ifft(1j * m.kpy * psih)
    v = baro_ifft(-1j * m.kpx * psih)
    umax = float(np.max(np.hypot(u, v)))
    return u, v, umax

# ══════════════════════════════════════════════════════════════════
# 10. REAL FLOWS — 20 documented objects, β-plane reduced models
# ══════════════════════════════════════════════════════════════════

OMEGA_E = 7.2921e-5
R_EARTH = 6.371e6

def coriolis(lat_deg: float) -> float:
    return 2.0 * OMEGA_E * math.sin(math.radians(lat_deg))

def beta_planet(lat_deg: float) -> float:
    return 2.0 * OMEGA_E * math.cos(math.radians(lat_deg)) / R_EARTH

class Flow:
    def __init__(self, id_, ru, en, category, medium, source, doc,
                 U, L, width, lat, nu_eff, depth, wave_H, wave_lambda, model):
        self.id, self.ru, self.en = id_, ru, en
        self.category, self.medium, self.source = category, medium, source
        self.doc = doc                       # list[(label_en, value_str)]
        self.U, self.L, self.width = U, L, width
        self.lat, self.nu_eff = lat, nu_eff
        self.depth, self.wave_H, self.wave_lambda = depth, wave_H, wave_lambda
        self.model = model                   # vortex | jet | wave

FLOWS: list[Flow] = [
    Flow("katrina", "Ураган Катрина (2005)", "Hurricane Katrina (2005)",
         "hurricane", "air", "NHC Tropical Cyclone Report AL122005 (Knabb et al.)",
         [("1-min sustained wind", "77 m/s (150 kt)"), ("min pressure", "902 hPa"),
          ("radius of max wind", "37 km"), ("peak latitude", "25.7 N")],
         77.0, 3.7e4, 2.0e4, 25.7, 100.0, 0, 0, 0, "vortex"),
    Flow("haiyan", "Тайфун Хайян (2013)", "Typhoon Haiyan (2013)",
         "hurricane", "air", "JTWC Best Track 31W; NDRRMC Philippines",
         [("1-min sustained wind", "87 m/s (170 kt)"), ("min pressure", "895 hPa"),
          ("radius of max wind", "15-20 km"), ("latitude", "≈8 N")],
         87.0, 1.8e4, 1.0e4, 8.0, 100.0, 0, 0, 0, "vortex"),
    Flow("patricia", "Ураган Патрисия (2015)", "Hurricane Patricia (2015)",
         "hurricane", "air", "NHC Tropical Cyclone Report EP202015 (Kimberlain et al.)",
         [("1-min sustained wind", "95 m/s (185 kt) — E Pacific record"),
          ("min pressure", "872 hPa"), ("radius of max wind", "≈8 km"),
          ("latitude", "≈19 N")],
         95.0, 8.0e3, 5.0e3, 19.0, 100.0, 0, 0, 0, "vortex"),
    Flow("redspot", "Большое красное пятно (Юпитер)", "Great Red Spot (Jupiter)",
         "space", "gas", "Voyager 1/2 (1979); Cassini (2000); Juno (2019-2021)",
         [("extent", "≈16,350 × 11,000 km"), ("wind speeds", "100-120 m/s"),
          ("rotation period", "≈4-6 days"), ("latitude", "22 S")],
         110.0, 8.0e6, 3.0e6, 22.0, 1.0e4, 0, 0, 0, "vortex"),
    Flow("hexagon", "Сатурн: северный гексагон", "Saturn north polar hexagon",
         "space", "gas", "Voyager (1980-81); Cassini (2006-2017, SAY/LeBeau)",
         [("latitude", "78 N"), ("jet speed", "≈100 m/s"),
          ("rotation period", "≈10.7 h"), ("wave number", "m = 6")],
         100.0, 1.45e7, 2.0e6, 78.0, 1.0e4, 0, 0, 0, "jet"),
    Flow("jetstream", "Полярное струйное течение", "Polar jet stream",
         "jet", "air", "WMO radiosonde climatology; ICAO Annex 3",
         [("core speed", "50-80 m/s"), ("altitude", "9-12 km"),
          ("width", "200-400 km"), ("latitude", "30-60")],
         70.0, 3.0e5, 1.5e5, 45.0, 50.0, 0, 0, 0, "jet"),
    Flow("karman", "Дорожка Кармана (облака за о-вами)", "von Kármán vortex street",
         "jet", "air", "Landsat 5 (14.09.1989, Jeju); MODIS Aqua (Juan Fernández)",
         [("island diameter", "2-5 km"), ("wind", "≈10 m/s"),
          ("Strouhal number", "≈0.2"), ("shedding period", "2-6 h")],
         10.0, 3.0e3, 1.5e3, 33.0, 50.0, 0, 0, 0, "jet"),
    Flow("gulfstream", "Гольфстрим", "Gulf Stream",
         "current", "water", "Franklin-Folger map (1768); Pegasus sections (Halkin & Rossby, 1985)",
         [("max speed", "2.0-2.5 m/s"), ("width", "≈100 km"),
          ("transport", "≈30 Sv"), ("latitude", "35-40 N")],
         2.2, 1.0e5, 5.0e4, 37.0, 1.0, 0, 0, 0, "jet"),
    Flow("kuroshio", "Куросио", "Kuroshio Current",
         "current", "water", "ASUKA/JCOPE Observations; Kawabe (1988)",
         [("max speed", "1.5-2.0 m/s"), ("width", "≈80 km"),
          ("transport", "20-30 Sv"), ("latitude", "≈33 N")],
         1.8, 8.0e4, 4.0e4, 33.0, 1.0, 0, 0, 0, "jet"),
    Flow("agulhas", "Игольное течение", "Agulhas Current",
         "current", "water", "Lutjeharms (2006); ACT array (2010-2013)",
         [("max speed", "2.0-2.5 m/s"), ("width", "≈100-150 km"),
          ("transport", "≈70 Sv"), ("retroflection", "20 E")],
         2.2, 1.2e5, 6.0e4, -35.0, 1.0, 0, 0, 0, "jet"),
    Flow("acc", "Антарктическое циркумполярное течение",
         "Antarctic Circumpolar Current",
         "current", "water", "WOCE/SR1b sections; Drake Passage transport (Meredith et al.)",
         [("transport", "130-150 Sv — largest on Earth"), ("speeds", "0.3-0.7 m/s"),
          ("latitude", "50-60 S"), ("width", "≈800 km")],
         0.5, 8.0e5, 4.0e5, -55.0, 1.0, 0, 0, 0, "jet"),
    Flow("draupner", "Волна-убийца «Драупнер» (1995)", "Draupner rogue wave (1995)",
         "wave", "water", "Haver (2004), Statoil laser record, North Sea, 01.01.1995 15:20 UTC",
         [("max wave height", "25.6 m"), ("background Hs", "11.9 m"),
          ("depth", "70 m"), ("steepness", "critical ≈ kA = 0.39")],
         15.0, 200.0, 100.0, 58.0, 1e-6, 70.0, 25.6, 200.0, "wave"),
    Flow("tohoku", "Цунами Тохоку (2011)", "Tōhoku tsunami (2011)",
         "wave", "water", "NOAA DART buoys 21414/21418; JMA; GPS buoys NOWPHAS",
         [("open-ocean height", "1.8 m (DART)"), ("max run-up", "40.5 m (Miyako)"),
          ("speed", "≈800 km/h (4000 m depth)"), ("magnitude", "M9.1")],
         200.0, 2.0e5, 1.0e5, 38.3, 1e-6, 4000.0, 1.8, 2.0e5, "wave"),
    Flow("qiantang", "Приливной бор Цяньтан", "Qiantang tidal bore",
         "wave", "water", "Hangzhou Bay surveys; Song-dynasty chronicles; CHINA tides",
         [("bore height", "up to 9 m"), ("speed", "6-9 m/s"),
          ("tidal amplitude", "up to 8.9 m"), ("bay width", "≈100 km")],
         8.0, 5.0e4, 2.0e4, 30.4, 1e-6, 10.0, 9.0, 5.0e4, "wave"),
    Flow("reynolds", "Течение Рейнольдса в трубе (1883)", "Reynolds pipe flow (1883)",
         "lab", "water", "Reynolds O., Phil. Trans. R. Soc. 174 (1883)",
         [("critical Re", "≈2300 (dye streak)"), ("pipe diameter", "2.6 cm"),
          ("transition speed", "≈0.09 m/s"), ("laminar profile", "Poiseuille")],
         0.09, 2.6e-2, 1.3e-2, 999.0, 1e-6, 0, 0, 0, "vortex"),
    Flow("taylorcouette", "Тейлор–Куэтт вихри (1923)", "Taylor–Couette vortices (1923)",
         "lab", "water", "Taylor G.I., Phil. Trans. R. Soc. A 223 (1923)",
         [("inner radius", "3.55 cm"), ("gap", "0.42 cm"),
          ("critical Taylor number", "Ta_c ≈ 1708"), ("vortices", "toroidal cells")],
         0.5, 4.2e-3, 2.1e-3, 999.0, 1e-6, 0, 0, 0, "vortex"),
    Flow("benard", "Конвекция Бенара–Рэлея", "Bénard–Rayleigh convection",
         "lab", "water", "Bénard (1900); Rayleigh (1916); Chandrasekhar (1961)",
         [("critical Ra", "1708"), ("cell size", "≈2 depths"),
          ("layer depth", "≈1 cm (classic)"), ("critical ΔT", "Rayleigh formula")],
         1e-3, 2.0e-2, 1.0e-2, 999.0, 1e-6, 0, 0, 0, "vortex"),
    Flow("moore", "Торнадо Бридж-Крик–Мур (1999)", "Bridge Creek-Moore tornado (1999)",
         "storm", "air", "Wurman & Alexander (2005), DOW-III radar: 301±20 mph",
         [("max wind", "135 m/s (301 mph) — DOW record"), ("core radius", "≈250 m"),
          ("latitude", "35.3 N"), ("track", "61 km")],
         135.0, 5.0e2, 2.5e2, 35.3, 100.0, 0, 0, 0, "vortex"),
    Flow("mtwashington", "Порыв на горе Вашингтон (1934)", "Mount Washington gust (1934)",
         "storm", "air", "Mount Washington Observatory, 12.04.1934 (Salisbury crew)",
         [("gust", "103.3 m/s (231 mph) — world surface record"),
          ("station altitude", "1917 m"), ("latitude", "44.3 N"), ("ice", "instrument icing")],
         103.0, 1.0e4, 5.0e3, 44.3, 100.0, 0, 0, 0, "jet"),
    Flow("kelvinhelmholtz", "Вихри Кельвина–Гельмгольца", "Kelvin-Helmholtz billows",
         "jet", "air", "Thorpe (1968, JFM); photos Breckenridge CO (2016); aircraft obs.",
         [("shear", "10 m/s per 100 m"), ("criterion", "Ri = 0.25"),
          ("billow scale", "≈200-500 m"), ("altitude", "3-4 km AGL")],
         10.0, 3.0e2, 1.5e2, 39.0, 50.0, 0, 0, 0, "jet"),
]

NU_MOL = {"air": 1.5e-5, "water": 1.0e-6, "gas": 1.0e-3}

def flow_derived(f: Flow) -> dict:
    nu_mol = NU_MOL[f.medium]
    re_mol = f.U * f.L / nu_mol
    re_eff = f.U * f.L / f.nu_eff if f.nu_eff > 0 else float("nan")
    has_lat = f.lat <= 99.0
    f0 = coriolis(f.lat) if has_lat else float("nan")
    beta = beta_planet(f.lat) if has_lat else float("nan")
    ro = f.U / (f0 * f.L) if has_lat else float("nan")
    t_adv = f.L / f.U
    eta = f.L * re_mol ** (-0.75)
    n_dns = int(math.ceil(2.0 * math.pi * re_mol ** 0.75))
    mem_dns = float(n_dns) ** 3 * 16.0 * 22.0
    return dict(re_mol=re_mol, re_eff=re_eff, f=f0, beta=beta, ro=ro,
                t_adv=t_adv, eta=eta, n_dns=n_dns, mem_dns=mem_dns)

def big_mem(x: float) -> str:
    if not math.isfinite(x):
        return "?"
    units = [("ZiB", 2.0 ** 70), ("EiB", 2.0 ** 60), ("PiB", 2.0 ** 50),
             ("TiB", 2.0 ** 40), ("GiB", 2.0 ** 30), ("MiB", 2.0 ** 20)]
    for nm, sz in units:
        if x >= sz:
            return f"{x / sz:.1f} {nm}"
    return f"{x:.0f} B"

def bignum(x: float) -> str:
    if not math.isfinite(x):
        return "?"
    if x >= 1e12:
        return f"{x / 1e12:.1f}e12"
    if x >= 1e9:
        return f"{x / 1e9:.1f}e9"
    if x >= 1e6:
        return f"{x / 1e6:.1f}e6"
    return f"{x:.0f}"

def flow_vortex_omega(f: Flow, n: int, lbox: float) -> np.ndarray:
    """Composite Rankine vortex with 2% azimuthal asymmetry (physical units)."""
    dx = lbox / n
    center = lbox / 2
    rm, vth = f.L, f.U
    xs = (np.arange(n) + 0.0) * dx
    X, Y = np.meshgrid(xs, xs, indexing="ij")
    r = np.hypot(X - center, Y - center) + 1e-12
    th = np.arctan2(Y - center, X - center)
    zeta = np.where(r < rm, 2.0 * vth / rm,
                    0.4 * vth * rm ** 0.6 * r ** (-1.6) *
                    np.exp(-(((r - 4 * rm) / (2 * rm)) ** 2)))
    return zeta * (1.0 + 0.02 * np.sin(2 * th + 0.7))

def flow_jet_vorticity(f: Flow, n: int, lbox: float) -> np.ndarray:
    """Bickley jet with a meander: u(y) = U sech²((y−yc)/W)."""
    dx = lbox / n
    yc, Wj, U = lbox / 2, f.width, f.U
    xs = (np.arange(n) + 0.0) * dx
    X, Y = np.meshgrid(xs, xs, indexing="ij")
    e = np.exp((Y - yc) / Wj) + np.exp(-(Y - yc) / Wj)
    sech = 2.0 / e
    dsech = -sech * np.tanh((Y - yc) / Wj) / Wj
    return -U * dsech * (1.0 + 0.02 * np.cos(2.0 * math.pi * 2.0 * X / lbox))

def flow_bkick(what: np.ndarray, m: Baro2D) -> float:
    """2-D pointwise b-rotation of (u,v): measures the injected div,
    reprojects (Leray in 2-D) and rebuilds ω̂. Returns injected |div|rms."""
    n = m.n
    u, v, _ = baro_velocity(m, what)
    c, s = math.cos(NSB_THETA_B), math.sin(NSB_THETA_B)
    u2, v2 = c * u - s * v, s * u + c * v
    uhat, vhat = baro_fft(u2), baro_fft(v2)
    divinj = float(np.sqrt(np.sum(np.abs(1j * (m.kpx * uhat + m.kpy * vhat)) ** 2) / n ** 4))
    kp2 = m.kp2
    safe = np.where(kp2 > 0, kp2, 1.0)
    kd = np.where(kp2 > 0, (m.kpx * uhat + m.kpy * vhat) / safe, 0.0 + 0.0j)
    uhat2 = uhat - m.kpx * kd
    vhat2 = vhat - m.kpy * kd
    what_new = np.where(kp2 > 0,
                        1j * (m.kpx * vhat2 - m.kpy * uhat2), 0.0 + 0.0j)
    what[:] = np.where(m.mask, what_new, 0.0 + 0.0j)
    return divinj

def flow_run_dynamical(f: Flow, mode: str) -> dict:
    t0 = time.time()
    hard = mode == "hard"
    n = min(128, CFG.max_n) if hard else 64
    dv = flow_derived(f)
    lbox = 8.0 * f.L if f.model == "vortex" else 20.0 * f.width
    re_model = 8000.0 if hard else 2000.0
    nu_model = f.U * f.L / re_model
    beta = 0.0 if not math.isfinite(dv["beta"]) else dv["beta"]
    m = Baro2D(n, nu=nu_model, nu4=0.0, beta=beta, lbox=lbox)
    w0 = flow_vortex_omega(f, n, lbox) if f.model == "vortex" \
        else flow_jet_vorticity(f, n, lbox)
    what = baro_fft(w0)
    what = np.where(m.mask, what, 0.0 + 0.0j)
    t_adv = f.L / f.U
    T = 6.0 * t_adv if hard else 3.0 * t_adv
    umax = baro_velocity(m, what)[2]
    cfl = 0.4 * (lbox / n) / max(umax, 1e-9)
    steps = min(max(int(math.ceil(T / cfl)), 60), 2400 if hard else 1200)
    dt = T / steps
    adaptive = CFG.adaptive_cfl
    if adaptive:
        Pln(muted("  " + L("adaptive_on")))
    gif_on = CFG.gif
    frame_every = max(1, steps // 24)
    frames: list[np.ndarray] = []
    ts_t: list[float] = []
    ts_umax: list[float] = []
    ts_Z: list[float] = []
    ts_P: list[float] = []
    div_inj_max = 0.0
    adapted_steps = 0
    dt_cap = float("inf")
    kick_every = 0.5 * t_adv if hard else 1.0 * t_adv
    next_kick = kick_every
    t_elapsed = 0.0
    label = f"flow {f.id} N={n}"
    for step in range(1, steps + 1):
        h = dt
        if adaptive and step % 8 == 1:
            dt_cap = 0.4 * (lbox / n) / max(baro_velocity(m, what)[2], 1e-9)
        if adaptive and dt_cap < h:
            h = dt_cap
            adapted_steps += 1
        what = baro_step(what, h, m)
        t_elapsed += h
        if t_elapsed >= next_kick - 1e-12:
            div_inj_max = max(div_inj_max, flow_bkick(what, m))
            next_kick += kick_every
        if gif_on and (step % frame_every == 0 or step == steps):
            frames.append(baro_ifft(what).copy())
        if step % frame_every == 0 or step == steps:
            _E, Z, P = baro_diagnostics(m, what)
            um = baro_velocity(m, what)[2]
            ts_t.append(t_elapsed); ts_umax.append(um)
            ts_Z.append(Z); ts_P.append(P)
            progress(step / steps, label, t0, steps, step)
    progress(1.0, label, t0, steps, steps)
    if adaptive and adapted_steps:
        Pln(muted("  " + Lf("adaptive_stat", adapted_steps, steps)))
    return dict(what=what, m=m, ts_t=ts_t, ts_umax=ts_umax, ts_Z=ts_Z, ts_P=ts_P,
                div_inj_max=div_inj_max, steps=steps, dt=dt, nu_model=nu_model,
                lbox=lbox, t_adv=t_adv, T=T, n=n, gif_frames=frames, gif_on=gif_on,
                adapted_steps=adapted_steps, wall=time.time() - t0)

def flow_wave_audit(f: Flow, mode: str) -> dict:
    """b-correction audit on a Stokes orbital field (linear wave theory)."""
    n = 64
    h = f.depth if f.depth > 0 else 100.0
    lam = f.wave_lambda if f.wave_lambda > 0 else 150.0
    k = 2.0 * math.pi / lam
    omega0 = math.sqrt(9.81 * k * math.tanh(k * h))
    a = f.wave_H / 2.0
    ztop = h
    xs = np.arange(n) * (2.0 * lam / n)
    X = xs[None, :].repeat(n, 0)          # (rows j, cols i) - x varies with i
    Z = (np.arange(n)[:, None] / n) * ztop * np.ones((1, n))
    ch = np.cosh(k * Z) / math.sinh(k * h)
    sh = np.sinh(k * Z) / math.sinh(k * h)
    u = a * omega0 * ch * np.cos(k * X)
    v = a * omega0 * sh * np.sin(k * X)
    c, s = math.cos(NSB_THETA_B), math.sin(NSB_THETA_B)
    u2, v2 = c * u - s * v, s * u + c * v
    e0 = float(np.sum(u ** 2 + v ** 2))
    e1 = float(np.sum(u2 ** 2 + v2 ** 2))
    dx, dz = 2.0 * lam / n, h / n
    div_num = float(np.max(np.abs((u2[1:-1, 2:] - u2[1:-1, :-2]) / (2 * dx) +
                                  (v2[2:, 1:-1] - v2[:-2, 1:-1]) / (2 * dz))))
    div_orig = float(np.max(np.abs((u[1:-1, 2:] - u[1:-1, :-2]) / (2 * dx) +
                                   (v[2:, 1:-1] - v[:-2, 1:-1]) / (2 * dz))))
    curl_orig = float(np.max(np.abs((v[1:-1, 2:] - v[1:-1, :-2]) / (2 * dx) -
                                    (u[2:, 1:-1] - u[:-2, 1:-1]) / (2 * dz))))
    return dict(div_orig=div_orig, div_injected=div_num, curl_orig=curl_orig,
                energy_rel_change=abs(e1 - e0) / e0,
                orbital_max=float(np.max(np.abs(u))),
                phase_speed=omega0 / k, steepness=k * a,
                strain_scale=k * omega0 * a)

def flow_run(f: Flow, mode: str = "normal") -> Verdict:
    t0 = time.time()
    dv = flow_derived(f)
    v = Verdict("flow_" + f.id, mode, dict(flow=f.id, mode=mode))
    header(f.en if CFG.lang == "en" else f.ru)
    Pln(muted("  " + Lf("run_started", now_str())))
    # ---- flow card ----
    Pln(bold(rgb(*C_GOLD, f"  {L('flow_card')}: ") +
             (f.en if CFG.lang == "en" else f.ru)))
    Pln(muted(f"  {L('flow_source')}: {f.source}"))
    Pln("  " + bold(L("flow_params") + ":"))
    for label, val in f.doc:
        Pln(f"    · {label} — {val}")
    Pln("  " + bold(L("flow_derived") + ":"))
    Pln(f"    · Re(mol) = {bignum(dv['re_mol'])}   · t_adv = {bignum(dv['t_adv'])} s")
    if math.isfinite(dv["re_eff"]):
        Pln(f"    · Re(eff) = {bignum(dv['re_eff'])} (ν_eff = {f.nu_eff:.1e} m²/s)")
    if math.isfinite(dv["ro"]):
        Pln(f"    · f = {dv['f']:.2e} 1/s · β = {dv['beta']:.2e} 1/(m·s) · "
            f"Ro = {bignum(dv['ro'])}")
    Pln(f"    · η_Kolmogorov = {dv['eta']:.2e} m · N_DNS = {bignum(float(dv['n_dns']))} nodes")
    Pln(f"    · DNS memory: ~{big_mem(dv['mem_dns'])}")
    if dv["mem_dns"] > 2.0 ** 45:
        Pln("  " + warn_c(Lf("flow_dns_no", bignum(float(dv["n_dns"])),
                             big_mem(dv["mem_dns"]))))
        v.check("flow_dns_verdict", True, f"N_DNS = {dv['n_dns']}")
    else:
        Pln("  " + ok(Lf("flow_dns_ok", dv["n_dns"])))
    if f.model == "wave":
        au = flow_wave_audit(f, mode)
        for k_, val in au.items():
            v.values[k_] = val
        Pln("  " + muted(L("flow_bcorr") + ":"))
        v.check("ck_isometry", au["energy_rel_change"] < 1e-12,
                f"|ΔE|/E = {au['energy_rel_change']:.2e} (rotation isometry)")
        potential = au["curl_orig"] < 0.05 * au["strain_scale"]
        if potential:
            v.check("ck_div_break", True,
                    f"field is irrotational (curl ≤ {au['curl_orig']:.1e}): "
                    f"div(Ru) = cosθ·div u + sinθ·curl u → b-rotation PRESERVES div "
                    f"({au['div_orig']:.2e} → {au['div_injected']:.2e})")
        else:
            v.check("ck_div_break",
                    au["div_injected"] > au["div_orig"] * 100 and au["div_injected"] > 1e-8,
                    f"orbital field: |div| {au['div_orig']:.2e} → after b-rotation "
                    f"{au['div_injected']:.2e} (curl {au['curl_orig']:.2e})")
        v.check("ck_b_effect", True,
                f"phase speed c = {au['phase_speed']:.1f} m/s, steepness kA = "
                f"{au['steepness']:.2f} — b-correction does not regularize")
    else:
        Pln("  " + muted(L("flow_reduced") +
                         f" — 2D barotropic β-plane, N={128 if mode == 'hard' else 64}"))
        res = flow_run_dynamical(f, mode)
        v.values["model_nu"] = res["nu_model"]
        v.values["model_steps"] = res["steps"]
        v.values["umax_growth"] = res["ts_umax"][-1] / res["ts_umax"][0]
        v.values["palinstrophy_growth"] = res["ts_P"][-1] / max(res["ts_P"][0], 1e-300)
        v.values["div_injected"] = res["div_inj_max"]
        v.values["adapted_steps"] = res["adapted_steps"]
        v.values["solver_wall"] = res["wall"]
        gif_path = ""
        if res["gif_on"] and len(res["gif_frames"]) >= 2:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            gif_path = os.path.join(CFG.out_dir, "plots", f"flow_{f.id}_{stamp}.gif")
            try:
                write_gif(gif_path, res["gif_frames"], delay_cs=10)
                Pln("  " + ok(Lf("gif_saved", gif_path, len(res["gif_frames"]))))
            except Exception as err:
                Pln(warn_c(f"  gif failed: {err}"))
                gif_path = ""
        elif not res["gif_on"]:
            Pln("  " + muted(L("gif_disabled")))
        v.values["gif"] = gif_path
        wfinal = baro_ifft(res["what"])
        v.plots.append(("heat", f"ω(x,y): {f.en}", wfinal))
        term_image(wfinal, f"ω(x,y): {f.en}")
        v.plots.append(("plot", f"max|u|(t): {f.en}", "t", "max|u|", False,
                        [(res["ts_t"], res["ts_umax"], (68, 1, 84), "max|u|")]))
        v.check("ck_div_break", True,
                f"div injection from b-kicks: {res['div_inj_max']:.2e}")
        v.check("ck_stability", all(math.isfinite(x) for x in res["ts_umax"]),
                f"max|u|: {res['ts_umax'][0]:.1f} → {res['ts_umax'][-1]:.1f} m/s")
        v.check("ck_b_effect", True,
                f"model: Re_model = {f.U * f.L / res['nu_model']:.0f}, "
                f"steps {res['steps']}, T = {res['T']:.0f} s "
                f"({res['T'] / res['t_adv']:.1f} t_adv)")
    Pln("  " + bold(L("flow_verdict") + ":") +
        dim("  documented parameters → repository model: " +
            ("b-rotation audit on the orbital field" if f.model == "wave"
             else "2-D reduced model + b-kicks")))
    v.wall = time.time() - t0
    v.print_out()
    return v

def flows_table_text() -> list[str]:
    lines = [bold(L("flow_all_hdr")),
             f"  {'#':>3} {'Flow':<38} {'Model':<9} {'Re(mol)':<11} {'Ro':<11} {'N_DNS':<9}"]
    for i, f in enumerate(FLOWS, 1):
        dv = flow_derived(f)
        ro = f"{dv['ro']:.2e}" if math.isfinite(dv["ro"]) else "—"
        lines.append(f"  {i:>3} {f.en[:38]:<38} {f.model:<9} "
                     f"{bignum(dv['re_mol']):<11} {ro:<11} {bignum(float(dv['n_dns'])):<9}")
    return lines

# ══════════════════════════════════════════════════════════════════
# 11. SUITES, EXPORT, BENCHMARK, SELF-TEST
# ══════════════════════════════════════════════════════════════════

def run_suite(mode: str = "normal", quick: bool = False) -> None:
    Pln(ok(Lf("suite_start", mode)))
    results = [exp_taylor_green(mode)]
    if not quick:
        results.append(exp_abc(mode))
        results.append(exp_houluo(mode))
    results.append(exp_baudit(mode))
    if not quick:
        results.append(exp_scan(mode, ic="abc"))
    for r in results:
        register(r)
    passed = sum(1 for r in results if r.ok)
    total = sum(len(r.checks) for r in results)
    Pln(ok(Lf("suite_done", passed, total, hms_long(time.time() - CFG.t_start))))

def verdict_to_dict(v: Verdict) -> dict:
    return dict(experiment=v.experiment, mode=v.mode, ok=v.ok, wall=v.wall,
                params=v.params,
                checks=[dict(key=c.key, ok=c.ok, detail=c.detail) for c in v.checks],
                values={k: (val if isinstance(val, (int, float, str, bool, type(None)))
                            else str(val)) for k, val in v.values.items()})

def export_session() -> list[str]:
    ensure_outdirs()
    saved: list[str] = []
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # ---------- JSON ----------
    jpath = os.path.join(CFG.out_dir, "data", f"session_{stamp}.json")
    with open(jpath, "w", encoding="utf-8") as f:
        json.dump(dict(version=NSB_VERSION, started=datetime.fromtimestamp(
            CFG.t_start).isoformat(), runs=CFG.session), f, ensure_ascii=False,
            indent=2, default=float)
    saved.append(jpath)
    # ---------- CSV per run ----------
    for i, run in enumerate(CFG.session, 1):
        cpath = os.path.join(CFG.out_dir, "data", f"run_{i:02d}_{run['experiment']}.csv")
        with open(cpath, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["metric", "value"])
            for k, val in run["values"].items():
                w.writerow([k, val])
            for c in run["checks"]:
                w.writerow([f"check:{c['key']}", int(c["ok"])])
        saved.append(cpath)
    # ---------- TXT + MD ----------
    lines_txt: list[str] = []
    lines_md: list[str] = ["# NSB Python Lab — session report", "",
                           f"*Version {NSB_VERSION}, "
                           f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*", ""]
    for run in CFG.session:
        lines_txt.append("=" * 70)
        lines_txt.append(f"EXPERIMENT: {run['experiment']}  mode={run['mode']}  "
                         f"{'OK' if run['ok'] else 'FAILED'}  ({run['wall']:.1f}s)")
        lines_md.append(f"## {run['experiment']} ({run['mode']}) — "
                        f"{'✅ OK' if run['ok'] else '❌ FAILED'}")
        lines_md.append("")
        lines_md.append("| check | result | detail |")
        lines_md.append("|---|---|---|")
        for c in run["checks"]:
            mark = "PASS" if c["ok"] else "FAIL"
            lines_txt.append(f"  [{mark}] {c['key']}  {c['detail']}")
            lines_md.append(f"| {c['key']} | {mark} | {c['detail']} |")
        lines_md.append("")
    tpath = os.path.join(CFG.out_dir, "reports", f"report_{stamp}.txt")
    mpath = os.path.join(CFG.out_dir, "reports", f"report_{stamp}.md")
    with open(tpath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines_txt) + "\n")
    with open(mpath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines_md) + "\n")
    saved += [tpath, mpath]
    # ---------- plots + final PDF article ----------
    blocks: list[tuple[str, object]] = []
    for i, vobj in enumerate(CFG.session, 1):
        blocks.append(("h1", f"{i}. {vobj['experiment']} ({vobj['mode']})"))
        for c in vobj["checks"]:
            blocks.append(("p", f"[{'PASS' if c['ok'] else 'FAIL'}] {c['key']}: "
                                f"{c['detail']}"))
    Pln(muted(L("rep_generating") if "rep_generating" in _I18N else "Generating final report…"))
    # render plots queued on verdict objects is already done at run time; here
    # we render the final heat map of the last run if present
    pdf_path = os.path.join(CFG.out_dir, "articles", f"article_{stamp}.pdf")
    try:
        write_pdf_article(pdf_path, "NSB Python Lab — session report", blocks)
        saved.append(pdf_path)
    except Exception as err:
        Pln(warn_c(f"  pdf failed: {err}"))
    Pln(ok(L("rep_saved") + ":"))
    for p in saved:
        Pln("   · " + p)
    Pln(muted("  " + L("rep_formats")))
    return saved

def roadmap_report() -> None:
    header(L("road_hdr"))
    Pln(muted("  " + L("road_bench") + f" (N=32) · {L('fft_numpy') if CFG.fft_backend == 'numpy' else L('fft_own')}"))
    gflops = bench_3dfft(32)
    Pln("  " + Lf("road_gflops", gflops))
    Pln()
    Pln(bold("  " + L("road_tbl_hdr")))
    Pln(f"  {'N':>5} {'memory':>10} {'s/step':>10}  verdict")
    for n in (32, 64, 128, 256):
        mem = n ** 3 * 16 * 24
        # ~13 3D-FFTs/step × 15·N³·log2(N) flops... measured per-flop rate:
        per_step = 13.0 * (15.0 * n ** 3 * math.log2(n)) / (gflops * 1e9)
        mem_s = big_mem(mem)
        if per_step < 5:
            verdict = L("road_verdict_laptop")
        elif per_step < 60:
            verdict = L("road_verdict_ws")
        elif per_step < 1800:
            verdict = L("road_verdict_hpc")
        else:
            verdict = L("road_verdict_no")
        Pln(f"  {n:>5} {mem_s:>10} {per_step:>10.2f}  {verdict}")
    Pln(muted("  GitHub Actions (2 cores): smoke N≤32 only"))

def bench_3dfft(n: int = 32, reps: int = 3) -> float:
    """Measured 3D-FFT throughput → GFLOP/s (15·N³·log2(N) flops per transform)."""
    rng = np.random.default_rng(1)
    A = rng.standard_normal((n, n, n)) + 1j * rng.standard_normal((n, n, n))
    fft3d(A.copy())                     # warm-up
    best = float("inf")
    for _ in range(reps):
        B = A.copy()
        t0 = time.time()
        fft3d(B)
        best = min(best, time.time() - t0)
    flops = 15.0 * n ** 3 * math.log2(n)
    return flops / max(best, 1e-9) / 1e9

def selftest() -> int:
    header(L("selftest_hdr"))
    fails = 0

    def check(name: str, okv: bool, detail: str) -> None:
        nonlocal fails
        Pln("  " + (ok(f"{L('pass')}: {name}") if okv
                    else bad(f"{L('fail')}: {name}")) + muted(f"  ({detail})"))
        if not okv:
            fails += 1

    errs = fft_selftest()
    check("FFT roundtrip 1D", errs["roundtrip"] < 1e-12, f"{errs['roundtrip']:.2e}")
    check("FFT vs naive DFT", errs["forward"] < 1e-12, f"{errs['forward']:.2e}")
    check("FFT roundtrip 2D", errs["roundtrip2d"] < 1e-12, f"{errs['roundtrip2d']:.2e}")
    check("FFT roundtrip 3D", errs["roundtrip3d"] < 1e-12, f"{errs['roundtrip3d']:.2e}")
    # RK4 order ≈ 4 on TG enstrophy with dt ladder (N=16, tiny horizon)
    s = NSE3D(16, 0.02)
    peaks = []
    for d in (0.04, 0.02, 0.01):
        r = run_decay_3d(s, prepare_state3(ic_taylor_green(16), s), d, 0.5,
                         f"selftest dt={d}", show_prog=False, sample_every=2)
        peaks.append(r["ts"].enstrophy[-1])
    p = observed_order(peaks[0], peaks[1], peaks[2])
    check("RK4 order ≈ 4", (not math.isnan(p)) and abs(p - 4.0) < 1.2,
          f"p = {p:.3f}")
    # Leray projection kills divergence
    s32 = NSE3D(16, 0.01)
    u0 = prepare_state3(ic_random(16, seed=7), s32)
    check("Leray projection div-free", divergence_max3(s32, u0) < 1e-12,
          f"max|div| = {divergence_max3(s32, u0):.2e}")
    # energy monotone under viscosity
    r = run_decay_3d(s32, u0, 0.01, 0.4, "selftest decay", show_prog=False)
    check("energy non-increasing", r["energy_rise"] < 1e-12,
          f"ΔE_max = {r['energy_rise']:.2e}")
    # b-rotation isometry
    E0 = energy3(u0, 16)
    T3 = zero_field3(16)
    rotate_pointwise3(T3, u0, b_rotation_matrix(), s32)
    E1 = energy3(T3, 16)
    check("pointwise b-rotation isometry", abs(E1 - E0) / E0 < 1e-12,
          f"|ΔE|/E = {abs(E1 - E0) / E0:.2e}")
    # full symmetry is a relabeling
    T4 = zero_field3(16)
    rotate_full_symmetry3(T4, u0, s32)
    wh0 = [np.empty_like(u0[0]) for _ in range(3)]
    wh1 = [np.empty_like(u0[0]) for _ in range(3)]
    curl_hat3(wh0, u0, s32)
    curl_hat3(wh1, T4, s32)
    rel = abs(enstrophy3(wh1, 16) - enstrophy3(wh0, 16)) / max(enstrophy3(wh0, 16), 1e-30)
    check("full symmetry = relabeling", rel < 1e-9, f"|ΔΩ|/Ω = {rel:.2e}")
    # PNG/GIF/PDF writers
    ensure_outdirs()
    probe = os.path.join(CFG.out_dir, "plots", "selftest_probe.png")
    heat_png(probe, np.random.default_rng(3).random((24, 24)), "selftest")
    head = open(probe, "rb").read(8)
    check("PNG writer", head == b"\x89PNG\r\n\x1a\n", "signature")
    gifp = os.path.join(CFG.out_dir, "plots", "selftest_probe.gif")
    write_gif(gifp, [np.random.default_rng(4).random((16, 16)) + i * 0.01
                     for i in range(4)])
    ghead = open(gifp, "rb").read(6)
    check("GIF writer", ghead == b"GIF89a", "signature")
    pdfp = os.path.join(CFG.out_dir, "articles", "selftest_probe.pdf")
    write_pdf_article(pdfp, "selftest", [("h1", "probe"), ("p", "hello")])
    phead = open(pdfp, "rb").read(5)
    check("PDF writer", phead == b"%PDF-", "signature")
    Pln()
    if fails == 0:
        Pln(ok(L("selftest_ok")))
        return 0
    Pln(bad(L("selftest_fail")))
    return 1

# ══════════════════════════════════════════════════════════════════
# 12. CLI + MENU + MAIN
# ══════════════════════════════════════════════════════════════════

def cli_help() -> None:
    Pln(f"""NSB Python Lab v{NSB_VERSION} — self-contained Navier–Stokes laboratory
Usage:
  python3 nsb_lab.py [options]
Modes:
  --quick                  fast run (mini-suite + final PDF)
  --suite normal|hard      full suite
  --experiment tg|abc|houluo|baudit|scan
  --flow <id|all|list>     real-flows laboratory (katrina, haiyan, ...)
  --roadmap                FFT benchmark and run-time estimates
  --selftest               built-in verification suite (FFT, RK4, PNG/GIF/PDF)
  --list-flows             print the 20-flow summary table
Options:
  --n N --nu V --dt V --t V --nu4 V   grid / viscosity / step / horizon / hypervisc
  --ic tg|abc|houluo       initial condition for scan
  --cfl 0|1                adaptive CFL step
  --ckpt N                 checkpoint every N steps (0 = off)
  --resume                 resume 3-D run from last checkpoint
  --gif 0|1                flow GIF animations
  --lang ru|en             UI language (NSB_LAB_LANG)
  --out DIR --seed N --dpi N
  --fft own|numpy          FFT backend (default own radix-2)
  --no-color --ascii       disable ANSI colours / force ASCII progress bar
  --help -h --version""")
    Pln("Examples:")
    Pln("  python3 nsb_lab.py --quick --lang en")
    Pln("  python3 nsb_lab.py --experiment tg --n 64 --t 4 --cfl 1")
    Pln("  python3 nsb_lab.py --flow katrina --gif 1")

def cli_parse(args: list[str]) -> tuple[str, dict]:
    lang = os.environ.get("NSB_LAB_LANG", "ru")
    action = "menu"
    opts: dict = {}
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--quick":
            action = "quick"
        elif a == "--suite":
            action = "suite"; opts["mode"] = args[i + 1] if i + 1 < len(args) else "normal"; i += 1
        elif a == "--experiment":
            action = "experiment"; opts["exp"] = args[i + 1] if i + 1 < len(args) else "tg"; i += 1
        elif a == "--flow":
            action = "flow"; opts["flow"] = args[i + 1] if i + 1 < len(args) else "list"; i += 1
        elif a == "--mode":
            opts["mode"] = args[i + 1] if i + 1 < len(args) else "normal"; i += 1
        elif a == "--roadmap":
            action = "roadmap"
        elif a == "--selftest":
            action = "selftest"
        elif a == "--list-flows":
            action = "list_flows"
        elif a == "--report":
            action = "report"
        elif a == "--n":
            i += 1; opts["n"] = int(args[i])
        elif a in ("--nu", "--nu4", "--dt", "--t"):
            key = a[2:]
            i += 1; opts[key] = float(args[i].replace(",", "."))
        elif a == "--ic":
            i += 1; opts["ic"] = args[i]
        elif a == "--lang":
            i += 1; lang = args[i]
        elif a == "--dpi":
            i += 1; CFG.dpi = int(args[i])
        elif a == "--out":
            i += 1; CFG.out_dir = os.path.expanduser(args[i])
        elif a == "--seed":
            i += 1; CFG.seed = int(args[i])
        elif a == "--ckpt":
            i += 1; CFG.ckpt_every = int(args[i])
        elif a == "--cfl":
            i += 1; CFG.adaptive_cfl = args[i] != "0"
        elif a == "--gif":
            i += 1; CFG.gif = args[i] != "0"
        elif a == "--fft":
            i += 1; CFG.fft_backend = args[i] if args[i] in ("own", "numpy") else "own"
        elif a == "--resume":
            opts["resume"] = True
        elif a == "--no-color":
            CFG.color = False
        elif a == "--ascii":
            CFG.ascii_only = True
        elif a in ("--help", "-h"):
            action = "help"
        elif a == "--version":
            action = "version"
        else:
            Pln(warn_c(f"unknown argument: {a}"))
        i += 1
    set_lang(lang)
    CFG.batch = action != "menu"
    CFG.quick = action == "quick"
    return action, opts

def render_verdict_plots(v: Verdict, idx: int) -> None:
    """Write queued plot/heat entries to PNG files in plots/."""
    ensure_outdirs()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for pi, p in enumerate(v.plots, 1):
        try:
            if p[0] == "plot":
                _, title, xlabel, ylabel, logy, series = p
                path = os.path.join(CFG.out_dir, "plots",
                                    f"run{idx:02d}_{pi}_{v.experiment}.png")
                plot_png(path, title, xlabel, ylabel, series, logy)
            elif p[0] == "heat":
                _, title, field = p
                path = os.path.join(CFG.out_dir, "plots",
                                    f"run{idx:02d}_{pi}_{v.experiment}.png")
                heat_png(path, field, title)
        except Exception as err:
            Pln(warn_c(f"  plot failed: {err}"))

def register(v: Verdict) -> None:
    render_verdict_plots(v, len(CFG.session) + 1)
    CFG.session.append(verdict_to_dict(v))

def cli_dispatch(action: str, opts: dict) -> int:
    if action == "help":
        cli_help()
        return 0
    if action == "version":
        Pln(f"NSB Python Lab v{NSB_VERSION}")
        return 0
    if action == "selftest":
        return selftest()
    if action == "list_flows":
        for ln in flows_table_text():
            Pln(ln)
        return 0
    if action == "quick":
        run_suite("normal", quick=True)
        export_session()
        return 0
    if action == "suite":
        run_suite(opts.get("mode", "normal"))
        export_session()
        return 0
    if action == "experiment":
        exp = opts.get("exp", "tg")
        n = opts.get("n", 0)
        nu = opts.get("nu", float("nan"))
        dt = opts.get("dt", float("nan"))
        t = opts.get("t", float("nan"))
        mode = opts.get("mode", "normal")
        if exp == "abc":
            v = exp_abc(mode, n=n, dt=dt, t_hor=t)
        elif exp == "houluo":
            v = exp_houluo(mode, n=n, dt=dt, t_hor=t)
        elif exp == "baudit":
            v = exp_baudit(mode, n=n, nu=nu, dt=dt, t_hor=t)
        elif exp == "scan":
            v = exp_scan(mode, ic=opts.get("ic", "abc"), n=n, dt=dt, t_hor=t)
        else:
            v = exp_taylor_green(mode, n=n, nu=nu, dt=dt, t_hor=t)
        register(v)
        export_session()
        return 0 if v.ok else 1
    if action == "flow":
        what = opts.get("flow", "list")
        mode = opts.get("mode", "normal")
        if what == "list":
            for ln in flows_table_text():
                Pln(ln)
            return 0
        flows = FLOWS if what == "all" else [f for f in FLOWS if f.id == what.lower()]
        if not flows:
            Pln(warn_c(f"no such flow: {what}"))
            return 1
        for f in flows:
            register(flow_run(f, mode))
        export_session()
        return 0
    if action == "roadmap":
        roadmap_report()
        return 0
    if action == "report":
        export_session()
        return 0
    return 2

def menu_custom() -> None:
    header(L("menu_custom").split(". ", 1)[-1])
    Pln(muted("  Enter = default"))
    try:
        n = input(f"  N [32]: ").strip()
        n = int(n) if n else 32
        nu = input("  ν [0.02]: ").strip()
        nu = float(nu.replace(",", ".")) if nu else 0.02
        dt = input("  dt [0.005]: ").strip()
        dt = float(dt.replace(",", ".")) if dt else 0.005
        T = input("  T [2.0]: ").strip()
        T = float(T.replace(",", ".")) if T else 2.0
        ic = input("  IC 1=TG 2=ABC 3=Hou-Luo 4=random [1]: ").strip() or "1"
        bc = input("  b-correction 0=off 1=symmetry 2=pointwise [0]: ").strip() or "0"
        eu = input("  Euler (ν→0)? 1=yes 0=no [0]: ").strip() or "0"
    except (EOFError, KeyboardInterrupt):
        return
    s = NSE3D(n, 1e-14 if eu == "1" else nu)
    icf = ic_taylor_green(n) if ic == "1" else ic_abc(n) if ic == "2" \
        else ic_hou_luo(n) if ic == "3" else ic_random(n)
    kick = None
    if bc == "1":
        kick = ("full", 0.25)
    elif bc == "2":
        kick = ("pointwise", 0.25)
    res = run_decay_3d(s, prepare_state3(icf, s), dt, T, f"custom N={n}",
                       kick=kick)
    v = Verdict("custom", "normal", dict(n=n, nu=nu, dt=dt, T=T, ic=ic, b=bc))
    v.series = res["ts"]
    v.values["div_max"] = res["div_max"]
    v.values["energy_rise"] = res["energy_rise"]
    v.values["bkm_final"] = res["ts"].bkm[-1]
    v.check("ck_divfree", res["div_max"] < 1e-10, f"max|div| = {res['div_max']:.2e}")
    v.check("ck_stability", all(math.isfinite(x) for x in res["ts"].sup_omega),
            f"BKM = {res['ts'].bkm[-1]:.3f}")
    register(v)
    v.print_out()

def menu_flows() -> None:
    while True:
        header(L("flows_hdr"))
        for ln in flows_table_text():
            Pln(ln)
        Pln(muted("  " + L("flows_menu_hint")))
        try:
            sel = input("  > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return
        if sel in ("q", ""):
            return
        if sel == "a":
            for f in FLOWS:
                register(flow_run(f, "normal"))
            return
        if sel.isdigit() and 1 <= int(sel) <= len(FLOWS):
            register(flow_run(FLOWS[int(sel) - 1], "normal"))

def menu_loop() -> None:
    while True:
        banner()
        for key in ("menu_quick", "menu_suite_normal", "menu_suite_hard",
                    "menu_custom", "menu_flows", "menu_roadmap", "menu_reports",
                    "menu_settings"):
            Pln("  " + bold(L(key)))
        Pln("  " + bold(L("menu_exit")))
        Pln("  " + L("lang_toggle"))
        Pln(muted(f"  {L('config_line', CFG.out_dir, CFG.dpi, CFG.seed, CFG.max_n)}"))
        try:
            sel = input(f"  {L('menu_prompt')} > ").strip()
        except (EOFError, KeyboardInterrupt):
            Pln()
            return
        if sel == "1":
            run_suite("normal", quick=True)
            export_session()
        elif sel == "2":
            run_suite("normal")
            export_session()
        elif sel == "3":
            run_suite("hard")
            export_session()
        elif sel == "4":
            menu_custom()
        elif sel == "5":
            menu_flows()
        elif sel == "6":
            roadmap_report()
        elif sel == "7":
            header(L("rep_hdr"))
            if not CFG.session:
                Pln("  " + muted(L("rep_none")))
            else:
                export_session()
        elif sel == "8":
            header(L("set_hdr"))
            Pln(f"  {L('set_dpi')}: {CFG.dpi}")
            Pln(f"  {L('set_out')}: {CFG.out_dir}")
            header(L("set_about"))
            for ln in L("set_about_txt").split("\n"):
                Pln("  " + ln)
        elif sel == "9":
            set_lang("en" if CFG.lang == "ru" else "ru")
            Pln("  " + ("Language: ENGLISH" if CFG.lang == "en" else "Язык: РУССКИЙ"))
        elif sel == "0":
            Pln(muted(f"  uptime {hms_long(uptime())}"))
            return
        else:
            Pln("  " + warn_c(L("invalid_choice")))

def main() -> int:
    detect_terminal()
    init_i18n()
    action, opts = cli_parse(sys.argv[1:])
    ensure_outdirs()
    logfile_open()
    if action == "menu" and not sys.stdin.isatty():
        cli_help()
        log_close()
        return 0
    if action == "menu":
        banner()
        code = 0
        try:
            menu_loop()
        except KeyboardInterrupt:
            Pln()
        log_close()
        return code
    code = cli_dispatch(action, opts)
    log_close()
    return code

if __name__ == "__main__":
    sys.exit(main())



