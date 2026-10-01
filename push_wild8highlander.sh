#!/usr/bin/env bash
# ============================================================================
# push_wild8highlander.sh — идемпотентная отправка navier-stokes-b на GitHub.
# Работает в Linux, macOS и Termux (Android; termux-exec перенаправляет shebang).
#
# ЧТО ДЕЛАЕТ (безопасно запускать сколько угодно раз):
#   1) проверяет git и, если папка ещё не git-репозиторий, делает `git init`;
#   2) настраивает личность коммитера (если ещё не задана) и credential.helper;
#   3) настраивает origin на https://github.com/wild8highlander/navier-stokes-b.git;
#   4) подтягивает изменения с сервера (offline-безопасно);
#   5) добавляет всё, делает коммит (если есть что коммитить) и пушит.
#
# ПЕРВЫЙ ЗАПУСК:
#   1) создайте ПУСТОЙ репозиторий navier-stokes-b на github.com под аккаунтом
#      wild8highlander (БЕЗ README / .gitignore / license — всё уже здесь);
#   2) создайте Personal Access Token (classic, scope repo):
#      Settings → Developer settings → Personal access tokens →
#      Tokens (classic) → Generate new token (classic);
#   3) запустите скрипт — он спросит логин и токен и ЗАПОМНИТ их
#      (git credential.helper store). Пароль от GitHub НЕ подходит.
#
# ПОВТОРНЫЕ ЗАПУСКИ — просто коммитят и пушат:
#   ./push_wild8highlander.sh                        # сообщение по умолчанию
#   ./push_wild8highlander.sh "моя правка"           # своё сообщение коммита
#   ./push_wild8highlander.sh --manifest "правка"    # + перегенерация MANIFEST.json
# ============================================================================
set -e

GH_USER="wild8highlander"
GH_REPO="navier-stokes-b"
GH_URL="https://github.com/${GH_USER}/${GH_REPO}.git"

# --- распознаём флаги -------------------------------------------------------
REGEN_MANIFEST=0
ARGS=()
for a in "$@"; do
    case "$a" in
        --manifest|-m) REGEN_MANIFEST=1 ;;
        *) ARGS+=("$a") ;;
    esac
done
MSG="${ARGS[0]:-navier-stokes-b: обновление программы b-коррекции (данные, статьи, верификация)}"

# --- 0) git установлен? -----------------------------------------------------
command -v git >/dev/null 2>&1 || {
    echo "ОШИБКА: git не установлен."
    echo "  Termux (Android):  pkg install git -y"
    echo "  Linux:             sudo apt install git"
    echo "  macOS:             brew install git  (или xcode-select --install)"
    exit 1
}

# --- 1) находим корень репозитория; если его нет — создаём ------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$REPO" ]; then
    echo "Папка ещё не git-репозиторий — инициализирую..."
    cd "$SCRIPT_DIR"
    git init -b main >/dev/null 2>&1 || { git init >/dev/null && git checkout -b main >/dev/null 2>&1 || git symbolic-ref HEAD refs/heads/main; }
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

# ветка по умолчанию — main
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
if [ -z "$BRANCH" ] || [ "$BRANCH" = "HEAD" ]; then
    git checkout -b main 2>/dev/null || git checkout main 2>/dev/null || true
    BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo main)"
fi

# --- 4) обновиться (offline-безопасно) --------------------------------------
git pull --rebase --autostash 2>/dev/null || echo "  (пропущено: нет сети или нечего тянуть)"

# --- 5) (опционально) перегенерировать MANIFEST.json -------------------------
if [ "$REGEN_MANIFEST" = "1" ] && [ -f ".github/scripts/regen_manifest.py" ]; then
    echo "Перегенерирую MANIFEST.json..."
    python3 .github/scripts/regen_manifest.py 2>/dev/null \
        || python .github/scripts/regen_manifest.py \
        || echo "  (не удалось — python3 недоступен? MANIFEST останется прежним)"
fi

# --- 6) добавить всё и закоммитить (если есть изменения) ---------------------
git add -A
if git diff --cached --quiet; then
    echo "Нет изменений — коммит не нужен."
else
    git commit -m "$MSG"
fi

# --- 7) отправка -------------------------------------------------------------
echo "Отправляю в origin/$BRANCH (объём ~100 МБ; на мобильной сети — несколько минут)..."
if git push -u origin "$BRANCH"; then
    echo ""
    echo "ГОТОВО: https://github.com/${GH_USER}/${GH_REPO}"
    echo "Первый push: включите Actions (Settings → Actions → General → Allow all actions),"
    echo "чтобы бейджи CI и Manifest на главной стали зелёными."
else
    echo ""
    echo "ОШИБКА push. Проверьте по порядку:"
    echo "  1) репозиторий ${GH_USER}/${GH_REPO} создан на github.com (пустой, без README);"
    echo "  2) при запросе пароля вставлен Personal Access Token (ghp_…), НЕ пароль GitHub;"
    echo "  3) токен действителен и имеет scope 'repo' (classic);"
    echo "  4) сеть доступна. Затем повторите: ./push_wild8highlander.sh"
    echo ""
    echo "Подробная инструкция: TERMUX_GUIDE.md (раздел «Частые проблемы»)."
    exit 1
fi
