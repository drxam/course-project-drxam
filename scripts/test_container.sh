#!/bin/bash
# Скрипт для проверки контейнера

set -e

IMAGE_NAME="secdev-app:test"
CONTAINER_NAME="secdev-test"

echo "=== Тестирование контейнера ==="

# Сборка образа
echo "1. Сборка образа..."
docker build -t $IMAGE_NAME .

# Проверка non-root пользователя
echo "2. Проверка non-root пользователя..."
USER_ID=$(docker run --rm $IMAGE_NAME id -u)
if [ "$USER_ID" = "0" ]; then
    echo "❌ ОШИБКА: Контейнер запускается под root (UID 0)"
    exit 1
fi
echo "✓ Контейнер запускается под non-root пользователем (UID: $USER_ID)"

# Проверка размера образа
echo "3. Размер образа..."
docker images $IMAGE_NAME --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

# Проверка истории слоёв
echo "4. История слоёв..."
docker history $IMAGE_NAME --format "table {{.CreatedBy}}\t{{.Size}}" | head -10

# Запуск контейнера
echo "5. Запуск контейнера..."
docker run -d --name $CONTAINER_NAME -p 8000:8000 $IMAGE_NAME

# Ожидание запуска
echo "6. Ожидание запуска..."
sleep 5

# Проверка healthcheck
echo "7. Проверка healthcheck..."
for i in {1..12}; do
    HEALTH=$(docker inspect --format='{{.State.Health.Status}}' $CONTAINER_NAME 2>/dev/null || echo "starting")
    echo "  Попытка $i: $HEALTH"
    if [ "$HEALTH" = "healthy" ]; then
        echo "✓ Контейнер здоров"
        break
    fi
    sleep 5
done

# Проверка доступности API
echo "8. Проверка доступности API..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ API доступен"
else
    echo "❌ API недоступен"
    docker logs $CONTAINER_NAME
    exit 1
fi

# Остановка и удаление
echo "9. Остановка контейнера..."
docker stop $CONTAINER_NAME
docker rm $CONTAINER_NAME

echo "=== Все проверки пройдены ==="
