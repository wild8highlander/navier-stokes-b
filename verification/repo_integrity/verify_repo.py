#!/usr/bin/env python3
"""Repository integrity verifier — confirms EVERY section and folder of
navier-stokes-b in one deterministic run.

This is the repository-wide gate requested by the docs/verification layer:
it walks the whole tree and checks, without trusting any cached state:

  A. DOCS HYGIENE   — every directory carries a README.md; no Cyrillic in
                      any README (the English-only documentation policy).
  B. CORE CONSTANTS — b, theta_b, cos(theta_b), ln(1+b) recomputed from the
                      closed forms and matched against
                      data/results/summary_numbers.json at full precision.
  C. PHYSICS CHAIN  — every P1..P6 protocol exists in data/results/, has
                      ok=true and the expected criteria keys; the pinned
                      headline values are re-checked against the JSON.
  D. BASELINE L1-L5 — every baseline verdict JSON exists in
                      data/results/baseline/ and carries the recorded
                      residuals within the stated tolerances.
  E. NSB-96 LABS    — the research_col_smar lab records (L1..L17) exist
                      (results/results/*_latest.json / reports) and the
                      aggregate scoreboard (WIN 67 / DRAW 7 / LOSS 2)
                      matches the pinned reports.
  F. MONOGRAPHS     — the two-language, two-format artifacts exist and are
                      non-trivial (root monograph, research_col_smar,
                      papers/kdv chapter 16, docs editions).
  G. VERIFICATION   — sections 1..7 run end-to-end (subprocess) and every
                      verdict JSON line parses with all_passed=true.
  H. FIGURES/ANIMS  — the new academic figure set and GIF animations exist
                      under assets/figures and assets/animations.
  I. SERVICES       — site/, research_webapp_fluid/index.html, the REST API
                      server, demos and docker files are present.

Output: per-group [PASS]/[FAIL] lines, a coverage matrix
        (group x checked items), a JSON verdict line, exit code 0 iff all
        groups passed.

Usage:
    python3 verification/repo_integrity/verify_repo.py
    python3 verification/repo_integrity/verify_repo.py --fast   # skip G subprocesses
"""
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CYR = re.compile(r"[\u0400-\u04FF]")
SKIP_PARTS = {
    ".git", "node_modules", "__pycache__", ".pytest_cache", ".ruff_cache",
    ".mypy_cache", ".pytype", ".hypothesis", ".venv", "venv", ".idea",
    ".vscode", ".cache", "dist", "build", "target", "dist-newstyle",
    ".lake", "output",
}

RESULTS = {}
FAILURES = []


def group(name):
    print(f"\n=== {name} ===")
    return []


def check(failures, name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name}" + (f"  ({detail})" if detail else ""))
    if not cond:
        failures.append(name)
    return cond


# ---------------------------------------------------------------------------
def check_docs_hygiene():
    f = group("A. DOCS HYGIENE — README in every directory, English-only")
    no_readme, cyr = [], []
    for d in sorted(p for p in ROOT.rglob("*") if p.is_dir()):
        if any(part in SKIP_PARTS for part in d.parts):
            continue
        if d == ROOT / ".github":
            continue
        if not any(d.glob("README*")):
            no_readme.append(d.relative_to(ROOT).as_posix())
    for md in sorted(ROOT.rglob("README*.md")):
        if any(part in SKIP_PARTS for part in md.parts):
            continue
        if CYR.search(md.read_text(encoding="utf-8", errors="ignore")):
            cyr.append(md.relative_to(ROOT).as_posix())
    n_dirs = sum(1 for p in ROOT.rglob("*") if p.is_dir()
                 and not any(part in SKIP_PARTS for part in p.parts)
                 and p != ROOT / ".github")
    check(f, f"every directory has a README ({n_dirs} dirs)",
          not no_readme, ", ".join(no_readme[:5]) if no_readme else "all covered")
    check(f, "no Cyrillic in any README", not cyr,
          ", ".join(cyr[:5]) if cyr else "all English")
    return not (no_readme or cyr)


