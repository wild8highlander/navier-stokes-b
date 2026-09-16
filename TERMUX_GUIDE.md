# 📱 Инструкция: отправка navier-stokes-b на GitHub с Android (Termux)

Пошаговое руководство для аккаунта **wild8highlander**. Время: ~10 минут
однократно; последующие отправки — одна команда `./push_wild8highlander.sh`.

---

## Шаг 0. Подготовка на GitHub (однократно, с любого устройства)

1. Зайдите на https://github.com под логином `wild8highlander`.
2. Создайте **пустой** репозиторий: кнопка **New repository** →
   имя `navier-stokes-b` → **не** добавляйте README, .gitignore и лицензию
   (всё это уже есть в папке) → **Create repository**.
3. Создайте токен доступа: **Settings → Developer settings →
   Personal access tokens → Tokens (classic) → Generate new token (classic)**:
   - Note: `termux-push`;
   - Expiration: по вкусу (90 дней);
   - Scope: ☑ **repo** (полностью);
   - **Generate token** и **сразу скопируйте** токен
     (`ghp_…`) — после закрытия страницы он больше не показывается.

## Шаг 1. Установите Termux

Устанавливайте **только с F-Droid** (версия из Play Market устарела):
https://f-droid.org/packages/com.termux/

После установки откройте Termux и обновите пакеты:

```bash
pkg update && pkg upgrade -y
pkg install git unzip -y
```

## Шаг 2. Перенесите архив на телефон

Вариант А — архив уже скачан на телефон:

```bash
termux-setup-storage          # разрешите доступ к хранилищу (появится ~/storage)
cd ~/storage/downloads        # или ~/storage/shared — куда скачали
unzip navier-stokes-b.zip -d ~
cd ~/navier-stokes-b
```

Вариант Б — скачать прямо из Termux (если архив лежит по прямой ссылке):

```bash
pkg install wget -y
wget <ПРЯМАЯ_ССЫЛКА_НА_НАВИЕР-СТОКС-b.zip> -O ~/nsb.zip
unzip ~/nsb.zip -d ~
cd ~/navier-stokes-b
```

## Шаг 3. Инициализируйте git (только если папка ещё не git-репозиторий)

```bash
git init -b main
```

## Шаг 4. Отправьте репозиторий

```bash
chmod +x push_wild8highlander.sh
./push_wild8highlander.sh
```

Скрипт сам настроит origin на `https://github.com/wild8highlander/navier-stokes-b.git`,
сделает коммит и запушит. При первом запуске появится запрос:

```
Username for 'https://github.com': wild8highlander
Password for 'https://wild8highlander@github.com': <вставьте PAT, Шаг 0.3>
```

⚠️ Вставляйте **токен** (`ghp_…`), а не пароль от GitHub. В Termux вставка —
долгое нажатие → *Paste*. Символы не отображаются — это нормально, нажмите Enter.

Учётные данные запомнятся (`credential.helper store`) — дальше пуш идёт без вопросов.

## Шаг 5. Проверьте результат

Откройте https://github.com/wild8highlander/navier-stokes-b — файлы на месте.

---

## Повторные отправки

```bash
cd ~/navier-stokes-b
./push_wild8highlander.sh "что изменилось — одно предложение"
```

## Частые проблемы

| Симптом | Решение |
|---|---|
| `Authentication failed` | Токен просрочен/скопирован не полностью — создайте новый (Шаг 0.3) |
| `Repository not found` | Репозиторий не создан или имя с опечаткой — проверьте Шаг 0.2 |
| `remote origin already exists` | Не ошибка: скрипт сам обновляет URL origin |
| `error: src refspec main…` | Сначала `git init -b main` (Шаг 3), затем повторите |
| Push «висит» при медленной сети | Повторите команду; объём репозитория ~100 МБ, на мобильной сети может уходить несколько минут |
| Termux закрывается в фоне | Возьмите в notification bar **Acquire wakelock** перед пушем |

## Шпаргалка git (если нужно вручную)

```bash
git status                        # что изменилось
git add -A                        # добавить всё
git commit -m "сообщение"         # зафиксировать
git push origin main              # отправить
git pull --rebase                 # забрать чужие изменения
```

*Лицензия IPL-RP-1.0: содержимое — собственность Isaev Iskhak Khamzatovich (wild8highlander). Все права защищены.*
