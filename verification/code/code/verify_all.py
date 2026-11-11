"""
verify_all.py — полный прогон вычислительного слоя каталога code/code.

  python3 verify_all.py    # точные константы (mpmath, 50 знаков) + аудит Lean

Состав соответствует фактическому содержимому каталога: константная
цепочка exact_constants.py (13 проверок, JSON в results/) и статический
аудит формального ядра tools/audit/audit_lean.py (72 теоремы, ноль
sorry/проектных аксиом, все импорты разрешаются). Полная цепочка
L1–L5 живёт в scripts/python_levels/ (aggregate: `make verify-common`
или `make verify-levels`); монолит — verify_ns_full.py в корне
verification/.

Численные проверки НЕ заменяют формальные доказательства (../../lean4/);
они проверяют численные следствия доказанных теорем и воспроизводимость.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
VER = HERE.parents[1]
sys.path.insert(0, str(HERE))


def main():
    results = {}
    t0 = time.time()
    print("=== code/code suite: exact constants + Lean audit")

    import exact_constants
    results["exact_constants"] = exact_constants.run()

    proc = subprocess.run(
        [sys.executable, str(VER / "tools/audit/audit_lean.py")],
        capture_output=True, text=True, timeout=300)
    out = proc.stdout or ""
    print(out.rstrip()[-1500:])
    results["lean_audit"] = (proc.returncode == 0
                             and '"ok": true' in out.replace("'", '"'))

    print("=" * 50)
    for k, v in results.items():
        print(f"  {k}: {'PASS' if v else 'FAIL'}")
    n_fail = sum(1 for v in results.values() if v is not True)
    verdict = {"suite": "code_code", "checks": results,
               "all_passed": n_fail == 0,
               "wall_time_s": round(time.time() - t0, 1)}
    print(f"JSON: {json.dumps(verdict)}")
    print(f"Итого: {'ВСЕ МОДУЛИ PASS' if n_fail == 0 else f'ПРОВАЛЕНО: {n_fail}'} "
          f"за {time.time() - t0:.0f} c")
    return n_fail == 0


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
