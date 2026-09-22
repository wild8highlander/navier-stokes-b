#!/usr/bin/env python3
"""Regenerate MANIFEST.json for the current tree (keeps metadata, refreshes files+date)."""
import datetime
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
# Cache / build / VCS directories that must never enter MANIFEST.json.
# (.ruff_cache was the 2026-09 CI failure: ruff-created files listed in the
# manifest but absent from any fresh checkout, so verify_manifest.py exited 1.)
SKIP_PARTS = {
    ".git", "node_modules", "__pycache__", ".pytest_cache", ".ruff_cache",
    ".mypy_cache", ".pytype", ".hypothesis", ".venv", "venv", ".idea",
    ".vscode", ".cache", "dist", "build", "target", "dist-newstyle",
    ".lake", "output", "site/node_modules",
}
# Dependency-managed subtrees excluded from the integrity manifest.
# verification/web-dashboard is a Node app whose package.json is updated by
# Dependabot PRs; pinning it into the sha256 manifest broke the
# manifest-integrity job on every dependency PR (2026-09 CI failures #14-#16).
# Integrity checking of hashes is meaningful only for the research artifact
# (data, code, documents, workflows), not for dependency manifests.
SKIP_PREFIXES = (
    "verification/web-dashboard/",
)


def main() -> int:
    mpath = ROOT / "MANIFEST.json"
    m = json.loads(mpath.read_text(encoding="utf-8"))
    files = {}
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file() or any(part in SKIP_PARTS for part in p.parts):
            continue
        rel = p.relative_to(ROOT).as_posix()
        if rel == "MANIFEST.json" or rel.startswith(SKIP_PREFIXES):
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