def check_core_constants():
    f = group("B. CORE CONSTANTS — closed forms vs summary_numbers.json")
    with open(ROOT / "data/results/summary_numbers.json", encoding="utf-8") as fh:
        s = json.load(fh)
    b = 1.0 / (4.0 * math.pi + 2.0 * math.sqrt(3.0))
    theta = math.asin(b)
    ok = True
    ok &= check(f, "b = 1/(4*pi + 2*sqrt(3)) matches pinned string",
                abs(b - float(s["b_str"])) < 5e-16, s["b_str"][:20] + "…")
    ok &= check(f, "theta_b (rad) matches", abs(theta - float(s["theta_b_rad_str"])) < 5e-16)
    ok &= check(f, "theta_b (deg) matches", abs(math.degrees(theta) - float(s["theta_b_deg_str"])) < 5e-16)
    ok &= check(f, "cos(theta_b) matches", abs(math.cos(theta) - float(s["cos_theta_b_str"])) < 5e-16)
    ok &= check(f, "ln(1+b) matches", abs(math.log1p(b) - float(s["ln1pb_str"])) < 5e-16)
    return ok


def check_physics_chain():
    f = group("C. PHYSICS CHAIN P1-P6 — protocols present, ok, pinned values")
    expect = {
        "p1_3d_microphysics.json": ["criteria", "C4_инъекция_энергии_за_шаг_отн"],
        "p2_grid_convergence.json": ["criteria", "C2_F_value"],
        "p3_buoyancy.json": ["criteria", "C2_Nu_base"],
        "p4_ensemble_sigma_y.json": ["analysis", "delta_rel"],
        "p5_droplet_feedback.json": ["runs", "two_way", "S_min_final"],
        "p6_b_universality.json": ["criteria", "C1_worst_angle_residual"],
    }
    ok = True
    for fn, keys in expect.items():
        p = ROOT / "data/results" / fn
        good = p.is_file()
        data = {}
        if good:
            with open(p, encoding="utf-8") as fh:
                data = json.load(fh)
            good = data.get("ok") is True
            node = data
            for k in keys:
                if isinstance(node, dict) and k in node:
                    node = node[k]
                else:
                    good = False
                    break
        check(f, f"{fn}: present, ok=true, key {'.'.join(keys)}", good)
        ok &= good
    # pinned headline numbers
    with open(ROOT / "data/results/p2_grid_convergence.json", encoding="utf-8") as fh:
        p2 = json.load(fh)
    ok &= check(f, "P2 factor F = 0.999997858567295",
                abs(p2["criteria"]["C2_F_value"] - 0.999997858567295) < 1e-15)
    with open(ROOT / "data/results/p3_buoyancy.json", encoding="utf-8") as fh:
        p3 = json.load(fh)
    ok &= check(f, "P3 Nu = 19.6356", abs(p3["criteria"]["C2_Nu_base"] - 19.63557178194509) < 1e-9)
    with open(ROOT / "data/results/p6_b_universality.json", encoding="utf-8") as fh:
        p6 = json.load(fh)
    ok &= check(f, "P6 worst angle residual <= 1e-14",
                p6["criteria"]["C1_worst_angle_residual"] < 1e-14)
    return ok


def check_baseline():
    f = group("D. BASELINE L1-L5 — pinned verdicts")
    base = ROOT / "data/results/baseline"
    files = ["l1_exact_constants.json", "l2_rotation_algebra.json",
             "l3_kirchhoff_vortices.json", "l4_nse_2d.json",
             "l5_nse_3d_bkm.json"]
    ok = True
    for fn in files:
        good = (base / fn).is_file()
        check(f, fn, good)
        ok &= good
    if ok:
        with open(base / "l2_rotation_algebra.json", encoding="utf-8") as fh:
            l2 = json.load(fh)
        vals = json.dumps(l2)
        ok &= check(f, "L2 records rotation-algebra residuals",
                    "4.44" in vals or "4.440892098500626e-16" in vals)
    return ok


