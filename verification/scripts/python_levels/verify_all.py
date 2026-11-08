# -*- coding: utf-8 -*-
"""
verify_all.py — полный прогон многоуровневой Python-верификации L1–L5.

  python3 verify_all.py            # всё, L5 ~10–20 мин
  NSE3D_SKIP=1 python3 verify_all.py   # без 3D-эталона (~1 мин)
  NSE3D_SMALL=1 python3 verify_all.py  # 3D в контрольном режиме N=24, T=1

Каждый уровень пишет свой JSON в results/ при каждом запуске.
"""
import os, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def main():
    results = {}
    t0 = time.time()

    import l1_exact_constants
    results["L1"] = l1_exact_constants.run()

    import l2_rotation_algebra
    results["L2"] = l2_rotation_algebra.run()

    import l3_kirchhoff_vortices
    results["L3"] = l3_kirchhoff_vortices.run()

    import l4_nse_2d
    results["L4"] = l4_nse_2d.run()

    if os.environ.get("NSE3D_SKIP"):
        print("L5: SKIP (NSE3D_SKIP=1)")
        results["L5"] = None
    else:
        import l5_nse_3d_bkm
        results["L5"] = l5_nse_3d_bkm.run()

    print("=" * 50)
    for k, v in results.items():
        print(f"  {k}: {'PASS' if v else ('SKIP' if v is None else 'FAIL')}")
    n_fail = sum(1 for v in results.values() if v is False)
    print(f"Итого: {'ВСЕ УРОВНИ PASS' if n_fail == 0 else f'ПРОВАЛЕНО: {n_fail}'} "
          f"за {time.time() - t0:.0f} c")
    return n_fail == 0


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
