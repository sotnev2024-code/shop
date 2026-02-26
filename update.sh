#!/bin/bash
# Обновление кода на сервере: git pull, сборка фронта, перезапуск бэкенда.
# Запуск: sudo bash update.sh   (из корня репозитория или: sudo bash /opt/shop/update.sh)

set -e

PROJECT_DIR="${PROJECT_DIR:-/opt/shop}"
if [[ ! -d "$PROJECT_DIR" ]]; then
  echo "Каталог не найден: $PROJECT_DIR. Задай PROJECT_DIR или запусти из корня репозитория."
  exit 1
fi

cd "$PROJECT_DIR"
echo "[*] Проект: $PROJECT_DIR"
echo ""

echo "[1/4] git pull..."
# Сброс локальных изменений, чтобы pull не падал (на сервере код = только из репозитория)
git fetch origin
git reset --hard "origin/$(git branch --show-current)"

echo "[2/4] Бэкенд: зависимости..."
cd "$PROJECT_DIR/backend"
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
deactivate

echo "[3/4] Фронт: сборка..."
cd "$PROJECT_DIR/frontend"
if ! npm ci 2>/dev/null; then
  echo "    npm ci не удался, пробуем npm install..."
  rm -rf node_modules
  npm install
fi
npm run build

echo "[4/4] Перезапуск бэкенда..."
systemctl restart shop-backend

echo ""
echo "Готово. Сайт обновлён."
