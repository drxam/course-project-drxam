.PHONY: build up down test lint scan clean help

# Переменные
IMAGE_NAME = secdev-app
CONTAINER_NAME = secdev-app

help: ## Показать справку
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

build: ## Собрать Docker образ
	docker build -t $(IMAGE_NAME):latest .

up: ## Запустить через docker-compose
	docker-compose up -d
	@echo "Приложение запущено на http://localhost:8000"

down: ## Остановить docker-compose
	docker-compose down

test: ## Запустить тесты контейнера
	@./scripts/test_container.sh

lint: ## Проверить Dockerfile с Hadolint
	@if command -v hadolint > /dev/null; then \
		hadolint Dockerfile; \
	else \
		echo "Hadolint не установлен. Установите: brew install hadolint"; \
	fi

scan: ## Сканировать образ на уязвимости с Trivy
	@if command -v trivy > /dev/null; then \
		docker build -t $(IMAGE_NAME):test .; \
		trivy image $(IMAGE_NAME):test; \
	else \
		echo "Trivy не установлен. Установите: brew install trivy"; \
	fi

clean: ## Удалить образы и контейнеры
	docker-compose down -v
	docker rmi $(IMAGE_NAME):latest $(IMAGE_NAME):test 2>/dev/null || true
	docker system prune -f

logs: ## Показать логи контейнера
	docker-compose logs -f app

shell: ## Войти в контейнер
	docker-compose exec app /bin/bash

check-user: ## Проверить, что контейнер запускается не под root
	@USER_ID=$$(docker run --rm $(IMAGE_NAME):latest id -u); \
	if [ "$$USER_ID" = "0" ]; then \
		echo "❌ ОШИБКА: Контейнер запускается под root"; \
		exit 1; \
	else \
		echo "✓ Контейнер запускается под non-root пользователем (UID: $$USER_ID)"; \
	fi

check-health: ## Проверить healthcheck
	@docker run -d --name test-health -p 8001:8000 $(IMAGE_NAME):latest; \
	sleep 10; \
	HEALTH=$$(docker inspect --format='{{.State.Health.Status}}' test-health 2>/dev/null || echo "starting"); \
	echo "Health status: $$HEALTH"; \
	docker stop test-health; \
	docker rm test-health
