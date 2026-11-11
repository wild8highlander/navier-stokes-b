#!/usr/bin/env python3
"""Согласованность численного слоя с формальным ядром и закреплёнными
значениями.

Проверяется (все значения считаются на месте, без внешних модулей):
  * точная константа b = 1/(4π+2√3) на 50 знаков (mpmath) против
    строкового эталона, который соответствует Lean-теореме
    VortexTube.b_eq_kirchhoff_value;
  * границы 0.062 < b < 0.063 — численно против Lean-теорем
    Section1.b_gt_062 / Section1.b_lt_063;
  * солитон KdV — невязка бегущей волны u''' − c·u' + 6·u·u' = 0 для
    u = (c/2)·sech²(√c·(x−ct)/2) на машинном нуле. В Lean определена
    сигнатура Section4.soliton (подстановка в KdV пока НЕ формализована —
    см. честный комментарий в lean4/Soliton.lean); этот тест закрепляет
    численную сторону того же утверждения;
  * мастер-соотношение Смагоринского–Колмогорова C_s = 1/(π(3C_K/2)^{3/4})
    против pinned-строки (численная сторона; Lean-порт соотношения в это
    ядро не входит — счётчики см. verify_ns_full.py задача 2 и
    scripts/julia_levels/l7_smagorinsky_kolmogorov.jl);
  * сквозной прогон pinned-задачи монолита (задача 9) как subprocess.
"""
import math
import subprocess
import sys
from pathlib import Path

VER = Path(__file__).resolve().parents[1]
MONOLITH = VER / "verify_ns_full.py"

PINNED_B_50 = "0.062381194121028227546339671639402081186993306823604"
PINNED_CS_50 = "0.1732659558297058017568595667273903913207704370073762727"


def test_b_exact_digits():
    try:
        import mpmath as mp
    except ImportError:
        import pytest
        pytest.skip("mpmath недоступен")
    mp.mp.dps = 60
    b = 1 / (4 * mp.pi + 2 * mp.sqrt(3))
    b50 = mp.nstr(b, 50)
    assert PINNED_B_50.startswith(b50), (b50, PINNED_B_50)
    assert mp.mpf("0.062") < b < mp.mpf("0.063"), "границы 0.062 < b < 0.063"


def test_b_bounds_float():
    b = 1 / (4 * math.pi + 2 * math.sqrt(3))
    assert 0.062 < b < 0.063


def test_kdv_soliton_residual_machine_zero():
    """Невязка u''' − c·u' + 6·u·u' для солитона (c/2)·sech²(√c·ξ/2),
    производные аналитические (символически верные формулы)."""
    def soliton(x, c):
        """u(ξ) = (c/2)·sech²(kξ), k = √c/2; точные производные:
           u'  = −(c√c/2)·s·t
           u'' = (c²/4)·s·(2t² − s)
           u'''= (c²√c/2)·s·t·(2s − t²),  s = sech², t = tanh.
        Невязка u''' − c·u' + 6·u·u' = (c²√c/2)·s·t·(1 − t² − s) ≡ 0,
        так как 1 − t² = s."""
        k = math.sqrt(c) / 2
        e = math.exp(-abs(x) * k)
        sech1 = 2 * e / (1 + e * e)          # sech(|x|k) — чётная функция
        t = math.tanh(x * k)
        s = sech1 * sech1
        u = (c / 2) * s
        up = -(c * math.sqrt(c) / 2) * s * t
        upp = (c * c / 4) * s * (2 * t * t - s)
        uppp = (c * c * math.sqrt(c) / 2) * s * t * (2 * s - t * t)
        return u, up, upp, uppp

    for c in (0.5, 1.0, 2.0):
        for xi in (-2.0, -0.7, 0.0, 0.9, 3.1):
            u, up, upp, uppp = soliton(xi, c)
            residual = uppp - c * up + 6 * u * up  # форма бегущей волны KdV
            assert abs(residual) < 1e-12, (c, xi, residual)


def test_master_relation_pinned():
    try:
        import mpmath as mp
    except ImportError:
        import pytest
        pytest.skip("mpmath недоступен")
    mp.mp.dps = 60
    cs = 1 / (mp.pi * (3 * mp.mpf("1.5") / 2) ** (mp.mpf(3) / 4))
    cs55 = mp.nstr(cs, 55)
    assert PINNED_CS_50.startswith(cs55) or cs55 == PINNED_CS_50, cs55


def test_monolith_pinned_task_passes():
    """Задача 9 монолита (pinned-значения на Float64) — сквозной прогон."""
    if not MONOLITH.is_file():
        import pytest
        pytest.skip("verify_ns_full.py не найден")
    proc = subprocess.run(
        [sys.executable, str(MONOLITH), "--task", "9", "--no-two-pass", "--quiet"],
        capture_output=True, text=True, timeout=600)
    assert proc.returncode == 0, f"монолит упал:\n{proc.stdout[-800:]}"
    assert "[FAIL]" not in proc.stdout, proc.stdout[-800:]