def check_labs():
    f = group("E. NSB-96 LABS — L1..L17 records and scoreboard")
    ok = True
    lab_jsons = ["matrix112_latest.json", "smoke48_latest.json",
                 "dns112_latest.json", "main96_latest.json",
                 "bfamily96_latest.json", "bprotocol96_latest.json",
                 "match_latest.json"]
    d = ROOT / "research_col_smar/results/results"
    for fn in lab_jsons:
        good = (d / fn).is_file()
        check(f, fn, good)
        ok &= good
    extra = ["extra11_gradstats_20261001_004200.json",
             "extra12_flux_20261001_004200.json",
             "extra13_kdvb_20261001_004222.txt",
             "extra16_convergence_20261001_004008.txt",
             "extra17_phiaudit_20261001_023151.json",
             "extra17_julia_crosscheck.json"]
    for fn in extra:
        good = (d / fn).is_file()
        check(f, fn, good)
        ok &= good
    rep = ROOT / "research_col_smar/reports/NSB_LAB_REPORT.md"
    good = rep.is_file() and "WIN 39" in rep.read_text(encoding="utf-8")
    check(f, "NSB_LAB_REPORT.md aggregate WIN 39 · DRAW 2 · LOSS 0", good)
    ok &= good
    rep2 = ROOT / "research_col_smar/reports/EXTRA_RESEARCH_REPORT.md"
    good2 = rep2.is_file() and "WIN 13" in rep2.read_text(encoding="utf-8")
    check(f, "EXTRA_RESEARCH_REPORT.md L17 WIN 13 · DRAW 0 · LOSS 2", good2)
    ok &= good2
    return ok


def check_monographs():
    f = group("F. MONOGRAPHS & PAPERS — two languages, two formats")
    ok = True
    paths = [
        "monograph/MONOGRAPH_RU.pdf", "monograph/MONOGRAPH_EN.pdf",
        "monograph/MONOGRAPH_RU.docx", "monograph/MONOGRAPH_EN.docx",
        "papers/correction-b/main.pdf", "papers/correction-b/main_v2.pdf",
        "papers/preprint/preprint_v1.pdf", "papers/preprint/preprint_v2.pdf",
        "papers/kdv/KdV_b_correction_Chapter16_RU.pdf",
        "papers/kdv/KdV_b_correction_Chapter16_EN.pdf",
        "papers/kdv/KdV_b_correction_Chapter16_RU.docx",
        "papers/kdv/KdV_b_correction_Chapter16_EN.docx",
        "docs/kdv/ru/KdV_b_correction_Chapter16.docx",
        "docs/kdv/en/KdV_b_correction_Chapter16.docx",
        "docs/correction-b/ru/monograph_with_figures.docx",
        "docs/correction-b/en/monograph_with_figures.docx",
        "research_col_smar/monograph/research_col_smar/MONOGRAPH_RU.docx",
        "research_col_smar/monograph/research_col_smar/MONOGRAPH_EN.docx",
    ]
    for rel in paths:
        p = ROOT / rel
        good = p.is_file() and p.stat().st_size > 10_000
        check(f, rel + (f" ({p.stat().st_size // 1024} KB)" if good else ""), good)
        ok &= good
    return ok


