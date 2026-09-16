#!/usr/bin/env bash
# push_wild8highlander.sh — идемпотентная отправка navier-stokes-b на GitHub.
# Работает в Linux, macOS и Termux (Android;termux-exec перенаправляет shebang).
#
# Первый запуск:
#   1) создайте ПУСТОЙ репозиторий navier-stokes-b на github.com под аккаунтом
#      wild8highlander (без README / .gitignore / license);
#   2) запустите скрипт — он спросит логин (wild8highlander) и PAT
#      (Personal Access Token, classic, scope repo) и запомнит их
#      (git credential.helper store).
#
# Повторные запуски просто коммитят и пушат изменения.
# Сообщение коммита можно передать аргументом:  ./push_wild8highlander.sh "моя правка"
set -e

GH_USER="wild8highlander"
GH_REPO="navier-stokes-b"
GH_URL="https://github.com/${GH_USER}/${GH_REPO}.git"

# 1) найти корень репозитория (скрипт можно звать из любой точки)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$REPO" ]; then
    echo "ОШИБКА: скрипт лежит вне git-репозитория."
    echo "Выполните в папке navier-stokes-b:  git init && ./push_wild8highlander.sh"
    exit 1
fi
cd "$REPO"
echo "Репозиторий: $REPO"
echo "Удалённый:  $(git remote get-url origin 2>/dev/null || echo 'не задан (настрою)')"

# 2) одноразовая настройка окружения (безопасно повторять)
command -v git >/dev/null || { echo "Установите git: pkg install git (Termux) / apt install git"; exit 1; }
git config credential.helper store || true
# личность коммиттера — только если ещё не задана глобально
git config user.name  >/dev/null 2>&1 || git config user.name  "$GH_USER"
git config user.email >/dev/null 2>&1 || git config user.email "aslan08_05@mail.ru"

# 3) origin → репозиторий wild8highlander/navier-stokes-b
if ! git remote get-url origin >/dev/null 2>&1; then
    git remote add origin "$GH_URL"
    echo "Добавлен origin → $GH_URL"
elif [ "$(git remote get-url origin)" != "$GH_URL" ]; then
    git remote set-url origin "$GH_URL"
    echo "origin обновлён → $GH_URL"
fi

# ветка по умолчанию — main
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
if [ -z "$BRANCH" ] || [ "$BRANCH" = "HEAD" ]; then
    git checkout -b main 2>/dev/null || git checkout main
    BRANCH="main"
fi

# 4) обновиться (offline-безопасно)
git pull --rebase --autostash || echo "  (пропущено: нет сети или нечего тянуть)"

# 5) добавить всё и закоммитить (если есть изменения)
git add -A
if git diff --cached --quiet; then
    echo "Нет изменений — коммит не нужен."
else
    MSG="${1:-navier-stokes-b: обновление программы b-коррекции (данные, статьи, верификация)}"
    git commit -m "$MSG"
fi

# 6) отправка
git push -u origin "$BRANCH" && echo "ОК: отправлено в origin/$BRANCH" || {
    echo "ОШИБКА push. Проверьте:"
    echo "  1) репозиторий ${GH_USER}/${GH_REPO} создан на github.com;"
    echo "  2) PAT (classic, scope repo) действителен;"
    echo "  3) сеть доступна. Повторите: git push (попросит логин/токен заново)."
    exit 1
}

echo "Готово: https://github.com/${GH_USER}/${GH_REPO}"
