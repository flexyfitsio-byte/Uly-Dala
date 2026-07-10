# Деплой на Railway

## Важно прочитать перед деплоем

Контейнеры Railway **не имеют постоянного диска** — всё, что приложение пишет на диск
во время работы, стирается при каждом передеплое. У нас это касается:

- `data/users.json` — XP, уровни, посещённые места, ответы на викторины
- `data/auth_users.json` — email и хэши паролей зарегистрированных пользователей

`data/places.json` (сами места) не пострадает — это статичные данные, часть кода.

**Решение на время MVP:** смонтировать Railway Volume и указать его путь в переменной
окружения `DATA_DIR` (см. шаг 5 ниже). Тогда пользовательские данные переживут передеплой.
Это временное решение — при росте проекта эти файлы стоит перенести в PostgreSQL
(Railway это тоже умеет одним кликом), не переписывая роуты — весь доступ к данным уже
изолирован в `database/db_manager.py`.

---

## Вариант А — через GitHub (рекомендуется для дальнейшей разработки)

1. Создайте репозиторий на GitHub и запушьте туда содержимое `uly_dala_startup/`:
   ```bash
   cd uly_dala_startup
   git init
   git add .
   git commit -m "Uly Dala MVP"
   git branch -M main
   git remote add origin https://github.com/<ваш-логин>/uly-dala.git
   git push -u origin main
   ```
2. Зайдите на [railway.app](https://railway.app), авторизуйтесь через GitHub.
3. **New Project → Deploy from GitHub repo** → выберите ваш репозиторий.
4. Railway сам определит, что это Python-приложение, установит зависимости из
   `requirements.txt` и запустит команду из `Procfile` (`gunicorn app:app`).
5. Зайдите в **Variables** созданного сервиса и добавьте:
   - `SECRET_KEY` — любая длинная случайная строка (обязательно, иначе сессии/логин сломаются)
   - `FLASK_DEBUG` = `False`
   - `AI_PROVIDER` (groq/xai/openai) + соответствующий ключ (`GROQ_API_KEY` и т.п.) — опционально, для настоящей генерации через LLM
     (без него ИИ-гид работает в демо-режиме)
   - `DATA_DIR` = `/data` — если подключите Volume (следующий пункт)
6. **(Рекомендуется)** Settings → Volumes → Add Volume, mount path `/data`.
   Это защитит XP и логины пользователей от передеплоев.
7. Settings → Networking → **Generate Domain** — получите публичный URL вида
   `uly-dala-production.up.railway.app`.
8. После каждого `git push` в `main` Railway передеплоит проект автоматически.

## Вариант Б — через CLI (быстрее для разового деплоя без GitHub)

```bash
npm install -g @railway/cli   # или: brew install railway
railway login
cd uly_dala_startup
railway init                  # создаст новый проект, спросит имя
railway up                     # загрузит текущую папку и задеплоит
```

Дальше так же зайдите в Variables на railway.app и задайте `SECRET_KEY`,
`FLASK_DEBUG=False`, опционально `AI_PROVIDER` + ключ провайдера и `DATA_DIR=/data` (+ Volume).
Домен создаётся так же через Settings → Networking → Generate Domain.

---

## Проверка после деплоя

Откройте `https://<ваш-домен>.up.railway.app` — должна открыться главная страница
с местами. Проверьте `/chat` (ИИ-гид) и попробуйте зарегистрироваться на `/register`.

Если что-то не работает — Railway → сервис → **View logs** обычно сразу показывает причину
(чаще всего — не задан `SECRET_KEY` или опечатка в имени переменной).
