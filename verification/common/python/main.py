"""Main entry point for the Python verification aggregate.

Runs the per-section reference verifier (verification/sectionN_*/python/verify.py)
as a subprocess and enforces the repository-wide output contract:

    banner -> per-assertion [PASS]/[FAIL] -> JSON: {...} verdict line
    exit 0 only if every assertion of the section passed.

Usage:
    python main.py --section 1 --preset default
    python main.py --all              # run every section 1..6
"""
import json
import subprocess
import sys
from pathlib import Path

COMMON_DIR = Path(__file__).parent
VERIFICATION_DIR = COMMON_DIR.parent.parent

SECTION_DIRS = {
    1: "section1_correction_b",
    2: "section2_preprint",
    3: "section3_ab_cloud",
    4: "section4_kdv",
    5: "section5_klein_attractor",
    6: "section6_riemann_zeros",
}

try:
    from config import SECTION_NAMES  # section display names
except ImportError:  # fallback when run from another working directory
    sys.path.insert(0, str(COMMON_DIR))
    from config import SECTION_NAMES


def run_section(section: int, preset: str) -> bool:
    """Run one section verifier; return True iff it passed."""
    print(f"Section {section}: {SECTION_NAMES.get(section, 'Unknown')}")
    print(f"Preset: {preset}")

    verifier = (VERIFICATION_DIR / SECTION_DIRS[section] / "python" / "verify.py").resolve()
    if not verifier.is_file():
        print(f"[FAIL] verifier not found: {verifier.relative_to(VERIFICATION_DIR)}")
        print(json.dumps({"section": section, "language": "python",
                          "values": {}, "all_passed": False}))
        return False

    proc = subprocess.run(
        [sys.executable, str(verifier), "--preset", preset],
        capture_output=True, text=True,
    )
    out = proc.stdout or ""
    if out:
        print(out.rstrip())
    if proc.returncode != 0 and proc.stderr:
        print(proc.stderr.rstrip())

    passed = proc.returncode == 0 and "FAIL" not in out
    # forward the verifier's own JSON verdict line; synthesise one if absent
    json_lines = [ln for ln in out.splitlines() if ln.startswith("JSON: ")]
    if not json_lines:
        verdict = {"section": section, "language": "python",
                   "values": {}, "all_passed": passed}
        print(f"JSON: {json.dumps(verdict)}")
    return passed


def main() -> int:
    argv = sys.argv[1:]
    sections = list(SECTION_DIRS)
    if "--section" in argv:
        section = int(argv[argv.index("--section") + 1])
        if section not in SECTION_DIRS:
            print(f"ERROR: unknown section {section} (valid: 1..6)")
            return 2
        sections = [section]
    preset = argv[argv.index("--preset") + 1] if "--preset" in argv else "default"

    ok = all(run_section(s, preset) for s in sections)
    if not ok:
        print("VERIFICATION: FAILED")
        return 1
    print("VERIFICATION: all assertions passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
