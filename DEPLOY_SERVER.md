# Размещение на сервере без Docker

Пошаговая установка на VPS: **Ubuntu 20.04, 22.04** или **Debian 12**. Нужны **Python 3.8**, Node (только для сборки), nginx. База данных — **SQLite** (файл создаётся автоматически).

На Ubuntu 20.04 Python 3.8 уже в репозитории; Node из `apt` старый — для сборки фронта лучше поставить Node 18 LTS (см. шаг 3).

**Скрипт-одним-запуском:** в корне репозитория есть `deploy.sh`. На сервере можно выполнить:
```bash
# Свой домен передаётся переменной (по умолчанию shop.plus-shop.ru)
sudo DOMAIN=твой-домен.ru bash deploy.sh
```
Если при запуске появляются ошибки вида `$'\r': command not found` или `invalid option` — у файла переводы строк Windows (CRLF). Исправь на сервере: `sed -i 's/\r$//' deploy.sh`, затем снова `sudo bash deploy.sh`. В репозитории для `deploy.sh` заданы LF (файл `.gitattributes`).

После скрипта остаётся отредактировать `backend/.env` и при необходимости включить HTTPS (certbot). Подробности — в конце вывода скрипта и в шагах ниже.

---

## Перед развёртыванием (локально или в репозитории)

- В репозитории есть `backend/.env.example` — на сервере его копируют в `backend/.env` и заполняют (см. шаг 2).
- В Git не попадают: `backend/.env`, `backend/shop.db`, `backend/uploads/` — они создаются на сервере.

---

## 1. Подготовка сервера

Подключитесь по SSH и выполните:

```bash
sudo apt update && sudo apt install -y python3.8 python3.8-venv python3-pip \
  nginx git
```

На Ubuntu 20.04/22.04 пакеты `python3.8` и `python3.8-venv` есть в репозитории. Node для сборки фронта лучше ставить отдельно (Node 18 LTS) — см. шаг 3.

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

Скопируйте пример конфига и отредактируйте под себя:

```bash
cp .env.example .env
nano .env
```

Обязательно задайте (остальное можно оставить по умолчанию):

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

Проверка запуска бэкенда вручную:

Если бэкенд уже запущен через systemd, порт 8000 занят — перед ручным запуском остановите сервис:  
`sudo systemctl stop shop-backend`

```bash
cd /opt/shop/backend
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

В другом терминале: `curl http://127.0.0.1:8000/health` — должен ответить `{"status":"ok"}`. Остановите uvicorn (Ctrl+C). После проверки снова запустите сервис: `sudo systemctl start shop-backend`.

---

## 3. Сборка фронтенда

На сервере нужна **Node.js 18+** (и npm 8+), иначе `npm ci` может выдать ошибку вида `Cannot read property '@telegram-apps/sdk-react' of undefined` из‑за старого формата lock-файла.

**Установка Node 18 LTS (если из apt стоит Node 10–16 и старый npm):**

```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
node -v   # должно быть v18.x или выше
npm -v    # должно быть 8.x или выше
```

После этого соберите фронт:

```bash
cd /opt/shop/frontend
npm ci
npm run build
```

Если `npm ci` всё равно падает — попробуйте установить зависимости без lock-файла и собрать:

```bash
cd /opt/shop/frontend
rm -rf node_modules
npm install
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
# RestartSec даёт порту 8000 освободиться после падения, иначе возможен Errno 98 (Address already in use)

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

База — один файл `backend/shop.db`. Бэкап: скопировать его (например, по cron). Каталог для бэкапов нужно создать один раз:

```bash
sudo mkdir -p /opt/backups
cp /opt/shop/backend/shop.db /opt/backups/shop_$(date +%Y%m%d).db
```

---

## 10. Почему не работает сайт — быстрая проверка

Выполни на сервере по порядку и смотри, на каком шаге ошибка:

| Шаг | Команда | Ожидание |
|-----|---------|----------|
| 1 | `sudo systemctl status shop-backend` | `active (running)` |
| 2 | `curl -s http://127.0.0.1:8000/health` | `{"status":"ok"}` |
| 3 | `curl -s -o /dev/null -w "%{http_code}" https://ТВОЙ_ДОМЕН/api/v1/health` | `200` |
| 4 | Открыть в браузере `https://ТВОЙ_ДОМЕН` | Открывается главная |

- **Шаг 1 не ОК** — бэкенд не запущен или падает. Логи: `sudo journalctl -u shop-backend -n 80`.
- **Шаг 2 не ОК** — процесс не слушает порт 8000 (падает при старте или порт занят). См. п. 5 ниже и логи.
- **Шаг 3 не ОК** — nginx не проксирует на бэкенд (502/504) или нет `location /api/` (404). Проверь конфиг nginx и `sudo nginx -t`.усвы
- **Шаг 4 не ОК** — сайт открывается, но бесконечная загрузка: фронт не получает ответ от API (см. ниже).

---

## 11. Если сайт бесконечно грузится

Приложение при старте запрашивает `/api/v1/config`. Пока ответ не пришёл — показывается спиннер. Проверьте по шагам:

**1. Бэкенд запущен и отвечает**

```bash
sudo systemctl status shop-backend
curl -s http://127.0.0.1:8000/health
```

Должно быть `{"status":"ok"}`. Если нет — смотрите логи: `sudo journalctl -u shop-backend -n 50`.

**2. Nginx проксирует API**

```bash
curl -s -o /dev/null -w "%{http_code}" https://ВАШ_ДОМЕН/api/v1/health
```

Должно быть `200`. Если 502 — бэкенд не слушает 8000 или nginx указывает не туда. Если 404 — в конфиге nginx нет `location /api/`.

**3. Открывать сайт из Telegram**

Магазин рассчитан на запуск как Mini App из бота. При открытии по прямой ссылке в браузере запрос `/config` получит 401 (нет авторизации Telegram) — в этом случае приложение должно всё равно уйти с загрузки и показать интерфейс. Если спиннер не исчезает, запрос к API не доходит или зависает (п. 1–2).

**4. Таймаут на фронте**

В `frontend/src/api/client.ts` можно задать `timeout: 15000` в `axios.create`, чтобы при недоступном API через 15 секунд запрос обрывался и приложение переставало «крутить» загрузку.

**5. Падения с TelegramNetworkError и Errno 98**

Если в логах видно `TelegramNetworkError` или `ServerDisconnected`, а затем `Errno 98 (Address already in use)` — бот не смог достучаться до Telegram (сеть/файрвол), процесс упал, а при быстром рестарте порт 8000 ещё занят. В коде добавлено: при сетевой ошибке бота процесс не завершается, polling перезапускается через 30 секунд. Убедитесь, что в юните systemd указано `RestartSec=5`. После обновления кода выполните `sudo systemctl daemon-reload` и `sudo systemctl restart shop-backend`.

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
