#!/usr/bin/env python3
"""audit_lean.py — аудит Lean-ядра verification/lean4.

Проверяет фактическое состояние кода (не документацию):

  1. Никаких `sorry` / `admit` в объявлениях (после вырезания комментариев).
  2. Никаких проектных аксиом: `axiom ...` / `postulate ...`.
     Встроенные аксиомы Lean/Mathlib (propext, Quot.sound, Classical.choice,
     sorryAx-запрет) учитываются отдельно — см. Tests/AxiomAudit.lean.
  3. Все импорты модулей Verification.* разрешаются в существующие файлы;
     импорты удалённых направлений (ResearchPapersVerification, Section*,
     AB-Cloud, Riemann) отсутствуют.

Выход: отчёт + JSON-строка + код возврата 0/1.
"""
import json
import re
import sys
from pathlib import Path

LEAN_DIR = Path(__file__).resolve().parents[2] / "lean4"

# Допустимая доверенная база (встроенные аксиомы Lean и стандартные механизмы
# Mathlib). Всё, что сверх этого списка в #print axioms центральных теорем,
# считается проектным допущением.
ALLOWED_AXIOMS = {"propext", "Quot.sound", "Classical.choice", "Lean.ofReduceBool"}

DECL_AXIOM = re.compile(r"^\s*(axiom|postulate)\s+\S", re.M)
STUB = re.compile(r"\b(sorry|admit)\b")
IMPORT = re.compile(r"^import\s+(\S+)", re.M)
IMPORT_PREFIX = re.compile(r"^(Verification|Tests)\.")
FORBIDDEN_IMPORT = re.compile(
    r"ResearchPapersVerification|Section\d|ABCloud|AB_Cloud|Hofstadter|HilbertPolya|Riemann",
    re.I,
)


def strip_comments(text: str) -> str:
    """Вырезает /- ... -/, /-- ... --/ и -- комментарии."""
    out = []
    i, n = 0, len(text)
    while i < n:
        if text.startswith("/-", i):
            depth = 1
            j = i + 2
            while j < n and depth:
                if text.startswith("/-", j):
                    depth += 1
                    j += 2
                elif text.startswith("-/", j):
                    depth -= 1
                    j += 2
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


def module_path(name: str) -> Path | None:
    parts = name.split(".")
    cand = LEAN_DIR.joinpath(*parts)
    for suffix in (".lean",):
        if cand.with_suffix(suffix).is_file():
            return cand.with_suffix(suffix)
    if (cand / "__init__.lean").exists():  # pragma: no cover
        return cand / "__init__.lean"
    dot = LEAN_DIR.joinpath(*parts[:-1], parts[-1] + ".lean")
    if dot.is_file():
        return dot
    return None


def main() -> int:
    findings: list[str] = []
    stats = {"files": 0, "theorems": 0, "defs": 0, "axioms": 0, "sorry": 0, "bad_imports": 0}
    files = sorted(
        f for f in LEAN_DIR.rglob("*.lean")
        if ".lake" not in f.parts
    )
    for f in files:
        rel = f.relative_to(LEAN_DIR).as_posix()
        raw = f.read_text(encoding="utf-8")
        code = strip_comments(raw)
        stats["files"] += 1
        stats["theorems"] += len(
            re.findall(r"^\s*(?:theorem|lemma|corollary)\s+", code, re.M))
        stats["defs"] += len(
            re.findall(r"^\s*(?:def|noncomputable def|abbrev|structure)\s+", code, re.M))
        for m in DECL_AXIOM.finditer(code):
            findings.append(f"{rel}: проектная аксиома: {code[m.start():m.end()].strip()[:60]}")
            stats["axioms"] += 1
        for m in STUB.finditer(code):
            findings.append(f"{rel}: незакрытое доказательство: {m.group(0)!r}")
            stats["sorry"] += 1
        for m in IMPORT.finditer(code):
            name = m.group(1)
            if FORBIDDEN_IMPORT.search(name):
                findings.append(f"{rel}: импорт удалённого направления: {name}")
                stats["bad_imports"] += 1
                continue
            if IMPORT_PREFIX.match(name) and module_path(name) is None:
                findings.append(f"{rel}: импорт не разрешается: {name}")
                stats["bad_imports"] += 1

    print("=== Lean audit (verification/lean4) ===")
    print(f"files={stats['files']} theorems={stats['theorems']} defs={stats['defs']}")
    print(f"project_axioms={stats['axioms']} sorries={stats['sorry']} "
          f"bad_imports={stats['bad_imports']}")
    for line in findings:
        print(f"[FAIL] {line}")
    if not findings:
        print("[PASS] no sorry/admit, no project axioms, all imports resolve")
    print(f"JSON: {json.dumps({'audit': 'lean', **stats, 'ok': not findings})}")
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
