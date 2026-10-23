"""Command-line entry point for the NSB research lab.

Usage (from the repository root):

    python -m research_lab.run_lab --experiment taylor_green --preset smoke
    python -m research_lab.run_lab --experiment abc_blowup_hunt --N 48 --T 3
    python -m research_lab.run_lab --list

Language button: --lang en|ru (or NSB_LAB_LANG). JSON keys stay English.
Exit code 0 = all internal-consistency checks passed.
"""
from __future__ import annotations

import argparse
import sys

from research_lab.experiments import (
    abc_blowup_hunt,
    bcorrection_stress,
    hou_luo_tubes,
    taylor_green,
)
from research_lab.i18n import Lang

EXPERIMENTS = {
    "taylor_green": taylor_green,
    "abc_blowup_hunt": abc_blowup_hunt,
    "hou_luo_tubes": hou_luo_tubes,
    "bcorrection_stress": bcorrection_stress,
}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="research_lab",
        description="Falsification-oriented Navier-Stokes laboratory")
    p.add_argument("--experiment", choices=sorted(EXPERIMENTS),
                   default="taylor_green")
    p.add_argument("--preset", choices=["smoke", "default", "deep"],
                   default="default",
                   help="smoke=CI-fast, default=workstation, deep=long run")
    p.add_argument("--N", type=int, default=None,
                   help="grid points per dimension (overrides preset)")
    p.add_argument("--T", type=float, default=None, help="time horizon")
    p.add_argument("--nu", type=float, default=None, help="kinematic viscosity")
    p.add_argument("--dt", type=float, default=None, help="time step")
    p.add_argument("--lang", choices=["en", "ru"], default=None,
                   help="output language (default: NSB_LAB_LANG or en)")
    p.add_argument("--list", action="store_true", help="list experiments")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.list:
        print("experiments:", ", ".join(sorted(EXPERIMENTS)))
        return 0
    lang = Lang(args.lang)
    module = EXPERIMENTS[args.experiment]
    return module.run(preset=args.preset, n=args.N, t_horizon=args.T,
                      nu=args.nu, dt=args.dt, lang_str=lang.lang)


if __name__ == "__main__":
    sys.exit(main())
