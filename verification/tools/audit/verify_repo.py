#!/usr/bin/env python3
"""verify_repo.py — аудит целостности verification/ по фактическому дереву.

Оркестратор поверх точечных проверок. Запускается командой
`make verify-repo` (в verification/) и завершается кодом 0 только при
полном успехе. Никакого кэша: каждая группа перепроверяется на месте.

  A. СТРУКТУРА      — все компоненты текущей архитектуры на месте:
                      lean4/ (6 модулей + Tests/AxiomAudit + lakefile +
                      lean-toolchain), scripts/{python_levels,julia_levels,
                      julia_lab}, common/python, code/ (P1–P6 + ядро
                      tg2d/chamber3d), монолит verify_ns_full.{py,jl},
                      tests/, tools/audit/.
  B. ДОВЕРЕННАЯ БАЗА — в коде verification/ нет импортов удалённых
                      направлений (ResearchPapersVerification, секции
                      S1–S7 старой раскладки, AB-Cloud, Riemann).
  C. ЯДРО LEAN      — корни lakefile совпадают с файлами; Main.lean
                      totalVerifiedTheorems равен числу `theorem`;
                      Tests/AxiomAudit.lean печатает ≥ 20 баз аксиом;
                      нет sorry/admit/проектных аксиом.
  D. ЧИСЛЕННЫЙ СЛОЙ — python_levels/verify_all.py (NSE3D_SKIP=1) проходит
                      целиком: L1–L4 PASS.
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

CORE_MODULES = ["Foundation.lean", "Basic.lean", "BrakingForm.lean",
                "ProofChain.lean", "Soliton.lean", "KleinQuartic.lean"]
PY_LEVELS = ["verify_all.py", "config.py",
             "l1_exact_constants.py", "l2_rotation_algebra.py",
             "l3_kirchhoff_vortices.py", "l4_nse_2d.py", "l5_nse_3d_bkm.py",
             "results/l1_exact_constants.json", "results/l2_rotation_algebra.json",
             "results/l3_kirchhoff_vortices.json", "results/l4_nse_2d.json",
             "results/l5_nse_3d_bkm.json"]
JL_LEVELS = ["verify_all.jl", "config.jl", "common.jl",
             "l1_exact_constants.jl", "l2_rotation_algebra.jl",
             "l3_kirchhoff_vortices.jl", "l4_nse_2d.jl",
             "l5_nse_3d_bkm.jl", "l7_smagorinsky_kolmogorov.jl"]
CODE_FILES = ["tg2d_core.py", "chamber3d.py", "make_plots.py", "run_all.sh",
              "p1_3d_microphysics.py", "p2_grid_convergence.py",
              "p3_buoyancy.py", "p4_ensemble_sigma_y.py",
              "p5_droplet_feedback.py", "p6_b_universality.py"]

FORBIDDEN = re.compile(
    r"ResearchPapersVerification|section\d_correction|section\d_preprint|"
    r"section\d_ab_cloud|section\d_kdv|section\d_klein|section\d_riemann|"
    r"section\d_smagorinsky|HofstadterHamiltonian|HilbertPolya", re.I)


def group_a_structure():
    required = (
        [f"lean4/{f}" for f in CORE_MODULES]
        + ["lean4/lakefile.lean", "lean4/lean-toolchain", "lean4/Main.lean",
           "lean4/Tests/AxiomAudit.lean", "lean4/README.md"]
        + [f"scripts/python_levels/{f}" for f in PY_LEVELS]
        + [f"scripts/julia_levels/{f}" for f in JL_LEVELS]
        + ["scripts/julia_lab/navier_stokes_lab.jl", "scripts/julia_lab/run.sh",
           "scripts/julia_lab/README.md", "scripts/julia_lab/DOCS_RU.md"]
        + ["common/python/main.py", "common/python/config.py",
           "common/python/verifier_base.py", "common/python/__init__.py"]
        + [f"code/{f}" for f in CODE_FILES]
        + ["verify_ns_full.py", "verify_ns_full.jl", "verify_ns_full_codes.zip",
           "tests/test_lean_core.py", "tests/test_numerical_consistency.py",
           "tools/audit/audit_lean.py", "tools/audit/verify_repo.py"]
        + ["README.md", "Makefile", "CODEOWNERS"]
    )
    missing = [p for p in required if not (VER / p).is_file()]
    present = len(required) - len(missing)
    return not missing, f"components present: {present}/{len(required)}", missing


def group_b_trust_base():
    offenders = []
    for pat in ("*.py", "*.jl", "*.sh"):
        for f in VER.rglob(pat):
            if ".git" in f.parts or "code/verification" in f.relative_to(VER).parts[:2]:
                continue  # исторический снапшот проверяется отдельно, см. README
            text = f.read_text(encoding="utf-8", errors="ignore")
            for m in re.finditer(r"^(?:import|from|include)\s+\S*", text, re.M):
                if FORBIDDEN.search(m.group(0)):
                    offenders.append(f"{f.relative_to(VER)}: {m.group(0)}")
    return not offenders, "no imports of removed directions", offenders


def _strip_lean_comments(text: str) -> str:
    """СкANNER комментариев Lean: блочные /- … -/ (вложенные) и -- до конца строки."""
    out, i, n = [], 0, len(text)
    while i < n:
        if text.startswith("/-", i):
            depth, j = 1, i + 2
            while j < n and depth:
                if text.startswith("/-", j):
                    depth, j = depth + 1, j + 2
                elif text.startswith("-/", j):
                    depth, j = depth - 1, j + 2
                else:
                    j += 1
            i = j
        elif text.startswith("--", i):
            j = text.find("\n", i)
            i = n if j == -1 else j
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def group_c_lean_core():
    problems = []
    lean = VER / "lean4"
    lake = (lean / "lakefile.lean").read_text(encoding="utf-8")
    roots = re.findall(r"roots\s*:=\s*#\[(.*?)\]", lake, re.S)
    if not roots:
        problems.append("lakefile: roots не найдены")
    else:
        declared = re.findall(r"`(\w+)", roots[0])
        for mod in declared:
            if not (lean / f"{mod}.lean").is_file():
                problems.append(f"lakefile: корень {mod} без файла")
    main = (lean / "Main.lean").read_text(encoding="utf-8")
    m = re.search(r"totalVerifiedTheorems\s*:\s*Nat\s*:=\s*(\d+)", main)
    actual = sum(len(re.findall(r"^theorem ", (lean / f).read_text(encoding="utf-8"), re.M))
                 for f in CORE_MODULES)
    if not m or int(m.group(1)) != actual:
        problems.append(f"Main.lean totalVerifiedTheorems={m.group(1) if m else '?'} ≠ {actual}")
    audit = (lean / "Tests/AxiomAudit.lean").read_text(encoding="utf-8")
    n = len(re.findall(r"^#print axioms", audit, re.M))
    if n < 20:
        problems.append(f"AxiomAudit покрывает только {n} теорем")
    for f in lean.rglob("*.lean"):
        if ".lake" in f.parts:
            continue
        text = _strip_lean_comments(f.read_text(encoding="utf-8"))
        if re.search(r"\b(sorry|admit)\b", text):
            problems.append(f"{f.relative_to(lean)}: sorry/admit")
        if re.search(r"^\s*(?:axiom|postulate)\s+\S+", text, re.M):
            problems.append(f"{f.relative_to(lean)}: проектная аксиома")
    return not problems, f"theorems={actual}, axiom-audit prints={n}", problems


def group_d_numerical():
    proc = subprocess.run(
        [sys.executable, str(VER / "scripts/python_levels/verify_all.py")],
        capture_output=True, text=True, timeout=900,
        env={"NSE3D_SKIP": "1", "PATH": "/usr/bin:/bin:/usr/local/bin",
             "PYTHONPATH": ""})
    out = proc.stdout or ""
    levels = re.findall(r"^\s*(L[1-5]): (PASS|FAIL|SKIP)", out, re.M)
    passed = {name for name, verdict in levels if verdict == "PASS"}
    ok = proc.returncode == 0 and {"L1", "L2", "L3", "L4"} <= passed
    detail = ", ".join(f"{n}:{v}" for n, v in levels) or out[-300:]
    return ok, f"python_levels (NSE3D_SKIP=1): {detail}", [] if ok else [detail]


def group_e_makefile():
    text = (VER / "Makefile").read_text(encoding="utf-8")
    offenders = [ln for ln in text.splitlines()
                 if not ln.lstrip().startswith("#")
                 and "|| true" in ln and "$(MAKE)" not in ln]
    return not offenders, "no `|| true` silencing in Makefile", offenders


def main() -> int:
    checks = [
        ("A. Структура", group_a_structure),
        ("B. Доверенная база", group_b_trust_base),
        ("C. Ядро Lean", group_c_lean_core),
        ("D. Численный слой", group_d_numerical),
        ("E. Гигиена Makefile", group_e_makefile),
    ]
    all_ok = True
    for name, fn in checks:
        ok, detail, problems = fn()
        print(f"[{'PASS' if ok else 'FAIL'}] {name}  ({detail})")
        for p in problems[:10]:
            print(f"       - {p}")
        all_ok &= ok
    print("JSON:", json.dumps({
        "audit": "verify_repo", "tree": "verification/",
        "all_passed": bool(all_ok)}))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
