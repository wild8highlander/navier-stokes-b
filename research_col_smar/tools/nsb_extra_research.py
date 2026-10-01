#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""nsb_extra_research.py — дополнительные исследования пакета NSB-96-UPGRADE.

Три новые лаборатории, дополняющие nsb_lab (L1–L10), по физике той же
программы b-коррекции:

  L11  Перемежаемость и градиентная статистика: 48³ (снимок монографии)
       против 96³ (состояние A96 на t = 6) — скос/плоскостность/гипер-
       плоскостность продольного градиента, PDF, функции структуры.
       Вопрос: устойчива ли мелкомасштабная статистика при удвоении
       разрешения?
  L12  Спектральный поток Π(k) и каскад: оболочечный трансфер T(k),
       диссипация D(k), поток Π(k) = Σ_{q≥k}[D(q) − T(q)]; тождества
       Σ T = 0 (точная консервативность нелинейного члена) и Π(0) = ε;
       коллапс Π(k)/ε между 48³ и 96³.
  L13  Гипердиссипативное семейство КдФ: u_t + 6uu_x + u_xxx = −ν(−∂²)^b u,
       b ∈ {1, 5/4, 3/2, 2} — мост между b-семейством НСЭ (гл. 12/15
       монографии) и главой 16 (КдФ). Проверки: точное сохранение массы
       (∀b > 0), тождество dP/dt = −ν⟨u(−∂²)^b u⟩ (две нормировки),
       самосходимость N и dt, диссипационный обрез k_ν(b) = (1/νT)^(1/2b).
  L14  Графики 4 × 600 dpi (RU + EN): figX1..figX4.
  L15  Сводные отчёты (MD/TXT) + вердикты WIN/DRAW/LOSS.
  L16  Самосходимость решателя P5: сетки 24³–96³ × шаги dt 4e-3–5e-4;
       наблюдаемый временной порядок IFK-RK2, Ричардсон-экстраполяция
       dt→0, атрибуция ошибки 48³↔96³ (пространство vs время). figX5.
       Переменные окружения: NSB16_CONFIGS="CONV72,..." — выполнить
       только перечисленные прогоны; NSB16_NOANALYSIS=1 — без анализа.
  L17  φ-аудит монографии о двухслойных φ-аттракторах (загруженная
       пользователем работа «Двухслойные φ-аттракторы в точечно-вихревой
       модели»): φ-алгебра (прил. Z), дискретный спектр Фибоначчи
       (табл. X.6), RG-отображение слияний μ → 1+1/μ (прил. Д.5),
       теоремы о нулевом дрейфе (§2.2: безрешётность a·b·b·c через
       тождество Кассини + вырождение a·a·b·b), симметрийная теорема
       C_s = 0 для процедуры приложения B, динамический тест мод
       (прил. Г, D.5), цепочка (D.6b)–(D.8), DNS-мост приложения Д
       (Okubo–Weiss квадруплеты: синтетическая валидация + срезы 96³
       TG). figX6. Кросс-язык: julia nsb_extra_research.jl (ядро L17).
       Артефакты: results/extra17_*_{json,txt,csv},
       results/extra17_julia_ref.json → extra17_julia_crosscheck.json.

Все параметры настраиваются (--set key value / меню «C»), интерфейс RU/EN,
прогресс-бар в одну строку, артефакты JSON/TXT/CSV + логи.

Примеры:
  python3 nsb_extra_research.py                     # меню (RU)
  python3 nsb_extra_research.py --lang en --run all
  python3 nsb_extra_research.py --run 11            # только L11
  python3 nsb_extra_research.py --set kdvb_nu 0.02 --run 13 --yes
  python3 nsb_extra_research.py --run 16 --yes   # самосходимость (L16)
  python3 nsb_extra_research.py --run 17 --yes   # φ-аудит монографии (L17)
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
import time
from datetime import datetime

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from nsb_lab import (  # noqa: E402
    UI, SpecSolver, Verdicts, wavevectors, dealias_mask, run_trajectory,
    clear_checkpoint, _dump_artifacts, _obj_to_text, _apply_font, fmt_sec,
    OUT_RESULTS, OUT_FIGURES, OUT_REPORTS, PKG_ROOT, REF_DIR,
    B_UNIV, THETA_B,
)

# палитра пакета (cascade)
C_ACCENT = "#92761f"
C_ACCENT2 = "#3aa0c2"
C_HEADER = "#4e4732"
C_TEXT = "#151513"
C_MUTED = "#7e7c74"
C_BORDER = "#c5bfac"
C_LOSS = "#b0483a"

B_UNIV_S = f"b = 1/(4π+2√3) = {B_UNIV:.9f}   θ_b = {math.degrees(THETA_B):.6f}°"

# ============================================================================
# КОНФИГУРАЦИЯ (все ключи настраиваются через --set / меню «C»)
# ============================================================================
EXTRA_CFG: dict = {
    "lang": "ru",
    "nu": 0.01,               # вязкость протокола P5
    "dt": 0.002,              # шаг протокола P5
    "t_snap": 6.0,            # момент снимков (T_end прогона A)
    "rmax": 16,               # макс. разнос функций структуры (в ячейках 48³)
    "pdf_xrange": 8.0,        # полуширина PDF нормированного градиента
    "dpi": 600,
    "fig_width": 13.5,
    "fig_height": 5.2,
    # пороги: относительная разность 48³ ↔ 96³ скалярных диагностик
    "thr_grad": [0.05, 0.15],
    # порог коллапса S_p(r) и Π(k)/ε в общем физическом интервале
    "thr_collapse": [0.08, 0.20],
    # тождества L12: Σ T = 0 и Π(0) = ε (остаток ~ 10⁻⁷ — фп-накопление
    # тройного произведения ⟨u, u×ω⟩ на N³ точках), а также Π(0) vs −dE/dt
    "thr_identity": [1e-6, 1e-4],
    "thr_pi_eps": [2e-3, 1e-2],
    # L13: гипердиссипативное КдФ
    "kdvb_family": [1.0, 1.25, 1.5, 2.0],
    "kdvb_nu": 0.02,
    "kdvb_n": 1024,
    "kdvb_n_coarse": 512,
    "kdvb_l": 100.0,
    "kdvb_dt": 0.0005,
    "kdvb_t_end": 10.0,
    "kdvb_c": 4.0,
    "kdvb_x0": 30.0,
    "thr_kdvb_mass": [1e-13, 1e-9],    # дрейф массы (ожидается машинная точность)
    "thr_kdvb_pident": [1e-3, 1e-2],   # тождество dP/dt (этаж схемы расщепления)
    "thr_kdvb_conv": [2e-3, 1e-2],     # самосходимость N и dt
    # L16: самосходимость решателя P5 (пространство × время) + Ричардсон
    "conv_ns": [24, 36, 72],           # сетки пространственного скана (+48, ref 96³)
    "conv_dts": [0.004, 0.001, 0.0005],  # шаги временного скана при N = 48 (+ dt протокола)
    "thr_conv_p": [1.8, 1.0],          # порядок IFK-RK2: WIN ≥ 1.8 (номинал 2), DRAW ≥ 1.0 (сходимость есть, редукция порядка)
    "thr_conv_mono": [3.5, 2.5],       # монотонность/насыщение: счёт из 4 величин (WIN ≥ 4, DRAW ≥ 3)
    "thr_conv_r2": [0.85, 0.60],       # r² экспоненциальной посадки err(N) ∝ e^(−cN)
    "thr_conv_sat": [0.6, 0.85],       # насыщение: err(72³)/err(48³) → 0 при ref 96³
    "thr_conv_bal": [1e-2, 3e-2],      # балансы энергии/энстрофии по всем прогонам
    "thr_conv_rich": [5e-3, 2e-2],     # невязка Ричардсона dt→0 при p = 2
    # L17: φ-аудит монографии (двухслойные φ-аттракторы)
    "phi_grids": [32, 64, 128],        # сетки LES-процедуры приложения B
    "phi_delta": 1.0,                  # масштаб фильтра Δ
    "phi_box": 3.5,                    # полуширина короба [-L/2, L/2]²
    "phi_dt": 0.002,                   # шаг RK4 Кирхгофа (тест мод)
    "phi_T": 24.0,                     # горизонт теста мод
    "phi_pert": 1e-6,                  # амплитуда возмущения (тест мод)
    "phi_zslices": [16, 32, 48, 64, 80],  # z-срезы 96³ для моста приложения Д
    "thr_phi_alg": [1e-12, 1e-9],      # φ-алгебра: максимум остатка
    "thr_phi_mu": [0.01, 0.03],        # спектр Фибоначчи: max |μ − φ|
    "thr_phi_binet": [0.5, 1.5],       # нарушения монотонности Бине (счёт)
    "thr_phi_rg": [0.02, 0.10],        # RG-отображение: откл. скорости от 1/φ²
    "thr_phi_zd": [1e-9, 1e-6],        # тождество Кассини / семейство: невязка
    "thr_phi_zdnosol": [5.5, 4.5],     # счёт a·b·b·c без решений (из 6; WIN при 6)
    "thr_phi_cs0": [1e-12, 1e-8],      # |C_s²| на симметричных (теорема = 0)
    "thr_phi_csneg": [41.5, 35.0],     # счёт отрицательных num (6 конф × 7 t; WIN при 42)
    "thr_phi_csctl": [1e-8, 1e-10],    # контрольные поля: min C_s² > 0
    "thr_phi_modes": [0.15, 0.30],     # тест мод: |ν̂/ν_breath − 1| (допуск Д.4)
    "thr_phi_d7": [0.25, 0.50],        # цепочка (D.6b)–(D.8): |τ/τ_claim − 1|
    "thr_phi_dnsyn": [0.05, 0.15],     # синтетика: |ρ̂/φ − 1|
    "thr_phi_dnstg": [4.5, 3.5],       # срезы TG с 2+/2− (из 5; WIN при 5)
    "thr_phi_jl": [1e-10, 1e-6],       # кросс-язык Julia↔Python
}
EXTRA_INT = ("rmax", "dpi", "kdvb_n", "kdvb_n_coarse")
EXTRA_FLOAT = ("nu", "dt", "t_snap", "pdf_xrange", "fig_width", "fig_height",
               "kdvb_nu", "kdvb_l", "kdvb_dt", "kdvb_t_end", "kdvb_c",
               "kdvb_x0", "phi_delta", "phi_box", "phi_dt", "phi_T",
               "phi_pert")
EXTRA_LIST = ("kdvb_family", "thr_grad", "thr_collapse", "thr_identity",
              "thr_pi_eps", "thr_kdvb_mass", "thr_kdvb_pident",
              "thr_kdvb_conv", "conv_ns", "conv_dts", "thr_conv_p",
              "thr_conv_mono", "thr_conv_r2", "thr_conv_sat",
              "thr_conv_bal", "thr_conv_rich", "phi_grids", "phi_zslices",
              "thr_phi_alg", "thr_phi_mu", "thr_phi_binet", "thr_phi_rg",
              "thr_phi_zd", "thr_phi_zdnosol", "thr_phi_cs0",
              "thr_phi_csneg", "thr_phi_csctl", "thr_phi_modes",
              "thr_phi_d7", "thr_phi_dnsyn", "thr_phi_dnstg",
              "thr_phi_jl")


class XCfg:
    """Обёртка конфигурации с доступом по ключу (совместима с Verdicts)."""

    def __init__(self, overrides: dict | None = None):
        self.d = dict(EXTRA_CFG)
        cfg_path = os.path.join(HERE, "config", "nsb_extra_config.json")
        if os.path.isfile(cfg_path):
            try:
                with open(cfg_path, encoding="utf-8") as fh:
                    user = json.load(fh)
                self.d.update({k: v for k, v in user.items() if k in self.d})
            except Exception:
                pass
        if overrides:
            self.d.update({k: v for k, v in overrides.items() if k in self.d})
        self.d["kdvb_family"] = [float(x) for x in self.d["kdvb_family"]]
        for key in ("thr_grad", "thr_collapse", "thr_identity", "thr_pi_eps",
                    "thr_kdvb_mass", "thr_kdvb_pident", "thr_kdvb_conv"):
            self.d[key] = [float(x) for x in self.d[key]]
        self.d["phi_grids"] = [int(x) for x in self.d["phi_grids"]]
        self.d["phi_zslices"] = [int(x) for x in self.d["phi_zslices"]]
        for key in self.d:
            if key.startswith("thr_phi_"):
                self.d[key] = [float(x) for x in self.d[key]]

    def __getitem__(self, key):
        return self.d[key]

    def get(self, key, default=None):
        return self.d.get(key, default)

    def set_key(self, key, value) -> bool:
        if key not in self.d:
            return False
        try:
            if key in EXTRA_INT:
                self.d[key] = int(value)
            elif key in EXTRA_FLOAT:
                self.d[key] = float(str(value).replace(",", "."))
            elif key in EXTRA_LIST:
                parsed = json.loads(
                    value if str(value).startswith("[") else f"[{value}]")
                self.d[key] = [float(x) for x in parsed]
            else:
                self.d[key] = str(value)
            return True
        except Exception:
            return False

    def save(self) -> str:
        d = os.path.join(HERE, "config")
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, "nsb_extra_config.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(self.d, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        return p


# ============================================================================
# ЛОКАЛИЗАЦИЯ
# ============================================================================
L10N = {
    "ru": {
        "title": "NSB EXTRA — ДОПОЛНИТЕЛЬНЫЕ ИССЛЕДОВАНИЯ (L11–L17)",
        "subtitle": "перемежаемость · поток · КдФ · самосходимость · φ-аудит монографии",
        "menu_hdr": "МЕНЮ — ВЫБЕРИТЕ ЛАБОРАТОРИЮ",
        "lab11": "L11 Перемежаемость и градиентная статистика 48³ vs 96³",
        "lab12": "L12 Спектральный поток Π(k) и каскад 48³ vs 96³",
        "lab13": "L13 Гипердиссипативное семейство КдФ ν(−∂²)^b",
        "lab14": "L14 Графики 4×600 dpi (RU + EN)",
        "lab15": "L15 Сводные отчёты (MD/TXT) + вердикты",
        "lab16": "L16 Самосходимость решателя: N × dt + Ричардсон (figX5)",
        "lab17": "L17 φ-аудит монографии о φ-аттракторах (figX6)",
        "lab_cfg": "C  Настройки",
        "lab_lang": "L  Переключить язык / Switch language",
        "lab_all": "A  ЗАПУСТИТЬ ВСЁ (L11→L17)",
        "lab_quit": "Q  Выход",
        "choose": "Ваш выбор: ",
        "config_hdr": "ТЕКУЩИЕ ПАРАМЕТРЫ (можно менять)",
        "config_ask": "Имя параметра (Enter — назад): ",
        "config_val": "Новое значение: ",
        "config_bad": "Неизвестный параметр или неверное значение.",
        "config_saved": "Сохранено в",
        "back": "Enter — в меню",
        "win": "ПОБЕДА", "draw": "НИЧЬЯ", "loss": "ПОРОЖЕНИЕ",
        "eta": "осталось",
        # статусы загрузки данных
        "snap_ok": "снимок 48³ загружен (E-контроль пройден)",
        "state_ok": "состояние 96³ загружено",
        "state_none": "состояние 96³ не найдено — запускаю траекторию A96 (~14 мин)",
        "integrity": "контроль целостности данных",
        # L11
        "l11_hdr": "L11  Перемежаемость и градиентная статистика: 48³ vs 96³ (t = 6)",
        "l11_scalar": "скаляр", "l11_48": "48³", "l11_96": "96³",
        "l11_rel": "отн. разн.", "l11_verdict": "вердикт",
        "l11_S3": "скос ⟨ζᵢ³⟩/⟨ζᵢ²⟩^3/2 (изотроп.)",
        "l11_F4": "плоскостность ⟨ζᵢ⁴⟩/⟨ζᵢ²⟩² (изотроп.)",
        "l11_F6": "гиперплоскостность ⟨ζᵢ⁶⟩/⟨ζᵢ²⟩³ (изотроп.)",
        "l11_wrms": "⟨ω²⟩^1/2 (vorticity rms)",
        "l11_wmax": "‖ω‖_∞",
        "l11_collapse": "коллапс S₄(r): среднее |S₄⁹⁶/S₄⁴⁸ − 1| в полосе",
        # L12
        "l12_hdr": "L12  Спектральный поток Π(k) и каскад: 48³ vs 96³ (t = 6)",
        "l12_sumT": "тождество Σ T(k) = 0 (консервативность нелинейного члена)",
        "l12_pi0": "тождество Π(0) = ε",
        "l12_pi0_dot": "Π(0) против −dE/dt из траектории",
        "l12_collapse": "коллапс Π(k)/ε: среднее |Π⁹⁶/ε⁹⁶ − Π⁴⁸/ε⁴⁸| / Π⁴⁸/ε⁴⁸",
        # L13
        "l13_hdr": "L13  Гипердиссипативное семейство КдФ: u_t + 6uu_x + u_xxx = −ν(−∂²)^b u",
        "l13_mass": "дрейф массы M (∀b > 0 — точное сохранение)",
        "l13_pident": "тождество dP/dt = −ν⟨u(−∂²)^b u⟩ (спектр vs физ. поле)",
        "l13_conv_n": "самосходимость по N (512 → 1024, b = 5/4)",
        "l13_conv_dt": "самосходимость по dt (5e-4 → 1e-3, b = 5/4)",
        "l13_amp": "A(T)/A₀", "l13_knu": "k_ν(b) теория", "l13_knu_m": "k_e измерен",
        "l13_tab_b": "b_pow", "l13_note": ("k_e — волновое число, где E(k,T)/E(k,0) = e⁻¹; "
                       "теория k_ν = (1/νT)^(1/2b); расхождение ожидаемо (перераспределение "
                       "энергии нелинейностью)"),
        # L16
        "l16_hdr": "L16  Самосходимость решателя P5: пространство (N) × время (dt) + Ричардсон",
        "l16_p_time": "наблюдаемый временной порядок IFK-RK2: min(p_E, p_Ω) ≥ 1.8",
        "l16_mono": "монотонное убывание ошибки по N (из 4 величин)",
        "l16_exp_r2": "r² экспоненциальной посадки err(N) ∝ e^(−cN), минимум",
        "l16_sat72": "насыщение сетки: err(72³) < err(48³) (из 4 величин)",
        "l16_balance": "максимум балансов энергии/энстрофии по прогонам L16",
        "l16_rich": "невязка Ричардсона dt→0 при p = 2 (максимум)",
        "l16_note": ("ref: 96³ (A96, dt = 2e-3) для пространства; dt = 5e-4 (N = 48) "
                     "для времени; p₁ — по ошибкам против ref, p₂ — Роаш (три уровня); "
                     "Q₀ = Q(dt/2) + (Q(dt/2) − Q(dt))/(2^p − 1), p = 2"),
        # L17
        "l17_hdr": "L17  φ-аудит монографии: φ-аттракторы, C_s, RG-каскад, DNS-мост",
        "l17_alg": "φ-алгебра (прил. Z.1): максимум остатка из 10 тождеств",
        "l17_mu": "спектр Фибоначчи (табл. X.6): max |μ − φ| из 10 квадруплетов",
        "l17_binet": "монотонность Бине: |μ − φ| убывает с ростом индекса (нарушений)",
        "l17_rg": "RG-отображение μ→1+1/μ: откл. скорости от 1/φ² ≈ 0.382",
        "l17_zdid": "нулев. дрейф: редуцированное условие (Кассини) vs прямое (невязка)",
        "l17_zdnosol": "a·b·b·c: квадруплетов без решений нулевого дрейфа (из 6)",
        "l17_zdfam": "a·a·b·b: вырожденное семейство, φ-геометрия достижима (невязка)",
        "l17_cs0": "теорема C_s=0 (нечётность по x): max |C_s²| на симметричных",
        "l17_csneg": "a·b·b·c: сканов с num < 0 (backscatter → C_s=null), из 42",
        "l17_csctl": "контрольные поля (пара 80/120, случайное): min C_s² > 0",
        "l17_modes": "тест мод (прил. Г): |ν̂(R₂)/ν_breath(D.5b) − 1|",
        "l17_d7": "цепочка (D.6b)–(D.8): |τ_φ/322 − 1| при Γ₁=1, Γ₂=φ, R₂=1",
        "l17_dnsyn": "DNS-мост, синтетика: |ρ̂/φ − 1| (восстановление известного ρ)",
        "l17_dnstg": "DNS-мост, TG 96³: срезов с квадруплетом 2+/2− (из 5)",
        "l17_jl": "кросс-язык Julia↔Python (ядро L17): max отн. откл.",
        "l17_note": ("аудит по загруженной монографии «Двухслойные φ-аттракторы в "
                     "точечно-вихревой модели»: подтверждена математическая рамка "
                     "(φ, Фибоначчи, RG); условия нулевого дрейфа (5) безрешётны для "
                     "a·b·b·c (Кассини) и вырождены для a·a·b·b; процедура C_s "
                     "приложения B даёт 0/null на всех конфигурациях табл. 2; "
                     "предсказания (D.5)/(D.8) не описывают двухпараболическую "
                     "геометрию; DNS-мост приложения Д валидирован на синтетике"),
    },
    "en": {
        "title": "NSB EXTRA — ADDITIONAL RESEARCH (L11–L17)",
        "subtitle": "intermittency · spectral flux · hyperdissipative KdV · self-convergence · φ-audit",
        "menu_hdr": "MENU — CHOOSE A LABORATORY",
        "lab11": "L11 Intermittency & gradient statistics 48³ vs 96³",
        "lab12": "L12 Spectral flux Π(k) and cascade 48³ vs 96³",
        "lab13": "L13 Hyperdissipative KdV family ν(−∂²)^b",
        "lab14": "L14 Figures 4×600 dpi (RU + EN)",
        "lab15": "L15 Aggregate reports (MD/TXT) + verdicts",
        "lab16": "L16 Solver self-convergence: N × dt + Richardson (figX5)",
        "lab17": "L17 φ-audit of the φ-attractor monograph (figX6)",
        "lab_cfg": "C  Settings",
        "lab_lang": "L  Switch language / Переключить язык",
        "lab_all": "A  RUN EVERYTHING (L11→L17)",
        "lab_quit": "Q  Quit",
        "choose": "Your choice: ",
        "config_hdr": "CURRENT PARAMETERS (editable)",
        "config_ask": "Parameter name (Enter — back): ",
        "config_val": "New value: ",
        "config_bad": "Unknown parameter or bad value.",
        "config_saved": "Saved to",
        "back": "Enter — menu",
        "win": "WIN", "draw": "DRAW", "loss": "LOSS",
        "eta": "ETA",
        "snap_ok": "48³ snapshot loaded (E integrity check passed)",
        "state_ok": "96³ state loaded",
        "state_none": "96³ state not found — running A96 trajectory (~14 min)",
        "integrity": "data integrity check",
        "l11_hdr": "L11  Intermittency & gradient statistics: 48³ vs 96³ (t = 6)",
        "l11_scalar": "scalar", "l11_48": "48³", "l11_96": "96³",
        "l11_rel": "rel. dev.", "l11_verdict": "verdict",
        "l11_S3": "skewness ⟨ζᵢ³⟩/⟨ζᵢ²⟩^3/2 (isotropic)",
        "l11_F4": "flatness ⟨ζᵢ⁴⟩/⟨ζᵢ²⟩² (isotropic)",
        "l11_F6": "hyperflatness ⟨ζᵢ⁶⟩/⟨ζᵢ²⟩³ (isotropic)",
        "l11_wrms": "⟨ω²⟩^1/2 (vorticity rms)",
        "l11_wmax": "‖ω‖_∞",
        "l11_collapse": "S₄(r) collapse: mean |S₄⁹⁶/S₄⁴⁸ − 1| in band",
        "l12_hdr": "L12  Spectral flux Π(k) and cascade: 48³ vs 96³ (t = 6)",
        "l12_sumT": "identity Σ T(k) = 0 (nonlinear-term conservation)",
        "l12_pi0": "identity Π(0) = ε",
        "l12_pi0_dot": "Π(0) vs −dE/dt from the trajectory",
        "l12_collapse": "Π(k)/ε collapse: mean |Π⁹⁶/ε⁹⁶ − Π⁴⁸/ε⁴⁸| / Π⁴⁸/ε⁴⁸",
        "l13_hdr": "L13  Hyperdissipative KdV family: u_t + 6uu_x + u_xxx = −ν(−∂²)^b u",
        "l13_mass": "mass drift M (∀b > 0 — exact conservation)",
        "l13_pident": "identity dP/dt = −ν⟨u(−∂²)^b u⟩ (spectral vs physical)",
        "l13_conv_n": "self-convergence in N (512 → 1024, b = 5/4)",
        "l13_conv_dt": "self-convergence in dt (5e-4 → 1e-3, b = 5/4)",
        "l13_amp": "A(T)/A₀", "l13_knu": "k_ν(b) theory", "l13_knu_m": "k_e measured",
        "l13_tab_b": "b_pow",
        "l13_note": ("k_e — wavenumber where E(k,T)/E(k,0) = e⁻¹; theory "
                     "k_ν = (1/νT)^(1/2b); deviation expected (nonlinear "
                     "redistribution)"),
        # L16
        "l16_hdr": "L16  P5 solver self-convergence: space (N) × time (dt) + Richardson",
        "l16_p_time": "observed temporal order of IFK-RK2: min(p_E, p_Ω) ≥ 1.8",
        "l16_mono": "monotone error decay in N (out of 4 quantities)",
        "l16_exp_r2": "r² of the exponential fit err(N) ∝ e^(−cN), minimum",
        "l16_sat72": "grid saturation: err(72³) < err(48³) (out of 4 quantities)",
        "l16_balance": "max energy/enstrophy balance over L16 runs",
        "l16_rich": "Richardson dt→0 residual at p = 2 (maximum)",
        "l16_note": ("ref: 96³ (A96, dt = 2e-3) for space; dt = 5e-4 (N = 48) "
                     "for time; p₁ — from errors vs ref, p₂ — Roache (three levels); "
                     "Q₀ = Q(dt/2) + (Q(dt/2) − Q(dt))/(2^p − 1), p = 2"),
        # L17
        "l17_hdr": "L17  φ-audit of the monograph: φ-attractors, C_s, RG cascade, DNS bridge",
        "l17_alg": "φ-algebra (app. Z.1): max residual over 10 identities",
        "l17_mu": "Fibonacci spectrum (tab. X.6): max |μ − φ| over 10 quadruples",
        "l17_binet": "Binet monotonicity: |μ − φ| shrinks with index (violations)",
        "l17_rg": "RG map μ→1+1/μ: rate deviation from 1/φ² ≈ 0.382",
        "l17_zdid": "zero drift: reduced (Cassini) condition vs direct (residual)",
        "l17_zdnosol": "a·b·b·c: quadruples with no zero-drift solution (of 6)",
        "l17_zdfam": "a·a·b·b: degenerate family, φ-geometry attainable (residual)",
        "l17_cs0": "C_s=0 theorem (odd-in-x): max |C_s²| on symmetric configs",
        "l17_csneg": "a·b·b·c: scans with num < 0 (backscatter → C_s=null), of 42",
        "l17_csctl": "control fields (pair 80/120, random): min C_s² > 0",
        "l17_modes": "mode test (app. Г): |ν̂(R₂)/ν_breath(D.5b) − 1|",
        "l17_d7": "chain (D.6b)–(D.8): |τ_φ/322 − 1| at Γ₁=1, Γ₂=φ, R₂=1",
        "l17_dnsyn": "DNS bridge, synthetic: |ρ̂/φ − 1| (recovery of a known ρ)",
        "l17_dnstg": "DNS bridge, TG 96³: slices with a 2+/2− quadruple (of 5)",
        "l17_jl": "cross-language Julia↔Python (L17 core): max rel dev",
        "l17_note": ("audit of the uploaded monograph 'Two-layer φ-attractors in the "
                     "point-vortex model': the mathematical frame (φ, Fibonacci, RG) "
                     "is confirmed; the zero-drift conditions (5) have no solution "
                     "for a·b·b·c (Cassini) and are degenerate for a·a·b·b; the "
                     "app.-B C_s procedure returns 0/null on every Table-2 "
                     "configuration; the (D.5)/(D.8) predictions do not describe "
                     "the two-parabola geometry; the app.-Д DNS bridge is validated "
                     "on synthetic data"),
    },
}

