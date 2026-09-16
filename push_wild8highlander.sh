#!/usr/bin/env bash
# push_wild8highlander.sh — idempotent publisher of navier-stokes-b to GitHub.
# Works on Linux, macOS and Termux (Android; termux-exec redirects the shebang).
#
# First run:
#   1) create an EMPTY repository navier-stokes-b on github.com under the
#      wild8highlander account (without README / .gitignore / license);
#   2) run this script — it will ask for the login (wild8highlander) and a PAT
#      (Personal Access Token, classic, scope repo) and remember them
#      (git credential.helper store).
#
# Subsequent runs simply commit and push the changes.
# A commit message can be passed as an argument:  ./push_wild8highlander.sh "my change"
set -e

GH_USER="wild8highlander"
GH_REPO="navier-stokes-b"
GH_URL="https://github.com/${GH_USER}/${GH_REPO}.git"

# 1) locate the repository root (the script may be called from anywhere)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$REPO" ]; then
    echo "ERROR: the script lives outside a git repository."
    echo "Run inside the navier-stokes-b folder:  git init && ./push_wild8highlander.sh"
    exit 1
fi
cd "$REPO"
echo "Repository: $REPO"
echo "Remote:     $(git remote get-url origin 2>/dev/null || echo 'not set (will configure)')"

# 2) one-time environment setup (safe to repeat)
command -v git >/dev/null || { echo "Install git: pkg install git (Termux) / apt install git"; exit 1; }
git config credential.helper store || true
# committer identity — only if not already configured globally
git config user.name  >/dev/null 2>&1 || git config user.name  "$GH_USER"
git config user.email >/dev/null 2>&1 || git config user.email "aslan08_05@mail.ru"

# 3) origin → wild8highlander/navier-stokes-b
if ! git remote get-url origin >/dev/null 2>&1; then
    git remote add origin "$GH_URL"
    echo "Added origin → $GH_URL"
elif [ "$(git remote get-url origin)" != "$GH_URL" ]; then
    git remote set-url origin "$GH_URL"
    echo "origin updated → $GH_URL"
fi

# default branch — main
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
if [ -z "$BRANCH" ] || [ "$BRANCH" = "HEAD" ]; then
    git checkout -b main 2>/dev/null || git checkout main
    BRANCH="main"
fi

# 4) update (offline-safe)
git pull --rebase --autostash || echo "  (skipped: no network or nothing to pull)"

# 5) stage everything and commit (if there are changes)
git add -A
if git diff --cached --quiet; then
    echo "Nothing to commit."
else
    MSG="${1:-navier-stokes-b: update of the b-correction program (data, papers, verification)}"
    git commit -m "$MSG"
fi

# 6) publish
git push -u origin "$BRANCH" && echo "OK: pushed to origin/$BRANCH" || {
    echo "PUSH FAILED. Check that:"
    echo "  1) the repository ${GH_USER}/${GH_REPO} exists on github.com;"
    echo "  2) the PAT (classic, scope repo) is valid;"
    echo "  3) the network is reachable. Then retry: git push (it will ask for login/token again)."
    exit 1
}

echo "Done: https://github.com/${GH_USER}/${GH_REPO}"
