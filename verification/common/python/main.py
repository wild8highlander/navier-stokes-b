"""Main entry point of the verification aggregate.

Runs a verification suite as a subprocess and enforces the
repository-wide output contract:

    banner -> per-assertion [PASS]/[FAIL] -> JSON: {...} verdict line
    exit 0 only if every assertion of the suite passed.

The runner never imports suite code — every suite is executed as a
subprocess so that a crash, a hang or a broken interpreter is a verdict,
not an exception inside the runner.

Usage:
    python main.py --suite levels --preset default
    python main.py --all                      # every suite, quick preset
    python main.py --list                     # suite registry as TSV
"""
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import SUITE_NAMES, get_config  # noqa: E402


def run_suite(suite: str, preset: str) -> bool:
    """Run one suite; return True iff it passed under the contract."""
    argv, env, name = get_config(suite, preset)
    print(f"=== {suite}: {name}")
    print(f"preset: {preset}")
    proc_env = dict(os.environ)
    proc_env.update(env)
    try:
        proc = subprocess.run(
            [sys.executable, *argv], capture_output=True, text=True,
            env=proc_env, timeout=3600)
    except subprocess.TimeoutExpired:
        print("[FAIL] suite timed out")
        print(json.dumps({"suite": suite, "all_passed": False}))
        return False
    out = proc.stdout or ""
    if out:
        print(out.rstrip())
    if proc.returncode != 0 and proc.stderr:
        print(proc.stderr.rstrip()[-2000:])

    passed = proc.returncode == 0 and "FAIL" not in out
    if not any(ln.startswith("JSON: ") for ln in out.splitlines()):
        print(f"JSON: {json.dumps({'suite': suite, 'all_passed': passed})}")
    return passed


def main() -> int:
    argv = sys.argv[1:]
    if "--list" in argv:
        for key, name in SUITE_NAMES.items():
            print(f"{key}\t{name}")
        return 0

    suites = list(SUITE_NAMES)
    if "--suite" in argv:
        idx = argv.index("--suite") + 1
        if idx >= len(argv):
            print("ERROR: --suite expects a value")
            return 2
        suites = argv[idx].split(",")
        unknown = [s for s in suites if s not in SUITE_NAMES]
        if unknown:
            print(f"ERROR: unknown suite(s) {unknown} (valid: {sorted(SUITE_NAMES)})")
            return 2
    preset = argv[argv.index("--preset") + 1] if "--preset" in argv else "default"
    if "--all" in argv:
        preset = "quick"

    results = {}
    for suite in suites:
        results[suite] = run_suite(suite, preset)

    verdict = {"suites": results, "preset": preset,
               "all_passed": all(results.values())}
    print(f"JSON: {json.dumps(verdict)}")
    if not verdict["all_passed"]:
        print("VERIFICATION: FAILED")
        return 1
    print("VERIFICATION: all assertions passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
