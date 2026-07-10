# Uly Dala — Backend

## Что было исправлено по сравнению с исходным zip

- Файлы разложены по правильным папкам (`routes/`, `services/`, `middleware/`, `prisma/`) — раньше импорты в коде не совпадали с плоской структурой файлов.
- Добавлена авторизация: `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me` — раньше JWT-мидлвар требовал токен, но выдавать его было негде.
- Добавлен `prisma/seed.js` с 5 реальными местами (Бурабай, Туркестан, Чарын, Кольсай, Медеу) — без этого таблица `Place` пуста и ИИ-маршруты никогда не строятся.
- Добавлены `GET /api/game/passport/stamps` и `GET /api/game/trips` для личного кабинета.
- Добавлен `bcryptjs` для хеширования паролей.
- `Procfile` теперь запускает миграцию, сид и сервер по очереди.

## Деплой на Railway

1. Залейте эту папку в GitHub-репозиторий (Railway деплоит из репо).
2. В Railway: **New Project → Deploy from GitHub repo**, выберите репозиторий.
3. Добавьте плагин **PostgreSQL** (New → Database → PostgreSQL) в том же проекте — Railway сам создаст переменную `DATABASE_URL` и подставит её в сервис.
4. В настройках сервиса (Variables) добавьте:
   - `JWT_SECRET`
   - `AI_API_KEY`
   - `AI_BASE_URL`
   - `AI_MODEL_NAME`
   (переменную `PORT` Railway задаёт сама, ничего делать не нужно)
5. Railway автоматически распознает `Procfile` и выполнит `npx prisma db push && node prisma/seed.js && node server.js` при каждом деплое.
6. После деплоя проверьте `https://<ваш-домен>.up.railway.app/health` — должен вернуться `{ "status": "alive" }`.

## Проверка API

```bash
# Регистрация
curl -X POST https://<домен>/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"12345678","fullName":"Тест Тестов"}'

# Генерация маршрута (нужен token из ответа выше)
curl -X POST https://<домен>/api/ai/generate-route \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"query":"Хочу в горы","budget":80000,"daysCount":3}'
```

## Чего всё ещё нет (для полного MVP из презентации)

- **Фронтенда нет вообще** — в zip только backend. Нужно поднять React + Vite отдельно и задеплоить на Vercel/Railway.
- Роутов для викторин (Quiz) — модель в базе есть, эндпоинтов для генерации/прохождения нет.
- Роута для "рассказать подробнее" (пересказ истории места через ИИ) — тоже упоминался в вашем плане, но не реализован.
