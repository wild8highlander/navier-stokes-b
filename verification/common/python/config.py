"""Section registry for the verification framework (actual tree).

Every entry maps a *suite* to a command that exists in this repository
and follows the shared output contract:

    banner -> per-assertion [PASS]/[FAIL] -> one JSON: {...} verdict line
    exit 0 only if everything passed.

The runner (main.py) executes each command as a subprocess and forwards
its verdict; it never imports the suite code — the suites stay
independently runnable.
"""

from pathlib import Path

VERIFICATION_DIR = Path(__file__).resolve().parents[2]

# Presets are mapped onto the switches the real suites understand.
# "fast"  -> the L-chain without the 3D benchmark (L5), monolith pinned task
# "full"  -> the L-chain with L5 (10-20 min) and the monolith CI preset
PRESETS = {
    "quick":   {"levels_env": {"NSE3D_SKIP": "1"}, "monolith_args": ["--task", "9"]},
    "default": {"levels_env": {"NSE3D_SKIP": "1"}, "monolith_args": ["--ci"]},
    "full":    {"levels_env": {},                  "monolith_args": ["--ci"]},
}

SUITE_COMMANDS = {
    "levels":   ([str(VERIFICATION_DIR / "scripts/python_levels/verify_all.py")], "levels_env"),
    "monolith": ([str(VERIFICATION_DIR / "verify_ns_full.py")], "monolith_args"),
    "code":     ([str(VERIFICATION_DIR / "code/code/exact_constants.py")], None),
    "audit":    ([str(VERIFICATION_DIR / "tools/audit/audit_lean.py")], None),
}

SUITE_NAMES = {
    "levels":   "The L1-L5 reference chain (scripts/python_levels)",
    "monolith": "The self-contained verifier verify_ns_full.py (22 tasks)",
    "code":     "Exact constants at 50 digits (code/code/exact_constants.py)",
    "audit":    "The static Lean-core audit (tools/audit/audit_lean.py)",
}


def get_config(suite="levels", preset="default"):
    """Return (argv, env, display_name) for one suite under one preset."""
    if suite not in SUITE_COMMANDS:
        raise KeyError(f"unknown suite {suite!r} (valid: {sorted(SUITE_COMMANDS)})")
    preset = preset if preset in PRESETS else "default"
    argv, env_key = SUITE_COMMANDS[suite]
    spec = PRESETS[preset]
    if env_key == "monolith_args":
        argv = argv + spec["monolith_args"]
        env = {}
    else:
        env = dict(spec.get(env_key, {}) if env_key else {})
    return argv, env, SUITE_NAMES[suite]
