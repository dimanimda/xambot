# MultiBot

Мультимессенджерная AI-платформа для бизнеса (on-premise).

## Быстрый старт

```bash
# 1. Зависимости
docker compose -f docker/docker-compose.yml up -d
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# 2. Конфигурация
cp .env.example .env
# Заполните MULTIBOT_YAIS_API_KEY, MULTIBOT_YAIS_FOLDER_ID

# 3. Миграции
alembic upgrade head

# 4. Запуск
python -m src.main
```

API docs: http://localhost:8000/docs
