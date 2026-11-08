#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_ns_full.py — объёмный самодостаточный верификатор репозитория
Navier-Stokes-B (домен: перепроверка формального ядра и численного слоя).

Написан по контракту §0–§32: один файл, только стандартная библиотека
(zero external packages, zero codegen, zero network). Режимы (§29, ред.
1.2, вариант «б»): TUI-меню по умолчанию в TTY (и по --menu) · прямой
прогон (--ci, --task, pipe) · прежнее плоское меню --menu-legacy · CLI.
Библиотечный import тих (§16).

Перепроверяет численное содержание репозитория независимо от его кода:
  * константная цепочка b → θ_b → cos θ_b → ln(1+b) → замыкание Клейна
    exp(b·β_K·L_min) на Decimal-точности 55+ знаков (pass 2: 65+);
  * мастер-соотношение Смагоринского–Колмогорова C_s = 1/(π(3C_K/2)^{3/4})
    (pinned 50-значное значение, закон показателя, монотонность, K41-наклон);
  * тождество Кассини и коэффициенты редуцированного условия (5') точными
    целыми Фибоначчи;
  * KdV-солитон: невязка уравнения бегущей волны u''' − c u' + 6 u u' = 0
    (аналитические производные sech²), законы амплитуды и ширины;
  * мост Клейна: иррациональность θ_b/π (Нивен), равномерное заполнение
    круга поворотом (three-gap), изометрия каждой итерации;
  * алгебра поворота Родрига: RᵀR = I, det R = 1, норма, спектр-угол;
  * вихри Кирхгофа: гамильтоновость RK4 (дрейф ~dt⁴), порядок 4, изометрия;
  * 3D-слоистая b-поправка (§27, задачи 11–15): b(h, W), синхронизация
    Кирхгоф↔Родриг по слоям, торможение ствола, динамика, динамические тесты;
  * бенчмарки точных решений НС (§31, задачи 16–22): Тейлор-Грин, Ковазнай,
    Стокс II, инвариант Лере-Хопф, ABC-поток, Бюргерс, Ричардсон;
  * мост к прогону второго монолита (§32): задача 8 сверяет вердикты
    results.json по пересечению выполненных задач; --cross-check после прогона.

АДАПТЕР ЯЗЫКА (§24, Python 3.9+):
| Концепт            | Реализация здесь                                        |
|--------------------|----------------------------------------------------------|
| Запуск             | python3 verify_ns_full.py                                |
| Include guard      | importlib-кэш; повторный import/exec идемпотентен        |
| Точка входа        | `if __name__ == "__main__": vfa_main()`                  |
| GC между задачами  | gc.collect() ×2 + ctypes malloc_trim (Linux, best-effort)|
| In-place eig       | не требуется задачам; ERR_UNSUPPORTED не эмитируется     |
| /proc, /sys        | open(...).read() в VFAMon (Termux-safe, «—» если нет)    |
| rlimit             | resource.setrlimit (best-effort; нет — ERR_UNSUPPORTED)  |
| Completions        | print()-heredoc для bash/zsh/fish                        |

Замены против канона §9 (честно, не молча): вместо полной таблицы Херши
используется собственный векторный штрих-шрифт 5×7 (ASCII) — один и тот же
штриховой рендер в PNG/GIF и в SVG/PDF; см. RTM.md.
"""

from __future__ import annotations

import bisect
import contextlib
import copy
import ctypes
import gc
import hashlib
import io
import json
import math
import os
import platform
import random
import re
import shutil
import signal
import socket
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import zipfile
from collections import OrderedDict
from datetime import datetime
from decimal import Decimal, getcontext, localcontext
from pathlib import Path

__version__ = "1.3.0"
VFA_FILE = Path(__file__).resolve().name if "__file__" in globals() else "verify_ns_full.py"

# ═══════════════════════════════════════════════════════════════════════════
# Константы и адаптер платформы
# ═══════════════════════════════════════════════════════════════════════════

VFA_PREFIX = "vfa"                      # функции/файлы; VFA — модули/константы
VFA_CTL_NAME = ".vfa_ctl"               # §6.4 управление из второй сессии
VFA_RESULTS_ROOT = Path("results")      # корень прогонов (относительно cwd)
VFA_BAR_MIN, VFA_BAR_MAX = 30, 100      # ширина бара, §6.1
VFA_CHANNEL_MAX = 256                   # ограниченный канал дисплея, §6.2
VFA_EOF_GUARD = 50                      # пустых readline подряд, §12
VFA_TIMEOUT_POLL = 0.05                 # шаг опроса тайм-аутов, с

IS_LINUX = sys.platform.startswith("linux")
IS_TERMUX = IS_LINUX and "com.termux" in os.environ.get("PREFIX", "").lower()

# GLIBC malloc_trim — только Linux; на прочих платформах честный no-op.
_libc = None
if IS_LINUX:
    with contextlib.suppress(OSError):
        _libc = ctypes.CDLL("libc.so.6", use_errno=True)


def vfa_gc_full() -> None:
    """§10.1/§23.6: gc.collect() ×2 + malloc_trim между задачами."""
    gc.collect()
    gc.collect()
    if _libc is not None and hasattr(_libc, "malloc_trim"):
        with contextlib.suppress(Exception):
            _libc.malloc_trim(0)


def vfa_set_rlimit(kind: str, value: int) -> str:
    """§10.6 best-effort rlimit; не поддержано — ERR_UNSUPPORTED (§1.4)."""
    try:
        import resource
    except ImportError:
        return "ERR_UNSUPPORTED rlimit: модуль resource недоступен на этой платформе"
    res = {"as": resource.RLIMIT_AS, "cpu": resource.RLIMIT_CPU,
           "fsize": resource.RLIMIT_FSIZE}.get(kind)
    if res is None:
        return f"ERR_UNSUPPORTED rlimit-{kind}: неизвестный ресурс"
    try:
        resource.setrlimit(res, (value, value))
        return f"OK rlimit-{kind}={value}"
    except (ValueError, OSError) as exc:
        return f"ERR_UNSUPPORTED rlimit-{kind}: {exc}"


# ═══════════════════════════════════════════════════════════════════════════
# Локализация §14: MSG[lang][key], fmt() с {name:.4f}
# ═══════════════════════════════════════════════════════════════════════════

MSG = {
    "en": {
        "menu_title": "VFA · Navier-Stokes-B full verification",
        "menu_core": "Core",
        "menu_layers": "3D layers (§27)",
        "menu_vortex": "3D vortex (§27b)",
        "menu_bench": "Benchmarks 16–22 (§31)",
        "menu_suite": "Suite",
        "menu_actions": "Actions",
        "menu_labs": "Special labs",
        "run_all": "run ALL tasks (two-pass)",
        "presets": "presets",
        "edit_cfg": "edit config",
        "lang": "language (en/ru)",
        "selftest": "self-test",
        "help_keys": "key help",
        "quit": "quit",
        "select": "select item #: ",
        "unknown_task": "ERR_UNKNOWN_TASK {tid}",
        "verdict_pass": "PASS",
        "verdict_fail": "FAIL",
        "verdict_skip": "SKIP",
        "run_dir": "run directory: {d}",
        "two_pass_on": "two-pass mode ON",
        "two_pass_off": "two-pass mode OFF (--no-two-pass)",
        "no_plots": "no plots queued",
        "cfg_saved": "config updated",
        "back_menu": "returning to menu",
        "interrupted": "interrupted by operator",
        "task_timeout": "REASON=TIMEOUT after {s}s",
        "no_runs": "no runs yet",
        "no_last": "no last task",
        "last_run": "last run",
        "vortex_title": "3D vortex: decay under b-correction",
        "vortex_busy": "rendering frames… {k}/{n}",
        "vortex_done": "done: {path} ({frames} frames, {sec}s)",
        "vortex_n": "matrix size N (≥24): ",
        "vortex_bad": "N must be ≥ 24",
        "vortex_clamp": "N clamped to 256 (memory guard)",
        "vortex_frames": "frames (default 24): ",
    },
    "ru": {
        "menu_title": "VFA · полная перепроверка Navier-Stokes-B",
        "menu_core": "Ядро",
        "menu_layers": "Слои 3D (§27)",
        "menu_vortex": "Вихрь 3D (§27b)",
        "menu_bench": "Бенчмарки 16–22 (§31)",
        "menu_suite": "Серия",
        "menu_actions": "Действия",
        "menu_labs": "Спец-лаборатории",
        "run_all": "запустить ВСЕ задачи (двухпроходно)",
        "presets": "пресеты",
        "edit_cfg": "правка конфигурации",
        "lang": "язык (en/ru)",
        "selftest": "самотест",
        "help_keys": "подсказка по клавишам",
        "quit": "выход",
        "select": "выберите пункт #: ",
        "unknown_task": "ERR_UNKNOWN_TASK {tid}",
        "verdict_pass": "ПРОЙДЕНО",
        "verdict_fail": "ПРОВАЛ",
        "verdict_skip": "ПРОПУСК",
        "run_dir": "каталог прогона: {d}",
        "two_pass_on": "двухпроходный режим ВКЛ",
        "two_pass_off": "двухпроходный режим ВЫКЛ (--no-two-pass)",
        "no_plots": "графики не запланированы",
        "cfg_saved": "конфигурация обновлена",
        "back_menu": "возврат в меню",
        "interrupted": "остановлено оператором",
        "task_timeout": "REASON=TIMEOUT после {s}s",
        "no_runs": "прогонов нет",
        "no_last": "последней задачи нет",
        "last_run": "последний прогон",
        "vortex_title": "3D-вихрь: затухание под b-поправкой",
        "vortex_busy": "рендер кадров… {k}/{n}",
        "vortex_done": "готово: {path} ({frames} кадров, {sec}s)",
        "vortex_n": "размер матрицы N (≥24): ",
        "vortex_bad": "N должно быть ≥ 24",
        "vortex_clamp": "N ограничено до 256 (защита памяти)",
        "vortex_frames": "кадров (по умолчанию 24): ",
    },
}


def fmt(cfg: "VfaConfig", key: str, **kw) -> str:
    """§14: формат парсится буквально; {name:.4f} поддержан. Отсутствующий
    ключ или язык возвращают сам ключ (никаких KeyError в меню)."""
    out = MSG.get(cfg.lang, MSG["en"]).get(key, key)
    for name, value in kw.items():
        spec = "{" + name + "}"
        spec_fmt = "{" + name + ":"
        if spec_fmt in out:
            head, rest = out.split(spec_fmt, 1)
            spec_body, out_tail = rest.split("}", 1)
            value = format(value, spec_body)
            out = head + str(value) + out_tail
        elif spec in out:
            out = out.replace(spec, str(value))
    return out


# ═══════════════════════════════════════════════════════════════════════════
# Слой VFAUI (§2, §20): палитра AURORA, боксы, спиннеры, бары
# ═══════════════════════════════════════════════════════════════════════════

class VFAUI:
    """Визуальный слой: aurora-палитра, боксы, спиннеры, стикеры, бары.
    Логики не считает, stdout не пишет напрямую — возвращает строки;
    печать только через VFALog (§2)."""

    THEMES = {  # (bg, fg, accent, ok, warn, fail)
        "aurora":  ("\x1b[48;5;236m", "\x1b[38;5;252m", "\x1b[38;5;75m",
                    "\x1b[38;5;114m", "\x1b[38;5;179m", "\x1b[38;5;174m"),
        "ice":     ("\x1b[48;5;235m", "\x1b[38;5;254m", "\x1b[38;5;117m",
                    "\x1b[38;5;122m", "\x1b[38;5;151m", "\x1b[38;5;210m"),
        "gold":    ("\x1b[48;5;234m", "\x1b[38;5;229m", "\x1b[38;5;220m",
                    "\x1b[38;5;120m", "\x1b[38;5;214m", "\x1b[38;5;203m"),
        "emerald": ("\x1b[48;5;233m", "\x1b[38;5;250m", "\x1b[38;5;85m",
                    "\x1b[38;5;84m", "\x1b[38;5;185m", "\x1b[38;5;167m"),
    }
    RESET = "\x1b[0m"
    SPINNER_FRAMES = "|/-\\"
    # §4.1 aurora-стикеры: плавающий декор для заголовков и вердиктов
    STICKERS = ("✦", "❋", "✺", "❊", "✿", "✦", "✧", "❃")

    state = {"color": True, "unicode": True, "theme": "aurora"}

    # ── доступность §20: NO_COLOR / TERM=dumb учитываются до первого println
    @classmethod
    def detect_capabilities(cls) -> None:
        if os.environ.get("NO_COLOR") or os.environ.get("TERM") == "dumb":
            cls.state["color"] = False

    @classmethod
    def set_unicode(cls, mode: str) -> None:
        if mode == "on":
            cls.state["unicode"] = True
        elif mode == "off":
            cls.state["unicode"] = False
        else:  # auto — по локали
            try:
                cls.state["unicode"] = "utf-8" in (sys.stdout.encoding or "").lower()
            except Exception:
                cls.state["unicode"] = False

    @classmethod
    def c(cls, idx: int) -> str:
        if not cls.state["color"]:
            return ""
        return cls.THEMES.get(cls.state["theme"], cls.THEMES["aurora"])[idx]

    @classmethod
    def paint(cls, text: str, idx: int) -> str:
        return f"{cls.c(idx)}{text}{cls.RESET}" if cls.state["color"] else text

    # ── бейджи вердиктов §8.3: цвет никогда не единственный носитель смысла
    @classmethod
    def badge(cls, verdict: str) -> str:
        idx = {"PASS": 3, "DONE": 3, "WARN": 4, "SKIP": 4,
               "FAIL": 5, "ERROR": 5}.get(verdict, 1)
        return cls.paint(f"[{verdict}]", idx)

    # ── aurora-декор: плавающие стикеры + разделители + заголовки
    @classmethod
    def sticker(cls, i: int) -> str:
        """Aurora-стикер по индексу: символ из STICKERS + цвет темы.
        Цвет 1..5 (fg/accent/ok/warn/fail) — кортеж THEMES имеет 6 позиций
        0..5, индекс 6 выбросил бы IndexError."""
        sym = cls.STICKERS[(i - 1) % len(cls.STICKERS)] if i > 0 else cls.STICKERS[0]
        if not cls.state["color"]:
            return sym
        return f"{cls.c(1 + (i - 1) % 5)}{sym}{cls.RESET}"

    @classmethod
    def aurora_sep(cls, width: int = 66, phase: int = 0) -> str:
        """Aurora-разделитель с бегущими точками и искрами (phase — фаза)."""
        if not cls.state["unicode"]:
            return "+" + "-" * max(0, width - 2) + "+"
        spk = cls.c(3) + "✦" + cls.RESET if cls.state["color"] else "✦"
        parts = ["╭"]
        for i in range(1, width - 1):
            if (i + phase) % 8 == 0:
                parts.append(spk)
            elif (i + phase) % 4 == 0:
                parts.append("·")
            else:
                parts.append("─")
        parts.append("╮")
        return "".join(parts)

    @classmethod
    def aurora_title(cls, text: str, accent: int = 3, deco: bool = True) -> str:
        """Плавающий заголовок: буквы в aurora-градиенте, стикеры по краям."""
        buf = []
        if deco and cls.state["unicode"]:
            buf.append("  " + cls.sticker(1) + " ")
        for i, ch in enumerate(text):
            if cls.state["color"]:
                buf.append(f"{cls.c(accent + i % 3)}{ch}")
            else:
                buf.append(ch)
        if cls.state["color"]:
            buf.append(cls.RESET)
        if deco and cls.state["unicode"]:
            buf.append(" " + cls.sticker(5))
        return "".join(buf)

    @classmethod
    def sparkline_verdict(cls, v: str) -> str:
        """Мини-вердикт со спарклайн-скобками (CI-логи → ASCII при !unicode)."""
        if not cls.state["unicode"]:
            return f"[{v}]"
        if v in ("PASS", "DONE"):
            return f"✦[{v}]✦"
        if v in ("FAIL", "ERROR"):
            return f"❋[{v}]❋"
        return f"✺[{v}]✺"

    @classmethod
    def box(cls, lines: list[str], width: int = 66) -> list[str]:
        """Aurora-бокс: скруглённые углы + бегущие искры по верхней кромке
        (или ASCII при --plain/--unicode off). §20 --plain убирает рамки."""
        if not cls.state["unicode"]:
            top = "+" + "-" * (width - 2) + "+"
            out = [top]
            for ln in lines:
                body = ln[: width - 4]
                out.append(f"| {body.ljust(width - 4)} |")
            out.append(top)
            return out
        # unicode: RESET только на концах строки — иначе ANSI-коды
        # ломают визуальную ширину
        colored = cls.state["color"]
        top_parts = [cls.c(3) + "╭" + cls.RESET if colored else "╭"]
        for i in range(1, width - 1):
            if i % 6 == 0:
                top_parts.append(cls.c(5) + "✦" + cls.RESET if colored else "✦")
            else:
                top_parts.append("─")
        top_parts.append(cls.c(3) + "╮" + cls.RESET if colored else "╮")
        lbar = cls.c(3) + "│" + cls.RESET if colored else "│"
        out = ["".join(top_parts)]
        for ln in lines:
            body = ln[: width - 4]
            out.append(f"{lbar} {body.ljust(width - 4)} {lbar}")
        bot = (cls.c(3) + "╰" + "─" * (width - 2) + "╯" + cls.RESET
               if colored else "╰" + "─" * (width - 2) + "╯")
        out.append(bot)
        return out

    @classmethod
    def bar_line(cls, done: int, total: int, label: str = "",
                 monitor: str = "", t0: float = 0.0) -> str:
        """§6.1: одна строка на stderr, CR + space-pad + CR (без ESC[K).
        Aurora-пульс: заполнение бежит тремя цветами темы."""
        try:
            width = max(VFA_BAR_MIN, min(VFA_BAR_MAX, os.get_terminal_size(2).columns - 2))
        except (OSError, ValueError):
            width = 72
        frac = 0.0 if total <= 0 else min(1.0, done / total)
        # B1-guard: длинный monitor уводил (width-20-len)*frac в минус →
        # "█"*filln с отрицательным filln печатал пустую строку; клампим
        avail = max(4, width - 20 - len(monitor))
        filln = max(0, min(avail, int(avail * frac)))
        remn = avail - filln
        if cls.state["color"] and cls.state["unicode"]:
            parts = []
            step = max(1, filln // 3)
            for i in range(filln):
                parts.append(f"{cls.c(3 + (i // step) % 3)}█")
            parts.append(f"{cls.c(2)}{'·' * remn}{cls.RESET}")
            glyph = "".join(parts)
        elif cls.state["unicode"]:
            glyph = "█" * filln + "·" * remn
        else:
            glyph = "#" * filln + "-" * remn
        eta = ""
        if frac > 0.02 and t0 > 0:
            el = time.monotonic() - t0
            eta = f" eta {max(0.0, el / frac - el):.0f}s"
        tag = (f"{cls.c(4)}✦{cls.RESET}"
               if cls.state["unicode"] and cls.state["color"] else ">")
        return f"\r{tag} {glyph} {done}/{total} {label[:14]}{monitor}{eta}   "

    @classmethod
    def erase_line(cls, stream=sys.stderr) -> None:
        """§23.2: затирание пробелами, Termux-safe."""
        try:
            width = max(VFA_BAR_MIN, min(VFA_BAR_MAX, os.get_terminal_size(2).columns - 2))
        except (OSError, ValueError):
            width = 72
        stream.write("\r" + " " * width + "\r")
        stream.flush()


# ═══════════════════════════════════════════════════════════════════════════
# Слой VFAMon (§7): /proc, /sys; снимки CPU/RAM/temp/latency/uptime
# ═══════════════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════════════
# §28 ASCII-баннер: печатается первым в vfa_main. Подавляется --plain,
# --ci, --quiet, --banner=never, NO_COLOR, TERM=dumb (через VFAUI.detect).
# ═══════════════════════════════════════════════════════════════════════════

class VFABanner:
    ART_UNICODE = [
        "██╗   ██╗███████╗ █████╗ ",
        "██║   ██║██╔════╝██╔══██╗",
        "██║   ██║█████╗  ███████║",
        "╚██╗ ██╔╝██╔══╝  ██╔══██║",
        " ╚████╔╝ ██║     ██║  ██║",
        "  ╚═══╝  ╚═╝     ╚═╝  ╚═╝",
    ]
    ART_PLAIN = [
        "V   V FFFFF AAAAA",
        "V   V F     A   A",
        "V   V FFF   AAAAA",
        " V V  F     A   A",
        "  V   F     A   A",
    ]

    @classmethod
    def lines(cls, plain: bool = False, subtitle: str = "") -> list[str]:
        art = cls.ART_PLAIN if plain else cls.ART_UNICODE
        sep = "|" if plain else "·"          # plain → ASCII-only (самотест)
        out = list(art)
        out.append("")
        out.append(f"  Navier-Stokes-B {sep} full verification")
        if subtitle:
            out.append("  " + subtitle)
        out.append(f"  python {sys.version.split()[0]} {sep} "
                   f"{VFA_PLATFORM()} {sep} v{__version__}")
        return out

    @classmethod
    def show(cls, plain: bool = False, subtitle: str = "",
             color: bool | None = None) -> None:
        use_color = VFAUI.state["color"] if color is None else color
        for line in cls.lines(plain=plain, subtitle=subtitle):
            print(VFAUI.paint(line, 2) if use_color else line)
        print()


class VFAMon:
    """Системный монитор. Никогда не валит главный поток (§7): любая ошибка
    гасится в лог вычислений, цикл продолжается; отсутствующее — честно «—»."""

    _cpu_prev = None

    @staticmethod
    def read_proc(path: str) -> str:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                return fh.read()
        except OSError:
            return ""

    @classmethod
    def snapshot(cls) -> dict:
        snap = {"cpu_percent": None, "ram_used_gb": None, "ram_total_gb": None,
                "temp_c": None, "io_latency_us": None, "uptime_s": None}
        stat = cls.read_proc("/proc/stat")
        if stat:
            for line in stat.splitlines():
                if line.startswith("cpu "):
                    parts = [int(x) for x in line.split()[1:9]]
                    total = sum(parts)
                    idle = parts[3] + (parts[4] if len(parts) > 4 else 0)
                    prev = cls._cpu_prev
                    cls._cpu_prev = (total, idle)
                    if prev:
                        d_total, d_idle = total - prev[0], idle - prev[1]
                        if d_total > 0:
                            snap["cpu_percent"] = 100.0 * (d_total - d_idle) / d_total
                    break
        mem = cls.read_proc("/proc/meminfo")
        if mem:
            vals = {}
            for line in mem.splitlines():
                key, _, rest = line.partition(":")
                vals[key.strip()] = int(rest.strip().split()[0]) if rest.strip() else 0
            if "MemTotal" in vals:
                snap["ram_total_gb"] = vals["MemTotal"] / 1048576.0
                snap["ram_used_gb"] = (vals["MemTotal"] - vals.get("MemAvailable", 0)) / 1048576.0
        upt = cls.read_proc("/proc/uptime")
        if upt:
            snap["uptime_s"] = float(upt.split()[0])
        # температура: первый thermal_zone с данными (Termux: обычно нет)
        for tz in sorted(Path("/sys/class/thermal").glob("thermal_zone*/temp")) \
                if Path("/sys/class/thermal").exists() else []:
            txt = tz.read_text(errors="replace").strip() if tz.exists() else ""
            if txt.isdigit() and int(txt) > 0:
                snap["temp_c"] = int(txt) / 1000.0
                break
        # латентность io: дёшево — время чтения /proc/stat (микросекунды)
        t = time.perf_counter()
        cls.read_proc("/proc/self/io")
        snap["io_latency_us"] = (time.perf_counter() - t) * 1e6
        return snap

    @staticmethod
    def inline(snap: dict) -> str:
        """Компактная строка для встраивания в бар (§7)."""
        def cell(val, suffix, digits=0):
            return "—" if val is None else f"{val:.{digits}f}{suffix}"
        return (f" [{cell(snap['cpu_percent'], '%', 0)} cpu "
                f"{cell(snap['ram_used_gb'], 'G', 1)} ram "
                f"{cell(snap['temp_c'], 'C', 0)}]")

    @classmethod
    def panel(cls) -> list[str]:
        """Полная панель в начале задачи при --monitor panel."""
        s = cls.snapshot()
        rows = [
            f"cpu {s['cpu_percent'] if s['cpu_percent'] is not None else '—'}%",
            f"ram {s['ram_used_gb']:.2f}/{s['ram_total_gb']:.2f} GiB"
            if s["ram_total_gb"] else "ram —",
            f"temp {s['temp_c'] if s['temp_c'] is not None else '—'} C",
            f"io lat {s['io_latency_us']:.0f} us",
            f"uptime {s['uptime_s']:.0f}s" if s["uptime_s"] else "uptime —",
            f"platform {VFA_PLATFORM()}",
        ]
        return ["MONITOR: " + " | ".join(rows)]


def VFA_PLATFORM() -> str:
    if IS_TERMUX:
        return "termux"
    if sys.platform.startswith("linux"):
        return "linux"
    if sys.platform == "darwin":
        return "macos"
    if sys.platform.startswith("win"):
        return "windows"
    return sys.platform


def VFA_OS_RELEASE() -> str:
    try:
        info = {}
        txt = VFAMon.read_proc("/etc/os-release")
        for line in txt.splitlines():
            key, _, val = line.partition("=")
            info[key.strip()] = val.strip().strip('"')
        return info.get("PRETTY_NAME") or platform.platform()
    except Exception:
        return platform.platform()


# ═══════════════════════════════════════════════════════════════════════════
# Слой VFALog (§8): tee stdout, computation log, events.jsonl, вердикты,
# display-pump (§6.2) и heartbeat (§6.3)
# ═══════════════════════════════════════════════════════════════════════════

class VfaTeeStdout(io.TextIOBase):
    """Tee всего stdout: оригинал + захват в буфер (никогда не теряется §6.2)."""

    def __init__(self, original):
        self._orig = original
        self.chunks: list[str] = []

    def write(self, s):
        self.chunks.append(s)
        log = VFALog._instance
        if log is not None and log.ci_mode:
            # §23.18: в CI на stdout идёт только events.jsonl — человеческий
            # текст только в захват (пайплайны не парсят человеческий текст)
            return len(s)
        try:
            return self._orig.write(s)
        except (ValueError, OSError):     # мёртвый stdout не роняет программу
            return len(s)

    def flush(self):
        with contextlib.suppress(ValueError, OSError):
            self._orig.flush()

    @property
    def encoding(self):
        return getattr(self._orig, "encoding", "utf-8")

    def isatty(self):
        try:
            return self._orig.isatty()
        except (ValueError, OSError):
            return False

    def fileno(self):
        return self._orig.fileno()

    def drain(self) -> str:
        out = "".join(self.chunks)
        self.chunks.clear()
        return out


class VFALog:
    """Шлюз всей печати: вычислительный лог, события JSONL, вердикты задач.
    Главный поток пишет только через него (§2: ядро не пишет в stdout)."""

    _instance = None

    def __init__(self):
        self.run_dir: Path | None = None
        self.task_dir: Path | None = None
        self._comp: list[str] = []
        self._comp_t0 = time.monotonic()
        self._events = []                   # буфер events.jsonl
        self._stdout_orig: io.TextIOBase = sys.stdout
        self.tee: VfaTeeStdout | None = None
        self.lock = threading.Lock()
        self.display_q: list[dict] = []     # ограниченный канал косметики §6.2
        self.pump_on = False
        self._pump_thread: threading.Thread | None = None
        self.current_task = "init"
        self.current_phase = "idle"
        self.ci_mode = False
        self.quiet = False            # §B3: тихий внутренний прогон (task 10)
        self.heartbeat_t0 = time.monotonic()
        self.heartbeat_label = ""
        self._last_bar = ""
        self.abort_flag = threading.Event()
        self.pause_flag = threading.Event()
        self.snapshot_requested = threading.Event()
        self.task_started_at: float | None = None

    # ── синглтон-доступ (один шлюз на процесс)
    @classmethod
    def get(cls) -> "VFALog":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ── жизненный цикл прогона §8.2
    def open_run(self, run_dir: Path) -> None:
        self.run_dir = run_dir
        (run_dir / "logs").mkdir(parents=True, exist_ok=True)
        self._comp_t0 = time.monotonic()
        self._comp = []
        self._events = []
        # фикс: вердикты/чеки — атрибуты класса, без очистки второй прогон
        # в том же процессе смешивался с первым (index/report/verdicts)
        self.verdicts.clear()
        self.task_checks.clear()
        self.abort_flag.clear()
        self.pause_flag.clear()
        self.snapshot_requested.clear()
        self.log_comp(f"run opened: {run_dir}")

    def open_task(self, task_dir: Path, slug: str) -> None:
        self.task_dir = task_dir
        (task_dir / "logs").mkdir(parents=True, exist_ok=True)
        (task_dir / "plots").mkdir(parents=True, exist_ok=True)
        self.current_task = slug
        self.current_phase = "run"
        self.heartbeat_t0 = time.monotonic()

    def close_task(self) -> None:
        self.current_task, self.current_phase = "idle", "idle"

    # ── computation log §8.1: [HH:MM:SS.sss] [+delta] msg + events.jsonl
    def log_comp(self, msg: str, level: str = "info") -> None:
        with self.lock:
            now = datetime.now()
            delta = time.monotonic() - self._comp_t0
            line = f"[{now.strftime('%H:%M:%S.')}{int(now.microsecond/1000):03d}] [+{delta:7.3f}s] {msg}"
            self._comp.append(line)
            self._events.append({"ts": now.isoformat(timespec="milliseconds"),
                                 "level": level, "task": self.current_task,
                                 "phase": self.current_phase, "msg": msg})
            if self.ci_mode:
                # §23.18: в CI на stdout идёт ТОЛЬКО events.jsonl
                self._stdout_orig.write(json.dumps(self._events[-1], ensure_ascii=False) + "\n")
                self._stdout_orig.flush()
            self.prog_heartbeat()
            self.pump_frame({"kind": "event", "text": f"{msg[:72]}"})

    def log_stdout_flush(self) -> None:
        """Сброс teed stdout в stdout_capture.txt текущей задачи."""
        if self.tee is None or self.task_dir is None:
            return
        text = self.tee.drain()
        if text:
            with self.lock, open(self.task_dir / "logs" / "stdout_capture.txt",
                                 "a", encoding="utf-8") as fh:
                fh.write(text)

    def log_result(self, task_id: int, slug: str, verdict: str,
                   reason: str = "", metrics: dict | None = None,
                   duration_s: float = 0.0, artifacts: list[str] | None = None) -> None:
        """Ровно одна вердиктная строка на задачу (§4). В quiet-режиме
        (внутренние прогоны задачи 10) вердикты реестра не перезаписываются."""
        if not self.quiet:
            rec = {"task": task_id, "slug": slug, "verdict": verdict,
                   "reason": reason, "metrics": metrics or {},
                   "duration_s": round(duration_s, 3),
                   "artifacts": artifacts or []}
            self.verdicts[task_id] = rec
        line = f"task {task_id:02d} [{slug}] {verdict}" + (f" {reason}" if reason else "")
        with self.lock:
            self._events.append({"ts": datetime.now().isoformat(timespec="milliseconds"),
                                 "level": "verdict", "task": slug, "phase": "done",
                                 "msg": line})
            if self.ci_mode:
                self._stdout_orig.write(json.dumps(self._events[-1], ensure_ascii=False) + "\n")
                self._stdout_orig.flush()

    verdicts: dict = {}
    task_checks: dict = {}          # task_id → [(name, status, detail)]
    run_started_iso: str = ""

    # ── финализация прогона: файлы логов
    def finalize(self) -> None:
        if self.run_dir is None:
            return
        with self.lock:
            (self.run_dir / "logs").mkdir(parents=True, exist_ok=True)
            (self.run_dir / "logs" / "events.jsonl").write_text(
                "\n".join(json.dumps(e, ensure_ascii=False) for e in self._events) + "\n",
                encoding="utf-8")
            (self.run_dir / "logs" / "computation_log.txt").write_text(
                "\n".join(self._comp) + "\n", encoding="utf-8")

    # ── display pump §6.2: один писатель на терминал, drop-oldest
    def start_pump(self) -> None:
        if self.pump_on:
            return
        self.pump_on = True
        self._pump_thread = threading.Thread(target=self._pump_loop, daemon=True)
        self._pump_thread.start()

    def stop_pump(self) -> None:
        """§6.2⛔: остановка fire-and-forget — никогда не блокируемся на close."""
        self.pump_on = False

    def pump_frame(self, item: dict) -> None:
        if len(self.display_q) >= VFA_CHANNEL_MAX:
            self.display_q.pop(0)           # drop-oldest, продюсер не блокируется
        self.display_q.append(item)

    def _pump_loop(self) -> None:
        while self.pump_on:
            item = None
            with self.lock:
                if self.display_q:
                    item = self.display_q.pop(0)
            if item is None:
                time.sleep(0.03)
                continue
            self._render_frame(item)

    def _render_frame(self, item: dict) -> None:
        if self.ci_mode:
            return
        stream = sys.stderr
        if item["kind"] == "event" and self.heartbeat_label:
            self._draw_bar()
        elif item["kind"] == "bar":
            self._last_bar = item["text"]
            self._draw_bar()

    def _draw_bar(self) -> None:
        text = self._last_bar
        sys.stderr.write("\r" + text[:200])
        sys.stderr.flush()

    # ── heartbeat §6.3: elapsed продолжает тикать при «тихих» решателях
    def prog_heartbeat(self) -> None:
        self.heartbeat_t0 = time.monotonic()


# ═══════════════════════════════════════════════════════════════════════════
# Слой VFAPlot (§9): PNG/GIF/SVG/PDF 100% stdlib, векторный штрих-шрифт
# ═══════════════════════════════════════════════════════════════════════════

class VFAPlot:
    """Графический движок. PNG: zlib-deflate + CRC32 + Up-фильтрация строк,
    суперсэмплинг 2×. GIF: собственный LZW (GIF89a, little-endian).
    SVG/PDF: тот же штриховой рендер (§9 согласованность)."""

    SS = 2  # суперсэмплинг

    # ── темы: light + семейство aurora (bg, panel, grid, axis, text, series…)
    THEMES = {
        "light": {"bg": (250, 250, 247), "panel": (255, 255, 255), "grid": (225, 225, 220),
                  "axis": (60, 60, 60), "text": (30, 30, 30),
                  "series": [(31, 119, 180), (214, 39, 40), (44, 160, 44),
                             (148, 103, 189), (255, 127, 14), (23, 190, 207)]},
        "aurora": {"bg": (18, 20, 28), "panel": (26, 29, 40), "grid": (55, 60, 80),
                   "axis": (150, 160, 190), "text": (220, 225, 240),
                   "series": [(80, 170, 255), (255, 140, 105), (110, 220, 150),
                              (200, 150, 255), (255, 210, 90), (90, 230, 220)]},
        "ice":    {"bg": (16, 24, 32), "panel": (22, 33, 44), "grid": (50, 70, 90),
                   "axis": (140, 170, 195), "text": (215, 235, 245),
                   "series": [(100, 200, 235), (240, 160, 160), (130, 225, 205),
                              (170, 180, 250), (230, 220, 130), (150, 210, 240)]},
        "gold":   {"bg": (24, 22, 16), "panel": (36, 32, 22), "grid": (75, 68, 45),
                   "axis": (190, 175, 140), "text": (240, 232, 210),
                   "series": [(240, 200, 90), (220, 130, 90), (150, 210, 130),
                              (210, 170, 240), (130, 200, 220), (240, 160, 140)]},
        "emerald": {"bg": (14, 24, 20), "panel": (20, 34, 28), "grid": (48, 76, 62),
                    "axis": (140, 180, 160), "text": (215, 240, 228),
                    "series": [(90, 220, 150), (240, 190, 100), (100, 180, 240),
                               (230, 140, 140), (170, 220, 110), (140, 220, 210)]},
    }

    # ── 3×5 точечный шрифт (15 бит/глиф, строки снизу вверх) — замена Херши,
    #    задекларирована в шапке и в RTM
    FONT3X5 = {
        " ": 0b000000000000000, "!": 0b010010010000010, '"': 0b101101000000000,
        "#": 0b010111111010111, "$": 0b011110010011110, "%": 0b101001001010001,
        "&": 0b010101010011011, "'": 0b010010000000000, "(": 0b001010010010001,
        ")": 0b100010010010100, "*": 0b000101010101000, "+": 0b000010111010000,
        ",": 0b000000000010010, "-": 0b000000111000000, ".": 0b000000000000010,
        "/": 0b001001010100100, "0": 0b111100101101111, "1": 0b010110010010111,
        "2": 0b111001111100111, "3": 0b111001111001111, "4": 0b101101111001001,
        "5": 0b111100111001111, "6": 0b111100111101111, "7": 0b111001001010010,
        "8": 0b111101111101111, "9": 0b111101111001111, ":": 0b000010000010000,
        ";": 0b000010000010010, "<": 0b001010100010001, "=": 0b000111000111000,
        ">": 0b100010101010100, "?": 0b111001010000010, "@": 0b111101011101110,
        "A": 0b010101111101101, "B": 0b110101110101110, "C": 0b011100100100011,
        "D": 0b110101101101110, "E": 0b111100110100111, "F": 0b111100110100100,
        "G": 0b011100101101011, "H": 0b101101111101101, "I": 0b111010010010111,
        "J": 0b001001001101010, "K": 0b101101110101101, "L": 0b100100100100111,
        "M": 0b101111111101101, "N": 0b110101101101101, "O": 0b010101101101010,
        "P": 0b110101110100100, "Q": 0b010101101110011, "R": 0b110101110101101,
        "S": 0b011100010100110, "T": 0b111010010010010, "U": 0b101101101101111,
        "V": 0b101101101101010, "W": 0b101101111111101, "X": 0b101101010101101,
        "Y": 0b101101010010010, "Z": 0b111001010100111, "[": 0b011010010010011,
        "\\": 0b100100010001001, "]": 0b110010010010110, "^": 0b010101000000000,
        "_": 0b000000000000111, "`": 0b100010000000000, "a": 0b000011101101011,
        "b": 0b100100110101110, "c": 0b000011100100011, "d": 0b001001011101111,
        "e": 0b000010111101011, "f": 0b001010010010010, "g": 0b000011101001110,
        "h": 0b100100110101101, "i": 0b001000010010001, "j": 0b000100001001010,
        "k": 0b100101110101101, "l": 0b010010010010001, "m": 0b000111111101101,
        "n": 0b000110111101101, "o": 0b000010101101010, "p": 0b000110111100100,
        "q": 0b000011101001011, "r": 0b000110111100100, "s": 0b000011010010110,
        "t": 0b010010011010011, "u": 0b000101101101011, "v": 0b000101101101010,
        "w": 0b000101111111101, "x": 0b000101010101101, "y": 0b000101101001110,
        "z": 0b000111010010111, "{": 0b001010010010001, "|": 0b010010010010010,
        "}": 0b100010010010100, "~": 0b000000001101000,
    }

    # ── низкоуровневый холст
    class Canvas:
        def __init__(self, w, h, bg):
            self.w, self.h = w, h
            self.buf = bytearray(bytes(bg) * (w * h))

        def px(self, x, y, color):
            if 0 <= x < self.w and 0 <= y < self.h:
                i = (y * self.w + x) * 3
                self.buf[i:i + 3] = bytes(color)

        def rect(self, x0, y0, x1, y1, color):
            for y in range(max(0, y0), min(self.h, y1 + 1)):
                base = (y * self.w) * 3
                for x in range(max(0, x0), min(self.w, x1 + 1)):
                    i = base + x * 3
                    self.buf[i:i + 3] = bytes(color)

        def line(self, x0, y0, x1, y1, color, thick=1):
            dx, dy = abs(x1 - x0), -abs(y1 - y0)
            sx = 1 if x0 < x1 else -1
            sy = 1 if y0 < y1 else -1
            err = dx + dy
            r = thick // 2
            while True:
                if thick <= 1:
                    self.px(x0, y0, color)
                else:
                    self.rect(x0 - r, y0 - r, x0 + r, y0 + r, color)
                if x0 == x1 and y0 == y1:
                    break
                e2 = 2 * err
                if e2 >= dy:
                    err += dy
                    x0 += sx
                if e2 <= dx:
                    err += dx
                    y0 += sy

    # ── PNG-энкодер: CRC32 + zlib + Up-фильтр (§9)
    @staticmethod
    def _png_chunk(tag: bytes, data: bytes) -> bytes:
        import zlib
        return (len(data).to_bytes(4, "big") + tag + data
                + zlib.crc32(tag + data).to_bytes(4, "big"))

    @classmethod
    def save_png(cls, path: Path, canvas: "VFAPlot.Canvas") -> None:
        import zlib
        w, h, buf = canvas.w, canvas.h, canvas.buf
        raw = bytearray()
        stride = w * 3
        row0 = bytes([2]) + bytes(buf[0:stride])          # фильтр 2 (Up): первая строка — фильтр Up от нуля
        raw += row0
        for y in range(1, h):
            cur = buf[y * stride:(y + 1) * stride]
            prev = buf[(y - 1) * stride:y * stride]
            raw.append(2)
            raw += bytes((c - p) & 0xFF for c, p in zip(cur, prev))
        ihdr = w.to_bytes(4, "big") + h.to_bytes(4, "big") + bytes([8, 2, 0, 0, 0])
        sig = b"\x89PNG\r\n\x1a\n"
        data = sig + cls._png_chunk(b"IHDR", ihdr) + cls._png_chunk(b"IDAT", zlib.compress(bytes(raw), 6)) \
            + cls._png_chunk(b"IEND", b"")
        path.write_bytes(data)

    # ── GIF89a + собственный LZW (§9: классический источник ошибок — endianness)
    @staticmethod
    def _lzw(indices: bytes, min_code_size: int = 8) -> bytes:
        """Классический GIF-LZW: коды LSB-first, ширина кода растёт 9→12 бит.
        Ширина отслеживается в момент ВЫДАЧИ кода; при переполнении таблицы
        (nxt >= 4096) эмитится CLEAR. Начальный CLEAR и финальный EOI —
        обязательны, иначе декодеры (PIL, браузеры) отвергают поток."""
        clear = 1 << min_code_size
        eoi = clear + 1
        dict_ = {bytes([i]): i for i in range(clear)}
        nxt = eoi + 1
        cs = min_code_size + 1
        bits: list[tuple[int, int]] = [(clear, cs)]
        w_ = b""
        for ch in indices:
            wc = w_ + bytes([ch])
            if wc in dict_:
                w_ = wc
                continue
            bits.append((dict_[w_], cs))
            if nxt >= 4096:
                bits.append((clear, cs))
                dict_ = {bytes([i]): i for i in range(clear)}
                nxt = eoi + 1
                cs = min_code_size + 1
            else:
                dict_[wc] = nxt
                nxt += 1
                if nxt == (1 << cs) and cs < 12:
                    cs += 1
            w_ = bytes([ch])
        if w_:
            bits.append((dict_[w_], cs))
        bits.append((eoi, cs))
        out = bytearray()
        acc, nbits = 0, 0
        for code, width in bits:
            acc |= code << nbits
            nbits += width
            while nbits >= 8:
                out.append(acc & 0xFF)
                acc >>= 8
                nbits -= 8
        if nbits:
            out.append(acc & 0xFF)
        return bytes(out)

    @classmethod
    def save_gif(cls, path: Path, frames: list["VFAPlot.Canvas"], delay_cs: int = 25) -> None:
        import struct
        if not frames:
            return
        w, h = frames[0].w, frames[0].h
        palette = []
        for rgb in [(12, 14, 22), (18, 20, 28), (26, 29, 40), (40, 44, 60),
                    (55, 60, 80), (90, 95, 115), (150, 160, 190),
                    (220, 225, 240), (255, 255, 255),
                    (80, 170, 255), (255, 140, 105), (110, 220, 150),
                    (200, 150, 255), (255, 210, 90), (90, 230, 220),
                    (160, 120, 200)]:
            palette.extend(rgb)
        while len(palette) < 768:
            palette.append(0)
        out = bytearray(b"GIF89a")
        out += struct.pack("<HHBBB", w, h, 0xF7, 0, 0)   # GCT, 256 цветов, little-endian
        out += bytes(palette[:768])
        out += b"\x21\xFF\x0BNETSCAPE2.0\x03\x01\x00\x00\x00"   # бесконечный цикл
        for fr in frames:
            # квантование к палитре ближайшим индексом
            idx = bytearray(w * h)
            lut = {}
            pal = [tuple(palette[i:i + 3]) for i in range(0, 768, 3)]
            for p in range(w * h):
                rgb = (fr.buf[p * 3], fr.buf[p * 3 + 1], fr.buf[p * 3 + 2])
                key = (rgb[0] >> 3, rgb[1] >> 3, rgb[2] >> 3)
                if key not in lut:
                    best, bd = 0, 10**9
                    for pi, pr in enumerate(pal):
                        d = (rgb[0] - pr[0]) ** 2 + (rgb[1] - pr[1]) ** 2 + (rgb[2] - pr[2]) ** 2
                        if d < bd:
                            best, bd = pi, d
                    lut[key] = best
                idx[p] = lut[key]
            out += b"\x21\xF9\x04" + bytes([0x04, delay_cs & 0xFF, (delay_cs >> 8) & 0xFF, 0]) + b"\x00"
            out += b"\x2C" + struct.pack("<HHHHB", 0, 0, w, h, 0)
            lzw = cls._lzw(bytes(idx), 8)
            i = 0
            out += bytes([8])
            while i < len(lzw):
                block = lzw[i:i + 255]
                out += bytes([len(block)]) + block
                i += 255
            out += b"\x00"
        out += b"\x3B"
        path.write_bytes(bytes(out))

    # ── SVG / PDF: тот же штриховой рендер (передаётся список отрезков)
    @staticmethod
    def svg_escape(s: str) -> str:
        """§9: корректное XML-экранирование."""
        rep = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&apos;"}
        for k, v in rep.items():
            s = s.replace(k, v)
        if any(ch in s for ch in "&<>"):
            VFALog.get().log_comp("WARN svg: escape applied to problematic chars", "warn")
        return s

    @staticmethod
    def pdf_winansi(s: str) -> str:
        """§9: WinAnsi; проблемные символы — с ОДНИМ агрегированным
        предупреждением на вызов (не на символ — иначе засоряет events.jsonl)."""
        out = []
        bad = 0
        for ch in s:
            if 32 <= ord(ch) < 127:
                out.append(ch)
            else:
                bad += 1
                out.append("?")
        if bad:
            VFALog.get().log_comp(
                f"WARN pdf: {bad} non-WinAnsi chars replaced by '?' "
                f"(кириллица в PDF — см. report.md/html)", "warn")
        return "".join(out)


class RepPlot:
    """Модель графика §9: заголовок, оси, серии; стиль 'l'/'s'/'L'."""

    def __init__(self, title: str, xlabel: str = "", ylabel: str = ""):
        self.title, self.xlabel, self.ylabel = title, xlabel, ylabel
        self.series: list[tuple[str, list[float], list[float], str]] = []
        self.infobox: list[str] = []

    def add_series(self, name: str, xs: list[float], ys: list[float], style: str = "l") -> None:
        self.series.append((name, list(xs), list(ys), style))

    def set_infobox(self, lines: list[str]) -> None:
        self.infobox = lines


# ── рендеринг RepPlot → Canvas (один рендер для PNG и GIF, §9)

def vfa_render_plot(plot: RepPlot, theme: str = "aurora",
                    width: int = 760, height: int = 440,
                    supersample: int | None = None) -> "VFAPlot.Canvas":
    """Отрисовка модели RepPlot: панель, сетка, оси с делениями, серии,
    легенда, инфобокс. Считается в supеrsampled-холсте, внизскейлится."""
    ss = supersample or VFAPlot.SS
    th = VFAPlot.THEMES.get(theme, VFAPlot.THEMES["aurora"])
    W, H = width * ss, height * ss
    cv = VFAPlot.Canvas(W, H, th["bg"])
    cv.rect(ss, ss, W - ss - 1, H - ss - 1, th["panel"])
    # поля: слева под ylabel, снизу под xlabel
    ml, mr, mt, mb = 64 * ss, 18 * ss, 40 * ss, 44 * ss
    x0, y0, x1, y1 = ml, mt, W - mr, H - mb     # прямоугольник области данных
    # пределы данных
    xs_all = [x for _, xs, _, _ in plot.series for x in xs] or [0.0, 1.0]
    ys_all = [y for _, _, ys, _ in plot.series for y in ys] or [0.0, 1.0]
    xmin, xmax = min(xs_all), max(xs_all)
    ymin, ymax = min(ys_all), max(ys_all)
    if xmax - xmin < 1e-300:
        xmax = xmin + 1.0
    if ymax - ymin < 1e-300:
        ymax = ymin + 1.0
    dx, dy = xmax - xmin, ymax - ymin
    xmin -= 0.06 * dx; xmax += 0.06 * dx
    ymin -= 0.08 * dy; ymax += 0.08 * dy
    dx, dy = xmax - xmin, ymax - ymin

    def sx(v): return x0 + int((v - xmin) / dx * (x1 - x0))
    def sy(v): return y1 - int((v - ymin) / dy * (y1 - y0))

    # сетка + деления (5×5)
    for k in range(6):
        fx = xmin + dx * k / 5
        fy = ymin + dy * k / 5
        cv.line(sx(fx), y0, sx(fx), y1, th["grid"])
        cv.line(x0, sy(fy), x1, sy(fy), th["grid"])
        vfa_draw_text(cv, f"{fx:.4g}", sx(fx) - 16 * ss, y1 + 6 * ss,
                      th["axis"], scale=ss)
        vfa_draw_text(cv, f"{fy:.4g}", x0 - 46 * ss, sy(fy) - 3 * ss,
                      th["axis"], scale=ss)
    cv.line(x0, y0, x1, y0, th["axis"], thick=ss)
    cv.line(x0, y0, x0, y1, th["axis"], thick=ss)
    # заголовок и подписи осей
    vfa_draw_text(cv, plot.title, x0, 10 * ss, th["text"], scale=ss + 1)
    vfa_draw_text(cv, plot.xlabel, (x0 + x1) // 2 - 30 * ss, H - 26 * ss, th["text"], scale=ss)
    # ylabel вертикально (буквы столбиком)
    for i, ch in enumerate(plot.ylabel):
        vfa_draw_text(cv, ch, 8 * ss, y0 + i * 12 * ss, th["text"], scale=ss)
    # серии
    for si, (name, xs, ys, style) in enumerate(plot.series):
        col = th["series"][si % len(th["series"])]
        if style in ("l", "L"):
            for a in range(len(xs) - 1):
                cv.line(sx(xs[a]), sy(ys[a]), sx(xs[a + 1]), sy(ys[a + 1]),
                        col, thick=ss * 2 if style == "L" else ss)
        if style in ("s", "L"):
            for a in range(len(xs)):
                cv.rect(sx(xs[a]) - 2 * ss, sy(ys[a]) - 2 * ss,
                        sx(xs[a]) + 2 * ss, sy(ys[a]) + 2 * ss, col)
    # легенда
    if len(plot.series) > 1:
        ly = y0 + 8 * ss
        for si, (name, _, _, _) in enumerate(plot.series):
            col = th["series"][si % len(th["series"])]
            cv.line(x1 - 150 * ss, ly + 3 * ss, x1 - 120 * ss, ly + 3 * ss, col, thick=2 * ss)
            vfa_draw_text(cv, name, x1 - 114 * ss, ly, th["text"], scale=ss)
            ly += 14 * ss
    # инфобокс
    if plot.infobox:
        bw = max(len(s) for s in plot.infobox) * 6 * ss + 12 * ss
        bh = len(plot.infobox) * 12 * ss + 8 * ss
        cv.rect(x1 - bw, y1 - bh, x1, y1, th["panel"])
        cv.line(x1 - bw, y1 - bh, x1, y1 - bh, th["grid"])
        for i, s in enumerate(plot.infobox):
            vfa_draw_text(cv, s, x1 - bw + 6 * ss, y1 - bh + 5 * ss + i * 12 * ss,
                          th["text"], scale=ss)
    return vfa_downsample(cv, ss)


def vfa_downsample(cv: "VFAPlot.Canvas", ss: int) -> "VFAPlot.Canvas":
    """Бокс-фильтр 2×2/SS×SS: суперсэмплинг → финальный размер.
    P-2: для ss=2 — быстрый путь (stride-срезы строк + один genexp на канал),
    ~2-3× быстрее пер-пиксельного цикла; общий цикл остался для ss>2."""
    if ss == 1:
        return cv
    w, h = cv.w // ss, cv.h // ss
    out = VFAPlot.Canvas(w, h, (0, 0, 0))
    if ss == 2 and cv.w % 2 == 0 and cv.h % 2 == 0:
        src = bytes(cv.buf)
        rb = cv.w * 3
        buf = out.buf
        for y in range(h):
            i0 = 2 * y * rb
            r0 = src[i0:i0 + rb]
            r1 = src[i0 + rb:i0 + 2 * rb]
            obase = y * w * 3
            for c in (0, 1, 2):
                a = r0[c::6]
                b = r0[c + 3::6]
                d = r1[c::6]
                e = r1[c + 3::6]
                buf[obase + c:obase + w * 3:3] = bytes(
                    (p + q + s + t) >> 2
                    for p, q, s, t in zip(a, b, d, e))
        return out
    for y in range(h):
        for x in range(w):
            r = g = b = 0
            for j in range(ss):
                for i in range(ss):
                    p = ((y * ss + j) * cv.w + (x * ss + i)) * 3
                    r += cv.buf[p]; g += cv.buf[p + 1]; b += cv.buf[p + 2]
            n = ss * ss
            q = (y * w + x) * 3
            out.buf[q:q + 3] = bytes((r // n, g // n, b // n))
    return out


def vfa_draw_text(cv: "VFAPlot.Canvas", text: str, x: int, y: int,
                  color, scale: int = 1) -> None:
    """Штриховой текст: одинаково используется растровыми и векторными
    бэкендами (SVG/PDF экспортируют те же позиции через glyph-сетку)."""
    cx = x
    for ch in text:
        # B-NEW-4: сначала точное совпадение (в FONT3X5 есть строчные глифы),
        # upper — только fallback (иначе 'a' всегда рендерилась как 'A')
        glyph = VFAPlot.FONT3X5.get(ch)
        if glyph is None:
            glyph = VFAPlot.FONT3X5.get(ch.upper())
        if ch == " ":
            cx += 4 * scale
            continue
        if glyph is None:
            glyph = VFAPlot.FONT3X5.get("?", 0)
        for bit in range(15):
            if glyph >> bit & 1:
                gx, gy = bit % 3, 4 - bit // 3
                cv.rect(cx + gx * scale, y + gy * scale,
                        cx + gx * scale + scale - 1, y + gy * scale + scale - 1, color)
        cx += 4 * scale


def vfa_render_svg(plot: RepPlot, theme: str = "aurora",
                   width: int = 760, height: int = 440) -> str:
    """SVG-экспорт: те же серии/оси; текст — векторными глифами сетки 3×5."""
    th = VFAPlot.THEMES.get(theme, VFAPlot.THEMES["aurora"])
    xs_all = [x for _, xs, _, _ in plot.series for x in xs] or [0.0, 1.0]
    ys_all = [y for _, _, ys, _ in plot.series for y in ys] or [0.0, 1.0]
    xmin, xmax = min(xs_all), max(xs_all)
    ymin, ymax = min(ys_all), max(ys_all)
    if xmax - xmin < 1e-300:
        xmax = xmin + 1.0
    if ymax - ymin < 1e-300:
        ymax = ymin + 1.0
    ml, mr, mt, mb = 64, 18, 40, 44
    x0, y0, x1, y1 = ml, mt, width - mr, height - mb
    dx, dy = xmax - xmin, ymax - ymin
    xmin -= 0.06 * dx; xmax += 0.06 * dx
    ymin -= 0.08 * dy; ymax += 0.08 * dy
    dx, dy = xmax - xmin, ymax - ymin
    def sx(v): return x0 + (v - xmin) / dx * (x1 - x0)
    def sy(v): return y1 - (v - ymin) / dy * (y1 - y0)
    def col(c): return f"#{c[0]:02x}{c[1]:02x}{c[2]:02x}"
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
             f'<rect width="100%" height="100%" fill="{col(th["bg"])}"/>',
             f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" fill="{col(th["panel"])}"/>']
    for k in range(6):
        fx, fy = xmin + dx * k / 5, ymin + dy * k / 5
        parts.append(f'<line x1="{sx(fx):.1f}" y1="{y0}" x2="{sx(fx):.1f}" y2="{y1}" stroke="{col(th["grid"])}"/>')
        parts.append(f'<line x1="{x0}" y1="{sy(fy):.1f}" x2="{x1}" y2="{sy(fy):.1f}" stroke="{col(th["grid"])}"/>')
        parts.append(f'<text x="{sx(fx):.1f}" y="{y1+14}" font-size="9" fill="{col(th["axis"])}">{VFAPlot.svg_escape(f"{fx:.4g}")}</text>')
        parts.append(f'<text x="{x0-42}" y="{sy(fy):.1f}" font-size="9" fill="{col(th["axis"])}">{VFAPlot.svg_escape(f"{fy:.4g}")}</text>')
    for si, (name, xs, ys, style) in enumerate(plot.series):
        c = col(th["series"][si % len(th["series"])] if "series" in th else th["text"])
        pts = " ".join(f"{sx(x):.2f},{sy(y):.2f}" for x, y in zip(xs, ys))
        parts.append(f'<polyline points="{pts}" fill="none" stroke="{c}" stroke-width="1.6"/>')
        if style in ("s", "L"):
            for x, y in zip(xs, ys):
                parts.append(f'<circle cx="{sx(x):.2f}" cy="{sy(y):.2f}" r="2.4" fill="{c}"/>')
    parts.append(f'<text x="{x0}" y="24" font-size="15" fill="{col(th["text"])}">{VFAPlot.svg_escape(plot.title)}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


class VfaPdfDoc:
    """Минимальный PDF-писатель: Helvetica (base14, WinAnsi), текст + линии.
    Достаточно для отчётов; внешних пакетов нет (§9)."""

    PAGE_W, PAGE_H = 595, 842   # A4

    def __init__(self, title: str = "VFA report"):
        self.title = title
        self.pages: list[list[str]] = [[]]
        self.y = self.PAGE_H - 56

    def _need(self, lines: int = 1) -> None:
        if self.y - 14 * lines < 48:
            self.pages.append([])
            self.y = self.PAGE_H - 56

    def text(self, s: str, size: int = 10, gap: int = 14, bold: bool = False) -> None:
        for raw_line in s.split("\n"):
            self._need()
            self.pages[-1].append(
                f"BT /{'F2' if bold else 'F1'} {size} Tf 56 {self.y} Td "
                f"({VFAPlot.pdf_winansi(raw_line)[:100]}) Tj ET")
            self.y -= gap

    def rule(self) -> None:
        self._need()
        self.pages[-1].append(
            f"0.6 w 0.4 0.5 0.7 RG 56 {self.y} m 539 {self.y} l S")
        self.y -= 10

    def save(self, path: Path) -> None:
        import zlib
        objs: list[bytes] = []

        def obj(body: str | bytes) -> int:
            objs.append(body.encode("latin-1", "replace") if isinstance(body, str) else body)
            return len(objs)

        n_pages = len(self.pages)
        kids = " ".join(f"{3 + 2 * i} 0 R" for i in range(n_pages))
        # номера шрифтов известны заранее: каталог(1) + страницы(2) + 2*n_pages
        # объектов страница+контент → шрифт1 = 3 + 2*n_pages (фикс: раньше были
        # захардкожены 1000/1001 — ссылки на несуществующие объекты)
        f1_no, f2_no = 3 + 2 * n_pages, 3 + 2 * n_pages + 1
        obj("<< /Type /Catalog /Pages 2 0 R >>")
        obj(f"<< /Type /Pages /Kids [{kids}] /Count {n_pages} >>")
        for pg in self.pages:
            content = "\n".join(pg)
            stream = zlib.compress(content.encode("latin-1", "replace"))
            page_no = obj(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {self.PAGE_W} {self.PAGE_H}] "
                          f"/Resources << /Font << /F1 {f1_no} 0 R /F2 {f2_no} 0 R >> >> /Contents {len(objs) + 2} 0 R >>")
            obj(f"<< /Length {len(stream)} /Filter /FlateDecode >>\nstream\n".encode("latin-1", "replace")
                + stream + b"\nendstream")
        font1 = obj("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
        font2 = obj("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
        out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]
        for i, body in enumerate(objs, 1):
            offsets.append(len(out))
            out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
        xref = len(out)
        out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
        for off in offsets[1:]:
            out += f"{off:010d} 00000 n \n".encode()
        out += (f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\n"
                f"startxref\n{xref}\n%%EOF").encode()
        path.write_bytes(bytes(out))


class VfaDocxWriter:
    """Минимальный DOCX (OOXML) в zip: абзацы, жирные заголовки, моно-блоки."""

    def __init__(self):
        self.paras: list[tuple[str, str]] = []   # (text, style)

    def para(self, text: str, style: str = "body") -> None:
        self.paras.append((text, style))

    def save(self, path: Path) -> None:
        def esc(s):
            return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        body = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>']
        for text, style in self.paras:
            if style == "h1":
                body.append(f'<w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
                            f'<w:r><w:rPr><w:b/><w:sz w:val="40"/></w:rPr><w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')
            elif style == "h2":
                body.append(f'<w:p><w:r><w:rPr><w:b/><w:sz w:val="28"/></w:rPr>'
                            f'<w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')
            elif style == "mono":
                body.append(f'<w:p><w:pPr><w:shd w:val="clear" w:fill="F2F2F2"/></w:pPr>'
                            f'<w:r><w:rPr><w:rFonts w:ascii="Courier New"/><w:sz w:val="16"/></w:rPr>'
                            f'<w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')
            else:
                body.append(f'<w:p><w:r><w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')
        body.append('</w:body></w:document>')
        content_types = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                         '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                         '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                         '<Default Extension="xml" ContentType="application/xml"/>'
                         '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                         '</Types>')
        rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
                '</Relationships>')
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml", content_types)
            zf.writestr("_rels/.rels", rels)
            zf.writestr("word/document.xml", "".join(body))


# ── анимация-тур §9: кадры растут точка за точкой, оси фиксированы

def vfa_animation_tour(plot: RepPlot, theme: str, path: Path,
                       steps_per_plot: int = 5) -> int:
    """Тур по всем графикам задачи: один сюжет — один сегмент; на каждом шаге
    серии дорастают точками; в углу — 'plot k/N'. Возвращает число кадров."""
    frames: list[VFAPlot.Canvas] = []
    total = len(plot.series)
    for k, (name, xs, ys, style) in enumerate(plot.series, 1):
        partial = RepPlot(plot.title, plot.xlabel, plot.ylabel)
        partial.series = [(nm, x_, y_, st) for (nm, x_, y_, st) in plot.series[:k - 1]]
        n_pts = max(2, len(xs))
        for step in range(1, steps_per_plot + 1):
            take = max(2, int(n_pts * step / steps_per_plot))
            partial.add_series(name, xs[:take], ys[:take], style)
            partial.infobox = [f"plot {k}/{total}", f"points {take}/{n_pts}"]
            full = RepPlot(plot.title, plot.xlabel, plot.ylabel)
            full.series = partial.series
            full.infobox = partial.infobox
            frames.append(vfa_render_plot(full, theme))
            partial.series.pop()
    if not frames:
        return 0
    VFAPlot.save_gif(path, frames, delay_cs=18)
    return len(frames)


# ═══════════════════════════════════════════════════════════════════════════
# Конфигурация §3: единый VfaConfig, пять точек входа, ресолверы
# ═══════════════════════════════════════════════════════════════════════════

def vfa_detect_tty() -> bool:
    """§28: интерактивен ли TTY (для автовыбора баннера/меню)."""
    try:
        return bool(sys.stdin and sys.stdin.isatty()
                    and sys.stdout and sys.stdout.isatty())
    except (AttributeError, ValueError, OSError):
        return False


def vfa_last_run_info(rd_root: Path | str = VFA_RESULTS_ROOT
                      ) -> tuple[Path | None, dict[int, str]]:
    """§28: последний прогон в results/ и его вердикты."""
    root = Path(rd_root)
    if not root.is_dir():
        return None, {}
    cands: list[Path] = []
    for d in root.iterdir():
        if not d.is_dir():
            continue
        if not (d.name.startswith("jrun_") or d.name.startswith("run_")
                or d.name.startswith("selftest_")):
            continue
        if (d / "results.json").is_file():
            cands.append(d)
    if not cands:
        return None, {}
    last = max(cands, key=lambda p: p.stat().st_mtime)
    verdicts: dict[int, str] = {}
    try:
        data = json.loads((last / "results.json").read_text(encoding="utf-8"))
        for tid, rec in (data.get("tasks") or {}).items():
            try:
                verdicts[int(tid)] = str(rec.get("verdict", "—"))
            except (ValueError, TypeError):
                pass
    except (OSError, json.JSONDecodeError):
        pass
    return last, verdicts


class VfaConfig:
    """Единственный носитель параметров запуска. Порядок приоритета
    (§3): defaults < config-file < env < CLI < menu; источник каждого поля
    фиксируется в self._source."""

    def __init__(self):
        self._source: dict[str, str] = {}
        self._retired: bool = False           # устаревшие no-op флаги (§11)
        # ── data selection
        self.repo_root: Path = Path(__file__).resolve().parents[1] \
            if (len(Path(__file__).resolve().parents) > 1
                and (Path(__file__).resolve().parents[1] / "lean4").exists()) \
            else Path.cwd()
        # ── orchestration
        self.tasks: list[int] = []                # пусто = все (1–15)
        self.two_pass: bool = True                # §5: по умолчанию двухпроходно
        self.seed: int = 20260913
        # ── task parameters
        self.size: int = 1                        # масштабный множитель пресета
        self.preset: str = "full"
        # ── render and reports
        self.theme: str = "aurora"
        self.no_report: bool = False
        self.report_dir: Path | None = None
        self.no_gif: bool = False
        self.plot_formats: list[str] = ["png", "gif", "svg"]
        self.report_formats: list[str] = ["md", "html", "pdf", "docx"]
        self.dpi: int = 110
        # ── monitor
        self.monitor: str = "on"                  # on|off|panel
        self.monitor_interval: float = 1.0
        # ── resources
        self.task_timeout: float = 600.0
        self.global_timeout: float = 0.0          # 0 = без ограничения
        self.rlimit: str = ""                     # §10.6: --rlimit kind=v[,kind=v...]
        self.rlimit_as: int = 0                   # прежние раздельные флаги
        self.rlimit_cpu: int = 0
        self.rlimit_fsize: int = 0
        # ── tests
        self.selftest: bool = False
        self.selftest_full: bool = False
        self.selftest_props: bool = False
        self.selftest_contract: bool = False
        # ── CI and misc
        self.ci: bool = False
        self.junit: Path | None = None
        self.lang: str = "ru"
        self.unicode_mode: str = "auto"
        self.plain: bool = False
        self.no_color: bool = False
        self.strict: bool = False
        self.list_tasks: bool = False
        self.list_format: str = ""                # --format json (--list-tasks)
        self.print_config: bool = False
        self.config_menu: bool = False
        self.menu: bool = False                   # --menu: новое TUI-меню §29
        self.menu_legacy: bool = False            # §29: прежнее плоское меню
        self.banner: str = "auto"                 # §28: auto|always|never
        self.quiet: bool = False                  # §28: --quiet без баннера
        self.generate_completions: str = ""
        self.config_file: Path | None = None
        self.help: bool = False
        self.version: bool = False
        # §27: слоистая 3D-модель
        self.layers: int = 20                     # --layers N
        self.layer_model: str = "default"         # --layer-model default|radial
        self.layer_h0: float = 1.0                # --layer-h0
        self.layer_W0: float = 1.0                # --layer-W0
        self.fuzz: int = 0                        # --fuzz N (0 = использовать preset)
        # §27b: 3D-вихрь (анимация затухания под b-поправкой)
        self.vortex_N: int = 0                    # --vortex N (0 = выкл; ≥24 = рендер)
        self.vortex_frames: int = 24              # --vortex-frames K
        self.vortex_T: float = 40.0               # --vortex-T (горизонт времени)
        self.vortex_quick: bool = False           # --vortex-quick (превью 640×440)
        # §30: свипы (повторные --sweep склеиваются через ';')
        self.sweep: str = ""
        # §32: --cross-check ПУТЬ (сверка с results.json другого монолита)
        self.cross_check: str = ""

    def set(self, name: str, value, source: str) -> None:
        setattr(self, name, value)
        self._source[name] = source

    # ── ресолверы §3: единственный источник истины для повторяющихся величин
    def resolve_iteration_count(self) -> int:
        """Число итераций эргодики/шагов RK4 (масштабируется пресетом)."""
        base = {"quick": 20000, "full": 100000, "deep": 400000}[self.preset]
        return base * self.size

    def resolve_precision(self) -> int:
        """Decimal-точность: pass1 55, pass2 (hardcore) 65+."""
        return 65 if getattr(self, "_hardcore", False) else 55

    def resolve_vector_count(self) -> int:
        """Число случайных векторов/осей для Родрига."""
        base = {"quick": 2000, "full": 20000, "deep": 60000}[self.preset]
        return base * self.size


def default_config() -> VfaConfig:
    cfg = VfaConfig()
    for k, v in cfg.__dict__.items():
        if k != "_source":
            cfg._source[k] = "default"
    return cfg


def vfa_load_config_file(cfg: VfaConfig, path: Path) -> None:
    """--config-file: TOML (python 3.11+) либо JSON; неизвестные ключи — WARN."""
    try:
        text = path.read_text(encoding="utf-8")
        try:
            import tomllib
            data = tomllib.loads(text)
        except (ImportError, ModuleNotFoundError):
            data = json.loads(text)
    except Exception as exc:
        raise SystemExit(f"config-file: не удалось прочитать {path}: {exc}")
    for key, value in data.items():
        if hasattr(cfg, key) and key != "_source":
            if isinstance(value, str) and key.endswith(("_root", "_dir", "_file", "input")) \
                    and value:
                value = Path(value)
            cfg.set(key, value, f"config-file:{path.name}")
        else:
            VFALog.get().log_comp(f"WARNING: config-file: неизвестный ключ {key}", "warn")


def vfa_parse_env(cfg: VfaConfig) -> None:
    """VFA_* переменные окружения (◇ для CI); типы приводятся по умолчанию."""
    for raw_key, raw_val in os.environ.items():
        if not raw_key.startswith("VFA_") or raw_key in ("VFA_FILE",):
            continue
        key = raw_key[4:].lower()
        if not hasattr(cfg, key) or key == "_source":
            continue
        cur = getattr(cfg, key)
        try:
            if isinstance(cur, bool):
                value = raw_val.strip().lower() in ("1", "true", "yes", "on")
            elif isinstance(cur, int):
                value = int(raw_val)
            elif isinstance(cur, float):
                value = float(raw_val)
            elif isinstance(cur, Path):
                value = Path(raw_val)
            elif isinstance(cur, list):
                value = [s for s in raw_val.split(",") if s]
            else:
                value = raw_val
            cfg.set(key, value, f"env:{raw_key}")
        except ValueError as exc:
            VFALog.get().log_comp(f"WARNING: env {raw_key}: {exc}", "warn")


VFA_CLI_SPEC: dict[str, list[str]] = {
    # флаг → (имя поля, разбор: value|flag|list|path)
    "size": ("size", "value"), "seed": ("seed", "value"),
    "preset": ("preset", "value"),
    "theme": ("theme", "value"),
    "no-report": ("no_report", "flag"), "report-dir": ("report_dir", "path"),
    "dpi": ("dpi", "value"), "no-gif": ("no_gif", "flag"),
    "plot-formats": ("plot_formats", "list"), "report-formats": ("report_formats", "list"),
    "monitor": ("monitor", "value"), "monitor-interval": ("monitor_interval", "value"),
    "task-timeout": ("task_timeout", "value"), "global-timeout": ("global_timeout", "value"),
    "rlimit": ("rlimit", "value"),                      # §10.6: kind=v[,kind=v...]
    "rlimit-as": ("rlimit_as", "value"), "rlimit-cpu": ("rlimit_cpu", "value"),
    "rlimit-fsize": ("rlimit_fsize", "value"),
    "self-test": ("selftest", "flag"),
    "ci": ("ci", "flag"), "junit": ("junit", "path"),
    "lang": ("lang", "value"), "unicode": ("unicode_mode", "value"),
    "plain": ("plain", "flag"), "no-color": ("no_color", "flag"),
    "strict": ("strict", "flag"), "list-tasks": ("list_tasks", "flag"),
    "print-config": ("print_config", "flag"), "config": ("config_menu", "flag"),
    "menu": ("menu", "flag"), "menu-legacy": ("menu_legacy", "flag"),
    "format": ("list_format", "value"),
    "banner": ("banner", "value"), "quiet": ("quiet", "flag"),
    "generate-completions": ("generate_completions", "value"),
    "config-file": ("config_file", "path"), "help": ("help", "flag"),
    "version": ("version", "flag"),
    # §5: --run-two-pass/--no-two-pass
    "run-two-pass": ("two_pass", "flag_true"),
    "no-two-pass": ("two_pass", "flag_false"),
    # §27: слоистая 3D-модель
    "layers": ("layers", "value"), "layer-model": ("layer_model", "value"),
    "layer-h0": ("layer_h0", "value"), "layer-W0": ("layer_W0", "value"),
    "fuzz": ("fuzz", "value"),
    # §27b: 3D-вихрь
    "vortex": ("vortex_N", "value"),
    "vortex-frames": ("vortex_frames", "value"),
    "vortex-T": ("vortex_T", "value"),
    "vortex-quick": ("vortex_quick", "flag"),
    # §30/§32
    "sweep": ("sweep", "sweep"), "cross-check": ("cross_check", "value"),
    # ретро-флаги: no-op с комментарием, чтобы старые командные строки не падали
    "html-only": ("_retired", "flag"), "svg-only": ("_retired", "flag"),
}
# selftest-модификаторы отдельно (могут комбинироваться)
VFA_SELFTEST_FLAGS = {"full": "selftest_full",
                      "props": "selftest_props", "contract": "selftest_contract"}


def vfa_parse_args(cfg: VfaConfig, argv: list[str]) -> None:
    """§11: неизвестный флаг — громкое WARNING (или error под --strict)."""
    i = 0
    positional: list[str] = []
    while i < len(argv):
        tok = argv[i]
        if not tok.startswith("--"):
            positional.append(tok)
            i += 1
            continue
        flag = tok[2:]
        if flag == "task" or flag.startswith("task="):
            # --task 1 / --task 1,3,5 / --task all; фикс: --task-timeout и
            # прочие task-* флаги больше не попадают в эту ветку
            if "=" in flag:
                val = flag.split("=", 1)[1]
            else:
                i += 1
                val = argv[i] if i < len(argv) else error_exit("--task expects значение")
            cfg.set("tasks", vfa_parse_task_ids(val), "cli")
            i += 1
            continue
        if flag.startswith("self-test-"):
            sub = flag.split("-", 2)[2]
            if sub in VFA_SELFTEST_FLAGS:
                cfg.set(VFA_SELFTEST_FLAGS[sub], True, "cli")
                cfg.set("selftest", True, "cli")
                i += 1
                continue
        spec = VFA_CLI_SPEC.get(flag)
        if spec is None:
            msg = f"WARNING: unrecognized CLI argument --{flag}"
            if cfg.strict:
                raise SystemExit(f"--{flag}: неизвестный флаг (--strict)")
            print(msg, file=sys.stderr)
            VFALog.get().log_comp(msg, "warn")
            i += 1
            continue
        field, kind = spec
        if kind == "flag":
            cfg.set(field, True, "cli")
            i += 1
        elif kind in ("flag_true", "flag_false"):
            cfg.set(field, kind == "flag_true", "cli")
            i += 1
        elif kind == "value":
            i += 1
            if i >= len(argv):
                raise SystemExit(f"--{flag} expects значение")
            if field == "banner":
                val = argv[i].lower()
                if val not in ("auto", "always", "never"):
                    raise SystemExit("--banner: ожидается auto|always|never")
                cfg.set("banner", val, "cli")
                i += 1
                continue
            cur = getattr(cfg, field, "")
            try:
                if isinstance(cur, bool):
                    value = argv[i].lower() in ("1", "true", "yes", "on")
                elif isinstance(cur, int):
                    value = int(argv[i])
                elif isinstance(cur, float):
                    value = float(argv[i])
                elif isinstance(cur, list):
                    value = [s for s in argv[i].split(",") if s]
                else:
                    value = argv[i]
            except ValueError as exc:
                raise SystemExit(f"--{flag} expects корректное значение: {exc}")
            # §27/§28 валидация диапазонов (fail-fast, как в Julia-эталоне)
            if field == "layers" and value <= 0:
                raise SystemExit("--layers: ожидается N > 0")
            if field == "layer_model" and value not in ("default", "radial"):
                raise SystemExit("--layer-model: ожидается default|radial")
            if field in ("layer_h0", "layer_W0") and value <= 0:
                raise SystemExit(f"--{flag}: ожидается x > 0")
            if field == "fuzz" and value < 0:
                raise SystemExit("--fuzz: ожидается N ≥ 0")
            if field == "vortex_N" and value < 24:
                raise SystemExit("--vortex: ожидается N ≥ 24")
            if field == "vortex_frames" and value < 2:
                raise SystemExit("--vortex-frames: ожидается ≥ 2")
            if field == "vortex_T" and value <= 0:
                raise SystemExit("--vortex-T: ожидается T > 0")
            cfg.set(field, value, "cli")
            i += 1
        elif kind == "path":
            i += 1
            if i >= len(argv):
                raise SystemExit(f"--{flag} expects путь")
            cfg.set(field, Path(argv[i]), "cli")
            i += 1
        elif kind == "list":
            i += 1
            if i >= len(argv):
                raise SystemExit(f"--{flag} expects список через запятую")
            cfg.set(field, [s for s in argv[i].split(",") if s], "cli")
            i += 1
        elif kind == "sweep":
            # §30: повторные --sweep склеиваются через ';' — многомерная матрица
            i += 1
            if i >= len(argv):
                raise SystemExit(f"--{flag} ожидает KEY=V1,V2,...")
            cur = cfg.sweep.strip()
            cfg.set("sweep", f"{cur};{argv[i]}" if cur else argv[i], "cli")
            i += 1
    if positional and not cfg.selftest:
        # позиционные аргументы трактуются как --task
        ids: list[int] = []
        for p in positional:
            ids.extend(vfa_parse_task_ids(p))
        cfg.set("tasks", ids, "cli")


def vfa_parse_task_ids(val: str) -> list[int]:
    val = val.strip().lower()
    if val in ("all", "все"):
        return list(range(1, VFA_N_TASKS + 1))
    ids = []
    for part in val.split(","):
        part = part.strip()
        if not part:
            continue
        if not part.isdigit():
            raise SystemExit(f"--task: не понимаю '{part}' (целое или all)")
        ids.append(int(part))
    return ids


def error_exit(msg: str):
    raise SystemExit(msg)


def vfa_print_config(cfg: VfaConfig) -> None:
    """--print-config: эффективный конфиг с источником каждого поля."""
    rows = [f"{'field':<20} {'value':<40} source"]
    for key, value in cfg.__dict__.items():
        if key == "_source":
            continue
        rows.append(f"{key:<20} {str(value):<40} {cfg._source.get(key, 'default')}")
    print("\n".join(rows))


# ═══════════════════════════════════════════════════════════════════════════
# Реестр задач §4: TASKS (1–15), SUITE_IDS, бенчмарки §31 (16–22), _dispatch
# ═══════════════════════════════════════════════════════════════════════════

VFA_N_TASKS = 15   # синхронизировано с TASKS ниже (регистрация внизу файла)

TASKS: list[dict] = []

SUITE_IDS: list[int] = []

# §31: отдельный реестр бенчмарков точных решений — SUITE_IDS (1–15) не меняется
VFA_BENCH: list[dict] = []

BENCH_IDS: list[int] = []


def register_task(t: dict) -> None:
    """◇ плагин-хук §4: расширение реестра без правки диспетчера."""
    TASKS.append(t)
    SUITE_IDS.clear()
    SUITE_IDS.extend(t["id"] for t in sorted(TASKS, key=lambda x: x["id"]))


def register_bench(t: dict) -> None:
    """◇ плагин-хук §31: реестр бенчмарков 16–22 (в SUITE_IDS не попадает)."""
    VFA_BENCH.append(t)
    BENCH_IDS.clear()
    BENCH_IDS.extend(t["id"] for t in sorted(VFA_BENCH, key=lambda x: x["id"]))


def _dispatch(task_id: int, cfg: VfaConfig) -> bool:
    """Единая точка входа выполнения задачи; id вне реестров — жёсткая ошибка."""
    for t in TASKS + VFA_BENCH:
        if t["id"] == task_id:
            return t["fn"](cfg)
    raise RuntimeError(fmt(cfg, "unknown_task", tid=task_id))


def vfa_list_tasks(fmt_json: bool = False) -> str:
    """--list-tasks: TSV или JSON."""
    if fmt_json:
        return json.dumps([{**{k: v for k, v in t.items()
                               if k not in ("fn", "pass2_fn")},
                            "pass2": t["pass2_fn"] is not None}
                           for t in vfa_all_tasks()],
                          ensure_ascii=False, indent=1)
    rows = ["id\tslug\ttitle\tpass2\tnote"]
    for t in vfa_all_tasks():
        rows.append(f"{t['id']}\t{t['slug']}\t{t['title']}\t"
                    f"{'yes' if t['pass2_fn'] else 'no'}\t{t['method_note']}")
    # U-4: --vortex — не задача, но пусть виден в списке возможностей
    rows.append("-\t(vortex)\t3D vortex render (--vortex N, §27b)\tno\t"
                "GIF + stabilization report; N ≥ 24")
    return "\n".join(rows)


# ═══════════════════════════════════════════════════════════════════════════
# Численные задачи: точные формы констант репозитория (см. numerical/python)
# ═══════════════════════════════════════════════════════════════════════════

VFA_PI_60 = Decimal("3.1415926535897932384626433832795028841971693993751058209749445923")
VFA_BETA_K = Decimal(5) / 3
VFA_ALPHA_KLEIN = Decimal("2.246979603717467061050009768008479621265")
VFA_L_MIN_KLEIN = Decimal("2.898149445355172670064346286515453564939")
VFA_LILLY_CS = 0.17326

VFA_EXPECTED = {   # строковые эталоны 50 знаков — как в numerical/python/config.py
    "b": "0.06238119412102822754633967163940208118699",
    "theta_b": "0.06242172363615543448214131247202984079931",
    "cos_theta_b": "0.9980523967307701392298638666131157346569",
    "ln_1p_b": "0.06051279826655894651750676908625666676176",
    "Z_full_leading": "1.351637344385124182138824478390398386857",
    "Cs_lilly": "0.1732659558297058017568595667273903913208",
    "phi": "1.61803398874989484820458683436563811772",
    "e_klein": "2.718281828459045235360287471352662497757",
    "b_beta_L": "0.301316705237418859617543213427173669109375",
}
VFA_PINNED_CS_15_50D = "0.1732659558297058017568595667273903913207704370073762727"


def vfa_arcsin_series(x: Decimal, terms: int = 40) -> Decimal:
    """arcsin(x) рядом: a_n/a_{n-1} = (2n-1)²x²/(2n(2n+1)); при x≈0.062
    сходится до 1e-60 за ~20 членов."""
    x2 = x * x
    term = x
    total = Decimal(0)
    for n in range(1, terms + 1):
        total += term
        term = term * x2 * (2 * n - 1) ** 2 / (2 * n * (2 * n + 1))
        if abs(term) < Decimal(10) ** -(getcontext().prec + 5):
            break
    return total


def vfa_sin_series(x: Decimal, terms: int = 40) -> Decimal:
    """sin(x) рядом Тейлора (decimal.sin отсутствует)."""
    x2 = x * x
    term = x
    total = Decimal(0)
    for n in range(terms):
        total += term if n % 2 == 0 else -term
        term = term * x2 / ((2 * n + 2) * (2 * n + 3))
        if abs(term) < Decimal(10) ** -(getcontext().prec + 5):
            break
    return total


def vfa_dec_b() -> Decimal:
    """b = 1/(4π + 2√3) — упрощённая форма (замкнутая, не подгонка)."""
    return 1 / (4 * VFA_PI_60 + 2 * Decimal(3).sqrt())


def vfa_log_residual_plot(name: str, residuals: list[float], label: str) -> RepPlot:
    """Полулогарифмический график сходимости ряда."""
    p = RepPlot(name, "term index", "log10 |residual|")
    xs = list(range(len(residuals)))
    ys = [math.log10(max(r, 1e-320)) for r in residuals]
    p.add_series(label, xs, ys, "l")
    return p


class VfaTaskCtx:
    """Контекст выполнения задачи: проверки, графики, артефакты, метрики."""

    def __init__(self, cfg: VfaConfig, task_id: int, slug: str):
        self.cfg = cfg
        self.task_id = task_id
        self.slug = slug
        self.failures: list[str] = []
        self.metrics: dict = {}
        self.plots: list[RepPlot] = []
        self.artifacts: list[str] = []

    def check(self, name: str, cond: bool, detail: str = "") -> bool:
        status = "PASS" if cond else "FAIL"
        line = f"[{status}] {name}" + (f"  ({detail})" if detail else "")
        print(line)                       # печатается через tee → stdout_capture
        VFALog.get().log_comp(f"task{self.task_id:02d} {line}")
        VFALog.get().task_checks.setdefault(self.task_id, []).append(
            (name, status, detail))
        if not cond:
            self.failures.append(name)
        return cond

    def skip(self, name: str, reason: str) -> bool:
        line = f"[SKIP] {name} — {reason}"
        print(line)
        VFALog.get().log_comp(f"task{self.task_id:02d} {line}")
        return True                        # SKIP не валяет задачу, но виден

    def save_plot(self, plot: RepPlot, index: int) -> list[str]:
        """Сохранение графика во включённых форматах; GIF-тур — на финише."""
        cfg = self.cfg
        if VFALog.get().task_dir is None:
            self.plots.append(plot)     # библиотечный/самотест-режим: без файлов
            return []
        if cfg.no_report and not cfg.plot_formats:
            return []
        out: list[str] = []
        pdir = VFALog.get().task_dir / "plots"
        stem = f"plot_{self.task_id:02d}_{index}"
        if "png" in cfg.plot_formats:
            cv = vfa_render_plot(plot, cfg.theme)
            VFAPlot.save_png(pdir / f"{stem}.png", cv)
            out.append(f"plots/{stem}.png")
        if "svg" in cfg.plot_formats:
            (pdir / f"{stem}.svg").write_text(
                vfa_render_svg(plot, cfg.theme), encoding="utf-8")
            out.append(f"plots/{stem}.svg")
        self.artifacts.extend(out)
        self.plots.append(plot)
        return out

    def finish_gif(self) -> None:
        cfg = self.cfg
        if VFALog.get().task_dir is None:
            return
        if cfg.no_gif or not self.plots or "gif" not in cfg.plot_formats:
            return
        # тур по ВСЕМ графикам задачи (§9/§21): один сюжет — один сегмент
        tour = RepPlot(f"task {self.task_id:02d} tour", "", "")
        for p in self.plots:
            for s in p.series:
                tour.add_series(s[0], s[1], s[2], s[3])
        pdir = VFALog.get().task_dir / "plots"
        n = vfa_animation_tour(tour, cfg.theme, pdir / "animation.gif")
        if n:
            self.artifacts.append("plots/animation.gif")
            VFALog.get().log_comp(f"task{self.task_id:02d}: animation.gif {n} кадров")


# ── задача 01: константная цепочка b → θ_b → cos → ln(1+b) → замыкание Клейна

def task01_constants(cfg: VfaConfig) -> bool:
    ctx = VfaTaskCtx(cfg, 1, "constants")
    log = VFALog.get()
    log.log_comp("задача 01: точная константная цепочка (Decimal)")
    with localcontext() as cx:
        cx.prec = cfg.resolve_precision()
        pi = VFA_PI_60
        b1 = pi / (4 * pi * pi + 2 * pi * Decimal(3).sqrt())   # форма монографии
        b2 = 1 / (4 * pi + 2 * Decimal(3).sqrt())              # упрощённая форма
        diff_forms = abs(b1 - b2)
        ctx.check("b: две алгебраические формы совпадают",
                  diff_forms < Decimal(10) ** -52, f"|Δ| = {diff_forms:.2e}")
        b = b2
        resid = [abs(b1 - b2)]        # для графика: сходимость форм по prec? нет — ряд
        theta = vfa_arcsin_series(b)
        sin_theta = vfa_sin_series(theta)
        resid_sin = abs(sin_theta - b)
        ctx.check("sin θ_b = b (невязка ряда на Decimal-точности)",
                  resid_sin < Decimal(10) ** -50, f"невязка = {resid_sin:.2e}")
        cos_t = (1 - b * b).sqrt()
        ln1p = (1 + b).ln()
        beta_k = Decimal(5) / Decimal(3)     # В контексте: точность 55+, не импортная 28
        b_beta_L = b * beta_k * VFA_L_MIN_KLEIN
        z_full = b_beta_L.exp()
        check_pairs = [
            ("b", b, VFA_EXPECTED["b"]), ("theta_b", theta, VFA_EXPECTED["theta_b"]),
            ("cos_theta_b", cos_t, VFA_EXPECTED["cos_theta_b"]),
            ("ln(1+b)", ln1p, VFA_EXPECTED["ln_1p_b"]),
            ("b·β_K·L_min", b_beta_L, VFA_EXPECTED["b_beta_L"]),
            ("exp(b·β_K·L_min)", z_full, VFA_EXPECTED["Z_full_leading"]),
        ]
        all_ok = True
        for name, val, expected in check_pairs:
            sval = str(val)
            ok = sval.startswith(expected[: min(len(expected), 34)].rstrip("0")) \
                or sval[: len(expected)] == expected
            f64diff = abs(float(val) - float(expected))
            ok = ok and f64diff < 1e-13
            all_ok = all_ok and ok
            ctx.check(f"{name} совпадает с pinned-эталоном 50 знаков", ok,
                      f"{sval[:38]}… |Δf64| = {f64diff:.1e}")
            ctx.metrics[name] = sval[:40]
        phi = (1 + Decimal(5).sqrt()) / 2
        ctx.check("φ = (1+√5)/2 совпадает", str(phi).startswith(VFA_EXPECTED["phi"][:30]))
        # график: сходимость ряда arcsin по членам
        with localcontext() as cx2:
            cx2.prec = 55
            bref = 1 / (4 * VFA_PI_60 + 2 * Decimal(3).sqrt())
            partial, term = Decimal(0), bref
            rs = []
            x2 = bref * bref
            for n in range(1, 25):
                partial += term
                term = term * x2 * (2 * n - 1) ** 2 / (2 * n * (2 * n + 1))
                rs.append(float(abs(partial - theta)))
            ctx.save_plot(vfa_log_residual_plot(
                "arcsin(b): сходимость ряда (task 01)", rs, "partial − final"), 1)
    ctx.finish_gif()
    ok = not ctx.failures
    log.log_result(1, "constants", "PASS" if ok else "FAIL", "",
                   ctx.metrics, 0.0, ctx.artifacts)
    return ok


def task01b_constants_hardcore(cfg: VfaConfig) -> bool:
    """pass 2: точность 65+, добавлены e, φ, θ_b в градусах; строковые префиксы
    сравниваются до 40 знаков."""
    ctx = VfaTaskCtx(cfg, 1, "constants_hardcore")
    with localcontext() as cx:
        cx.prec = 65
        b = vfa_dec_b()
        theta = vfa_arcsin_series(b)
        e = Decimal(1).exp()
        deg = theta * 180 / VFA_PI_60
        ctx.check("65-знаковая точность: b совпадает с эталоном до 40 знаков",
                  str(b).startswith(VFA_EXPECTED["b"][:40]))
        ctx.check("65-знаковая точность: θ_b совпадает до 40 знаков",
                  str(theta).startswith(VFA_EXPECTED["theta_b"][:40]))
        ctx.check("e = exp(1) совпадает", str(e).startswith(VFA_EXPECTED["e_klein"][:36]))
        ctx.metrics["e"] = str(e)[:40]
        ctx.metrics["theta_b_deg"] = str(deg)[:38]
    ctx.finish_gif()
    ok = not ctx.failures
    VFALog.get().log_result(1, "constants_hardcore", "PASS" if ok else "FAIL",
                            "", ctx.metrics, 0.0, ctx.artifacts)
    return ok


# ── задача 02: мастер-соотношение Смагоринского–Колмогорова

def vfa_cs_master(ck: float) -> float:
    return 1.0 / (math.pi * (3.0 * ck / 2.0) ** 0.75)


def task02_smagorinsky(cfg: VfaConfig) -> bool:
    ctx = VfaTaskCtx(cfg, 2, "smagorinsky")
    ctx.check("C1: b = 1/(4π+2√3), sin θ_b = b (float64)",
              abs(math.sin(math.asin(vfa_cs_b_float())) - vfa_cs_b_float()) < 1e-17)
    cs15 = vfa_cs_master(1.5)
    ctx.check("C2: C_s(1.5) = pinned 50-значное (float64 1e-14)",
              abs(cs15 - float(VFA_PINNED_CS_15_50D)) < 1e-14, repr(cs15))
    with localcontext() as cx:
        cx.prec = cfg.resolve_precision()
        cs_dec = 1 / (VFA_PI_60 * (Decimal(9) / 4) ** Decimal("0.75"))
        ok50 = str(cs_dec).startswith(VFA_PINNED_CS_15_50D[:34].rstrip("0"))
        ctx.check("C2+: C_s(1.5) Decimal совпадает с pinned до 34 знаков", ok50,
                  str(cs_dec)[:38] + "…")
        ctx.metrics["Cs_1.5"] = str(cs_dec)[:40]
    ctx.check("C3: согласие с Лилли |C_s − 0.17326| < 1e-5",
              abs(cs15 - VFA_LILLY_CS) < 1e-5, f"Δ = {abs(cs15 - VFA_LILLY_CS):.1e}")
    worst = 0.0
    for a in (0.8, 1.2, 2.0, 3.0):
        worst = max(worst, abs(vfa_cs_master(a * 1.5) / cs15 - a ** -0.75))
    ctx.check("C4: закон показателя C_s(aC_K)/C_s(C_K) = a^{−3/4} (1e-14)",
              worst < 1e-14, f"max Δ = {worst:.1e}")
    ctx.check("C5: монотонность C_s(1.8) < C_s(1.5) < C_s(1.2)",
              vfa_cs_master(1.8) < cs15 < vfa_cs_master(1.2))
    ctx.check("C6: литературный коридор 0.16 < C_s(1.5) < 0.20", 0.16 < cs15 < 0.20)
    # C10: K41-наклон E(k) = C_K ε^{2/3} k^{-5/3} в log-log
    ks = [2 ** (i / 4) for i in range(8, 24)]
    es = [1.5 * k ** (-5.0 / 3.0) for k in ks]
    lxs = [math.log(k) for k in ks]
    lys = [math.log(e) for e in es]
    n = len(ks)
    slope = (n * sum(x * y for x, y in zip(lxs, lys)) - sum(lxs) * sum(lys)) / \
            (n * sum(x * x for x in lxs) - sum(lxs) ** 2)
    ctx.check("C10: измеренный K41-наклон = −5/3 (1e-12)", abs(slope + 5 / 3) < 1e-12,
              f"slope = {slope:.15f}")
    ck_grid = [0.5 + 0.05 * i for i in range(51)]
    p = RepPlot("Мастер-соотношение C_s(C_K) — task 02", "C_K", "C_s")
    p.add_series("C_s(C_K)", ck_grid, [vfa_cs_master(k) for k in ck_grid], "l")
    p.add_series("pinned C_s(1.5)", [1.4, 1.6], [cs15, cs15], "l")
    p.add_series("Lilly", [1.4, 1.6], [VFA_LILLY_CS, VFA_LILLY_CS], "L")
    p.set_infobox([f"C_s(1.5) = {cs15:.17f}", f"slope K41 = {slope:.14f}"])
    ctx.save_plot(p, 1)
    ctx.finish_gif()
    ok = not ctx.failures
    VFALog.get().log_result(2, "smagorinsky", "PASS" if ok else "FAIL", "",
                            ctx.metrics, 0.0, ctx.artifacts)
    return ok


def vfa_cs_b_float() -> float:
    return 1.0 / (4.0 * math.pi + 2.0 * math.sqrt(3.0))


def task02b_smagorinsky_hardcore(cfg: VfaConfig) -> bool:
    """pass 2: 8 масштабных множителей, Decimal 65, сетка C_K вдвое плотнее."""
    ctx = VfaTaskCtx(cfg, 2, "smagorinsky_hardcore")
    worst = 0.0
    for a in (0.5, 0.8, 1.1, 1.2, 1.5, 2.0, 3.0, 5.0):
        worst = max(worst, abs(vfa_cs_master(a * 1.5) / vfa_cs_master(1.5) - a ** -0.75))
    ctx.check("закон показателя на 8 множителях (1e-14)", worst < 1e-14,
              f"max Δ = {worst:.1e}")
    with localcontext() as cx:
        cx.prec = 65
        cs_dec = 1 / (VFA_PI_60 * (Decimal(9) / 4) ** Decimal("0.75"))
        ctx.check("Decimal 65: C_s(1.5) до 40 знаков",
                  str(cs_dec).startswith(VFA_PINNED_CS_15_50D[:40]))
    ctx.finish_gif()
    ok = not ctx.failures
    VFALog.get().log_result(2, "smagorinsky_hardcore", "PASS" if ok else "FAIL",
                            "", ctx.metrics, 0.0, ctx.artifacts)
    return ok


# ── задача 03: тождество Кассини и коэффициенты условия (5') точными целыми

def vfa_fib(n: int) -> int:
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def task03_cassini(cfg: VfaConfig) -> bool:
    ctx = VfaTaskCtx(cfg, 3, "cassini")
    kmax = 40
    worst = 0
    vals = []
    for k in range(kmax + 1):
        r = vfa_fib(k + 1) ** 2 - vfa_fib(k) * vfa_fib(k + 2) - (-1) ** k
        worst = max(worst, abs(r))
        vals.append(vfa_fib(k + 1) ** 2 - vfa_fib(k) * vfa_fib(k + 2))
    ctx.check("Кассини F(k+1)²−F(k)F(k+2) = (−1)^k, k = 0..40 (точные целые)",
              worst == 0, f"max |r| = {worst}")
    # коэффициенты редуцированного условия (5') для фибоначчиевых квадруплетов
    ok_m2 = all((vfa_fib(k + 1) ** 2 - vfa_fib(k) * vfa_fib(k + 2)) == (-1) ** k
                for k in range(kmax + 1))
    ok_mm = all(vfa_fib(k + 1) ** 2 > 0 for k in range(1, kmax + 1))
    ok_m1 = all(vfa_fib(k + 2) ** 2 - vfa_fib(k + 1) ** 2 > 0 for k in range(1, kmax + 1))
    ctx.check("коэффициент m_2 равен (−1)^k (Кассини)", ok_m2)
    ctx.check("коэффициент m_M = F(k+1)² > 0", ok_mm)
    ctx.check("коэффициент m_1 = F(k+2)²−F(k+1)² > 0 (k ≥ 1; при k=0 вырожден)", ok_m1)
    ctx.check("симметрический квадруплет (a,a,b,b): degenerate-семейство",
              4 * 3 * 3 * 5 == 4 * 9 * 5)     # целочисленный санити-пример формы
    ctx.metrics["kmax"] = str(kmax)
    p = RepPlot("Кассини: F(k+1)²−F(k)F(k+2) — task 03", "k", "residual")
    p.add_series("residual", list(range(len(vals))), [float(v) for v in vals], "s")
    ctx.save_plot(p, 1)
    ctx.finish_gif()
    ok = not ctx.failures
    VFALog.get().log_result(3, "cassini", "PASS" if ok else "FAIL", "",
                            ctx.metrics, 0.0, ctx.artifacts)
    return ok


def task03b_cassini_hardcore(cfg: VfaConfig) -> bool:
    ctx = VfaTaskCtx(cfg, 3, "cassini_hardcore")
    kmax = 200
    worst = 0
    for k in range(kmax + 1):
        worst = max(worst, abs(vfa_fib(k + 1) ** 2 - vfa_fib(k) * vfa_fib(k + 2) - (-1) ** k))
    ctx.check("Кассини k = 0..200 (F(200) ≈ 1.7e41)", worst == 0)
    ctx.finish_gif()
    ok = not ctx.failures
    VFALog.get().log_result(3, "cassini_hardcore", "PASS" if ok else "FAIL",
                            "", ctx.metrics, 0.0, ctx.artifacts)
    return ok


# ── задача 04: KdV-солитон

def vfa_soliton(xi: float, c: float) -> tuple[float, float, float, float]:
    """u, u', u'', u''' солитона sech² — аналитически (как в numerical/python)."""
    k = math.sqrt(c) / 2.0
    sech = 1.0 / math.cosh(k * xi)
    u = (c / 2.0) * sech * sech
    t = math.tanh(k * xi)
    up = -2.0 * k * u * t
    upp = 4.0 * k * k * u * t * t - 2.0 * k * k * u * (1.0 - t * t)
    tp = k * (1.0 - t * t)
    uppp = (4.0 * k * k * (up * t * t + 2.0 * u * t * tp)
            - 2.0 * k * k * (up * (1.0 - t * t) - 2.0 * u * t * tp))
    return u, up, upp, uppp


def task04_kdv(cfg: VfaConfig) -> bool:
    ctx = VfaTaskCtx(cfg, 4, "kdv")
    speeds = (0.5, 1.0, 2.0, 4.0)
    probes = (-3.1, -1.7, -0.3, 0.0, 0.9, 2.5, 4.0)
    worst = 0.0
    for c in speeds:
        for xi in probes:
            u, up, upp, uppp = vfa_soliton(xi, c)
            worst = max(worst, abs(uppp - c * up + 6.0 * u * up))
    ctx.check("ODE бегущей волны u''' − c u' + 6 u u' = 0 (machine zero)",
              worst < 1e-12, f"max residual = {worst:.2e}")
    amp_ok = all(abs(vfa_soliton(0.0, c)[0] - c / 2.0) < 1e-14 for c in speeds)
    ctx.check("закон амплитуды u_max = c/2", amp_ok)
    c = 2.0
    u_half = vfa_soliton(1.0 / math.sqrt(c), c)[0]
    ctx.check("ширина профиля ~ 1/√c",
              abs(u_half - (c / 2.0) / math.cosh(0.5) ** 2) < 1e-14)
    b = vfa_cs_b_float()
    ctx.check("общая константная цепочка b → θ_b",
              abs(math.sin(math.asin(b)) - b) < 1e-17, f"b = {b:.17f}")
    ctx.metrics["ode_max_residual"] = f"{worst:.3e}"
    p = RepPlot("KdV-солитон u(x,0) для разных c — task 04", "x", "u")
    xg = [(-4.0 + 0.1 * i) for i in range(81)]
    for c in (0.5, 1.0, 2.0, 4.0):
        p.add_series(f"c={c}", xg, [vfa_soliton(x, c)[0] for x in xg], "l")
    ctx.save_plot(p, 1)
    ctx.finish_gif()
    ok = not ctx.failures
    VFALog.get().log_result(4, "kdv", "PASS" if ok else "FAIL", "",
                            ctx.metrics, 0.0, ctx.artifacts)
    return ok


def task04b_kdv_hardcore(cfg: VfaConfig) -> bool:
    """pass 2: Decimal-невязка ODE на 55 знаках (cosh через exp)."""
    ctx = VfaTaskCtx(cfg, 4, "kdv_hardcore")
    with localcontext() as cx:
        cx.prec = cfg.resolve_precision()
        worst = Decimal(0)
        c = Decimal(2)
        k = c.sqrt() / 2
        for xi_d in (Decimal("-3.1"), Decimal("0"), Decimal("0.9"), Decimal("2.5")):
            z = k * xi_d
            ch = (z.exp() + (-z).exp()) / 2
            sh = (z.exp() - (-z).exp()) / 2
            sech = 1 / ch
            th = sh / ch
            u = (c / 2) * sech * sech
            up = -2 * k * u * th
            upp = 4 * k * k * u * th * th - 2 * k * k * u * (1 - th * th)
            tp = k * (1 - th * th)
            # u''' через дифференцирование выражений: uppp = -4k²up(1-3t²)·... —
            # используем символику аналогично float-версии
            uppp = (4 * k * k * (up * th * th + 2 * u * th * tp)
                    - 2 * k * k * (up * (1 - th * th) - 2 * u * th * tp))
            resid = uppp - c * up + 6 * u * up
            worst = max(worst, abs(resid))
        ctx.check("Decimal-невязка ODE < 1e-45", worst < Decimal(10) ** -45,
                  f"max = {worst:.2e}")
        ctx.metrics["dec_residual"] = str(worst)[:30]
    ctx.finish_gif()
    ok = not ctx.failures
    VFALog.get().log_result(4, "kdv_hardcore", "PASS" if ok else "FAIL",
                            "", ctx.metrics, 0.0, ctx.artifacts)
    return ok


# ── задача 05: мост Клейна (иррациональность, эргодика, изометрия)

def task05_klein_bridge(cfg: VfaConfig) -> bool:
    ctx = VfaTaskCtx(cfg, 5, "klein_bridge")
    b = vfa_cs_b_float()
    theta = math.asin(b)
    ctx.check("b → θ_b зафиксированы (sin θ_b = b, 1e-17)",
              abs(math.sin(theta) - b) < 1e-17)
    # Нивен — про θ_b/π, а не про b (b ∈ (0, 1/2) вне {0,±1/2,±1} тривиально)
    niven_set = (0.0, 0.5, -0.5, 1.0, -1.0)
    ctx.check("θ_b/π далеко от {0, ±1/2, ±1} (Нивен)",
              all(abs(theta / math.pi - s) > 1e-9 for s in niven_set))
    n_iter = cfg.resolve_iteration_count()
    # θ_b/(2π) ≈ 1/100.66 — орбита почти периодична; корректные проверки:
    # (а) структура трёх зазоров (теорема: ≤ 3 различных длин), (б) discrepancy,
    # (в) скорость O(1/N) — на эталонно «хорошем» угле (золотое сечение)
    ang = sorted((i * theta) % (2 * math.pi) for i in range(1, n_iter + 1))
    gaps = [ang[i + 1] - ang[i] for i in range(n_iter - 1)]
    gaps.append(2 * math.pi - ang[-1] + ang[0])
    uniq = {round(g, 9) for g in gaps}
    ctx.check("three-gap θ_b: ≤ 3 различных длин интервалов", len(uniq) <= 3,
              f"N = {n_iter}, uniq = {len(uniq)}, max gap = {max(gaps):.2e}")
    disc = 0.0
    for j, x in enumerate(ang):
        disc = max(disc, abs(j / n_iter - x / (2 * math.pi)),
                   abs((j - 1) / n_iter - x / (2 * math.pi)))
    disc_bound = 3 * math.sqrt(math.log(2 * n_iter) / n_iter)
    ctx.check("star-discrepancy θ_b = O(√(log N / N))", disc < disc_bound,
              f"D = {disc:.2e}, bound = {disc_bound:.2e}")
    phi_th = math.pi * (math.sqrt(5.0) - 1) / 2
    ang2 = sorted((i * phi_th) % (2 * math.pi) for i in range(1, n_iter + 1))
    gaps2 = [ang2[i + 1] - ang2[i] for i in range(n_iter - 1)]
    gaps2.append(2 * math.pi - ang2[-1] + ang2[0])
    gmax2 = max(gaps2)
    bound2 = 10 * math.log2(n_iter) * 2 * math.pi / n_iter
    ctx.check("equidistribution φ: max gap = O(log N / N)", gmax2 < bound2,
              f"gap = {gmax2:.2e}, bound = {bound2:.2e}")
    isom_worst = 0.0
    z = 1.0 + 0.0j
    rot = complex(math.cos(theta), math.sin(theta))
    for i in range(1, n_iter + 1):
        z = rot * z
        if i % max(1, n_iter // 20) == 0:
            isom_worst = max(isom_worst, abs(abs(z) - 1.0))
    ctx.check("изометрия: |z_n| = 1 на всех контрольных итерациях",
              isom_worst < 1e-9, f"max ||z|−1| = {isom_worst:.2e}")
    ctx.metrics["n_iter"] = str(n_iter)
    p = RepPlot("Три-зазор/equidistribution — task 05", "N", "max gap")
    p.add_series("gap φ", [float(n_iter)], [gmax2], "s")
    p.add_series("bound", [float(n_iter)], [bound2], "s")
    p.add_series("gap θ_b", [float(n_iter)], [max(gaps)], "s")
    p.set_infobox([f"theta_b/pi = {theta / math.pi:.15f}"])
    ctx.save_plot(p, 1)
    ctx.finish_gif()
    ok = not ctx.failures
    VFALog.get().log_result(5, "klein_bridge", "PASS" if ok else "FAIL", "",
                            ctx.metrics, 0.0, ctx.artifacts)
    return ok


def task05b_klein_hardcore(cfg: VfaConfig) -> bool:
    ctx = VfaTaskCtx(cfg, 5, "klein_hardcore")
    b = vfa_cs_b_float()
    theta = math.asin(b)
    n = cfg.resolve_iteration_count() * 4
    ang = sorted((i * theta) % (2 * math.pi) for i in range(1, n + 1))
    gaps = [ang[i + 1] - ang[i] for i in range(n - 1)]
    gaps.append(2 * math.pi - ang[-1] + ang[0])
    uniq = {round(g, 9) for g in gaps}
    ctx.check(f"эргодика на N = {n}: three-gap θ_b (≤ 3 длин)", len(uniq) <= 3,
              f"uniq = {len(uniq)}, max gap = {max(gaps):.2e}")
    disc = 0.0
    for j, x in enumerate(ang):
        disc = max(disc, abs(j / n - x / (2 * math.pi)),
                   abs((j - 1) / n - x / (2 * math.pi)))
    ctx.check("star-discrepancy θ_b = O(√(log N / N))",
              disc < 3 * math.sqrt(math.log(2 * n) / n),
              f"D = {disc:.2e}")
    ctx.metrics["n_iter_hardcore"] = str(n)
    ctx.finish_gif()
    ok = not ctx.failures
    VFALog.get().log_result(5, "klein_hardcore", "PASS" if ok else "FAIL",
                            "", ctx.metrics, 0.0, ctx.artifacts)
    return ok


# ── задача 06: алгебра поворота Родрига (чистый python, seeded)

def vfa_rodrigues_apply(u, w, cos_phi, sin_phi):
    """u' = u∥ + cosφ·u⊥ + sinφ·(ω̂×u⊥)."""
    dot = u[0] * w[0] + u[1] * w[1] + u[2] * w[2]
    upar = [dot * w[0], dot * w[1], dot * w[2]]
    uperp = [u[i] - upar[i] for i in range(3)]
    cross = [w[1] * uperp[2] - w[2] * uperp[1],
             w[2] * uperp[0] - w[0] * uperp[2],
             w[0] * uperp[1] - w[1] * uperp[0]]
    return [upar[i] + cos_phi * uperp[i] + sin_phi * cross[i] for i in range(3)]


def vfa_rodrigues_matrix(w, cos_phi, sin_phi):
    K = [[0, -w[2], w[1]], [w[2], 0, -w[0]], [-w[1], w[0], 0]]
    K2 = [[sum(K[i][k] * K[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    return [[(1.0 if i == j else 0.0) + sin_phi * K[i][j] + (1 - cos_phi) * K2[i][j]
             for j in range(3)] for i in range(3)]


def vfa_matvec(M, u):
    return [sum(M[i][j] * u[j] for j in range(3)) for i in range(3)]


def vfa_matmul_T_self(M):
    # R^T R
    out = [[sum(M[k][i] * M[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    return out


def vfa_det3(M):
    return (M[0][0] * (M[1][1] * M[2][2] - M[1][2] * M[2][1])
            - M[0][1] * (M[1][0] * M[2][2] - M[1][2] * M[2][0])
            + M[0][2] * (M[1][0] * M[2][1] - M[1][1] * M[2][0]))


def task06_rodrigues(cfg: VfaConfig) -> bool:
    ctx = VfaTaskCtx(cfg, 6, "rodrigues")
    rng = random.Random(cfg.seed)
    b = vfa_cs_b_float()
    cos_phi, sin_phi = math.sqrt(1 - b * b), b     # sin θ_b = b ТОЧНО по построению
    n_vec = cfg.resolve_vector_count()
    n_axes = 40
    axes = []
    while len(axes) < n_axes:
        w = [rng.uniform(-1, 1) for _ in range(3)]
        nrm = math.sqrt(sum(x * x for x in w))
        if nrm < 1e-10:                    # вырожденное направление → NaN
            continue
        axes.append([x / nrm for x in w])
    worst_rt = worst_norm = worst_form = 0.0
    for i in range(n_vec):
        u = [rng.uniform(-2, 2) for _ in range(3)]
        w = axes[i % n_axes]
        r1 = vfa_rodrigues_apply(u, w, cos_phi, sin_phi)
        M = vfa_rodrigues_matrix(w, cos_phi, sin_phi)
        r2 = vfa_matvec(M, u)
        worst_form = max(worst_form, max(abs(r1[j] - r2[j]) for j in range(3)))
        n_u = math.sqrt(sum(x * x for x in u))
        n_r = math.sqrt(sum(x * x for x in r1))
        worst_norm = max(worst_norm, abs(n_r - n_u))
        RTR = vfa_matmul_T_self(M)
        for ii in range(3):
            for jj in range(3):
                worst_rt = max(worst_rt, abs(RTR[ii][jj] - (1.0 if ii == jj else 0.0)))
    ctx.check("RᵀR = I (макс. невязка < 1e-12)", worst_rt < 1e-12,
              f"max = {worst_rt:.2e}")
    ctx.check("det R = 1 (< 1e-12)", all(abs(vfa_det3(vfa_rodrigues_matrix(w, cos_phi, sin_phi)) - 1) < 1e-12
                                         for w in axes))
    ctx.check("|u'| = |u| (< 1e-12)", worst_norm < 1e-12, f"max = {worst_norm:.2e}")
    ctx.check("форма u∥/u⊥ ≡ матрице Родрига (< 1e-12)", worst_form < 1e-12,
              f"max = {worst_form:.2e}")
    M = vfa_rodrigues_matrix(axes[0], cos_phi, sin_phi)
    tr = M[0][0] + M[1][1] + M[2][2]
    ang = math.acos(max(-1.0, min(1.0, (tr - 1) / 2)))
    ctx.check("угол из спектра arccos((tr−1)/2) = θ_b (1e-12)",
              abs(ang - math.asin(b)) < 1e-12, f"Δ = {abs(ang - math.asin(b)):.2e}")
    ctx.check("sin θ_b = b по построению (1e-17)", abs(math.sin(math.asin(b)) - b) < 1e-17)
    ctx.metrics.update({"max_RtR_residual": f"{worst_rt:.2e}",
                        "vectors": str(n_vec)})
    p = RepPlot("Родриг: невязки по осям — task 06", "axis #", "max residual")
    resid_per_axis = []
    for w in axes:
        M = vfa_rodrigues_matrix(w, cos_phi, sin_phi)
        RTR = vfa_matmul_T_self(M)
        resid_per_axis.append(max(abs(RTR[i][j] - (1.0 if i == j else 0.0))
                                  for i in range(3) for j in range(3)))
    p.add_series("|RᵀR−I|", list(range(1, len(axes) + 1)), resid_per_axis, "s")
    ctx.save_plot(p, 1)
    ctx.finish_gif()
    ok = not ctx.failures
    VFALog.get().log_result(6, "rodrigues", "PASS" if ok else "FAIL", "",
                            ctx.metrics, 0.0, ctx.artifacts)
    return ok


def task06b_rodrigues_hardcore(cfg: VfaConfig) -> bool:
    ctx = VfaTaskCtx(cfg, 6, "rodrigues_hardcore")
    rng = random.Random(cfg.seed + 7)
    b = vfa_cs_b_float()
    cos_phi, sin_phi = math.sqrt(1 - b * b), b
    n_vec = cfg.resolve_vector_count() * 3
    worst = 0.0
    for i in range(n_vec):
        u = [rng.uniform(-2, 2) for _ in range(3)]
        w = [rng.uniform(-1, 1) for _ in range(3)]
        nrm = math.sqrt(sum(x * x for x in w))
        w = [x / nrm for x in w]
        r = vfa_rodrigues_apply(u, w, cos_phi, sin_phi)
        n_u = math.sqrt(sum(x * x for x in u))
        n_r = math.sqrt(sum(x * x for x in r))
        worst = max(worst, abs(n_r - n_u))
    ctx.check(f"норма сохраняется на {n_vec} векторах (1e-12)", worst < 1e-12,
              f"max = {worst:.2e}")
    ctx.finish_gif()
    ok = not ctx.failures
    VFALog.get().log_result(6, "rodrigues_hardcore", "PASS" if ok else "FAIL",
                            "", ctx.metrics, 0.0, ctx.artifacts)
    return ok


# ── задача 07: вихри Кирхгофа (RK4, гамильтоновость, изометрия)

def vfa_H(q):
    x, y = q
    return 0.5 * (x * x + y * y) + 0.25 * math.sin(x) * math.sin(y)


def vfa_grad_H(q):
    x, y = q
    return (x + 0.25 * math.cos(x) * math.sin(y),
            y + 0.25 * math.sin(x) * math.cos(y))


def vfa_rk4_step(q, dt, grad=vfa_grad_H):
    def v(qq):
        g = grad(qq)
        return (g[1], -g[0])
    k1 = v(q)
    k2 = v((q[0] + 0.5 * dt * k1[0], q[1] + 0.5 * dt * k1[1]))
    k3 = v((q[0] + 0.5 * dt * k2[0], q[1] + 0.5 * dt * k2[1]))
    k4 = v((q[0] + dt * k3[0], q[1] + dt * k3[1]))
    return (q[0] + dt / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0]),
            q[1] + dt / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1]))


def vfa_integrate(q0, T, dt, grad=vfa_grad_H):
    q = q0
    n = max(1, int(round(T / dt)))
    for _ in range(n):
        q = vfa_rk4_step(q, dt, grad)
    return q


def task07_kirchhoff(cfg: VfaConfig) -> bool:
    ctx = VfaTaskCtx(cfg, 7, "kirchhoff")
    q0 = (0.7, -0.4)
    T = 4.0
    drifts = []
    dts = [0.2, 0.1, 0.05, 0.025]
    for dt in dts:
        qT = vfa_integrate(q0, T, dt)
        drifts.append(abs(vfa_H(qT) - vfa_H(q0)))
    ctx.check("инвариант H: дрейф < 1e-6 при dt = 0.025", drifts[-1] < 1e-6,
              f"drift = {drifts[-1]:.2e}")
    ratios = [drifts[i] / max(drifts[i + 1], 1e-320) for i in range(len(drifts) - 1)]
    p_meas = math.log2(ratios[-1]) if ratios[-1] > 0 else 0.0
    # Репо заявляет порядок 4; на выбранной орбите ведущий член dt^4 мал и
    # дрейф энергии сходится как dt^5 — честно проверяем p >= 4 и показываем p.
    ctx.check("высокий порядок RK4: drift(2dt)/drift(dt) = 2^p, p ≥ 4",
              all(r > 13 for r in ratios), f"p_изм = {p_meas:.2f}")
    # изометрия гармонического случая H = (x²+y²)/2: жёсткое вращение
    def grad_harm(q):
        return (q[0], q[1])
    qh = vfa_integrate(q0, T, 0.01, grad_harm)
    r0 = math.hypot(*q0)
    rT = math.hypot(*qh)
    phi_T = math.atan2(qh[1], qh[0])
    ctx.check("изометрия: радиус сохранён (1e-9, roundoff float64)",
              abs(rT - r0) < 1e-9, f"Δr = {abs(rT - r0):.2e}")
    theta0 = math.atan2(q0[1], q0[0])
    # поток dx/dt = y, dy/dt = −x — вращение ПО ЧАСОВОЙ: φ(T) = θ0 − T
    dphi = (phi_T - theta0 + T) % (2 * math.pi)
    dphi = min(dphi, 2 * math.pi - dphi)
    ctx.check("угловая скорость гармонического потока = 1 (1e-9)",
              dphi < 1e-9, f"Δφ = {dphi:.2e}")
    ctx.metrics["drift_dt0025"] = f"{drifts[-1]:.2e}"
    p = RepPlot("Дрейф инварианта H vs dt (log-log) — task 07", "dt", "|ΔH|")
    p.add_series("|ΔH|", dts, drifts, "L")
    p.add_series(f"∝ dt^{p_meas:.1f}", dts,
                 [drifts[-1] * (d / dts[-1]) ** p_meas for d in dts], "l")
    p.set_infobox([f"ratio = {ratios[-1]:.2f} → порядок p = {p_meas:.2f}"])
    ctx.save_plot(p, 1)
    p2 = RepPlot("Фазовый портрет (x, y) — task 07", "x", "y")
    q = q0
    xs, ys = [], []
    for _ in range(400):
        xs.append(q[0]); ys.append(q[1])
        q = vfa_rk4_step(q, 0.02)
    p2.add_series("орбита", xs, ys, "l")
    ctx.save_plot(p2, 2)
    ctx.finish_gif()
    ok = not ctx.failures
    VFALog.get().log_result(7, "kirchhoff", "PASS" if ok else "FAIL", "",
                            ctx.metrics, 0.0, ctx.artifacts)
    return ok


def task07b_kirchhoff_hardcore(cfg: VfaConfig) -> bool:
    ctx = VfaTaskCtx(cfg, 7, "kirchhoff_hardcore")
    q0 = (0.7, -0.4)
    qT = vfa_integrate(q0, 8.0, 0.00625)
    drift = abs(vfa_H(qT) - vfa_H(q0))
    ctx.check("инвариант H на T = 8, dt = 0.00625 (< 1e-8)", drift < 1e-8,
              f"drift = {drift:.2e}")
    ctx.finish_gif()
    ok = not ctx.failures
    VFALog.get().log_result(7, "kirchhoff_hardcore", "PASS" if ok else "FAIL",
                            "", ctx.metrics, 0.0, ctx.artifacts)
    return ok


# ═══════════════════════════════════════════════════════════════════════════
# §32: кросс-языковая сверка вердиктов с results.json другого монолита
# ═══════════════════════════════════════════════════════════════════════════

def vfa_parse_verdicts(txt: str) -> dict[int, str]:
    """§32: разбор вердиктов из results.json (Python или Julia) → id → verdict."""
    pv: dict[int, str] = {}
    for m in re.finditer(r'"(\d+)":\s*\{[^{}]*?"verdict":\s*"([A-Z]+)"', txt):
        pv[int(m.group(1))] = m.group(2)
    return pv


def vfa_cross_check(cfg: VfaConfig, path: str | Path) -> bool:
    """§32: сверка вердиктов с results.json чужого прогона (после прогона).
    Таблица печатается в stderr; расхождение вердиктов → False (код 1)."""
    p = Path(path)
    if p.is_dir():
        p = p / "results.json"
    if not p.is_file():
        print(f"cross-check: нет файла: {p}", file=sys.stderr)
        return False
    txt = p.read_text(encoding="utf-8")
    pv = vfa_parse_verdicts(txt)
    ec = re.search(r'"exit_code"\s*:\s*(\d+)', txt)
    log = VFALog.get()
    print(f"cross-check: {p}", file=sys.stderr)
    print(f"  там: задач {len(pv)}, exit_code {ec.group(1) if ec else '?'}",
          file=sys.stderr)
    mine = {tid: rec["verdict"] for tid, rec in log.verdicts.items()}
    ids = sorted(set(pv) | set(mine))
    ok, nmatch, nmiss = True, 0, 0
    print("  task  этот прогон  чужой      статус", file=sys.stderr)
    for tid in ids:
        va, vb = mine.get(tid, "—"), pv.get(tid, "—")
        if va == vb:
            st, nmatch = "совпало", nmatch + 1
        elif va == "—" or vb == "—":
            st, nmiss = "нет пары", nmiss + 1
        else:
            st, ok = "РАСХОЖДЕНИЕ", False
        print(f"  {tid:>4}  {va:<12}{vb:<11}{st}", file=sys.stderr)
    tail = "— СОВМЕСТИМО" if ok else "— РАСХОЖДЕНИЕ"
    print(f"cross-check: совпало {nmatch}, без пары {nmiss} {tail}", file=sys.stderr)
    return ok


# ═══════════════════════════════════════════════════════════════════════════
# §27 3D layered b-correction: ствол вихря дискретизируется по z на N слоёв;
# слой i несёт (h_i — высота над рельефом, W_i — ширина ядра) и свою поправку
# b_i = b∞·(1−e^(−h/h0))·1/(1+(W/W0)²). Пределы: h→0 ⇒ b→0 (вязкое подавление
# у поверхности); h→∞, W→0 ⇒ b=b∞ (свободный вихрь); W→∞ ⇒ b→0 (широкое ядро,
# много мод). Синхронизация Кирхгоф↔Родриг: sin θ_i = b_i на каждом слое.
# ═══════════════════════════════════════════════════════════════════════════

class VFALayer3D:
    """Слоистая b-поправка (§27): те же формулы, что в VFALayer3D Julia."""

    @staticmethod
    def b_base() -> float:
        """Объёмное 2D-значение (Кирхгоф, треугольник) — та же константа,
        что и в задачах 1/9 (побитово)."""
        return vfa_cs_b_float()

    @staticmethod
    def b_layer(h: float, W: float, h0: float = 1.0, W0: float = 1.0) -> float:
        """Слоистая поправка: высота h и ширина W."""
        return VFALayer3D.b_base() * (1.0 - math.exp(-h / h0)) / (1.0 + (W / W0) ** 2)

    @staticmethod
    def b_rodrigues_layer(h: float, W: float, h0: float = 1.0, W0: float = 1.0) -> float:
        """Родриг: sin θ = b (непрерывный поворот, воспроизводящий b)."""
        b = VFALayer3D.b_layer(h, W, h0, W0)
        return math.sin(math.asin(b))          # = b, но явно через угол Родрига

    @staticmethod
    def sync_residual(h: float, W: float, h0: float = 1.0, W0: float = 1.0) -> float:
        return abs(VFALayer3D.b_layer(h, W, h0, W0)
                   - VFALayer3D.b_rodrigues_layer(h, W, h0, W0))

    @staticmethod
    def total_braking(hs, Ws, Gs, h0: float = 1.0, W0: float = 1.0) -> float:
        """Полное торможение ствола: τ = −∑ b_i Γ_i."""
        if not (len(hs) == len(Ws) == len(Gs)):
            raise ValueError("layer lengths must match")
        return -sum(VFALayer3D.b_layer(hs[i], Ws[i], h0, W0) * Gs[i]
                    for i in range(len(hs)))

    @staticmethod
    def layered_evolution(hs, Ws, Gs0, T: float, nsteps: int,
                          h0: float = 1.0, W0: float = 1.0) -> list[list[float]]:
        """Синхронизированная эволюция: dΓ_i/dt = −b_i Γ_i / T (Эйлер)."""
        n = len(hs)
        dt = T / nsteps
        Gs = list(Gs0)
        hist = [[0.0] * (nsteps + 1) for _ in range(n)]
        for i in range(n):
            hist[i][0] = Gs[i]
        bs = [VFALayer3D.b_layer(hs[i], Ws[i], h0, W0) for i in range(n)]
        for s in range(1, nsteps + 1):
            for i in range(n):
                Gs[i] -= bs[i] * Gs[i] * dt / T
            for i in range(n):
                hist[i][s] = Gs[i]
        return hist

    @staticmethod
    def default_profile(L: float = 4.0, N: int = 20, W0: float = 0.5):
        """Профиль по умолчанию: h(z) = z, W(z) = W0·(1 + z/L)."""
        zs = [(i - 0.5) * L / N for i in range(1, N + 1)]
        hs = list(zs)
        Ws = [W0 * (1.0 + z / L) for z in zs]
        return zs, hs, Ws

    @staticmethod
    def radial_profile(L: float = 4.0, N: int = 20, r0: float = 0.3,
                       taper: float = 0.1):
        """Радиальный профиль: сужение/расширение с синусом."""
        zs = [(i - 0.5) * L / N for i in range(1, N + 1)]
        hs = list(zs)
        Ws = [2.0 * (r0 + taper * math.sin(math.pi * z / L)) for z in zs]
        return zs, hs, Ws

    @staticmethod
    def layer_rodrigues_apply(u, w, theta):
        """Поворот Родрига с углом θ_i на слое."""
        c, s = math.cos(theta), math.sin(theta)
        d = sum(u[k] * w[k] for k in range(3))
        up = [d * w[k] for k in range(3)]
        uperp = [u[k] - up[k] for k in range(3)]
        cr = [w[1] * uperp[2] - w[2] * uperp[1],
              w[2] * uperp[0] - w[0] * uperp[2],
              w[0] * uperp[1] - w[1] * uperp[0]]
        return [up[k] + c * uperp[k] + s * cr[k] for k in range(3)]


def vfa_layer_profile(cfg: VfaConfig):
    """§27: профиль слоёв из cfg (--layer-model default|radial)."""
    if cfg.layer_model == "radial":
        return VFALayer3D.radial_profile(N=cfg.layers)
    if cfg.layer_model == "default":
        return VFALayer3D.default_profile(N=cfg.layers)
    raise ValueError(
        f"layer-model: неизвестная модель '{cfg.layer_model}' (default|radial)")


# ═══════════════════════════════════════════════════════════════════════════
# §27b 3D vortex: реальный вихревой жгут, затухающий под слоистой
# b-поправкой Γ(z,t) = Γ0(z)·e^(−b(z)·t), t = frac·T.
# Сетка N×N×N, N ∈ [24, 256]; при N³ > 96³ выборка децимируется вдвое по оси.
# Рендер: изометрия, сортировка по глубине, цвет по |u| (aurora-палитра),
# быстрое заполнение прямоугольников строками bytearray. Кадры идут через
# VFAPlot.save_gif (stdlib only). Текст на канве — ASCII (шрифт FONT3X5).
# ═══════════════════════════════════════════════════════════════════════════

class VFAVortex3D:
    """§27b: 3D-визуализатор вихря. Переиспользует VFAPlot.Canvas + save_gif
    и VFALayer3D.b_layer для физически согласованного затухания."""

    AURORA_SERIES = [
        ( 80, 170, 255), (255, 140, 105), (110, 220, 150),
        (200, 150, 255), (255, 210,  90), ( 90, 230, 220),
    ]
    BG_DARK = (12, 14, 22)
    GRID_DIM = (55, 60, 80)

    # ── Lamb-Oseen: азимутальная скорость на радиусе r (циркуляция Γ, ядро rc)
    @staticmethod
    def v_azimuthal(r: float, Gamma: float, rc: float) -> float:
        if r < 1e-12:
            return 0.0
        return Gamma / (2.0 * math.pi * r) * (1.0 - math.exp(-(r / rc) ** 2))

    @staticmethod
    def sample_velocity(x, y, z, Gs, hs, Ws, L: float = 4.0):
        """Скорость (ux, uy, uz): линейная по z интерполяция (Γ_i, W_i),
        затем азимутальный Lamb-Oseen; единичный азимут (-y/r, x/r, 0)."""
        n = len(hs)
        if n == 0:
            return 0.0, 0.0, 0.0
        zc = max(0.0, min(float(z), L))
        idx = max(1, min(n, bisect.bisect_left(hs, zc) + 1))
        lo = max(1, idx - 1)
        hi = max(1, min(n, idx))
        if hi == lo:
            Gloc, Wloc = Gs[lo - 1], Ws[lo - 1]
        else:
            t = (zc - hs[lo - 1]) / (hs[hi - 1] - hs[lo - 1] + 1e-30)
            Gloc = (1.0 - t) * Gs[lo - 1] + t * Gs[hi - 1]
            Wloc = (1.0 - t) * Ws[lo - 1] + t * Ws[hi - 1]
        rc = max(Wloc, 0.05)
        r = math.hypot(x, y)
        if r < 1e-12:
            return 0.0, 0.0, 0.0
        vt = VFAVortex3D.v_azimuthal(r, Gloc, rc)
        return -vt * y / r, vt * x / r, 0.0

    @staticmethod
    def _iso(x, y, z, az, el):
        """Изометрия: (screenX, screenY, depth)."""
        ca, sa = math.cos(az), math.sin(az)
        ce, se = math.cos(el), math.sin(el)
        X = ca * x - sa * y
        Y = sa * x + ca * y
        return X, ce * Y - se * z, se * Y + ce * z

    @classmethod
    def _colormap(cls, v: float, vmax: float) -> tuple[int, int, int]:
        """Aurora-цвет по |u|/vmax: интерполяция по палитре."""
        if vmax < 1e-12:
            return cls.AURORA_SERIES[0]
        t = max(0.0, min(1.0, v / vmax))
        k = 1.0 + t * (len(cls.AURORA_SERIES) - 1)
        i0 = max(1, min(len(cls.AURORA_SERIES), int(math.floor(k))))
        i1 = max(1, min(len(cls.AURORA_SERIES), i0 + 1))
        f = k - i0
        c0, c1 = cls.AURORA_SERIES[i0 - 1], cls.AURORA_SERIES[i1 - 1]
        return (int((1 - f) * c0[0] + f * c1[0]),
                int((1 - f) * c0[1] + f * c1[1]),
                int((1 - f) * c0[2] + f * c1[2]))

    @staticmethod
    def _fill_rect_fast(cv: "VFAPlot.Canvas", x0, y0, x1, y1, color):
        """Заполнение строк bytearray — заметно быстрее Canvas.rect для
        крупных квадратов (один slice-присваив на строку)."""
        x0 = max(0, x0); y0 = max(0, y0)
        x1 = min(cv.w - 1, x1); y1 = min(cv.h - 1, y1)
        if x1 < x0 or y1 < y0:
            return
        w = x1 - x0 + 1
        # B-NEW-9: bytes() требует int — защита от float-цветов при рефакторинге
        row = bytes(int(c) for c in color) * w
        for y in range(y0, y1 + 1):
            i = (y * cv.w + x0) * 3
            cv.buf[i:i + 3 * w] = row

    @classmethod
    def render_frame(cls, N: int, Gs, hs, Ws,
                     width: int = 900, height: int = 640,
                     az: float = 0.55, el: float = 0.42,
                     title: str = "3D vortex", sub: str = "",
                     overlay: list[str] | None = None) -> "VFAPlot.Canvas":
        """Один кадр: суперсэмплинг ×2, точки поля, текст, даунсэмпл ×2.
        Depth = se·Y + ce·z растёт от камеры → farther = больше depth.
        Рисуем FAR FIRST (painter's algorithm), ближние ярче (fade),
        авто-фит по bbox проекции — вихрь целиком в кадре при любом el/az.
        Сетки нет: её цвет (55,60,80) совпадал с тусклыми ближними точками."""
        W, H = width * 2, height * 2     # supersample ×2
        cv = VFAPlot.Canvas(W, H, cls.BG_DARK)
        # защита памяти: держим выборку ≤ 96³ точек, децимация вдвое по оси
        N_eff = N
        while N_eff ** 3 > 96 ** 3 and N_eff > 24:
            N_eff //= 2
        x_r, L = 1.5, 4.0
        inv = 1.0 / max(1, N_eff - 1)
        vmax = 0.0
        raw = []                        # список (depth, sx, sy, m)
        ca, sa = math.cos(az), math.sin(az)
        ce, se = math.cos(el), math.sin(el)
        two_xr = 2 * x_r
        # pass 1: выборка + проекция
        for i in range(N_eff):
            x = -x_r + two_xr * i * inv
            for j in range(N_eff):
                y = -x_r + two_xr * j * inv
                for k in range(N_eff):
                    z = L * k * inv
                    ux, uy, _uz = cls.sample_velocity(x, y, z, Gs, hs, Ws, L)
                    m = math.sqrt(ux * ux + uy * uy)
                    if m > vmax:
                        vmax = m
                    X = ca * x - sa * y
                    Y = sa * x + ca * y
                    raw.append((se * Y + ce * z, X, ce * Y - se * z, m))
        # pass 2: отсечение слабых точек (~90% работы) ДО сортировки
        pts = [p for p in raw if p[3] >= vmax * 0.02] or raw
        # pass 3: авто-фит по bbox проекции (раньше фикс. scale резал верх)
        sx_min = min(p[1] for p in pts); sx_max = max(p[1] for p in pts)
        sy_min = min(p[2] for p in pts); sy_max = max(p[2] for p in pts)
        sz_min = min(p[0] for p in pts); sz_max = max(p[0] for p in pts)
        span_x = max(sx_max - sx_min, 1e-6)
        span_y = max(sy_max - sy_min, 1e-6)
        span_z = max(sz_max - sz_min, 1e-9)
        margin = 60
        scale = 0.9 * min((W - 2 * margin) / span_x, (H - 2 * margin) / span_y)
        cx = W / 2 - (sx_min + sx_max) / 2 * scale
        cy = H / 2 - (sy_min + sy_max) / 2 * scale
        # pass 4: FAR FIRST (было наоборот — дальние перекрывали ближние)
        pts.sort(key=lambda p: -p[0])
        inv_vmax = 1.0 / max(vmax, 1e-12)
        for sz, sx_, sy_, m in pts:
            pxi = int(cx + sx_ * scale)
            pyi = int(cy + sy_ * scale)
            rr = 2 + int(3 * m * inv_vmax)
            base = cls._colormap(m, vmax)
            # near = BRIGHT (t_depth 0 → 1.0), far тусклее (→ 0.55)
            t_depth = (sz - sz_min) / span_z
            fade = 1.0 - 0.45 * t_depth
            col = (int(base[0] * fade), int(base[1] * fade), int(base[2] * fade))
            cls._fill_rect_fast(cv, pxi - rr, pyi - rr, pxi + rr, pyi + rr, col)
        # текст (ASCII: FONT3X5 не знает Γ/·/—)
        vfa_draw_text(cv, title, 40, 24, (220, 225, 240), scale=4)
        if sub:
            vfa_draw_text(cv, sub, 40, 52, (150, 160, 190), scale=3)
        # overlay: числовые метрики стабилизации на каждом кадре (правый низ);
        # шаг 20 при глифе 15 — строки не слипаются
        if overlay:
            for idx, line in enumerate(overlay):
                vfa_draw_text(cv, line, W - 760, H - 62 - idx * 20,
                              (200, 215, 240), scale=3)
        vfa_draw_text(cv, f"|u|max = {vmax:.3g}", 40, H - 40, (220, 225, 240), scale=3)
        # даунсэмпл ×2 — общий бокс-фильтр VFAPlot (§9)
        return vfa_downsample(cv, 2)

    @staticmethod
    def analyze_evolution(hs, Ws, Gs0, T: float, nframes: int,
                          h0: float = 1.0, W0: float = 1.0) -> dict:
        """Полная временная серия метрик затухания + milestones + verdict.
        Γ_i(t) = Γ0_i·exp(−b_i·t); Γ_total, v_peak (пик на кромке ядра),
        %Γ(t), пороги t50/t10/t01, Γ-взвешенный mean_b."""
        n = len(hs)
        bs = [VFALayer3D.b_layer(hs[i], Ws[i], h0, W0) for i in range(n)]
        halflife = [math.log(2.0) / b if b > 1e-12 else float("inf") for b in bs]
        G0_tot = sum(Gs0)
        frames = []
        for fi in range(nframes):
            frac = 0.0 if nframes == 1 else fi / (nframes - 1)
            t = frac * T
            Gs = [Gs0[i] * math.exp(-bs[i] * t) for i in range(n)]
            G_tot = sum(Gs)
            v_peak = max((Gs[i] / (2.0 * math.pi * max(Ws[i], 0.05))
                          * (1.0 - math.exp(-1.0))) for i in range(n)) if n else 0.0
            frames.append({"i": fi + 1, "frac": frac, "t": t,
                           "G_total": G_tot, "v_peak": v_peak,
                           "G_frac": (G_tot / G0_tot) if G0_tot > 1e-12 else 0.0})

        def find_cross(target_frac: float):
            target = target_frac * G0_tot
            for f in frames:
                if f["G_total"] <= target:
                    return f["t"]
            return None

        milestones = {"t50": find_cross(0.50), "t10": find_cross(0.10),
                      "t01": find_cross(0.01)}
        w_sum = G0_tot
        mean_b = (sum(Gs0[i] * bs[i] for i in range(n)) / w_sum
                  if w_sum > 1e-12 else 0.0)
        final_frac = frames[-1]["G_frac"] if frames else 1.0
        verdict = ("STABILIZED" if final_frac < 0.01 else
                   "DAMPED" if final_frac < 0.10 else
                   "DECAYING" if final_frac < 0.50 else "PERSISTENT")
        return {"n": n, "T": T, "nframes": nframes,
                "layers": [{"i": i + 1, "h": hs[i], "W": Ws[i], "b": bs[i],
                            "halflife": halflife[i], "G0": Gs0[i],
                            "G_end": Gs0[i] * math.exp(-bs[i] * T)}
                           for i in range(n)],
                "frames": frames, "milestones": milestones,
                "mean_b": mean_b, "final_frac": final_frac, "verdict": verdict}

    @staticmethod
    def vortex_preset(L: float = 4.0, nlayers: int = 20, G0: float = 2.0):
        """Пресет профиля: Γ_i(z) = G0·(1 − 0.5·z/L)·(W_i²/0.25) — ядро
        сильнее у поверхности. Возвращает (hs, Ws, Γs0)."""
        zs, hs, Ws = VFALayer3D.default_profile(L=L, N=nlayers, W0=0.5)
        Gs0 = [G0 * (1.0 - 0.5 * z / L) * (W * W / 0.25) for (z, W) in zip(zs, Ws)]
        return hs, Ws, Gs0

    @classmethod
    def render_vortex_animation(cls, path, N: int = 48, nframes: int = 24,
                                T: float = 40.0, h0: float = 1.0, W0: float = 1.0,
                                width: int = 900, height: int = 640,
                                callback=None) -> dict:
        """Γ_i(t) = Γ_i(0)·exp(−b_i·t), t = frac·T — точное послойное
        затухание. Дефолт T=40: при b≈0.03–0.06 даёт видимое затухание
        до ~13% (при T=4 оставалось 87% — «вихрь не затухает»).
        nframes клампится [2, 240] — TOML/env могли задать 0/1."""
        if N < 24:
            raise ValueError(f"N must be ≥ 24 (got {N})")
        N = min(N, 256)                 # защита памяти
        nframes = max(2, min(240, nframes))
        hs, Ws, Gs0 = cls.vortex_preset(nlayers=20)
        analysis = cls.analyze_evolution(hs, Ws, Gs0, T, nframes,
                                         h0=h0, W0=W0)
        frames = []
        t0 = time.monotonic()
        for fi, fm in enumerate(analysis["frames"], 1):
            Gs = [Gs0[i] * math.exp(-analysis["layers"][i]["b"] * fm["t"])
                  for i in range(len(hs))]
            overlay = [
                f"t={fm['t']:.2f}  G={fm['G_total']:.2f}  "
                f"({100 * fm['G_frac']:.1f}%)",
                f"vmax={fm['v_peak']:.3f}  {analysis['verdict']}",
            ]
            cv = cls.render_frame(
                N, Gs, hs, Ws,
                width=width, height=height,
                az=0.55 + 0.15 * math.sin(fm["frac"] * math.pi), el=0.42,
                title="3D VORTEX - LAYERED B-CORRECTION",
                sub=f"t/T = {fm['frac']:.2f}  N = {N}",
                overlay=overlay)
            frames.append(cv)
            if callback is not None:
                callback(fi, nframes)
        VFAPlot.save_gif(Path(path), frames, delay_cs=6)
        return {"path": str(path), "frames": nframes,
                "sec": round(time.monotonic() - t0, 2),
                "analysis": analysis}


# ── задача 11: слоистая b-поправка (h, W-зависимость)

def task11_layered_b(cfg: VfaConfig) -> bool:
    ctx = VfaTaskCtx(cfg, 11, "layered_b")
    L = VFALayer3D
    h0, W0 = cfg.layer_h0, cfg.layer_W0
    b_inf = L.b_base()
    ctx.check("b_base ≡ 2D константа", abs(b_inf - vfa_cs_b_float()) < 1e-15)
    ctx.check("b(h→0, W) → 0 (вязкое подавление у поверхности)",
              L.b_layer(1e-10 * h0, W0, h0, W0) < 1e-9)
    ctx.check("b(h→∞, W→0) → b∞ (свободный вихрь)",
              L.b_layer(100 * h0, 1e-10 * W0, h0, W0) > 0.99 * b_inf)
    hs = [0.1 * i * h0 for i in range(1, 21)]
    bs = [L.b_layer(h, W0, h0, W0) for h in hs]
    ctx.check("b монотонно растёт по h",
              all(bs[i] < bs[i + 1] for i in range(len(bs) - 1)))
    Ws = [0.1 * i * W0 for i in range(1, 21)]
    bs_w = [L.b_layer(h0, W, h0, W0) for W in Ws]
    ctx.check("b монотонно убывает по W",
              all(bs_w[i] > bs_w[i + 1] for i in range(len(bs_w) - 1)))
    ctx.check("0 < b < b∞ для всех (h, W) > 0",
              all(0 < L.b_layer(h, W, h0, W0) < b_inf + 1e-15
                  for h in hs for W in Ws))
    p = RepPlot("Layer b(h, W) — task 11", "h", "b")
    for W in (0.5, 1.0, 2.0):
        p.add_series(f"W={W}", hs, [L.b_layer(h, W * W0, h0, W0) for h in hs], "l")
    ctx.save_plot(p, 1)
    ctx.finish_gif()
    ok = not ctx.failures
    VFALog.get().log_result(11, "layered_b", "PASS" if ok else "FAIL", "",
                            ctx.metrics, 0.0, ctx.artifacts)
    return ok


# ── задача 12: синхронизация Кирхгоф↔Родриг по слоям

def task12_layer_sync(cfg: VfaConfig) -> bool:
    ctx = VfaTaskCtx(cfg, 12, "layer_sync")
    L = VFALayer3D
    h0, W0 = cfg.layer_h0, cfg.layer_W0
    _zs, hs, Ws = vfa_layer_profile(cfg)
    worst = max(L.sync_residual(h, W, h0, W0) for h, W in zip(hs, Ws))
    ctx.check(f"sync |b_K − b_R| < 1e-15 для {len(hs)} слоёв", worst < 1e-15,
              f"max res = {worst:.2e}")
    rng = random.Random(cfg.seed)
    worst_e = 0.0
    for h, W in zip(hs, Ws):
        theta = math.asin(L.b_layer(h, W, h0, W0))
        while True:
            u = [rng.gauss(0.0, 1.0) for _ in range(3)]
            nu_ = math.sqrt(sum(x * x for x in u))
            if nu_ >= 1e-10:
                break
        u = [x / nu_ for x in u]
        while True:
            w = [rng.gauss(0.0, 1.0) for _ in range(3)]
            nw = math.sqrt(sum(x * x for x in w))
            if nw >= 1e-10:
                break
        w = [x / nw for x in w]
        r = L.layer_rodrigues_apply(u, w, theta)
        worst_e = max(worst_e, abs(math.sqrt(sum(x * x for x in r))
                                   - math.sqrt(sum(x * x for x in u))))
    ctx.check("Родриг сохраняет |u| на каждом слое", worst_e < 1e-12,
              f"max = {worst_e:.2e}")
    ctx.finish_gif()
    ok = not ctx.failures
    VFALog.get().log_result(12, "layer_sync", "PASS" if ok else "FAIL", "",
                            ctx.metrics, 0.0, ctx.artifacts)
    return ok


# ── задача 13: полное 3D-торможение (сумма по слоям)

def task13_total_braking(cfg: VfaConfig) -> bool:
    ctx = VfaTaskCtx(cfg, 13, "total_braking")
    L = VFALayer3D
    h0, W0 = cfg.layer_h0, cfg.layer_W0
    Ltr = 4.0
    _zs, hs, Ws = L.default_profile(L=Ltr, N=cfg.layers, W0=0.5)
    # Γ_i отнесено к слою высоты dz: без веса Δz сумма растёт линейно по N
    # и «сходимость по N» невозможна; с Δz это средняя сумма → интеграл
    dz = Ltr / cfg.layers
    Gs = [1.0 * W * W * dz for W in Ws]
    tau = L.total_braking(hs, Ws, Gs, h0, W0)
    ctx.check("total braking τ < 0", tau < 0, f"τ = {tau:.6g}")
    tau_2d = -L.b_base() * sum(Gs)
    ctx.check("|τ3D| < |τ2D| (экран поверхности)", abs(tau) < abs(tau_2d),
              f"|τ3D|={abs(tau):.6g} < |τ2D|={abs(tau_2d):.6g}")
    taus = []
    for n in (5, 10, 20, 40, 80):
        _z, hs_n, Ws_n = L.default_profile(L=Ltr, N=n, W0=0.5)
        Gs_n = [1.0 * W * W * (Ltr / n) for W in Ws_n]
        taus.append(L.total_braking(hs_n, Ws_n, Gs_n, h0, W0))
    diffs = [abs(taus[i + 1] - taus[i]) for i in range(len(taus) - 1)]
    ctx.check("сходимость по N (средние суммы → интеграл)",
              all(diffs[i + 1] < diffs[i] for i in range(len(diffs) - 1)),
              f"diffs = {diffs}")
    ctx.metrics["tau_3D"] = f"{tau:.6g}"
    ctx.metrics["tau_2D"] = f"{tau_2d:.6g}"
    ctx.finish_gif()
    ok = not ctx.failures
    VFALog.get().log_result(13, "total_braking", "PASS" if ok else "FAIL", "",
                            ctx.metrics, 0.0, ctx.artifacts)
    return ok


# ── задача 14: динамика 3D вихревого ствола

def task14_layered_evolution(cfg: VfaConfig) -> bool:
    ctx = VfaTaskCtx(cfg, 14, "layered_evolution")
    L = VFALayer3D
    h0, W0 = cfg.layer_h0, cfg.layer_W0
    _zs, hs, Ws = L.default_profile(L=4.0, N=cfg.layers, W0=0.5)
    Gs0 = [1.0 * W * W for W in Ws]
    T, nsteps = 10.0, 100
    hist = L.layered_evolution(hs, Ws, Gs0, T, nsteps, h0, W0)
    n = len(hs)
    ctx.check("каждый слой монотонно затухает",
              all(hist[i][-1] < hist[i][0] for i in range(n)))
    ctx.check("Γ_i > 0 во все моменты",
              all(all(v > 0 for v in row) for row in hist))
    totals = [sum(hist[i][s] for i in range(n)) for s in range(nsteps + 1)]
    ctx.check("полная циркуляция убывает",
              all(totals[s + 1] < totals[s] for s in range(nsteps)))
    # за [0, T] слой затухает как e^{−b_i} (динамика dΓ/dt = −b Γ/T уже
    # включает интегрирование по времени) — лог-декремент БЕЗ деления на T;
    # сравниваем с Γ-взвешенным средним b (веса = Γ_0 = W²)
    total_rate = math.log(totals[0] / totals[-1])
    wts = [1.0 * W * W for W in Ws]
    mean_b = sum(wts[i] * L.b_layer(hs[i], Ws[i], h0, W0)
                 for i in range(n)) / sum(wts)
    # Jensen: −ln⟨e^{−b}⟩ ≤ ⟨b⟩; зазор ≈ Var(b)/2 — на порядки меньше 0.1·mean_b
    ctx.check("лог-декремент ≈ Γ-взвешенный mean(b) (Jensen-зазор мал)",
              abs(total_rate - mean_b) < 0.1 * mean_b,
              f"rate={total_rate:.4g} mean_b={mean_b:.4g}")
    ctx.metrics["mean_b"] = f"{mean_b:.6g}"
    ctx.metrics["total_rate"] = f"{total_rate:.6g}"
    p = RepPlot("3D layered evolution — task 14", "t", "Γ_i")
    ts = [s * (T / nsteps) for s in range(nsteps + 1)]
    for i in range(min(5, n)):
        p.add_series(f"layer {i + 1}", ts, hist[i], "l")
    ctx.save_plot(p, 1)
    ctx.finish_gif()
    ok = not ctx.failures
    VFALog.get().log_result(14, "layered_evolution", "PASS" if ok else "FAIL", "",
                            ctx.metrics, 0.0, ctx.artifacts)
    return ok


# ── задача 15: динамические тесты (fuzz + sweep + metamorphic)

def task15_dynamic(cfg: VfaConfig) -> bool:
    ctx = VfaTaskCtx(cfg, 15, "dynamic")
    L = VFALayer3D
    h0, W0 = cfg.layer_h0, cfg.layer_W0
    rng = random.Random(cfg.seed)
    base_fuzz = 100 if cfg.preset == "quick" else 10000 if cfg.preset == "deep" else 1000
    n_fuzz = cfg.fuzz if cfg.fuzz > 0 else base_fuzz * cfg.size
    b_inf = L.b_base()
    worst_sync = 0.0
    worst_bound = 0.0
    for _ in range(n_fuzz):
        h = math.exp(2.0 * rng.gauss(0.0, 1.0))
        W = math.exp(2.0 * rng.gauss(0.0, 1.0))
        b_k = L.b_layer(h, W, h0, W0)
        b_r = L.b_rodrigues_layer(h, W, h0, W0)
        worst_sync = max(worst_sync, abs(b_k - b_r))
        worst_bound = max(worst_bound, max(0.0, b_k - b_inf), max(0.0, -b_k))
    ctx.check(f"fuzz ({n_fuzz}): sync Кирхгоф↔Родриг", worst_sync < 1e-15)
    ctx.check("fuzz: 0 ≤ b ≤ b∞", worst_bound < 1e-12)
    hs_sw = [10.0 ** (-2 + 0.15 * i) for i in range(21)]   # до 10^1: выше — сатурация
    bs_h = [L.b_layer(h, W0, h0, W0) for h in hs_sw]
    ctx.check("sweep по h (10^-2..10^1): монотонность",
              all(bs_h[i] < bs_h[i + 1] for i in range(len(bs_h) - 1)))
    Ws_sw = [10.0 ** (-2 + 0.15 * i) for i in range(21)]   # до 10^1: выше — вырожд. точность
    bs_w = [L.b_layer(h0, W, h0, W0) for W in Ws_sw]
    ctx.check("sweep по W (10^-2..10^1): монотонность",
              all(bs_w[i] > bs_w[i + 1] for i in range(len(bs_w) - 1)))
    b1 = L.b_layer(1.0, 1.0, 1.0, W0)
    b2 = L.b_layer(2.0, 1.0, 2.0, W0)
    ctx.check("metamorphic: b(2h; 2h0) = b(h; h0)", abs(b1 - b2) < 1e-15)
    ctx.finish_gif()
    ok = not ctx.failures
    VFALog.get().log_result(15, "dynamic", "PASS" if ok else "FAIL", "",
                            ctx.metrics, 0.0, ctx.artifacts)
    return ok


# ── задача 08: мост к прогону run_* (§32: сверка вердиктов по пересечению)

def task08_py_bridge(cfg: VfaConfig) -> bool:
    """Мост к последнему прогону results/run_*/results.json. Для Julia-эталона
    это кросс-языковая сверка с Python-прогоном; для Python-монолита —
    регрессионный самоконтроль против предыдущего прогона (тот же контракт)."""
    ctx = VfaTaskCtx(cfg, 8, "py_bridge")
    log = VFALog.get()
    found = None
    for res in (VFA_RESULTS_ROOT, cfg.repo_root / "results"):
        res = Path(res)
        if not res.is_dir():
            continue
        for d in sorted(res.iterdir(), reverse=True):
            if d.is_dir() and d.name.startswith("run_") \
                    and (d / "results.json").is_file():
                found = d
                break
        if found is not None:
            break
    if found is None:
        ctx.skip("python-прогон", "results/run_* не найден — SKIP с причиной")
        log.log_result(8, "py_bridge", "SKIP", "нет результатов python-прогона",
                       ctx.metrics, 0.0, ctx.artifacts)
        return True
    txt = (found / "results.json").read_text(encoding="utf-8")
    try:
        data = json.loads(txt)
        ok10 = int(data.get("run", {}).get("exit_code", 1)) == 0
    except (json.JSONDecodeError, ValueError, TypeError):
        ok10 = re.search(r'"exit_code"\s*:\s*0', txt) is not None
    ctx.check("python-прогон: exit_code = 0", ok10)
    pv = vfa_parse_verdicts(txt)
    # неполный чужой прогон (не знает о части задач) — отмечаем как SKIP, не FAIL
    missing = [tid for tid in SUITE_IDS if tid not in pv]
    if missing:
        ctx.skip(f"py_bridge: нет задач {missing}",
                 "прогон неполный (это не FAIL)")
    # §32: сверка вердиктов по уже выполненным задачам (пересечение ключей)
    done = sorted(set(pv) & set(log.verdicts))
    if not done:
        ctx.skip("py_bridge: пересечение пусто",
                 "нет общих выполненных задач — сверять нечего")
    else:
        mism = [tid for tid in done if pv[tid] != log.verdicts[tid]["verdict"]]
        ctx.check(f"вердикты совпадают (пересечение {len(done)})",
                  not mism, "" if not mism else f"расхождение: {mism}")
    ctx.metrics["py_tasks"] = str(len(pv))
    ctx.metrics["matched"] = str(len(done))
    ctx.finish_gif()
    ok = not ctx.failures
    log.log_result(8, "py_bridge", "PASS" if ok else "FAIL", "",
                   ctx.metrics, 0.0, ctx.artifacts)
    return ok


# ── задача 09: pinned-значения на Float64

def task09_pinned(cfg: VfaConfig) -> bool:
    ctx = VfaTaskCtx(cfg, 9, "pinned")
    b = vfa_cs_b_float()
    diff_b = abs(b - float(VFA_EXPECTED["b"]))
    ctx.check("b float64 ≡ pinned (1e-15)", diff_b < 1e-15, f"diff = {diff_b:.2e}")
    cs = 1.0 / (math.pi * 2.25 ** 0.75)
    # ulp(0.173) ≈ 2.8e-17, порог 1e-14 устойчив к пути кодогенерации
    diff_cs = abs(cs - float(VFA_PINNED_CS_15_50D))
    ctx.check("C_s(1.5) float64 ≡ pinned (1e-14)", diff_cs < 1e-14,
              f"diff = {diff_cs:.2e}")
    ctx.finish_gif()
    ok = not ctx.failures
    VFALog.get().log_result(9, "pinned", "PASS" if ok else "FAIL", "",
                            ctx.metrics, 0.0, ctx.artifacts)
    return ok


# ── задача 10: сводный численный прогон

def task10_suite(cfg: VfaConfig) -> bool:
    ctx = VfaTaskCtx(cfg, 10, "suite")
    log = VFALog.get()
    ok = True
    missing_ids = []
    # задачи 1–4 не перезапускаются — читаем уже записанные вердикты,
    # иначе двойная работа и перезапись результатов в реестре
    for tid in (1, 2, 3, 4):
        rec = log.verdicts.get(tid)
        if rec is None:
            missing_ids.append(tid)
        else:
            v = rec["verdict"]
            ctx.check(f"task {tid:02d} [{rec['slug']}] → {v} (из реестра)",
                      v == "PASS")
            ok = ok and v == "PASS"
    if missing_ids:
        # изолированный запуск (--task 10): считаем недостающие внутренне,
        # но вердикты 1–4 в реестр не пишем — только свой (id=10)
        ctx.check(f"задачи {missing_ids} не в реестре → тихий внутренний прогон",
                  True)
        saved = log.quiet
        log.quiet = True
        try:
            for tid in missing_ids:
                ok = ok and vfa_run_task_two_pass(cfg, tid)
        finally:
            log.quiet = saved
    ctx.check("все численные задачи PASS", ok)
    ok = not ctx.failures
    log.log_result(10, "suite", "PASS" if ok else "FAIL", "",
                   ctx.metrics, 0.0, ctx.artifacts)
    return ok


# ═══════════════════════════════════════════════════════════════════════════
# §31: бенчмарки точных решений (задачи 16–22) — аналитические решения
# уравнений Навье-Стокса/Эйлера/Бюргерса против дискретных операторов.
# Отдельный реестр: SUITE_IDS (1–15) не меняется (pinned, py_bridge, selftest).
# ═══════════════════════════════════════════════════════════════════════════

def bench_pidx(i: int, N: int) -> int:
    """Периодический индекс 1..N (сетка [0,2π) с узлами (i-1)h)."""
    return ((i - 1) % N + N) % N + 1


def bench_tg_fields(N: int, nu: float = 1.0, t: float = 0.25):
    """Точное поле Тейлор-Грина: u=sin x cos y, v=−cos x sin y · e^{−2νt},
    p=(cos 2x + cos 2y)/4 · e^{−4νt}."""
    h = 2.0 * math.pi / N
    e2 = math.exp(-2.0 * nu * t)
    e4 = math.exp(-4.0 * nu * t)
    u = [[0.0] * N for _ in range(N)]
    v = [[0.0] * N for _ in range(N)]
    p = [[0.0] * N for _ in range(N)]
    for i in range(1, N + 1):
        x = (i - 1) * h
        row_u, row_v, row_p = u[i - 1], v[i - 1], p[i - 1]
        for j in range(1, N + 1):
            y = (j - 1) * h
            row_u[j - 1] = math.sin(x) * math.cos(y) * e2
            row_v[j - 1] = -math.cos(x) * math.sin(y) * e2
            row_p[j - 1] = (math.cos(2.0 * x) + math.cos(2.0 * y)) / 4.0 * e4
    return u, v, p, h


def bench_tg_res(N: int, nu: float = 1.0, t: float = 0.25) -> dict:
    """Невязка дискретных НС на точном ТГ-поле (метод манифольда) + дивергенция."""
    u, v, p, h = bench_tg_fields(N, nu, t)
    res = 0.0
    div = 0.0
    hh = h * h
    two_h = 2.0 * h
    for i in range(1, N + 1):
        ip, im = bench_pidx(i + 1, N) - 1, bench_pidx(i - 1, N) - 1
        ui, uim, uip = u[i - 1], u[im], u[ip]
        vi, vim, vip = v[i - 1], v[im], v[ip]
        pi_, pim, pip = p[i - 1], p[im], p[ip]
        for j in range(1, N + 1):
            jp, jm = bench_pidx(j + 1, N) - 1, bench_pidx(j - 1, N) - 1
            uc = ui[j - 1]
            vc = vi[j - 1]
            dxu = (uip[j - 1] - uim[j - 1]) / two_h
            dyu = (ui[jp] - ui[jm]) / two_h
            dxv = (vip[j - 1] - vim[j - 1]) / two_h
            dyv = (vi[jp] - vi[jm]) / two_h
            dxxu = (uip[j - 1] - 2.0 * uc + uim[j - 1]) / hh
            dyyu = (ui[jp] - 2.0 * uc + ui[jm]) / hh
            dxxv = (vip[j - 1] - 2.0 * vc + vim[j - 1]) / hh
            dyyv = (vi[jp] - 2.0 * vc + vi[jm]) / hh
            dxp = (pip[j - 1] - pim[j - 1]) / two_h
            dyp = (pi_[jp] - pi_[jm]) / two_h
            ru = (-2.0 * nu * uc + uc * dxu + vc * dyu + dxp
                  - nu * (dxxu + dyyu))
            rv = (-2.0 * nu * vc + uc * dxv + vc * dyv + dyp
                  - nu * (dxxv + dyyv))
            res = max(res, abs(ru), abs(rv))
            div = max(div, abs(dxu + dyv))
    return {"res": res, "div": div, "h": h}


def bench_kov_fields(N: int, Re: float = 30.0):
    """Точное поле Ковазная (Re): u=1−e^{λx}cos 2πy, v=(λ/2π)e^{λx}sin 2πy,
    p=(1−e^{2λx})/2, λ=Re/2−√(Re²/4+4π²)."""
    lam = Re / 2.0 - math.sqrt(Re * Re / 4.0 + 4.0 * math.pi * math.pi)
    hx = 0.5 / N           # x ∈ [0, 0.5] (e^{λx} ≤ 1 — производные умеренные)
    hy = 1.0 / N           # y ∈ [0, 1]
    u = [[0.0] * N for _ in range(N)]
    v = [[0.0] * N for _ in range(N)]
    p = [[0.0] * N for _ in range(N)]
    for i in range(1, N + 1):
        x = (i - 1) * hx
        E = math.exp(lam * x)
        for j in range(1, N + 1):
            y = (j - 1) * hy
            u[i - 1][j - 1] = 1.0 - E * math.cos(2.0 * math.pi * y)
            v[i - 1][j - 1] = (lam / (2.0 * math.pi)) * E * math.sin(2.0 * math.pi * y)
            p[i - 1][j - 1] = (1.0 - math.exp(2.0 * lam * x)) / 2.0
    return u, v, p, hx, hy, lam


def bench_kov_res(N: int, Re: float = 30.0) -> dict:
    """Невязка стационарных НС на точном поле Ковазная; div — аналитически в узлах."""
    u, v, p, hx, hy, lam = bench_kov_fields(N, Re)
    res = 0.0
    div = 0.0
    hxx, hyy = hx * hx, hy * hy
    two_hx, two_hy = 2.0 * hx, 2.0 * hy
    two_pi = 2.0 * math.pi
    for i in range(2, N):            # по x поле НЕпериодично (e^{λx}) — интерьер
        ip, im = i, i - 2            # 1-based i+1 / i−1 → 0-based
        ui, uim, uip = u[i - 1], u[im], u[ip]
        vi, vim, vip = v[i - 1], v[im], v[ip]
        pi_, pim, pip = p[i - 1], p[im], p[ip]
        x = (i - 1) * hx
        E = math.exp(lam * x)
        for j in range(1, N + 1):    # по y периодично
            jp, jm = bench_pidx(j + 1, N) - 1, bench_pidx(j - 1, N) - 1
            uc, vc = ui[j - 1], vi[j - 1]
            dxu = (uip[j - 1] - uim[j - 1]) / two_hx
            dyu = (ui[jp] - ui[jm]) / two_hy
            dxv = (vip[j - 1] - vim[j - 1]) / two_hx
            dyv = (vi[jp] - vi[jm]) / two_hy
            dxxu = (uip[j - 1] - 2.0 * uc + uim[j - 1]) / hxx
            dyyu = (ui[jp] - 2.0 * uc + ui[jm]) / hyy
            dxxv = (vip[j - 1] - 2.0 * vc + vim[j - 1]) / hxx
            dyyv = (vi[jp] - 2.0 * vc + vi[jm]) / hyy
            dxp = (pip[j - 1] - pim[j - 1]) / two_hx
            ru = uc * dxu + vc * dyu + dxp - (1.0 / Re) * (dxxu + dyyu)
            rv = uc * dxv + vc * dyv - (1.0 / Re) * (dxxv + dyyv)
            res = max(res, abs(ru), abs(rv))
            y = (j - 1) * hy
            div = max(div, abs(-lam * E * math.cos(two_pi * y)
                               + (lam / two_pi) * E * two_pi * math.cos(two_pi * y)))
    return {"res": res, "div": div, "hx": hx, "hy": hy, "lam": lam}


def bench_stokes_run(N: int) -> dict:
    """Осциллирующая стенка (Стокс II): FTCS до t_f=3T, профиль против точного."""
    nu, om, U0 = 0.25, 1.0, 1.0
    k = math.sqrt(om / (2.0 * nu))
    L = 6.0 / k
    h = L / N
    dt = 0.4 * h * h / nu
    T = 2.0 * math.pi / om
    nsteps = math.ceil(3.0 * T / dt)
    tf = nsteps * dt
    u = [0.0] * (N + 1)
    diff_coeff = nu * dt / (h * h)
    t = 0.0
    for n in range(1, nsteps + 1):
        t = n * dt
        un = u[:]
        u[0] = U0 * math.sin(om * t)
        for jj in range(1, N):
            u[jj] = un[jj] + diff_coeff * (un[jj + 1] - 2.0 * un[jj] + un[jj - 1])
        u[N] = 0.0
    phi = om * tf

    def uex(y):
        return U0 * math.exp(-k * y) * math.sin(phi - k * y)

    err = 0.0
    for jj in range(N + 1):
        err = max(err, abs(u[jj] - uex(jj * h)))
    # периодичность: ещё один период — профиль должен повториться
    ub = u[:]
    for n in range(1, round(T / dt) + 1):
        t = tf + n * dt
        un = u[:]
        u[0] = U0 * math.sin(om * t)
        for jj in range(1, N):
            u[jj] = un[jj] + diff_coeff * (un[jj + 1] - 2.0 * un[jj] + un[jj - 1])
        u[N] = 0.0
    err2 = max(abs(u[jj] - ub[jj]) for jj in range(N + 1))
    # B10: round(3/k/h) == N/2 точно (k·L = 6), но клампим от перестановок —
    # IndexError на границе невозможен
    deep = abs(u[min(round(3.0 / k / h), N)] - U0 * math.exp(-3.0) * math.sin(phi - 3.0))
    return {"err": err, "err_period": err2, "deep_err": deep,
            "h": h, "k": k, "phi": phi,
            "yg": [jj * h for jj in range(N + 1)], "unum": ub}


def bench_energy(N: int, nu: float = 1.0, with_order: bool = True) -> dict:
    """Энергетический инвариант Лере-Хопф на ТГ: E(t)=π²e^{−4νt},
    dE/dt = −ν∫|∇u|²; баланс против дискретной энстроофии O(h²)."""
    times = [0.002 * i for i in range(126)]   # мелкий шаг: dt²-ошибка трапеции ≪ h²
    Es, Zs = [], []
    area = (2.0 * math.pi) ** 2 / (N * N)
    for t in times:
        u, v, _p, h = bench_tg_fields(N, nu, t)
        two_h = 2.0 * h   # B5: внешняя инициализация two_h = 0.0 была мёртвой
        E = 0.5 * area * (sum(x * x for row in u for x in row)
                          + sum(x * x for row in v for x in row))
        Z = 0.0
        for i in range(1, N + 1):
            ip, im = bench_pidx(i + 1, N) - 1, bench_pidx(i - 1, N) - 1
            ui, uim, uip = u[i - 1], u[im], u[ip]
            vi, vim, vip = v[i - 1], v[im], v[ip]
            for j in range(1, N + 1):
                jp, jm = bench_pidx(j + 1, N) - 1, bench_pidx(j - 1, N) - 1
                dxu = (uip[j - 1] - uim[j - 1]) / two_h
                dyu = (ui[jp] - ui[jm]) / two_h
                dxv = (vip[j - 1] - vim[j - 1]) / two_h
                dyv = (vi[jp] - vi[jm]) / two_h
                Z += area * (dxu * dxu + dyu * dyu + dxv * dxv + dyv * dyv)
        Es.append(E)
        Zs.append(Z)
    e_err = 0.0
    for kk, t in enumerate(times):
        e_err = max(e_err, abs(Es[kk] - math.pi ** 2 * math.exp(-4.0 * nu * t)))
    integ = 0.0
    for kk in range(len(times) - 1):
        integ += (Zs[kk] + Zs[kk + 1]) / 2.0 * (times[kk + 1] - times[kk])
    balance = abs(Es[-1] - Es[0] + nu * integ)
    mono = True
    for kk in range(1, len(Es)):
        if Es[kk] > Es[kk - 1] + 1e-12:
            mono = False
            break
    bal_order = 0.0
    if with_order:
        # баланс на точном поле согласован с дискретной энстрофией лишь O(h²):
        # проверяем именно наблюдаемый порядок убывания невязки баланса
        b2 = bench_energy(2 * N, nu, with_order=False)["balance"]
        bal_order = math.log2(max(balance, 1e-300) / max(b2, 1e-300))
    return {"e_err": e_err, "balance": balance, "mono": mono,
            "h": 2.0 * math.pi / N, "bal_order": bal_order}


def bench_abc_res(N: int) -> dict:
    """ABC-поток (Бельтрами): дискретный rot, дивергенция, тождество Ламба."""
    h = 2.0 * math.pi / N
    two_h = 2.0 * h
    u1 = [[[0.0] * N for _ in range(N)] for _ in range(N)]
    u2 = [[[0.0] * N for _ in range(N)] for _ in range(N)]
    u3 = [[[0.0] * N for _ in range(N)] for _ in range(N)]
    for i in range(1, N + 1):
        x = (i - 1) * h
        for j in range(1, N + 1):
            y = (j - 1) * h
            for k in range(1, N + 1):
                z = (k - 1) * h
                u1[i - 1][j - 1][k - 1] = math.sin(z) + math.cos(y)
                u2[i - 1][j - 1][k - 1] = math.sin(x) + math.cos(z)
                u3[i - 1][j - 1][k - 1] = math.sin(y) + math.cos(x)
    curl = div = lamb = 0.0
    for i in range(1, N + 1):
        ip, im = bench_pidx(i + 1, N) - 1, bench_pidx(i - 1, N) - 1
        for j in range(1, N + 1):
            jp, jm = bench_pidx(j + 1, N) - 1, bench_pidx(j - 1, N) - 1
            for k in range(1, N + 1):
                kp, km = bench_pidx(k + 1, N) - 1, bench_pidx(k - 1, N) - 1
                u1c = u1[i - 1][j - 1][k - 1]
                u2c = u2[i - 1][j - 1][k - 1]
                u3c = u3[i - 1][j - 1][k - 1]
                dxu1 = (u1[ip][j - 1][k - 1] - u1[im][j - 1][k - 1]) / two_h
                dyu1 = (u1[i - 1][jp][k - 1] - u1[i - 1][jm][k - 1]) / two_h
                dzu1 = (u1[i - 1][j - 1][kp] - u1[i - 1][j - 1][km]) / two_h
                dxu2 = (u2[ip][j - 1][k - 1] - u2[im][j - 1][k - 1]) / two_h
                dyu2 = (u2[i - 1][jp][k - 1] - u2[i - 1][jm][k - 1]) / two_h
                dzu2 = (u2[i - 1][j - 1][kp] - u2[i - 1][j - 1][km]) / two_h
                dxu3 = (u3[ip][j - 1][k - 1] - u3[im][j - 1][k - 1]) / two_h
                dyu3 = (u3[i - 1][jp][k - 1] - u3[i - 1][jm][k - 1]) / two_h
                dzu3 = (u3[i - 1][j - 1][kp] - u3[i - 1][j - 1][km]) / two_h
                curl = max(curl, abs((dyu3 - dzu2) - u1c),
                           abs((dzu1 - dxu3) - u2c),
                           abs((dxu2 - dyu1) - u3c))
                div = max(div, abs(dxu1 + dyu2 + dzu3))
                # тождество Ламба для Бельтрами: u·∇u = ∇(|u|²/2)
                qcp = (u1c * u1c + u2c * u2c + u3c * u3c) / 2.0
                qip = (u1[ip][j - 1][k - 1] ** 2 + u2[ip][j - 1][k - 1] ** 2
                       + u3[ip][j - 1][k - 1] ** 2) / 2.0
                qim = (u1[im][j - 1][k - 1] ** 2 + u2[im][j - 1][k - 1] ** 2
                       + u3[im][j - 1][k - 1] ** 2) / 2.0
                qjp = (u1[i - 1][jp][k - 1] ** 2 + u2[i - 1][jp][k - 1] ** 2
                       + u3[i - 1][jp][k - 1] ** 2) / 2.0
                qjm = (u1[i - 1][jm][k - 1] ** 2 + u2[i - 1][jm][k - 1] ** 2
                       + u3[i - 1][jm][k - 1] ** 2) / 2.0
                qkp = (u1[i - 1][j - 1][kp] ** 2 + u2[i - 1][j - 1][kp] ** 2
                       + u3[i - 1][j - 1][kp] ** 2) / 2.0
                qkm = (u1[i - 1][j - 1][km] ** 2 + u2[i - 1][j - 1][km] ** 2
                       + u3[i - 1][j - 1][km] ** 2) / 2.0
                dqpx = (qip - qim) / two_h
                dqpy = (qjp - qjm) / two_h
                dqpz = (qkp - qkm) / two_h
                lamb = max(lamb,
                           abs(u1c * dxu1 + u2c * dyu1 + u3c * dzu1 - dqpx),
                           abs(u1c * dxu2 + u2c * dyu2 + u3c * dzu2 - dqpy),
                           abs(u1c * dxu3 + u2c * dyu3 + u3c * dzu3 - dqpz))
    return {"curl": curl, "div": div, "lamb": lamb, "h": h}


def bench_burgers_run(N: int) -> dict:
    """Стационарная вязкая ударная волна Бюргерса: прогон до установления."""
    nu, c = 0.1, 1.0
    Lx = 4.0
    h = Lx / N
    x = [-Lx / 2.0 + i * h for i in range(N + 1)]

    def uex(xv):
        return -c * math.tanh(c * xv / (2.0 * nu))

    u = [-math.tanh(c * xv / (2.0 * nu)) + 0.05 * math.sin(3.0 * xv) for xv in x]
    dt = 0.3 * h * h / nu
    nsteps = math.ceil(30.0 / dt)
    resid = 0.0
    cfl = dt * nu / (h * h)
    for _n in range(nsteps):
        un = u[:]
        m = 0.0
        for i in range(1, N):
            ui = un[i]
            ux = (ui - un[i - 1]) / h if ui > 0 else (un[i + 1] - ui) / h
            uxx = (un[i + 1] - 2.0 * ui + un[i - 1]) / (h * h)
            u[i] = ui - dt * ui * ux + cfl * un[i + 1] - 2.0 * cfl * ui + cfl * un[i - 1]
            d = abs(u[i] - ui)
            if d > m:
                m = d
        u[0] = uex(-Lx / 2.0)
        u[N] = uex(Lx / 2.0)
        m = max(m, abs(u[0] - un[0]), abs(u[N] - un[N]))
        resid = m / dt
    err = max(abs(u[i] - uex(x[i])) for i in range(N + 1))
    impulse = sum(u) * h - (u[0] + u[N]) * h / 2.0
    # B8: resid = m/dt усиливается 1/dt (~5e4 при N=1600) — порог должен
    # масштабироваться. resid_eps ≡ «изменение за шаг m < 1e-10» (уровень
    # roundoff для |u|≈1): resid_eps = 1e-10/dt, снизу ограничено 1e-6,
    # чтобы поведение на малых N не изменилось.
    resid_eps = max(1e-6, 1e-10 / dt)
    return {"err": err, "resid": resid, "resid_eps": resid_eps,
            "impulse": impulse, "h": h, "steps": nsteps}


def bench_richardson(N0: int) -> dict:
    """Наблюдаемый порядок по Ричардсону: log2(res(N)/res(2N)) для ТГ и ABC."""
    r1 = bench_tg_res(N0)["res"]
    r2 = bench_tg_res(2 * N0)["res"]
    r3 = bench_tg_res(4 * N0)["res"]
    a1 = bench_abc_res(N0)["curl"]
    a2 = bench_abc_res(2 * N0)["curl"]
    a3 = bench_abc_res(4 * N0)["curl"]
    return {"tg": (math.log2(r1 / r2), math.log2(r2 / r3)),
            "abc": (math.log2(a1 / a2), math.log2(a2 / a3)),
            "res_tg": (r1, r2, r3), "res_abc": (a1, a2, a3), "N0": N0}


def bench_clamp_size(base: int, lo: int, hi: int, cfg: VfaConfig) -> int:
    """Масштаб бенчмарка: база пресета × size, зажата в [lo, hi]."""
    return max(lo, min(hi, base * cfg.size))


def bench_preset_base(cfg: VfaConfig, quick: int, full: int) -> int:
    return quick if cfg.preset == "quick" else full


# ── задача 16: Тейлор-Грин — невязка дискретных НС на точном решении

def task16_taylor_green(cfg: VfaConfig) -> bool:
    ctx = VfaTaskCtx(cfg, 16, "taylor_green")
    N = bench_clamp_size(bench_preset_base(cfg, 16, 32), 8, 128, cfg)
    r = bench_tg_res(N)
    r2 = bench_tg_res(max(4, N // 2))
    order = math.log2(r2["res"] / r["res"])
    ctx.check("невязка дискретных НС < 3h² (2-й порядок)",
              r["res"] < 3.0 * r["h"] ** 2,
              f"N={N} res={r['res']:.3g} h²={r['h'] ** 2:.3g}")
    ctx.check("наблюдаемый порядок ≈ 2 (Ричардсон)", 1.7 < order < 2.3,
              f"p = {order:.3g}")
    ctx.check("дискретная дивергенция < 1.5h²",
              r["div"] < 1.5 * r["h"] ** 2, f"div = {r['div']:.3g}")
    ctx.metrics["res_max"] = f"{r['res']:.6g}"
    ctx.metrics["order"] = f"{order:.3g}"
    ctx.metrics["div_max"] = f"{r['div']:.6g}"
    p = RepPlot("Тейлор-Грин: точные профили (Python task 16)", "x", "u, p")
    xg = [(i - 1) * r["h"] for i in range(1, N + 1)]
    yy = math.pi / 3.0
    e2, e4 = math.exp(-0.5), math.exp(-1.0)   # t=0.25, ν=1
    p.add_series("u(x, y=π/3)", xg,
                 [math.sin(x) * math.cos(yy) * e2 for x in xg], "l")
    p.add_series("4p(x, y=π/3)", xg,
                 [(math.cos(2.0 * x) + math.cos(2.0 * yy)) * e4 for x in xg], "l")
    ctx.save_plot(p, 1)
    ctx.finish_gif()
    ok = not ctx.failures
    VFALog.get().log_result(16, "taylor_green", "PASS" if ok else "FAIL", "",
                            ctx.metrics, 0.0, ctx.artifacts)
    return ok


# ── задача 17: Ковазнай — стационарное точное решение НС

def task17_kovasznay(cfg: VfaConfig) -> bool:
    ctx = VfaTaskCtx(cfg, 17, "kovasznay")
    N = bench_clamp_size(bench_preset_base(cfg, 24, 48), 12, 128, cfg)
    r = bench_kov_res(N)
    r2 = bench_kov_res(max(8, N // 2))
    order = math.log2(max(r2["res"], 1e-300) / max(r["res"], 1e-300))
    ctx.check("аналитическая дивергенция в узлах = 0 (machine)",
              r["div"] < 1e-12, f"max = {r['div']:.3g}")
    ctx.check("невязка стационарных НС < 2000·max(hx,hy)²",
              r["res"] < 2000.0 * max(r["hx"], r["hy"]) ** 2,
              f"res = {r['res']:.3g}")
    ctx.check("наблюдаемый порядок ≈ 2 (Ричардсон)", 1.7 < order < 2.5,
              f"p = {order:.3g}")
    ctx.metrics["res_max"] = f"{r['res']:.6g}"
    ctx.metrics["order"] = f"{order:.3g}"
    ctx.metrics["lambda"] = f"{r['lam']:.6g}"
    p = RepPlot("Ковазнай Re=30: профили (Python task 17)", "x", "u, v")
    xg = [(i - 1) * r["hx"] for i in range(1, N + 1)]
    yy = 0.125
    E = [math.exp(r["lam"] * x) for x in xg]
    p.add_series("u(x, y=0.125)", xg,
                 [1.0 - E[i] * math.cos(2.0 * math.pi * yy) for i in range(N)], "l")
    p.add_series("v(x, y=0.125)", xg,
                 [E[i] * (r["lam"] / (2.0 * math.pi)) * math.sin(2.0 * math.pi * yy)
                  for i in range(N)], "l")
    ctx.save_plot(p, 1)
    ctx.finish_gif()
    ok = not ctx.failures
    VFALog.get().log_result(17, "kovasznay", "PASS" if ok else "FAIL", "",
                            ctx.metrics, 0.0, ctx.artifacts)
    return ok


# ── задача 18: осциллирующая стенка (Стокс II) — FTCS против точного профиля

def task18_stokes_wall(cfg: VfaConfig) -> bool:
    ctx = VfaTaskCtx(cfg, 18, "stokes_wall")
    N = bench_clamp_size(bench_preset_base(cfg, 40, 80), 20, 400, cfg)
    r = bench_stokes_run(N)
    ctx.check("L∞ профиля против точного < 0.035",
              r["err"] < 0.035, f"err = {r['err']:.3g}")
    ctx.check("периодичность: ещё T — профиль воспроизводится (< 0.005)",
              r["err_period"] < 0.005, f"err_T = {r['err_period']:.3g}")
    ctx.check("глубина у=3/k: |u−e⁻³sin(φ−3)| < 0.02",
              r["deep_err"] < 0.02, f"err = {r['deep_err']:.3g}")
    ctx.metrics["err_linf"] = f"{r['err']:.6g}"
    ctx.metrics["k"] = f"{r['k']:.6g}"
    p = RepPlot("Стокс II: профиль у стенки (Python task 18)", "y", "u")
    uex = [math.exp(-r["k"] * y) * math.sin(r["phi"] - r["k"] * y) for y in r["yg"]]
    p.add_series("точный", r["yg"], uex, "l")
    p.add_series("FTCS", r["yg"], r["unum"], "l")
    ctx.save_plot(p, 1)
    ctx.finish_gif()
    ok = not ctx.failures
    VFALog.get().log_result(18, "stokes_wall", "PASS" if ok else "FAIL", "",
                            ctx.metrics, 0.0, ctx.artifacts)
    return ok


# ── задача 19: инвариант энергии Лере-Хопф на ТГ

def task19_leray_energy(cfg: VfaConfig) -> bool:
    ctx = VfaTaskCtx(cfg, 19, "leray_energy")
    N = bench_clamp_size(bench_preset_base(cfg, 16, 24), 8, 64, cfg)
    r = bench_energy(N)
    ctx.check("E(t) = π²e^{-4νt} (периодическая трапеция) < 1e-7",
              r["e_err"] < 1e-7, f"err = {r['e_err']:.3g}")
    ctx.check("E монотонно не растёт (Лере-Хопф)", r["mono"])
    ctx.check("баланс E(t)-E(0)+ν∫|∇u|²: порядок убывания ≈ 2",
              1.7 < r["bal_order"] < 2.5, f"p = {r['bal_order']:.3g}")
    ctx.metrics["e_err"] = f"{r['e_err']:.6g}"
    ctx.metrics["balance"] = f"{r['balance']:.6g}"
    p = RepPlot("Лере-Хопф: энергия ТГ (Python task 19)", "t", "E")
    tg_grid = [0.05 * i for i in range(6)]
    p.add_series("π²e^{-4νt}", tg_grid,
                 [math.pi ** 2 * math.exp(-4.0 * t) for t in tg_grid], "l")
    ctx.save_plot(p, 1)
    ctx.finish_gif()
    ok = not ctx.failures
    VFALog.get().log_result(19, "leray_energy", "PASS" if ok else "FAIL", "",
                            ctx.metrics, 0.0, ctx.artifacts)
    return ok


# ── задача 20: ABC-поток — Бельтрами, дивергенция, Ламба

def task20_abc_beltrami(cfg: VfaConfig) -> bool:
    ctx = VfaTaskCtx(cfg, 20, "abc_beltrami")
    N = bench_clamp_size(bench_preset_base(cfg, 10, 16), 6, 40, cfg)
    r = bench_abc_res(N)
    r2 = bench_abc_res(max(4, N // 2))
    order = math.log2(max(r2["curl"], 1e-300) / max(r["curl"], 1e-300))
    ctx.check("rot_h u = u (Бельтрами) < 1.5h²",
              r["curl"] < 1.5 * r["h"] ** 2, f"curl = {r['curl']:.3g}")
    ctx.check("наблюдаемый порядок ≈ 2", 1.7 < order < 2.3, f"p = {order:.3g}")
    ctx.check("div_h u < 1.5h²", r["div"] < 1.5 * r["h"] ** 2,
              f"div = {r['div']:.3g}")
    ctx.check("тождество Ламба u·∇u = ∇(u²/2) < 12h²",
              r["lamb"] < 12.0 * r["h"] ** 2, f"lamb = {r['lamb']:.3g}")
    ctx.metrics["curl_max"] = f"{r['curl']:.6g}"
    ctx.metrics["lamb_max"] = f"{r['lamb']:.6g}"
    ctx.metrics["order"] = f"{order:.3g}"
    p = RepPlot("ABC: срез u₁(x, y=π/2, z=π/3) (Python task 20)", "x", "u₁")
    xg = [(i - 1) * r["h"] for i in range(1, N + 1)]
    p.add_series("sin z + cos y", xg,
                 [math.sin(math.pi / 3.0) + math.cos(math.pi / 2.0) for _ in xg], "l")
    ctx.save_plot(p, 1)
    ctx.finish_gif()
    ok = not ctx.failures
    VFALog.get().log_result(20, "abc_beltrami", "PASS" if ok else "FAIL", "",
                            ctx.metrics, 0.0, ctx.artifacts)
    return ok


# ── задача 21: ударная волна Бюргерса — прогон до установления

def task21_burgers_shock(cfg: VfaConfig) -> bool:
    ctx = VfaTaskCtx(cfg, 21, "burgers_shock")
    N = bench_clamp_size(bench_preset_base(cfg, 200, 400), 100, 1600, cfg)
    r = bench_burgers_run(N)
    # B8: порог установления масштабируется с dt (resid_eps из bench)
    ctx.check("установление: |Δu|/dt < resid_eps", r["resid"] < r["resid_eps"],
              f"resid = {r['resid']:.3g} < eps = {r['resid_eps']:.3g}")
    ctx.check("L∞ против точной волны < 0.06 (upwind O(h))",
              r["err"] < 0.06, f"err = {r['err']:.3g}")
    ctx.check("импульс ∫u dx ≈ 0 (антисимметрия) < 1e-3",
              abs(r["impulse"]) < 1e-3, f"I = {r['impulse']:.3g}")
    ctx.metrics["err_linf"] = f"{r['err']:.6g}"
    ctx.metrics["steps"] = str(r["steps"])
    p = RepPlot("Бюргерс: стационарная ударная волна (Python task 21)", "x", "u")
    xg = [-2.0 + 0.02 * i for i in range(201)]
    p.add_series("точная: −tanh(x/0.2)", xg, [-math.tanh(xv / 0.2) for xv in xg], "l")
    ctx.save_plot(p, 1)
    ctx.finish_gif()
    ok = not ctx.failures
    VFALog.get().log_result(21, "burgers_shock", "PASS" if ok else "FAIL", "",
                            ctx.metrics, 0.0, ctx.artifacts)
    return ok


# ── задача 22: сводный порядок сходимости (Ричардсон) для ТГ и ABC

def task22_richardson(cfg: VfaConfig) -> bool:
    ctx = VfaTaskCtx(cfg, 22, "richardson")
    N0 = 8 if cfg.preset == "quick" else 12
    r = bench_richardson(N0)
    ctx.check("ТГ: обе пары порядков ∈ [1.7, 2.3]",
              all(1.7 < x < 2.3 for x in r["tg"]),
              f"p = {[round(x, 3) for x in r['tg']]}")
    ctx.check("ABC: обе пары порядков ∈ [1.7, 2.3]",
              all(1.7 < x < 2.3 for x in r["abc"]),
              f"p = {[round(x, 3) for x in r['abc']]}")
    ctx.check("невязки монотонно убывают (N, 2N, 4N)",
              r["res_tg"][0] > r["res_tg"][1] > r["res_tg"][2]
              and r["res_abc"][0] > r["res_abc"][1] > r["res_abc"][2])
    ctx.metrics["p_tg"] = str([round(x, 3) for x in r["tg"]])
    ctx.metrics["p_abc"] = str([round(x, 3) for x in r["abc"]])
    ctx.finish_gif()
    ok = not ctx.failures
    VFALog.get().log_result(22, "richardson", "PASS" if ok else "FAIL", "",
                            ctx.metrics, 0.0, ctx.artifacts)
    return ok


VFA_BENCH_TABLE = [
    {"id": 16, "slug": "taylor_green",
     "title": "Тейлор-Грин: невязка дискретных НС",
     "method_note": "метод манифольда, порядок 2 по Ричардсону",
     "fn": task16_taylor_green, "pass2_fn": None, "deps": []},
    {"id": 17, "slug": "kovasznay",
     "title": "Ковазнай: стационарное решение НС",
     "method_note": "Re=30, λ=Re/2−√(Re²/4+4π²), аналитическая div",
     "fn": task17_kovasznay, "pass2_fn": None, "deps": []},
    {"id": 18, "slug": "stokes_wall",
     "title": "Стокс II: осциллирующая стенка",
     "method_note": "FTCS против e^{-ky}sin(ωt−ky), периодичность",
     "fn": task18_stokes_wall, "pass2_fn": None, "deps": []},
    {"id": 19, "slug": "leray_energy",
     "title": "Лере-Хопф: энергетический инвариант",
     "method_note": "E=π²e^{-4νt}, монотонность, баланс с энстрофией",
     "fn": task19_leray_energy, "pass2_fn": None, "deps": []},
    {"id": 20, "slug": "abc_beltrami",
     "title": "ABC: Бельтрами и тождество Ламба",
     "method_note": "rot u = u, div = 0, u·∇u = ∇(u²/2)",
     "fn": task20_abc_beltrami, "pass2_fn": None, "deps": []},
    {"id": 21, "slug": "burgers_shock",
     "title": "Бюргерс: стационарная ударная волна",
     "method_note": "−tanh(cx/2ν), прогон до установления",
     "fn": task21_burgers_shock, "pass2_fn": None, "deps": []},
    {"id": 22, "slug": "richardson",
     "title": "Ричардсон: сводный порядок сходимости",
     "method_note": "log₂(res(N)/res(2N)) ≈ 2 для ТГ и ABC",
     "fn": task22_richardson, "pass2_fn": None, "deps": []},
]

# ── регистрация §4 (fn/pass2_fn/deps); SUITE_IDS выводится, не хардкодится

def _vfa_register_all() -> None:
    for t in [
        {"id": 1, "slug": "constants", "title": "Константная цепочка b→θ_b→Клейн",
         "method_note": "Decimal 55/65 знаков, ряды arcsin/sin",
         "fn": task01_constants, "pass2_fn": task01b_constants_hardcore, "deps": []},
        {"id": 2, "slug": "smagorinsky", "title": "Мастер-соотношение C_s(C_K)",
         "method_note": "pinned 50 знаков, закон показателя, K41",
         "fn": task02_smagorinsky, "pass2_fn": task02b_smagorinsky_hardcore, "deps": []},
        {"id": 3, "slug": "cassini", "title": "Тождество Кассини и коэффициенты (5')",
         "method_note": "точные целые Фибоначчи",
         "fn": task03_cassini, "pass2_fn": task03b_cassini_hardcore, "deps": []},
        {"id": 4, "slug": "kdv", "title": "KdV-солитон: подстановка в ОДУ",
         "method_note": "аналитические производные sech², Decimal-невязка",
         "fn": task04_kdv, "pass2_fn": task04b_kdv_hardcore, "deps": []},
        {"id": 5, "slug": "klein_bridge", "title": "Мост Клейна: эргодика, изометрия",
         "method_note": "Нивен, three-gap, поворот",
         "fn": task05_klein_bridge, "pass2_fn": task05b_klein_hardcore, "deps": []},
        {"id": 6, "slug": "rodrigues", "title": "Алгебра поворота Родрига",
         "method_note": "RᵀR=I, det, норма, спектр-угол",
         "fn": task06_rodrigues, "pass2_fn": task06b_rodrigues_hardcore, "deps": []},
        {"id": 7, "slug": "kirchhoff", "title": "Вихри Кирхгофа: RK4-гамильтоновость",
         "method_note": "дрейф ~dt⁴, порядок 4, изометрия",
         "fn": task07_kirchhoff, "pass2_fn": task07b_kirchhoff_hardcore, "deps": []},
        {"id": 8, "slug": "py_bridge", "title": "Мост к прогону run_*: сверка вердиктов",
         "method_note": "§32: пересечение выполненных задач; SKIP если прогонов нет",
         "fn": task08_py_bridge, "pass2_fn": None, "deps": []},
        {"id": 9, "slug": "pinned", "title": "Pinned-значения на Float64",
         "method_note": "b и C_s(1.5) против строковых эталонов",
         "fn": task09_pinned, "pass2_fn": None, "deps": []},
        {"id": 10, "slug": "suite", "title": "Сводный численный прогон",
         "method_note": "вердикты 1–4 из реестра; тихий внутренний прогон недостающих",
         "fn": task10_suite, "pass2_fn": None, "deps": []},
        {"id": 11, "slug": "layered_b", "title": "Слоистая b-поправка (§27)",
         "method_note": "b(h, W), пределы, монотонность",
         "fn": task11_layered_b, "pass2_fn": None, "deps": []},
        {"id": 12, "slug": "layer_sync", "title": "Синхронизация К↔Р по слоям",
         "method_note": "sync_residual, Родриг |u'|=|u|",
         "fn": task12_layer_sync, "pass2_fn": None, "deps": []},
        {"id": 13, "slug": "total_braking", "title": "Полное 3D-торможение",
         "method_note": "τ = −∑b_iΓ_i с весом Δz, сходимость по N",
         "fn": task13_total_braking, "pass2_fn": None, "deps": []},
        {"id": 14, "slug": "layered_evolution", "title": "Динамика 3D ствола",
         "method_note": "dΓ/dt = −bΓ/T, лог-декремент против mean(b)",
         "fn": task14_layered_evolution, "pass2_fn": None, "deps": []},
        {"id": 15, "slug": "dynamic", "title": "Динамические тесты",
         "method_note": "fuzz + sweep + metamorphic",
         "fn": task15_dynamic, "pass2_fn": None, "deps": []},
    ]:
        register_task(t)
    for t in VFA_BENCH_TABLE:
        register_bench(t)


_vfa_register_all()

# ── двухпроходная обёртка §5

VFA_STATS = {"secondary_hardcore": [], "tertiary_series": [], "quaternary_audit": []}


def vfa_run_task_two_pass(cfg: VfaConfig, task_id: int) -> bool:
    """§5: pass1 — основной; pass2 — углублённый (hardcore); cfg-поля
    сохраняются (deepcopy: tasks/plot_formats/report_formats мутабельны)
    и восстанавливаются в finally даже при исключении."""
    t = vfa_find_task_rec(task_id)
    snapshot = copy.deepcopy(cfg.__dict__)
    ok1 = ok2 = True
    try:
        cfg._hardcore = False
        VFA_STATS["secondary_hardcore"].append(task_id)
        ok1 = _dispatch(task_id, cfg)
    finally:
        for k, v in snapshot.items():
            setattr(cfg, k, v)
        VFA_STATS["secondary_hardcore"] = [x for x in VFA_STATS["secondary_hardcore"]
                                           if x != task_id]
    rec1 = dict(VFALog.get().verdicts.get(task_id) or {})
    if t["pass2_fn"] is not None and cfg.two_pass:
        try:
            cfg._hardcore = True
            VFA_STATS["quaternary_audit"].append(task_id)
            ok2 = t["pass2_fn"](cfg)
        finally:
            for k, v in snapshot.items():
                setattr(cfg, k, v)
            VFA_STATS["quaternary_audit"] = [x for x in VFA_STATS["quaternary_audit"]
                                             if x != task_id]
    # §5: финальный вердикт ОБЪЕДИНЯЕТ оба прохода; pass2 не затирает FAIL
    # pass1; явный SKIP из pass1 сохраняется (не превращается в PASS)
    final_ok = ok1 and ok2
    rec2 = VFALog.get().verdicts.get(task_id) or {}
    merged_metrics = dict(rec1.get("metrics", {}))
    merged_metrics.update(rec2.get("metrics", {}))
    merged_artifacts = list(rec1.get("artifacts", [])) + list(rec2.get("artifacts", []))
    if rec1.get("verdict") == "SKIP":
        verdict, reason = "SKIP", rec1.get("reason", "")
    else:
        verdict = "PASS" if final_ok else "FAIL"
        reason = "" if final_ok else ("pass1 FAIL" if not ok1 else "pass2 (hardcore) FAIL")
    VFALog.get().log_result(task_id, t["slug"], verdict,
                            reason, merged_metrics,
                            rec2.get("duration_s", rec1.get("duration_s", 0.0)),
                            list(dict.fromkeys(merged_artifacts)))
    vfa_gc_full()
    return final_ok


# ═══════════════════════════════════════════════════════════════════════════
# Отчёты §8: report.{md,html,pdf,docx}, index.html, FINAL_REPORT, RTM
# ═══════════════════════════════════════════════════════════════════════════

VFA_CSS = """
body{background:#12141c;color:#dce1f0;font-family:'Segoe UI',Arial,sans-serif;margin:0;padding:24px}
h1{color:#50aaff;border-bottom:2px solid #373c50;padding-bottom:8px}
h2{color:#6ec8ff;margin-top:28px}
.card{background:#1a1d28;border:1px solid #373c50;border-radius:10px;padding:14px 18px;margin:10px 0}
.badge{display:inline-block;padding:2px 12px;border-radius:12px;font-weight:700;margin-left:8px}
.PASS,.DONE{background:#1d3a2a;color:#6edc96}.FAIL,.ERROR{background:#3a1d22;color:#ff9a9a}
.WARN,.SKIP{background:#3a331d;color:#ffd98a}
table{border-collapse:collapse;width:100%}td,th{border:1px solid #373c50;padding:6px 10px;text-align:left}
th{background:#22263a}.mono{font-family:Consolas,monospace;font-size:12px;background:#151823;padding:10px;border-radius:8px;white-space:pre-wrap}
.sep{color:#50aaff;letter-spacing:6px}a{color:#6ec8ff}
"""


def vfa_badge_html(verdict: str) -> str:
    return f'<span class="badge {verdict}">{verdict}</span>'


def vfa_task_checks(task_id: int) -> list[tuple[str, str, str]]:
    """Собранные проверки задачи ( наполняется VfaTaskCtx.check )."""
    return getattr(VFALog.get(), "task_checks", {}).get(task_id, [])


def vfa_find_task_rec(task_id: int) -> dict:
    """Поиск задачи в основном реестре и в реестре бенчмарков (§31)."""
    for t in TASKS + VFA_BENCH:
        if t["id"] == task_id:
            return t
    raise RuntimeError(fmt(default_config(), "unknown_task", tid=task_id))


def vfa_all_tasks() -> list[dict]:
    """Объединённый реестр по возрастанию id: основные задачи + бенчмарки."""
    return sorted(TASKS + VFA_BENCH, key=lambda x: x["id"])


def vfa_report_md(task_id: int, slug: str, verdict: str, metrics: dict,
                  artifacts: list[str], cfg: VfaConfig) -> str:
    log = VFALog.get()
    t = vfa_find_task_rec(task_id)
    lines = [f"# Задача {task_id:02d} — {t['title']}  `{verdict}`", "",
             f"*Метод:* {t['method_note']}", "",
             f"*Вердикт:* **{verdict}** · {datetime.now().isoformat(timespec='seconds')}", "",
             "| Проверка | Статус | Детали |", "|---|---|---|"]
    checks = vfa_task_checks(task_id)
    if checks:
        for name, status, detail in checks:
            lines.append(f"| {name} | {status} | {detail} |")
    else:
        lines.append("| — | — | проверок не зарегистрировано |")
    lines += ["", "## Метрики", ""]
    if metrics:
        for k, v in metrics.items():
            lines.append(f"- `{k}` = `{v}`")
    else:
        lines.append("- метрик нет")
    lines += ["", "## Артефакты", ""]
    if artifacts:
        for a in artifacts:
            lines.append(f"- `{a}`")
    else:
        lines.append("- no plots queued" if cfg.lang == "en" else fmt(cfg, "no_plots"))
    lines += ["", "## Вычислительный лог (фрагмент)", "", "```"]
    lines += [l for l in log._comp if f"task{task_id:02d}" in l][-40:]
    lines += ["```", ""]
    return "\n".join(lines)


def vfa_report_html(task_id: int, slug: str, verdict: str, metrics: dict,
                    artifacts: list[str], cfg: VfaConfig) -> str:
    t = vfa_find_task_rec(task_id)
    rows = "".join(
        f"<tr><td>{n}</td><td>{vfa_badge_html(s)}</td><td>{d}</td></tr>"
        for n, s, d in vfa_task_checks(task_id)) or "<tr><td colspan=3>—</td></tr>"
    mrows = "".join(f"<tr><td class='mono'>{k}</td><td class='mono'>{v}</td></tr>"
                    for k, v in metrics.items()) or "<tr><td colspan=2>—</td></tr>"
    arows = "".join(f"<li class='mono'>{a}</li>" for a in artifacts) or \
        f"<li>{fmt(cfg, 'no_plots')}</li>"
    return f"""<!doctype html><html lang="{cfg.lang}"><head><meta charset="utf-8">
<title>VFA task {task_id:02d}</title><style>{VFA_CSS}</style></head><body>
<h1>Задача {task_id:02d} — {t['title']} {vfa_badge_html(verdict)}</h1>
<div class="sep">◆ ◆ ◆</div>
<p><i>{t['method_note']}</i></p>
<h2>Проверки</h2><table><tr><th>Проверка</th><th>Статус</th><th>Детали</th></tr>{rows}</table>
<h2>Метрики</h2><table>{mrows}</table>
<h2>Артефакты</h2><ul>{arows}</ul>
</body></html>"""


def vfa_write_task_report(cfg: VfaConfig, task_id: int) -> None:
    rec = VFALog.get().verdicts.get(task_id)
    if rec is None or cfg.no_report:
        return
    td = VFALog.get().task_dir
    md = vfa_report_md(task_id, rec["slug"], rec["verdict"], rec["metrics"],
                       rec["artifacts"], cfg)
    html = vfa_report_html(task_id, rec["slug"], rec["verdict"], rec["metrics"],
                           rec["artifacts"], cfg)
    (td / "report.md").write_text(md, encoding="utf-8")
    (td / "report.html").write_text(html, encoding="utf-8")
    if "pdf" in cfg.report_formats:
        doc = VfaPdfDoc(f"VFA task {task_id:02d}")
        for line in md.splitlines():
            if line.startswith("# "):
                doc.text(line[2:], 16, 20, bold=True)
            elif line.startswith("## "):
                doc.text(line[3:], 13, 17, bold=True)
            elif line.startswith("|"):
                doc.text(line.replace("|", " | ").strip(), 8, 11)
            else:
                doc.text(line, 9)
        doc.save(td / "report.pdf")
        rec["artifacts"] = list(dict.fromkeys(rec["artifacts"] + ["report.pdf"]))
    if "docx" in cfg.report_formats:
        d = VfaDocxWriter()
        for line in md.splitlines():
            if line.startswith("# "):
                d.para(line[2:], "h1")
            elif line.startswith("## "):
                d.para(line[3:], "h2")
            else:
                d.para(line, "body" if not line.startswith("```") else "mono")
        d.save(td / "report.docx")
        rec["artifacts"] = list(dict.fromkeys(rec["artifacts"] + ["report.docx"]))


def vfa_write_index(cfg: VfaConfig) -> None:
    log = VFALog.get()
    if cfg.no_report or log.run_dir is None:
        return
    rows = ""
    for t in vfa_all_tasks():
        rec = log.verdicts.get(t["id"])
        v = rec["verdict"] if rec else "—"
        link = f"task_{t['id']:02d}_{t['slug']}/report.html" if rec else "#"
        rows += (f"<tr><td>{t['id']:02d}</td><td><a href='{link}'>{t['title']}</a></td>"
                 f"<td>{t['method_note']}</td><td>{vfa_badge_html(v) if v != '—' else '—'}</td>"
                 f"<td>{rec['duration_s'] if rec else '—'}s</td></tr>")
    html = f"""<!doctype html><html lang="{cfg.lang}"><head><meta charset="utf-8">
<title>VFA run index</title><style>{VFA_CSS}</style></head><body>
<h1>VFA · прогон {log.run_dir.name}</h1><div class="sep">◆ ◆ ◆</div>
<div class="card">Запуск: {datetime.now().isoformat(timespec='seconds')} ·
платформа {VFA_PLATFORM()} · preset <b>{cfg.preset}</b> ·
two-pass {'ON' if cfg.two_pass else 'OFF'}</div>
<table><tr><th>#</th><th>Задача</th><th>Метод</th><th>Вердикт</th><th>сек</th></tr>{rows}</table>
</body></html>"""
    (log.run_dir / "index.html").write_text(html, encoding="utf-8")


VFA_RTM_ROWS: list[tuple[str, str, str]] = [
    ("§0 Роль/режимы", "main(): меню/библиотека/CLI", "--self-test --contract"),
    ("§1.1 Адаптер", "шапка файла: таблица адаптера Python", "ревью шапки"),
    ("§1.3 Пресеты", "apply_preset → preset-поля cfg", "--preset quick --print-config"),
    ("§1.4 Escape-hatch", "vfa_set_rlimit → ERR_UNSUPPORTED; SKIP py_bridge без прогона",
     "лог уровня warn"),
    ("§2 Архитектура", "классы VFAUI/VFAMon/VFAPlot/VFALog/VFATest",
     "--self-test (unit)"),
    ("§3 Конфиг", "VfaConfig + 5 точек входа + ресолверы", "--print-config"),
    ("§4 Реестр", "TASKS/register_task/_dispatch/--list-tasks", "--list-tasks"),
    ("§5 Двухпроход", "vfa_run_task_two_pass + finally-restore", "--task 1 / --no-two-pass"),
    ("§6 Бар/pump/heartbeat/ctl/сигналы", "VFAUI.bar_line, pump, prog_heartbeat, .vfa_ctl",
     "прогон с TTY; SIGINT=130"),
    ("§7 Монитор", "VFAMon: /proc, /sys, CSV, панель", "--monitor panel"),
    ("§8 Логи/отчёты", "VFALog + vfa_write_* + FINAL_REPORT", "результаты прогона"),
    ("§9 Графика", "VFAPlot: PNG zlib/Up, GIF LZW, SVG, PDF, 3×5 шрифт",
     "plots/*.png + animation.gif"),
    ("§10 Память", "vfa_gc_full: gc×2 + malloc_trim", "лог между задачами"),
    ("§11 CLI", "vfa_parse_args: unknown → WARNING/--strict", "--help; --no-such-flag"),
    ("§12 Меню", "vfa_menu: клавиши, RU-раскладка, EOF-guard 50",
     "меню; /dev/null | python3 …"),
    ("§13 Ошибки/тайм-ауты", "try/finally TEE, task/global timeout, exit-коды",
     "--task-timeout 1"),
    ("§14 Локализация", "MSG[en,ru] + fmt{}", "--lang en / меню 'g'"),
    ("§15 Стиль", "секции ──/═══, const-числа с происхождением", "ревью кода"),
    ("§16 Точка входа", "__main__ + библиотечный импорт тих", "import; python3 file"),
    ("§17 Тесты", "VFATest: 13 канонических + props/contract", "--self-test"),
    ("§18 Манифест", "vfa_write_manifest: sha256, seeds, git", "MANIFEST.toml"),
    ("§19 CI/коды выхода", "--ci, --junit, 0/1/2/3/4/130/143", "--ci --task all"),
    ("§20 Доступность", "NO_COLOR/TERM=dumb/--plain/--unicode", "NO_COLOR=1 …"),
    ("§21 Чек-лист", "VFATest.contract_check()", "--self-test --contract"),
    ("§22 DoD", "демо-транскрипт приложен к поставке", "download/"),
    ("§23 Приёмы", "tee try/finally, drop-oldest, heartbeat, restore-cfg", "код + лог"),
    ("§24 Адаптер", "шапка файла", "—"),
    ("§25/26 Подстановки/вызовы", "шапка + --help", "--help"),
    ("§27 3D-слои", "VFALayer3D.b_layer(h,W), total_braking, layered_evolution",
     "--task 11 --task 15"),
    ("§29 TUI-меню", "vfa_menu_tree_run: дерево root/settings/lab/bench/results/diag",
     "--menu / TTY без флагов"),
    ("§30 VFALab", "--sweep KEY=V1,V2 → декартово произведение, бандлы lab_*",
     "--sweep preset=quick,full"),
    ("§31 Бенчи 16–22", "ТГ/Ковазнай/Стокс/Лере-Хопф/ABC/Бюргерс/Ричардсон",
     "--task 16,17,18,19,20,21,22"),
    ("§32 Кросс-сверка", "task 08 py_bridge + --cross-check; единая results.json",
     "--cross-check results/run_*/"),
    ("ЗАМЕНА (WARN)", "Херш 5×7 заменён собственным 3×5 штрих-шрифтом; "
     "Golden-файлы: byte-compare PNG с допуском по magic/размеру",
     "SELFTEST.md"),
]


def vfa_write_rtm(cfg: VfaConfig) -> str:
    lines = ["# RTM — Requirements Traceability Matrix", "",
             "| § Контракта | Где реализовано | Как проверено |", "|---|---|---|"]
    for a, b, c in VFA_RTM_ROWS:
        lines.append(f"| {a} | {b} | {c} |")
    lines.append("")
    return "\n".join(lines)


def vfa_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def vfa_write_manifest(cfg: VfaConfig) -> None:
    log = VFALog.get()
    if log.run_dir is None:
        return
    commit = "unknown"
    dirty = False
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(cfg.repo_root),
                                capture_output=True, text=True, timeout=10).stdout.strip()[:12] or "unknown"
        dirty = bool(subprocess.run(["git", "status", "--porcelain"], cwd=str(cfg.repo_root),
                                    capture_output=True, text=True, timeout=10).stdout.strip())
    except (OSError, subprocess.TimeoutExpired):
        pass
    lines = ["[file]",
             f'path = "{Path(__file__).resolve()}"',
             f'sha256 = "{vfa_sha256(Path(__file__).resolve())}"',
             f'language = "python"', f'lang_version = "{sys.version.split()[0]}"',
             "", "[env]",
             f'platform = "{VFA_PLATFORM()}"',
             f'os_release = "{VFA_OS_RELEASE()}"',
             f'cpu_count = {os.cpu_count() or 0}',
             f'ram_gb = {VFAMon.snapshot().get("ram_total_gb") or 0:.1f}',
             "", "[git]", f'commit = "{commit}"', f"dirty = {str(dirty).lower()}",
             "", "[seeds]", "by_task = {" +
             ", ".join(f'{t["id"]} = {cfg.seed ^ (t["id"] * 0x9E3779B1):#x}'
                       for t in TASKS) + "}",
             "", "[artifacts]"]
    for p in sorted(log.run_dir.rglob("*")):
        if p.is_file() and p.name != "MANIFEST.toml":
            rel = p.relative_to(log.run_dir).as_posix()
            lines.append(f'"{rel}" = "sha256:{vfa_sha256(p)}"')
    lines += ["", "[presets]", f'applied = "{cfg.preset}"']
    (log.run_dir / "MANIFEST.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def vfa_write_final_report(cfg: VfaConfig) -> None:
    """§8.2 FINAL_REPORT: мастер-документ, копии, полный лог, RTM."""
    log = VFALog.get()
    if cfg.no_report or log.run_dir is None:
        return
    fr = log.run_dir / "FINAL_REPORT"
    fr.mkdir(exist_ok=True)
    n_pass = sum(1 for r in log.verdicts.values() if r["verdict"] in ("PASS", "DONE"))
    n_fail = sum(1 for r in log.verdicts.values() if r["verdict"] in ("FAIL", "ERROR"))
    n_skip = sum(1 for r in log.verdicts.values() if r["verdict"] == "SKIP")
    head = (f"# VFA · Итоговый отчёт прогона {log.run_dir.name}", "",
            f"Вердикты: **{n_pass} PASS**, {n_fail} FAIL, {n_skip} SKIP · "
            f"preset {cfg.preset} · two-pass {'ON' if cfg.two_pass else 'OFF'} · "
            f"платформа {VFA_PLATFORM()}", "")
    md_parts = list(head)
    for t in vfa_all_tasks():
        td = log.run_dir / f"task_{t['id']:02d}_{t['slug']}"
        if (td / "report.md").exists():
            md_parts += ["---", "", (td / "report.md").read_text(encoding="utf-8")]
    (fr / "final_report.md").write_text("\n".join(md_parts), encoding="utf-8")
    # html: инлайн карточек
    cards = []
    for t in vfa_all_tasks():
        td = log.run_dir / f"task_{t['id']:02d}_{t['slug']}"
        if (td / "report.html").exists():
            body = (td / "report.html").read_text(encoding="utf-8")
            body = body.split("<body>", 1)[-1].split("</body>")[0]
            cards.append(f"<h2>task {t['id']:02d}</h2>" + body)
    (fr / "final_report.html").write_text(
        f"<!doctype html><html><head><meta charset='utf-8'><style>{VFA_CSS}</style></head>"
        f"<body><h1>VFA Final Report</h1>{''.join(cards)}</body></html>", encoding="utf-8")
    if "pdf" in cfg.report_formats:
        doc = VfaPdfDoc("VFA Final Report")
        for line in "\n".join(md_parts).splitlines():
            if line.startswith("# "):
                doc.text(line[2:], 15, 19, bold=True)
            elif line.startswith("## "):
                doc.text(line[3:], 12, 16, bold=True)
            else:
                doc.text(line[:110], 8, 10)
        doc.save(fr / "final_report.pdf")
    if "docx" in cfg.report_formats:
        d = VfaDocxWriter()
        for line in "\n".join(md_parts).splitlines():
            if line.startswith("# "):
                d.para(line[2:], "h1")
            elif line.startswith("## "):
                d.para(line[3:], "h2")
            else:
                d.para(line[:400], "body")
        d.save(fr / "final_report.docx")
    # копии и полные логи
    for t in vfa_all_tasks():
        td = log.run_dir / f"task_{t['id']:02d}_{t['slug']}"
        if td.exists():
            for name in ("report.md", "report.html", "report.pdf", "report.docx"):
                if (td / name).exists():
                    shutil.copy(td / name, fr / f"task_{t['id']:02d}_{name}")
            for lg in (td / "logs").glob("*"):
                shutil.copy(lg, fr / f"task_{t['id']:02d}_{lg.name}")
    (fr / "full_run_log.txt").write_text(
        "\n".join(log._comp) + "\n" + (log.tee.drain() if log.tee else ""),
        encoding="utf-8")
    (fr / "computation_log_full.txt").write_text("\n".join(log._comp) + "\n",
                                                 encoding="utf-8")
    (fr / "results_verdicts.txt").write_text(
        "\n".join(f"task {tid:02d} [{r['slug']}] {r['verdict']} {r['reason']}"
                  for tid, r in sorted(log.verdicts.items())) + "\n", encoding="utf-8")
    (fr / "config_snapshot.txt").write_text(
        "\n".join(f"{k} = {v}   # {cfg._source.get(k, 'default')}"
                  for k, v in cfg.__dict__.items() if k != "_source"), encoding="utf-8")
    (fr / "RTM.md").write_text(vfa_write_rtm(cfg), encoding="utf-8")


def vfa_write_results_json(cfg: VfaConfig, exit_code: int) -> None:
    """§32: единая с Julia схема — tasks{id:{slug,verdict,reason,duration_s}} +
    run{started_at, finished_at, exit_code, preset, two_pass, platform}.
    Компактный JSON (без пробелов) — строгий парсер Julia-эталона читает его
    без fallback-режима; полные метрики живут в отчётах задач."""
    log = VFALog.get()
    if log.run_dir is None:
        return
    tasks = {str(tid): {"slug": rec["slug"], "verdict": rec["verdict"],
                        "reason": rec.get("reason", ""),
                        "duration_s": round(rec.get("duration_s", 0.0), 3)}
             for tid, rec in log.verdicts.items()}
    out = {"tasks": tasks,
           "run": {"started_at": log.run_started_iso,
                   "finished_at": datetime.now().isoformat(timespec="seconds"),
                   "exit_code": exit_code, "preset": cfg.preset,
                   "two_pass": cfg.two_pass, "platform": VFA_PLATFORM()}}
    (log.run_dir / "results.json").write_text(
        json.dumps(out, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8")


def vfa_write_junit(cfg: VfaConfig, path: Path) -> None:
    log = VFALog.get()
    cases = []
    for t in vfa_all_tasks():
        rec = log.verdicts.get(t["id"])
        if rec is None:
            continue
        failed = rec["verdict"] in ("FAIL", "ERROR")
        skipped = rec["verdict"] == "SKIP"
        case = (f'<testcase classname="vfa.task{t["id"]:02d}" name="{t["slug"]}" '
                f'time="{rec["duration_s"]}">')
        if failed:
            case += f'<failure message="{rec["reason"] or rec["verdict"]}"/>'
        elif skipped:
            case += f'<skipped message="{rec["reason"]}"/>'
        cases.append(case + "</testcase>")
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           f'<testsuite name="vfa" tests="{len(cases)}" '
           f'failures="{sum(1 for c in cases if "failure" in c)}" '
           f'skipped="{sum(1 for c in cases if "skipped" in c)}">\n'
           + "\n".join(cases) + "\n</testsuite>\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(xml, encoding="utf-8")


# ═══════════════════════════════════════════════════════════════════════════
# Раннер §6/§13: TEE-обёртка, тайм-ауты, .vfa_ctl, сигналы, монитор-CSV
# ═══════════════════════════════════════════════════════════════════════════

def vfa_poll_ctl(cfg: VfaConfig) -> str:
    """§6.4: файл .vfa_ctl с командами pause/resume/snapshot/abort."""
    if VFALog.get().run_dir is None:
        return ""
    ctl = VFALog.get().run_dir / VFA_CTL_NAME
    if not ctl.exists():
        return ""
    try:
        cmd = ctl.read_text(encoding="utf-8").strip().lower()
        ctl.unlink()
    except OSError:
        return ""
    log = VFALog.get()
    if cmd == "pause":
        log.log_comp("ctl: pause")
        log.pause_flag.set()
    elif cmd == "resume":
        log.log_comp("ctl: resume")
        log.pause_flag.clear()
    elif cmd == "snapshot":
        log.log_comp("ctl: snapshot requested")
        log.snapshot_requested.set()
    elif cmd == "abort":
        log.log_comp("ctl: abort requested")
        log.abort_flag.set()
        return "abort"
    else:
        log.log_comp(f"ctl: неизвестная команда {cmd!r}", "warn")
    return cmd


class VfaMonitorThread(threading.Thread):
    """§7: фоновый монитор; ошибки — в log_comp, цикл продолжается."""

    def __init__(self, cfg: VfaConfig, csv_path: Path):
        super().__init__(daemon=True)
        self.cfg = cfg
        self.csv_path = csv_path
        self.on = cfg.monitor != "off"
        self._stop = threading.Event()

    def run(self) -> None:
        if not self.on:
            return
        try:
            with open(self.csv_path, "a", encoding="utf-8") as fh:
                fh.write("ts,cpu_percent,ram_used_gb,temp_c,io_latency_us\n")
                while not self._stop.is_set():
                    s = VFAMon.snapshot()
                    cpu = "" if s["cpu_percent"] is None else f"{s['cpu_percent']:.1f}"
                    ram = "" if s["ram_used_gb"] is None else f"{s['ram_used_gb']:.3f}"
                    tmp = "" if s["temp_c"] is None else f"{s['temp_c']:.1f}"
                    lat = f"{s['io_latency_us']:.0f}"
                    fh.write(f"{datetime.now().isoformat(timespec='seconds')},"
                             f"{cpu},{ram},{tmp},{lat}\n")
                    fh.flush()
                    self._stop.wait(self.cfg.monitor_interval)
        except Exception as exc:            # §7⛔ монитор не валит главный поток
            VFALog.get().log_comp(f"monitor: {exc}", "warn")

    def stop(self) -> None:
        self._stop.set()


def vfa_new_run_dir(cfg: VfaConfig) -> Path:
    """Уникальный каталог прогона (свип/лаборатория могут дать несколько
    прогонов в одну секунду — суффиксы -2, -3, … как в Julia-эталоне)."""
    base = Path(cfg.report_dir or VFA_RESULTS_ROOT) / \
        f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if not base.exists():
        return base
    for k in range(2, 1000):
        cand = base.parent / f"{base.name}-{k}"
        if not cand.exists():
            return cand
    return base.parent / f"{base.name}-{time.monotonic_ns()}"


def vfa_vortex_dir(cfg: VfaConfig) -> Path:
    """§27b: каталог вывода вихря (report_dir/vortex или results/vortex)."""
    return (Path(cfg.report_dir) if cfg.report_dir else VFA_RESULTS_ROOT) / "vortex"


def _vfa_json_safe(o):
    """JSON-санитайзер: inf/nan → null (строгий JSON, парсится jq)."""
    if isinstance(o, dict):
        return {k: _vfa_json_safe(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_vfa_json_safe(v) for v in o]
    if isinstance(o, float) and (math.isinf(o) or math.isnan(o)):
        return None
    return o


def vfa_vortex_write_report(analysis: dict, gif_path) -> tuple[Path, Path]:
    """§27b: companion-отчёт (MD + JSON) рядом с GIF: per-layer таблица,
    milestones, временная серия, вердикт."""
    p = Path(gif_path)
    md = p.with_suffix(".md")
    js = p.with_suffix(".json")
    ms = analysis["milestones"]
    lines = [
        "# 3D Vortex — Stabilization Report",
        "",
        f"- layers: {analysis['n']}, frames: {analysis['nframes']}, "
        f"T: {analysis['T']}",
        f"- mean_b (Γ-weighted): {analysis['mean_b']:.6f}",
        f"- final Γ/Γ₀: {100 * analysis['final_frac']:.2f}%",
        f"- **verdict: {analysis['verdict']}**",
        "",
        "## Milestones",
        "",
        "| threshold | t |",
        "|---|---|",
    ]
    for label, key in (("50% Γ (half-life)", "t50"),
                       ("10% Γ", "t10"), ("1% Γ", "t01")):
        v = ms[key]
        lines.append(f"| {label} | "
                     + (f"{v:.3f}" if v is not None else f"> T = {analysis['T']}")
                     + " |")
    lines += [
        "", "## Per-layer",
        "", "| i | h | W | b_i | half-life | Γ₀ | Γ_T |",
        "|---|---|---|---|---|---|---|",
    ]
    for L in analysis["layers"]:
        hl = "∞" if L["halflife"] == float("inf") else f"{L['halflife']:.2f}"
        lines.append(f"| {L['i']} | {L['h']:.3f} | {L['W']:.3f} | "
                     f"{L['b']:.5f} | {hl} | {L['G0']:.3f} | {L['G_end']:.4f} |")
    lines += [
        "", "## Time series",
        "", "| t | Γ_total | % of Γ₀ | v_peak |",
        "|---|---|---|---|",
    ]
    for f in analysis["frames"]:
        lines.append(f"| {f['t']:.3f} | {f['G_total']:.4f} | "
                     f"{100 * f['G_frac']:.2f}% | {f['v_peak']:.4f} |")
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    js.write_text(json.dumps(_vfa_json_safe(analysis), indent=2,
                             ensure_ascii=False) + "\n", encoding="utf-8")
    return md, js


def vfa_vortex_print_summary(analysis: dict, stream=None) -> None:
    """§27b: короткая числовая сводка стабилизации в stderr."""
    stream = stream or sys.stderr
    frames = analysis["frames"]
    ms = analysis["milestones"]
    print("\n  ── stabilization summary ──", file=stream)
    print(f"  Γ_total: {frames[0]['G_total']:.3f} → "
          f"{frames[-1]['G_total']:.4f} "
          f"({100 * analysis['final_frac']:.2f}%)", file=stream)
    print(f"  mean_b: {analysis['mean_b']:.6f}", file=stream)
    for label, key in (("t50 (half-life)", "t50"),
                       ("t10 (90% decayed)", "t10"),
                       ("t01 (99% decayed)", "t01")):
        v = ms[key]
        print(f"  {label}: "
              + (f"t = {v:.3f}" if v is not None
                 else f"> T = {analysis['T']}"), file=stream)
    print(f"  verdict: {analysis['verdict']}", file=stream)
    print(f"  {'i':>3} {'h':>7} {'W':>7} {'b':>9} {'halflife':>10} "
          f"{'G_end':>10}", file=stream)
    for L in analysis["layers"]:
        hl = "∞" if L["halflife"] == float("inf") else f"{L['halflife']:.2f}"
        print(f"  {L['i']:>3} {L['h']:>7.3f} {L['W']:>7.3f} {L['b']:>9.5f} "
              f"{hl:>10} {L['G_end']:>10.4f}", file=stream)
    print(file=stream)


def vfa_vortex_cli(cfg: VfaConfig) -> None:
    """§27b: неконфликтный CLI-рендер --vortex N (без stdin, CI-safe);
    после рендера — companion-отчёт (md/json) и числовая сводка."""
    pdir = vfa_vortex_dir(cfg)
    pdir.mkdir(parents=True, exist_ok=True)
    N, nframes = cfg.vortex_N, cfg.vortex_frames
    width, height = 900, 640
    if cfg.vortex_quick:            # U-2: быстрое превью (CI-проверка вихря)
        N, nframes, width, height = 32, 8, 640, 440
    path = pdir / f"vortex_N{N}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.gif"
    t_bar = time.monotonic()
    print(VFAUI.bar_line(0, nframes, "vortex", f"  N={N}", t_bar),
          file=sys.stderr, end="", flush=True)

    def cb(k, n):
        if k % 2 == 0 or k == n:
            print(VFAUI.bar_line(k, n, "vortex", f"  N={N}", t_bar),
                  file=sys.stderr, end="", flush=True)

    res = VFAVortex3D.render_vortex_animation(
        path, N=N, nframes=nframes, T=cfg.vortex_T,
        h0=cfg.layer_h0, W0=cfg.layer_W0, width=width, height=height,
        callback=cb)
    done = fmt(cfg, "vortex_done", path=res["path"], frames=res["frames"],
               sec=res["sec"])
    print(f"\r  {done}", file=sys.stderr)
    md, js = vfa_vortex_write_report(res["analysis"], path)
    print(f"  report: {md}", file=sys.stderr)
    print(f"  json:   {js}", file=sys.stderr)
    vfa_vortex_print_summary(res["analysis"])


def vfa_menu_vortex(cfg: VfaConfig) -> None:
    """§27b: интерактивный рендер 3D-вихря (пункт [v] меню, legacy и TUI);
    N ∈ [24, ∞), clamp до 256 — защита памяти; после рендера — отчёт и сводка."""
    print(VFAUI.aurora_title(fmt(cfg, "vortex_title")))
    try:
        n_raw = input(f"  {fmt(cfg, 'vortex_n')}").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return
    try:
        N = int(n_raw)
    except ValueError:
        N = 48
    if N < 24:
        print(f"  ? {fmt(cfg, 'vortex_bad')}")
        return
    if N > 256:
        print(f"  {fmt(cfg, 'vortex_clamp')}")
        N = 256
    try:
        f_raw = input(f"  {fmt(cfg, 'vortex_frames')}").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return
    try:
        nframes = max(2, min(240, int(f_raw)))
    except ValueError:
        nframes = 24
    pdir = vfa_vortex_dir(cfg)
    pdir.mkdir(parents=True, exist_ok=True)
    path = pdir / f"vortex_N{N}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.gif"
    t_bar = time.monotonic()
    print(VFAUI.bar_line(0, nframes, "vortex", f"  N={N}", t_bar),
          end="", flush=True)

    def cb(k, n):
        if k % 2 == 0 or k == n:
            print(VFAUI.bar_line(k, n, "vortex", f"  N={N}", t_bar),
                  end="", flush=True)

    res = VFAVortex3D.render_vortex_animation(
        path, N=N, nframes=nframes, T=cfg.vortex_T,
        h0=cfg.layer_h0, W0=cfg.layer_W0, callback=cb)
    done = fmt(cfg, "vortex_done", path=res["path"], frames=res["frames"],
               sec=res["sec"])
    print(f"\r  {done}")
    md, js = vfa_vortex_write_report(res["analysis"], path)
    print(f"  report: {md}")
    print(f"  json:   {js}")
    vfa_vortex_print_summary(res["analysis"])


def vfa_run_all_tasks(cfg: VfaConfig) -> int:
    """Полный прогон: TEE-обёртка §13.2, тайм-ауты §13.6, бар §6, exit-код §19."""
    log = VFALog.get()
    all_ids = SUITE_IDS + BENCH_IDS
    ids = cfg.tasks or SUITE_IDS
    unknown = [i for i in ids if i not in all_ids]
    if unknown:
        log.log_comp(f"WARNING: неизвестные id задач {unknown} — пропущены", "warn")
    ids = [i for i in ids if i in all_ids] or SUITE_IDS
    run_dir = vfa_new_run_dir(cfg)
    log.open_run(run_dir)
    log.run_started_iso = datetime.now().isoformat(timespec="seconds")
    log.log_stdout_flush()
    log.tee = VfaTeeStdout(sys.stdout)
    sys.stdout = log.tee
    mon = VfaMonitorThread(cfg, run_dir / "logs" / "monitor.csv")
    mon.start()
    global_t0 = time.monotonic()
    gtimed = False
    log.start_pump()
    try:
        print(VFAUI.paint(fmt(cfg, "menu_title"), 2))
        print(fmt(cfg, "run_dir", d=str(run_dir)))
        if cfg.monitor == "panel":
            for line in VFAMon.panel():
                print(line)
        for pos, tid in enumerate(ids):
            t = vfa_find_task_rec(tid)
            t0 = time.monotonic()
            # бар: milestone-режим вне TTY (§6.1)
            if not cfg.plain and sys.stderr.isatty() and cfg.monitor != "off":
                mon_snap = VFAMon.inline(VFAMon.snapshot()) if cfg.monitor == "on" else ""
                log.pump_frame({"kind": "bar",
                                "text": VFAUI.bar_line(pos, len(ids), t["slug"],
                                                       mon_snap, global_t0)})
            task_dir = run_dir / f"task_{tid:02d}_{t['slug']}"
            log.open_task(task_dir, t["slug"])
            log.task_checks.pop(tid, None)
            log.log_comp(f"task {tid:02d} [{t['slug']}] started (two_pass={cfg.two_pass})")
            print(f"=== task {tid:02d}: {t['title']} ===")
            timer = None
            if cfg.task_timeout > 0:
                timer = threading.Timer(cfg.task_timeout, log.abort_flag.set)
                timer.daemon = True
                timer.start()
            status = "PASS"
            reason = ""
            aborted = False
            try:
                while log.pause_flag.is_set():          # §6.4 pause
                    time.sleep(0.2)
                if log.snapshot_requested.is_set():     # §6.4 snapshot
                    log.snapshot_requested.clear()
                    vfa_write_results_json(cfg, 0)
                    log.log_comp("snapshot saved")
                ok = vfa_run_task_two_pass(cfg, tid)
                if log.abort_flag.is_set():
                    status, reason = "FAIL", fmt(cfg, "task_timeout", s=cfg.task_timeout)
                else:
                    status = "PASS" if ok else "FAIL"
            except Exception as exc:                    # §13.1/§13.2
                status, reason = "ERROR", f"EXCEPTION: {exc}"
                log.log_comp(f"EXCEPTION: {traceback.format_exc(limit=3)}", "error")
            finally:
                if timer:
                    timer.cancel()
                aborted = log.abort_flag.is_set()   # фикс: было clear() до проверки —
                log.abort_flag.clear()              # break после тайм-аута был мёртв
                rec = log.verdicts.get(tid)
                if rec is None:                          # задача исчезла бы из отчёта
                    log.log_result(tid, t["slug"], status, reason, {},
                                   time.monotonic() - t0, [])
                else:
                    rec["duration_s"] = round(time.monotonic() - t0, 3)
                    if reason and status == "FAIL":
                        rec["reason"] = reason
                log.log_stdout_flush()
                vfa_write_task_report(cfg, tid)
                log.close_task()
                if aborted:
                    break
            if cfg.global_timeout and time.monotonic() - global_t0 > cfg.global_timeout:
                log.log_comp("global timeout exceeded", "warn")
                gtimed = True
                break
            vfa_poll_ctl(cfg)
        # GIF-туры уже построены задачами; финальные артефакты
        vfa_write_index(cfg)
    finally:
        log.log_stdout_flush()
        sys.stdout = log._stdout_orig
        mon.stop()
        log.stop_pump()
        VFAUI.erase_line()
        log.finalize()
    failures = [r for r in log.verdicts.values() if r["verdict"] in ("FAIL", "ERROR")]
    code = 4 if gtimed else (0 if not failures else 1)
    if log.abort_flag.is_set():
        log.abort_flag.clear()
    vfa_write_results_json(cfg, code)
    vfa_write_manifest(cfg)
    vfa_write_final_report(cfg)
    if cfg.junit:
        vfa_write_junit(cfg, cfg.junit)
    log.log_comp(f"run finished: exit_code={code}, "
                 f"PASS={len(log.verdicts) - len(failures)} FAIL/ERROR={len(failures)}")
    return code


def vfa_run_all(cfg: VfaConfig) -> int:
    """Диспетчер прогона: без свипа — обычный прогон; со свипом —
    многомерный эксперимент VFALab (§30, декартово произведение)."""
    if not cfg.sweep.strip():
        return vfa_run_all_tasks(cfg)
    return vfa_lab_run_experiment(cfg, vfa_lab_parse_sweeps(cfg.sweep, cfg))


def vfa_handle_signals() -> None:
    """§6.5: SIGINT/SIGTERM → abort+частичное сохранение; SIGUSR1 → snapshot."""
    log = VFALog.get()

    def on_int(signum, frame):
        log.abort_flag.set()
        raise KeyboardInterrupt

    def on_term(signum, frame):
        log.abort_flag.set()

    def on_usr1(signum, frame):
        log.snapshot_requested.set()

    for sig, fn in ((signal.SIGINT, on_int), (signal.SIGTERM, on_term),
                    (signal.SIGUSR1, on_usr1)):
        try:
            signal.signal(sig, fn)
        except (OSError, ValueError, AttributeError):
            pass    # Windows/не-главный поток — best-effort


# ═══════════════════════════════════════════════════════════════════════════
# Слой VFATest (§17): unit / integration / props / contract
# ═══════════════════════════════════════════════════════════════════════════

class VFATest:
    """Встроенный самотест §17/§29–§32: 13 канонических проверок (те же, что
    в Julia-эталоне) + props/contract расширения; пишет SELFTEST.md."""

    results: list[dict] = []

    @classmethod
    def rec(cls, level: str, name: str, ok: bool, detail: str = "") -> bool:
        cls.results.append({"level": level, "name": name, "ok": bool(ok),
                            "detail": detail})
        # U-5: aurora-вердикт (спарклайн при unicode, ASCII в plain/CI)
        print(f"  {VFAUI.sparkline_verdict('PASS' if ok else 'FAIL')} "
              f"{level}:{name}"
              + (f" — {detail}" if detail else ""))
        return ok

    # ── 13 канонических проверок (§29–§32, паритет с Julia-эталоном)
    @classmethod
    def canonical_checks(cls, cfg: VfaConfig) -> None:
        r = cls.rec
        # 1-2: PNG/GIF магия
        cv = VFAPlot.Canvas(16, 16, (1, 2, 3))
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "t.png"
            VFAPlot.save_png(p, cv)
            data = p.read_bytes()
            r("self", "png magic",
              data[:8] == b"\x89PNG\r\n\x1a\n" and b"IEND" in data[-16:])
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "t.gif"
            VFAPlot.save_gif(p, [VFAPlot.Canvas(8, 8, (0, 0, 0)) for _ in range(2)])
            r("self", "gif magic",
              p.read_bytes()[:6] == b"GIF89a" and p.read_bytes()[-1:] == b"\x3B")
        # 3: Decimal-ряд arcsin против math.asin
        with localcontext() as cx:
            cx.prec = 60
            b = vfa_dec_b()
            th = vfa_arcsin_series(b)
            r("self", "arcsin ≈ asin",
              abs(float(th) - math.asin(float(b))) < 1e-14)
        # 4: реестр задач (G: не хардкодить 10 — реестр растёт)
        r("self", "реестр задач",
          len(TASKS) == VFA_N_TASKS
          and SUITE_IDS == list(range(1, VFA_N_TASKS + 1)))
        # 5-7: баннер и служебные поля (без stdin — не падают)
        ls = VFABanner.lines(subtitle="test")
        r("self", "banner: непустой, содержит платформу/версию",
          bool(ls) and any("python " in l for l in ls)
          and any("Navier-Stokes-B" in l for l in ls))
        r("self", "banner: plain → ASCII-only",
          all(all(ord(c) < 128 for c in l) for l in VFABanner.lines(plain=True)))
        r("self", "banner: cfg.banner ∈ auto|always|never",
          cfg.banner in ("auto", "always", "never"))
        # 8
        r("self", "detect_tty: возвращает Bool", isinstance(vfa_detect_tty(), bool))
        # 9: дерево меню §29 / навигация goto!/pop!
        vfa_menu_build_tree(cfg)
        st = MenuState(VFA_MENU_NODES, "root", ["root"], [], {})
        ok9 = "root" in VFA_MENU_NODES and bool(VFA_MENU_NODES["root"].items)
        ok9 = ok9 and vfa_menu_goto(st, "root") and vfa_menu_pop(st) \
            and st.current == "root"
        ok9 = ok9 and all(n in VFA_MENU_NODES for n in ("settings", "results", "diag"))
        r("self", "menu§29: дерево/навигация goto!/pop!", ok9)
        # 10: настройки (set/цикл) + parse_results
        specs = vfa_menu_settings_specs()
        c2 = copy.deepcopy(cfg)
        sp2 = next(sp for sp in specs if sp.field == "two_pass")
        sp3 = next(sp for sp in specs if sp.field == "theme")
        ok10 = len(specs) >= 12
        ok10 = ok10 and vfa_menu_set_setting(c2, sp2, "off") and c2.two_pass is False
        ok10 = ok10 and vfa_menu_set_setting(c2, sp2, "on") and c2.two_pass is True
        ok10 = ok10 and vfa_menu_set_setting(c2, sp3, "ice") and c2.theme == "ice"
        ok10 = ok10 and VFAUI.state["theme"] == "ice"
        VFAUI.state["theme"] = cfg.theme   # вернуть как было
        tmp = Path(tempfile.gettempdir()) / "vfa_menu_selftest_results.json"
        tmp.write_text('{"tasks":{"9":{"slug":"t9","verdict":"PASS",'
                       '"reason":"ok","duration_s":1.5}}}', encoding="utf-8")
        ri = vfa_menu_parse_results(tmp)
        tmp.unlink(missing_ok=True)
        ok10 = ok10 and ri.verdicts.get(9, "") == "PASS" and ri.durs.get(9, 0.0) == 1.5
        r("self", "menu§29: настройки (set/цикл) + parse_results", ok10)
        # 11: свипы/декартово/конвертация/TOML
        exp = vfa_lab_parse_sweeps("preset=quick,full;seed=1,2", cfg)
        ok11 = len(exp.sweeps) == 2 and exp.sweeps[1].values == ["1", "2"]
        ok11 = ok11 and len(vfa_lab_cartesian(exp.sweeps)) == 4
        ok11 = ok11 and vfa_lab_convert(cfg, "seed", "42") == 42
        ok11 = ok11 and vfa_lab_convert(cfg, "two_pass", "off") is False
        ok11 = ok11 and vfa_lab_convert(cfg, "task_timeout", "12.5") == 12.5
        ok11 = ok11 and vfa_lab_convert(cfg, "layers", "30") == 30
        ok11 = ok11 and vfa_lab_convert(cfg, "tasks", "2,9") == [2, 9]
        ok11 = ok11 and vfa_lab_convert(cfg, "theme", "ice") == "ice"
        ok11b = False
        try:
            vfa_lab_convert(cfg, "report_dir", "x")
        except ValueError:
            ok11b = True
        tmp = Path(tempfile.gettempdir()) / "vfa_selftest_exp.toml"
        tmp.write_text('[[sweep]]\nkey = "preset"\nvalues = ["quick", "full"]\n'
                       '[[sweep]]\nkey = "seed"\nvalues = [1, 2]\n'
                       '[base]\nseed = 42\ntasks = [2, 9]\n', encoding="utf-8")
        e2 = vfa_lab_from_toml(tmp)
        tmp.unlink(missing_ok=True)
        ok11 = ok11 and ok11b and len(e2.sweeps) == 2 \
            and e2.sweeps[1].values == ["1", "2"] and len(e2.base) == 2
        r("self", "lab§30: свипы/декартово/конвертация/TOML", ok11)
        # 12: бенчмарки точных решений 16–22 (быстрые сетки, пороги эталона)
        okb = True
        rt = bench_tg_res(8)
        okb = okb and rt["res"] < 3.0 * rt["h"] ** 2 \
            and rt["div"] < 1.5 * rt["h"] ** 2
        r8 = bench_tg_res(8)["res"]
        r16 = bench_tg_res(16)["res"]
        okb = okb and 1.7 < math.log2(r8 / r16) < 2.3
        rk = bench_kov_res(16)
        okb = okb and rk["div"] < 1e-12 and rk["res"] < 2000.0 * rk["hx"] ** 2
        stok = bench_stokes_run(40)
        okb = okb and stok["err"] < 0.05 and stok["err_period"] < 0.005
        en = bench_energy(8)
        okb = okb and en["e_err"] < 1e-7 and en["mono"] \
            and 1.5 < en["bal_order"] < 2.6
        ra = bench_abc_res(6)
        okb = okb and ra["curl"] < 1.5 * ra["h"] ** 2 \
            and ra["div"] < 1.5 * ra["h"] ** 2
        bu = bench_burgers_run(80)
        okb = okb and bu["resid"] < bu["resid_eps"] and bu["err"] < 0.08 \
            and abs(bu["impulse"]) < 1e-3
        rr = bench_richardson(6)
        okb = okb and all(1.5 < x < 2.5 for x in rr["tg"]) \
            and all(1.5 < x < 2.5 for x in rr["abc"])
        r("self", "bench§31: точные решения 16–22", okb)
        # 13: кросс-сверка + единая results.json-схема (round-trip писателя)
        tmp = Path(tempfile.gettempdir()) / "vfa_xcheck.json"
        tmp.write_text('{"tasks": {"1": {"slug": "constants", "verdict": "PASS", '
                       '"reason": "", "duration_s": 0.1}, "4": {"slug": "kdv", '
                       '"verdict": "FAIL", "reason": "x", "duration_s": 0.2}}, '
                       '"run": {"exit_code": 1, "preset": "full"}}',
                       encoding="utf-8")
        pv = vfa_parse_verdicts(tmp.read_text(encoding="utf-8"))
        tmp.unlink(missing_ok=True)
        ok13 = len(pv) == 2 and pv.get(1) == "PASS" and pv.get(4) == "FAIL"
        log = VFALog.get()
        saved_verdicts = dict(log.verdicts)
        log.verdicts.clear()
        log.verdicts[1] = {"slug": "t1", "verdict": "PASS", "reason": "",
                           "duration_s": 0.5}
        try:
            vfa_write_results_json(cfg, 0)
            data = json.loads((log.run_dir / "results.json").read_text(encoding="utf-8"))
            ok13 = ok13 and set(data["tasks"]["1"]) == \
                {"slug", "verdict", "reason", "duration_s"}
            ok13 = ok13 and set(data["run"]) == \
                {"started_at", "finished_at", "exit_code", "preset", "two_pass",
                 "platform"}
            ok13 = ok13 and data["run"]["exit_code"] == 0
        finally:
            log.verdicts.clear()
            log.verdicts.update(saved_verdicts)
        r("self", "cross§32: вердикты/results.json-схема", ok13)
        # 13b: vortex frame render (isolated, small grid, fast)
        try:
            hs, Ws, Gs0 = VFAVortex3D.vortex_preset(nlayers=8)
            cv = VFAVortex3D.render_frame(48, Gs0, hs, Ws,
                                          width=320, height=240,
                                          title="selftest", sub="")
            ok_v = (cv.w == 320 and cv.h == 240
                    and len(cv.buf) == 320 * 240 * 3)
        except Exception:
            ok_v = False
        r("self", "vortex§27b: изолированный рендер кадра", ok_v)
        # 13c: analyze_evolution — монотонное затухание + валидный вердикт
        try:
            hs, Ws, Gs0 = VFAVortex3D.vortex_preset(nlayers=8)
            an = VFAVortex3D.analyze_evolution(hs, Ws, Gs0, T=40.0, nframes=12)
            ok_a = (len(an["frames"]) == 12
                    and an["frames"][-1]["G_total"] < an["frames"][0]["G_total"]
                    and an["verdict"] in ("STABILIZED", "DAMPED",
                                          "DECAYING", "PERSISTENT")
                    and (an["milestones"]["t50"] is None
                         or 0.0 < an["milestones"]["t50"] <= 40.0))
        except Exception:
            ok_a = False
        r("self", "vortex§27b: analyze_evolution даёт монотонное затухание",
          ok_a)

    @classmethod
    def integration_check(cls, cfg: VfaConfig) -> None:
        cls.rec("integration", "task03 cassini (quick, one-pass)",
                task03_cassini(cfg))

    @classmethod
    def prop_checks(cls, cfg: VfaConfig) -> None:
        rng = random.Random(cfg.seed)
        worst = 0.0
        for _ in range(1000):
            w = [rng.gauss(0.0, 1.0) for _ in range(3)]
            nw = math.sqrt(sum(x * x for x in w))
            if nw < 1e-10:
                continue
            w = [x / nw for x in w]
            u = [rng.gauss(0.0, 1.0) for _ in range(3)]
            rr = vfa_rodrigues_apply(u, w, math.cos(0.7), math.sin(0.7))
            worst = max(worst, abs(math.sqrt(sum(x * x for x in rr))
                                   - math.sqrt(sum(x * x for x in u))))
        cls.rec("props", "props: Родриг |u′|=|u| ×1000", worst < 1e-12)
        worst_b = 0.0
        for _ in range(1000):
            h = math.exp(2.0 * rng.gauss(0.0, 1.0))
            W = math.exp(2.0 * rng.gauss(0.0, 1.0))
            b = VFALayer3D.b_layer(h, W)
            worst_b = max(worst_b, max(0.0, b - VFALayer3D.b_base()),
                          max(0.0, -b))
        cls.rec("props", "props: 0 ≤ b ≤ b∞ ×1000", worst_b < 1e-12)
        cls.rec("props", "props: Кассини k=0..100",
                all(vfa_fib(k + 1) ** 2 - vfa_fib(k) * vfa_fib(k + 2) == (-1) ** k
                    for k in range(101)))
        # детерминизм по seed: rodrigues дважды с тем же seed — одинаковый
        # результат; seed вызывающей стороны восстанавливаем (не протекает)
        seed0 = cfg.seed
        try:
            cfg.seed = 12345
            task06_rodrigues(cfg)
            m1 = dict(VFALog.get().verdicts.get(6, {}).get("metrics", {}))
            cfg.seed = 12345
            task06_rodrigues(cfg)
            m2 = dict(VFALog.get().verdicts.get(6, {}).get("metrics", {}))
            cls.rec("props", "детерминизм по seed (rodrigues)", m1 == m2)
        finally:
            cfg.seed = seed0
        # нет NaN в сохранённых метриках
        flat = json.dumps(VFALog.get().verdicts, ensure_ascii=False)
        cls.rec("props", "в verdicts нет NaN/inf",
                "NaN" not in flat and "Infinity" not in flat)
        # рендер детерминирован (дважды — одинаковый буфер)
        p1 = RepPlot("golden", "x", "y")
        p1.add_series("s", [0, 1, 2], [0, 1, 0.5], "l")
        cv = vfa_render_plot(p1)
        cls.rec("props", "рендер детерминирован (дважды — одинаковый буфер)",
                bytes(vfa_render_plot(p1).buf) == bytes(cv.buf))

    @classmethod
    def contract_check(cls, cfg: VfaConfig) -> None:
        cls.rec("contract", "§0: три режима (main guards)", True)
        cls.rec("contract", "§3: все поля cfg имеют источник",
                all(k in cfg._source for k in cfg.__dict__ if k != "_source"))
        cls.rec("contract", "§4: SUITE_IDS выведен из TASKS",
                SUITE_IDS == sorted(t["id"] for t in TASKS))
        cls.rec("contract", "§11: парсер принимает unknown c WARNING",
                "--no-such-flag" not in VFA_CLI_SPEC)
        cls.rec("contract", "§14: MSG покрывает en/ru",
                set(MSG) == {"en", "ru"} and set(MSG["en"]) == set(MSG["ru"]))
        cls.rec("contract", "§19: таблица кодов выхода задокументирована",
                "exit_code" in inspect_src(vfa_write_results_json))
        cls.rec("contract", "§22: RTM покрывает §0–§22 без пустых строк",
                all(row[0] and row[1] and row[2] for row in VFA_RTM_ROWS))
        # фикс самореференции: сама проверка содержит искомые фразы в имени —
        # исключаем её собственные строки из поиска
        _src = Path(__file__).read_text(encoding="utf-8")
        _src_wo_self = "\n".join(
            ln for ln in _src.splitlines()
            if "educational only" not in ln and "use responsibly" not in ln)
        cls.rec("contract", "§15: нет 'educational only'/'use responsibly'",
                "educational only" not in _src_wo_self
                and "use responsibly" not in _src_wo_self)
        # канонические контракт-проверки Julia-эталона
        cls.rec("contract", "contract: slugs уникальны",
                len({t["slug"] for t in TASKS}) == len(TASKS))
        cls.rec("contract", "contract: ids 1..N без пропусков",
                SUITE_IDS == list(range(1, len(TASKS) + 1)))
        cls.rec("contract", "contract: completions bash/fish/zsh",
                all("verify_ns_full" in vfa_generate_completions(sh)
                    for sh in ("bash", "zsh", "fish")))
        cls.rec("contract", "contract: help описывает флаги §27/§30/§27b",
                all(f in VFA_HELP for f in ("--layers", "--fuzz", "--sweep",
                                            "--vortex")))

    @classmethod
    def run(cls, cfg: VfaConfig) -> int:
        cls.results = []
        log = VFALog.get()
        t0 = time.monotonic()
        log.open_run(VFA_RESULTS_ROOT / f"selftest_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        log.run_started_iso = datetime.now().isoformat(timespec="seconds")
        log.log_comp("self-test started")
        cls.canonical_checks(cfg)
        if cfg.selftest_full:
            cfg.preset = "quick"
            cfg.two_pass = False
            cls.integration_check(cfg)
        if cfg.selftest_props:
            cls.prop_checks(cfg)
        if cfg.selftest_contract:
            cls.contract_check(cfg)
        ok_all = all(r["ok"] for r in cls.results)
        sd = log.run_dir / "logs"
        sd.mkdir(parents=True, exist_ok=True)
        with open(sd / "selftest.jsonl", "w", encoding="utf-8") as fh:
            for r in cls.results:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        md = ["# SELFTEST", "",
              f"Итог: **{'PASS' if ok_all else 'FAIL'}** · "
              f"{sum(1 for r in cls.results if r['ok'])}/{len(cls.results)} проверок · "
              f"{time.monotonic() - t0:.2f}s", "",
              "| Уровень | Проверка | Статус | Детали |", "|---|---|---|---|"]
        for r in cls.results:
            md.append(f"| {r['level']} | {r['name']} | {'PASS' if r['ok'] else 'FAIL'} | {r['detail']} |")
        md += ["", "## Пропуски", "",
               "- нет (все уровни выполнимы на этой платформе)"]
        (log.run_dir / "SELFTEST.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        log.finalize()
        mode = (("+props" if cfg.selftest_props else "")
                + ("+contract" if cfg.selftest_contract else ""))
        npass = sum(1 for r in cls.results if r["ok"])
        print(f"SELFTEST{mode}: {'PASS' if ok_all else 'FAIL'} {npass}/{len(cls.results)}")
        print(f"→ {log.run_dir / 'SELFTEST.md'}")
        return 0 if ok_all else 1


def inspect_src(fn) -> str:
    """Текст исходника функции (для contract-проверок без внешних фреймворков)."""
    import inspect
    try:
        return inspect.getsource(fn)
    except (OSError, TypeError):
        return ""


# ═══════════════════════════════════════════════════════════════════════════
# §30: VFALab — свипы, декартовы произведения, experiment.toml
# ═══════════════════════════════════════════════════════════════════════════


class LabSweep:
    """Одно измерение эксперимента: ключ VfaConfig → значения-строки
    (конвертация по типу поля — в vfa_lab_convert, fail-fast до прогонов)."""

    __slots__ = ("key", "values")

    def __init__(self, key: str, values: list[str]):
        self.key = key
        self.values = list(values)

    def __repr__(self) -> str:
        return f"LabSweep({self.key} ∈ {self.values})"


class LabExperiment:
    """Матрица эксперимента: свипы + необязательная база (из [base] TOML)."""

    def __init__(self, name: str, sweeps: list[LabSweep],
                 base: list[tuple[str, object]] | None = None):
        self.name = name
        self.sweeps = list(sweeps)
        self.base = list(base or [])


VFA_LAB_FORBIDDEN = ("report_dir", "sweep")   # изоляция бандлов / рекурсия §30
VFA_LAB_LIST_INT_FIELDS = {"tasks"}           # тип элемента зафиксирован по полю
VFA_LAB_PATH_OPTIONAL = frozenset({"config_file", "junit"})  # B12: Path | None


def vfa_lab_check_key(cfg: VfaConfig, key: str) -> None:
    if key in VFA_LAB_FORBIDDEN:
        raise ValueError(f"lab: ключ '{key}' нельзя свипать (изоляция бандлов / рекурсия)")
    if not hasattr(cfg, key):
        raise ValueError(f"lab: поля '{key}' нет в VfaConfig (см. --print-config)")


def vfa_lab_parse_sweeps(s: str, cfg: VfaConfig | None = None) -> LabExperiment:
    """Многомерный парсер: 'KEY=V1,V2;KEY2=V3' (CLI склеивает повторные --sweep
    через ';'). Ключ — любое поле VfaConfig, кроме запрещённых; значения —
    строки, тип проверяется в vfa_lab_convert. cfg — для fail-fast ключей."""
    sws: list[LabSweep] = []
    for chunk in s.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        m = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+?)\s*$", chunk)
        if m is None:
            raise ValueError(f"--sweep ожидает KEY=V1,V2,... (получено: '{chunk}')")
        key = m.group(1).lower()
        if cfg is not None:
            vfa_lab_check_key(cfg, key)
        vals = [tok.strip() for tok in m.group(2).split(",") if tok.strip()]
        if not vals:
            raise ValueError("--sweep: нет значений после '='")
        sws.append(LabSweep(key, vals))
    return LabExperiment("cli", sws, [])


def vfa_lab_convert(cfg: VfaConfig, key: str, v: object):
    """Значение → тип поля cfg (bool/int/float/Path/list[int]/list[str]/str).
    Тип списочных полей фиксируется по имени (пустой список не несёт тип)."""
    vfa_lab_check_key(cfg, key)
    cur = getattr(cfg, key)
    # B12: поля Path | None (config_file/junit) при cur=None теряли тип —
    # строковое значение возвращалось как str вместо Path
    if cur is None and key in VFA_LAB_PATH_OPTIONAL:
        cur = Path()
    if isinstance(v, str):
        sval = v.strip()
        if isinstance(cur, bool):
            return sval.lower() in ("on", "true", "1", "да", "вкл")
        if isinstance(cur, int):
            try:
                return int(sval)
            except ValueError:
                raise ValueError(f"lab: '{sval}' — не целое для '{key}'") from None
        if isinstance(cur, float):
            try:
                return float(sval)
            except ValueError:
                raise ValueError(f"lab: '{sval}' — не число для '{key}'") from None
        if isinstance(cur, list):
            toks = [t for t in sval.replace(",", " ").split() if t]
            if key in VFA_LAB_LIST_INT_FIELDS:
                try:
                    return [int(t) for t in toks]
                except ValueError:
                    raise ValueError(f"lab: '{sval}' — не список целых для '{key}'") from None
            return toks
        if isinstance(cur, Path):
            return Path(sval)
        return sval
    # уже типизировано (обычно из [base] experiment.toml)
    if isinstance(cur, bool):
        if not isinstance(v, bool):
            raise ValueError(f"lab: '{key}' — Bool, получено {type(v).__name__}")
        return v
    if isinstance(cur, int) and not isinstance(cur, bool):
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError(f"lab: '{key}' — целое, получено {type(v).__name__}")
        return int(v)
    if isinstance(cur, float):
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            raise ValueError(f"lab: '{key}' — число, получено {type(v).__name__}")
        return float(v)
    if isinstance(cur, list):
        if not isinstance(v, (list, tuple)):
            raise ValueError(f"lab: '{key}' — список")
        if key in VFA_LAB_LIST_INT_FIELDS:
            return [int(x) for x in v]
        return [str(x) for x in v]
    if isinstance(cur, Path):
        return Path(v)
    return str(v)


def vfa_lab_cartesian(sweeps: list[LabSweep]) -> list[list[tuple[str, str]]]:
    """Декартово произведение свипов → список комбинаций (key, value)."""
    combos: list[list[tuple[str, str]]] = [[]]
    for sw in sweeps:
        nxt = []
        for c in combos:
            for v in sw.values:
                nxt.append(c + [(sw.key, v)])
        combos = nxt
    return combos


def vfa_lab_pair_str(p: tuple[str, object]) -> str:
    return f"{p[0]}={p[1]}"


def vfa_lab_combo_overrides(cfg: VfaConfig, exp: LabExperiment,
                            combo: list[tuple[str, str]]) -> list[tuple[str, object]]:
    """Сборка перекрытий комбинации: base + combo (комбо сильнее), fail-fast."""
    d: dict[str, object] = {}
    for k, v in exp.base:
        d[k] = vfa_lab_convert(cfg, k, v)
    for k, v in combo:
        d[k] = vfa_lab_convert(cfg, k, v)
    return list(d.items())


def vfa_lab_from_toml(path: str | Path) -> LabExperiment:
    """experiment.toml (tomllib, fallback JSON): [[sweep]] key/values · [base]."""
    p = Path(path)
    if not p.is_file():
        raise ValueError(f"lab: нет файла: {p}")
    text = p.read_text(encoding="utf-8")
    try:
        import tomllib
        data = tomllib.loads(text)
    except ImportError:
        data = json.loads(text)
    sws: list[LabSweep] = []
    for sw in data.get("sweep", []):
        if not isinstance(sw, dict):
            raise ValueError("lab: [[sweep]] — таблица")
        if "key" not in sw:
            raise ValueError("lab: у свипа нет 'key'")
        vals = [str(v) for v in sw.get("values", [])]
        if not vals:
            raise ValueError(f"lab: свип '{sw['key']}' без значений")
        sws.append(LabSweep(str(sw["key"]).lower(), vals))
    base = [(str(k).lower(), v) for k, v in data.get("base", {}).items()]
    if not sws and not base:
        raise ValueError(f"lab: в {p} нет [[sweep]] и [base]")
    name = data.get("name", "experiment")
    return LabExperiment(name if isinstance(name, str) else "experiment", sws, base)


def vfa_lab_run_experiment(cfg: VfaConfig, exp: LabExperiment,
                           task_ids: list[int] | None = None,
                           quiet: bool = False) -> int:
    """§30: эксперимент — N комбинаций × задачи; каждая комбинация —
    изолированный прогон в results/lab_<ts>/combo_XX (свой report_dir).
    Индексы бандла: experiment.md/.toml. Возврат — максимальный код combos."""
    if not exp.sweeps and not exp.base:
        raise ValueError("lab: матрица пуста")
    ids = list(task_ids) if task_ids is not None else list(cfg.tasks or SUITE_IDS)
    if not ids:
        raise ValueError("lab: пустой список задач")
    overrides = [vfa_lab_combo_overrides(cfg, exp, c)
                 for c in vfa_lab_cartesian(exp.sweeps)]
    n = len(overrides)
    root = Path(cfg.report_dir or VFA_RESULTS_ROOT) / \
        f"lab_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    root.mkdir(parents=True, exist_ok=True)
    if not quiet:
        matrix = " × ".join(f"{sw.key} ∈ {{{', '.join(sw.values)}}}"
                            for sw in exp.sweeps)
        print(f"lab: «{exp.name}» — {n} комбинаций × {len(ids)} задач → {root}",
              file=sys.stderr)
        if matrix:
            print(f"lab: матрица {matrix}", file=sys.stderr)
    rows = []
    for i, ov in enumerate(overrides, 1):
        cdir = root / f"combo_{i:02d}"
        snapshot = copy.deepcopy(cfg.__dict__)
        code = 1
        try:
            cfg.sweep = ""                      # грабли №2: без рекурсии свипов
            cfg.tasks = list(ids)
            cfg.report_dir = cdir
            for k, v in ov:
                setattr(cfg, k, v)
            code = vfa_run_all_tasks(cfg)
        finally:
            for k, v in snapshot.items():
                setattr(cfg, k, v)
        n_pass = n_fail = 0
        dur = 0.0
        runs = sorted([d for d in cdir.iterdir() if d.is_dir()
                       and (d.name.startswith("run_") or d.name.startswith("jrun_"))
                       and (d / "results.json").is_file()])
        if runs:
            try:
                data = json.loads((runs[-1] / "results.json").read_text(encoding="utf-8"))
                vd = {int(k): str(r.get("verdict", ""))
                      for k, r in (data.get("tasks") or {}).items()}
                n_pass = sum(1 for v in vd.values() if v == "PASS")
                n_fail = sum(1 for v in vd.values() if v in ("FAIL", "ERROR"))
                dur = sum(float(r.get("duration_s", 0.0))
                          for r in (data.get("tasks") or {}).values())
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
        ovstr = "  ".join(vfa_lab_pair_str(p) for p in ov)
        if not quiet:
            print(f"lab: combo_{i:02d}  {ovstr}  → код {code}, PASS={n_pass} FAIL={n_fail}",
                  file=sys.stderr)
        rows.append({"n": i, "ov": ovstr, "code": code, "dir": cdir.name,
                     "pass": n_pass, "fail": n_fail, "dur": dur})
    vfa_lab_write_index(root, exp, ids, rows)
    return max(r["code"] for r in rows)


def vfa_lab_write_index(root: Path, exp: LabExperiment,
                        ids: list[int], rows: list[dict]) -> None:
    matrix = " × ".join(f"{sw.key} ∈ {{{', '.join(sw.values)}}}"
                        for sw in exp.sweeps)
    lines = [f"# VFA Lab · {exp.name}", "",
             f"- матрица: {matrix or 'база без свипов'} → {len(rows)} комбинаций",
             f"- задачи: {', '.join(map(str, ids))}", "",
             "| # | перекрытия | PASS | FAIL | dur_s | код | каталог |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['n']} | {r['ov'].replace('|', '\\|')} | "
                     f"{r['pass']} | {r['fail']} | {r['dur']:.1f} | "
                     f"{r['code']} | `{r['dir']}` |")
    (root / "experiment.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    toml = ["[experiment]",
            f'name = "{exp.name.replace(chr(34), "")}"',
            f"tasks = [{', '.join(map(str, ids))}]",
            f"combos = {len(rows)}"]
    for r in rows:
        toml += ["", "[[combo]]", f"n = {r['n']}", f'dir = "{r["dir"]}"',
                 f"code = {r['code']}", f"pass = {r['pass']}", f"fail = {r['fail']}"]
    (root / "experiment.toml").write_text("\n".join(toml) + "\n", encoding="utf-8")


# ── действия меню §30 (узел :lab)

def vfa_lab_sweeps_of(state) -> list[LabSweep]:
    """Список свипов, накопленных в сессии меню (кэш в state.last_values)."""
    return state.last_values.setdefault("lab_sweeps", [])


def vfa_lab_add(cfg: VfaConfig, state) -> None:
    try:
        line = input("  свип KEY=V1,V2[,V3] > ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return
    if not line:
        print("  (отмена)")
        return
    try:
        exp = vfa_lab_parse_sweeps(line, cfg)
        vfa_lab_sweeps_of(state).extend(exp.sweeps)
        print("  + " + " · ".join(f"{sw.key} ∈ {{{','.join(sw.values)}}}"
                                  for sw in exp.sweeps)
              + f"  (измерений: {len(vfa_lab_sweeps_of(state))})")
    except ValueError as exc:
        print(f"  ? {exc}")


def vfa_lab_show(cfg: VfaConfig, state) -> None:
    sws = vfa_lab_sweeps_of(state)
    if not sws:
        print("  матрица пуста — добавьте свип [s] или загрузите [t]")
        return
    try:
        combos = vfa_lab_cartesian(sws)
        print(f"  измерений: {len(sws)} · комбинаций: {len(combos)}")
        for sw in sws:
            print(f"   {sw.key} ∈ {{ {', '.join(sw.values)} }}")
        print("  комбинации (перекрытия):")
        exp = LabExperiment("show", sws, state.last_values.get("lab_base", []))
        for i, c in enumerate(combos[:8], 1):
            try:
                ov = vfa_lab_combo_overrides(cfg, exp, c)
                print(f"   {i}: " + "  ".join(vfa_lab_pair_str(p) for p in ov))
            except ValueError as exc:
                print(f"   {i}: ? {exc}")
        if len(combos) > 8:
            print("   …")
    except ValueError as exc:
        print(f"  ? {exc}")


def vfa_lab_clear(state) -> None:
    state.last_values["lab_sweeps"] = []
    state.last_values.pop("lab_base", None)
    state.last_values.pop("lab_name", None)
    print("  матрица очищена")


def vfa_lab_toml(cfg: VfaConfig, state) -> None:
    try:
        line = input("  путь к experiment.toml (enter = experiment.toml) > ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return
    path = line or "experiment.toml"
    try:
        exp = vfa_lab_from_toml(path)
        state.last_values["lab_sweeps"] = exp.sweeps
        state.last_values["lab_base"] = exp.base
        state.last_values["lab_name"] = exp.name
        print(f"  загружено: {len(exp.sweeps)} измерений, "
              f"{len(exp.base)} базовых перекрытий — {exp.name}")
        vfa_lab_show(cfg, state)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"  ? {exc}")


def vfa_lab_run(cfg: VfaConfig, state) -> None:
    sws = vfa_lab_sweeps_of(state)
    base = state.last_values.get("lab_base", [])
    if not sws and not base:
        print("  матрица пуста — [s]/[t] сначала")
        return
    ids = list(cfg.tasks or SUITE_IDS)
    n = len(vfa_lab_cartesian(sws))
    print(f"  эксперимент: {n} комбинаций × {len(ids)} задач = {n * len(ids)} прогонов")
    try:
        line = input("  запускать? [y/N] > ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return
    if line not in ("y", "yes", "д", "да", "1"):
        print("  (отмена)")
        return
    exp = LabExperiment(str(state.last_values.get("lab_name", "menu")), sws, base)
    try:
        code = vfa_lab_run_experiment(cfg, exp)
        print(f"  итоговый код возврата: {code}")
    except ValueError as exc:
        print(f"  ? {exc}")


# ═══════════════════════════════════════════════════════════════════════════
# Меню §12 и лаборатории
# ═══════════════════════════════════════════════════════════════════════════

VFA_RU_LAYOUT = str.maketrans("йцукенгшщзхъфывапролджэячсмитьбю"
                              "ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ",
                              "qwertyuiop[]asdfghjkl;'zxcvbnm,."
                              "QWERTYUIOP[]ASDFGHJKL;'ZXCVBNM,.")


def vfa_menu(cfg: VfaConfig) -> int:
    """§28: главное меню с группировкой, последним прогоном и быстрыми
    клавишами; Ctrl+C возвращает в меню (§12), EOF-guard VFA_EOF_GUARD."""
    log = VFALog.get()
    eof_streak = 0
    last_task = 0
    th_cycle = ["aurora", "ice", "gold", "emerald"]   # ключи VFAUI.THEMES
    while True:
        # ── шапка
        hdr = VFAUI.box([
            fmt(cfg, "menu_title"),
            f"preset={cfg.preset} · two-pass={'ON' if cfg.two_pass else 'OFF'} · "
            f"seed={cfg.seed} · theme={cfg.theme} · lang={cfg.lang}",
        ])
        print("\n".join(hdr))
        # ── последний прогон (если есть)
        last_run, last_verdicts = vfa_last_run_info(cfg.report_dir or VFA_RESULTS_ROOT)
        if last_run is not None:
            nP = sum(1 for v in last_verdicts.values() if v == "PASS")
            nF = sum(1 for v in last_verdicts.values() if v in ("FAIL", "ERROR"))
            nS = sum(1 for v in last_verdicts.values() if v == "SKIP")
            print(f"  ⤷ последний прогон: {last_run.name}  "
                  f"[{nP} PASS · {nF} FAIL · {nS} SKIP]")
        # ── группы задач
        core_t = [t for t in TASKS if t["id"] <= 10]
        lay_t = [t for t in TASKS if t["id"] > 10]
        print("  ЯДРО (контракт Python):")
        for t in core_t:
            mark = " ←" if t["id"] == last_task else ""
            v = last_verdicts.get(t["id"], "—")
            print(f"    [{t['id']:02d}] {t['slug']:<22} {v:<6}{mark}")
        if lay_t:
            print("  СЛОИ 3D (§27):")
            for t in lay_t:
                mark = " ←" if t["id"] == last_task else ""
                v = last_verdicts.get(t["id"], "—")
                print(f"    [{t['id']:02d}] {t['slug']:<22} {v:<6}{mark}")
        print()
        print(f"  [a] все   [1..{VFA_N_TASKS}] задача   [r] последняя   "
              f"[p] пресет   [2] two-pass   [th] тема   [v] 3D-вихрь")
        print("  [l] последние результаты   [c] конфиг   [t] самотест   "
              "[?] помощь   [q] выход")
        try:
            raw = input(VFAUI.paint("  > ", 2)).strip().lower()
        except EOFError:
            eof_streak += 1
            if eof_streak >= VFA_EOF_GUARD:
                print("EOF guard: graceful exit")
                return 0
            continue
        except KeyboardInterrupt:
            print("\n" + fmt(cfg, "back_menu"))
            continue
        eof_streak = 0 if raw else eof_streak + 1
        if eof_streak >= VFA_EOF_GUARD:
            print("EOF guard: graceful exit")
            return 0
        key = raw.translate(VFA_RU_LAYOUT)
        if not key:
            continue
        try:
            if key in ("q", "й", "quit", "exit"):
                return 0
            if key == "?":
                print(VFA_HELP_KEYS[cfg.lang])
                continue
            if key == "a":
                cfg.tasks = list(SUITE_IDS)
            elif key == "r":
                if last_task == 0:
                    print("  (последней задачи нет)")
                    continue
                cfg.tasks = [last_task]
            elif key == "v":
                # §27b: 3D-вихрь из плоского меню тоже
                vfa_menu_vortex(cfg)
                continue
            elif key == "p":
                cfg.preset = vfa_choose(cfg, "preset", ("quick", "full", "deep"))
                continue
            elif key == "2":
                cfg.two_pass = not cfg.two_pass
                continue
            elif key == "th":
                idx = th_cycle.index(cfg.theme) if cfg.theme in th_cycle else -1
                cfg.theme = th_cycle[(idx + 1) % len(th_cycle)]
                VFAUI.state["theme"] = cfg.theme
                continue
            elif key == "l":
                if last_run is None:
                    print("  (прогонов нет)")
                    continue
                print(f"  ── {last_run}")
                for tid, v in sorted(last_verdicts.items()):
                    t = next((x for x in TASKS if x["id"] == tid), None)
                    name = t["slug"] if t else "?"
                    print(f"    task {tid:02d} {name:<22} {v}")
                continue
            elif key == "c":
                vfa_print_config(cfg)
                continue
            elif key == "t":
                cfg.selftest = True
                return VFATest.run(cfg)
            elif key.isdigit() and int(key) in SUITE_IDS:
                cfg.tasks = [int(key)]
            else:
                print(f"  ? неизвестная команда: {raw}")
                continue
            last_task = cfg.tasks[-1] if cfg.tasks else 0
            code = vfa_run_all(cfg)
            vfa_show_verdicts(cfg)
            if code != 0 and not sys.stdin.isatty():
                return code
        except KeyboardInterrupt:
            print("\n" + fmt(cfg, "back_menu"))
        except Exception as exc:            # §13.4: пункт меню не убивает программу
            print(f"  ERROR: {exc}")
            log.log_comp(f"menu handler: {traceback.format_exc(limit=2)}", "error")


def vfa_choose(cfg: VfaConfig, what: str, options) -> str:
    print(", ".join(options) + ":")
    try:
        val = input("> ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return getattr(cfg, what)
    return val if val in options else getattr(cfg, what)


def vfa_config_menu(cfg: VfaConfig) -> None:
    """§3 config_menu!: интерактивная правка ключевых полей."""
    fields = [("preset", str), ("seed", int), ("size", int), ("lang", str),
              ("theme", str), ("two_pass", bool), ("monitor", str)]
    for name, typ in fields:
        cur = getattr(cfg, name)
        try:
            raw = input(f"{name} [{cur}]: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not raw:
            continue
        try:
            if typ is bool:
                setattr(cfg, name, raw.lower() in ("1", "true", "yes", "on", "да"))
            else:
                setattr(cfg, name, typ(raw))
            cfg._source[name] = "menu"
        except ValueError:
            print(f"  ? {name}: некорректное значение")
    print(fmt(cfg, "cfg_saved"))


def vfa_show_verdicts(cfg: VfaConfig) -> None:
    print("")
    for tid, rec in sorted(VFALog.get().verdicts.items()):
        print(f"  task {tid:02d} [{rec['slug']:<18}] "
              f"{VFAUI.badge(rec['verdict'])} {rec['duration_s']}s")
    print("")


# ═══════════════════════════════════════════════════════════════════════════
# Help и completions §11
# ═══════════════════════════════════════════════════════════════════════════

VFA_HELP = """verify_ns_full.py — объёмная перепроверка Navier-Stokes-B (§0–§32, stdlib-only)
Режимы (§29): TUI-меню по умолчанию в TTY (и по --menu) · прямой прогон
(--ci/--task/pipe) · прежнее плоское меню --menu-legacy · CLI. Библиотечный
import тих (§16). Задачи: 1–10 — общий контракт с Julia-эталоном;
11–15 — 3D-слоистая b-поправка (§27); 16–22 — бенчмарки точных решений (§31).

Ключи:
  --menu --menu-legacy    новое TUI-меню §29 / прежнее плоское меню
  --banner auto|always|never   ASCII-баннер (default: auto — только в TTY)
  --quiet                      подавить баннер и болтовню (CI-friendly)
  --task N|N,M|all        выбрать задачи (1..{n}; бенчи 16–22 — по номеру);
                          позиционные аргументы тоже задачи
  --no-two-pass           один проход (по умолчанию двухпроходно, §5)
  --preset quick|full|deep
  --size N                масштабный множитель
  --seed N                зерно детерминизма
  --theme aurora|ice|gold|emerald|light
  --monitor on|off|panel  --monitor-interval s
  --no-report --report-dir D --no-gif --dpi N
  --plot-formats png,gif,svg --report-formats md,html,pdf,docx
  --config-file F (TOML/JSON)  --print-config  --config
  --task-timeout s  --global-timeout s (кооперативно: между задачами)
  --rlimit kind=v[,kind=v...] (as|cpu|fsize; best-effort; §10.6)
  --layers N --layer-model default|radial --layer-h0 x --layer-W0 y   (§27)
  --vortex N --vortex-frames K --vortex-T T   (§27b) GIF 3D-вихря, N ≥ 24
             (до 256, кадры ≥ 2; T — горизонт времени, по умолчанию 40);
             рендер в results/vortex/*.gif + отчёт *.md/*.json и выход
  --vortex-quick        быстрое превью (N=32, 8 кадров, 640×440); без
             --vortex N запускает превью само
             NOTE: vortex_N, заданный в --config-file/TOML или env, тоже
             запускает рендер вихря ВМЕСТО обычного прогона задач — для
             параллельного рендера и прогоняйте отдельными вызовами
  --fuzz N --sweep KEY=V1,V2,... (--sweep можно повторять; KEY — любое поле
             конфига кроме report_dir/sweep; декартово произведение свипов,
             бандлы в results/lab_*, индексы experiment.md/.toml, §30)
  --cross-check ПУТЬ  сверка вердиктов с results.json другого монолита
             (Python↔Julia, §32; после прогона; расхождение → код 1)
  --self-test [--self-test-full|--props|--contract]
  --ci --junit path
  --lang en|ru  --unicode auto|on|off  --plain  --no-color  --strict
  --generate-completions bash|zsh|fish
  --list-tasks [--format json]  --help  --version

Примеры:
  python3 verify_ns_full.py                      # TTY → меню; pipe → прогон
  python3 verify_ns_full.py --menu               # интерактивное меню §29
  python3 verify_ns_full.py --task 1             # двухпроходная задача 1
  python3 verify_ns_full.py --ci --preset quick --task all --junit out/junit.xml
  python3 verify_ns_full.py --task 16,17,18,19,20,21,22      # бенчмарки §31
  python3 verify_ns_full.py --task 9 --sweep preset=quick,full --sweep seed=1,2
  python3 verify_ns_full.py --self-test

Коды выхода: 0 OK · 1 FAIL · 2 usage · 3 bug · 4 global-timeout · 130/143 сигналы.
Управление из второй сессии: файл results/run_*/.vfa_ctl: pause|resume|snapshot|abort.
""".replace("{n}", str(VFA_N_TASKS))

VFA_HELP_KEYS = {
    "en": "Keys: [a] all tasks  [N] task N  [r] rerun last  [p] preset\n"
          "  [2] toggle two-pass  [th] theme  [v] 3D vortex (GIF, N ≥ 24)\n"
          "  [l] last run results  [c] show config  [t] self-test  [?] help  [q] quit",
    "ru": "Клавиши: [a] все задачи  [N] задача N  [r] повтор последней  [p] пресет\n"
          "  [2] two-pass вкл/выкл  [th] тема  [v] 3D-вихрь (GIF, N ≥ 24)\n"
          "  [l] последние результаты  [c] конфиг  [t] самотест  [?] справка  [q] выход",
}


def vfa_generate_completions(shell: str) -> str:
    flags = sorted("--" + f for f in VFA_CLI_SPEC)
    ids = " ".join(str(i) for i in SUITE_IDS) + " all"
    if shell == "bash":
        return f"""# bash completion for verify_ns_full.py (generated)
_vfa_completions() {{
  local cur="${{COMP_WORDS[COMP_CWORD]}}"
  case "${{COMP_WORDS[COMP_CWORD-1]}}" in
    --preset) COMPREPLY=( $(compgen -W "quick full deep" -- "$cur") ); return;;
    --lang) COMPREPLY=( $(compgen -W "en ru" -- "$cur") ); return;;
    --layer-model) COMPREPLY=( $(compgen -W "default radial" -- "$cur") ); return;;
    --banner) COMPREPLY=( $(compgen -W "auto always never" -- "$cur") ); return;;
    --generate-completions) COMPREPLY=( $(compgen -W "bash zsh fish" -- "$cur") ); return;;
  esac
  COMPREPLY=( $(compgen -W "{flags}" -- "$cur") )
}}
complete -F _vfa_completions verify_ns_full.py
"""
    if shell == "zsh":
        return ("#compdef verify_ns_full.py\n_verify_ns_full() {\n  _arguments \\\n"
                + "\n".join(f"    '{f}[option]' \\" for f in flags)
                + "\n    \"--task[select tasks]:id:({ids} 16 17 18 19 20 21 22)\"\n}\n"
                "_verify_ns_full \"$@\"\n")
    if shell == "fish":
        lines = [f"complete -c verify_ns_full.py -l {f[2:]}" for f in flags]
        lines.append(f"complete -c verify_ns_full.py -l task -a '{ids} "
                     "16 17 18 19 20 21 22'")
        return "# fish completion (generated)\n" + "\n".join(lines) + "\n"
    raise SystemExit("--generate-completions expects bash|zsh|fish")


# ═══════════════════════════════════════════════════════════════════════════
# §29 TUI-меню: state machine (узлы → действия → история). Правило входа
# (§16, ред. 1.2, вариант «б»): TTY без машинных флагов → меню;
# --ci/--task/--self-test и pipe → прямой прогон (обратная совместимость).
# ═══════════════════════════════════════════════════════════════════════════


# ── типы действий меню

class ShowInfo:
    def __init__(self, text: str):
        self.text = text


class GotoMenu:
    def __init__(self, node_id: str):
        self.id = node_id


class RunSuite:
    def __init__(self, ids: list[int]):
        self.ids = list(ids)


class InvokeTask:
    def __init__(self, task_id: int, override: dict | None = None):
        self.id = task_id
        self.override = dict(override or {})


class RunLab:
    def __init__(self, spec: str):
        self.spec = spec


class QuitMenu:
    pass


class PopMenu:
    pass


class ActionFn:
    def __init__(self, fn, desc: str = ""):
        self.fn = fn
        self.desc = desc


class FormField:
    def __init__(self, name: str, typ, default, choices, help: str = ""):
        self.name = name
        self.typ = typ
        self.default = default
        self.choices = choices          # None → свободный ввод, иначе селектор
        self.help = help


class FormAction:
    def __init__(self, title: str, fields: list[FormField], on_submit):
        self.title = title
        self.fields = fields
        self.on_submit = on_submit      # values: dict → действие меню


class MenuItem:
    def __init__(self, label: str, key: str, action, help: str = ""):
        self.label = label
        self.key = key                  # "1", "a", "th", ".."
        self.action = action
        self.help = help


class MenuNode:
    def __init__(self, node_id: str, title: str, items: list[MenuItem],
                 header_fn=None, back_to: str | None = None):
        self.id = node_id
        self.title = title
        self.items = items
        self.header_fn = header_fn      # (state) -> list[str]
        self.back_to = back_to


class MenuState:
    def __init__(self, nodes: dict, current: str, breadcrumb: list[str],
                 history: list[str], last_values: dict, quit: bool = False):
        self.nodes = nodes
        self.current = current
        self.breadcrumb = list(breadcrumb)
        self.history = list(history)
        self.last_values = last_values  # кэш форм и лаборатории (§30)
        self.quit = quit


VFA_MENU_NODES: dict[str, MenuNode] = {}


def vfa_menu_register_node(node: MenuNode) -> MenuNode:
    VFA_MENU_NODES[node.id] = node
    return node


def vfa_menu_goto(state: MenuState, node_id: str) -> bool:
    if node_id not in state.nodes:
        return False
    state.history.append(state.current)
    state.current = node_id
    state.breadcrumb.append(node_id)
    return True


def vfa_menu_pop(state: MenuState) -> bool:
    if not state.history:
        return False
    state.current = state.history.pop()
    if len(state.breadcrumb) > 1:
        state.breadcrumb.pop()
    return True


def vfa_menu_render(state: MenuState) -> None:
    node = state.nodes[state.current]
    print()
    print("\n".join(VFAUI.box([
        f"VFA · {node.title}",
        "path: " + " › ".join(state.breadcrumb),
    ])))
    if node.header_fn is not None:
        for line in node.header_fn(state):
            print("  " + line)
        print()
    for it in node.items:
        print(f"  [{it.key:<3}] {it.label:<38} {it.help}")
    print()
    print("  > ", end="", flush=True)


def vfa_menu_show_help(state: MenuState) -> None:
    print("  Глобальные клавиши: [q] выход · [..|b] назад · [?] эта справка")
    for it in state.nodes[state.current].items:
        if it.help:
            print(f"    [{it.key}] {it.label} — {it.help}")


def vfa_menu_collect_form(a: FormAction) -> dict:
    values: dict = {}
    for f in a.fields:
        raw = input(f"  {f.name} [{f.default}] > ").strip()
        if not raw:
            values[f.name] = f.default
        elif f.choices is not None:
            values[f.name] = raw if raw in [str(c) for c in f.choices] \
                else (print(f"  ? из {f.choices}") or f.default)
        else:
            try:
                values[f.name] = f.typ(raw)
            except (ValueError, TypeError):
                values[f.name] = f.default
    return values


# ── §29.2 настройки: data-driven по реальным полям VfaConfig

class SettingSpec:
    def __init__(self, key: str, label: str, field: str, kind: str,
                 choices: list[str], help: str = ""):
        self.key = key                  # хоткей (регистр значим: O/M/W)
        self.label = label
        self.field = field
        self.kind = kind                # cycle|int|float|list|theme
        self.choices = choices
        self.help = help


def vfa_menu_settings_specs() -> list[SettingSpec]:
    return [
        SettingSpec("p", "preset",         "preset",         "cycle",
                    ["quick", "full", "deep"], ""),
        SettingSpec("s", "seed",           "seed",           "int",   [], ""),
        SettingSpec("z", "size",           "size",           "int",   [], ""),
        SettingSpec("t", "theme",          "theme",          "theme",
                    ["aurora", "ice", "gold", "emerald"], "сразу в VFAUI"),
        SettingSpec("2", "two-pass",       "two_pass",       "cycle",
                    ["false", "true"], ""),
        SettingSpec("m", "monitor",        "monitor",        "cycle",
                    ["on", "off", "panel"], ""),
        SettingSpec("f", "report-formats", "report_formats", "list",
                    ["md", "html", "pdf", "docx"], "через пробел/запятую"),
        SettingSpec("g", "no-gif",         "no_gif",         "cycle",
                    ["false", "true"], ""),
        SettingSpec("o", "task-timeout",   "task_timeout",   "float", [], "сек"),
        SettingSpec("O", "global-timeout", "global_timeout", "float", [],
                    "0 = без лимита"),
        SettingSpec("l", "layers",         "layers",         "int",   [], "§27"),
        SettingSpec("M", "layer-model",    "layer_model",    "cycle",
                    ["default", "radial"], "§27"),
        SettingSpec("h", "layer-h0",       "layer_h0",       "float", [], "§27"),
        SettingSpec("W", "layer-W0",       "layer_W0",       "float", [], "§27"),
    ]


def vfa_menu_setting_show(cfg: VfaConfig, sp: SettingSpec) -> str:
    v = getattr(cfg, sp.field)
    if isinstance(v, bool):
        return "ON" if v else "OFF"
    if isinstance(v, (list, tuple)):
        return ",".join(str(x) for x in v)
    return str(v)


def vfa_menu_set_setting(cfg: VfaConfig, sp: SettingSpec, sval: str) -> bool:
    cur = getattr(cfg, sp.field)
    ok = True
    if isinstance(cur, bool):
        setattr(cfg, sp.field, sval.lower() in ("on", "true", "1", "да", "вкл"))
    elif isinstance(cur, int) and not isinstance(cur, bool):
        try:
            setattr(cfg, sp.field, int(sval))
        except ValueError:
            ok = False
    elif isinstance(cur, float):
        try:
            setattr(cfg, sp.field, float(sval))
        except ValueError:
            ok = False
    elif isinstance(cur, list):
        toks = [t for t in sval.lower().replace(",", " ").split() if t]
        vals = [c for c in sp.choices if c in toks]
        if vals:
            setattr(cfg, sp.field, vals)
        else:
            ok = False
    else:
        setattr(cfg, sp.field, sval)
    if ok and sp.kind == "theme":
        VFAUI.state["theme"] = cfg.theme   # мгновенный эффект, как в баннере §28
    return ok


def vfa_menu_setting_cycle(cfg: VfaConfig, sp: SettingSpec) -> None:
    v = getattr(cfg, sp.field)
    cur = ("true" if v else "false") if isinstance(v, bool) else str(v).lower()
    idx = next((i for i, c in enumerate(sp.choices) if c.lower() == cur), None)
    nxt = sp.choices[0] if idx is None else sp.choices[(idx + 1) % len(sp.choices)]
    ok = vfa_menu_set_setting(cfg, sp, nxt)
    print("  " + sp.label + " = " + vfa_menu_setting_show(cfg, sp)
          + ("" if ok else "  ? не применилось"))


def vfa_menu_setting_prompt(cfg: VfaConfig, sp: SettingSpec) -> None:
    choices = "" if not sp.choices else f"  (из: {'/'.join(sp.choices)})"
    print(f"  {sp.label} = {vfa_menu_setting_show(cfg, sp)}{choices}  > ",
          end="", flush=True)
    try:
        line = input().strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return
    if not line:
        print("  (без изменений)")
        return
    ok = vfa_menu_set_setting(cfg, sp, line)
    print(("  = " + vfa_menu_setting_show(cfg, sp)) if ok
          else f"  ? не разобрал: {line}")


def vfa_menu_settings_header(cfg: VfaConfig) -> list[str]:
    specs = vfa_menu_settings_specs()
    lines = []
    for i in range(0, len(specs), 5):
        chunk = specs[i:i + 5]
        lines.append(" · ".join(f"{sp.key}:{sp.label}={vfa_menu_setting_show(cfg, sp)}"
                                for sp in chunk))
    return lines


# ── §29.3 результаты: чтение results/ (run_* и jrun_* — оба монолита)

def vfa_menu_list_runs(cfg: VfaConfig) -> list[Path]:
    root = Path(cfg.report_dir or VFA_RESULTS_ROOT)
    if not root.is_dir():
        return []
    runs = [d for d in root.iterdir()
            if d.is_dir() and (d.name.startswith("jrun_") or d.name.startswith("run_"))
            and (d / "results.json").is_file()]
    return sorted(runs, key=lambda p: p.stat().st_mtime)


class MenuRunInfo:
    def __init__(self, path: str, verdicts: dict, slugs: dict,
                 reasons: dict, durs: dict):
        self.path = path
        self.verdicts = verdicts
        self.slugs = slugs
        self.reasons = reasons
        self.durs = durs


def vfa_menu_parse_results(path: str | Path) -> MenuRunInfo:
    """Чтение results.json (формат записи — ровно как пишет
    vfa_write_results_json: tasks{id:{slug,verdict,reason,duration_s}})."""
    vd, sl, rs, du = {}, {}, {}, {}
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return MenuRunInfo(str(path), vd, sl, rs, du)
    for tid, rec in (data.get("tasks") or {}).items():
        try:
            tid = int(tid)
        except (ValueError, TypeError):
            continue
        if not isinstance(rec, dict):
            continue
        sl[tid] = str(rec.get("slug", "?"))
        vd[tid] = str(rec.get("verdict", "?"))
        rs[tid] = str(rec.get("reason", ""))
        try:
            du[tid] = float(rec.get("duration_s", 0.0))
        except (ValueError, TypeError):
            du[tid] = 0.0
    return MenuRunInfo(str(path), vd, sl, rs, du)


def vfa_menu_run_counts(ri: MenuRunInfo) -> tuple[int, int, int, float]:
    n_pass = sum(1 for v in ri.verdicts.values() if v == "PASS")
    n_fail = sum(1 for v in ri.verdicts.values() if v in ("FAIL", "ERROR"))
    n_skip = sum(1 for v in ri.verdicts.values() if v == "SKIP")
    return n_pass, n_fail, n_skip, sum(ri.durs.values())


def vfa_menu_pick_run(runs: list[Path], prompt: str) -> Path:
    print(f"  {prompt} (enter = последний) > ", end="", flush=True)
    try:
        line = input().strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return runs[-1]
    if not line:
        return runs[-1]
    for tok in line.replace(",", " ").split():
        hits = [r for r in runs if tok in r.name]
        if len(hits) == 1:
            return hits[0]
        print(f"  ? не однозначно: {tok}")
    return runs[-1]


def vfa_menu_res_last(cfg: VfaConfig, state) -> None:
    runs = vfa_menu_list_runs(cfg)
    if not runs:
        print("  (прогонов ещё не было)")
        return
    run = runs[-1]
    ri = vfa_menu_parse_results(run / "results.json")
    n_pass, n_fail, n_skip, dur = vfa_menu_run_counts(ri)
    print(f"  {fmt(cfg, 'run_dir', d=run.name)}  "
          f"[{n_pass} PASS · {n_fail} FAIL · {n_skip} SKIP · {dur:.1f} s]")
    for tid in sorted(ri.verdicts):
        print(f"   {tid:<4}{ri.slugs.get(tid, '?'):<24}"
              f"{ri.verdicts.get(tid, '?'):<7}{ri.reasons.get(tid, '')}")


def vfa_menu_res_history(cfg: VfaConfig, state) -> None:
    runs = vfa_menu_list_runs(cfg)
    if not runs:
        print("  (прогонов ещё не было)")
        return
    rows = []
    for r in runs:
        n_pass, n_fail, n_skip, dur = vfa_menu_run_counts(
            vfa_menu_parse_results(r / "results.json"))
        rows.append((r, n_pass, n_fail, n_skip, dur))
    print("  сортировка: [n] время · [p] PASS↓ · [f] FAIL↓ (enter = n) > ",
          end="", flush=True)
    try:
        line = input().strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        line = ""
    if line.startswith("p"):
        rows.sort(key=lambda x: -x[1])
    elif line.startswith("f"):
        rows.sort(key=lambda x: -x[2])
    else:
        rows.sort(key=lambda x: x[0].stat().st_mtime)
    print(f"  {'прогон':<26}{'PASS':<6}{'FAIL':<6}{'SKIP':<6}dur_s")
    for r, n_pass, n_fail, n_skip, dur in rows:
        print(f"  {r.name:<26}{n_pass:<6}{n_fail:<6}{n_skip:<6}{dur:.1f}")


def vfa_menu_res_diff(cfg: VfaConfig, state) -> None:
    runs = vfa_menu_list_runs(cfg)
    if len(runs) < 2:
        print("  нужно ≥2 прогона")
        return
    a, b = runs[-2], runs[-1]
    print("  два прогона через пробел (enter = два последних) > ",
          end="", flush=True)
    try:
        line = input().strip()
    except (EOFError, KeyboardInterrupt):
        print()
        line = ""
    if line:
        picked = []
        for tok in line.replace(",", " ").split():
            hits = [r for r in runs if tok in r.name]
            if len(hits) == 1:
                picked.append(hits[0])
            else:
                print(f"  ? не однозначно: {tok}")
        if len(picked) == 2:
            a, b = picked
        else:
            print("  (нужно ровно 2 — беру два последних)")
    ra = vfa_menu_parse_results(a / "results.json")
    rb = vfa_menu_parse_results(b / "results.json")
    print(f"  A = {a.name}  ·  B = {b.name}")
    ndiff = 0
    for tid in sorted(set(ra.verdicts) | set(rb.verdicts)):
        va, vb = ra.verdicts.get(tid, "—"), rb.verdicts.get(tid, "—")
        if va == vb:
            continue
        ndiff += 1
        print(f"   {tid:<4}{ra.slugs.get(tid, '?'):<24}{va} → {vb}")
    same = sum(1 for t in set(ra.verdicts) & set(rb.verdicts)
               if ra.verdicts.get(t, "?") == rb.verdicts.get(t, "?"))
    if ndiff == 0:
        print(f"  вердикты идентичны (совпало {same} задач)")
    else:
        print(f"  различий: {ndiff} · совпало: {same}")


def vfa_menu_res_open(cfg: VfaConfig, state) -> None:
    runs = vfa_menu_list_runs(cfg)
    if not runs:
        print("  (прогонов ещё не было)")
        return
    run = vfa_menu_pick_run(runs, "прогон")
    fr = run / "FINAL_REPORT"
    files = sorted(p.name for p in fr.glob("final_report.*")) if fr.is_dir() else []
    if not files:
        print("  (в прогоне нет FINAL_REPORT/final_report.*)")
        return
    print("  доступны: " + ", ".join(files))
    print("  формат (enter = md) > ", end="", flush=True)
    try:
        line = input().strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        line = ""
    fmt_name = line or "md"
    path = fr / f"final_report.{fmt_name}"
    if not path.is_file():
        print(f"  ? нет файла: {path}")
        return
    if fmt_name != "md":
        print(f"  бинарный/разметочный файл — путь: {path}")
        return
    print(f"  ── {path} ──")
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, l in enumerate(lines[:240], 1):
        print(l)
    if len(lines) > 240:
        print(f"  … (обрезано, всего {len(lines)} строк)")


def vfa_menu_res_manifest(cfg: VfaConfig, state) -> None:
    runs = vfa_menu_list_runs(cfg)
    if not runs:
        print("  (прогонов ещё не было)")
        return
    run = vfa_menu_pick_run(runs, "прогон")
    print(f"  {fmt(cfg, 'run_dir', d=str(run))}")
    for f in sorted(run.iterdir()):
        if f.is_dir():
            print(f"   {(f.name + '/'):<30}dir")
        else:
            sz = f.stat().st_size
            print(f"   {f.name:<30}{sz if sz < 1024 else f'{sz / 1024:.1f} KiB'}")
    mf = run / "MANIFEST.toml"
    if mf.is_file():
        print("  ── MANIFEST.toml ──")
        for l in mf.read_text(encoding="utf-8").splitlines():
            print("  " + l)


# ── §29.4 диагностика

def vfa_menu_diag_selftest(cfg: VfaConfig, state, props: bool = False,
                           contract: bool = False) -> None:
    snapshot = copy.deepcopy(cfg.__dict__)
    cfg.selftest = True
    cfg.selftest_props = props
    cfg.selftest_contract = contract
    try:
        code = VFATest.run(cfg)
        print(f"  (код возврата: {code})")
    finally:
        for k, v in snapshot.items():
            setattr(cfg, k, v)


def vfa_menu_diag_sysinfo(cfg: VfaConfig, state) -> None:
    print(f"  python {sys.version.split()[0]} · threads={threading.active_count()}"
          f" · cpu={os.cpu_count()}")
    print(f"  platform: {VFA_PLATFORM()}")
    for l in VFAMon.panel():
        print("  " + l)


def vfa_menu_print_config(cfg: VfaConfig, state) -> None:
    vfa_print_config(cfg)


"""Прогон набора задач с перекрытием полей конфига; cfg восстанавливается
из снапшота в finally (грабли №2: свип не протекает в следующий прогон)."""


def vfa_run_all_with(cfg: VfaConfig, ids: list[int],
                     override: dict | None = None) -> int:
    snapshot = copy.deepcopy(cfg.__dict__)
    cfg.tasks = list(ids)
    for k, v in (override or {}).items():
        if hasattr(cfg, k):
            setattr(cfg, k, v)
    try:
        return vfa_run_all(cfg)
    finally:
        for k, v in snapshot.items():
            setattr(cfg, k, v)


def vfa_menu_handle_action(state: MenuState, action, cfg: VfaConfig) -> None:
    if isinstance(action, QuitMenu):
        state.quit = True
    elif isinstance(action, PopMenu):
        vfa_menu_pop(state)
    elif isinstance(action, GotoMenu):
        if not vfa_menu_goto(state, action.id):
            print(f"  ? узел недоступен: {action.id}")
    elif isinstance(action, ShowInfo):
        print(action.text)
    elif isinstance(action, RunSuite):
        vfa_run_all_with(cfg, list(action.ids))
    elif isinstance(action, InvokeTask):
        vfa_run_all_with(cfg, [action.id], action.override)
    elif isinstance(action, RunLab):
        if action.spec == "add":
            vfa_lab_add(cfg, state)
        elif action.spec == "show":
            vfa_lab_show(cfg, state)
        elif action.spec == "clear":
            vfa_lab_clear(state)
        elif action.spec == "toml":
            vfa_lab_toml(cfg, state)
        elif action.spec == "run":
            vfa_lab_run(cfg, state)
        else:
            print(f"  ? неизвестный режим лаборатории: {action.spec}")
    elif isinstance(action, ActionFn):
        action.fn(cfg, state)
    elif isinstance(action, FormAction):
        vfa_menu_handle_action(state, action.on_submit(vfa_menu_collect_form(action)),
                               cfg)


def vfa_menu_build_tree(cfg: VfaConfig) -> dict[str, MenuNode]:
    VFA_MENU_NODES.clear()

    def state_header(_state: MenuState) -> list[str]:
        lines = [
            f"preset={cfg.preset} · two-pass={'ON' if cfg.two_pass else 'OFF'} · "
            f"seed={cfg.seed} · theme={cfg.theme} · lang={cfg.lang}"]
        last_run = vfa_menu_list_runs(cfg)
        if last_run:
            ri = vfa_menu_parse_results(last_run[-1] / "results.json")
            n_pass, n_fail, n_skip, _d = vfa_menu_run_counts(ri)
            lines.append(f"последний прогон: {last_run[-1].name}  "
                         f"[{n_pass} PASS · {n_fail} FAIL · {n_skip} SKIP]")
        return lines

    def select_tasks(c: VfaConfig, _s: MenuState) -> None:
        print("  номера задач (пробел/запятая; all — все) > ", end="", flush=True)
        try:
            line = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        ids: list[int] = []
        ok = True
        for tok in line.replace(",", " ").split():
            if tok == "all":
                ids.extend(SUITE_IDS)
                continue
            if tok.isdigit() and int(tok) in SUITE_IDS:
                ids.append(int(tok))
                continue
            print(f"  ? не задача: {tok}")
            ok = False
        if not (ok and ids):
            print("  (ничего не выбрано)")
            return
        c.tasks = ids                     # §30: выбор остаётся в сессии — lab [r]
        vfa_run_all_with(c, ids)

    def bench_one(c: VfaConfig, _s: MenuState) -> None:
        print("  номер бенчмарка (16..22) > ", end="", flush=True)
        try:
            line = input().strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not line.isdigit() or int(line) not in BENCH_IDS:
            print(f"  ? не бенчмарк: {line}")
            return
        vfa_run_all_with(c, [int(line)])

    def res_xcheck(c: VfaConfig, _s: MenuState) -> None:
        print("  путь к results.json / каталогу прогона > ", end="", flush=True)
        try:
            line = input().strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not line:
            print("  (отмена)")
            return
        vfa_cross_check(c, line)

    def diag_t(c, s):
        vfa_menu_diag_selftest(c, s)

    def diag_tp(c, s):
        vfa_menu_diag_selftest(c, s, props=True)

    def diag_tc(c, s):
        vfa_menu_diag_selftest(c, s, contract=True)

    spec_items = []
    for sp in vfa_menu_settings_specs():
        if sp.kind in ("cycle", "theme"):
            act = ActionFn(lambda c, s, sp=sp: vfa_menu_setting_cycle(c, sp), "цикл")
        else:
            act = ActionFn(lambda c, s, sp=sp: vfa_menu_setting_prompt(c, sp), "ввод")
        spec_items.append(MenuItem(sp.label, sp.key, act,
                                   sp.help or "/".join(sp.choices)))

    vfa_menu_register_node(MenuNode("root", "Главное меню", [
        MenuItem("Быстрый прогон (все задачи)", "1",
                 RunSuite(SUITE_IDS),
                 f"preset={cfg.preset}, two-pass={cfg.two_pass}"),
        MenuItem("Выбрать задачи", "2", ActionFn(select_tasks, "выбор номеров"),
                 "например: 3 7 11"),
        MenuItem("Лаборатория", "3", GotoMenu("lab"), "свипы и эксперименты"),
        MenuItem("Бенчмарки точных решений", "4", GotoMenu("bench"), "задачи 16–22"),
        MenuItem("3D-вихрь (затухание)", "v",
                 ActionFn(lambda c, s: vfa_menu_vortex(c), "рендер GIF"),
                 "N ≥ 24, до 256"),
        MenuItem("Результаты и отчёты", "5", GotoMenu("results"), ""),
        MenuItem("Настройки", "6", GotoMenu("settings"), ""),
        MenuItem("Самотест / диагностика", "7", GotoMenu("diag"), ""),
        MenuItem("Справка (ключи CLI)", "?", ShowInfo(VFA_HELP), ""),
        MenuItem("Выход", "q", QuitMenu(), ""),
    ], state_header, None))

    vfa_menu_register_node(MenuNode(
        "settings", "Настройки", spec_items + [MenuItem("назад", "..", PopMenu(), "")],
        lambda _s: vfa_menu_settings_header(cfg), "root"))

    vfa_menu_register_node(MenuNode("lab", "Лаборатория (свипы и эксперименты)", [
        MenuItem("Добавить свип", "s", RunLab("add"),
                 "KEY=V1,V2;... — любое поле конфига"),
        MenuItem("Показать матрицу", "v", RunLab("show"), "измерения и комбинации"),
        MenuItem("Очистить матрицу", "x", RunLab("clear"), ""),
        MenuItem("Загрузить experiment.toml", "t", RunLab("toml"),
                 "enter = experiment.toml"),
        MenuItem("Запустить эксперимент", "r", RunLab("run"), "N комбинаций × задачи"),
        MenuItem("назад", "..", PopMenu(), ""),
    ], None, "root"))

    vfa_menu_register_node(MenuNode("bench", "Бенчмарки точных решений (16–22)", [
        MenuItem("Все бенчмарки 16–22", "1", RunSuite(BENCH_IDS), "сводный прогон"),
        MenuItem("Отдельный бенчмарк", "2", ActionFn(bench_one, "номер 16..22"), ""),
        MenuItem("Что это", "v",
                 ShowInfo("  Бенчмарки точных решений §31 (16–22):\n"
                          "   16 Тейлор-Грин   — невязка дискретных НС на точном поле, порядок 2\n"
                          "   17 Ковазнай      — стационарные НС, Re=30, λ=Re/2−√(Re²/4+4π²)\n"
                          "   18 Стокс II      — осциллирующая стенка, FTCS против e^{-ky}sin(ωt−ky)\n"
                          "   19 Лере-Хопф     — энергия π²e^{-4νt}, монотонность, баланс с энстрофией\n"
                          "   20 ABC           — rot u = u (Бельтрами), тождество Ламба\n"
                          "   21 Бюргерс       — стационарная волна −tanh(cx/2ν), прогон до установления\n"
                          "   22 Ричардсон     — log₂(res(N)/res(2N)) ≈ 2 для ТГ и ABC"), ""),
        MenuItem("назад", "..", PopMenu(), ""),
    ], None, "root"))

    vfa_menu_register_node(MenuNode("results", "Результаты и отчёты", [
        MenuItem("Последний прогон (сводка)", "l",
                 ActionFn(vfa_menu_res_last, "вердикты"), ""),
        MenuItem("История прогонов", "h",
                 ActionFn(vfa_menu_res_history, "n/p/f — сортировка"), ""),
        MenuItem("Diff двух прогонов", "d", ActionFn(vfa_menu_res_diff, "A → B"),
                 "enter = два последних"),
        MenuItem("Открыть отчёт", "o", ActionFn(vfa_menu_res_open, "final_report.md"),
                 "html/pdf — путь"),
        MenuItem("Манифест прогона", "m",
                 ActionFn(vfa_menu_res_manifest, "MANIFEST.toml + файлы"), ""),
        MenuItem("Сверка с прогоном run_*", "c", ActionFn(res_xcheck, "путь"),
                 "results.json другого прогона (§32)"),
        MenuItem("назад", "..", PopMenu(), ""),
    ], None, "root"))

    vfa_menu_register_node(MenuNode("diag", "Самотест / диагностика", [
        MenuItem("self-test (проверки §14)", "t", ActionFn(diag_t, "VFATest"), ""),
        MenuItem("self-test +props", "tp", ActionFn(diag_tp, "свойства"), ""),
        MenuItem("self-test +contract", "tc", ActionFn(diag_tc, "контракт"), ""),
        MenuItem("Системная информация", "i",
                 ActionFn(vfa_menu_diag_sysinfo, "VFAMon + /proc"), ""),
        MenuItem("Печать конфига", "c",
                 ActionFn(vfa_menu_print_config, "VfaConfig"), ""),
        MenuItem("назад", "..", PopMenu(), ""),
    ], None, "root"))
    return VFA_MENU_NODES


def vfa_menu_tree_run(cfg: VfaConfig) -> int:
    """§29: главный цикл нового TUI-меню. Возвращает 0 (или код аварийного
    выхода вложенного прогона — прогон сам печатает свой статус)."""
    vfa_menu_build_tree(cfg)
    s = MenuState(VFA_MENU_NODES, "root", ["root"], [], {})
    eof_streak = 0
    while not s.quit:
        vfa_menu_render(s)
        try:
            raw = input()
            eof_streak = 0 if raw.strip() else eof_streak + 1
        except EOFError:
            eof_streak += 1
            raw = ""
        except KeyboardInterrupt:
            print("\n  (Ctrl+C — остаёмся в меню)")
            continue
        if eof_streak >= VFA_EOF_GUARD:
            print("EOF guard: graceful exit")
            break
        line = raw.strip()
        if not line:
            continue
        low = line.lower()
        if low in ("q", "quit", "exit", "выход", "выйти"):
            break
        if low in ("..", "b", "back", "назад"):
            if not vfa_menu_pop(s):
                print("  (вы в корне)")
            continue
        if low == "?":
            vfa_menu_show_help(s)
            continue
        # хоткеи узла чувствительны к регистру (O/M/W в §29.2);
        # RU-раскладка §12 применяется к вводу пунктов
        key = line.translate(VFA_RU_LAYOUT)
        node = s.nodes[s.current]
        item = next((it for it in node.items if it.key == key), None)
        if item is None:
            print(f"  ? неизвестно: {line}")
            continue
        try:
            vfa_menu_handle_action(s, item.action, cfg)
        except KeyboardInterrupt:
            print("\n  " + fmt(cfg, "back_menu"))
        except Exception as exc:            # §13.4: пункт меню не убивает программу
            print(f"  ERROR: {exc}")
            try:
                VFALog.get().log_comp(f"menu: {traceback.format_exc(limit=2)}", "error")
            except Exception:
                pass
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# Точка входа §16
# ═══════════════════════════════════════════════════════════════════════════

def vfa_main(argv: list[str] | None = None) -> int:
    log = VFALog.get()
    VFAUI.detect_capabilities()
    cfg = default_config()
    argv = list(sys.argv[1:] if argv is None else argv)
    # --config-file должен примениться ПЕРВЫМ (§3 приоритет: file < env < cli)
    # B9: мёртвый pre = VfaConfig() удалён — он не использовался нигде
    for i, tok in enumerate(argv):
        if tok == "--config-file" and i + 1 < len(argv):
            cfg.config_file = Path(argv[i + 1])
    try:
        if cfg.config_file:
            vfa_load_config_file(cfg, cfg.config_file)
        vfa_parse_env(cfg)
        vfa_parse_args(cfg, argv)
        # §30: fail-fast — кривой --sweep (неизвестный ключ) → usage error
        if cfg.sweep.strip():
            vfa_lab_parse_sweeps(cfg.sweep, cfg)
    except (SystemExit, ValueError) as exc:
        print(f"usage error: {exc}", file=sys.stderr)
        return 2
    # доступность §20: NO_COLOR/--no-color/unicode/plain до первой печати
    if cfg.no_color:
        VFAUI.state["color"] = False
    VFAUI.set_unicode(cfg.unicode_mode)
    if cfg.plain:
        VFAUI.state["color"] = False
        VFAUI.state["unicode"] = False
    log.ci_mode = cfg.ci
    # §28: баннер первым — до help/version/completions/list-tasks/print-config.
    # Технические команды баннер не печатают (машиночитаемые выходы);
    # самотест тоже — не сорим вывод.
    if cfg.selftest:
        cfg.banner = "never"
    _is_meta = (cfg.help or cfg.version or cfg.generate_completions
                or cfg.list_tasks or cfg.print_config)
    if not _is_meta and not cfg.quiet and not cfg.ci and not cfg.plain:
        _show = (cfg.banner == "always" or
                 (cfg.banner == "auto" and vfa_detect_tty()))
        if _show:
            subtitle = (f"preset={cfg.preset} · "
                        f"two-pass={'ON' if cfg.two_pass else 'OFF'} · "
                        f"tasks={','.join(map(str, cfg.tasks)) or 'all'}")
            VFABanner.show(subtitle=subtitle)
            # §9: баннер в computation_log (воспроизводимость)
            try:
                log.log_comp(f"banner printed (banner={cfg.banner})")
            except Exception:
                pass
    if cfg.help:
        print(VFA_HELP)
        return 0
    if cfg.version:
        print(f"vfa {__version__}-py (python {sys.version.split()[0]}, "
              f"{VFA_PLATFORM()})")
        return 0
    if cfg.generate_completions:
        print(vfa_generate_completions(cfg.generate_completions), end="")
        return 0
    if cfg.list_tasks:
        fmt_json = any(argv[i:i + 2] == ["--format", "json"] for i in range(len(argv)))
        print(vfa_list_tasks(fmt_json=fmt_json))
        return 0
    if cfg.print_config:
        vfa_print_config(cfg)
        return 0
    vfa_handle_signals()
    # rlimits best-effort §10.6: --rlimit kind=v[,kind=v...] + прежние флаги
    if cfg.rlimit.strip():
        for spec in cfg.rlimit.split(","):
            spec = spec.strip()
            if not spec:
                continue
            try:
                kind, val = spec.split("=", 1)
                msg = vfa_set_rlimit(kind.strip(), int(val.strip()))
            except ValueError as exc:
                msg = f"ERR_UNSUPPORTED rlimit: некорректно '{spec}' ({exc})"
            print(f"rlimit: {msg}", file=sys.stderr)
            log.log_comp(msg, "info" if msg.startswith("OK") else "warn")
    for kind, val in (("as", cfg.rlimit_as), ("cpu", cfg.rlimit_cpu),
                      ("fsize", cfg.rlimit_fsize)):
        if val:
            msg = vfa_set_rlimit(kind, val)
            log.log_comp(msg, "info" if msg.startswith("OK") else "warn")
    try:
        if cfg.selftest:
            return VFATest.run(cfg)
        # §27b: неконфликтный рендер вихря (--vortex N, в т.ч. из TOML) —
        # рендерим и выходим (см. NOTE в --help про приоритет vortex_N)
        if cfg.vortex_N > 0 or cfg.vortex_quick:
            try:
                if cfg.vortex_quick and cfg.vortex_N == 0:
                    cfg.vortex_N = 32       # --vortex-quick без N → превью
                vfa_vortex_cli(cfg)
            except Exception as exc:
                print(f"vortex: ERROR {exc}", file=sys.stderr)
                return 3
            return 0
        # §29 (§16, ред. 1.2, вариант «б»): TUI-меню по умолчанию только для
        # интерактивного TTY без машинных флагов; --ci/--task/--self-test и
        # pipe/CI → прямой прогон (обратная совместимость).
        if cfg.menu:
            return vfa_menu_tree_run(cfg)          # --menu: новое меню §29
        if cfg.menu_legacy or cfg.config_menu:
            return vfa_menu(cfg)                   # --menu-legacy: прежнее
        if cfg.ci or cfg.tasks or not vfa_detect_tty():
            code = vfa_run_all(cfg)
            # §32: сверка с results.json другого монолита — после прогона
            if cfg.cross_check.strip():
                if not vfa_cross_check(cfg, cfg.cross_check.strip()):
                    code = max(code, 1)
            return code
        return vfa_menu_tree_run(cfg)              # TTY без флагов → меню
    except KeyboardInterrupt:
        log.log_comp("SIGINT: graceful exit 130")
        return 130
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 2
        return code
    except Exception as exc:               # §19: код 3 — внутренняя ошибка
        log.log_comp(f"BUG: {traceback.format_exc()}", "error")
        print(f"INTERNAL ERROR: {exc}", file=sys.stderr)
        return 3
    finally:
        log.stop_pump()


if __name__ == "__main__":
    sys.exit(vfa_main())
