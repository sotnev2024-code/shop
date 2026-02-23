# Данные для поддержки Timeweb Cloud (деплой через Docker Compose)

Ниже всё, что можно скопировать в обращение в поддержку.

---

## 1. Команды запуска

На сервере (в каталоге проекта) выполняем:

```bash
# Сборка и запуск в production
docker compose -f docker-compose.prod.yml up -d --build
```

Проверка статуса и логов:

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs --tail=100
```

Если нужны логи по отдельным сервисам:

```bash
docker compose -f docker-compose.prod.yml logs backend --tail=200
docker compose -f docker-compose.prod.yml logs app --tail=200
docker compose -f docker-compose.prod.yml logs db --tail=50
```

---

## 2. Файл docker-compose (production)

Используется файл **docker-compose.prod.yml** в корне проекта:

```yaml
version: "3.8"

services:
  db:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: shop_user
      POSTGRES_PASSWORD: shop_pass
      POSTGRES_DB: shop_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U shop_user -d shop_db"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    restart: unless-stopped
    env_file:
      - ./backend/.env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  app:
    build:
      context: .
      dockerfile: Dockerfile.prod
    restart: unless-stopped
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```

---

## 3. Dockerfile бэкенда (backend/Dockerfile)

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 4. Dockerfile приложения (фронт + nginx) — корень проекта, Dockerfile.prod

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.app.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

## 5. Конфиг nginx (nginx.app.conf в корне)

Используется внутри образа **app**:

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /uploads/ {
        proxy_pass http://backend:8000/uploads/;
        proxy_set_header Host $host;
    }

    location /webhook {
        proxy_pass http://backend:8000/webhook;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://backend:8000/health;
        proxy_set_header Host $host;
    }
}
```

---

## 6. Что написать в обращении в поддержку

Можно отправить текст в таком виде:

```
Деплой через Docker Compose (production).

Команда запуска:
docker compose -f docker-compose.prod.yml up -d --build

Структура проекта:
- docker-compose.prod.yml — в корне
- backend/Dockerfile — бэкенд (FastAPI)
- Dockerfile.prod — в корне, сборка фронта (Vite) + nginx
- nginx.app.conf — в корне
- backend/.env — переменные окружения (создаётся из backend/.env.example)

Приложение слушает порт 80 (контейнер app).

Во вложении / ниже прикладываю:
1. Полный вывод команды: docker compose -f docker-compose.prod.yml up -d --build
2. Вывод: docker compose -f docker-compose.prod.yml logs --tail=200
3. Содержимое docker-compose.prod.yml, обоих Dockerfile и nginx.app.conf — см. файл TIMEWEB_DEPLOY.md в репозитории или приложенный текст.
```

После этого вставить в обращение **реальные логи** (копировать из консоли после запуска команд выше) и при необходимости — содержимое файлов из этого документа.

---

## 7. Как получить логи для поддержки

На сервере в каталоге проекта выполните и скопируйте вывод в обращение:

```bash
# Полная сборка и запуск (скопировать весь вывод)
docker compose -f docker-compose.prod.yml up -d --build

# Статус контейнеров
docker compose -f docker-compose.prod.yml ps

# Общие логи (последние 200 строк)
docker compose -f docker-compose.prod.yml logs --tail=200
```

Если есть ошибка — приложите вывод именно той команды, где она появляется, и фрагмент логов сервиса, который падает (backend, app, db).
