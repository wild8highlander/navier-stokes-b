#!/usr/bin/env python3
"""Тесты ядра: структура, отсутствие заглушек, импорты, доверенная база.

Запускается через `make test` (в verification/) или
`python -m pytest verification/tests/ -v` из корня репозитория.
Тяжёлые проверки (полная сборка Lean) — в `make verify-lean`; здесь
проверяется то, что не требует toolchain, плюс опционально `lake`,
если он установлен.
"""
import re
import shutil
import subprocess
from pathlib import Path

VER = Path(__file__).resolve().parents[1]
LEAN = VER / "lean4"

# Допустимая доверенная база (#print axioms центральных теорем).
ALLOWED_AXIOMS = {"propext", "Quot.sound", "Classical.choice", "Lean.ofReduceBool"}

# Основные модули пакета (входят в lean_lib NsbCore в lakefile.lean).
CORE_MODULES = ["Foundation.lean", "Basic.lean", "BrakingForm.lean",
                "ProofChain.lean", "Soliton.lean", "KleinQuartic.lean"]


def lean_files():
    return sorted(f for f in LEAN.rglob("*.lean") if ".lake" not in f.parts)


def strip_comments(text: str) -> str:
    out = []
    i, n = 0, len(text)
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


# ---------------------------------------------------------------------------
def test_core_structure_present():
    required = CORE_MODULES + [
        "Main.lean", "lakefile.lean", "lean-toolchain", "README.md",
        "Tests/AxiomAudit.lean",
    ]
    missing = [f for f in required if not (LEAN / f).is_file()]
    assert not missing, f"отсутствуют модули ядра: {missing}"


def test_no_history_files():
    history = [p.name for p in LEAN.rglob("*")
               if p.is_file() and re.search(r"_v1\.lean$|_draft\.lean$", p.name)]
    assert not history, f"файлы истории версий в ядре: {history}"


def test_no_sorry_or_admit():
    for f in lean_files():
        code = strip_comments(f.read_text(encoding="utf-8"))
        hits = re.findall(r"\b(sorry|admit)\b", code)
        assert not hits, f"{f.relative_to(LEAN)}: {hits}"


def test_no_project_axioms():
    for f in lean_files():
        code = strip_comments(f.read_text(encoding="utf-8"))
        hits = re.findall(r"^\s*(?:axiom|postulate)\s+\S+.*$", code, re.M)
        assert not hits, f"{f.relative_to(LEAN)}: проектные аксиомы: {hits}"


def test_imports_resolve_and_no_deleted_directions():
    forbidden = re.compile(
        r"ResearchPapersVerification|Section\d_|Hofstadter|HilbertPolya|Riemann", re.I)
    local = {"Foundation", "Basic", "BrakingForm", "ProofChain",
             "Soliton", "KleinQuartic"}
    for f in lean_files():
        for m in re.finditer(r"^import\s+(\S+)", f.read_text(encoding="utf-8"), re.M):
            name = m.group(1)
            assert not forbidden.search(name), f"{f}: импорт удалённого направления {name}"
            if name in local:
                assert (LEAN / f"{name}.lean").is_file(), f"{f}: импорт не разрешается: {name}"


def test_theorem_count_matches_main():
    """totalVerifiedTheorems в Main.lean обязан равняться числу `theorem`
    в шести основных модулях (тот же счёт делает audit_lean.py)."""
    main = (LEAN / "Main.lean").read_text(encoding="utf-8")
    m = re.search(r"totalVerifiedTheorems\s*:\s*Nat\s*:=\s*(\d+)", main)
    assert m, "Main.lean: не найден totalVerifiedTheorems"
    declared = int(m.group(1))
    actual = sum(
        len(re.findall(r"^theorem ", (LEAN / f).read_text(encoding="utf-8"), re.M))
        for f in CORE_MODULES)
    assert declared == actual, f"Main.lean: {declared}, фактически {actual}"


def test_axiom_audit_prints_core_theorems():
    audit = (LEAN / "Tests/AxiomAudit.lean").read_text(encoding="utf-8")
    n = len(re.findall(r"^#print axioms", audit, re.M))
    assert n >= 20, f"AxiomAudit покрывает только {n} теорем"
    for must in ["R_b_det_one", "vort_brakingIter_superpos", "gammaEff_ratio_tendsto",
                 "b_eq_kirchhoff_value", "klein_bridge_implies_nse_regularity"]:
        assert must in audit, f"AxiomAudit не покрывает {must}"


def test_lake_build_axioms_clean():
    """Полная проверка доверенной базы: только если lake установлен."""
    lake = shutil.which("lake")
    if lake is None:
        import pytest
        pytest.skip("lake не установлен — пропускаем сборочную проверку")
    proc = subprocess.run([lake, "env", "lean", "Tests/AxiomAudit.lean"],
                          cwd=LEAN, capture_output=True, text=True, timeout=1800)
    out = proc.stdout + proc.stderr
    assert proc.returncode == 0, f"AxiomAudit не компилируется:\n{out[-2000:]}"
    deps = dict(re.findall(r"'([^']+)' depends on axioms: \[([^]]*)\]", out))
    assert deps, f"#print axioms не дали вывода:\n{out[-1000:]}"
    bad = {k: v for k, v in deps.items()
           if set(x.strip() for x in v.split(",")) - ALLOWED_AXIOMS}
    assert not bad, f"теоремы с недопустимой доверенной базой: {bad}"
