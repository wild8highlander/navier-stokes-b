#!/data/data/com.termux/files/usr/bin/bash
# push_open_problems.sh — push the open-problems package to GitHub from Termux.
# One-time setup (already done on this device):
#   pkg install git
#   git config --global user.name  "wild8highlander"
#   git config --global user.email "wild8highlander@users.noreply.github.com"
#   git config --global credential.helper store
#   # then one manual push entering login=wild8highlander + PAT classic as password
#
# Usage / Запуск:
#   cd ~/research-papers        # (or the repo clone path)
#   bash open-problems/push_open_problems.sh

set -e
cd "$(dirname "$0")/.."   # repo root (script lives in open-problems/)

echo "== open-problems push =="
if ! git pull --rebase --autostash origin main; then
    echo "ОШИБКА pull — разберитесь вручную"
    exit 1
fi

git add open-problems/
git commit -m "open-problems v2: 7 base problems + P1-b / P4-b / P4-c / P5-b / P5-c — all numbers from real runs 2026-09-16" \
  || echo "(nothing to commit)"
git push origin main

echo "== done. verify: https://github.com/wild8highlander/research-papers/tree/main/open-problems =="
