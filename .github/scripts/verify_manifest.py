#!/usr/bin/env python3
"""Check sha256 of every file listed in MANIFEST.json (CI-safe, exit 1 on failure)."""
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]  # .github/scripts -> repo root


def main() -> int:
    m = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    files = m.get("files") or {}
    if not files:
        print("MANIFEST.json: no 'files' section found")
        return 1
    bad = missing = 0
    for rel, meta in files.items():
        p = ROOT / rel
        expect = meta if isinstance(meta, str) else (meta.get("sha256") or meta.get("sha256sum"))
        if not p.is_file():
            print("MISSING ", rel)
            missing += 1
            continue
        if hashlib.sha256(p.read_bytes()).hexdigest() != expect:
            print("MISMATCH", rel)
            bad += 1
    print(f"MANIFEST.json: {len(files)} entries, {missing} missing, {bad} mismatched")
    return 1 if (bad or missing) else 0


if __name__ == "__main__":
    sys.exit(main())
