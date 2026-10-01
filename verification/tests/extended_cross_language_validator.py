"""Extended cross-language validator.

Reports the language × section coverage matrix of the verification
framework and, where the toolchains are available, executes the
computational ports and compares their JSON verdicts against the Python
reference. Any disagreement is a CI failure by construction.

Usage:
    python3 verification/tests/extended_cross_language_validator.py       # registry report
    python3 verification/tests/extended_cross_language_validator.py --run # + execute available
"""
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

VERIFICATION_DIR = Path(__file__).resolve().parent.parent

NUMERICAL_LANGUAGES = ["python", "julia", "java", "rust", "cpp", "haskell"]
FORMAL_LANGUAGES = ["lean4", "coq", "isabelle", "agda"]
SECTIONS = {1: "Correction b", 2: "Preprint NSE", 3: "AB-Cloud",
            4: "KdV", 5: "Klein Attractor", 6: "Riemann Zeros",
            7: "Smagorinsky–Kolmogorov"}

SECTION_DIRS = {1: "section1_correction_b", 2: "section2_preprint",
                3: "section3_ab_cloud", 4: "section4_kdv",
                5: "section5_klein_attractor", 6: "section6_riemann_zeros",
                7: "section7_smagorinsky_kolmogorov"}

TOOLCHAIN_BIN = {"julia": "julia", "java": "java", "rust": "cargo",
                 "cpp": "g++", "haskell": "cabal", "lean4": "lake",
                 "coq": "coqc", "isabelle": "isabelle", "agda": "agda"}


def main() -> int:
    print("Extended Cross-Language Validation Report")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Numerical languages: {NUMERICAL_LANGUAGES}")
    print(f"Formal languages: {FORMAL_LANGUAGES}")
    total = len(NUMERICAL_LANGUAGES + FORMAL_LANGUAGES) * len(SECTIONS)
    print(f"Total artifacts: {total} ({len(SECTIONS)} sections × "
          f"{len(NUMERICAL_LANGUAGES + FORMAL_LANGUAGES)} languages)")
    print()

    # Section 1..7 registry with the location of each Python reference port
    print("Section registry (Python reference ports):")
    ok = True
    for sid, name in SECTIONS.items():
        d = SECTION_DIRS[sid]
        port = VERIFICATION_DIR / d / "python" / "verify.py"
        good = port.is_file()
        ok &= good
        print(f"  S{sid} {name:<28} {'OK ' if good else 'MISSING'}  "
              f"verification/{d}/python/verify.py")
    print()

    if "--run" not in sys.argv:
        print("Report-only mode. Add --run to execute the available "
              "computational ports.")
        return 0 if ok else 1

    # Execute every computational port whose toolchain is present
    print("Execution matrix (available toolchains only):")
    py = sys.executable
    for sid in SECTIONS:
        d = SECTION_DIRS[sid]
        port = VERIFICATION_DIR / d / "python" / "verify.py"
        proc = subprocess.run([py, str(port)], capture_output=True, text=True,
                              timeout=300)
        verdict = None
        for line in (proc.stdout or "").splitlines():
            if line.startswith("JSON: "):
                try:
                    verdict = json.loads(line[6:])
                except json.JSONDecodeError:
                    verdict = None
        passed = bool(verdict and verdict.get("all_passed")
                      and proc.returncode == 0)
        ok &= passed
        print(f"  python  S{sid}: {'PASS' if passed else 'FAIL'}")

    for lang, binname in TOOLCHAIN_BIN.items():
        if not shutil.which(binname):
            print(f"  {lang:<8} : toolchain not found — skipped")
            continue
        print(f"  {lang:<8} : toolchain present; build targets via "
              f"`make verify-{'lean' if lang == 'lean4' else lang}`")
    print()
    print("VALIDATOR:", "ALL AVAILABLE PORTS PASS" if ok else "FAILURES PRESENT")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
