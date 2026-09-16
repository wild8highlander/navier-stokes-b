#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_all.py — run the whole open-problems chain in order, print a summary."""
import subprocess
import sys
import time
import os

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = [
    ("core_b.py", "L1-L3: constant b + universal rotation"),
    ("p1b_droplet_feedback.py", "P1 + P1-b: 3D chamber, feedback vs baseline"),
    ("p2_track_momentum.py", "P2: track momentum (b-beading width)"),
    ("p3_surface_universality.py", "P3: universality on arbitrary surfaces"),
    ("p4_ensemble.py", "P4/P4-b/P4-c: ensemble T=2..32 (~4 min)"),
    ("p5_bprotocol.py", "P5-b + P5-c: b-protocol duplex + K=8"),
    ("p6_taylor_green_bkm.py", "P6: Taylor-Green 3D BKM (~1 min)"),
    ("p7_collider_scale.py", "P7: collider-scale experiments"),
    ("make_figures.py", "figures from results/*.json"),
]


def main():
    t0 = time.time()
    for script, title in STEPS:
        print(f"\n=== [{script}] {title} ===", flush=True)
        r = subprocess.run([sys.executable, os.path.join(HERE, script)])
        if r.returncode != 0:
            print(f"!! {script} FAILED with code {r.returncode}")
            sys.exit(r.returncode)
    print(f"\nAll steps done in {time.time()-t0:.0f} s. Results in ../results, figures in ../figures.")


if __name__ == "__main__":
    main()
