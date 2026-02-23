# Размещение проекта на сервере

Краткая инструкция по деплою магазина (Telegram Mini App + админка) на сервер.

## Что нужно на сервере

- **Docker** и **Docker Compose** (v2: `docker compose`)
- Домен или IP, на который будет открыт сайт
- Для бота: токен Telegram Bot и публичный HTTPS-адрес (для webhook или доступа к Mini App)

---

## 1. Клонирование и настройка окружения

На сервере:

```bash
# Клонировать репозиторий (или загрузить архив)
git clone <url-репозитория> shop
cd shop
```

Создайте файл с переменными окружения для бэкенда:

```bash
cp backend/.env.example backend/.env
nano backend/.env   # или любой редактор
```

**Обязательно задайте в `backend/.env`:**

| Переменная | Описание |
|------------|----------|
| `BOT_TOKEN` | Токен бота от @BotFather |
| `WEBAPP_URL` | Полный URL Mini App, например `https://yourdomain.com` |
| `DATABASE_URL` | Для Docker: `postgresql+asyncpg://shop_user:shop_pass@db:5432/shop_db` |
| `REDIS_URL` | Для Docker: `redis://redis:6379/0` |
| `SECRET_KEY` | Случайная строка для подписи сессий |
| `ADMIN_IDS` | Telegram ID админов через запятую |
| `OWNER_ID` | Telegram ID владельца (для панели владельца) |

Остальные переменные можно оставить по умолчанию или задать по необходимости (МойСклад, оплата и т.д.).

---

## 2. Запуск в production (рекомендуемый способ)

Сборка и запуск всех сервисов (БД, Redis, бэкенд, фронт в виде статики за nginx):

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

- Приложение будет доступно на **порту 80** (откройте в браузере `http://IP_СЕРВЕРА` или `https://ваш-домен`).
- Фронт (каталог, админка) отдаётся nginx, запросы `/api/`, `/uploads/`, `/webhook` проксируются на бэкенд.

Проверка:

```bash
docker compose -f docker-compose.prod.yml ps
curl http://localhost/health   # если health отдаётся через тот же порт — настройте или проверьте бэкенд напрямую
```

Логи:

```bash
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f app
```

---

## 3. Локальная разработка

Основной **docker-compose.yml** в репозитории настроен под облако (Timeweb и др.): без `version`, без именованных volumes, без `env_file`. Для разработки на своём компьютере используйте:

```bash
docker compose -f docker-compose.dev.yml up -d --build
```

Нужен файл **backend/.env** (скопируйте из `backend/.env.example`). Сайт — порт 80, бэкенд — 8000, фронт (Vite) — 3000.

---

## 4. HTTPS и домен

1. **Домен:** укажите A-запись на IP сервера.
2. **Сертификат:** удобнее всего использовать **Let's Encrypt** (certbot). После получения сертификатов настройте nginx на приём 443 и отдачу сертификатов (можно вынести конфиг в отдельный файл и подключить его в контейнере nginx).
3. В `backend/.env` задайте `WEBAPP_URL=https://ваш-домен.ru`, чтобы Mini App открывался по HTTPS.

При необходимости можно добавить второй конфиг nginx для HTTPS и подключать его в том же образе `app` (через volume или свой Dockerfile).

---

## 5. Обновление после изменений в коде

```bash
cd shop
git pull   # или загрузите новые файлы

# Пересобрать и перезапустить
docker compose -f docker-compose.prod.yml up -d --build
```

Миграции БД (если появятся) обычно запускаются при старте приложения или отдельной командой — смотрите описание в проекте.

---

## 6. Структура для production

- **docker-compose.prod.yml** — БД (PostgreSQL), Redis, бэкенд (FastAPI), один контейнер **app** (собранный фронт + nginx на порту 80).
- **Dockerfile.prod** — двухэтапная сборка: сборка фронта (Vite), затем nginx со статикой и проксированием API.
- **nginx.app.conf** — конфиг nginx внутри образа app: раздача SPA и проксирование `/api/`, `/uploads/`, `/webhook` на backend.
- **backend/.env** — переменные окружения бэкенда (никогда не коммитьте реальный `.env` в репозиторий).

После запуска откройте в браузере ваш домен или IP — должна открыться главная (каталог). Админка и панель владельца доступны через пункты меню Mini App; для доступа нужны соответствующие Telegram ID в `ADMIN_IDS` и `OWNER_ID`.
