#!/usr/bin/env python3
"""verify_repo.py — проверка целостности verification/ под новую архитектуру.

Проверяет (без доверия к кэшированному состоянию):

  A. СТРУКТУРА   — lean4/ (ядро), numerical/ (python, julia, experiments,
                   results), tests/, tools/audit присутствуют; старые
                   направления (agda, coq, isabelle, cpp, rust, haskell,
                   api, demo, docker, notebooks, section_*, python_levels,
                   julia_levels, common, repo_integrity) удалены.
  B. ДОВЕРЕННАЯ БАЗА — в коде verification/ нет упоминаний удалённых
                   направлений (AB-Cloud, Riemann, секции S1–S7) как
                   действующих модулей.
  C. ЯДРО LEAN   — lakefile, lean-toolchain, Verification.lean, все модули
                   новой архитектуры, Tests/AxiomAudit.lean на месте;
                   в lean4 нет history-файлов (*_v1, draft).
  D. ЧИСЛЕННЫЙ СЛОЙ — stdlib-модули numerical/python запускаются и печатают
                   корректный JSON-вердикт (тяжёлый 3D-эталон не запускается).
  E. ЗАПРЕТ `|| true` — Makefile не глушит коды возврата.

Выход: [PASS]/[FAIL] по группам, JSON-вердикт, exit 0 только при полном
успехе.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

VER = Path(__file__).resolve().parents[2]
FAILS: list[str] = []

REQUIRED_DIRS = [
    "lean4/Verification/Constants",
    "lean4/Verification/LinearAlgebra",
    "lean4/Verification/Fourier",
    "lean4/Verification/Vorticity",
    "lean4/Verification/Analysis",
    "lean4/Verification/PDE",
    "lean4/Verification/Geometry",
    "lean4/Verification/Turbulence",
    "lean4/Tests",
    "numerical/python/results",
    "numerical/julia",
    "numerical/experiments",
    "tests",
    "tools/audit",
]

REQUIRED_FILES = [
    "lean4/Verification.lean",
    "lean4/Main.lean",
    "lean4/lakefile.lean",
    "lean4/lean-toolchain",
    "lean4/README.md",
    "lean4/OPEN_PROBLEMS.md",
    "lean4/Tests/AxiomAudit.lean",
    "lean4/Verification/Constants/BCorrection.lean",
    "lean4/Verification/LinearAlgebra/Rodrigues.lean",
    "lean4/Verification/Fourier/LerayProjection.lean",
    "lean4/Verification/Vorticity/BrakingProtocol.lean",
    "lean4/Verification/Analysis/EffectiveDamping.lean",
    "lean4/Verification/PDE/NavierStokes.lean",
    "lean4/Verification/PDE/KdV.lean",
    "lean4/Verification/Geometry/KleinGeometry.lean",
    "lean4/Verification/Turbulence/SmagorinskyKolmogorov.lean",
    "numerical/python/exact_constants.py",
    "numerical/python/rotation_algebra.py",
    "numerical/python/kirchhoff_vortices.py",
    "numerical/python/nse_2d.py",
    "numerical/python/kdv_soliton.py",
    "numerical/python/klein_dynamics.py",
    "numerical/python/preprint_chain.py",
    "numerical/python/smagorinsky_kolmogorov.py",
    "numerical/python/verify_all.py",
    "numerical/julia/verify_all.jl",
    "tools/audit/audit_lean.py",
    "Makefile",
    "README.md",
    "OPEN_PROBLEMS.md",
]

FORBIDDEN_DIRS = [
    "agda", "coq", "isabelle", "cpp", "rust", "haskell", "api", "demo",
    "docker", "notebooks", "common", "repo_integrity", "scripts",
    "python_levels", "julia_levels",
]
FORBIDDEN_PREFIX = "section_"

# Упоминания удалённых направлений как действующих частей системы —
# в исполняемом коде (исторические пометки в документации не проверяются).
CODE_SUFFIXES = {".py", ".lean", ".jl", ".sh"}
FORBIDDEN_CODE = re.compile(
    r"ab[_-]?cloud|hofstadter|hilbert[_-]?polya|riemann|section\d"
    r"|Section[1-7]_|section[1-7]_|totalVerifiedTheorems",
    re.IGNORECASE,
)  # noqa: E501

HISTORY_FILE = re.compile(r"_v1\.lean$|_v1$|.*_draft\.lean$")


def check(group: str, name: str, cond: bool, detail: str = "") -> bool:
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))
    if not cond:
        FAILS.append(f"{group}:{name}")
    return cond


def check_structure() -> None:
    print("\n=== A. СТРУКТУРА ===")
    missing = [d for d in REQUIRED_DIRS if not (VER / d).is_dir()]
    check("A", f"все каталоги новой архитектуры ({len(REQUIRED_DIRS)})", not missing,
          ", ".join(missing) if missing else "ok")
    missing = [f for f in REQUIRED_FILES if not (VER / f).is_file()]
    check("A", f"все файлы новой архитектуры ({len(REQUIRED_FILES)})", not missing,
          ", ".join(missing[:5]) if missing else "ok")
    stale = [d for d in FORBIDDEN_DIRS if (VER / d).exists()]
    stale += [p.name for p in VER.iterdir() if p.is_dir() and p.name.startswith(FORBIDDEN_PREFIX)]
    check("A", "старые направления удалены", not stale, ", ".join(stale) if stale else "ok")


def check_no_deleted_directions() -> None:
    print("\n=== B. УДАЛЁННЫЕ НАПРАВЛЕНИЯ ===")
    hits = []
    for p in VER.rglob("*"):
        if p.suffix in CODE_SUFFIXES and p.is_file():
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if FORBIDDEN_CODE.search(line):
                    hits.append(f"{p.relative_to(VER)}:{i}: {line.strip()[:70]}")
    check("B", "код не ссылается на AB-Cloud/Riemann/секции S1–S7", not hits,
          "; ".join(hits[:4]) if hits else "ok")


def check_lean_core() -> None:
    print("\n=== C. ЯДРО LEAN ===")
    history = [p.name for p in VER.rglob("*")
               if p.is_file() and HISTORY_FILE.search(p.name)]
    check("C", "нет файлов истории версий (*_v1, *_draft)", not history,
          ", ".join(history) if history else "ok")
    toolchain = (VER / "lean4/lean-toolchain").read_text().strip()
    check("C", "lean-toolchain закреплён", toolchain == "leanprover/lean4:v4.14.0", toolchain)
    lakefile = (VER / "lean4/lakefile.lean").read_text()
    check("C", "lakefile требует mathlib v4.14.0",
          '@ "v4.14.0"' in lakefile and "lean_lib Verification" in lakefile)
    audit = (VER / "lean4/Tests/AxiomAudit.lean").read_text()
    n_axiom_checks = audit.count("#print axioms")
    check("C", "AxiomAudit печатает аксиомы центральных теорем",
          n_axiom_checks >= 20, f"{n_axiom_checks} команд")


def check_numerical_smoke() -> None:
    print("\n=== D. ЧИСЛЕННЫЙ СЛОЙ (smoke) ===")
    stdlib_modules = [
        "numerical/python/kdv_soliton.py",
        "numerical/python/klein_dynamics.py",
        "numerical/python/preprint_chain.py",
        "numerical/python/smagorinsky_kolmogorov.py",
    ]
    for mod in stdlib_modules:
        try:
            proc = subprocess.run([sys.executable, str(VER / mod)],
                                  capture_output=True, text=True, timeout=300)
            out = proc.stdout or ""
            ok = proc.returncode == 0 and "FAIL" not in out and "JSON: " in out
            check("D", f"{Path(mod).name}", ok,
                  f"exit={proc.returncode}" + ("" if ok else out[-120:]))
        except subprocess.TimeoutExpired:
            check("D", f"{Path(mod).name}", False, "timeout")


def check_makefile() -> None:
    print("\n=== E. MAKEFILE ===")
    mk = (VER / "Makefile").read_text()
    check("E", "нет `|| true` (ошибки не глушатся)", "|| true" not in mk)
    check("E", "цель verify-lean собирает ядро", "verify-lean" in mk and "lake" in mk)


def main() -> int:
    print("=== verify_repo: целостность verification/ ===")
    check_structure()
    check_no_deleted_directions()
    check_lean_core()
    if "--fast" not in sys.argv:
        check_numerical_smoke()
    else:
        print("\n=== D. ЧИСЛЕННЫЙ СЛОЙ (smoke) — пропущен (--fast) ===")
    check_makefile()
    ok = not FAILS
    print("\n=== ИТОГ ===")
    verdict = "PASS — все группы пройдены" if ok else f"FAIL — {len(FAILS)} проверок"
    print("VERIFICATION: " + verdict)
    for f in FAILS:
        print(f"  - {f}")
    print(f"JSON: {json.dumps({'verifier': 'verify_repo', 'ok': ok, 'failures': FAILS})}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
