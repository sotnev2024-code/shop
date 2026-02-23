#!/bin/bash
# ============================================
# Shop Mini App - Quick Deploy Script
# ============================================

set -e

echo "=== Shop Mini App - Deployment ==="
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "ERROR: docker-compose not found. Please install docker-compose."
    exit 1
fi

# Check .env
if [ ! -f "backend/.env" ]; then
    echo "No .env file found. Creating from .env.example..."
    cp backend/.env.example backend/.env
    echo ""
    echo "IMPORTANT: Edit backend/.env with your settings before continuing!"
    echo "  - BOT_TOKEN: Your Telegram bot token"
    echo "  - WEBAPP_URL: Your domain URL"
    echo "  - ADMIN_CHAT_ID: Chat ID for order notifications"
    echo "  - ADMIN_IDS: Comma-separated Telegram IDs for admin access"
    echo ""
    read -p "Press Enter after editing .env to continue..."
fi

echo ""
echo "Building and starting services..."
docker compose up -d --build

echo ""
echo "Waiting for database to be ready..."
sleep 5

echo ""
echo "Running database migrations..."
docker compose exec backend alembic upgrade head

echo ""
echo "=== Deployment complete! ==="
echo ""
echo "Services:"
echo "  - Backend API: http://localhost:8000"
echo "  - Frontend:    http://localhost:3000"
echo "  - Nginx:       http://localhost:80"
echo ""
echo "Next steps:"
echo "  1. Set up SSL (certbot) for your domain"
echo "  2. Update WEBAPP_URL in .env to your HTTPS domain"
echo "  3. Set webhook: https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://your-domain.com/webhook"
echo ""





