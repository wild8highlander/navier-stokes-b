# -*- coding: utf-8 -*-
"""
L1 — константы: символьная форма против float64, 50 знаков (mpmath).

Проверки:
  * b в двух алгебраических формах совпадают (π/(4π²+2π√3) = 1/(4π+2√3));
  * sin θ_b = b — точно (невязка 0 на 50 знаках);
  * cos θ_b = √(1−b²); ln(1+b); C_s Лилли = (1/π)(9/4)^(−3/4); φ; e;
  * замыкание Клейна: exp(b·β_K·L_min) = 1,3516373443851241821… —
    это независимая проверка цифр константы L_min монографии;
  * каждое значение: сравнение символьного (50 знаков) и float64 (~16 знаков).
Опционально (если установлен sympy): алгебраическое упрощение разности форм b → 0.
"""
import json, math, sys
from pathlib import Path

import mpmath as mp

sys.path.insert(0, str(Path(__file__).parent))
from config import constants, EXPECTED, MP_DIGITS, B_FORM_SIMP

RESULTS_DIR = Path(__file__).parent / "results"


def run():
    c = constants()
    results = {}
    all_ok = True

    def entry(key, sym_value, expected_str):
        nonlocal all_ok
        sym_str = mp.nstr(sym_value, MP_DIGITS)
        f64 = float(sym_value)
        f64_str = repr(f64)
        abs_diff = abs(f64 - float(expected_str))
        ok = sym_str.startswith(expected_str[: min(len(expected_str), 34)].rstrip("0")) \
            or sym_str[: len(expected_str)] == expected_str
        ok = ok and abs_diff < 1e-13
        all_ok = all_ok and ok
        results[key] = {
            "symbolic": sym_str,
            "float64": f64_str,
            "abs_diff": f"{abs_diff:.3e}",
            "ok": bool(ok),
        }

    entry("b (две формы)", c["b"], EXPECTED["b"])
    # алгебраическое тождество двух форм
    diff_forms = c["b"] - B_FORM_SIMP()
    results["b: разность двух форм"] = {"symbolic": mp.nstr(diff_forms, 5), "ok": bool(diff_forms == 0)}
    all_ok = all_ok and diff_forms == 0

    entry("theta_b = arcsin(b)", c["theta_b"], EXPECTED["theta_b"])
    resid = mp.sin(c["theta_b"]) - c["b"]
    results["sin(theta_b) = b (невязка)"] = {"symbolic": mp.nstr(resid, 5), "ok": bool(resid == 0)}
    all_ok = all_ok and resid == 0
    results["theta_b в градусах"] = {"symbolic": mp.nstr(c["theta_b_deg"], 40),
                                     "float64": repr(math.degrees(math.asin(float(c["b"]))))}

    entry("cos(theta_b) = sqrt(1-b^2)", c["cos_theta_b"], EXPECTED["cos_theta_b"])
    entry("ln(1+b)", c["ln_1p_b"], EXPECTED["ln_1p_b"])
    entry("Z_full/Z_leading = exp(b·β_K·L_min)", c["Z_full_leading"], EXPECTED["Z_full_leading"])
    entry("b·β_K·L_min", c["b_beta_L"], EXPECTED["b_beta_L"])
    entry("C_s (Лилли)", c["Cs_lilly"], EXPECTED["Cs_lilly"])
    entry("phi", c["phi"], EXPECTED["phi"])
    entry("e_klein (= e)", c["e_klein"], EXPECTED["e_klein"])
    entry("alpha (Клейн, монография)", c["alpha_klein"], EXPECTED["alpha_klein"])
    entry("L_min (Клейн, монография)", c["L_min_klein"], EXPECTED["L_min_klein"])

    # опциональный sympy: символьное доказательство эквивалентности форм b
    sympy_note = "sympy не установлен — пропущено (не влияет на статус)"
    try:
        import sympy as sp
        x = sp.symbols("x", positive=True)
        pi_s = sp.pi
        diff = sp.simplify(pi_s / (4 * pi_s**2 + 2 * pi_s * sp.sqrt(3)) - 1 / (4 * pi_s + 2 * sp.sqrt(3)))
        sympy_note = f"символьная разность форм b: {diff}"
    except Exception as e:  # noqa: BLE001
        sympy_note = f"sympy недоступен: {e}"
    results["sympy"] = {"note": sympy_note}

    out = {"level": "L1", "ok": all_ok, "digits": MP_DIGITS, "results": results}
    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "l1_exact_constants.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"L1: {'PASS' if all_ok else 'FAIL'} — {sum(1 for v in results.values() if isinstance(v, dict) and v.get('ok'))} проверок")
    return all_ok


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
