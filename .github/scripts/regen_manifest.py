#!/usr/bin/env python3
"""Regenerate MANIFEST.json for the current tree (keeps metadata, refreshes files+date)."""
import datetime
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
SKIP_PARTS = {".git", "node_modules", "__pycache__", ".pytest_cache"}


def main() -> int:
    mpath = ROOT / "MANIFEST.json"
    m = json.loads(mpath.read_text(encoding="utf-8"))
    files = {}
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file() or any(part in SKIP_PARTS for part in p.parts):
            continue
        rel = p.relative_to(ROOT).as_posix()
        if rel == "MANIFEST.json":
            continue
        b = p.read_bytes()
        files[rel] = {"sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b)}
    m["files"] = files
    m["date"] = datetime.date.today().isoformat()
    mpath.write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"MANIFEST.json regenerated: {len(files)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
