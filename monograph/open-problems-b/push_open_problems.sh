#!/usr/bin/env bash
# ============================================================================
# push_open_problems.sh — публикация папки open-problems в GitHub
# Репозиторий: wild8highlander/research-papers (main)
# Работает в Termux (Android) и в любом POSIX-окружении с git.
#
# Запуск из КОРНЯ репозитория:   bash open-problems/push_open_problems.sh
# Или из любой папки:            bash /путь/к/open-problems/push_open_problems.sh
#
# Первый запуск спросит логин и PAT (classic, scope repo) — один раз,
# дальше git сохранит их через credential.helper store.
# ============================================================================
set -euo pipefail

# --- определить корень репозитория ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

echo ">> Репозиторий: $REPO_DIR"
if [ ! -d ".git" ]; then
  echo "!! Это не git-репозиторий. Сначала: git clone https://github.com/wild8highlander/research-papers.git"
  exit 1
fi

# --- убедиться, что remote настроен ---
if ! git remote get-url origin >/dev/null 2>&1; then
  git remote add origin https://github.com/wild8highlander/research-papers.git
fi

# --- credstore: один раз спросить и запомнить ---
CRED_FILE="$HOME/.git-credentials"
NEED_CRED=1
if [ -f "$CRED_FILE" ] && grep -q "github.com" "$CRED_FILE" 2>/dev/null; then
  NEED_CRED=0
fi
if [ "$NEED_CRED" = "1" ]; then
  git config --global credential.helper store
  echo ">> Настройка доступа GitHub (один раз)."
  echo "   Логин: wild8highlander"
  echo "   Пароль: PAT (classic) с правом repo — https://github.com/settings/tokens"
  git fetch origin 2>/dev/null || {
    echo -n "   Username: "; read -r GH_USER
    echo -n "   Token: "; read -rs GH_TOKEN; echo
    printf 'https://%s:%s@github.com\n' "$GH_USER" "$GH_TOKEN" > "$CRED_FILE"
    chmod 600 "$CRED_FILE"
  }
fi

# --- синхронизация с удалённым ---
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
echo ">> Ветка: $CURRENT_BRANCH"
git fetch origin "$CURRENT_BRANCH" 2>/dev/null || echo ">> remote-ветка ещё не существует — это нормально"
if git rev-parse --verify "origin/$CURRENT_BRANCH" >/dev/null 2>&1; then
  git pull --rebase origin "$CURRENT_BRANCH" || {
    echo "!! Конфликт rebase. Реши вручную: git status / git rebase --continue"
    exit 1
  }
fi

# --- добавить папку open-problems целиком ---
git add open-problems/
if git diff --cached --quiet; then
  echo ">> Нет изменений для коммита — всё уже в репозитории."
else
  git commit -m "open-problems: P5-b (b-протокол в двусторонней связи) + P4-b (ансамбль T=8, Re=2000) — реальные прогоны, JSON, графики, документация"
fi

echo ">> Push в origin/$CURRENT_BRANCH…"
git push origin "$CURRENT_BRANCH"

echo ""
echo ">> ГОТОВО. Папка open-problems опубликована."
echo ">> Проверка: https://github.com/wild8highlander/research-papers/tree/main/open-problems"
