#!/usr/bin/env python3
"""Docs hygiene: every directory must have a README; no Cyrillic in any README.

Note: the top-level .github/ directory is exempt from the README requirement.
GitHub renders .github/README.md on the repository homepage INSTEAD of the
root README.md, so .github/ carries AUTOMATION.md (not a README) on purpose.
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
CYR = re.compile(r"[\u0400-\u04FF]")
# Generated / local-only directories that never carry READMEs on purpose.
SKIP_PARTS = {
    ".git", "node_modules", "__pycache__", ".pytest_cache", ".ruff_cache",
    ".mypy_cache", ".pytype", ".hypothesis", ".venv", "venv", ".idea",
    ".vscode", ".cache", "dist", "build", "target", "dist-newstyle",
    ".lake", "output",
}


def main() -> int:
    no_readme, cyr = [], []
    for d in sorted(p for p in ROOT.rglob("*") if p.is_dir()):
        if any(part in SKIP_PARTS for part in d.parts):
            continue
        if d == ROOT / ".github":
            continue
        if not any(d.glob("README*")):
            no_readme.append(d.relative_to(ROOT).as_posix() or ".")
    for md in sorted(ROOT.rglob("README*.md")):
        if any(part in SKIP_PARTS for part in md.parts):
            continue
        if CYR.search(md.read_text(encoding="utf-8", errors="ignore")):
            cyr.append(md.relative_to(ROOT).as_posix())
    if no_readme:
        print("directories without README:", *("  " + s for s in no_readme), sep="\n")
    if cyr:
        print("READMEs containing Cyrillic:", *("  " + s for s in cyr), sep="\n")
    ok = not (no_readme or cyr)
    if ok:
        print("DOCS HYGIENE: OK")
    else:
        print(f"DOCS HYGIENE: FAIL ({len(no_readme)} dirs, {len(cyr)} cyr)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
