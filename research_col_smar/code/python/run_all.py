"""run_all.py — orchestrator of the Smagorinsky-Kolmogorov program (Python).

Executes P1-P5 and regenerates both figure editions:
    python3 run_all.py          # everything (P4 DNS and P5 DNS take ~25 min)

Optional heavier stages (not in the default set):
    python3 run_all.py p5b      # 96^3 resolution study (~40-60 min)
    python3 run_all.py p5c      # stretching ensembles (~20-40 min)
    python3 run_all.py p5d      # extended ensemble + Q-R topology (~2.5-3 h)
                                #   shardable: p5d dns 0 2 / p5d gausur ...

After P5, run the C++/Julia tracks and the three-language cross-checks:
    cd ../cpp && make run && cd ../../julia && julia p5_regularity.jl ../../
    julia p5c_stretch.jl ../../ && python3 p5_crosscheck.py
    julia p5d_qr.jl ../../ && python3 p5d_crosscheck.py

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
    # heavy optional extensions (not part of the default set)
    "p5b": ["p5b_resolution_96.py"],
    "p5c": ["p5c_stretch_ensemble.py"],
}
DEFAULT = ["p1", "p2", "p3", "p4", "p5"]


def run_p5d(args: list[str]) -> int:
    """P5-D driver: subphases with optional sharding.

    python3 run_all.py p5d                    # all phases, one process
    python3 run_all.py p5d dns 0 2            # dns phase, shard 0 of 2
    python3 run_all.py p5d gausur qr96 protocol
    """
    phases = args[1:] or ["dns", "gausur", "qr96", "protocol"]
    if phases[0] == "dns" and len(phases) >= 3:
        shard, nshards = int(phases[1]), int(phases[2])
        phases = [f"dns --shard {shard} --nshards {nshards}"]
    for ph in phases:
        cmd = [PY, "p5d_qr_ensemble.py"] + ph.split()
        print(f"=== stage p5d: {' '.join(cmd[1:])} ===", flush=True)
        t0 = time.time()
        subprocess.run(cmd, cwd=HERE, check=True)
        print(f"=== stage p5d {ph} done in {time.time() - t0:.1f} s ===", flush=True)
    return 0


def main() -> int:
    wanted = sys.argv[1:] or list(DEFAULT)
    if wanted and wanted[0] == "p5d":
        return run_p5d(wanted)
    for name in wanted:
        if name not in STAGES:
            print(f"unknown stage {name}")
            return 1
        print(f"=== stage {name}: {STAGES[name][0]} ===", flush=True)
        t0 = time.time()
        subprocess.run([PY, STAGES[name][0]], cwd=HERE, check=True)
        print(f"=== stage {name} done in {time.time() - t0:.1f} s ===", flush=True)
    if "figures" in wanted or not sys.argv[1:]:
        for lang in ("ru", "en"):
            subprocess.run([PY, "figures.py", lang], cwd=HERE, check=True)
    elif len(sys.argv) == 1:
        for lang in ("ru", "en"):
            subprocess.run([PY, "figures.py", lang], cwd=HERE, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
