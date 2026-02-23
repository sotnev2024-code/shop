# Shop - Telegram Mini App

Интернет-магазин в виде Telegram Mini App с админ-панелью и интеграциями с 1C и МойСклад.

## Требования

- **Python 3.10+** (рекомендуется 3.11+)
- **Node.js 18+** и npm
- **Telegram Bot Token** (получить у [@BotFather](https://t.me/BotFather))

## Быстрый старт

### 1. Клонирование и настройка окружения

```powershell
# Перейдите в директорию проекта
cd C:\Users\sotne\PycharmProjects\shop

# Создайте виртуальное окружение Python (если еще не создано)
python -m venv venv

# Активируйте виртуальное окружение
.\venv\Scripts\Activate.ps1

# Установите зависимости Python
cd backend
pip install -r requirements.txt
cd ..
```

### 2. Настройка переменных окружения

Создайте файл `backend/.env` со следующим содержимым:

```env
# Режим разработки (для локальной разработки без Telegram)
DEV_MODE=true

# База данных (SQLite для локальной разработки)
DATABASE_URL=sqlite+aiosqlite:///./shop.db

# Telegram Bot
BOT_TOKEN=ваш_токен_бота_от_BotFather
WEBAPP_URL=http://localhost:3000
ADMIN_CHAT_ID=ваш_telegram_id

# ID владельца платформы (для доступа к панели owner)
OWNER_ID=ваш_telegram_id

# Настройки магазина
SHOP_NAME=Мой магазин
CURRENCY=RUB

# Источник товаров (database, moysklad, one_c)
PRODUCT_SOURCE=database

# Тип оформления заказа (basic, enhanced, payment, full)
CHECKOUT_TYPE=basic

# Включенные функции
DELIVERY_ENABLED=false
PICKUP_ENABLED=true
PROMO_ENABLED=true
MAILING_ENABLED=true

# Интервал синхронизации товаров (в минутах)
SYNC_INTERVAL_MINUTES=15

# Интеграции (опционально)
MOYSKLAD_API_KEY=
MOYSKLAD_API_SECRET=
ONE_C_API_URL=
YANDEX_DELIVERY_API_KEY=
SDEK_API_KEY=
RUSSIAN_POST_API_KEY=
```

**Важно:** 
- Замените `ваш_токен_бота_от_BotFather` на реальный токен от BotFather
- Замените `ваш_telegram_id` на ваш Telegram ID (можно узнать у [@userinfobot](https://t.me/userinfobot))

### 3. Инициализация базы данных

```powershell
# Активируйте виртуальное окружение (если еще не активировано)
.\venv\Scripts\Activate.ps1

# Перейдите в директорию backend
cd backend

# Запустите инициализацию БД
python init_db.py

cd ..
```

### 4. Установка зависимостей frontend

```powershell
cd frontend
npm install
cd ..
```

## Запуск проекта

### Автоматический запуск (рекомендуется)

Просто запустите скрипт `start.ps1`:

```powershell
.\start.ps1
```

Скрипт автоматически:
- Проверит наличие Node.js и зависимостей
- Создаст базу данных, если её нет
- Запустит backend на порту 8000
- Запустит frontend на порту 3000

### Ручной запуск

#### Backend (в отдельном терминале):

```powershell
# Активируйте виртуальное окружение
.\venv\Scripts\Activate.ps1

# Перейдите в директорию backend
cd backend

# Запустите сервер
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend будет доступен по адресу: http://localhost:8000
API документация (Swagger): http://localhost:8000/docs

#### Frontend (в отдельном терминале):

```powershell
cd frontend
npm run dev
```

Frontend будет доступен по адресу: http://localhost:3000

## Использование

### Локальная разработка (DEV_MODE=true)

1. Откройте http://localhost:3000 в браузере
2. В dev режиме аутентификация обходится автоматически
3. Вы будете залогинены как тестовый пользователь

### Продакшн (DEV_MODE=false)

1. Создайте бота через [@BotFather](https://t.me/BotFather)
2. Получите токен бота
3. Настройте `WEBAPP_URL` на ваш домен (например, `https://yourdomain.com`)
4. Запустите бота и откройте Mini App через Telegram

## Структура проекта

```
shop/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── bot/         # Telegram bot handlers
│   │   ├── db/          # Database models
│   │   ├── schemas/     # Pydantic schemas
│   │   └── services/    # Business logic
│   ├── .env             # Environment variables
│   └── requirements.txt # Python dependencies
│
├── frontend/            # React frontend
│   ├── src/
│   │   ├── admin/       # Admin panel pages
│   │   ├── api/         # API client
│   │   ├── components/  # React components
│   │   ├── pages/       # Page components
│   │   └── store/       # Zustand stores
│   └── package.json     # Node dependencies
│
└── start.ps1           # Startup script
```

## Основные функции

- ✅ Каталог товаров с фильтрацией и поиском
- ✅ Корзина и оформление заказов
- ✅ Избранное
- ✅ Админ-панель (управление товарами, заказами, настройками)
- ✅ Панель владельца (настройка модулей и интеграций)
- ✅ Интеграция с 1C и МойСклад
- ✅ Промокоды
- ✅ Рассылки
- ✅ Различные типы оформления заказа

## Полезные команды

```powershell
# Остановить все процессы на портах 3000 и 8000
Get-NetTCPConnection -LocalPort 3000,8000 -State Listen | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }

# Пересоздать базу данных
Remove-Item backend\shop.db -ErrorAction SilentlyContinue
cd backend
python init_db.py
cd ..

# Просмотр логов backend
# Логи выводятся в консоль, где запущен uvicorn
```

## Решение проблем

### Ошибка 401 Unauthorized
- Убедитесь, что `DEV_MODE=true` в `backend/.env`
- Перезапустите backend после изменения `.env`

### База данных не создается
- Проверьте права на запись в директорию `backend/`
- Убедитесь, что `DATABASE_URL` указан правильно

### Frontend не подключается к backend
- Проверьте, что backend запущен на порту 8000
- Проверьте настройки proxy в `frontend/vite.config.ts`

### Порт уже занят
- Остановите процессы на портах 3000 и 8000 (см. команды выше)
- Или измените порты в конфигурации

## Дополнительная информация

- **Backend API Docs**: http://localhost:8000/docs
- **Backend ReDoc**: http://localhost:8000/redoc

#   s h o p  
 