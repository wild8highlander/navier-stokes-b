"""run_all.py — orchestrator of the Smagorinsky-Kolmogorov program (Python).

Executes P1-P5 and regenerates both figure editions:
    python3 run_all.py          # everything (P4 DNS and P5 DNS take ~25 min)

After P5, run the C++/Julia tracks and the three-language cross-check:
    cd ../cpp && make run && cd ../../julia && julia p5_regularity.jl ../../
    python3 p5_crosscheck.py

Individual stages:
    python3 run_all.py p1 p3 figures
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

STAGES = {
    "p1": ["p1_lilly.py"],
    "p2": ["p2_closures.py"],
    "p3": ["p3_synthetic_apriori.py"],
    "p4": ["p4_dns_les.py"],
    "p5": ["p5_regularity.py"],
}


def main() -> int:
    wanted = sys.argv[1:] or ["p1", "p2", "p3", "p4", "p5"]
    for name in wanted:
        if name not in STAGES:
            print(f"unknown stage {name}")
            return 1
        print(f"=== stage {name}: {STAGES[name][0]} ===", flush=True)
        t0 = time.time()
        subprocess.run([PY, STAGES[name][0]], cwd=HERE, check=True)
        print(f"=== stage {name} done in {time.time() - t0:.1f} s ===", flush=True)
    if "figures" in wanted or not wanted:
        for lang in ("ru", "en"):
            subprocess.run([PY, "figures.py", lang], cwd=HERE, check=True)
    elif len(sys.argv) == 1:
        for lang in ("ru", "en"):
            subprocess.run([PY, "figures.py", lang], cwd=HERE, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
