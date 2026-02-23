# Размещение на сервере без Docker

Пошаговая установка на VPS (Ubuntu 22.04 / Debian 12): **Python 3.8**, Node (только для сборки), nginx. База данных — **SQLite** (файл создаётся автоматически).

---

## 1. Подготовка сервера

Подключитесь по SSH и выполните:

```bash
sudo apt update && sudo apt install -y python3.8 python3.8-venv python3-pip \
  nginx nodejs npm git
```

Создайте пользователя для приложения (необязательно, можно под root):

```bash
sudo useradd -m -s /bin/bash app
sudo su - app
```

Дальше команды — от имени этого пользователя или root.

---

## 2. Клонирование и бэкенд

```bash
cd /opt   # или /home/app
sudo git clone https://github.com/sotnev2024-code/shop.git
cd shop
```

Создайте виртуальное окружение и установите зависимости:

```bash
cd backend
python3.8 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

> Если какие-то пакеты не ставятся на Python 3.8 (требуют 3.9+), уточните у хостера возможность установки более новой версии Python (pyenv, deadsnakes или другой образ).

Создайте файл `.env` в папке `backend/`:

```bash
nano .env
```

Содержимое (подставьте свои значения):

```env
BOT_TOKEN=токен_от_BotFather
WEBAPP_URL=https://shop.plus-shop.ru
ADMIN_IDS=ваш_telegram_id
OWNER_ID=ваш_telegram_id
SECRET_KEY=случайная_длинная_строка

# SQLite — файл создаётся сам в backend/shop.db
DATABASE_URL=sqlite+aiosqlite:///./shop.db
# Redis не обязателен, можно оставить пустым
REDIS_URL=
```

Проверка запуска бэкенда:

```bash
cd /opt/shop/backend
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

В другом терминале: `curl http://127.0.0.1:8000/health` — должен ответить `{"status":"ok"}`. Остановите uvicorn (Ctrl+C).

---

## 3. Сборка фронтенда

На сервере (нужен Node только для сборки):

```bash
cd /opt/shop/frontend
npm ci
npm run build
```

В папке `frontend/dist/` появятся статические файлы — их будет отдавать nginx.

---

## 4. Systemd — автозапуск бэкенда

Создайте юнит (от root):

```bash
sudo nano /etc/systemd/system/shop-backend.service
```

Вставьте (путь `/opt/shop` замените, если проект лежит в другом месте):

```ini
[Unit]
Description=Shop Backend (FastAPI)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/shop/backend
Environment="PATH=/opt/shop/backend/.venv/bin"
ExecStart=/opt/shop/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Включите и запустите:

```bash
sudo systemctl daemon-reload
sudo systemctl enable shop-backend
sudo systemctl start shop-backend
sudo systemctl status shop-backend
```

---

## 5. Nginx — сайт и прокси на бэкенд

Создайте конфиг (подставьте свой домен):

```bash
sudo nano /etc/nginx/sites-available/shop
```

Вставьте (замените `shop.plus-shop.ru` на свой домен):

```nginx
server {
    listen 80;
    server_name shop.plus-shop.ru;

    root /opt/shop/frontend/dist;
    index index.html;
    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /uploads/ {
        proxy_pass http://127.0.0.1:8000/uploads/;
        proxy_set_header Host $host;
    }

    location /webhook {
        proxy_pass http://127.0.0.1:8000/webhook;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host $host;
    }
}
```

Включите сайт и перезапустите nginx:

```bash
sudo ln -s /etc/nginx/sites-available/shop /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

Проверьте в браузере: **http://shop.plus-shop.ru** — должна открыться главная.

---

## 6. SSL (HTTPS) через Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d shop.plus-shop.ru
```

Следуйте подсказкам. Certbot сам настроит HTTPS в nginx. После этого откройте **https://shop.plus-shop.ru**.

В `backend/.env` убедитесь, что указано: `WEBAPP_URL=https://shop.plus-shop.ru`. Перезапустите бэкенд:

```bash
sudo systemctl restart shop-backend
```

---

## 7. Каталог для загрузок

Бэкенд создаёт `backend/uploads` сам при первом запуске. Если приложение работает не из-под root, проверьте права:

```bash
sudo chown -R www-data:www-data /opt/shop/backend/uploads
```

(или пользователь, под которым запущен uvicorn в systemd).

---

## 8. Обновление с GitHub

```bash
cd /opt/shop
sudo git pull

cd backend && source .venv/bin/activate && pip install -r requirements.txt
sudo systemctl restart shop-backend

cd ../frontend && npm ci && npm run build
sudo systemctl reload nginx
```

---

## 9. Бэкап SQLite

База — один файл `backend/shop.db`. Бэкап: скопировать его (например, по cron):

```bash
cp /opt/shop/backend/shop.db /opt/backups/shop_$(date +%Y%m%d).db
```

---

## Краткий чеклист

| Шаг | Действие |
|-----|----------|
| 1 | Установить Python 3.8, nginx, Node, git |
| 2 | Клонировать репозиторий, venv, pip install, создать backend/.env с DATABASE_URL=sqlite+aiosqlite:///./shop.db |
| 3 | В frontend: npm ci && npm run build |
| 4 | Systemd: shop-backend.service на порту 8000 |
| 5 | Nginx: раздача frontend/dist и прокси /api, /uploads, /webhook на 127.0.0.1:8000 |
| 6 | certbot --nginx для HTTPS |
| 7 | WEBAPP_URL в .env = https://ваш-домен |

После этого сайт работает по HTTPS без Docker. База SQLite создаётся автоматически при первом запуске.
