#!/usr/bin/env bash
# ============================================================================
# push_research.sh — идемпотентная отправка новых исследовательских программ
# (research_col_smar + research_webapp_fluid) в репозиторий
# https://github.com/wild8highlander/navier-stokes-b
#
# Работает в Linux, macOS и Termux (Android; termux-exec перенаправляет
# shebang). Безопасно запускать сколько угодно раз.
#
# ЧТО ДЕЛАЕТ:
#   1) проверяет git; если текущая папка ещё не git-репозиторий — делает
#      `git init` (ветка main);
#   2) настраивает личность коммитера (если не задана) и credential.helper;
#   3) настраивает origin на wild8highlander/navier-stokes-b.git;
#   4) подтягивает изменения с сервера (offline-безопасно);
#   5) обновляет MANIFEST.json (если есть python3 и скрипт репозитория);
#   6) добавляет всё, делает коммит (если есть что коммитить) и пушит.
#
# ПЕРВЫЙ ЗАПУСК:
#   1) создайте Personal Access Token (classic, scope repo):
#      GitHub → Settings → Developer settings → Personal access tokens →
#      Tokens (classic) → Generate new token (classic) → scope: repo;
#   2) запустите скрипт: он спросит логин и токен и ЗАПОМНИТ их
#      (git credential.helper store). Пароль от GitHub НЕ подходит.
#
# ПОВТОРНЫЕ ЗАПУСКИ — просто коммитят и пушат:
#   ./push_research.sh                       # сообщение по умолчанию
#   ./push_research.sh "моё сообщение"       # своё сообщение коммита
# ============================================================================
set -e

GH_USER="wild8highlander"
GH_REPO="navier-stokes-b"
GH_URL="https://github.com/${GH_USER}/${GH_REPO}.git"
DEFAULT_MSG="research_col_smar + research_webapp_fluid: Smagorinsky-Kolmogorov constants program (P1-P4, monographs RU/EN, three-language verification, fluid lab web app)"

MSG="${1:-$DEFAULT_MSG}"

# --- 0) git установлен? ------------------------------------------------------
command -v git >/dev/null 2>&1 || {
    echo "ОШИБКА: git не установлен."
    echo "  Termux (Android):  pkg install git -y"
    echo "  Linux:             sudo apt install git"
    echo "  macOS:             brew install git  (или xcode-select --install)"
    exit 1
}

# --- 1) находим корень репозитория; если его нет — создаём -------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$REPO" ]; then
    echo "Папка ещё не git-репозиторий — инициализирую..."
    cd "$SCRIPT_DIR"
    git init -b main >/dev/null 2>&1 || {
        git init >/dev/null
        git checkout -b main >/dev/null 2>&1 || git symbolic-ref HEAD refs/heads/main
    }
    REPO="$SCRIPT_DIR"
fi
cd "$REPO"
echo "Репозиторий: $REPO"
echo "Удалённый:   $(git remote get-url origin 2>/dev/null || echo 'не задан (настрою)')"

# --- 2) одноразовая настройка окружения (безопасно повторять) ---------------
git config credential.helper store || true
git config user.name  >/dev/null 2>&1 || git config user.name  "$GH_USER"
git config user.email >/dev/null 2>&1 || git config user.email "aslan08_05@mail.ru"

# --- 3) origin → репозиторий wild8highlander/navier-stokes-b ----------------
if ! git remote get-url origin >/dev/null 2>&1; then
    git remote add origin "$GH_URL"
    echo "Добавлен origin → $GH_URL"
elif [ "$(git remote get-url origin)" != "$GH_URL" ]; then
    git remote set-url origin "$GH_URL"
    echo "origin обновлён → $GH_URL"
fi

# --- 4) подтягиваем серверное состояние (offline-безопасно) -----------------
if git ls-remote --exit-code origin >/dev/null 2>&1; then
    git pull --rebase --autostash origin main >/dev/null 2>&1 \
        || echo "Предупреждение: не удалось pull (офлайн или конфликт) — продолжаю локально."
else
    echo "Удалённый репозиторий пуст или недоступен — первый пуш создаст main."
fi

# --- 5) перегенерация MANIFEST.json (sha256 всех файлов) --------------------
if command -v python3 >/dev/null 2>&1 && [ -f ".github/scripts/regen_manifest.py" ]; then
    echo "Обновляю MANIFEST.json..."
    python3 .github/scripts/regen_manifest.py >/dev/null 2>&1 \
        || echo "Предупреждение: MANIFEST.json не обновлён (не критично)."
fi

# --- 6) коммит и пуш ---------------------------------------------------------
git add -A
if git diff --cached --quiet; then
    echo "Нет изменений для коммита."
else
    git commit -m "$MSG"
fi

echo "Пушу в $GH_URL (ветка main)..."
if git push -u origin main; then
    echo ""
    echo "ГОТОВО: исследовательские программы отправлены на GitHub."
    echo "  → https://github.com/${GH_USER}/${GH_REPO}"
    echo "  → research_col_smar      (монографии RU/EN, коды Python/C++/Julia, протоколы P1-P4)"
    echo "  → research_webapp_fluid  (веб-приложение симуляции жидкости)"
else
    echo ""
    echo "Пуш не прошёл. Частые причины:"
    echo "  1) нет прав на запись → проверьте токен (scope repo) и логин;"
    echo "  2) на сервере есть чужие коммиты → повторите скрипт (он сделает pull --rebase);"
    echo "  3) нет сети → повторите позже."
    exit 1
fi
