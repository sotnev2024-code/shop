#!/bin/bash
# Развёртывание магазина на Ubuntu 20.04/22.04 (без Docker)
# Запуск: sudo bash deploy.sh
# Перед запуском: задай DOMAIN и при необходимости REPO_URL / PROJECT_DIR ниже.

set -e

# ============== Настройки (поменяй под себя) ==============
DOMAIN="${DOMAIN:-shop.plus-shop.ru}"
REPO_URL="${REPO_URL:-https://github.com/sotnev2024-code/shop.git}"
PROJECT_DIR="${PROJECT_DIR:-/opt/shop}"
# ==========================================================

echo "[*] Домен: $DOMAIN"
echo "[*] Проект: $PROJECT_DIR"
echo ""

# --- 1. Пакеты ---
echo "[1/6] Установка пакетов (python3.8, nginx, git)..."
apt update -qq
apt install -y python3.8 python3.8-venv python3-pip nginx git

# --- 2. Node 18 (для сборки фронта) ---
echo "[2/6] Установка Node.js 18 LTS..."
if ! command -v node &>/dev/null || [[ $(node -v 2>/dev/null | cut -d. -f1 | tr -d v) -lt 18 ]]; then
  curl -fsSL https://deb.nodesource.com/setup_18.x | bash
  apt install -y nodejs
fi
echo "    Node: $(node -v), npm: $(npm -v)"

# --- 3. Клонирование и бэкенд ---
echo "[3/6] Репозиторий и бэкенд..."
if [[ ! -d "$PROJECT_DIR" ]]; then
  mkdir -p "$(dirname "$PROJECT_DIR")"
  git clone "$REPO_URL" "$PROJECT_DIR"
fi
cd "$PROJECT_DIR/backend"
if [[ ! -d .venv ]]; then
  python3.8 -m venv .venv
fi
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "    Создан backend/.env из примера — обязательно отредактируй: BOT_TOKEN, WEBAPP_URL, ADMIN_IDS, OWNER_ID, SECRET_KEY"
fi
deactivate

# --- 4. Фронтенд ---
echo "[4/6] Сборка фронтенда..."
cd "$PROJECT_DIR/frontend"
if ! npm ci 2>/dev/null; then
  echo "    npm ci не удался, пробуем npm install..."
  rm -rf node_modules
  npm install
fi
npm run build

# --- 5. Systemd ---
echo "[5/6] Systemd-юнит shop-backend..."
cat > /etc/systemd/system/shop-backend.service << EOF
[Unit]
Description=Shop Backend (FastAPI)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR/backend
Environment="PATH=$PROJECT_DIR/backend/.venv/bin"
ExecStart=$PROJECT_DIR/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable shop-backend
systemctl start shop-backend
echo "    Сервис shop-backend: $(systemctl is-active shop-backend)"

# --- 6. Nginx ---
echo "[6/6] Nginx..."
cat > /etc/nginx/sites-available/shop << EOF
server {
    listen 80;
    server_name $DOMAIN;

    root $PROJECT_DIR/frontend/dist;
    index index.html;
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /uploads/ {
        proxy_pass http://127.0.0.1:8000/uploads/;
        proxy_set_header Host \$host;
    }

    location /webhook {
        proxy_pass http://127.0.0.1:8000/webhook;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host \$host;
    }
}
EOF
ln -sf /etc/nginx/sites-available/shop /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx

echo ""
echo "=== Готово ==="
echo "Сайт: http://$DOMAIN"
echo ""
echo "Обязательно:"
echo "  1. Отредактируй $PROJECT_DIR/backend/.env (BOT_TOKEN, WEBAPP_URL, ADMIN_IDS, OWNER_ID, SECRET_KEY)"
echo "  2. Перезапусти бэкенд: sudo systemctl restart shop-backend"
echo "  3. HTTPS: sudo apt install certbot python3-certbot-nginx && sudo certbot --nginx -d $DOMAIN"
echo "  4. В .env укажи WEBAPP_URL=https://$DOMAIN и снова: sudo systemctl restart shop-backend"
echo ""