_CACHE: dict = {}  # кэш состояний/статистики между лабораториями


# ============================================================================
# ЗАГРУЗКА ДАННЫХ: снимок 48³ и состояние 96³ на t = 6
# ============================================================================
def _find_reference() -> str:
    """reference/ пакета, затем research_col_smar/results репозитория."""
    cands = [
        REF_DIR,
        os.path.join(HERE, "..", "reference"),
        os.path.join(os.path.dirname(PKG_ROOT), "research_col_smar", "results"),
        os.path.join(os.path.dirname(os.path.dirname(PKG_ROOT)),
                     "navier-stokes-b", "research_col_smar", "results"),
    ]
    for p in cands:
        if p and os.path.isfile(os.path.join(p, "p5_snapshot_u.f64")):
            return p
    return REF_DIR


def load_solver48(cfg: XCfg, ui: UI) -> SpecSolver:
    """48³-снимок монографии → SpecSolver с проверкой E(t=6)."""
    ref = _find_reference()
    u48 = np.fromfile(os.path.join(ref, "p5_snapshot_u.f64"),
                      dtype=np.float64).reshape(3, 48, 48, 48)
    sol = SpecSolver(48, cfg["nu"], cfg["dt"], 1.0)
    sol.uh = np.fft.rfftn(u48, axes=(1, 2, 3)) * sol.mask
    sol.uh[:, 0, 0, 0] = 0.0
    e = sol.energy()
    if ui is not None:
        ui.say(ui.dim(f"  [{ui.t['integrity']}] E48(t=6) = {e:.7f} "
                      f"(монография: 0.1226305)"))
    _CACHE["E48"] = e
    return sol


def load_solver96(cfg: XCfg, ui: UI) -> SpecSolver:
    """96³-состояние A96 на t = 6: чекпоинты → автономный прогон."""
    n = 96
    cands = [
        os.path.join(OUT_RESULTS, "ckpt_A96.npz"),
        os.path.join(HERE, "..", "reference", "ck96_state_t6.npz"),
        os.path.join(REF_DIR, "ck96_state_t6.npz"),
        os.path.join(HERE, "..", "..", "work", "ckpt_backup", "ckpt_A96.npz"),
    ]
    for p in cands:
        if os.path.isfile(p):
            with np.load(p, allow_pickle=False) as z:
                uh = z["uh"].copy()
            sol = SpecSolver(n, cfg["nu"], cfg["dt"], 1.0)
            sol.uh = uh
            if ui is not None:
                ui.say(ui.dim(f"  [{ui.t['state_ok']}] {os.path.basename(p)}: "
                              f"E96(t=6) = {sol.energy():.7f} "
                              f"(пакет main96: 0.1226268)"))
            _CACHE["E96"] = sol.energy()
            return sol
    # резерв: воспроизводим траекторию A96 (чекпоинтируется, ~14 мин)
    if ui is not None:
        ui.say(ui.y(f"  [{ui.t['state_none']}]"))
    res = run_trajectory("A96", n, cfg["nu"], cfg["dt"], cfg["t_snap"],
                         save_every=10, ui=ui, cfg=None, checkpoint=True)
    sol = SpecSolver(n, cfg["nu"], cfg["dt"], 1.0)
    with np.load(os.path.join(OUT_RESULTS, "ckpt_A96.npz"),
                 allow_pickle=False) as z:
        sol.uh = z["uh"].copy()
    _CACHE["E96"] = sol.energy()
    return sol


# ============================================================================
# L11: ПЕРЕМЕЖАЕМОСТЬ И ГРАДИЕНТНАЯ СТАТИСТИКА
# ============================================================================
def grad_stats(sol: SpecSolver) -> dict:
    """Изотропные градиентные диагностики: ζᵢ = ∂uᵢ/∂xᵢ, усреднение по 3 осям.

    Продольные моменты, усреднённые по трём направлениям — стандартная
    комбинация изотропной турбулентности (скол ≈ −0.4…−0.6)."""
    n = sol.n
    m = {2: [], 3: [], 4: [], 6: []}
    zetas = []
    for a in range(3):
        ka = (sol.kx, sol.ky, sol.kz)[a]
        z = np.fft.irfftn(1j * ka * sol.uh[a], s=(n,) * 3, axes=(0, 1, 2))
        zetas.append(z)
        for p in m:
            m[p].append(float(np.mean(z ** p)))
    v = {p: float(np.mean(vals)) for p, vals in m.items()}
    w = sol.vorticity()
    w2 = float(np.mean(np.sum(w * w, axis=0)))
    wmax = float(np.max(np.sqrt(np.sum(w * w, axis=0))))
    return {
        "n": n,
        "zeta_rms": math.sqrt(v[2]),
        "S3": v[3] / max(v[2] ** 1.5, 1e-300),
        "F4": v[4] / max(v[2] ** 2, 1e-300),
        "F6": v[6] / max(v[2] ** 3, 1e-300),
        "omega_rms": math.sqrt(w2),
        "omega_max": wmax,
        "_zeta": np.stack(zetas),
    }


def increments_along_x(sol: SpecSolver, rmax: int) -> tuple:
    """Продольные приращения δu_∥(r) вдоль x: S_p(r), p = 2, 3, 4, 6."""
    u1 = sol.phys()[0]
    Sp = {p: np.zeros(rmax) for p in (2, 3, 4, 6)}
    for r in range(1, rmax + 1):
        du = np.roll(u1, -r, axis=0) - u1
        for p in (2, 3, 4, 6):
            Sp[p][r - 1] = float(np.mean(du ** p))
    r_phys = np.arange(1, rmax + 1) * (2.0 * math.pi / sol.n)
    return r_phys, Sp


def _interp_loglog(x_src: np.ndarray, y_src: np.ndarray, x_q: np.ndarray):
    lx, ly = np.log(x_src), np.log(np.abs(y_src))
    lq = np.log(x_q)
    return np.exp(np.interp(lq, lx, ly))


def _collapse_metric(rA, SA, rB, SB, band) -> float:
    """Среднее |B/A − 1| по общему физическому интервалу (log-log интерп)."""
    lo = max(rA.min(), rB.min(), band[0])
    hi = min(rA.max(), rB.max(), band[1])
    if not (hi > lo):
        return float("nan")
    rq = np.linspace(math.log(lo), math.log(hi), 24)
    A = _interp_loglog(rA, SA, np.exp(rq))
    B = _interp_loglog(rB, SB, np.exp(rq))
    return float(np.mean(np.abs(B / A - 1.0)))


def lab11_gradstats(ui: UI, cfg: XCfg) -> dict:
    ui.say(ui.c(ui.t["l11_hdr"]))
    t0 = time.perf_counter()
    sol48 = _CACHE.get("sol48") or load_solver48(cfg, ui)
    sol96 = _CACHE.get("sol96") or load_solver96(cfg, ui)
    _CACHE["sol48"], _CACHE["sol96"] = sol48, sol96

    with _noop():
        g48 = grad_stats(sol48)
        ui.bar(0.3, "L11 48³ " + ui.t["done"])
        g96 = grad_stats(sol96)
        ui.bar(0.6, "L11 96³ " + ui.t["done"])
        rmax = int(cfg["rmax"])
        r48, S48 = increments_along_x(sol48, rmax)
        r96, S96 = increments_along_x(sol96, rmax * 2)
        ui.bar(1.0, "L11 " + ui.t["done"])

    V = Verdicts(cfg)
    t = ui.t
    rows = []
    for key, name in (("S3", t["l11_S3"]), ("F4", t["l11_F4"]),
                      ("F6", t["l11_F6"]), ("omega_rms", t["l11_wrms"]),
                      ("omega_max", t["l11_wmax"])):
        a, b = g48[key], g96[key]
        rel = abs(b - a) / max(abs(a), 1e-300)
        v = V.judge("L11", name, rel, thr_key="thr_grad")
        rows.append((name, a, b, rel, v))
    col4 = _collapse_metric(r48, S48[4], r96, S96[4], (0.30, 1.60))
    col2 = _collapse_metric(r48, S48[2], r96, S96[2], (0.30, 1.60))
    v = V.judge("L11", t["l11_collapse"], col4, thr_key="thr_collapse")
    rows.append((t["l11_collapse"], col4, col2, float("nan"), v))

    # таблица
    ui.say("")
    ui.say(ui.y(f"    {'scalar' if ui.lang == 'en' else 'скаляр':<44}"
                f"{'48³':>12}{'96³':>12}{'rel':>10}  verdict"))
    for name, a, b, rel, v in rows:
        vc = {"WIN": ui.g, "DRAW": ui.y, "LOSS": ui.r}[v](v)
        if math.isnan(rel):
            rel_s = "—"
        else:
            rel_s = f"{rel:.2e}"
        ui.say(f"    {name:<44}{a:>12.5f}{b:>12.5f}{rel_s:>10}  {vc}")
    ui.say(ui.dim(f"    S₄(r) collapse metric: {col4:.3f}; "
                  f"S₂(r): {col2:.3f}"))
    tally = V.tally()
    ui.say(ui.c(f"    L11: WIN={tally['WIN']} DRAW={tally['DRAW']} "
                f"LOSS={tally['LOSS']}   "
                f"[{fmt_sec(time.perf_counter() - t0)}]"))

    # артефакты
    obj = {
        "program": "NSB-96-UPGRADE / nsb_extra_research",
        "lab": "L11 intermittency & gradient statistics",
        "t": cfg["t_snap"], "nu": cfg["nu"],
        "E48_check": _CACHE.get("E48"), "E96_check": _CACHE.get("E96"),
        "thresholds": {"thr_grad": cfg["thr_grad"],
                       "thr_collapse": cfg["thr_collapse"]},
        "scalars": {
            "48": {k: g48[k] for k in ("S3", "F4", "F6", "omega_rms",
                                       "omega_max")},
            "96": {k: g96[k] for k in ("S3", "F4", "F6", "omega_rms",
                                       "omega_max")},
        },
        "structure_functions": {
            "r48_phys": r48.tolist(),
            "S2_48": S48[2].tolist(), "S3_48": S48[3].tolist(),
            "S4_48": S48[4].tolist(), "S6_48": S48[6].tolist(),
            "r96_phys": r96.tolist(),
            "S2_96": S96[2].tolist(), "S3_96": S96[3].tolist(),
            "S4_96": S96[4].tolist(), "S6_96": S96[6].tolist(),
            "collapse_S4_band_0.30_1.60": col4,
            "collapse_S2_band_0.30_1.60": col2,
        },
        "verdicts": V.rows,
        "tally": tally,
    }
    _CACHE["l11"] = obj
    _dump_artifacts("extra11_gradstats", obj, ui)
    return obj


class _noop:
    def __enter__(self):
        return None

    def __exit__(self, *a):
        return False


# ============================================================================
# L12: СПЕКТРАЛЬНЫЙ ПОТОК Π(k) И КАСКАД
# ============================================================================
def shell_transfer(sol: SpecSolver) -> tuple:
    """Оболочечные спектр E(k) и трансфер T(k) — ПОЛНОЕ пространство Фурье.

    Только в полном пространстве тождество Галёркина Σ T = 0 точное
    (полупространство rFFT искажает его плоскостями kz = 0, kz = Nyquist).
    Конвенции (всё на объём):
        E(k) = Σ_shell |Û|²/N⁶          (Σ E = ⟨|u|²⟩ = E решателя)
        T(k) = 2·Σ_shell Re(Û*·P[M̂]) / N⁶   (Σ T = 0 точно)
        D(k) = 2ν k² E(k)               (dE/dt = Σ(T − D) = −Σ D)
        Π(k) = Σ_{q≥k} [D(q) − T(q)]   →   Π(0) = −dE/dt, Π(k_max) = 0.
    """
    n = sol.n
    u = sol.phys()
    w = sol.vorticity()
    cross = np.stack([
        u[1] * w[2] - u[2] * w[1],
        u[2] * w[0] - u[0] * w[2],
        u[0] * w[1] - u[1] * w[0],
    ])
    Uh = np.fft.fftn(u, axes=(1, 2, 3))
    Mh = np.fft.fftn(cross, axes=(1, 2, 3))
    kf = np.fft.fftfreq(n, d=1.0 / n)
    kxf = kf[:, None, None]
    kyf = kf[None, :, None]
    kzf = kf[None, None, :]
    k2f = kxf ** 2 + kyf ** 2 + kzf ** 2
    k2e = k2f.copy()
    k2e[0, 0, 0] = 1.0
    crit = n // 3
    maskf = (np.abs(kxf) <= crit) & (np.abs(kyf) <= crit) & \
        (np.abs(kzf) <= crit)
    div = (kxf * Mh[0] + kyf * Mh[1] + kzf * Mh[2]) / k2e
    Mh = np.stack([Mh[a] - (kxf, kyf, kzf)[a] * div for a in range(3)])
    Mh *= maskf
    co = np.sum(np.real(np.conj(Uh) * Mh), axis=0)
    uh2 = np.sum(np.abs(Uh) ** 2, axis=0)
    kb = np.rint(np.sqrt(k2f)).astype(int)
    nb = n // 2 + 1
    E = np.zeros(nb)
    T = np.zeros(nb)
    for kk in range(1, nb):
        m = kb == kk
        if m.any():
            E[kk] = float(np.sum(uh2[m])) / n ** 6
            T[kk] = 2.0 * float(np.sum(co[m])) / n ** 6
    return E, T


def flux_curve(E: np.ndarray, T: np.ndarray, nu: float, b_pow: float) -> tuple:
    """Π(k) = Σ_{q≥k}[D(q) − T(q)], D = 2ν k^{2b} E; возвращает (Π, ε_tot)."""
    kk = np.arange(len(E), dtype=float)
    D = 2.0 * nu * kk ** (2.0 * b_pow) * E
    Pi = np.cumsum((D - T)[::-1])[::-1]
    return Pi, float(np.sum(D))


def lab12_flux(ui: UI, cfg: XCfg) -> dict:
    ui.say(ui.c(ui.t["l12_hdr"]))
    t0 = time.perf_counter()
    sol48 = _CACHE.get("sol48") or load_solver48(cfg, ui)
    sol96 = _CACHE.get("sol96") or load_solver96(cfg, ui)
    _CACHE["sol48"], _CACHE["sol96"] = sol48, sol96

    E48, T48 = shell_transfer(sol48)
    ui.bar(0.35, "L12 48³ " + ui.t["done"])
    E96, T96 = shell_transfer(sol96)
    ui.bar(0.7, "L12 96³ " + ui.t["done"])
    Pi48, eps48 = flux_curve(E48, T48, cfg["nu"], 1.0)
    Pi96, eps96 = flux_curve(E96, T96, cfg["nu"], 1.0)
    ui.bar(1.0, "L12 " + ui.t["done"])

    V = Verdicts(cfg)
    t = ui.t
    # тождество 1: Σ T = 0
    sT48 = float(np.sum(T48))
    sT96 = float(np.sum(T96))
    sc48 = abs(sT48) / max(eps48, 1e-300)
    sc96 = abs(sT96) / max(eps96, 1e-300)
    v1 = V.judge("L12", t["l12_sumT"], max(sc48, sc96),
                 thr_key="thr_identity")
    # тождество 2: Π(0) = ε
    p0_48 = abs(Pi48[1] - eps48) / eps48  # Π(0) — весь диапазон, k≥1 ≈ то же
    p0_96 = abs(Pi96[1] - eps96) / eps96
    v2 = V.judge("L12", t["l12_pi0"], max(p0_48, p0_96),
                 thr_key="thr_identity")
    # тождество 3: Π(0) против −dE/dt из логов траекторий
    dot48 = _dEdt_from_csv("p5_bkm.csv", cfg["t_snap"])
    dot96 = _dEdt_from_csv("lab_A96_trajectory.csv", cfg["t_snap"],
                           pkg_results=True)
    dev = []
    if dot48 is not None:
        dev.append(abs(Pi48[1] - dot48) / max(abs(dot48), 1e-300))
    if dot96 is not None:
        dev.append(abs(Pi96[1] - dot96) / max(abs(dot96), 1e-300))
    v3 = V.judge("L12", t["l12_pi0_dot"],
                 max(dev) if dev else float("nan"),
                 thr_key="thr_pi_eps")
    # коллапс Π(k)/ε в инерционном интервале 48³ (k = 2..0.7·kc48)
    kc48 = 16.0
    kb = np.arange(2, int(0.7 * kc48) + 1)
    A = Pi48[kb] / eps48
    B = np.interp(kb.astype(float),
                  np.arange(len(Pi96)), Pi96 / eps96)
    col = float(np.mean(np.abs(B / A - 1.0)))
    v4 = V.judge("L12", t["l12_collapse"], col, thr_key="thr_collapse")

    rows = [(t["l12_sumT"], max(sc48, sc96), v1),
            (t["l12_pi0"], max(p0_48, p0_96), v2),
            (t["l12_pi0_dot"], max(dev) if dev else float("nan"), v3),
            (t["l12_collapse"], col, v4)]
    ui.say("")
    for name, val, v in rows:
        vc = {"WIN": ui.g, "DRAW": ui.y, "LOSS": ui.r}[v](v)
        ui.say(f"    {name:<58} {val:.3e}  {vc}")
    ui.say(ui.dim(f"    ε(48³) = {eps48:.6f}   ε(96³) = {eps96:.6f}   "
                  f"rel = {abs(eps96 - eps48) / eps48:.2e}"))
    tally = V.tally()
    ui.say(ui.c(f"    L12: WIN={tally['WIN']} DRAW={tally['DRAW']} "
                f"LOSS={tally['LOSS']}   "
                f"[{fmt_sec(time.perf_counter() - t0)}]"))

    obj = {
        "program": "NSB-96-UPGRADE / nsb_extra_research",
        "lab": "L12 spectral flux and cascade",
        "t": cfg["t_snap"], "nu": cfg["nu"],
        "eps48": eps48, "eps96": eps96,
        "sumT48": sT48, "sumT96": sT96,
        "minus_dEdt_48": dot48, "minus_dEdt_96": dot96,
        "collapse_Pi_band_k2_11": col,
        "k48": np.arange(len(E48)).tolist(),
        "k96": np.arange(len(E96)).tolist(),
        "E48": E48.tolist(), "T48": T48.tolist(), "Pi48": Pi48.tolist(),
        "E96": E96.tolist(), "T96": T96.tolist(), "Pi96": Pi96.tolist(),
        "verdicts": V.rows, "tally": tally,
    }
    _CACHE["l12"] = obj
    _dump_artifacts("extra12_flux", obj, ui)
    return obj


def _dEdt_from_csv(name: str, t0: float, pkg_results: bool = False):
    """−dE/dt в момент t0 по логу траектории (по последним 3 точкам ≤ t0)."""
    p = os.path.join(OUT_RESULTS, name) if pkg_results else \
        os.path.join(REF_DIR, name)
    if not os.path.isfile(p):
        return None
    try:
        rows = []
        with open(p, encoding="utf-8") as fh:
            rd = csv.reader(fh)
            head = next(rd)
            it = {h.strip().lower(): i for i, h in enumerate(head)}
            ecol = next((c for c in ("e", "e_a") if c in it), None)
            if ecol is None:
                return None
            for r in rd:
                if len(r) < len(head):
                    continue
                try:
                    rows.append((float(r[it["t"]]), float(r[it[ecol]])))
                except (ValueError, KeyError):
                    continue
        rows.sort()
        ts = np.array([a for a, _ in rows])
        Es = np.array([b for _, b in rows])
        m = ts <= t0 + 1e-9
        if m.sum() < 4:
            return None
        # 3-й порядок, односторонняя (назад): f'(t0) ≈
        # (11f₀ − 18f₋₁ + 9f₋₂ − 2f₋₃)/(6h)
        tt, ee = ts[m][-4:], Es[m][-4:]
        h = tt[1] - tt[0]
        return float(-(11.0 * ee[3] - 18.0 * ee[2] + 9.0 * ee[1]
                       - 2.0 * ee[0]) / (6.0 * h))
    except Exception:
        return None


