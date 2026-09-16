#!/usr/bin/env python3
"""Docs hygiene: every directory must have a README; no Cyrillic in any README."""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
CYR = re.compile(r"[\u0400-\u04FF]")


def main() -> int:
    no_readme, cyr = [], []
    for d in sorted(p for p in ROOT.rglob("*") if p.is_dir()):
        if any(part in {".git", "node_modules", "__pycache__"} for part in d.parts):
            continue
        if not any(d.glob("README*")):
            no_readme.append(d.relative_to(ROOT).as_posix() or ".")
    for md in sorted(ROOT.rglob("README*.md")):
        if any(part in {".git", "node_modules"} for part in md.parts):
            continue
        if CYR.search(md.read_text(encoding="utf-8", errors="ignore")):
            cyr.append(md.relative_to(ROOT).as_posix())
    if no_readme:
        print("directories without README:", *("  " + s for s in no_readme), sep="\n")
    if cyr:
        print("READMEs containing Cyrillic:", *("  " + s for s in cyr), sep="\n")
    ok = not (no_readme or cyr)
    print("DOCS HYGIENE: OK" if ok else f"DOCS HYGIENE: FAIL ({len(no_readme)} dirs, {len(cyr)} cyr)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
