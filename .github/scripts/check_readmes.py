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
# Generated / local-only directories that never carry READMEs on purpose
# ("results" = verifier run directories, regenerated and git-ignored).
SKIP_PARTS = {
    ".git", "node_modules", "__pycache__", ".pytest_cache", ".ruff_cache",
    ".mypy_cache", ".pytype", ".hypothesis", ".venv", "venv", ".idea",
    ".vscode", ".cache", "dist", "build", "target", "dist-newstyle",
    ".lake", "output", "results",
}


def main() -> int:
    no_readme, cyr = [], []
    for d in sorted(p for p in ROOT.rglob("*") if p.is_dir()):
        if any(part in SKIP_PARTS for part in d.parts):
            continue
        if d == ROOT / ".github" or ".github" in d.parts:
            # GitHub renders a .github/README.md INSTEAD of the project README,
            # so automation directories (root and per-subproject) carry no README
            # on purpose — same rationale as the root exemption.
            continue
        if not any(d.glob("README*")):
            no_readme.append(d.relative_to(ROOT).as_posix() or ".")
    for md in sorted(ROOT.rglob("README*.md")):
        if any(part in SKIP_PARTS for part in md.parts):
            continue
        if re.match(r"README\.(ru|zh)\.md$", md.name):
            # Language-suffixed translations are allowed by policy — the
            # repository ships bilingual artifacts (LICENSE.ru.md, LICENSE.zh.md,
            # research_lab/README.ru.md) and links them from the English primary.
            continue
        text = md.read_text(encoding="utf-8", errors="ignore")
        # Prose check only: strip fenced code blocks (quoted terminal output is
        # evidence, not prose), inline code and link targets (real shipped
        # filenames may be Cyrillic — e.g. monographs/RU/Монография_…_RU.pdf).
        text = re.sub(r"```.*?```", " ", text, flags=re.S)
        text = re.sub(r"`[^`]*`", " ", text)
        text = re.sub(r"\]\([^)]*\)", "](…)", text)
        if CYR.search(text):
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