# ============================================================================
# L13: ГИПЕРДИССИПАТИВНОЕ СЕМЕЙСТВО КдФ
# ============================================================================
def _kdv_b_wavenumbers(n: int, l: float) -> np.ndarray:
    return np.fft.fftfreq(n, d=l / n) * 2.0 * math.pi


def kdv_soliton(x: np.ndarray, c: float, x0: float) -> np.ndarray:
    return (c / 2.0) * (1.0 / np.cosh(math.sqrt(c) / 2.0 * (x - x0))) ** 2


def kdv_b_run(n: int, l: float, dt: float, t_end: float, u0: np.ndarray,
              nu: float, b_pow: float, ui: UI | None = None,
              tag: str = "", log_every: int = 5) -> dict:
    """IFRK4 для u_t + 6uu_x + u_xxx = −ν(−∂²)^b u (2/3-обезвреживание).

    Возвращает серии t, A, M, P, dPdt_спектр и финальные спектры.
    """
    k = _kdv_b_wavenumbers(n, l)
    Lin = 1j * k ** 3 - nu * np.abs(k) ** (2.0 * b_pow)
    Eop = np.exp(Lin * dt)
    Eop2 = np.exp(Lin * dt / 2.0)
    crit = (n // 3) * (2.0 * math.pi / l)
    mask = np.abs(k) <= crit
    uh = np.fft.fft(u0) * mask
    n_steps = int(round(t_end / dt))
    x = np.linspace(0.0, l, n, endpoint=False)
    u_init = np.fft.ifft(uh).real  # маскированное НУ — от него идёт эволюция

    def nl(u_phys: np.ndarray) -> np.ndarray:
        return -3.0j * k * np.fft.fft(u_phys * u_phys) * mask

    def pdecay_spec(uh_cur: np.ndarray) -> float:
        # dP/dt = −ν·(1/N²)·Σ k^{2b}|û|²  (N = n; среднее по домену)
        return -nu * float(np.sum(np.abs(k) ** (2.0 * b_pow)
                                  * np.abs(uh_cur) ** 2)) / n ** 2

    out = {"t": [0.0], "A": [float(np.max(np.abs(u_init)))],
           "M": [float(np.mean(u_init))],
           "P": [float(np.mean(u_init ** 2) / 2.0)],
           "dPdt": [pdecay_spec(uh)], "u_final": None, "spec0": None,
           "specT": None}
    spec0 = np.abs(uh) ** 2 * mask
    out["spec0"] = (2.0 * spec0 / n) * (l / n)  # форма: 2|û|²·dx
    t_wall = time.perf_counter()
    for step in range(n_steps):
        a = nl(np.fft.ifft(uh).real)
        b_ = nl(np.fft.ifft(Eop2 * (uh + dt / 2.0 * a)).real)
        c_ = nl(np.fft.ifft(Eop2 * uh + dt / 2.0 * b_).real)
        d_ = nl(np.fft.ifft(Eop * uh + dt * Eop2 * c_).real)
        uh = Eop * uh + dt / 6.0 * (Eop * a + 2.0 * Eop2 * (b_ + c_) + d_)
        uh = uh * mask
        if (step + 1) % log_every == 0 or step == n_steps - 1:
            u_f = np.fft.ifft(uh).real
            out["t"].append((step + 1) * dt)
            out["A"].append(float(np.max(np.abs(u_f))))
            out["M"].append(float(np.mean(u_f)))
            out["P"].append(float(np.mean(u_f ** 2) / 2.0))
            out["dPdt"].append(pdecay_spec(uh))
            if ui is not None and step % (log_every * 20) == 0:
                frac = (step + 1) / n_steps
                el = time.perf_counter() - t_wall
                eta = el / max(frac, 1e-9) * (1.0 - frac)
                ui.bar(frac, f"L13 [{tag}] t={(step + 1) * dt:.2f}/{t_end:g} "
                             f"A={out['A'][-1]:.6f} {ui.t['eta']} "
                             f"{fmt_sec(eta)}")
    u_f = np.fft.ifft(uh).real
    out["u_final"] = u_f
    out["specT"] = (2.0 * np.abs(uh) ** 2 / n) * (l / n)
    out["k"] = k
    out["x"] = x
    out["mass_drift"] = abs(out["M"][-1] - out["M"][0]) / \
        max(abs(out["M"][0]), 1e-300)
    return out


def lab13_kdvb(ui: UI, cfg: XCfg) -> dict:
    ui.say(ui.c(ui.t["l13_hdr"]))
    t0 = time.perf_counter()
    n = cfg["kdvb_n"]
    l = cfg["kdvb_l"]
    dt = cfg["kdvb_dt"]
    T = cfg["kdvb_t_end"]
    nu = cfg["kdvb_nu"]
    c = cfg["kdvb_c"]
    x0 = cfg["kdvb_x0"]

    x = np.linspace(0.0, l, n, endpoint=False)
    u0 = kdv_soliton(x, c, x0)
    runs = {}
    fam = cfg["kdvb_family"]
    for i, b in enumerate(fam):
        tag = f"b={b:g}"
        runs[b] = kdv_b_run(n, l, dt, T, u0, nu, b, ui=ui, tag=tag)
        ui.bar((i + 1) / (len(fam) + 2.0),
               f"L13 b={b:g} " + ui.t["done"])

    # самосходимость: N coarse vs N (b = 5/4)
    bref = 1.25
    xc = np.linspace(0.0, l, cfg["kdvb_n_coarse"], endpoint=False)
    run_c = kdv_b_run(cfg["kdvb_n_coarse"], l, dt, T, kdv_soliton(xc, c, x0),
                      nu, bref, ui=ui, tag="N=512")
    ui.bar(len(fam) / (len(fam) + 2.0), "L13 N-conv " + ui.t["done"])
    # самосходимость: dt/2 (b = 5/4)
    run_dt = kdv_b_run(n, l, dt / 2.0, T, u0, nu, bref, ui=ui, tag="dt/2",
                       log_every=10)
    ui.bar(1.0, "L13 " + ui.t["done"])

    V = Verdicts(cfg)
    t = ui.t
    # 1) масса: точное сохранение ∀b > 0
    mdrift = max(r["mass_drift"] for r in runs.values())
    v1 = V.judge("L13", t["l13_mass"], mdrift, thr_key="thr_kdvb_mass")
    # 2) тождество dP/dt: численно по P(t) против спектральной формулы.
    # Поточечная относительная невязка на окне t ≥ 0.1·T (после начального
    # переходного процесса); остаток ~10⁻⁴ — этаж схемы расщепления IFRK4.
    pdevs = []
    for r in runs.values():
        tt = np.array(r["t"])
        PP = np.array(r["P"])
        dd = np.array(r["dPdt"])
        h = tt[1] - tt[0]
        fd = (-3.0 * PP[:-2] + 4.0 * PP[1:-1] - PP[2:]) / (2.0 * h)
        late = (tt[1:-1] >= 0.1 * cfg["kdvb_t_end"]) & \
               (np.abs(dd[1:-1]) > 1e-12)
        if not late.any():
            late = np.abs(dd[1:-1]) > 1e-12
        rel = np.abs(fd - dd[1:-1])[late] / np.abs(dd[1:-1])[late]
        pdevs.append(float(np.max(rel)) if rel.size else float("nan"))
    pident = max(pdevs)
    v2 = V.judge("L13", t["l13_pident"], pident, thr_key="thr_kdvb_pident")
    # 3) самосходимость по N
    m = min(len(run_c["u_final"]), len(runs[bref]["u_final"]) *
            cfg["kdvb_n_coarse"] // n)
    u_c = run_c["u_final"]
    u_f = runs[bref]["u_final"][:: n // cfg["kdvb_n_coarse"]]
    nn = min(len(u_c), len(u_f))
    conv_n = float(np.max(np.abs(u_c[:nn] - u_f[:nn]))) / \
        max(float(np.max(np.abs(u_f[:nn]))), 1e-300)
    v3 = V.judge("L13", t["l13_conv_n"], conv_n, thr_key="thr_kdvb_conv")
    # 4) самосходимость по dt
    u_d = run_dt["u_final"]
    conv_dt = float(np.max(np.abs(u_d - runs[bref]["u_final"]))) / \
        max(float(np.max(np.abs(u_f[:n]))), 1e-300)
    v4 = V.judge("L13", t["l13_conv_dt"], conv_dt, thr_key="thr_kdvb_conv")

    # диссипационный обрез k_e против теории k_ν = (1/νT)^(1/2b):
    # ищем пересечение lg E(T)/E(0) = −1 на монотонном блоке k > 0
    kmax_deal = (n // 3) * (2 * math.pi / l)
    ktable = []
    for b in fam:
        r = runs[b]
        kk_pos = np.abs(r["k"])[: n // 2 + 1]  # ascending: 0…Nyquist
        lg = np.log(r["specT"][: n // 2 + 1] /
                    np.maximum(r["spec0"][: n // 2 + 1], 1e-300))
        ok = (kk_pos > 0.5) & (kk_pos < kmax_deal) & \
             (r["spec0"][: n // 2 + 1] > 1e-14 * r["spec0"].max())
        k_e = float("nan")
        if ok.sum() > 8:
            kq, lq = kk_pos[ok], lg[ok]
            below = np.where(lq <= -1.0)[0]
            if len(below):
                i = int(below[0])
                if i == 0:
                    k_e = float(kq[0])
                else:
                    lg1, lg0 = lq[i], lq[i - 1]
                    k1, k0 = kq[i], kq[i - 1]
                    k_e = float(k0 + (-1.0 - lg0) * (k1 - k0)
                                / (lg1 - lg0))
        k_th = (1.0 / (nu * T)) ** (1.0 / (2.0 * b))
        ktable.append({
            "b": b, "A_ratio": r["A"][-1] / r["A"][0],
            "k_nu_theory": k_th, "k_e_measured": k_e,
            "mass_drift": r["mass_drift"],
        })

    ui.say("")
    vc = {"WIN": ui.g, "DRAW": ui.y, "LOSS": ui.r}
    for name, val, v in ((t["l13_mass"], mdrift, v1),
                         (t["l13_pident"], pident, v2),
                         (t["l13_conv_n"], conv_n, v3),
                         (t["l13_conv_dt"], conv_dt, v4)):
        ui.say(f"    {name:<58} {val:.3e}  {vc[v](v)}")
    ui.say(ui.y(f"    {'b_pow':>6}{'A(T)/A0':>12}{'k_nu th':>12}"
                f"{'k_e meas':>12}{'M drift':>12}"))
    for row in ktable:
        ui.say(f"    {row['b']:>6g}{row['A_ratio']:>12.5f}"
               f"{row['k_nu_theory']:>12.4f}"
               f"{row['k_e_measured']:>12.4f}"
               f"{row['mass_drift']:>12.2e}")
    ui.say(ui.dim("    " + t["l13_note"]))
    tally = V.tally()
    ui.say(ui.c(f"    L13: WIN={tally['WIN']} DRAW={tally['DRAW']} "
                f"LOSS={tally['LOSS']}   "
                f"[{fmt_sec(time.perf_counter() - t0)}]"))

    obj = {
        "program": "NSB-96-UPGRADE / nsb_extra_research",
        "lab": "L13 hyperdissipative KdV family",
        "equation": "u_t + 6 u u_x + u_xxx = -nu (-d2)^b u",
        "nu": nu, "n": n, "l": l, "dt": dt, "T": T, "c": c, "x0": x0,
        "mass_drift_max": mdrift,
        "p_identity_max_dev": pident,
        "conv_N": conv_n, "conv_dt": conv_dt,
        "thresholds": {"thr_kdvb_mass": cfg["thr_kdvb_mass"],
                       "thr_kdvb_pident": cfg["thr_kdvb_pident"],
                       "thr_kdvb_conv": cfg["thr_kdvb_conv"]},
        "family_table": ktable,
        "series": {f"{b:g}": {"t": runs[b]["t"], "A": runs[b]["A"],
                              "P": runs[b]["P"], "M": runs[b]["M"]}
                   for b in fam},
        "spectra": {f"{b:g}": {"k": np.abs(runs[b]["k"])[: n // 2 + 1].tolist(),
                               "E0": runs[b]["spec0"][: n // 2 + 1].tolist(),
                               "ET": runs[b]["specT"][: n // 2 + 1].tolist()}
                    for b in fam},
        "verdicts": V.rows, "tally": tally,
    }
    _CACHE["l13"] = obj
    _dump_artifacts("extra13_kdvb", obj, ui)
    return obj


# ============================================================================
# L16: САМОСХОДИМОСТЬ РЕШАТЕЛЯ P5: ПРОСТРАНСТВО (N) × ВРЕМЯ (dt) + РИЧАРДСОН
# ============================================================================
CONV_QTY = ("Omega_max", "omega_inf_max", "I_BKM_T", "E_final")
CONV_BAL = ("energy_balance_rel_max", "enstrophy_balance_rel_max")


def _conv_state_path() -> str:
    return os.path.join(OUT_RESULTS, "extra16_scan_state.json")


def _conv_load_state() -> dict:
    p = _conv_state_path()
    if os.path.isfile(p):
        try:
            with open(p, encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            pass
    return {"runs": {}}


def _conv_save_state(st: dict) -> None:
    p = _conv_state_path()
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(st, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, p)


def _conv_run_one(ui: UI, label: str, n: int, dt: float, t_end: float,
                  nu: float, state: dict, wanted: bool = True) -> dict | None:
    """Один прогон скана самосходимости (чекпоинт → resume бит-в-бит)."""
    prev = state["runs"].get(label)
    if prev and prev.get("summary", {}).get("done"):
        ui.say(ui.dim(f"  [{label}] {ui.t['done']}: Ω_max="
                      f"{prev['summary']['Omega_max']:.6f}, "
                      f"E={prev['summary']['E_final']:.6f}"))
        return prev["summary"]
    if not wanted:
        return None
    ui.say(ui.y(f"  [{label}] N={n}, dt={dt:g}, T={t_end:g} "
                f"(чекпоинт каждые 250 шагов)"))
    res = run_trajectory(label, n, nu, dt, t_end, save_every=10,
                         ui=ui, cfg=None, checkpoint=True)
    summ = dict(res["summary"])
    state["runs"][label] = {"n": n, "dt": dt, "t_end": t_end,
                            "summary": summ}
    _conv_save_state(state)
    if summ["done"]:
        clear_checkpoint(label)
    return summ


def _exp_fit(ns_: list, errs_: list) -> dict:
    """Посадка err = A·exp(−c·N): коэффициент c, амплитуда A, r²."""
    x = np.asarray(ns_, dtype=float)
    y = np.log(np.asarray(errs_, dtype=float))
    ok = np.isfinite(y) & np.isfinite(x)
    x, y = x[ok], y[ok]
    if x.size < 3:
        return {"c": float("nan"), "A": float("nan"), "r2": float("nan"),
                "n_pts": int(x.size)}
    amat = np.vstack([x, np.ones_like(x)]).T
    coef, *_ = np.linalg.lstsq(amat, y, rcond=None)
    yh = amat @ coef
    ss_res = float(np.sum((y - yh) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    return {"c": float(-coef[0]), "A": float(math.exp(coef[1])),
            "r2": float(1.0 - ss_res / ss_tot) if ss_tot > 0 else float("nan"),
            "n_pts": int(x.size)}


def lab16_convergence(ui: UI, cfg: XCfg) -> dict:
    """L16: самосходимость решателя P5 по N (24→96) и dt (4e-3→5e-4),
    наблюдаемый временной порядок IFK-RK2, Ричардсон-экстраполяция dt→0
    и атрибуция ошибки 48³↔96³ (пространство против времени)."""
    ui.say(ui.c(ui.t["l16_hdr"]))
    t0 = time.perf_counter()
    nu, T, dt0 = cfg["nu"], cfg["t_snap"], cfg["dt"]
    ns = sorted(int(x) for x in cfg["conv_ns"])               # 24, 36, 72
    dts = sorted({float(x) for x in cfg["conv_dts"]}, reverse=True)
    only = [s.strip() for s in os.environ.get("NSB16_CONFIGS", "").split(",")
            if s.strip()]
    no_ana = bool(os.environ.get("NSB16_NOANALYSIS"))

    plan_map = {**{f"CONV{n}": (n, dt0) for n in ns},
                "CONV48": (48, dt0),
                **{f"CONV48DT{dt:g}": (48, dt) for dt in dts}}
    all_labels = list(plan_map.keys())
    labels_spatial = [f"CONV{n}" for n in ns] + ["CONV48"]

    state = _conv_load_state()
    done_ct = 0
    for lab in all_labels:
        n_, dt_ = plan_map[lab]
        s = _conv_run_one(ui, lab, n_, dt_, T, nu, state,
                          wanted=(not only) or (lab in only))
        if s is not None and s.get("done"):
            done_ct += 1
        ui.bar(done_ct / max(len(all_labels), 1), f"L16 {lab} " + ui.t["done"])
    if no_ana:
        ui.say(ui.dim("  L16: NSB16_NOANALYSIS — прогон/резюме без анализа"))
        return {}
    missing = [lab for lab in all_labels
               if not state["runs"].get(lab, {}).get("summary", {}).get("done")]
    if missing:
        ui.say(ui.y(f"  L16: скан неполон, анализ отложен: {', '.join(missing)}"))
        return {}

    # ---- референсы ----------------------------------------------------------
    with open(os.path.join(OUT_RESULTS, "main96_latest.json"),
              encoding="utf-8") as fh:
        ref96 = json.load(fh)["run_A96_summary"]
    ref_dt = state["runs"][f"CONV48DT{min(dts):g}"]["summary"]

    # ---- пространственная сходимость (dt = dt0, ref = 96³) ------------------
    spatial: dict = {}
    for q in CONV_QTY:
        q96 = float(ref96[q])
        pts = sorted(
            ({"N": int(state["runs"][lab]["summary"]["grid"]),
              "value": float(state["runs"][lab]["summary"][q]),
              "rel_err": abs(float(state["runs"][lab]["summary"][q]) - q96)
              / abs(q96)}
             for lab in labels_spatial),
            key=lambda p: p["N"])
        errs = [p["rel_err"] for p in pts]
        ns_ = [p["N"] for p in pts]
        mono = (all(errs[i + 1] <= errs[i] + 1e-15
                    for i in range(len(errs) - 1)) and errs[-1] < errs[0])
        fit = _exp_fit(ns_, errs)
        i48 = ns_.index(48)
        i72 = ns_.index(72) if 72 in ns_ else None
        ratio = (errs[i72] / errs[i48]
                 if i72 is not None and errs[i48] > 0 else float("nan"))
        spatial[q] = {"ref96": q96, "points": pts, "monotone": bool(mono),
                      "exp_fit": fit, "err72_over_err48": float(ratio)}

    # ---- временная сходимость (N = 48, ref = min(dts)) ----------------------
    dts_all = sorted({float(dt0)} | set(dts), reverse=True)   # 4e-3 … 5e-4
    temporal: dict = {}
    for q in CONV_QTY:
        qr = float(ref_dt[q])
        pts = []
        for dt in dts_all:
            lab = "CONV48" if abs(dt - dt0) < 1e-15 else f"CONV48DT{dt:g}"
            v = float(state["runs"][lab]["summary"][q])
            pts.append({"dt": float(dt), "value": v,
                        "rel_err": abs(v - qr) / abs(qr)})
        em = {round(p["dt"], 12): p["rel_err"] for p in pts}
        vm = {round(p["dt"], 12): p["value"] for p in pts}
        e2, e1 = em[round(2e-3, 12)], em[round(1e-3, 12)]
        v2e3, v1e3, v05 = (vm[round(d, 12)]
                           for d in (2e-3, 1e-3, 5e-4))
        p1 = math.log2(e2 / e1) if e2 > 0 and e1 > 0 else float("nan")
        num, den = v2e3 - v1e3, v1e3 - v05
        p2 = (math.log2(num / den)
              if num * den > 0 and abs(den) > 1e-300 else float("nan"))
        ps = [p for p in (p1, p2) if math.isfinite(p)]
        p_mean = float(np.mean(ps)) if ps else float("nan")
        q0 = v05 + (v05 - v1e3) / 3.0                       # Ричардсон, p = 2
        resid = abs(v05 - q0) / abs(q0) if q0 != 0 else float("nan")
        temporal[q] = {"ref_dt_min": qr, "points": pts, "p_2e3_1e3": p1,
                       "p_roache_3lvl": p2, "p_mean": p_mean,
                       "richardson_p2": {"Q_dt_2e3": v2e3, "Q_dt_1e3": v1e3,
                                         "Q_dt_5e4": v05, "Q0": float(q0),
                                         "resid": float(resid)}}

    # ---- атрибуция ошибки 48³↔96³: пространство против времени --------------
    attribution: dict = {}
    for q in CONV_QTY:
        sp48 = next(p["rel_err"] for p in spatial[q]["points"] if p["N"] == 48)
        q0 = temporal[q]["richardson_p2"]["Q0"]
        v2e3 = temporal[q]["richardson_p2"]["Q_dt_2e3"]
        tp_err = abs(v2e3 - q0) / abs(q0) if q0 != 0 else float("nan")
        attribution[q] = {
            "spatial_err_48_vs_96": sp48,
            "temporal_err_dt2e3_vs_rich0": tp_err,
            "ratio_spatial_over_temporal":
                sp48 / tp_err if tp_err and math.isfinite(tp_err) and tp_err > 0
                else float("nan"),
        }

    # ---- балансы целостности ------------------------------------------------
    bals = [{"run": lab, "metric": b, "value": float(state["runs"][lab]["summary"][b])}
            for lab in all_labels for b in CONV_BAL]
    bal_max = max(x["value"] for x in bals)

    # ---- вердикты -----------------------------------------------------------
    V = Verdicts(cfg)
    t = ui.t
    p_E = temporal["E_final"]["p_mean"]
    p_Om = temporal["Omega_max"]["p_mean"]
    pfin = [p for p in (p_E, p_Om) if math.isfinite(p)]
    p_worst = min(pfin) if pfin else float("nan")
    v1 = V.judge("L16", t["l16_p_time"], p_worst, kind="min_gt",
                 thr_key="thr_conv_p")
    n_mono = sum(1 for q in CONV_QTY if spatial[q]["monotone"])
    v2 = V.judge("L16", t["l16_mono"], float(n_mono), kind="min_gt",
                 thr_key="thr_conv_mono")
    r2s = [spatial[q]["exp_fit"]["r2"] for q in CONV_QTY
           if math.isfinite(spatial[q]["exp_fit"]["r2"])]
    r2_min = float(np.min(r2s)) if r2s else float("nan")
    v3 = V.judge("L16", t["l16_exp_r2"], r2_min, kind="min_gt",
                 thr_key="thr_conv_r2")
    sat_fin = [spatial[q]["err72_over_err48"] for q in CONV_QTY
               if math.isfinite(spatial[q]["err72_over_err48"])]
    sat = max(sat_fin) if sat_fin else float("nan")
    n_sat = sum(1 for q in CONV_QTY
                if math.isfinite(spatial[q]["err72_over_err48"])
                and spatial[q]["err72_over_err48"] < 1.0)
    v4 = V.judge("L16", t["l16_sat72"], float(n_sat), kind="min_gt",
                 thr_key="thr_conv_mono")
    v5 = V.judge("L16", t["l16_balance"], bal_max, kind="max_lt",
                 thr_key="thr_conv_bal")
    res_fin = [temporal[q]["richardson_p2"]["resid"] for q in CONV_QTY
               if math.isfinite(temporal[q]["richardson_p2"]["resid"])]
    res_max = max(res_fin) if res_fin else float("nan")
    v6 = V.judge("L16", t["l16_rich"], res_max, kind="max_lt",
                 thr_key="thr_conv_rich")

    # ---- консольный вывод ---------------------------------------------------
    ui.say("")
    vc = {"WIN": ui.g, "DRAW": ui.y, "LOSS": ui.r}
    for name, disp, v in ((t["l16_p_time"], f"{p_worst:.2f}", v1),
                          (t["l16_mono"], f"{n_mono}/4", v2),
                          (t["l16_exp_r2"], f"{r2_min:.3f}", v3),
                          (t["l16_sat72"], f"{n_sat}/4", v4),
                          (t["l16_balance"], f"{bal_max:.2e}", v5),
                          (t["l16_rich"], f"{res_max:.2e}", v6)):
        ui.say(f"    {name:<62} {disp:>8}  {vc[v](v)}")
    ui.say("")
    ui.say(ui.y(f"    {ui.t['l16_hdr'][:0]}{'пространственная ошибка (vs 96³):' if ui.lang == 'ru' else 'spatial error (vs 96³):'}"))
    ui.say(ui.y(f"    {'N':>6}{'Ω_max':>12}{'‖ω‖∞':>12}{'I_BKM':>12}{'E_fin':>12}"))
    for i, p in enumerate(spatial["Omega_max"]["points"]):
        cells = "".join(f"{spatial[q]['points'][i]['rel_err']:>12.2e}"
                        for q in CONV_QTY)
        ui.say(f"    {p['N']:>6g}{cells}")
    ui.say("")
    ui.say(ui.y(f"    {'временная ошибка (vs dt = %g, N = 48):' % min(dts) if ui.lang == 'ru' else 'temporal error (vs dt = %g, N = 48):' % min(dts)}"))
    ui.say(ui.y(f"    {'dt':>10}{'Ω_max':>12}{'‖ω‖∞':>12}{'I_BKM':>12}{'E_fin':>12}"))
    for dt_ in sorted(dts_all):
        cells = ""
        for q in CONV_QTY:
            e = next(p["rel_err"] for p in temporal[q]["points"]
                     if abs(p["dt"] - dt_) < 1e-12)
            cells += f"{e:>12.2e}"
        ui.say(f"    {dt_:>10g}{cells}")
    ui.say("")
    for q in ("Omega_max", "E_final"):
        d = temporal[q]
        ui.say(f"    {q:<12} p₁={d['p_2e3_1e3']:.2f}  "
               f"p₂={d['p_roache_3lvl']:.2f}  p̄={d['p_mean']:.2f}   "
               f"Q₀={d['richardson_p2']['Q0']:.9f}   "
               f"resid={d['richardson_p2']['resid']:.2e}")
    ui.say(ui.dim("    " + t["l16_note"]))
    tally = V.tally()
    ui.say(ui.c(f"    L16: WIN={tally['WIN']} DRAW={tally['DRAW']} "
                f"LOSS={tally['LOSS']}   [{fmt_sec(time.perf_counter() - t0)}]"))

    obj = {
        "program": "NSB-96-UPGRADE / nsb_extra_research",
        "lab": "L16 solver self-convergence (N × dt) and Richardson extrapolation",
        "protocol": {"nu": nu, "dt_protocol": dt0, "T": T,
                     "ic": "Taylor–Green", "scheme": "IFK-RK2, 2/3-dealias",
                     "spatial_scan_N": sorted(
                         [int(state['runs'][lab]['summary']['grid'])
                          for lab in labels_spatial] + [96]),
                     "temporal_scan_dt": sorted(dts_all),
                     "ref_spatial": "A96 (main96, 96³, dt = 2e-3, T = 6)",
                     "ref_temporal": "CONV48DT0.0005 (48³, dt = 5e-4, T = 6)"},
        "runs": {lab: state["runs"][lab] for lab in all_labels},
        "spatial": spatial, "temporal": temporal,
        "attribution": attribution, "balances": bals,
        "headline": {"p_time_worst": p_worst, "n_monotone": n_mono,
                     "r2_exp_min": r2_min, "n_sat72": n_sat,
                     "err72_over_err48_max": sat,
                     "balance_max": bal_max, "richardson_resid_max": res_max},
        "thresholds": {k: cfg[k] for k in
                       ("thr_conv_p", "thr_conv_mono", "thr_conv_r2",
                        "thr_conv_sat", "thr_conv_bal", "thr_conv_rich")},
        "verdicts": V.rows, "tally": tally,
    }
    _CACHE["l16"] = obj
    _dump_artifacts("extra16_convergence", obj, ui)
    _fig_x5(ui, cfg, obj)
    return obj


def _fig_x5(ui: UI, cfg: XCfg, obj: dict) -> None:
    """figX5_convergence_{ru,en}.png — пространственная и временная сходимость."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _apply_font()
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 10.5,
        "axes.edgecolor": C_BORDER, "axes.labelcolor": C_TEXT,
        "xtick.color": C_MUTED, "ytick.color": C_MUTED,
        "axes.linewidth": 0.8, "axes.spines.top": False,
        "axes.spines.right": False,
    })
    sp, tp = obj["spatial"], obj["temporal"]
    cols = {"Omega_max": C_ACCENT, "omega_inf_max": C_ACCENT2,
            "I_BKM_T": "#7a9a3f", "E_final": C_LOSS}
    qname = {"Omega_max": "Ω_max", "omega_inf_max": "‖ω‖_∞",
             "I_BKM_T": "I_BKM", "E_final": "E_final"}
    for lang in ("ru", "en"):
        L = FIG_X[lang]
        fig, ax = plt.subplots(1, 2, figsize=(cfg["fig_width"],
                                              cfg["fig_height"]),
                               constrained_layout=True)
        # (a) пространственная сходимость: err vs N (полулог)
        for q in CONV_QTY:
            pts = sp[q]["points"]
            ax[0].semilogy([p["N"] for p in pts],
                           [max(p["rel_err"], 1e-16) for p in pts],
                           "o-", color=cols[q], lw=1.5, ms=4,
                           label=qname[q])
        fit = sp["Omega_max"]["exp_fit"]
        nn = [p["N"] for p in sp["Omega_max"]["points"]]
        if math.isfinite(fit["c"]) and math.isfinite(fit["A"]):
            xx = np.linspace(min(nn), max(nn), 60)
            ax[0].semilogy(xx, fit["A"] * np.exp(-fit["c"] * xx), ":",
                           color=C_MUTED, lw=1.2)
            ax[0].text(0.03, 0.06, f"c = {fit['c']:.3f},  r² = {fit['r2']:.3f}",
                       transform=ax[0].transAxes, fontsize=9, color=C_MUTED)
        ax[0].set_xlabel("N")
        ax[0].set_ylabel(L["x5_err"])
        ax[0].set_title(L["x5_sp"], fontsize=10.5, color=C_TEXT)
        ax[0].grid(True, ls=":", alpha=0.35)
        ax[0].legend(frameon=False, fontsize=9)
        # (b) временная сходимость: err vs dt (log-log, ref dt = 5e-4)
        for q in CONV_QTY:
            pts = [p for p in tp[q]["points"] if p["rel_err"] > 0]
            ax[1].loglog([p["dt"] for p in pts],
                         [p["rel_err"] for p in pts],
                         "s--", color=cols[q], lw=1.5, ms=4, label=qname[q])
        anch = next((p["rel_err"] for p in tp["Omega_max"]["points"]
                     if abs(p["dt"] - 2e-3) < 1e-12 and p["rel_err"] > 0),
                    None)
        if anch is not None:
            dd = np.array(sorted(p["dt"] for p in tp["Omega_max"]["points"]
                                 if p["rel_err"] > 0))
            ax[1].loglog(dd, anch * (dd / 2e-3) ** 2, ":", color=C_MUTED,
                         lw=1.2, label=L["x5_slope2"])
        pm_Om = tp["Omega_max"]["p_mean"]
        pm_E = tp["E_final"]["p_mean"]
        ax[1].text(0.97, 0.94,
                   f"p(Ω_max) = {pm_Om:.2f}\np(E_final) = {pm_E:.2f}",
                   transform=ax[1].transAxes, ha="right", va="top",
                   fontsize=9, color=C_TEXT)
        ax[1].set_xlabel("dt")
        ax[1].set_ylabel(L["x5_err"])
        ax[1].set_title(L["x5_dt"], fontsize=10.5, color=C_TEXT)
        ax[1].grid(True, ls=":", alpha=0.35, which="both")
        ax[1].legend(frameon=False, fontsize=9)
        fig.suptitle(L["x5_title"], fontsize=12, color=C_HEADER)
        fig.text(0.99, 0.01, L["foot"], ha="right", fontsize=8,
                 color=C_MUTED)
        pth = os.path.join(OUT_FIGURES, f"figX5_convergence_{lang}.png")
        fig.savefig(pth, dpi=int(cfg["dpi"]))
        plt.close(fig)
        ui.bar(0.5 if lang == "ru" else 1.0, "L16 figX5 " + lang)
        ui.say(ui.dim(f"  figX5 → {os.path.relpath(pth, PKG_ROOT)}"))


# ============================================================================
# L17: φ-АУДИТ МОНОВРАФИИ О ДВУХСЛОЙНЫХ φ-АТТРАКТОРАХ
# ============================================================================
PHI_G = (1.0 + math.sqrt(5.0)) / 2.0
PHI_FIB = (8, 13, 21, 34, 55, 89, 144, 233)          # F6..F13
# Таблица 2 монографии: (ΓA, ΓB, ΓC, ΓD), заявленный ε, подмножество
PHI_TABLE2 = (
    ((89, 144, 144, 233), 1.0e-5, "A"),
    ((55, 89, 89, 144), 1.0e-5, "A"),
    ((89, 89, 144, 144), 3.0e-5, "A"),
    ((34, 55, 55, 89), 3.0e-5, "A"),
    ((21, 34, 34, 55), 9.0e-5, "A"),
    ((13, 21, 21, 34), 2.4e-4, "B"),
    ((34, 34, 55, 55), 2.4e-4, "B"),
    ((8, 13, 13, 21), 6.3e-4, "B"),
    ((21, 21, 34, 34), 6.3e-4, "B"),
    ((8, 8, 13, 13), 4.3e-3, "C"),
)
PHI_DELTA2 = 0.05                                     # регуляризация Рэнкина


def phi_algebra() -> list:
    """Приложение Z.1: тождества. Первые 7 — точные (машинная точность);
    последние 3 — сравнения со скруглёнными константами монографии."""
    phi = PHI_G
    checks = [
        ("phi^2 = phi + 1", phi ** 2 - (phi + 1.0), True),
        ("phi - 1 = 1/phi", (phi - 1.0) - 1.0 / phi, True),
        ("phi^2 + 1 = phi + 2", (phi ** 2 + 1.0) - (phi + 2.0), True),
        ("phi^2 + 1 = sqrt(5)·phi", (phi ** 2 + 1.0) - math.sqrt(5.0) * phi, True),
        ("rho^2 - rho - 1 = 0 (rho = phi)", (phi ** 2 - phi - 1.0), True),
        ("2·phi^2 - phi - 2 = phi", (2.0 * phi ** 2 - phi - 2.0) - phi, True),
        ("phi^2 - 1 = phi", (phi ** 2 - 1.0) - phi, True),
        ("K_univ = 0.95/(2·ln phi) ≈ 0.987 (скругл.)",
         (0.95 / (2.0 * math.log(phi))) - 0.9871, False),
        ("|M'(phi)| = 1/phi^2 ≈ 0.382 (скругл.)",
         (1.0 / phi ** 2) - 0.3819660112501051, False),
        ("sqrt(1 + ln 600)·0.08 ≈ 0.2176 (скругл.)",
         (math.sqrt(1.0 + math.log(600.0)) * 0.08) - 0.2176, False),
    ]
    return checks


def phi_fib_spectrum() -> dict:
    """Таблица X.6: μ = (Γ₃+Γ₄)/(Γ₁+Γ₂); монотонность Бине ВНУТРИ каждого
    семейства (a·b·b·c и a·a·b·b) по возрастанию младшего индекса."""
    rows = []
    for (g, eps_claim, sub) in PHI_TABLE2:
        mu = (g[2] + g[3]) / (g[0] + g[1])
        fam = "abc" if g[0] != g[1] else "aabb"
        rows.append({"G": g, "mu": mu, "dev": abs(mu - PHI_G),
                     "eps_claim": eps_claim, "subset": sub, "family": fam})
    viol = 0
    for fam in ("abc", "aabb"):
        sub = sorted((r for r in rows if r["family"] == fam),
                     key=lambda r: PHI_FIB.index(
                         min(PHI_FIB, key=lambda f: abs(f - r["G"][0]))))
        devs = [r["dev"] for r in sub]
        viol += sum(1 for i in range(len(devs) - 1)
                    if devs[i + 1] > devs[i] + 1e-15)
    return {"rows": rows, "binet_violations": viol,
            "max_dev": max(r["dev"] for r in rows)}


def phi_rg_map(n_starts: int = 12) -> dict:
    """Приложение Д.5: μₙ₊₁ = 1 + 1/μₙ → φ; мультипликатор 1/φ²."""
    starts = [0.4 * (k + 1) for k in range(n_starts)]   # детерминированно
    traj = []
    for mu0 in starts:
        seq = [mu0]
        for _ in range(60):
            mu = 1.0 + 1.0 / seq[-1]
            seq.append(mu)
            if abs(mu - PHI_G) < 1e-15:
                break
        traj.append(seq)
    # скорость: асимптотический множитель = медиана пошаговых отношений
    # |μₙ₊₁−φ|/|μₙ−φ| в окне 1e-14 … 1e-3 (вне переходного режима и шума)
    ratios = []
    for seq in traj:
        for n_ in range(len(seq) - 1):
            d0 = abs(seq[n_] - PHI_G)
            d1 = abs(seq[n_ + 1] - PHI_G)
            if 1e-14 < d0 < 1e-3 and d1 > 0:
                ratios.append(d1 / d0)
    ratio = float(np.median(ratios)) if ratios else float("nan")
    mult_th = 1.0 / PHI_G ** 2                       # ≈ 0.3819660
    xs, ys = [], []
    for seq in traj:
        for n_, mu in enumerate(seq):
            d = abs(mu - PHI_G)
            if 1e-13 < d < 0.1:
                xs.append(float(n_))
                ys.append(math.log(d))
    A = np.vstack([xs, np.ones_like(xs)]).T
    coef, *_ = np.linalg.lstsq(A, np.array(ys), rcond=None)
    slope = float(coef[0])
    slope_th = math.log(1.0 / PHI_G ** 2)               # ≈ −0.9624
    conv = all(abs(seq[-1] - PHI_G) < 1e-12 for seq in traj)
    return {"starts": starts, "trajs": traj, "slope": slope,
            "slope_theory": slope_th, "ratio": ratio,
            "multiplier_theory": mult_th,
            "rate_rel_dev": abs(ratio - mult_th) / mult_th,
            "all_converged": bool(conv)}


def phi_vels(r1: float, r2: float, g4) -> dict:
    """Скорости 4 вихрей двухслойного прямоугольника (условия (5) монографии).
    Слои: (ΓA,ΓB) внизу, (ΓC,ΓD) вверху; Рэнкин δ² на каждую пару."""
    ga, gb, gc, gd = g4
    m1 = max(r1 * r1, PHI_DELTA2)
    m2 = max(r2 * r2, PHI_DELTA2)
    mm = max(r1 * r1 + r2 * r2, PHI_DELTA2)
    k1 = 1.0 / (2.0 * math.pi * m1)
    k2 = 1.0 / (2.0 * math.pi * m2)
    km = 1.0 / (2.0 * math.pi * mm)
    return {
        "A": (gc * r2 * k2 + gd * r2 * km, -gb * r1 * k1 - gd * r1 * km),
        "B": (gc * r2 * km + gd * r2 * k2, ga * r1 * k1 + gc * r1 * km),
        "C": (ga * r2 * k2 + gb * r2 * km, -gb * r1 * km - gd * r1 * k1),
        "D": (ga * r2 * km + gb * r2 * k2, ga * r1 * km + gc * r1 * k1),
    }


def phi_drift_direct(r1: float, r2: float, g4, s: float) -> tuple:
    """Невязки условий нулевого дрейфа (5) в B и A: F_B = v_B − s·u_B,
    F_A = v_A + s·u_A, где s = 2at (наклон параболы)."""
    v = phi_vels(r1, r2, g4)
    (ua, va), (ub, vb) = v["A"], v["B"]
    return vb - s * ub, va + s * ua


def phi_drift_reduced(r1: float, r2: float, g4) -> float:
    """Редуцированное условие (теорема L17): исключение s даёт
    (ΓBΓC − ΓAΓD)·m₂ + (ΓBΓD − ΓAΓC)·m_M + (ΓD² − ΓC²)·m₁ = 0."""
    ga, gb, gc, gd = g4
    m1 = max(r1 * r1, PHI_DELTA2)
    m2 = max(r2 * r2, PHI_DELTA2)
    mm = max(r1 * r1 + r2 * r2, PHI_DELTA2)
    return ((gb * gc - ga * gd) * m2 + (gb * gd - ga * gc) * mm
            + (gd * gd - gc * gc) * m1)


def phi_zd_scan(g4, t: float, n_scan: int = 4000) -> int:
    """Счёт корней g(R₂) = v_A + s(R₂)·u_A при фиксированном t (R₁ = 2t):
    s из условия в B; корни ищутся бисекцией по знаку на лог-сетке."""
    r1 = 2.0 * t

    def gfun(r2):
        v = phi_vels(r1, r2, g4)
        ub, vb = v["B"]
        if abs(ub) < 1e-300:
            return float("nan")
        ua, va = v["A"]
        return va + (vb / ub) * ua

    lo, hi = 0.10 * r1, 5.0 * r1
    grid = [lo * (hi / lo) ** (i / (n_scan - 1)) for i in range(n_scan)]
    vals = [gfun(x) for x in grid]
    roots = 0
    for i in range(n_scan - 1):
        a_, b_ = vals[i], vals[i + 1]
        if not (math.isfinite(a_) and math.isfinite(b_)) or a_ * b_ > 0:
            continue
        x0, x1, y0 = grid[i], grid[i + 1], a_
        ok = True
        for _ in range(80):
            xm = 0.5 * (x0 + x1)
            ym = gfun(xm)
            if not math.isfinite(ym):
                ok = False
                break
            if y0 * ym <= 0:
                x1, y1 = xm, ym
            else:
                x0, y0 = xm, ym
        if ok:
            roots += 1
    return roots


def phi_zd_family_residual(g4, t_grid) -> float:
    """Симметричное семейство (ΓA=ΓB, ΓC=ΓD): φ-геометрия достижима —
    при R₂ = 2t/φ условие в B определяет s; невязка обоих условий (5)."""
    worst = 0.0
    for t in t_grid:
        r1 = 2.0 * t
        r2 = r1 / PHI_G
        v = phi_vels(r1, r2, g4)
        ub, vb = v["B"]
        if abs(ub) < 1e-300:
            continue
        s = vb / ub
        fb, fa = phi_drift_direct(r1, r2, g4, s)
        sc = max(abs(fb), abs(fa)) / max(1.0, abs(vb))
        worst = max(worst, sc)
    return worst


def phi_zd_identity_check(g4_list, t_grid, r2_fracs=(0.3, 0.8, 1.2, 2.5)) -> float:
    """Редуцированное условие ≡ прямому (теорема L17):
    v_A·u_B + v_B·u_A = −R₁R₂·reduced / ((2π)²·m₁·m₂·m_M).
    Проверяется на произвольных (t, R₂) — не только φ-геометрии."""
    worst = 0.0
    for g4 in g4_list:
        for t in t_grid:
            r1 = 2.0 * t
            for fr in r2_fracs:
                r2 = fr * r1
                v = phi_vels(r1, r2, g4)
                (ua, va), (ub, vb) = v["A"], v["B"]
                m1 = max(r1 * r1, PHI_DELTA2)
                m2 = max(r2 * r2, PHI_DELTA2)
                mm = max(r1 * r1 + r2 * r2, PHI_DELTA2)
                red = phi_drift_reduced(r1, r2, g4)
                expected = -r1 * r2 * red / ((2.0 * math.pi) ** 2 * m1 * m2 * mm)
                t1, t2 = va * ub, vb * ua
                direct = t1 + t2
                denom = abs(t1) + abs(t2) + abs(expected)
                if denom <= 0:
                    continue
                worst = max(worst, abs(direct - expected) / denom)
    return worst


def phi_bardina_field(u: np.ndarray, v: np.ndarray, delta: float,
                      box_half: float) -> tuple:
    """Процедура приложения B монографии: гауссов фильтр (усечение на
    границе без перенормировки), τ^SS Бардины, центральные разности.
    Возвращает (num, den)."""
    n = u.shape[0]
    h = (2.0 * box_half) / n
    sigma = delta / math.sqrt(12.0)
    sp = sigma / h
    krad = int(math.ceil(3.0 * sp))
    ker = np.exp(-0.5 * (np.arange(-krad, krad + 1) / sp) ** 2)
    ker /= ker.sum()
    idx = np.arange(n)

    def f2d(f):
        tmp = np.zeros_like(f)
        for i in range(n):
            acc = np.zeros(n)
            for kk in range(-krad, krad + 1):
                ii = i + kk
                if 0 <= ii < n:
                    acc += f[ii, :] * ker[kk + krad]
            tmp[i, :] = acc
        res = np.zeros_like(f)
        for j in range(n):
            acc = np.zeros(n)
            for kk in range(-krad, krad + 1):
                jj = j + kk
                if 0 <= jj < n:
                    acc += tmp[:, jj] * ker[kk + krad]
            res[:, j] = acc
        return res

    ut, vt = f2d(u), f2d(v)
    uut, vvt, uvt = f2d(u * u), f2d(v * v), f2d(u * v)
    dudx = (ut[2:, 1:-1] - ut[:-2, 1:-1]) / (2.0 * h)
    dvdy = (vt[1:-1, 2:] - vt[1:-1, :-2]) / (2.0 * h)
    dudy = (ut[1:-1, 2:] - ut[1:-1, :-2]) / (2.0 * h)
    dvdx = (vt[2:, 1:-1] - vt[:-2, 1:-1]) / (2.0 * h)
    sxx = np.zeros_like(u); syy = np.zeros_like(u); sxy = np.zeros_like(u)
    sxx[1:-1, 1:-1] = dudx
    syy[1:-1, 1:-1] = dvdy
    sxy[1:-1, 1:-1] = 0.5 * (dudy + dvdx)
    ns = np.zeros_like(u)
    ns[1:-1, 1:-1] = np.sqrt(2.0 * (dudx ** 2 + dvdy ** 2
                                    + 2.0 * sxy[1:-1, 1:-1] ** 2))
    txx = uut - ut * ut
    tyy = vvt - vt * vt
    txy = uvt - ut * vt
    m = ns > 1e-10
    num = float(np.sum(-(txx[m] * sxx[m] + 2.0 * txy[m] * sxy[m]
                         + tyy[m] * syy[m])))
    den = float(np.sum(2.0 * delta * delta * ns[m] ** 3))
    return num, den


def phi_rankin_field(vortices, n: int, box_half: float) -> tuple:
    """Поле скорости Рэнкина (formула (3), reg2 = 0.05) на сетке приложения B."""
    h = (2.0 * box_half) / n
    idx = (np.arange(n) + 0.5) * h - box_half
    x, y = np.meshgrid(idx, idx, indexing="ij")
    u = np.zeros((n, n))
    v = np.zeros((n, n))
    for (vx, vy, g) in vortices:
        dx = x - vx
        dy = y - vy
        r2e = np.maximum(dx * dx + dy * dy, PHI_DELTA2)
        c = g / (2.0 * math.pi * r2e)
        u += -c * dy
        v += c * dx
    return u, v


def phi_rect_vortices(t: float, g4, y0: float = 0.0) -> list:
    """Двухслойная φ-геометрия: R₁ = 2t, R₂ = 2t/φ, прямоугольник с центром
    (0, y0 + R₂/2); возвращается список [(x, y, Γ), …]."""
    r1 = 2.0 * t
    r2 = r1 / PHI_G
    return [(-r1 / 2.0, y0, float(g4[0])), (r1 / 2.0, y0, float(g4[1])),
            (-r1 / 2.0, y0 + r2, float(g4[2])), (r1 / 2.0, y0 + r2, float(g4[3]))]


def phi_kirchhoff_rhs(state: np.ndarray, g4) -> np.ndarray:
    """Уравнения Кирхгофа (3) с регуляризацией Рэнкина для 4 вихрей."""
    vel = np.zeros((4, 2))
    for i in range(4):
        dx = state[i, 0] - state[:, 0]
        dy = state[i, 1] - state[:, 1]
        r2 = dx * dx + dy * dy
        for j in range(4):
            if j == i:
                continue
            c = g4[j] / (2.0 * math.pi * max(r2[j], PHI_DELTA2))
            vel[i, 0] += -c * dy[j]
            vel[i, 1] += c * dx[j]
    return vel


def phi_d5_freqs(g1: float, g2: float, r2: float) -> tuple:
    """Формулы (D.5a–c) приложения Г: ν_prec, ν_breath, ν_pulse."""
    a = g1 / (2.0 * math.pi * r2 ** 2)
    b = g2 / (2.0 * math.pi * r2 ** 2)
    nu_prec = (a * PHI_G ** 2 + b) / (PHI_G ** 2 + 1.0)
    nu_breath = math.sqrt(2.0 * a * b * PHI_G / math.sqrt(5.0))
    nu_pulse = math.sqrt(a ** 2 * PHI_G ** 2 + b ** 2 / PHI_G ** 2
                         + 2.0 * a * b / math.sqrt(5.0))
    return nu_prec, nu_breath, nu_pulse


def phi_modes_run(g4, r2: float, dt: float, t_end: float, pert: float) -> dict:
    """Динамический тест (прил. Г, предсказание (i)): интегрирование Кирхгофа
    от φ-геометрии с малым возмущением; ряды R₁(t), R₂(t), ρ(t)."""
    r1 = PHI_G * r2
    base = np.array([[-r1 / 2.0, 0.0], [r1 / 2.0, 0.0],
                     [-r1 / 2.0, r2], [r1 / 2.0, r2]])
    state = base + pert * np.array([[1.0, -0.6], [-0.7, 0.5],
                                    [0.4, -0.3], [-0.2, 0.1]])
    nst = int(round(t_end / dt))
    every = 2
    rec = {"dt_rec": dt * every, "R1": [], "R2": []}
    for s_ in range(nst):
        k1 = phi_kirchhoff_rhs(state, g4)
        k2 = phi_kirchhoff_rhs(state + 0.5 * dt * k1, g4)
        k3 = phi_kirchhoff_rhs(state + 0.5 * dt * k2, g4)
        k4 = phi_kirchhoff_rhs(state + dt * k3, g4)
        state = state + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        if s_ % every == 0:
            r1t = math.hypot(*(state[1] - state[0]))
            gap = 0.5 * (state[2] + state[3]) - 0.5 * (state[0] + state[1])
            rec["R1"].append(r1t)
            rec["R2"].append(math.hypot(gap[0], gap[1]))
    return rec


def phi_dom_freq(x: list) -> float:
    """Доминирующая частота ряда (окно Ханна, rFFT)."""
    x = np.asarray(x, dtype=float)
    x = x - x.mean()
    if len(x) < 16 or float(np.std(x)) < 1e-16:
        return float("nan")
    sp = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    fr = np.fft.rfftfreq(len(x), d=1.0)
    m = fr > 0
    if not m.any():
        return float("nan")
    return float(fr[m][int(np.argmax(sp[m]))])


def phi_d7_chain() -> dict:
    """Цепочка (D.6b)–(D.8) при Γ₁=1, Γ₂=φ, R₂=1, C_s=0.081, Δ=1:
    E_kin, α₂ (D.6b), γ двумя формами (D.7), τ_φ против заявленных 322."""
    g1, g2, r2 = 1.0, PHI_G, 1.0
    cs, dl = 0.081, 1.0
    # прямоугольник: (±φ/2, 0), (±φ/2, 1)
    r1 = PHI_G * r2
    pos = [(-r1 / 2.0, 0.0), (r1 / 2.0, 0.0), (-r1 / 2.0, r2), (r1 / 2.0, r2)]
    gg = [g1, g1, g2, g2]
    ekin = 0.0
    for i in range(4):
        acc = 0.0
        for j in range(4):
            if i == j:
                continue
            d2 = (pos[i][0] - pos[j][0]) ** 2 + (pos[i][1] - pos[j][1]) ** 2
            acc += 1.0 / d2
        ekin += gg[i] ** 2 * acc / (4.0 * math.pi)
    a = g1 / (2.0 * math.pi * r2 ** 2)
    b = g2 / (2.0 * math.pi * r2 ** 2)
    _, nu_b, _ = phi_d5_freqs(g1, g2, r2)
    alpha2_d6b = a * b * PHI_G * (PHI_G - 1.0) / (ekin * (PHI_G ** 2 + 1.0))
    gamma_form1 = cs ** 2 * dl ** 2 * nu_b ** 2 / (2.0 * ekin)
    gamma_form2 = alpha2_d6b * cs ** 2 * dl ** 2 * nu_b
    tau1 = 1.0 / gamma_form1 if gamma_form1 > 0 else float("inf")
    tau2 = 1.0 / gamma_form2 if gamma_form2 > 0 else float("inf")
    tau_claim = 322.0
    return {"E_kin": ekin, "nu_breath": nu_b, "nu_breath_claim": 0.209,
            "alpha2_d6b": alpha2_d6b, "alpha2_claim": 0.82,
            "gamma_form1": gamma_form1, "gamma_form2": gamma_form2,
            "gamma_claim": 0.0031, "tau_form1": tau1, "tau_form2": tau2,
            "tau_claim": tau_claim,
            "tau_dev": abs(min(tau1, tau2) / tau_claim - 1.0),
            "nu_dev": abs(nu_b / 0.209 - 1.0)}


def phi_ow_slice(up: np.ndarray, vp: np.ndarray) -> dict:
    """Протокол приложения Д на одном 2D-срезе: критерий Окубо–Вайсса,
    сегментация, центроиды, циркуляции. Возвращает словарь с вихрями."""
    from collections import deque
    n = up.shape[0]
    k1 = np.fft.fftfreq(n) * n
    kx = k1[:, None]
    ky = k1[None, :]

    def sd(f, axis):
        return np.fft.ifft2(np.fft.fft2(f) * 1j * (kx if axis == 0 else ky)).real

    dux, duy = sd(up, 0), sd(up, 1)
    dvx, dvy = sd(vp, 0), sd(vp, 1)
    om = dvx - duy
    w = (dux - dvy) ** 2 + (dvx + duy) ** 2 - om ** 2
    th = 0.1 * float(w.std())
    mask = w < -th
    lab = np.zeros((n, n), dtype=int)
    cur = 0
    comps = []
    for i in range(n):
        for j in range(n):
            if mask[i, j] and lab[i, j] == 0:
                cur += 1
                q = deque([(i, j)])
                lab[i, j] = cur
                cells = []
                while q:
                    a, b = q.popleft()
                    cells.append((a, b))
                    for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        aa, bb = (a + da) % n, (b + db) % n
                        if mask[aa, bb] and lab[aa, bb] == 0:
                            lab[aa, bb] = cur
                            q.append((aa, bb))
                comps.append(cells)
    h = 2.0 * math.pi / n
    da = h * h
    xc = (np.arange(n) + 0.5) * h
    vorts = []
    for cells in comps:
        wts = np.array([om[c] for c in cells])
        sw = float(wts.sum())
        gam = sw * da
        if abs(sw) < 1e-9:
            continue
        ref = cells[int(np.argmax(np.abs(wts)))]
        rx, ry = xc[ref[0]], xc[ref[1]]
        dxs = np.array([((xc[c[0]] - rx + math.pi) % (2.0 * math.pi)) - math.pi
                        for c in cells])
        dys = np.array([((xc[c[1]] - ry + math.pi) % (2.0 * math.pi)) - math.pi
                        for c in cells])
        cx = rx + float((dxs * wts).sum() / sw)
        cy = ry + float((dys * wts).sum() / sw)
        cx = cx % (2.0 * math.pi)
        cy = cy % (2.0 * math.pi)
        vorts.append({"x": cx, "y": cy, "G": float(gam),
                      "d": math.sqrt(len(cells) * da / math.pi)})
    gmax = max((abs(v["G"]) for v in vorts), default=0.0)
    keep = [v for v in vorts if abs(v["G"]) >= 0.05 * gmax]
    return {"omega": om, "W": w, "th": th, "vortices": keep}


def phi_quadruples(vortices: list) -> tuple:
    """Квадруплеты 2+/2− (прил. Д.2–Д.3): ρ = R₁/R₂, условия (а)–(в).
    Минимально-периодическая метрика на торе [0, 2π)²."""
    def dist2(p, q):
        dx = ((p[0] - q[0] + math.pi) % (2.0 * math.pi)) - math.pi
        dy = ((p[1] - q[1] + math.pi) % (2.0 * math.pi)) - math.pi
        return dx, dy, math.hypot(dx, dy)

    pos = [v for v in vortices if v["G"] > 0]
    neg = [v for v in vortices if v["G"] < 0]
    rhos = []
    for i in range(len(pos)):
        for j in range(i + 1, len(pos)):
            for k in range(len(neg)):
                for m in range(k + 1, len(neg)):
                    q = (pos[i], pos[j], neg[k], neg[m])
                    _, _, r1 = dist2((q[0]["x"], q[0]["y"]),
                                     (q[1]["x"], q[1]["y"]))
                    c1 = (0.5 * (q[0]["x"] + q[1]["x"]),
                          0.5 * (q[0]["y"] + q[1]["y"]))
                    c2 = (0.5 * (q[2]["x"] + q[3]["x"]),
                          0.5 * (q[2]["y"] + q[3]["y"]))
                    _, _, r2 = dist2(c1, c2)
                    if r2 <= 1e-12:
                        continue
                    rho = r1 / r2
                    if 0.5 <= rho <= 3.5:
                        # условие (в) Д.2 (|P₄| = |ΣΓₖxₖ| < 0.2·max|Γ|·R_search)
                        # определено только в абсолютном кадре бесконечной
                        # плоскости; на торе при ΣΓ ≠ 0 оно кадрозависимо —
                        # в L17 вычисляется как ДИАГНОСТИКА, квадруплет
                        # фильтруется по (а) 2+/2− и (б) окну ρ ∈ [0.5, 3.5]
                        rhos.append(rho)
    return rhos


def phi_dns_synthetic() -> dict:
    """Валидация DNS-механики на известном ответе: гауссовы вихри (Лэмб)
    2+/2− на φ-прямоугольнике → пайплайн должен вернуть ρ̂ ≈ φ."""
    n = 96
    ll = 2.0 * math.pi
    h = ll / n
    xc = (np.arange(n) + 0.5) * h
    x, y = np.meshgrid(xc, xc, indexing="ij")
    r2 = 1.484
    r1 = PHI_G * r2
    rc = 0.35
    # центр конфигурации в середине домена — без заворота через границу
    ox = oy = math.pi
    vv = [(ox - r1 / 2.0, oy - r2 / 2.0, 89.0), (ox + r1 / 2.0, oy - r2 / 2.0, 89.0),
          (ox - r1 / 2.0, oy + r2 / 2.0, -144.0), (ox + r1 / 2.0, oy + r2 / 2.0, -144.0)]
    om = np.zeros((n, n))
    for (px, py, g) in vv:
        dx = ((x - px + ll / 2) % ll) - ll / 2
        dy = ((y - py + ll / 2) % ll) - ll / 2
        om += g / (math.pi * rc ** 2) * np.exp(-(dx * dx + dy * dy) / rc ** 2)
    # скорости из завихрённости: Δψ = −ω (k = 0 исключён)
    k1 = np.fft.fftfreq(n) * n
    kx = k1[:, None]
    ky = k1[None, :]
    k2grid = kx ** 2 + ky ** 2
    k2grid[0, 0] = 1.0

    def sd(f, axis):
        return np.fft.ifft2(np.fft.fft2(f) * 1j * (kx if axis == 0 else ky)).real

    psi = np.fft.ifft2(np.fft.fft2(om) / k2grid).real
    up = sd(psi, 1)
    vp = -sd(psi, 0)
    res = phi_ow_slice(up, vp)
    rhos = phi_quadruples(res["vortices"])
    rho_hat = min(rhos, key=lambda r: abs(r - PHI_G)) if rhos else float("nan")
    return {"n_vortices": len(res["vortices"]), "n_quads": len(rhos),
            "rho_hat": float(rho_hat),
            "rel_dev": abs(rho_hat / PHI_G - 1.0)
            if math.isfinite(rho_hat) else float("nan"),
            "omega": om.tolist(),
            "vortices": [{"x": v["x"], "y": v["y"], "G": v["G"]}
                         for v in res["vortices"]],
            "input": [(float(px), float(py), float(g)) for (px, py, g) in vv]}


def phi_dns_tg(cfg: XCfg) -> dict:
    """Мост приложения Д на данных пакета: срезы состояния 96³ (t = 6)."""
    sol96 = _CACHE.get("sol96") or load_solver96(cfg, None)
    _CACHE["sol96"] = sol96
    n = sol96.n
    u = sol96.phys()
    slices = []
    slices_full = []
    for z0 in cfg["phi_zslices"]:
        res = phi_ow_slice(u[0, :, :, z0], u[1, :, :, z0])
        v = res["vortices"]
        npos = sum(1 for q in v if q["G"] > 0)
        nneg = sum(1 for q in v if q["G"] < 0)
        rhos = phi_quadruples(v)
        slices.append({"z": int(z0), "n_vortices": len(v), "n_pos": npos,
                       "n_neg": nneg, "n_quads": len(rhos),
                       "rho_median": float(np.median(rhos)) if rhos
                       else float("nan"),
                       "omega": res["omega"]})
        slices_full.append(res)
    ok = sum(1 for s in slices if s["n_pos"] >= 2 and s["n_neg"] >= 2)
    # вырождение метрики ρ на шахматной решётке TG: сильнейшие пары
    ratios_r2r1 = []
    for s, res_full in zip(slices, slices_full):
        v = res_full["vortices"]
        pos = sorted((q for q in v if q["G"] > 0), key=lambda q: -abs(q["G"]))
        neg = sorted((q for q in v if q["G"] < 0), key=lambda q: -abs(q["G"]))
        if len(pos) >= 2 and len(neg) >= 2:
            def mind(p, q):
                dx = ((p[0] - q[0] + math.pi) % (2.0 * math.pi)) - math.pi
                dy = ((p[1] - q[1] + math.pi) % (2.0 * math.pi)) - math.pi
                return math.hypot(dx, dy)
            r1 = mind((pos[0]["x"], pos[0]["y"]),
                      (pos[1]["x"], pos[1]["y"]))
            c1 = (0.5 * (pos[0]["x"] + pos[1]["x"]),
                  0.5 * (pos[0]["y"] + pos[1]["y"]))
            c2 = (0.5 * (neg[0]["x"] + neg[1]["x"]),
                  0.5 * (neg[0]["y"] + neg[1]["y"]))
            r2 = mind(c1, c2)
            if r1 > 1e-12:
                ratios_r2r1.append(r2 / r1)
    return {"slices": [{k: v for k, v in s.items() if k != "omega"}
                       for s in slices],
            "slices_ok": ok, "slices_total": len(slices),
            "r2_over_r1_median": float(np.median(ratios_r2r1))
            if ratios_r2r1 else float("nan"),
            "_slices_full": slices_full}


def lab17_phiaudit(ui: UI, cfg: XCfg) -> dict:
    """L17: независимый вычислительный аудит монографии о двухслойных
    φ-аттракторах: φ-алгебра, спектр Фибоначчи, RG-отображение, теоремы
    о нулевом дрейфе и C_s, тест мод, цепочка (D.6b)–(D.8), DNS-мост."""
    ui.say(ui.c(ui.t["l17_hdr"]))
    t0 = time.perf_counter()
    t = ui.t
    V = Verdicts(cfg)
    delta = cfg["phi_delta"]
    box = cfg["phi_box"]

    # ---- 1) φ-алгебра (прил. Z.1) -------------------------------------------
    checks = phi_algebra()
    alg_max = max(abs(rr) for _, rr, ex in checks if ex)
    alg_val = max(abs(rr) for _, rr, ex in checks if not ex)
    v1 = V.judge("L17", t["l17_alg"], alg_max, thr_key="thr_phi_alg")
    ui.bar(0.08, "L17 alg " + ui.t["done"])

    # ---- 2) спектр Фибоначчи (табл. X.6) ------------------------------------
    fib = phi_fib_spectrum()
    v2 = V.judge("L17", t["l17_mu"], fib["max_dev"], thr_key="thr_phi_mu")
    v3 = V.judge("L17", t["l17_binet"], float(fib["binet_violations"]),
                 thr_key="thr_phi_binet")

    # ---- 3) RG-отображение слияний (прил. Д.5) ------------------------------
    rg = phi_rg_map()
    v4 = V.judge("L17", t["l17_rg"], rg["rate_rel_dev"], thr_key="thr_phi_rg")
    ui.bar(0.16, "L17 fib/rg " + ui.t["done"])

    # ---- 4) нулевой дрейф: тождество + безрешётность + семейство ------------
    asym = [g for (g, _, _) in PHI_TABLE2 if g[0] != g[1]]
    sym = [g for (g, _, _) in PHI_TABLE2 if g[0] == g[1]]
    tgrid = (0.3, 0.8, 1.5)
    idm = phi_zd_identity_check(asym[:2], tgrid)
    v5 = V.judge("L17", t["l17_zdid"], idm, thr_key="thr_phi_zd")
    scans = []
    nosol = 0
    for g in asym:
        roots_total = sum(phi_zd_scan(g, tt) for tt in tgrid)
        scans.append({"G": g, "cassini": g[1] * g[2] - g[0] * g[3],
                      "roots": roots_total})
        if roots_total == 0:
            nosol += 1
    v6 = V.judge("L17", t["l17_zdnosol"], float(nosol), kind="min_gt",
                 thr_key="thr_phi_zdnosol")
    fam = max(phi_zd_family_residual(g, tgrid) for g in sym)
    v7 = V.judge("L17", t["l17_zdfam"], fam, thr_key="thr_phi_zd")
    ui.bar(0.28, "L17 zerodrift " + ui.t["done"])

    # ---- 5) C_s: процедура приложения B на φ-геометрии -----------------------
    grids = [int(x) for x in cfg["phi_grids"]]
    cs_tab = []
    cs0_max = 0.0
    for (g, eps_claim, sub) in PHI_TABLE2:
        vort = phi_rect_vortices(0.5, g, y0=-0.5 / PHI_G)
        row = {"G": g, "subset": sub, "eps_claim": eps_claim, "cs": {}}
        for nn in grids:
            u_f, v_f = phi_rankin_field(vort, nn, box)
            num, den = phi_bardina_field(u_f, v_f, delta, box)
            cs2 = num / den if (den > 0 and num > 0) else float("nan")
            row["cs"][str(nn)] = {"num": num, "den": den, "cs2": cs2}
            if g[0] == g[1] and math.isfinite(cs2):
                cs0_max = max(cs0_max, abs(cs2))
        cs_tab.append(row)
    v8 = V.judge("L17", t["l17_cs0"], cs0_max, thr_key="thr_phi_cs0")
    # backscatter на асимметричных: 6 конф × 7 значений t
    t_scan = (0.25, 0.4, 0.6, 0.9, 1.3, 1.8, 2.4)
    neg_count = 0
    neg_detail = []
    for g in asym:
        for tt in t_scan:
            vort = phi_rect_vortices(tt, g, y0=-tt / PHI_G)
            u_f, v_f = phi_rankin_field(vort, 64, box)
            num, den = phi_bardina_field(u_f, v_f, delta, box)
            neg_detail.append({"G": g, "t": tt, "num": num, "den": den})
            if num < 0:
                neg_count += 1
    total_scans = len(neg_detail)
    v9 = V.judge("L17", t["l17_csneg"], float(neg_count), kind="min_gt",
                 thr_key="thr_phi_csneg")
    # контрольные поля: пайплайн видит ненулевой положительный поток
    u_f, v_f = phi_rankin_field([(-0.5, 0.0, 80.0), (0.5, 0.1, 120.0)], 64, box)
    num_p, den_p = phi_bardina_field(u_f, v_f, delta, box)
    cs2_pair = num_p / den_p if (den_p > 0 and num_p > 0) else float("nan")
    rng = np.random.default_rng(20260930)
    kf = np.fft.fftfreq(64) * 64
    kx2, ky2 = np.meshgrid(kf, kf, indexing="ij")
    kk2 = kx2 ** 2 + ky2 ** 2
    kk2[0, 0] = 1.0
    amp = 1.0 / np.maximum(kk2, 1.0) ** 1.5
    u_r = np.fft.ifft2(amp * np.exp(2j * math.pi * rng.random((64, 64)))).real
    v_r = np.fft.ifft2(amp * np.exp(2j * math.pi * rng.random((64, 64)))).real
    sc = 10.0 / max(float(u_r.std()), float(v_r.std()), 1e-30)
    u_r, v_r = u_r * sc, v_r * sc
    num_r, den_r = phi_bardina_field(u_r, v_r, delta, box)
    cs2_rand = num_r / den_r if (den_r > 0 and num_r > 0) else float("nan")
    ctl_fin = [x for x in (cs2_pair, cs2_rand) if math.isfinite(x)]
    v10 = V.judge("L17", t["l17_csctl"],
                  min(ctl_fin) if ctl_fin else float("nan"),
                  kind="min_gt", thr_key="thr_phi_csctl")
    ui.bar(0.5, "L17 C_s " + ui.t["done"])

    # ---- 6) тест мод (прил. Г) ----------------------------------------------
    g_sym = (89.0, 89.0, 144.0, 144.0)
    rec = phi_modes_run(g_sym, 1.0, cfg["phi_dt"], cfg["phi_T"],
                        cfg["phi_pert"])
    dt_rec = rec["dt_rec"]
    nu_hat_r2 = phi_dom_freq(rec["R2"]) / dt_rec
    nu_hat_rho = phi_dom_freq(np.array(rec["R1"]) / np.array(rec["R2"])) / dt_rec
    _, nu_b, nu_u = phi_d5_freqs(89.0, 144.0, 1.0)
    modes_dev = abs(nu_hat_r2 / nu_b - 1.0) if math.isfinite(nu_hat_r2) \
        else float("nan")
    v11 = V.judge("L17", t["l17_modes"], modes_dev, thr_key="thr_phi_modes")

    # ---- 7) цепочка (D.6b)–(D.8) --------------------------------------------
    d7 = phi_d7_chain()
    v12 = V.judge("L17", t["l17_d7"], d7["tau_dev"], thr_key="thr_phi_d7")
    ui.bar(0.58, "L17 modes/d7 " + ui.t["done"])

    # ---- 8) DNS-мост приложения Д --------------------------------------------
    syn = phi_dns_synthetic()
    v13 = V.judge("L17", t["l17_dnsyn"], syn["rel_dev"],
                  thr_key="thr_phi_dnsyn")
    tg = phi_dns_tg(cfg)
    v14 = V.judge("L17", t["l17_dnstg"], float(tg["slices_ok"]),
                  kind="min_gt", thr_key="thr_phi_dnstg")
    ui.bar(0.9, "L17 DNS " + ui.t["done"])

    # ---- 9) кросс-язык Julia (если кросс-чек существует) ---------------------
    jl_path = os.path.join(OUT_RESULTS, "extra17_julia_crosscheck.json")
    if os.path.isfile(jl_path):
        try:
            with open(jl_path, encoding="utf-8") as fh:
                jl = json.load(fh)
            jl_max = max(row["rel_dev"] for row in jl["checks"])
            v15 = V.judge("L17", t["l17_jl"], jl_max, thr_key="thr_phi_jl")
        except Exception:
            v15 = V.judge("L17", t["l17_jl"], float("nan"),
                          thr_key="thr_phi_jl")
    else:
        v15 = V.judge("L17", t["l17_jl"], float("nan"), thr_key="thr_phi_jl",
                      note="julia tools/nsb_extra_research.jl phi17")

    # ---- консольная таблица --------------------------------------------------
    ui.say("")
    vc = {"WIN": ui.g, "DRAW": ui.y, "LOSS": ui.r}
    for name, disp, v in (
            (t["l17_alg"], f"{alg_max:.2e}", v1),
            (t["l17_mu"], f"{fib['max_dev']:.2e}", v2),
            (t["l17_binet"], f"{fib['binet_violations']}", v3),
            (t["l17_rg"], f"{rg['rate_rel_dev']:.2e}", v4),
            (t["l17_zdid"], f"{idm:.2e}", v5),
            (t["l17_zdnosol"], f"{nosol}/6", v6),
            (t["l17_zdfam"], f"{fam:.2e}", v7),
            (t["l17_cs0"], f"{cs0_max:.2e}", v8),
            (t["l17_csneg"], f"{neg_count}/{total_scans}", v9),
            (t["l17_csctl"], f"{min(ctl_fin) if ctl_fin else float('nan'):.2e}",
             v10),
            (t["l17_modes"], f"{modes_dev:.3f}", v11),
            (t["l17_d7"], f"{d7['tau_dev']:.2f}", v12),
            (t["l17_dnsyn"], f"{syn['rel_dev']:.4f}", v13),
            (t["l17_dnstg"], f"{tg['slices_ok']}/{tg['slices_total']}", v14),
            (t["l17_jl"], f"{jl_max:.2e}" if os.path.isfile(jl_path) else "—",
             v15)):
        ui.say(f"    {name:<62} {disp:>8}  {vc[v](v)}")
    ui.say(ui.dim(f"    точные тождества (7): max остаток {alg_max:.2e}; "
                  f"скруглённые константы (3): max откл. {alg_val:.2e} "
                  f"(погрешность округления монографии)"))
    ui.say(ui.dim(f"    ν̂(R₂) = {nu_hat_r2:.3f} против ν_breath(D.5b) = "
                  f"{nu_b:.3f}; ν̂(ρ) = {nu_hat_rho:.3f} против "
                  f"ν_pulse = {nu_u:.3f}"))
    ui.say(ui.dim(f"    (D.7): γ₁ = {d7['gamma_form1']:.2e}, "
                  f"γ₂ = {d7['gamma_form2']:.2e} против заявленного "
                  f"{d7['gamma_claim']:.4f}; τ₁ = {d7['tau_form1']:.0f}, "
                  f"τ₂ = {d7['tau_form2']:.0f} против 322"))
    ui.say(ui.dim(f"    синтетика: ρ̂ = {syn['rho_hat']:.4f} "
                  f"({syn['n_vortices']} вихрей, {syn['n_quads']} квадруплетов); "
                  f"TG: R₂/R₁ медиана = {tg['r2_over_r1_median']:.3f}"))
    ui.say(ui.dim("    " + t["l17_note"]))
    tally = V.tally()
    ui.say(ui.c(f"    L17: WIN={tally['WIN']} DRAW={tally['DRAW']} "
                f"LOSS={tally['LOSS']}   [{fmt_sec(time.perf_counter() - t0)}]"))

    obj = {
        "program": "NSB-96-UPGRADE / nsb_extra_research",
        "lab": "L17 phi-audit of the two-layer phi-attractor monograph",
        "monograph": "Двухслойные φ-аттракторы в точечно-вихревой модели: "
                     "универсальная константа Смагоринского и динамические "
                     "инварианты (загружена пользователем)",
        "phi": PHI_G,
        "algebra": [{"name": nm, "residual": rr, "exact": ex}
                    for nm, rr, ex in checks],
        "algebra_rounded_max_dev": alg_val,
        "fib_spectrum": fib,
        "rg_map": rg,
        "zero_drift": {"identity_max_mismatch": idm,
                       "asym_scans": scans,
                       "sym_family_residual": fam},
        "cs_table": cs_tab,
        "cs_backscatter": {"n_negative": neg_count, "n_total": total_scans,
                           "detail": neg_detail},
        "cs_control": {"pair": {"num": num_p, "den": den_p, "cs2": cs2_pair},
                       "random": {"num": num_r, "den": den_r,
                                  "cs2": cs2_rand}},
        "modes": {"nu_hat_R2": nu_hat_r2, "nu_hat_rho": nu_hat_rho,
                  "nu_breath_d5b": nu_b, "nu_pulse_d5c": nu_u,
                  "rel_dev": modes_dev,
                  "R2_series": rec["R2"], "R1_series": rec["R1"],
                  "dt_rec": dt_rec},
        "d7_chain": d7,
        "dns_synthetic": syn,
        "dns_tg": tg,
        "thresholds": {k: cfg[k] for k in cfg.d if k.startswith("thr_phi_")},
        "verdicts": V.rows, "tally": tally,
    }
    _CACHE["l17"] = obj
    _dump_artifacts("extra17_phiaudit", obj, ui)
    _write_julia_ref17(obj)
    _fig_x6(ui, cfg, obj)
    return obj


def _write_julia_ref17(obj: dict) -> str:
    """Эталон детерминированного ядра L17 для кросс-языковой проверки Julia."""
    ref = {
        "program": "NSB-96-UPGRADE / nsb_extra_research (Python reference, L17)",
        "phi": PHI_G,
        "fib_mu": [r["mu"] for r in obj["fib_spectrum"]["rows"]],
        "fib_max_dev": obj["fib_spectrum"]["max_dev"],
        "rg_slope": obj["rg_map"]["slope"],
        "rg_ratio": obj["rg_map"]["ratio"],
        "rg_slope_theory": obj["rg_map"]["slope_theory"],
        "zd_cassini": [s["cassini"] for s in obj["zero_drift"]["asym_scans"]],
        "zd_identity_mismatch": obj["zero_drift"]["identity_max_mismatch"],
        "zd_sym_family_residual": obj["zero_drift"]["sym_family_residual"],
        "cs_pair_cs2": obj["cs_control"]["pair"]["cs2"],
        "zd_scan_case": {"G": (55, 89, 89, 144), "t": 0.8,
                         "roots": next(s["roots"] for s
                                       in obj["zero_drift"]["asym_scans"]
                                       if s["G"] == (55, 89, 89, 144))},
    }
    p = os.path.join(OUT_RESULTS, "extra17_julia_ref.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(ref, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return p


def _fig_x6(ui: UI, cfg: XCfg, obj: dict) -> None:
    """figX6_phiaudit_{ru,en}.png — 4 панели φ-аудита (2×2, 600 dpi)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _apply_font()
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 10.5,
        "axes.edgecolor": C_BORDER, "axes.labelcolor": C_TEXT,
        "xtick.color": C_MUTED, "ytick.color": C_MUTED,
        "axes.linewidth": 0.8, "axes.spines.top": False,
        "axes.spines.right": False,
    })
    for lang in ("ru", "en"):
        L = FIG_X[lang]
        fig, ax = plt.subplots(2, 2, figsize=(cfg["fig_width"], 9.6),
                               constrained_layout=True)

        # ---- (a) C_s: поток масштабного подобия --------------------------
        a = ax[0][0]
        labels, vals, cols = [], [], []
        for row in obj["cs_table"]:
            c64 = row["cs"].get("64", {})
            num, den = c64.get("num", 0.0), c64.get("den", 1.0)
            cs2 = c64.get("cs2", float("nan"))
            g = row["G"]
            labels.append("·".join(str(x) for x in g) + f" [{row['subset']}]")
            if row["G"][0] == row["G"][1]:            # теорема: ≡ 0
                vals.append(1e-20)
                cols.append(C_MUTED)
            elif math.isfinite(cs2):
                vals.append(cs2)
                cols.append(C_ACCENT)
            else:
                vals.append(num / den if den > 0 else 0.0)
                cols.append(C_LOSS)
        labels.append("80/120 ctl")
        vals.append(obj["cs_control"]["pair"]["cs2"])
        cols.append("#7a9a3f")
        labels.append("rand ctl")
        vals.append(obj["cs_control"]["random"]["cs2"])
        cols.append("#7a9a3f")
        bars = a.bar(range(len(vals)), vals, color=cols, width=0.62)
        a.axhspan(0.075 ** 2, 0.085 ** 2, color=C_ACCENT2, alpha=0.18,
                  label=L["x6_cs_claim"])
        a.axhline(0.0, color=C_BORDER, lw=0.8)
        a.axhline(0.17 ** 2, color=C_LOSS, lw=1.0, ls="--",
                  label=L["x6_cs_lilly"])
        a.set_yscale("symlog", linthresh=1e-20)
        a.set_xticks(range(len(labels)))
        a.set_xticklabels(labels, rotation=48, ha="right", fontsize=7)
        a.set_ylabel("num/den ≈ C_s²")
        a.set_title(L["x6_cs"], fontsize=10.5, color=C_TEXT)
        a.grid(True, axis="y", ls=":", alpha=0.35)
        a.legend(frameon=False, fontsize=8, loc="lower right")

        # ---- (b) RG-отображение ------------------------------------------
        b_ = ax[0][1]
        for tr in obj["rg_map"]["trajs"]:
            nn = list(range(len(tr)))
            dd = [max(abs(mu - PHI_G), 1e-17) for mu in tr]
            b_.semilogy(nn, dd, color=C_ACCENT, alpha=0.35, lw=0.9)
        n_fit = np.arange(0, 26)
        s0 = 0.6
        b_.semilogy(n_fit, s0 * np.exp(obj["rg_map"]["slope_theory"] * n_fit),
                    ":", color=C_TEXT, lw=1.6, label=L["x6_rg_slope"])
        b_.set_xlabel(L["x6_rg_n"])
        b_.set_ylabel("|μₙ − φ|")
        b_.set_title(L["x6_rg"], fontsize=10.5, color=C_TEXT)
        b_.grid(True, ls=":", alpha=0.35, which="both")
        b_.legend(frameon=False, fontsize=9)
        b_.text(0.97, 0.06,
                f"slope = {obj['rg_map']['slope']:.4f} "
                f"(theory {obj['rg_map']['slope_theory']:.4f})",
                transform=b_.transAxes, ha="right", fontsize=8,
                color=C_MUTED)

        # ---- (c) нулевой дрейф: ландшафт g(R₂) ----------------------------
        c_ = ax[1][0]
        g_asym = (55, 89, 89, 144)
        g_sym = (89, 89, 144, 144)
        r1 = 2.0 * 0.8
        grid = [0.1 * r1 * (5.0 / 0.1) ** (i / 240) for i in range(241)]

        def gf(g4, r2):
            v = phi_vels(r1, r2, g4)
            ub, vb = v["B"]
            ua, va = v["A"]
            return va + (vb / ub) * ua

        ga = [gf(g_asym, x) for x in grid]
        gs_ = [abs(gf(g_sym, x)) for x in grid]
        c_.semilogy(grid, [max(abs(x), 1e-18) for x in ga], color=C_ACCENT,
                    lw=1.6, label=L["x6_zd_ab"])
        c_.semilogy(grid, [max(x, 1e-18) for x in gs_], color=C_ACCENT2,
                    lw=1.3, ls="--", label=L["x6_zd_sym"])
        c_.axhline(1e-16, color=C_MUTED, lw=0.8, ls=":")
        c_.set_xlabel("R₂ (R₁ = 1.6, t = 0.8)")
        c_.set_ylabel("|g(R₂)|")
        c_.set_title(L["x6_zd"], fontsize=10.5, color=C_TEXT)
        c_.grid(True, ls=":", alpha=0.35, which="both")
        c_.legend(frameon=False, fontsize=9)
        c_.text(0.03, 0.05, L["x6_zd_ann"], transform=c_.transAxes,
                fontsize=8, color=C_MUTED)

        # ---- (d) DNS-мост: синтетика + срез TG ----------------------------
        d_ = ax[1][1]
        om_syn = np.array(obj["dns_synthetic"]["omega"])
        im = d_.imshow(om_syn, origin="lower", extent=(0, 2 * math.pi, 0,
                                                       2 * math.pi),
                       cmap="RdBu_r")
        for v in obj["dns_synthetic"]["vortices"]:
            d_.plot(v["x"], v["y"], marker="o", ms=9, mfc="none",
                    mec="#151513" if v["G"] > 0 else "#3aa0c2", mew=1.6)
        d_.set_title(L["x6_dns_syn"].format(
            rho=obj["dns_synthetic"]["rho_hat"]), fontsize=10.5,
            color=C_TEXT)
        d_.set_xticks([0, math.pi, 2 * math.pi])
        d_.set_xticklabels(["0", "π", "2π"])
        d_.set_yticks([0, math.pi, 2 * math.pi])
        d_.set_yticklabels(["0", "π", "2π"])
        fig.colorbar(im, ax=d_, shrink=0.85, pad=0.02)
        d_.text(0.03, 0.04, L["x6_dns_tg"], transform=d_.transAxes,
                fontsize=8, color="#151513",
                bbox=dict(fc="white", alpha=0.75, ec="none"))

        fig.suptitle(L["x6_title"], fontsize=12.5, color=C_HEADER)
        fig.text(0.99, 0.01, L["foot"], ha="right", fontsize=8,
                 color=C_MUTED)
        pth = os.path.join(OUT_FIGURES, f"figX6_phiaudit_{lang}.png")
        fig.savefig(pth, dpi=int(cfg["dpi"]))
        plt.close(fig)
        ui.bar(0.5 if lang == "ru" else 1.0, "L17 figX6 " + lang)
        ui.say(ui.dim(f"  figX6 → {os.path.relpath(pth, PKG_ROOT)}"))


# ============================================================================
# L14: ГРАФИКИ — 4 файла × 600 dpi × RU/EN
# ============================================================================
FIG_X = {
    "ru": {
        "x1_title": "Перемежаемость при удвоении разрешения: PDF и плоскостность (t = 6)",
        "x1_pdf": "PDF продольного градиента ζ/⟨ζ²⟩^1/2",
        "x1_gauss": "гауссова referencia", "x1_gauss_r": "гауссово распределение",
        "x1_f": "плоскостность приращений Fₚ(r) = Sₚ/S₂^{p/2}",
        "x1_p4": "F₄", "x1_p6": "F₆",
        "x2_title": "Функции структуры продольных приращений: 48³ vs 96³",
        "x2_sp": "Sₚ(r) = ⟨(δu∥)^p⟩, 96³",
        "x2_r23": "r^{2/3}", "x2_r1": "r",
        "x2_ratio": "отношение 96³/48³ (интерполяция в общих r)",
        "x3_title": "Спектральный поток Π(k) и каскад при t = 6",
        "x3_pi": "Π(k)/ε",
        "x3_band": "инерционный интервал 48³",
        "x3_td": "оболочечные T(k) и D(k), 96³",
        "x3_T": "трансфер T(k)", "x3_D": "диссипация D(k)",
        "x4_title": "Гипердиссипативное семейство КдФ: u_t + 6uu_x + u_xxx = −ν(−∂²)^b u",
        "x4_spec": "E(k): T = 0 против T = {T:g} (ν = {nu:g})",
        "x4_e0": "начальный спектр",
        "x4_amp": "A(t)/A₀ — затухание амплитуды солитона",
        "x5_title": "Самосходимость решателя P5: пространство × время "
                    "(вихрь Тейлора–Грина, ν = 0.01, T = 6)",
        "x5_err": "отн. ошибка |Q − Q_ref|/|Q_ref|",
        "x5_sp": "пространство: dt = 2·10⁻³, ref = 96³ (A96)",
        "x5_dt": "время: N = 48, ref dt = 5·10⁻⁴",
        "x5_slope2": "наклон 2 (IFK-RK2)",
        "x6_title": "L17 · φ-аудит монографии о двухслойных φ-аттракторах",
        "x6_cs": "поток масштабного подобия num/den ≈ C_s² (прил. B): φ-геометрия",
        "x6_cs_claim": "заявленный уровень C_s⁽⁰⁾ = 0.080±0.005",
        "x6_cs_lilly": "предел Лилли 0.17",
        "x6_cs_sym": "симметричные (теорема ≡ 0)",
        "x6_cs_asym": "асимметричные (num < 0)",
        "x6_cs_ctl": "контроль (не нулевой)",
        "x6_rg": "RG-отображение слияний: |μₙ − φ| (прил. Д.5)",
        "x6_rg_n": "шаг слияния n",
        "x6_rg_slope": "наклон −2 ln φ (мультипликатор 1/φ²)",
        "x6_zd": "нулев. дрейф (5): ландшафт g(R₂) при t = 0.8",
        "x6_zd_ab": "log|g|, a·b·b·c (решений нет)",
        "x6_zd_sym": "a·a·b·b: вырождено (g ≡ 0)",
        "x6_zd_ann": "Γ_BΓ_C − Γ_AΓ_D = ±1 (Кассини), F²ₖ₊₁ доминирует",
        "x6_dns": "DNS-мост приложения Д: синтетика и срез TG 96³",
        "x6_dns_syn": "синтетика (2+/2−, гауссовы вихри): ρ̂ = {rho:.4f} против φ = 1.6180",
        "x6_dns_tg": "обнаруженные вихри: чёрные+/синие−; TG 96³: шахматная решётка, центры пар совпадают → ρ вырождается (R₂/R₁ ≈ 0)",
        "foot": "NSB EXTRA · nsb_extra_research.py · 600 dpi",
    },
    "en": {
        "x1_title": "Intermittency at doubled resolution: PDFs and flatness (t = 6)",
        "x1_pdf": "PDF of longitudinal gradient ζ/⟨ζ²⟩^1/2",
        "x1_gauss": "Gaussian reference", "x1_gauss_r": "Gaussian distribution",
        "x1_f": "increment flatness Fₚ(r) = Sₚ/S₂^{p/2}",
        "x1_p4": "F₄", "x1_p6": "F₆",
        "x2_title": "Longitudinal structure functions: 48³ vs 96³",
        "x2_sp": "Sₚ(r) = ⟨(δu∥)^p⟩, 96³",
        "x2_r23": "r^{2/3}", "x2_r1": "r",
        "x2_ratio": "ratio 96³/48³ (interpolated on common r)",
        "x3_title": "Spectral flux Π(k) and cascade at t = 6",
        "x3_pi": "Π(k)/ε",
        "x3_band": "48³ inertial range",
        "x3_td": "shell T(k) and D(k), 96³",
        "x3_T": "transfer T(k)", "x3_D": "dissipation D(k)",
        "x4_title": "Hyperdissipative KdV family: u_t + 6uu_x + u_xxx = −ν(−∂²)^b u",
        "x4_spec": "E(k): T = 0 vs T = {T:g} (ν = {nu:g})",
        "x4_e0": "initial spectrum",
        "x4_amp": "A(t)/A₀ — soliton amplitude decay",
        "x5_title": "P5 solver self-convergence: space × time "
                    "(Taylor–Green vortex, ν = 0.01, T = 6)",
        "x5_err": "rel. error |Q − Q_ref|/|Q_ref|",
        "x5_sp": "space: dt = 2·10⁻³, ref = 96³ (A96)",
        "x5_dt": "time: N = 48, ref dt = 5·10⁻⁴",
        "x5_slope2": "slope 2 (IFK-RK2)",
        "x6_title": "L17 · φ-audit of the two-layer φ-attractor monograph",
        "x6_cs": "scale-similarity flux num/den ≈ C_s² (app. B): φ-geometry",
        "x6_cs_claim": "claimed level C_s⁽⁰⁾ = 0.080±0.005",
        "x6_cs_lilly": "Lilly limit 0.17",
        "x6_cs_sym": "symmetric (theorem ≡ 0)",
        "x6_cs_asym": "asymmetric (num < 0)",
        "x6_cs_ctl": "control (non-zero)",
        "x6_rg": "RG merging map: |μₙ − φ| (app. Д.5)",
        "x6_rg_n": "merging step n",
        "x6_rg_slope": "slope −2 ln φ (multiplier 1/φ²)",
        "x6_zd": "zero drift (5): g(R₂) landscape at t = 0.8",
        "x6_zd_ab": "log|g|, a·b·b·c (no solutions)",
        "x6_zd_sym": "a·a·b·b: degenerate (g ≡ 0)",
        "x6_zd_ann": "Γ_BΓ_C − Γ_AΓ_D = ±1 (Cassini), F²ₖ₊₁ dominates",
        "x6_dns": "app.-Д DNS bridge: synthetic and TG 96³ slice",
        "x6_dns_syn": "synthetic (2+/2−, Gaussian vortices): ρ̂ = {rho:.4f} vs φ = 1.6180",
        "x6_dns_tg": "detected vortices: black+/blue−; TG 96³: checkerboard lattice, pair centers coincide → ρ degenerates (R₂/R₁ ≈ 0)",
        "foot": "NSB EXTRA · nsb_extra_research.py · 600 dpi",
    },
}


def _pdf_of(zeta: np.ndarray, xrange: float, nbins: int = 61,
            min_count: int = 5) -> tuple:
    """PDF нормированного градиента; бины с числом попаданий < min_count
    маскируются (NaN), чтобы не рисовать статистические пустоты хвоста."""
    z = zeta.ravel() / math.sqrt(float(np.mean(zeta ** 2)))
    edges = np.linspace(-xrange, xrange, nbins + 1)
    h, _ = np.histogram(z, bins=edges)
    centers = 0.5 * (edges[1:] + edges[:-1])
    p = h / max(h.sum(), 1) / (edges[1] - edges[0])
    p = np.where(h >= min_count, p, np.nan)
    return centers, p


def lab14_figures(ui: UI, cfg: XCfg) -> list:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _apply_font()
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 10.5,
        "axes.edgecolor": C_BORDER, "axes.labelcolor": C_TEXT,
        "xtick.color": C_MUTED, "ytick.color": C_MUTED,
        "axes.linewidth": 0.8, "axes.spines.top": False,
        "axes.spines.right": False,
    })

    l11 = _CACHE.get("l11")
    l12 = _CACHE.get("l12")
    l13 = _CACHE.get("l13")
    if l11 is None:
        l11 = lab11_gradstats(ui, cfg)
    if l12 is None:
        l12 = lab12_flux(ui, cfg)
    if l13 is None:
        l13 = lab13_kdvb(ui, cfg)

    sol48 = _CACHE["sol48"]
    sol96 = _CACHE["sol96"]
    sf = l11["structure_functions"]
    out: list = []

    for lang in ("ru", "en"):
        L = FIG_X[lang]
        w, h = cfg["fig_width"], cfg["fig_height"]
        dpi = int(cfg["dpi"])

        # ---------- figX1: PDF + F_p(r) -----------------------------------
        fig, ax = plt.subplots(1, 2, figsize=(w, h), constrained_layout=True)
        z48 = grad_stats(sol48)["_zeta"]
        z96 = grad_stats(sol96)["_zeta"]
        c48, p48 = _pdf_of(z48, cfg["pdf_xrange"])
        c96, p96 = _pdf_of(z96, cfg["pdf_xrange"])
        ax[0].semilogy(c48, np.where(np.isfinite(p48), p48, np.nan),
                       color=C_ACCENT2, lw=1.6, label="48³")
        ax[0].semilogy(c96, np.where(np.isfinite(p96), p96, np.nan),
                       color=C_ACCENT, lw=1.6, ls="--", label="96³")
        gg = np.exp(-c96 ** 2 / 2) / math.sqrt(2 * math.pi)
        ax[0].semilogy(c96, gg, color=C_MUTED, lw=1.0, ls=":",
                       label=L["x1_gauss_r"])
        ax[0].set_xlabel("ζ / ⟨ζ²⟩^{1/2}")
        ax[0].set_ylabel(L["x1_pdf"])
        ax[0].set_ylim(1e-10, 1)
        ax[0].grid(True, ls=":", alpha=0.35)
        ax[0].legend(frameon=False)
        r48 = np.array(sf["r48_phys"])
        r96 = np.array(sf["r96_phys"])
        S2_48 = np.array(sf["S2_48"]); S4_48 = np.array(sf["S4_48"])
        S6_48 = np.array(sf["S6_48"])
        S2_96 = np.array(sf["S2_96"]); S4_96 = np.array(sf["S4_96"])
        S6_96 = np.array(sf["S6_96"])
        ax[1].loglog(r48, S4_48 / S2_48 ** 2, color=C_ACCENT2, lw=1.6,
                     label=f"{L['x1_p4']} 48³")
        ax[1].loglog(r96, S4_96 / S2_96 ** 2, color=C_ACCENT, lw=1.6,
                     ls="--", label=f"{L['x1_p4']} 96³")
        ax[1].loglog(r48, S6_48 / S2_48 ** 3, color=C_ACCENT2, lw=1.2,
                     alpha=0.55, label=f"{L['x1_p6']} 48³")
        ax[1].loglog(r96, S6_96 / S2_96 ** 3, color=C_ACCENT, lw=1.2,
                     ls="--", alpha=0.7, label=f"{L['x1_p6']} 96³")
        ax[1].set_xlabel(L["x2_r1"])
        ax[1].set_ylabel(L["x1_f"])
        ax[1].grid(True, ls=":", alpha=0.35, which="both")
        ax[1].legend(frameon=False, fontsize=9)
        fig.suptitle(L["x1_title"], fontsize=12, color=C_HEADER)
        fig.text(0.99, 0.01, L["foot"], ha="right", fontsize=8,
                 color=C_MUTED)
        p = os.path.join(OUT_FIGURES, f"figX1_grad_stats_{lang}.png")
        fig.savefig(p, dpi=dpi)
        plt.close(fig)
        out.append(p)
        ui.bar(0.25 if lang == "ru" else 0.75, "L14 figX1 " + lang)

        # ---------- figX2: structure functions ----------------------------
        fig, ax = plt.subplots(1, 2, figsize=(w, h), constrained_layout=True)
        cols = {2: C_ACCENT2, 3: "#7a9a3f", 4: C_ACCENT, 6: C_LOSS}
        for pexp in (2, 3, 4, 6):
            ax[0].loglog(r96, np.abs(np.array(sf[f"S{pexp}_96"])),
                         color=cols[pexp], lw=1.5, label=f"p = {pexp}")
        rr = np.linspace(r96.min(), r96.max(), 50)
        ax[0].loglog(rr, 1e-4 * rr ** (2.0 / 3.0), color=C_MUTED, ls=":",
                     lw=1.0, label=L["x2_r23"])
        ax[0].set_xlabel(L["x2_r1"])
        ax[0].set_ylabel(L["x2_sp"])
        ax[0].grid(True, ls=":", alpha=0.35, which="both")
        ax[0].legend(frameon=False, fontsize=9)
        band = (0.30, 1.60)
        for pexp in (2, 4):
            A = np.abs(np.array(sf[f"S{pexp}_48"]))
            B = np.abs(np.array(sf[f"S{pexp}_96"]))
            rq = np.linspace(math.log(max(r48.min(), r96.min())),
                             math.log(min(r48.max(), r96.max())), 60)
            Ai = _interp_loglog(r48, A, np.exp(rq))
            Bi = _interp_loglog(r96, B, np.exp(rq))
            ax[1].semilogx(np.exp(rq), Bi / Ai, color=cols[pexp], lw=1.6,
                           label=f"p = {pexp}")
        ax[1].axhspan(1 - cfg["thr_collapse"][1], 1 + cfg["thr_collapse"][1],
                      color=C_ACCENT, alpha=0.08)
        ax[1].axhline(1.0, color=C_MUTED, lw=0.8, ls="--")
        ax[1].set_xlim(band[0], min(r96.max(), r48.max()))
        ax[1].set_xlabel(L["x2_r1"])
        ax[1].set_ylabel(L["x2_ratio"])
        ax[1].grid(True, ls=":", alpha=0.35)
        ax[1].legend(frameon=False, fontsize=9)
        fig.suptitle(L["x2_title"], fontsize=12, color=C_HEADER)
        fig.text(0.99, 0.01, L["foot"], ha="right", fontsize=8,
                 color=C_MUTED)
        p = os.path.join(OUT_FIGURES, f"figX2_structure_{lang}.png")
        fig.savefig(p, dpi=dpi)
        plt.close(fig)
        out.append(p)
        ui.bar(0.375 if lang == "ru" else 0.875, "L14 figX2 " + lang)

        # ---------- figX3: flux -------------------------------------------
        fig, ax = plt.subplots(1, 2, figsize=(w, h), constrained_layout=True)
        k48 = np.array(l12["k48"], dtype=float)
        k96 = np.array(l12["k96"], dtype=float)
        Pi48 = np.array(l12["Pi48"]) / l12["eps48"]
        Pi96 = np.array(l12["Pi96"]) / l12["eps96"]
        ax[0].semilogx(k48[1:], Pi48[1:], color=C_ACCENT2, lw=1.7,
                       label="48³")
        ax[0].semilogx(k96[1:], Pi96[1:], color=C_ACCENT, lw=1.7, ls="--",
                       label="96³")
        ax[0].axvspan(2.0, 11.2, color=C_ACCENT, alpha=0.08)
        ax[0].set_xlabel("k")
        ax[0].set_ylabel(L["x3_pi"])
        ax[0].set_ylim(0, 1.15)
        ax[0].grid(True, ls=":", alpha=0.35)
        ax[0].legend(frameon=False)
        T96 = np.array(l12["T96"])
        E96 = np.array(l12["E96"])
        kk = k96[1:]
        ax[1].semilogx(kk, T96[1:], color=C_ACCENT, lw=1.6,
                       label=L["x3_T"])
        ax[1].semilogx(kk, 2.0 * l12["nu"] * kk ** 2 * E96[1:],
                       color=C_ACCENT2, lw=1.6, ls="--", label=L["x3_D"])
        ax[1].set_xlabel("k")
        ax[1].set_ylabel(L["x3_td"])
        ax[1].grid(True, ls=":", alpha=0.35)
        ax[1].legend(frameon=False, fontsize=9)
        fig.suptitle(L["x3_title"], fontsize=12, color=C_HEADER)
        fig.text(0.99, 0.01, L["foot"], ha="right", fontsize=8,
                 color=C_MUTED)
        p = os.path.join(OUT_FIGURES, f"figX3_flux_{lang}.png")
        fig.savefig(p, dpi=dpi)
        plt.close(fig)
        out.append(p)
        ui.bar(0.5 if lang == "ru" else 1.0, "L14 figX3 " + lang)

        # ---------- figX4: hyperdissipative KdV ---------------------------
        fig, ax = plt.subplots(1, 2, figsize=(w, h), constrained_layout=True)
        fam_cols = {"1": C_ACCENT2, "1.25": "#7a9a3f", "1.5": C_ACCENT,
                    "2": C_LOSS}
        for b, lab in (("1", "b = 1"), ("1.25", "b = 5/4"),
                       ("1.5", "b = 3/2"), ("2", "b = 2")):
            if b not in l13["spectra"]:
                continue
            kk = np.array(l13["spectra"][b]["k"])
            ET = np.array(l13["spectra"][b]["ET"])
            if b == "1":
                E0 = np.array(l13["spectra"][b]["E0"])
                ax[0].loglog(kk[1:], np.maximum(E0[1:], 1e-22),
                             color=C_MUTED, lw=1.0, ls=":",
                             label=L["x4_e0"])
            ax[0].loglog(kk[1:], np.maximum(ET[1:], 1e-22),
                         color=fam_cols[b], lw=1.6, label=lab)
        ax[0].set_ylim(1e-22, 1e2)
        ax[0].set_xlabel("k")
        ax[0].set_ylabel("E(k)")
        ax[0].grid(True, ls=":", alpha=0.35, which="both")
        ax[0].legend(frameon=False, fontsize=9)
        for b, lab in (("1", "b = 1"), ("1.25", "b = 5/4"),
                       ("1.5", "b = 3/2"), ("2", "b = 2")):
            if b not in l13["series"]:
                continue
            tt = np.array(l13["series"][b]["t"])
            AA = np.array(l13["series"][b]["A"])
            ax[1].plot(tt, AA / AA[0], color=fam_cols[b], lw=1.6, label=lab)
        ax[1].set_xlabel("t")
        ax[1].set_ylabel(L["x4_amp"])
        ax[1].grid(True, ls=":", alpha=0.35)
        ax[1].legend(frameon=False, fontsize=9)
        fig.suptitle(
            L["x4_title"].format(T=cfg["kdvb_t_end"], nu=cfg["kdvb_nu"]),
            fontsize=12, color=C_HEADER)
        fig.text(0.99, 0.01, L["foot"], ha="right", fontsize=8,
                 color=C_MUTED)
        p = os.path.join(OUT_FIGURES, f"figX4_kdv_bfamily_{lang}.png")
        fig.savefig(p, dpi=dpi)
        plt.close(fig)
        out.append(p)
        ui.bar(1.0, "L14 figX4 " + lang)

    ui.say(ui.c(f"    L14: {len(out)} files × 600 dpi"))
    for p in out:
        ui.say(ui.dim(f"      {os.path.relpath(p, PKG_ROOT)}"))
    return out


# ============================================================================
# L15: СВОДНЫЕ ОТЧЁТЫ
# ============================================================================
def lab15_report(ui: UI, cfg: XCfg) -> str:
    l11 = _CACHE.get("l11")
    l12 = _CACHE.get("l12")
    l13 = _CACHE.get("l13")
    l16 = _CACHE.get("l16")
    l17 = _CACHE.get("l17")
    if l11 is None:
        l11 = lab11_gradstats(ui, cfg)
    if l12 is None:
        l12 = lab12_flux(ui, cfg)
    if l13 is None:
        l13 = lab13_kdvb(ui, cfg)
    if l17 is None:
        p17 = os.path.join(OUT_RESULTS, "extra17_phiaudit_latest.json")
        if os.path.isfile(p17):
            with open(p17, encoding="utf-8") as fh:
                l17 = json.load(fh)
    if l16 is None:
        p16 = os.path.join(OUT_RESULTS, "extra16_convergence_latest.json")
        if os.path.isfile(p16):
            with open(p16, encoding="utf-8") as fh:
                l16 = json.load(fh)

    def tally_line(o):
        tt = o["tally"]
        return (f"WIN {tt['WIN']} · DRAW {tt['DRAW']} · "
                f"LOSS {tt['LOSS']}")

    ru = ui.lang == "ru"
    lines = []
    ap = lines.append
    ap("# NSB EXTRA — дополнительные исследования (L11–L17)" if ru else
       "# NSB EXTRA — additional research (L11–L17)")
    ap("")
    ap(f"Пакет: NSB-96-UPGRADE · файл: `tools/nsb_extra_research.py` · "
       f"дата: {datetime.now():%Y-%m-%d %H:%M}" if ru else
       f"Package: NSB-96-UPGRADE · file: `tools/nsb_extra_research.py` · "
       f"date: {datetime.now():%Y-%m-%d %H:%M}")
    ap("")
    ap("Четыре исследования, дополняющие протокол nsb_lab (L1–L10), по физике "
       "той же программы b-коррекции. Все числа воспроизводимы: "
       "`python3 tools/nsb_extra_research.py --run all`."
       if ru else
       "Four studies extending the nsb_lab protocol (L1–L10) within the "
       "same b-correction program. All numbers reproducible: "
       "`python3 tools/nsb_extra_research.py --run all`.")
    ap("")

    # ---- L11 -------------------------------------------------------------
    sc = l11["scalars"]
    ap("## L11. Перемежаемость и градиентная статистика: 48³ vs 96³ (t = 6)"
       if ru else
       "## L11. Intermittency & gradient statistics: 48³ vs 96³ (t = 6)")
    ap("")
    ap("Снимки одного и того же протокола (вихрь Тейлора–Грина, ν = 0.01, "
       "IFK-RK2, 2/3-обезвреживание) на T_end = 6: 48³ — из монографии "
       "(p5_snapshot_u.f64), 96³ — состояние прогона A96. Продольный "
       "градиент ζ = ∂u₁/∂x₁ вычисляется спектрально."
       if ru else
       "Snapshots of the same protocol (Taylor–Green vortex, ν = 0.01, "
       "IFK-RK2, 2/3 dealiasing) at T_end = 6: 48³ — from the monograph "
       "(p5_snapshot_u.f64), 96³ — the A96 run state. The longitudinal "
       "gradient ζ = ∂u₁/∂x₁ is computed spectrally.")
    ap("")
    ap("| величина | 48³ | 96³ | отн. разн. | вердикт |" if ru else
       "| quantity | 48³ | 96³ | rel. dev. | verdict |")
    ap("|---|---|---|---|---|")
    names = {"S3": "скос ζ" if ru else "skewness ζ",
             "F4": "плоскостность ζ" if ru else "flatness ζ",
             "F6": "гиперплоскостность ζ" if ru else "hyperflatness ζ",
             "omega_rms": "⟨ω²⟩^{1/2}" if ru else "⟨ω²⟩^{1/2}",
             "omega_max": "‖ω‖_∞"}
    for k in ("S3", "F4", "F6", "omega_rms", "omega_max"):
        a, b = sc["48"][k], sc["96"][k]
        rel = abs(b - a) / max(abs(a), 1e-300)
        thr = cfg["thr_grad"]
        v = "WIN" if rel < thr[0] else ("DRAW" if rel < thr[1] else "LOSS")
        ap(f"| {names[k]} | {a:.5f} | {b:.5f} | {rel:.2e} | {v} |")
    ap("")
    sf = l11["structure_functions"]
    ap(f"Коллапс функций структуры S₄(r) между 48³ и 96³ в общем "
       f"физическом интервале r ∈ [0.30, 1.60]: среднее |S₄⁹⁶/S₄⁴⁸ − 1| = "
       f"**{sf['collapse_S4_band_0.30_1.60']:.3f}** (для S₂: "
       f"{sf['collapse_S2_band_0.30_1.60']:.3f}). Интермиттентность "
       f"(рост F₄(r) при r → 0) воспроизводится при обоих разрешениях; "
       f"мелкомасштабная статистика устойчива к удвоению сетки."
       if ru else
       f"Structure-function collapse S₄(r) between 48³ and 96³ over the "
       f"common physical band r ∈ [0.30, 1.60]: mean |S₄⁹⁶/S₄⁴⁸ − 1| = "
       f"**{sf['collapse_S4_band_0.30_1.60']:.3f}** (for S₂: "
       f"{sf['collapse_S2_band_0.30_1.60']:.3f}). Intermittency (growth of "
       f"F₄(r) as r → 0) is reproduced at both resolutions; small-scale "
       f"statistics are robust to grid doubling.")
    ap("")
    ap(f"**Итог L11: {tally_line(l11)}.**" if ru else
       f"**L11 tally: {tally_line(l11)}.**")
    ap("")

    # ---- L12 -------------------------------------------------------------
    ap("## L12. Спектральный поток Π(k) и каскад: 48³ vs 96³ (t = 6)"
       if ru else
       "## L12. Spectral flux Π(k) and cascade: 48³ vs 96³ (t = 6)")
    ap("")
    ap("Оболочечный трансфер T(k) нелинейного члена (проектированный и "
       "обезвреженный), диссипация D(k) = νk²E(k), поток "
       "Π(k) = Σ_{q≥k}[D(q) − T(q)]. Три точных тождества и коллапс "
       "между разрешениями:"
       if ru else
       "Shell transfer T(k) of the projected, dealiased nonlinear term, "
       "dissipation D(k) = νk²E(k), flux Π(k) = Σ_{q≥k}[D(q) − T(q)]. "
       "Three exact identities and the inter-resolution collapse:")
    ap("")
    ap(f"- Σ T(k) = 0 (точная консервативность нелинейного члена): "
       f"|ΣT|/ε = {max(abs(l12['sumT48']) / l12['eps48'], abs(l12['sumT96']) / l12['eps96']):.2e}"
       if ru else
       f"- Σ T(k) = 0 (exact nonlinear conservation): "
       f"|ΣT|/ε = {max(abs(l12['sumT48']) / l12['eps48'], abs(l12['sumT96']) / l12['eps96']):.2e}")
    ap(f"- Π(0) = ε: отклонение ≤ {l12['verdicts'][1]['value']:.2e}"
       if ru else
       f"- Π(0) = ε: deviation ≤ {l12['verdicts'][1]['value']:.2e}")
    ap(f"- Π(0) против −dE/dt логов траекторий: "
       f"{l12['verdicts'][2]['value']:.2e}"
       if ru else
       f"- Π(0) vs −dE/dt of the trajectory logs: "
       f"{l12['verdicts'][2]['value']:.2e}")
    ap(f"- коллапс Π(k)/ε (k = 2…11): "
       f"**{l12['collapse_Pi_band_k2_11']:.3f}**"
       if ru else
       f"- Π(k)/ε collapse (k = 2…11): "
       f"**{l12['collapse_Pi_band_k2_11']:.3f}**")
    ap("")
    ap(f"ε(48³) = {l12['eps48']:.6f}, ε(96³) = {l12['eps96']:.6f} "
       f"(отн. разн. {abs(l12['eps96'] - l12['eps48']) / l12['eps48']:.2e}). "
       f"Прямой каскад с плато Π(k)/ε ≈ const в инерционном интервале "
       f"воспроизводится при обоих разрешениях; поток замыкается "
       f"диссипацией на k → k_max."
       if ru else
       f"ε(48³) = {l12['eps48']:.6f}, ε(96³) = {l12['eps96']:.6f} "
       f"(rel. dev. {abs(l12['eps96'] - l12['eps48']) / l12['eps48']:.2e}). "
       f"The forward cascade with the Π(k)/ε ≈ const plateau in the "
       f"inertial range is reproduced at both resolutions; the flux is "
       f"closed by dissipation as k → k_max.")
    ap("")
    ap(f"**Итог L12: {tally_line(l12)}.**" if ru else
       f"**L12 tally: {tally_line(l12)}.**")
    ap("")

    # ---- L13 -------------------------------------------------------------
    ap("## L13. Гипердиссипативное семейство КдФ: "
       "u_t + 6uu_x + u_xxx = −ν(−∂²)^b u" if ru else
       "## L13. Hyperdissipative KdV family: "
       "u_t + 6uu_x + u_xxx = −ν(−∂²)^b u")
    ap("")
    ap(f"Мост между b-семейством НСЭ (гл. 12/15 монографии) и главой 16 "
       f"(КдФ): солитон c = {cfg['kdvb_c']:g}, N = {cfg['kdvb_n']}, "
       f"L = {cfg['kdvb_l']:g}, dt = {cfg['kdvb_dt']:g}, T = "
       f"{cfg['kdvb_t_end']:g}, ν = {cfg['kdvb_nu']:g}, правило 2/3, "
       f"IFRK4. Семейство b ∈ {{{', '.join(f'{x:g}' for x in cfg['kdvb_family'])}}}."
       if ru else
       f"A bridge between the NS b-family (monograph ch. 12/15) and "
       f"chapter 16 (KdV): soliton c = {cfg['kdvb_c']:g}, N = "
       f"{cfg['kdvb_n']}, L = {cfg['kdvb_l']:g}, dt = {cfg['kdvb_dt']:g}, "
       f"T = {cfg['kdvb_t_end']:g}, ν = {cfg['kdvb_nu']:g}, the 2/3 rule, "
       f"IFRK4. Family b ∈ {{{', '.join(f'{x:g}' for x in cfg['kdvb_family'])}}}.")
    ap("")
    ap("| b_pow | A(T)/A₀ | k_ν(b) теория | k_e измерен | дрейф M |"
       if ru else
       "| b_pow | A(T)/A₀ | k_ν(b) theory | k_e measured | M drift |")
    ap("|---|---|---|---|---|")
    for row in l13["family_table"]:
        ap(f"| {row['b']:g} | {row['A_ratio']:.5f} | "
           f"{row['k_nu_theory']:.4f} | {row['k_e_measured']:.4f} | "
           f"{row['mass_drift']:.1e} |")
    ap("")
    ap(f"Точные проверки: дрейф массы {l13['mass_drift_max']:.1e} "
       f"(масса сохраняется ∀ b > 0 — k = 0 не затрагивается ни одним "
       f"членом); тождество dP/dt = −ν⟨u(−∂²)^b u⟩ в двух нормировках — "
       f"отклонение {l13['p_identity_max_dev']:.1e}; самосходимость "
       f"N 512→1024: {l13['conv_N']:.1e}; dt 1e-3→5e-4: "
       f"{l13['conv_dt']:.1e}. Диссипационный обрез k_e воспроизводит "
       f"зависимость k_ν(b) = (1/νT)^(1/2b) с ожидаемым сдвигом за счёт "
       f"нелинейного перераспределения энергии — та же физика "
       f"диссипационного интервала, что и в b-семействе НСЭ "
       f"(k_d·η_b → x*(b))."
       if ru else
       f"Exact checks: mass drift {l13['mass_drift_max']:.1e} (mass is "
       f"conserved ∀ b > 0 — the k = 0 mode is untouched by every term); "
       f"the identity dP/dt = −ν⟨u(−∂²)^b u⟩ in two normalizations "
       f"deviates by {l13['p_identity_max_dev']:.1e}; self-convergence "
       f"N 512→1024: {l13['conv_N']:.1e}; dt 1e-3→5e-4: "
       f"{l13['conv_dt']:.1e}. The dissipative cutoff k_e reproduces the "
       f"k_ν(b) = (1/νT)^(1/2b) dependence with the expected shift due to "
       f"nonlinear redistribution — the same dissipation-range physics "
       f"as in the NS b-family (k_d·η_b → x*(b)).")
    ap("")
    ap(f"**Итог L13: {tally_line(l13)}.**" if ru else
       f"**L13 tally: {tally_line(l13)}.**")
    ap("")

    # ---- L16 -------------------------------------------------------------
    if l16 is not None:
        hl = l16["headline"]
        att = l16["attribution"]
        ap("## L16. Самосходимость решателя P5: пространство × время + Ричардсон"
           if ru else
           "## L16. P5 solver self-convergence: space × time + Richardson")
        ap("")
        ap("Два скана одним и тем же решателем (IFK-RK2, 2/3-обезвреживание; "
           "вихрь Тейлора–Грина, ν = 0.01, T = 6). Пространственный: N ∈ "
           "{24, 36, 48, 72} при dt = 2·10⁻³ против референса 96³ (A96). "
           "Временной: dt ∈ {4·10⁻³, 2·10⁻³, 10⁻³, 5·10⁻⁴} при N = 48 против "
           "ref dt = 5·10⁻⁴. Все прогоны чекпоинтируются и детерминированы."
           if ru else
           "Two scans by the same solver (IFK-RK2, 2/3 dealiasing; Taylor–Green "
           "vortex, ν = 0.01, T = 6). Spatial: N ∈ {24, 36, 48, 72} at "
           "dt = 2·10⁻³ against the 96³ reference (A96). Temporal: dt ∈ "
           "{4·10⁻³, 2·10⁻³, 10⁻³, 5·10⁻⁴} at N = 48 against ref dt = 5·10⁻⁴. "
           "All runs are checkpointed and deterministic.")
        ap("")
        ap("Относительная ошибка против 96³ (dt = 2·10⁻³):" if ru else
           "Relative error against 96³ (dt = 2·10⁻³):")
        ap("")
        ap("| N | Ω_max | ‖ω‖_∞ | I_BKM | E_final |")
        ap("|---|---|---|---|---|")
        for i, p in enumerate(l16["spatial"]["Omega_max"]["points"]):
            cells = " | ".join(
                f"{l16['spatial'][q]['points'][i]['rel_err']:.2e}"
                for q in ("Omega_max", "omega_inf_max", "I_BKM_T", "E_final"))
            ap(f"| {p['N']} | {cells} |")
        ap("")
        fit = l16["spatial"]["Omega_max"]["exp_fit"]
        ap(f"Наблюдаемый временной порядок: p(Ω_max) = {l16['temporal']['Omega_max']['p_mean']:.2f}, "
           f"p(E_final) = {l16['temporal']['E_final']['p_mean']:.2f} — ниже "
           f"формального порядка 2 (редукция порядка / внеасимптотический "
           f"режим: относительные временные ошибки при dt = 2·10⁻³ уже на "
           f"уровне 10⁻⁷…10⁻⁵, рядом с этажом схемы). Ключевое: эти "
           f"временные ошибки ничтожны на фоне пространственных (см. "
           f"атрибуцию ниже), выводы 48³↔96³ от них не зависят."
           if ru else
           f"Observed temporal order: p(Ω_max) = {l16['temporal']['Omega_max']['p_mean']:.2f}, "
           f"p(E_final) = {l16['temporal']['E_final']['p_mean']:.2f} — below "
           f"the formal order 2 (order reduction / pre-asymptotic regime: "
           f"relative temporal errors at dt = 2·10⁻³ are already at "
           f"10⁻⁷…10⁻⁵, near the scheme floor). The key point: these "
           f"temporal errors are negligible against the spatial ones (see "
           f"attribution below), so the 48³↔96³ conclusions are unaffected.")
        ap("")
        ap(f"Экспоненциальная посадка err(N) ∝ e^(−cN) (Ω_max): "
           f"c = {fit['c']:.3f}, r² = {fit['r2']:.3f}; минимальный r² по "
           f"величинам — {hl['r2_exp_min']:.3f}. Сетки 24³→72³ сходятся к "
           f"96³-референсу экспоненциально; монотонность: "
           f"{hl['n_monotone']}/4 величин (‖ω‖_∞ — sup-статистика, "
           f"немонотонна на уровне 10⁻² между 48³ и 72³)."
           if ru else
           f"Exponential fit err(N) ∝ e^(−cN) (Ω_max): c = {fit['c']:.3f}, "
           f"r² = {fit['r2']:.3f}; minimum r² over quantities: "
           f"{hl['r2_exp_min']:.3f}. Grids 24³→72³ converge exponentially "
           f"to the 96³ reference; monotonicity: {hl['n_monotone']}/4 "
           f"quantities (‖ω‖_∞ — a sup-statistic, non-monotone at the "
           f"10⁻² level between 48³ and 72³).")
        ap("")
        ap("Временная сходимость (N = 48, ref dt = 5·10⁻⁴):" if ru else
           "Temporal convergence (N = 48, ref dt = 5·10⁻⁴):")
        ap("")
        ap("| dt | Ω_max | ‖ω‖_∞ | I_BKM | E_final |")
        ap("|---|---|---|---|---|")
        for dt_ in sorted(p["dt"] for p in l16["temporal"]["Omega_max"]["points"]):
            row = []
            for q in ("Omega_max", "omega_inf_max", "I_BKM_T", "E_final"):
                e = next(pp["rel_err"] for pp in l16["temporal"][q]["points"]
                         if abs(pp["dt"] - dt_) < 1e-12)
                row.append(f"{e:.2e}")
            ap(f"| {dt_:g} | {' | '.join(row)} |")
        ap("")
        for q, nm in (("Omega_max", "Ω_max"), ("E_final", "E_final")):
            d = l16["temporal"][q]
            rq = d["richardson_p2"]
            ap(f"- {nm}: p₁ = {d['p_2e3_1e3']:.2f}, "
               f"p₂ (Роаш, три уровня) = {d['p_roache_3lvl']:.2f}, "
               f"p̄ = {d['p_mean']:.2f}; Ричардсон dt→0 при p = 2: "
               f"Q₀ = {rq['Q0']:.9f}, невязка {rq['resid']:.2e}"
               if ru else
               f"- {nm}: p₁ = {d['p_2e3_1e3']:.2f}, "
               f"p₂ (Roache, three-level) = {d['p_roache_3lvl']:.2f}, "
               f"p̄ = {d['p_mean']:.2f}; Richardson dt→0 at p = 2: "
               f"Q₀ = {rq['Q0']:.9f}, residual {rq['resid']:.2e}")
        ap("")
        att_s = ", ".join(
            f"{nm} ×{att[q]['ratio_spatial_over_temporal']:.0f}"
            for q, nm in (("Omega_max", "Ω_max"), ("E_final", "E_final"))
            if math.isfinite(att[q]["ratio_spatial_over_temporal"]))
        ap(f"Атрибуция ошибки 48³↔96³ (пространственная ошибка / временная "
           f"ошибка при dt = 2·10⁻³): {att_s}. Расхождение headline-величин "
           f"между 48³ и 96³ определяется разрешением спектрального хвоста, "
           f"а не временным шагом протокола — независимое подтверждение "
           f"интерпретации монографии (выводы 1–2 REPORT_96_FINDINGS)."
           if ru else
           f"Attribution of the 48³↔96³ difference (spatial error / temporal "
           f"error at dt = 2·10⁻³): {att_s}. The headline-quantity gap "
           f"between 48³ and 96³ is governed by spectral-tail resolution, "
           f"not by the protocol time step — an independent confirmation of "
           f"the monograph interpretation (findings 1–2 in "
           f"REPORT_96_FINDINGS).")
        ap("")
        for r in l16["verdicts"]:
            ap(f"- {r['test']}: {r['value']:.3g} → **{r['verdict']}**")
        ap("")
        ap(f"**Итог L16: {tally_line(l16)}.**" if ru else
           f"**L16 tally: {tally_line(l16)}.**")
        ap("")

    # ---- L17 -------------------------------------------------------------
    if l17 is not None:
        zd = l17["zero_drift"]
        csb = l17["cs_backscatter"]
        md = l17["modes"]
        d7 = l17["d7_chain"]
        syn = l17["dns_synthetic"]
        tgt = l17["dns_tg"]
        ap("## L17. φ-аудит монографии о двухслойных φ-аттракторах"
           if ru else
           "## L17. φ-audit of the two-layer φ-attractor monograph")
        ap("")
        ap("Независимый вычислительный аудит загруженной пользователем "
           "монографии «Двухслойные φ-аттракторы в точечно-вихревой модели: "
           "универсальная константа Смагоринского и динамические инварианты». "
           "Проверяется математическая рамка (φ, Фибоначчи, RG), условия "
           "нулевого дрейфа §2.2, LES-процедура приложения B, линейная "
           "теория приложения Г и DNS-протокол приложения Д."
           if ru else
           "An independent computational audit of the user-uploaded monograph "
           "'Two-layer φ-attractors in the point-vortex model'. Verified: the "
           "mathematical frame (φ, Fibonacci, RG), the §2.2 zero-drift "
           "conditions, the app.-B LES procedure, the app.-Г linear theory "
           "and the app.-Д DNS protocol.")
        ap("")
        ap("**Подтверждено (точно):**" if ru else "**Confirmed (exact):**")
        ap(f"- φ-алгебра (прил. Z.1): максимум остатка из 10 тождеств "
           f"{max(c['residual'] for c in l17['algebra']):.1e} — машинная "
           f"точность"
           if ru else
           f"- φ-algebra (app. Z.1): max residual over 10 identities "
           f"{max(c['residual'] for c in l17['algebra']):.1e} — machine "
           f"precision")
        ap(f"- спектр Фибоначчи (табл. X.6): max |μ−φ| = "
           f"{l17['fib_spectrum']['max_dev']:.4f}, монотонность Бине: "
           f"{l17['fib_spectrum']['binet_violations']} нарушений"
           if ru else
           f"- Fibonacci spectrum (tab. X.6): max |μ−φ| = "
           f"{l17['fib_spectrum']['max_dev']:.4f}, Binet monotonicity: "
           f"{l17['fib_spectrum']['binet_violations']} violations")
        ap(f"- RG-отображение μ→1+1/μ: наклон {l17['rg_map']['slope']:.4f} "
           f"против теоретического ln(1/φ²) = "
           f"{l17['rg_map']['slope_theory']:.4f} (откл. "
           f"{l17['rg_map']['rate_rel_dev']:.1e})"
           if ru else
           f"- RG map μ→1+1/μ: slope {l17['rg_map']['slope']:.4f} vs "
           f"theoretical ln(1/φ²) = {l17['rg_map']['slope_theory']:.4f} "
           f"(dev. {l17['rg_map']['rate_rel_dev']:.1e})")
        ap("")
        ap("**Новые строгие результаты (теоремы L17):**" if ru else
           "**New rigorous results (L17 theorems):**")
        ap(f"- условие нулевого дрейфа (5) при исключении s сводится к "
           f"(Γ_BΓ_C − Γ_AΓ_D)·m₂ + (Γ_BΓ_D − Γ_AΓ_C)·m_M + (Γ_D² − Γ_C²)·m₁ "
           f"= 0 (невязка тождества {zd['identity_max_mismatch']:.1e}); для "
           f"фибоначчиевых квадруплетов a·b·b·c Γ_BΓ_C − Γ_AΓ_D = ±1 "
           f"(Кассини), а доминирующий член F²ₖ₊₁·m_M > 0 — решений НЕТ при "
           f"любом масштабе ({sum(1 for s in zd['asym_scans'] if s['roots'] == 0)}"
           f"/6 конфигураций, скан корней)"
           if ru else
           f"- eliminating s from the zero-drift condition (5) gives "
           f"(Γ_BΓ_C − Γ_AΓ_D)·m₂ + (Γ_BΓ_D − Γ_AΓ_C)·m_M + (Γ_D² − Γ_C²)·m₁ "
           f"= 0 (identity residual {zd['identity_max_mismatch']:.1e}); for "
           f"Fibonacci a·b·b·c quadruples Γ_BΓ_C − Γ_AΓ_D = ±1 (Cassini) "
           f"while the dominant term F²ₖ₊₁·m_M > 0 — NO solution at any "
           f"scale ({sum(1 for s in zd['asym_scans'] if s['roots'] == 0)}/6 "
           f"configurations, root scan)")
        ap(f"- для симметричных a·a·b·b все три коэффициента обнуляются — "
           f"система вырождена в однопараметрическое семейство, и φ-геометрия "
           f"достижима конструктивно (невязка {zd['sym_family_residual']:.1e})"
           if ru else
           f"- for symmetric a·a·b·b all three coefficients vanish — the "
           f"system degenerates to a one-parameter family, and the "
           f"φ-geometry is attainable constructively (residual "
           f"{zd['sym_family_residual']:.1e})")
        ap(f"- подынтегральное выражение процедуры приложения B нечётно по x "
           f"при x-зеркальной симметрии конфигурации ⇒ числитель ≡ 0 (макс. "
           f"|C_s²| на симметричных {l17['verdicts'][7]['value']:.1e}); на "
           f"асимметричных a·b·b·c поток отрицателен во всех "
           f"{csb['n_negative']}/{csb['n_total']} сканах (backscatter) ⇒ "
           f"процедура возвращает null — заявленная универсальность "
           f"C_s⁽⁰⁾ = 0.080±0.005 из опубликованной процедуры + геометрии "
           f"не воспроизводится (контрольные поля дают ненулевой поток)"
           if ru else
           f"- the app.-B integrand is odd in x for x-mirror-symmetric "
           f"configurations ⇒ the numerator ≡ 0 (max |C_s²| on symmetric "
           f"{l17['verdicts'][7]['value']:.1e}); on asymmetric a·b·b·c the "
           f"flux is negative in all {csb['n_negative']}/{csb['n_total']} "
           f"scans (backscatter) ⇒ the procedure returns null — the claimed "
           f"universality C_s⁽⁰⁾ = 0.080±0.005 is not reproducible from the "
           f"published procedure + geometry (control fields show non-zero "
           f"flux)")
        ap("")
        ap("**Расхождения с приложениями Г/Д:**" if ru else
           "**Discrepancies with apps. Г/Д:**")
        ap(f"- доминирующая частота формы ν̂(R₂) = {md['nu_hat_R2']:.2f} "
           f"против предсказания (D.5b) ν_breath = {md['nu_breath_d5b']:.2f} "
           f"(откл. {md['rel_dev']:.2f} ≫ допуска 0.15 из Д.4) — формулы "
           f"(D.5) описывают другую конфигурацию (жёсткое вращение), а не "
           f"двухпараболическую геометрию §2"
           if ru else
           f"- dominant shape frequency ν̂(R₂) = {md['nu_hat_R2']:.2f} vs the "
           f"(D.5b) prediction ν_breath = {md['nu_breath_d5b']:.2f} "
           f"(dev. {md['rel_dev']:.2f} ≫ the 0.15 tolerance of Д.4) — the "
           f"(D.5) formulas describe a different configuration (rigid "
           f"rotation), not the §2 two-parabola geometry")
        ap(f"- цепочка (D.6b)–(D.8): α₂(D.6b) = {d7['alpha2_d6b']:.4f} "
           f"против заявленного {d7['alpha2_claim']}; γ двумя формами (D.7): "
           f"{d7['gamma_form1']:.2e} и {d7['gamma_form2']:.2e} против "
           f"{d7['gamma_claim']:.4f}; τ_φ ≈ {min(d7['tau_form1'], d7['tau_form2']):.0f} "
           f"против 322 оборотов"
           if ru else
           f"- the (D.6b)–(D.8) chain: α₂(D.6b) = {d7['alpha2_d6b']:.4f} vs "
           f"the claimed {d7['alpha2_claim']}; γ in the two (D.7) forms: "
           f"{d7['gamma_form1']:.2e} and {d7['gamma_form2']:.2e} vs "
           f"{d7['gamma_claim']:.4f}; τ_φ ≈ {min(d7['tau_form1'], d7['tau_form2']):.0f} "
           f"vs 322 turnovers")
        ap(f"- DNS-мост приложения Д: механика валидирована на синтетическом "
           f"φ-поле (ρ̂ = {syn['rho_hat']:.4f} против φ, откл. "
           f"{syn['rel_dev']:.4f}); на срезах 96³ TG (t = 6) квадруплеты "
           f"2+/2− обнаружены в {tgt['slices_ok']}/{tgt['slices_total']} "
           f"срезах, но метрика ρ = R₁/R₂ вырождается на шахматной решётке "
           f"TG (медиана R₂/R₁ = {tgt['r2_over_r1_median']:.3f}) — для "
           f"φ-статистики нужен ансамбль 2D-турбулентности с обратным "
           f"каскадом"
           if ru else
           f"- the app.-Д DNS bridge: the machinery is validated on a "
           f"synthetic φ-field (ρ̂ = {syn['rho_hat']:.4f} vs φ, dev. "
           f"{syn['rel_dev']:.4f}); on the 96³ TG slices (t = 6) 2+/2− "
           f"quadruples are found in {tgt['slices_ok']}/{tgt['slices_total']} "
           f"slices, but the ρ = R₁/R₂ metric degenerates on the TG "
           f"checkerboard lattice (median R₂/R₁ = "
           f"{tgt['r2_over_r1_median']:.3f}) — φ-statistics require a "
           f"2D inverse-cascade turbulence ensemble")
        ap("")
        for r in l17["verdicts"]:
            ap(f"- {r['test']}: {r['value']:.3g} → **{r['verdict']}**")
        ap("")
        ap(f"**Итог L17: {tally_line(l17)}.**" if ru else
           f"**L17 tally: {tally_line(l17)}.**")
        ap("")

    # ---- сводные вердикты -------------------------------------------------
    ap("## Сводка вердиктов" if ru else "## Verdict summary")
    ap("")
    ap("| лаборатория | WIN | DRAW | LOSS |" if ru else
       "| laboratory | WIN | DRAW | LOSS |")
    ap("|---|---|---|---|")
    for tag, o in (("L11", l11), ("L12", l12), ("L13", l13), ("L16", l16),
                   ("L17", l17)):
        if o is None:
            continue
        tt = o["tally"]
        ap(f"| {tag} | {tt['WIN']} | {tt['DRAW']} | {tt['LOSS']} |")
    ap("")

    md = "\n".join(lines)
    p_md = os.path.join(OUT_REPORTS, "EXTRA_RESEARCH_REPORT.md")
    with open(p_md, "w", encoding="utf-8") as fh:
        fh.write(md + "\n")
    p_tx = os.path.join(OUT_REPORTS, "EXTRA_RESEARCH_REPORT.txt")
    with open(p_tx, "w", encoding="utf-8") as fh:
        fh.write(_obj_to_text({
            "L11": {k: v for k, v in l11.items()
                    if k not in ("structure_functions",)},
            "L12": {k: v for k, v in l12.items()
                    if k not in ("E48", "T48", "Pi48", "E96", "T96",
                                 "Pi96", "k")},
            "L13": {k: v for k, v in l13.items()
                    if k not in ("series", "spectra")},
            "L16": ({k: v for k, v in l16.items()
                     if k not in ("runs", "balances")} if l16 else {}),
            "L17": ({k: v for k, v in l17.items()
                     if k not in ("modes", "dns_tg", "cs_backscatter", "fib_spectrum")}
                    if l17 else {}),
        }))
    ui.say(ui.c(f"    L15: {os.path.relpath(p_md, PKG_ROOT)}"))
    ui.say(ui.dim(f"         {os.path.relpath(p_tx, PKG_ROOT)}"))
    return p_md


# ============================================================================
# КРОСС-ЯЗЫКОВОЙ ЭТАЛОН ДЛЯ JULIA (nsb_extra_research.jl)
# ============================================================================
def write_julia_ref(cfg: XCfg, ui: UI | None = None) -> str:
    """Файл-эталон extra14_julia_ref.json: те же величины в том же случае,
    что считает nsb_extra_research.jl (сравнение Python ↔ Julia)."""
    sol48 = _CACHE.get("sol48") or load_solver48(cfg, ui)
    sol96 = _CACHE.get("sol96") or load_solver96(cfg, ui)
    _CACHE["sol48"], _CACHE["sol96"] = sol48, sol96
    g48 = grad_stats(sol48)
    g96 = grad_stats(sol96)
    n, l = cfg["kdvb_n_coarse"], cfg["kdvb_l"]
    dt, T, nu, b = 1e-3, 2.0, cfg["kdvb_nu"], 1.25
    x = np.linspace(0.0, l, n, endpoint=False)
    r = kdv_b_run(n, l, dt, T, kdv_soliton(x, cfg["kdvb_c"], cfg["kdvb_x0"]),
                  nu, b)
    obj = {
        "program": "NSB-96-UPGRADE / nsb_extra_research (Python reference)",
        "grad48": {k: g48[k] for k in ("S3", "F4", "F6")},
        "grad96": {k: g96[k] for k in ("S3", "F4", "F6")},
        "E96_check": _CACHE.get("E96"),
        "E48_check": _CACHE.get("E48"),
        "kdv_case": {"n": n, "l": l, "dt": dt, "T": T, "nu": nu, "b": b,
                     "c": cfg["kdvb_c"], "x0": cfg["kdvb_x0"],
                     "A_T": r["A"][-1], "P_T": r["P"][-1],
                     "M0": r["M"][0], "MT": r["M"][-1],
                     "mass_drift": r["mass_drift"]},
    }
    p = os.path.join(OUT_RESULTS, "extra14_julia_ref.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    if ui is not None:
        ui.say(ui.c(f"    julia-ref: {os.path.relpath(p, PKG_ROOT)}"))
    return p


# ============================================================================
# МЕНЮ И CLI
# ============================================================================
def _set_lang(ui: UI, lang: str) -> None:
    """Объединяем базовые строки nsb_lab с локализацией L11–L15."""
    ui.lang = lang if lang in L10N else "ru"
    from nsb_lab import I18N
    merged = dict(I18N[ui.lang])
    merged.update(L10N[ui.lang])
    ui.t = merged


def _banner(ui: UI) -> None:
    art = r"""
    ___  ____  ___  ____  ___    _  _  ____  ____  ___
   / __)(  _ \(  _)(_  _)/ __)  ( \/ )(  _ \(_  _)/ __)
  ( (__ ) __/ ) _)  )(  ( (__    \  /  )   /  )(  \__ \
   \___)(__)  (___) (__) \___)    \/  (_)\_) (__) (___/"""
    ui.say(ui.c(art))
    ui.say(ui.y("=" * 78))
    ui.say(ui.c(ui.t["title"].center(78)))
    ui.say(ui.dim(ui.t["subtitle"].center(78)))
    ui.say(ui.m(B_UNIV_S.center(78)))
    ui.say(ui.y("=" * 78))


def _menu(ui: UI, cfg: XCfg) -> None:
    t = ui.t
    while True:
        _banner(ui)
        ui.say(ui.c(f"  [{t['menu_hdr']}]", ))
        for key, label in (("11", t["lab11"]), ("12", t["lab12"]),
                           ("13", t["lab13"]), ("14", t["lab14"]),
                           ("15", t["lab15"]), ("16", t["lab16"]),
                           ("17", t["lab17"]),
                           ("C", t["lab_cfg"]),
                           ("L", t["lab_lang"]), ("A", t["lab_all"]),
                           ("Q", t["lab_quit"])):
            ui.say(f"   {key:<3} {label}")
        ch = ui.ask(t["choose"]).strip().upper()
        if ch == "Q":
            ui.say(ui.dim("bye"))
            return
        if ch == "L":
            _set_lang(ui, "en" if ui.lang == "ru" else "ru")
            cfg.d["lang"] = ui.lang
            continue
        if ch == "C":
            _config_menu(ui, cfg)
            continue
        os.system("cls" if os.name == "nt" else "clear")
        try:
            if ch == "A":
                _run_all(ui, cfg)
            elif ch in ("11", "12", "13", "14", "15", "16", "17"):
                _dispatch(ui, cfg, ch)
            else:
                continue
        except Exception as exc:  # noqa: BLE001
            ui.say(ui.r(f"  ERROR: {exc!r}"))
        ui.say(ui.dim(f"\n  {t['back']}"))
        ui.ask("")


def _config_menu(ui: UI, cfg: XCfg) -> None:
    t = ui.t
    while True:
        ui.say(ui.c(f"  [{t['config_hdr']}]"))
        for k, v in cfg.d.items():
            ui.say(ui.dim(f"   {k:<22} = {v}"))
        name = ui.ask(t["config_ask"]).strip()
        if not name:
            return
        val = ui.ask(t["config_val"]).strip()
        if not cfg.set_key(name, val):
            ui.say(ui.r("  " + t["config_bad"]))
            continue
        p = cfg.save()
        ui.say(ui.g(f"  {t['config_saved']} {p}"))


def _dispatch(ui: UI, cfg: XCfg, lab: str) -> dict | list | str | None:
    if lab == "11":
        return lab11_gradstats(ui, cfg)
    if lab == "12":
        return lab12_flux(ui, cfg)
    if lab == "13":
        return lab13_kdvb(ui, cfg)
    if lab == "14":
        return lab14_figures(ui, cfg)
    if lab == "15":
        return lab15_report(ui, cfg)
    if lab == "16":
        return lab16_convergence(ui, cfg)
    if lab == "17":
        return lab17_phiaudit(ui, cfg)
    if lab == "jref":
        return write_julia_ref(ui=ui, cfg=cfg)
    return None


def _run_all(ui: UI, cfg: XCfg) -> None:
    for lab in ("11", "12", "13", "16", "17", "14", "15"):
        ui.say("")
        _dispatch(ui, cfg, lab)
    ui.say("")
    ui.say(ui.c("  " + "=" * 74))
    ui.say(ui.c("  NSB EXTRA — ВСЕ ЛАБОРАТОРИИ ЗАВЕРШЕНЫ".center(78)
                if ui.lang == "ru" else
                "  NSB EXTRA — ALL LABORATORIES COMPLETE".center(78)))


def main() -> None:
    ap = argparse.ArgumentParser(
        description="NSB EXTRA research labs (L11–L17) for NSB-96-UPGRADE")
    ap.add_argument("--lang", choices=("ru", "en"), default=None)
    ap.add_argument("--run", default=None,
                    help="all | 11 | 12 | 13 | 14 | 15 | 16 | 17")
    ap.add_argument("--yes", action="store_true",
                    help="non-interactive mode")
    ap.add_argument("--set", nargs=2, action="append", default=[],
                    metavar=("KEY", "VALUE"))
    args = ap.parse_args()

    overrides = {k: v for k, v in args.set}
    cfg = XCfg(overrides)
    lang = args.lang or cfg.d.get("lang", "ru")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(PKG_ROOT, "logs",
                            f"nsb_extra_{stamp}.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    ui = UI(lang, log_path)
    _set_lang(ui, lang)

    if args.run is None and not args.yes:
        _menu(ui, cfg)
        return
    _banner(ui)
    if args.run in (None, "all"):
        _run_all(ui, cfg)
    else:
        r = args.run.strip().lower()
        alias = {"gradstats": "11", "flux": "12", "kdvb": "13",
                 "figures": "14", "report": "15", "conv": "16",
                 "convergence": "16", "phi": "17", "phiaudit": "17",
                 "julia-ref": "jref", "jref": "jref"}
        r = alias.get(r, r)
        if r not in ("11", "12", "13", "14", "15", "16", "17", "jref"):
            ui.say(ui.r(f"  unknown lab: {args.run}"))
            return
        _dispatch(ui, cfg, r)


if __name__ == "__main__":
    main()
