#!/bin/bash
# Скрипт для запуска приложения через docker-compose

set -e

echo "=== Запуск приложения через docker-compose ==="

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo "Создание .env файла из примера..."
    cat > .env << EOF
ENVIRONMENT=development
JWT_SECRET_KEY=your-secret-key-change-in-production
EOF
    echo "✓ Создан .env файл (обновите JWT_SECRET_KEY для production)"
fi

# Запуск через docker-compose
echo "Запуск docker-compose..."
docker-compose up --build -d

echo "Ожидание запуска сервиса..."
sleep 5

# Проверка статуса
echo "Проверка статуса контейнера..."
docker-compose ps

# Проверка healthcheck
echo "Проверка healthcheck..."
for i in {1..12}; do
    HEALTH=$(docker inspect --format='{{.State.Health.Status}}' secdev-app 2>/dev/null || echo "starting")
    echo "  Попытка $i: $HEALTH"
    if [ "$HEALTH" = "healthy" ]; then
        echo "✓ Контейнер здоров"
        break
    fi
    sleep 5
done

echo "=== Приложение запущено ==="
echo "API доступен по адресу: http://localhost:8000"
echo "Документация: http://localhost:8000/docs"
echo ""
echo "Для остановки: docker-compose down"
