"""Experiment modules for the NSB research lab.

Each experiment follows the repository output contract:
    banner -> per-assertion [PASS]/[FAIL] -> JSON verdict line
and exposes run(preset, n, t_horizon, nu, dt, lang) -> (exit_code, verdict).
"""
