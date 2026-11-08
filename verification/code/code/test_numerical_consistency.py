#!/usr/bin/env python3
"""Согласованность численного слоя с формальным ядром и закреплёнными
значениями.

Проверяется:
  * точная константа b = 1/(4π+2√3) на 50 знаков (mpmath) против
    строкового эталона, который соответствует Lean-теореме
    Verification.Constants.b_eq_kirchhoff_value;
  * границы 0.062 < b < 0.063 — численно против Lean-теорем
    b_gt_062 / b_lt_063;
  * солитон KdV (численно) против Lean-теоремы
    Verification.KdV.soliton_solves_KdV — невязка ODE на машинном нуле;
  * мастер-соотношение C_s — численно против Lean-теоремы cs_pos/квантов.
"""
import math
import subprocess
import sys
from pathlib import Path

VER = Path(__file__).resolve().parents[1]
NUM = VER / "numerical" / "python"

PINNED_B_50 = "0.062381194121028227546339671639402081186993306823604"


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
    sys.path.insert(0, str(NUM))
    import kdv_soliton as k
    for c in (0.5, 1.0, 2.0):
        for xi in (-2.0, -0.7, 0.0, 0.9, 3.1):
            u, up, upp, uppp = k.soliton(xi, c)
            residual = uppp - c * up + 6 * u * up  # travelling-wave form of KdV
            assert abs(residual) < 1e-12, (c, xi, residual)


def test_stdlib_numerical_modules_pass():
    """stdlib-модули вычислительного слоя обязаны проходить целиком."""
    for mod in ["kdv_soliton.py", "klein_dynamics.py", "preprint_chain.py",
                "smagorinsky_kolmogorov.py"]:
        proc = subprocess.run([sys.executable, str(NUM / mod)],
                              capture_output=True, text=True, timeout=300)
        assert proc.returncode == 0, f"{mod} упал:\n{proc.stdout[-800:]}"
        assert "FAIL" not in proc.stdout, f"{mod} содержит FAIL"
        assert "JSON: " in proc.stdout, f"{mod} не выдал JSON-вердикт"
