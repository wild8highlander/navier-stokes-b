"""
verify_all.py — полный прогон вычислительного слоя Python.

  python3 verify_all.py              # всё; nse_3d_bkm ~10–20 мин
  NSE3D_SKIP=1 python3 verify_all.py # без 3D-эталона (~1 мин)
  NSE3D_SMALL=1 python3 verify_all.py # 3D в контрольном режиме N=24, T=1

Каждый модуль пишет свой JSON в results/ при каждом запуске.
Численные проверки НЕ заменяют формальные доказательства (../lean4/);
они проверяют численные следствия доказанных теорем и воспроизводимость.
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def main():
    results = {}
    t0 = time.time()

    import exact_constants
    results["exact_constants"] = exact_constants.run()

    import rotation_algebra
    results["rotation_algebra"] = rotation_algebra.run()

    import kirchhoff_vortices
    results["kirchhoff_vortices"] = kirchhoff_vortices.run()

    import nse_2d
    results["nse_2d"] = nse_2d.run()

    if os.environ.get("NSE3D_SKIP"):
        print("nse_3d_bkm: SKIP (NSE3D_SKIP=1)")
        results["nse_3d_bkm"] = None
    else:
        import nse_3d_bkm
        results["nse_3d_bkm"] = nse_3d_bkm.run()

    print("=" * 50)
    for k, v in results.items():
        print(f"  {k}: {'PASS' if v else ('SKIP' if v is None else 'FAIL')}")
    n_fail = sum(1 for v in results.values() if v is False)
    print(f"Итого: {'ВСЕ МОДУЛИ PASS' if n_fail == 0 else f'ПРОВАЛЕНО: {n_fail}'} "
          f"за {time.time() - t0:.0f} c")
    return n_fail == 0


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