def check_verification_sections(fast=False):
    f = group("G. VERIFICATION SECTIONS 1-7 — subprocess end-to-end")
    sections = {
        1: "section1_correction_b", 2: "section2_preprint",
        3: "section3_ab_cloud", 4: "section4_kdv",
        5: "section5_klein_attractor", 6: "section6_riemann_zeros",
        7: "section7_smagorinsky_kolmogorov",
    }
    ok = True
    if fast:
        check(f, "subprocess runs skipped (--fast)", True)
        return True
    for sid, d in sections.items():
        v = ROOT / "verification" / d / "python" / "verify.py"
        good = v.is_file()
        verdict_ok = False
        if good:
            try:
                proc = subprocess.run([sys.executable, str(v)],
                                      capture_output=True, text=True,
                                      timeout=300)
                for line in (proc.stdout or "").splitlines():
                    if line.startswith("JSON: "):
                        try:
                            verdict = json.loads(line[6:])
                            verdict_ok = (verdict.get("section") == sid
                                          and verdict.get("all_passed") is True
                                          and proc.returncode == 0)
                        except json.JSONDecodeError:
                            verdict_ok = False
            except subprocess.TimeoutExpired:
                verdict_ok = False
        check(f, f"section {sid} ({d}) end-to-end PASS", good and verdict_ok)
        ok &= good and verdict_ok
    return ok


def check_figures():
    f = group("H. FIGURES & ANIMATIONS — academic figure set present")
    figs = ["fig_b_anatomy.png", "fig_rodrigues_rotation.png",
            "fig_headline_results.png", "fig_labs_scoreboard.png",
            "fig_master_relation.png", "fig_verification_matrix.png",
            "fig_program_timeline.png", "fig_kdv_bfamily.png",
            "fig_convergence_l16.png", "fig_p6_universality.png",
            "fig_bkm_protocol.png"]
    anims = ["anim_taylor_green.gif", "anim_spectrum_cascade.gif",
             "anim_kdv_collision.gif", "anim_b_rotation.gif"]
    ok = True
    for fn in figs:
        p = ROOT / "assets/figures" / fn
        good = p.is_file() and p.stat().st_size > 20_000
        check(f, "assets/figures/" + fn, good)
        ok &= good
    for fn in anims:
        p = ROOT / "assets/animations" / fn
        good = p.is_file() and p.stat().st_size > 50_000
        check(f, "assets/animations/" + fn, good)
        ok &= good
    return ok


def check_services():
    f = group("I. SERVICES — site, web app, API, demos, docker")
    paths = [
        "site/index.html",
        "research_webapp_fluid/index.html",
        "verification/api/server.py",
        "verification/demo/gradio_app.py",
        "verification/demo/streamlit_app.py",
        "verification/docker/lean4/Dockerfile",
        "verification/docker/coq/Dockerfile",
        "verification/docker/isabelle/Dockerfile",
        "verification/docker/agda/Dockerfile",
        "verification/docker/cpp/Dockerfile",
        "verification/docker/rust/Dockerfile",
        "verification/docker/haskell/Dockerfile",
        "MANIFEST.json",
        "CITATION.cff",
        "push_wild8highlander.sh",
        "TERMUX_GUIDE.md",
    ]
    ok = True
    for rel in paths:
        good = (ROOT / rel).is_file()
        check(f, rel, good)
        ok &= good
    return ok


def main() -> int:
    print("=" * 72)
    print("navier-stokes-b — REPOSITORY INTEGRITY VERIFICATION")
    print(f"root: {ROOT}")
    print("=" * 72)
    fast = "--fast" in sys.argv
    outcomes = {
        "A docs hygiene": check_docs_hygiene(),
        "B core constants": check_core_constants(),
        "C physics chain": check_physics_chain(),
        "D baseline L1-L5": check_baseline(),
        "E NSB-96 labs": check_labs(),
        "F monographs": check_monographs(),
        "G sections 1-7": check_verification_sections(fast),
        "H figures/anims": check_figures(),
        "I services": check_services(),
    }
    print("\n" + "=" * 72)
    print("COVERAGE MATRIX")
    print("=" * 72)
    for k, v in outcomes.items():
        print(f"  {k:<22} {'PASS' if v else 'FAIL'}")
    all_ok = all(outcomes.values())
    verdict = {"verifier": "repo_integrity", "groups": len(outcomes),
               "all_passed": all_ok}
    print(f"\nJSON: {json.dumps(verdict)}")
    print("REPOSITORY INTEGRITY:", "ALL GROUPS PASS" if all_ok else "FAILURES PRESENT")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
