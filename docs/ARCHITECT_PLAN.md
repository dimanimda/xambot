# ARCHITECT PLAN: MultiBot v0.1 — Week 1

**Дата:** 17.06.2026  
**Статус:** Дизайн-документ (read-only)  
**Роль:** Architect

---

## Содержание

1. [Project Directory Tree](#1-project-directory-tree)
2. [Database Schema](#2-database-schema)
3. [Configuration Design](#3-configuration-design)
4. [Detailed Week 1 Task Breakdown](#4-detailed-week-1-task-breakdown)
   - [Task 1: Project Initialization](#task-1-project-initialization)
   - [Task 2: Multi-tenant Model](#task-2-multi-tenant-model)
   - [Task 3: YAIS AI Provider](#task-3-yais-ai-provider)
   - [Task 4: MAX Adapter](#task-4-max-adapter)
   - [Task 5: End-to-end Dialog](#task-5-end-to-end-dialog)
5. [Data Flow Diagrams](#5-data-flow-diagrams)
6. [Error Handling Strategy](#6-error-handling-strategy)
7. [Testing Strategy for Week 1](#7-testing-strategy-for-week-1)
8. [Architectural Decisions Log](#8-architectural-decisions-log)

---

## 1. Project Directory Tree

### Полное дерево (Week 1 результат)

```
xambot/
│
├── docs/                                    # Документация проекта
│   ├── TO.md                               # Техническое задание (утверждено)
│   ├── PLAN.md                             # План реализации (утверждён)
│   └── ARCHITECT_PLAN.md                   # ← ЭТОТ ФАЙЛ
│
├── src/                                     # Исходный код приложения
│   ├── __init__.py                         # Пакет multibot
│   ├── main.py                             # Точка входа: uvicorn.run()
│   │
│   ├── core/                               # Ядро платформы
│   │   ├── __init__.py
│   │   ├── config.py                       # Pydantic Settings (все env vars)
│   │   ├── database.py                     # AsyncEngine, Session factory
│   │   ├── security.py                     # Fernet-шифрование (EncryptionService)
│   │   ├── router.py                       # MessageRouter (оркестратор диалога)
│   │   ├── tenant.py                       # TenantManager (разрешение компании)
│   │   ├── logging_config.py              # structlog: JSON-логи, trace_id
│   │   ├── exceptions.py                   # Кастомные исключения ядра
│   │   │
│   │   ├── models/                         # SQLAlchemy ORM модели
│   │   │   ├── __init__.py                 # Re-export всех моделей
│   │   │   ├── base.py                     # DeclarativeBase + TimestampMixin
│   │   │   ├── company.py                  # Company (tenant)
│   │   │   ├── user.py                     # User (сотрудник компании)
│   │   │   ├── conversation.py             # Conversation (диалог)
│   │   │   ├── message.py                  # Message (сообщение)
│   │   │   └── integration.py              # Integration (настройки плагина)
│   │   │
│   │   └── services/                       # Бизнес-логика (сервисный слой)
│   │       ├── __init__.py
│   │       ├── company_service.py          # CompanyService (CRUD компаний)
│   │       ├── user_service.py             # UserService (get_or_create)
│   │       ├── conversation_service.py     # ConversationService (диалоги)
│   │       ├── message_service.py          # MessageService (сообщения)
│   │       └── integration_service.py      # IntegrationService (CRUD + шифрование)
│   │
│   ├── ai/                                 # AI-провайдеры (слой абстракции)
│   │   ├── __init__.py
│   │   ├── base.py                         # Абстрактный AIProvider
│   │   ├── yais.py                         # YAISResponsesProvider (Yandex AI Studio)
│   │   └── schemas.py                      # Pydantic: AIRequest, AIResponse, MessageRecord
│   │
│   ├── adapters/                           # Адаптеры мессенджеров (plug-in слой)
│   │   ├── __init__.py
│   │   ├── base.py                         # Абстрактный MessengerAdapter
│   │   └── maxx/                           # MAX Messenger адаптер
│   │       ├── __init__.py
│   │       ├── client.py                   # MaxRESTClient (HTTP к platform-api.max.ru)
│   │       ├── webhook.py                  # MaxWebhookHandler (парсинг входящих)
│   │       ├── schemas.py                  # MAX-specific Pydantic модели
│   │       └── formatting.py               # MaxMessageFormatter (Markdown/HTML)
│   │
│   ├── plugins/                            # Интеграционные плагины (Week 2, скелет Week 1)
│   │   ├── __init__.py
│   │   ├── base.py                         # Абстрактный Plugin (интерфейс)
│   │   ├── registry.py                     # PluginRegistry (загрузка manifest.yaml)
│   │   └── bitrix24/                       # Bitrix24 CRM плагин
│   │       ├── manifest.yaml               # Метаданные + tools (JSON Schema)
│   │       ├── __init__.py                 # Bitrix24Plugin
│   │       ├── client.py                   # Bitrix24RESTClient
│   │       └── tools/                      # Реализация инструментов
│   │           └── crm.py                  # crm.lead.add, crm.deal.list, crm.deal.get
│   │
│   └── api/                                # FastAPI слой (HTTP интерфейс)
│       ├── __init__.py
│       ├── app.py                          # create_app() — фабрика FastAPI
│       ├── deps.py                         # FastAPI Depends: get_db, get_router, etc.
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── webhooks.py                 # POST /api/v1/webhooks/maxx/{company_slug}
│       │   ├── health.py                   # GET /health, GET /health/ready
│       │   └── admin/                      # Админ-панель (Week 3)
│       │       ├── __init__.py
│       │       ├── companies.py
│       │       ├── integrations.py
│       │       └── logs.py
│       └── middleware/
│           ├── __init__.py
│           ├── request_id.py               # X-Request-ID генерация/извлечение
│           └── error_handler.py            # Глобальный exception handler → 500
│
├── alembic/                                # Миграции БД (Alembic async)
│   ├── env.py                              # Асинхронный env (импорт models, engine)
│   ├── script.py.mako                      # Шаблон миграций
│   └── versions/                           # Файлы миграций
│       └── 001_initial_schema.py           # Неделя 1: все 5 таблиц
│
├── tests/                                  # Тесты (pytest)
│   ├── __init__.py
│   ├── conftest.py                         # Фикстуры: test DB, async client, mock YAIS
│   ├── test_core/
│   │   ├── test_config.py                  # Загрузка Settings, env var приоритеты
│   │   ├── test_security.py                # Шифрование/дешифрование roundtrip
│   │   ├── test_tenant.py                  # TenantManager: slug → company
│   │   └── test_router.py                  # MessageRouter.process_message (unit)
│   ├── test_ai/
│   │   ├── test_yais_client.py             # YAIS: request building, response parsing
│   │   └── test_yais_schemas.py            # Pydantic валидация YAIS ответов
│   ├── test_adapters/
│   │   ├── test_maxx_client.py             # MaxRESTClient: message formatting, API calls
│   │   ├── test_maxx_webhook.py            # MaxWebhookHandler: парсинг payload
│   │   └── test_maxx_formatting.py         # MaxMessageFormatter: Markdown escaping
│   └── test_api/
│       ├── test_health.py                  # GET /health, /health/ready
│       └── test_webhooks.py                # Интеграционный: webhook → ответ
│
├── scripts/                                # Утилиты
│   ├── init_db.sh                          # Создание БД + миграции + seed
│   └── generate_key.py                     # Генерация Fernet ключа
│
├── docker/                                 # Docker конфигурация
│   ├── Dockerfile                          # Multi-stage Python 3.12 сборка
│   └── docker-compose.yml                  # app + postgres:16-pgvector + redis:7
│
├── .env.example                            # Шаблон переменных окружения
├── .gitignore
├── pyproject.toml                          # Зависимости + конфигурация инструментов
├── alembic.ini                             # Конфигурация Alembic (указывает на src/)
└── README.md                               # Описание проекта, инструкция по деплою
```

### Обоснование структуры

| Директория | Назначение | Почему здесь |
|-----------|-----------|-------------|
| `src/core/` | Ядро: модели, сервисы, роутер, тенант | Независимо от мессенджеров, AI, плагинов. Zero внешних зависимостей кроме БД |
| `src/ai/` | AI-провайдеры | В MVP один (YAIS), но архитектура позволяет добавить OpenAI-совместимые позже |
| `src/adapters/` | Адаптеры мессенджеров | Каждый мессенджер — подпакет. Интерфейс `MessengerAdapter` гарантирует заменяемость |
| `src/plugins/` | Интеграционные плагины | Каждый плагин — подпакет с `manifest.yaml`. PluginRegistry загружает в рантайме |
| `src/api/` | HTTP слой | FastAPI routes, deps, middleware. Отдельно от ядра — можно заменить веб-фреймворк |
| `alembic/` | Миграции | Стандартный путь. Async env в `env.py` |
| `tests/` | Тесты | Зеркалит структуру `src/`. `conftest.py` с фикстурами |
| `docker/` | Инфраструктура | `Dockerfile` для продакшена. `docker-compose.yml` для локальной разработки |

---

## 2. Database Schema

### 2.1. Схема БД (PostgreSQL 16)

```
┌──────────────────────────────────────────────────────────────────────┐
│                           companies                                   │
├──────────────────────────────────────────────────────────────────────┤
│ id            UUID PRIMARY KEY DEFAULT gen_random_uuid()              │
│ name          VARCHAR(255) NOT NULL                                   │
│ slug          VARCHAR(100) UNIQUE NOT NULL                            │
│ is_active     BOOLEAN DEFAULT TRUE                                    │
│ settings      JSONB DEFAULT '{}'::jsonb                               │
│ created_at    TIMESTAMPTZ DEFAULT now()                               │
└───────────────────────┬──────────────────────────────────────────────┘
                        │ 1:N
        ┌───────────────┼───────────────┬──────────────────┐
        ▼               ▼               ▼                  ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
│    users     │ │ conversations│ │ integrations │ │   documents  (*) │
├──────────────┤ ├──────────────┤ ├──────────────┤ │   Week 3         │
│ id       UUID│ │ id       UUID│ │ id       UUID│ └──────────────────┘
│ company_id   │ │ company_id   │ │ company_id   │
│      FK→comp │ │      FK→comp │ │      FK→comp │
│ messenger    │ │ user_id      │ │ plugin_name  │
│ msg_user_id  │ │      FK→user │ │ config  TEXT │ (*) RAG:
│ first_name   │ │ messenger    │ │   ENCRYPTED  │ documents,
│ last_name    │ │ msg_chat_id  │ │ enabled  BOOL│ document_chunks
│ username     │ │ prev_resp_id │ │ created_at   │ with pgvector
│ phone        │ │ status       │ │ updated_at   │
│ role         │ │ started_at   │ │ UNIQUE(comp, │
│ created_at   │ │ last_msg_at  │ │   plugin)    │
│ UNIQUE(comp, │ └──────┬───────┘ └──────────────┘
│  msg,user)   │        │ 1:N
└──────────────┘        ▼
               ┌──────────────┐
               │   messages   │
               ├──────────────┤
               │ id       UUID│
               │ conv_id  UUID│
               │      FK→conv │
               │ role VARCHAR │  user|assistant|tool|system
               │ content TEXT │
               │ tool_calls   │  JSONB (function_call array)
               │ tool_call_id │  VARCHAR (для tool-сообщений)
               │ metadata     │  JSONB (usage, timing, etc.)
               │ created_at   │
               └──────────────┘
```

### 2.2. SQLAlchemy модели (файлы и колонки)

#### `src/core/models/base.py`

```python
# Импорт:
#   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
#   from sqlalchemy import DateTime, func
#   from datetime import datetime

class Base(DeclarativeBase):
    """Базовый класс для всех ORM моделей."""
    pass

class TimestampMixin:
    """Mixin для created_at."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

#### `src/core/models/company.py`

```python
# Класс: Company(Base, TimestampMixin)
# Таблица: companies

# Колонки:
#   id:            Mapped[uuid.UUID]  PK, default=uuid4
#   name:          Mapped[str]        String(255), nullable=False
#   slug:          Mapped[str]        String(100), unique=True, nullable=False, index=True
#   is_active:     Mapped[bool]       Boolean, default=True
#   settings:      Mapped[dict]       JSONB, default=dict
#   created_at:    наследуется из TimestampMixin

# Relationships:
#   users:          relationship("User", back_populates="company", lazy="selectin")
#   conversations:  relationship("Conversation", back_populates="company", lazy="selectin")
#   integrations:   relationship("Integration", back_populates="company", lazy="selectin")

# Методы:
#   __repr__() → f"<Company {self.slug}>"
```

#### `src/core/models/user.py`

```python
# Класс: User(Base, TimestampMixin)
# Таблица: users

# Колонки:
#   id:                Mapped[uuid.UUID]  PK, default=uuid4
#   company_id:        Mapped[uuid.UUID]  FK → companies.id, NOT NULL, index=True
#   messenger:         Mapped[str]        String(50), NOT NULL      # "maxx" | "telegram" | "vk"
#   messenger_user_id: Mapped[str]        String(255), NOT NULL     # ID пользователя в мессенджере
#   first_name:        Mapped[Optional[str]] String(255), nullable=True
#   last_name:         Mapped[Optional[str]] String(255), nullable=True
#   username:          Mapped[Optional[str]] String(255), nullable=True
#   phone:             Mapped[Optional[str]] String(50), nullable=True
#   role:              Mapped[str]        String(50), default="user" # "user" | "admin"
#   created_at:        наследуется

# Constraints:
#   __table_args__ = (UniqueConstraint("company_id", "messenger", "messenger_user_id",
#                                       name="uq_user_messenger"),)

# Relationships:
#   company:       relationship("Company", back_populates="users")
#   conversations: relationship("Conversation", back_populates="user")

# Методы:
#   __repr__() → f"<User {self.messenger}:{self.messenger_user_id}>"
```

#### `src/core/models/conversation.py`

```python
# Класс: Conversation(Base)
# Таблица: conversations

# Колонки:
#   id:                  Mapped[uuid.UUID]  PK, default=uuid4
#   company_id:          Mapped[uuid.UUID]  FK → companies.id, NOT NULL, index=True
#   user_id:             Mapped[uuid.UUID]  FK → users.id, NOT NULL
#   messenger:           Mapped[str]        String(50), NOT NULL
#   messenger_chat_id:   Mapped[str]        String(255), NOT NULL  # ID чата в мессенджере
#   previous_response_id:Mapped[Optional[str]] String(255), nullable=True  # YAIS multi-turn
#   status:              Mapped[str]        String(50), default="active"  # active|closed|archived
#   started_at:          Mapped[datetime]   DateTime(tz=True), server_default=func.now()
#   last_message_at:     Mapped[datetime]   DateTime(tz=True), server_default=func.now(),
#                                           onupdate=func.now()

# Relationships:
#   company:  relationship("Company", back_populates="conversations")
#   user:     relationship("User", back_populates="conversations")
#   messages: relationship("Message", back_populates="conversation", order_by="Message.created_at")

# Методы:
#   __repr__() → f"<Conversation {self.id} [{self.status}]>"
```

#### `src/core/models/message.py`

```python
# Класс: Message(Base)
# Таблица: messages

# Колонки:
#   id:              Mapped[uuid.UUID]  PK, default=uuid4
#   conversation_id: Mapped[uuid.UUID]  FK → conversations.id, NOT NULL, index=True
#   role:            Mapped[str]        String(20), NOT NULL  # user|assistant|tool|system
#   content:         Mapped[Optional[str]] Text, nullable=True
#   tool_calls:      Mapped[Optional[dict]] JSONB, nullable=True
#                                       # Массив: [{"call_id": "..", "name": "..", "arguments": {..}}]
#   tool_call_id:    Mapped[Optional[str]] String(255), nullable=True
#                                       # ID вызова (для role="tool")
#   metadata_:       Mapped[Optional[dict]] "metadata", JSONB, nullable=True
#                                       # {"usage": {...}, "model": "...", "latency_ms": 123}
#   created_at:      Mapped[datetime]   DateTime(tz=True), server_default=func.now()

# Relationships:
#   conversation: relationship("Conversation", back_populates="messages")

# Методы:
#   __repr__() → f"<Message {self.role} @ {self.created_at}>"
```

#### `src/core/models/integration.py`

```python
# Класс: Integration(Base)
# Таблица: integrations

# Колонки:
#   id:           Mapped[uuid.UUID]  PK, default=uuid4
#   company_id:   Mapped[uuid.UUID]  FK → companies.id, NOT NULL, index=True
#   plugin_name:  Mapped[str]        String(100), NOT NULL  # "bitrix24" | "amocrm" | "maxx" | "yais"
#   config:       Mapped[str]        Text, NOT NULL
#                                    # Fernet-encrypted JSON: {"webhook_url": "...", "api_key": "..."}
#   enabled:      Mapped[bool]       Boolean, default=False
#   created_at:   Mapped[datetime]   DateTime(tz=True), server_default=func.now()
#   updated_at:   Mapped[datetime]   DateTime(tz=True), server_default=func.now(),
#                                    onupdate=func.now()

# Constraints:
#   __table_args__ = (UniqueConstraint("company_id", "plugin_name",
#                                       name="uq_company_plugin"),)

# Relationships:
#   company: relationship("Company", back_populates="integrations")

# Методы:
#   __repr__() → f"<Integration {self.plugin_name} [{self.company_id}]>"
```

### 2.3. Индексы и производительность

| Таблица | Индекс | Тип | Назначение |
|---------|--------|-----|------------|
| `companies` | `companies_slug_key` | UNIQUE BTREE | Поиск компании по slug (вебхук URL) |
| `users` | `uq_user_messenger` | UNIQUE BTREE (company_id, messenger, messenger_user_id) | get_or_create пользователя |
| `users` | `ix_users_company_id` | BTREE | Фильтр по компании |
| `conversations` | `ix_conversations_company_id` | BTREE | Фильтр по компании |
| `conversations` | `ix_conversations_user_id` | BTREE | Диалоги пользователя |
| `messages` | `ix_messages_conversation_id` | BTREE | История диалога, ORDER BY created_at |
| `integrations` | `uq_company_plugin` | UNIQUE BTREE (company_id, plugin_name) | Поиск интеграции компании |

---

## 3. Configuration Design

### 3.1. Environment Variables (полный список)

Все переменные имеют префикс `MULTIBOT_`. Загружаются через `pydantic-settings` из `.env` файла и/или окружения.

```bash
# ============================
# Приложение
# ============================
MULTIBOT_ENV=development                # development | production | test
MULTIBOT_DEBUG=true                     # Включает детальные трейсбеки в ответах
MULTIBOT_LOG_LEVEL=INFO                 # DEBUG | INFO | WARNING | ERROR
MULTIBOT_LOG_FORMAT=json                # json | console (для разработки)

# ============================
# Сервер
# ============================
MULTIBOT_HOST=0.0.0.0
MULTIBOT_PORT=8000
MULTIBOT_WEBHOOK_BASE_URL=              # https://example.com — для регистрации вебхуков MAX
                                         # (в dev: ngrok URL в .env.local)

# ============================
# База данных
# ============================
MULTIBOT_DATABASE_URL=postgresql+asyncpg://multibot:multibot@localhost:5432/multibot
# Формат: postgresql+asyncpg://user:pass@host:port/dbname
# Для тестов: postgresql+asyncpg://multibot:multibot@localhost:5432/multibot_test

# ============================
# Шифрование (EncryptionService)
# ============================
MULTIBOT_ENCRYPTION_KEY=                # Fernet ключ (base64, 32 байта)
# Если пусто при первом запуске — генерируется автоматически, выводится в лог.
# В production ОБЯЗАТЕЛЬНО задать вручную и хранить в secrets manager.
# Сгенерировать: python scripts/generate_key.py

# ============================
# Yandex AI Studio (YAIS)
# ============================
MULTIBOT_YAIS_API_KEY=t1.9euelZ...     # IAM токен или API-ключ Yandex Cloud
MULTIBOT_YAIS_FOLDER_ID=b1g...          # ID каталога Yandex Cloud
MULTIBOT_YAIS_BASE_URL=https://ai.api.yandexcloud.net
MULTIBOT_YAIS_PRIMARY_MODEL=gpt://{folder}/gpt-oss-20b/latest
MULTIBOT_YAIS_FALLBACK_MODEL=yandexgpt-5-lite
MULTIBOT_YAIS_EMBEDDING_MODEL=text-embeddings-v2

# ============================
# MAX Messenger (платформенный default, для тестов)
# ============================
MULTIBOT_MAX_DEFAULT_BOT_TOKEN=         # Токен бота MAX для разработки/тестов
# В production: токены хранятся в integrations.config (зашифровано) per company

# ============================
# Лимиты и таймауты
# ============================
MULTIBOT_CONVERSATION_HISTORY_LIMIT=20       # Сколько сообщений передавать в AI
MULTIBOT_TOOL_CALL_MAX_ITERATIONS=5          # Макс. цепочка function_call → результат → AI
MULTIBOT_AI_REQUEST_TIMEOUT_SECONDS=30       # Таймаут HTTP-запроса к YAIS
MULTIBOT_MESSENGER_SEND_TIMEOUT_SECONDS=10   # Таймаут отправки сообщения в мессенджер
```

### 3.2. Класс Settings

Файл: `src/core/config.py`

```python
# Импорт:
#   from pydantic_settings import BaseSettings, SettingsConfigDict
#   from pydantic import Field, field_validator
#   from cryptography.fernet import Fernet

# Класс:
#   Settings(BaseSettings)
#
#   model_config = SettingsConfigDict(
#       env_prefix="MULTIBOT_",
#       env_file=".env",
#       env_file_encoding="utf-8",
#       extra="ignore",          # Игнорировать неизвестные переменные
#   )
#
# Поля (все как в секции 3.1):
#   - env: str = "development"
#   - debug: bool = False
#   - log_level: str = "INFO"
#   - log_format: str = "json"
#   - host: str = "0.0.0.0"
#   - port: int = 8000
#   - webhook_base_url: str = ""
#   - database_url: str = "postgresql+asyncpg://multibot:multibot@localhost:5432/multibot"
#   - encryption_key: str = ""      # Если пусто → автогенерация
#   - yais_api_key: str = ""
#   - yais_folder_id: str = ""
#   - yais_base_url: str = "https://ai.api.yandexcloud.net"
#   - yais_primary_model: str = ""
#   - yais_fallback_model: str = "yandexgpt-5-lite"
#   - yais_embedding_model: str = "text-embeddings-v2"
#   - max_default_bot_token: str = ""
#   - conversation_history_limit: int = 20
#   - tool_call_max_iterations: int = 5
#   - ai_request_timeout_seconds: int = 30
#   - messenger_send_timeout_seconds: int = 10
#
# Методы:
#   get_encryption_key() → bytes:
#       Если encryption_key пуст: сгенерировать Fernet.generate_key(),
#       вывести в лог WARNING "Generated new encryption key: {key}",
#       сохранить в self.encryption_key (для runtime).
#       Вернуть key как bytes (base64-decode если строка).
#
#   get_yais_model_url() → str:
#       Подставить folder_id в модель:
#       return self.yais_primary_model.format(folder=self.yais_folder_id)
#       # → "gpt://b1g.../gpt-oss-20b/latest"
```

### 3.3. Иерархия загрузки конфигурации

```
1. Значения по умолчанию (в классе Settings)
2. .env файл в корне проекта
3. Переменные окружения (MULTIBOT_*)
4. .env.local (для разработки, не коммитится, загружается вручную при необходимости)
```

Приоритет: переменные окружения > `.env` > defaults.

---

## 4. Detailed Week 1 Task Breakdown

---

### TASK 1: Project Initialization

**Цель:** Скелет проекта, FastAPI приложение поднимается, БД подключается, `GET /health` отвечает 200.

**Время:** ~3–4 часа

**Проверка:** `curl localhost:8000/health` → `{"status": "ok"}`

#### Файлы и их содержимое

---

**Файл 1:** `pyproject.toml`

```toml
[project]
name = "multibot"
version = "0.1.0"
description = "MultiBot — мультимессенджерная AI-платформа для бизнеса"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115,<0.116",
    "uvicorn[standard]>=0.34,<0.35",
    "sqlalchemy[asyncio]>=2.0,<2.1",
    "asyncpg>=0.30,<0.31",
    "alembic>=1.14,<1.15",
    "pydantic-settings>=2.7,<2.8",
    "httpx>=0.28,<0.29",
    "pyyaml>=6.0,<7.0",
    "cryptography>=44.0,<45.0",
    "structlog>=24.0,<25.0",
    "python-dotenv>=1.0,<2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0,<9.0",
    "pytest-asyncio>=0.25,<0.26",
    "pytest-cov>=6.0,<7.0",
    "httpx-mock>=0.12,<0.13",
    "ruff>=0.8,<1.0",
    "mypy>=1.14,<1.15",
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

---

**Файл 2:** `.env.example`

```bash
MULTIBOT_ENV=development
MULTIBOT_DEBUG=true
MULTIBOT_LOG_LEVEL=INFO
MULTIBOT_DATABASE_URL=postgresql+asyncpg://multibot:multibot@localhost:5432/multibot
MULTIBOT_ENCRYPTION_KEY=
MULTIBOT_YAIS_API_KEY=
MULTIBOT_YAIS_FOLDER_ID=
MULTIBOT_YAIS_PRIMARY_MODEL=gpt://{folder}/gpt-oss-20b/latest
MULTIBOT_WEBHOOK_BASE_URL=
MULTIBOT_MAX_DEFAULT_BOT_TOKEN=
```

---

**Файл 3:** `.gitignore`

```
.env
.env.local
__pycache__/
*.pyc
.venv/
venv/
*.egg-info/
dist/
.pytest_cache/
.mypy_cache/
.ruff_cache/
htmlcov/
coverage.xml
*.log
data/
```

---

**Файл 4:** `docker/Dockerfile`

```dockerfile
# Multi-stage build
FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY src/ ./src/
COPY alembic.ini .
COPY alembic/ ./alembic/
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

**Файл 5:** `docker/docker-compose.yml`

```yaml
# Зависимости для локальной разработки
version: "3.9"
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: multibot
      POSTGRES_USER: multibot
      POSTGRES_PASSWORD: multibot
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  pgdata:
```

---

**Файл 6:** `src/__init__.py`

```python
"""MultiBot — мультимессенджерная AI-платформа для бизнеса."""
```

---

**Файл 7:** `src/core/__init__.py`

```python
"""Core engine: config, database, models, services, router."""
```

---

**Файл 8:** `src/core/config.py` — Класс `Settings`

```python
# Импорты:
#   from pydantic_settings import BaseSettings, SettingsConfigDict
#   from cryptography.fernet import Fernet
#   import logging

# Класс Settings(BaseSettings):
#   model_config = SettingsConfigDict(
#       env_prefix="MULTIBOT_",
#       env_file=".env",
#       env_file_encoding="utf-8",
#       extra="ignore",
#   )
#
#   env: str = "development"
#   debug: bool = False
#   log_level: str = "INFO"
#   log_format: str = "json"
#   host: str = "0.0.0.0"
#   port: int = 8000
#   webhook_base_url: str = ""
#   database_url: str = "postgresql+asyncpg://multibot:multibot@localhost:5432/multibot"
#   encryption_key: str = ""
#   yais_api_key: str = ""
#   yais_folder_id: str = ""
#   yais_base_url: str = "https://ai.api.yandexcloud.net"
#   yais_primary_model: str = ""
#   yais_fallback_model: str = "yandexgpt-5-lite"
#   yais_embedding_model: str = "text-embeddings-v2"
#   max_default_bot_token: str = ""
#   conversation_history_limit: int = 20
#   tool_call_max_iterations: int = 5
#   ai_request_timeout_seconds: int = 30
#   messenger_send_timeout_seconds: int = 10
#
#   def get_encryption_key(self) -> bytes:
#       logger = logging.getLogger(__name__)
#       if not self.encryption_key:
#           key = Fernet.generate_key()
#           logger.warning(
#               "ENCRYPTION_KEY not set. Generated temporary key. "
#               "Set MULTIBOT_ENCRYPTION_KEY in production!"
#           )
#           self.encryption_key = key.decode("utf-8")
#       return self.encryption_key.encode("utf-8") if isinstance(self.encryption_key, str) else self.encryption_key
#
#   def get_yais_model_url(self) -> str:
#       return self.yais_primary_model.format(folder=self.yais_folder_id)
#
#   def get_yais_fallback_model_url(self) -> str:
#       return self.yais_fallback_model

# Глобальный синглтон:
# settings = Settings()
```

---

**Файл 9:** `src/core/database.py` — Engine и сессии

```python
# Импорты:
#   from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine
#   from src.core.config import settings

# Функции:
#   create_engine(database_url: str | None = None) → AsyncEngine:
#       url = database_url or settings.database_url
#       return create_async_engine(url, echo=settings.debug, pool_size=10, max_overflow=20)

#   create_session_factory(engine: AsyncEngine | None = None) → async_sessionmaker[AsyncSession]:
#       _engine = engine or create_engine()
#       return async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)

#   async def get_session() → AsyncGenerator[AsyncSession, None]:
#       """FastAPI dependency. Yield async session."""
#       async with _session_factory() as session:
#           yield session

#   async def init_db(engine: AsyncEngine) → None:
#       """Create all tables (dev only; use alembic in production)."""
#       from src.core.models.base import Base
#       async with engine.begin() as conn:
#           await conn.run_sync(Base.metadata.create_all)

#   async def check_db_connection(engine: AsyncEngine) -> bool:
#       """Health check: can we connect to DB?"""
#       try:
#           async with engine.connect() as conn:
#               await conn.execute(text("SELECT 1"))
#           return True
#       except Exception:
#           return False

# Ленивая инициализация (создаётся при первом вызове):
#   _engine: AsyncEngine | None = None
#   _session_factory: async_sessionmaker[AsyncSession] | None = None
```

---

**Файл 10:** `src/core/logging_config.py` — structlog

```python
# Импорты:
#   import structlog
#   from src.core.config import settings

# Функция:
#   def setup_logging() -> None:
#       """Configure structlog with JSON rendering."""
#       shared_processors = [
#           structlog.contextvars.merge_contextvars,
#           structlog.processors.add_log_level,
#           structlog.processors.TimeStamper(fmt="iso"),
#       ]
#       if settings.log_format == "json":
#           structlog.configure(
#               processors=shared_processors + [structlog.processors.JSONRenderer()],
#               wrapper_class=structlog.make_filtering_bound_logger(
#                   getattr(logging, settings.log_level)
#               ),
#           )
#       else:
#           structlog.configure(
#               processors=shared_processors + [structlog.dev.ConsoleRenderer()],
#               wrapper_class=structlog.make_filtering_bound_logger(
#                   getattr(logging, settings.log_level)
#               ),
#           )

#   def get_logger(name: str) → structlog.BoundLogger:
#       return structlog.get_logger(name)
```

---

**Файл 11:** `src/core/exceptions.py` — Кастомные исключения

```python
# Классы:
#   class MultiBotError(Exception):
#       """Base exception for MultiBot."""
#       def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
#           self.message = message
#           self.code = code
#           super().__init__(message)
#
#   class TenantNotFoundError(MultiBotError):
#       """Company not found by slug."""
#       code = "TENANT_NOT_FOUND"
#
#   class TenantInactiveError(MultiBotError):
#       """Company is deactivated."""
#       code = "TENANT_INACTIVE"
#
#   class AIProviderError(MultiBotError):
#       """Base for AI provider errors."""
#       code = "AI_PROVIDER_ERROR"
#
#   class AITimeoutError(AIProviderError):
#       code = "AI_TIMEOUT"
#
#   class AIRateLimitError(AIProviderError):
#       code = "AI_RATE_LIMIT"
#
#   class AIAuthError(AIProviderError):
#       code = "AI_AUTH_ERROR"
#
#   class MessengerError(MultiBotError):
#       """Base for messenger errors."""
#       code = "MESSENGER_ERROR"
#
#   class MessengerSendError(MessengerError):
#       code = "MESSENGER_SEND_ERROR"
#
#   class PluginError(MultiBotError):
#       """Base for plugin errors."""
#       code = "PLUGIN_ERROR"
#
#   class ToolExecutionError(PluginError):
#       code = "TOOL_EXECUTION_ERROR"
```

---

**Файл 12:** `src/api/__init__.py`

```python
"""FastAPI application layer."""
```

---

**Файл 13:** `src/api/app.py` — Фабрика FastAPI приложения

```python
# Импорты:
#   from fastapi import FastAPI
#   from src.core.config import Settings
#   from src.api.routes.health import router as health_router
#   from src.api.middleware.request_id import RequestIDMiddleware
#   from src.api.middleware.error_handler import register_error_handlers

# Функция:
#   def create_app(settings: Settings) → FastAPI:
#       app = FastAPI(
#           title="MultiBot",
#           version="0.1.0",
#           description="Мультимессенджерная AI-платформа для бизнеса",
#           docs_url="/docs" if settings.debug else None,
#       )
#       # Middleware
#       app.add_middleware(RequestIDMiddleware)
#       # Error handlers
#       register_error_handlers(app)
#       # Routes
#       app.include_router(health_router, tags=["health"])
#       # State
#       app.state.settings = settings
#       return app
```

---

**Файл 14:** `src/api/routes/__init__.py`

```python
"""API route modules."""
```

---

**Файл 15:** `src/api/routes/health.py` — Health endpoints

```python
# Импорты:
#   from fastapi import APIRouter, Depends
#   from sqlalchemy.ext.asyncio import AsyncSession
#   from src.core.database import check_db_connection, create_engine

# router = APIRouter()

# @router.get("/health")
# async def health_check() → dict:
#     """Liveness probe. Always returns 200 if app is running."""
#     return {"status": "ok", "version": "0.1.0"}

# @router.get("/health/ready")
# async def readiness_check() → dict:
#     """Readiness probe. Checks DB connectivity."""
#     engine = create_engine()
#     db_ok = await check_db_connection(engine)
#     status_code = 200 if db_ok else 503
#     return JSONResponse(
#         content={"status": "ready" if db_ok else "not_ready", "database": db_ok},
#         status_code=status_code,
#     )
```

---

**Файл 16:** `src/api/deps.py` — FastAPI зависимости

```python
# Импорты:
#   from fastapi import Depends
#   from sqlalchemy.ext.asyncio import AsyncSession
#   from src.core.database import get_session

# Функции:
#   async def get_db() → AsyncGenerator[AsyncSession, None]:
#       """Yield a database session. Automatically closed after request."""
#       async for session in get_session():
#           yield session
```

---

**Файл 17:** `src/api/middleware/__init__.py`

```python
"""FastAPI middleware modules."""
```

---

**Файл 18:** `src/api/middleware/request_id.py` — Request ID

```python
# Импорты:
#   from starlette.middleware.base import BaseHTTPMiddleware
#   from starlette.requests import Request
#   from starlette.responses import Response
#   import uuid
#   import structlog

# Класс:
#   class RequestIDMiddleware(BaseHTTPMiddleware):
#       """Inject X-Request-ID header and bind to structlog context."""
#       async def dispatch(self, request: Request, call_next) -> Response:
#           request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
#           structlog.contextvars.bind_contextvars(request_id=request_id)
#           response = await call_next(request)
#           response.headers["X-Request-ID"] = request_id
#           structlog.contextvars.unbind_contextvars("request_id")
#           return response
```

---

**Файл 19:** `src/api/middleware/error_handler.py` — Глобальный обработчик ошибок

```python
# Импорты:
#   from fastapi import FastAPI, Request
#   from fastapi.responses import JSONResponse
#   import structlog

# Функция:
#   def register_error_handlers(app: FastAPI) -> None:
#       logger = structlog.get_logger(__name__)
#
#       @app.exception_handler(Exception)
#       async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
#           logger.error("Unhandled exception", exc_info=exc, path=request.url.path)
#           return JSONResponse(
#               status_code=500,
#               content={"error": "INTERNAL_ERROR", "message": "Внутренняя ошибка сервера"},
#           )
```

---

**Файл 20:** `src/main.py` — Точка входа

```python
# Импорты:
#   import uvicorn
#   from src.core.config import settings
#   from src.core.logging_config import setup_logging
#   from src.api.app import create_app

# setup_logging()
# app = create_app(settings)

# if __name__ == "__main__":
#     uvicorn.run(
#         "src.main:app",
#         host=settings.host,
#         port=settings.port,
#         reload=settings.debug,
#         log_level=settings.log_level.lower(),
#     )
```

---

**Файл 21:** `alembic.ini`

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
sqlalchemy.url = driver://user:pass@localhost/dbname
# Заменяется в env.py на значение из settings

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

---

**Файл 22:** `alembic/env.py`

```python
# Асинхронный env для Alembic:
# Импортирует src.core.models.base.Base и все модели
# Использует src.core.database.create_engine() для получения AsyncEngine
# run_migrations_online() → async with engine.connect() as conn: ...
# target_metadata = Base.metadata
```

---

**Файл 23:** `src/core/models/base.py`

См. секцию 2.2 — класс `Base` (DeclarativeBase) и `TimestampMixin`.

---

**Файл 24:** `README.md` — обновить существующий

```markdown
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
```

---

### TASK 2: Multi-tenant Model

**Цель:** ORM-модели (5 таблиц), миграция, сервисный слой с CRUD, шифрование API-ключей.

**Время:** ~5–6 часов

**Проверка:** `alembic upgrade head` создаёт таблицы. Тесты: создать компанию → пользователя → диалог → сообщение → интеграцию с зашифрованным конфигом.

#### Файлы

---

**Файл 25:** `src/core/models/company.py` — `Company`

См. секцию 2.2.

```python
# Класс Company(Base, TimestampMixin)
# Таблица: companies
# Колонки: id, name, slug(unique, index), is_active, settings(JSONB), created_at
# Relationships: users, conversations, integrations (lazy="selectin")
```

---

**Файл 26:** `src/core/models/user.py` — `User`

См. секцию 2.2.

```python
# Класс User(Base, TimestampMixin)
# Таблица: users
# Колонки: id, company_id(FK), messenger, messenger_user_id,
#          first_name?, last_name?, username?, phone?, role, created_at
# Constraints: UniqueConstraint(company_id, messenger, messenger_user_id)
# Relationships: company, conversations
```

---

**Файл 27:** `src/core/models/conversation.py` — `Conversation`

См. секцию 2.2.

```python
# Класс Conversation(Base)
# Таблица: conversations
# Колонки: id, company_id(FK), user_id(FK), messenger, messenger_chat_id,
#          previous_response_id?, status, started_at, last_message_at
# Relationships: company, user, messages
```

---

**Файл 28:** `src/core/models/message.py` — `Message`

См. секцию 2.2.

```python
# Класс Message(Base)
# Таблица: messages
# Колонки: id, conversation_id(FK), role, content?, tool_calls?(JSONB),
#          tool_call_id?, metadata_?(JSONB, поле "metadata"), created_at
# Relationships: conversation
```

---

**Файл 29:** `src/core/models/integration.py` — `Integration`

См. секцию 2.2.

```python
# Класс Integration(Base)
# Таблица: integrations
# Колонки: id, company_id(FK), plugin_name, config(TEXT, encrypted JSON),
#          enabled, created_at, updated_at
# Constraints: UniqueConstraint(company_id, plugin_name)
# Relationships: company
```

---

**Файл 30:** `src/core/models/__init__.py` — Re-export всех моделей

```python
# from src.core.models.base import Base, TimestampMixin
# from src.core.models.company import Company
# from src.core.models.user import User
# from src.core.models.conversation import Conversation
# from src.core.models.message import Message
# from src.core.models.integration import Integration

# __all__ = ["Base", "TimestampMixin", "Company", "User", "Conversation", "Message", "Integration"]
```

---

**Файл 31:** `src/core/security.py` — `EncryptionService`

```python
# Импорты:
#   from cryptography.fernet import Fernet, InvalidToken
#   import json
#   from typing import Any

# Класс EncryptionService:
#   """Fernet-based symmetric encryption for API keys at rest.
#   Использует AES-128-CBC + HMAC (через cryptography.fernet).
#   """
#
#   def __init__(self, key: bytes) -> None:
#       """key: 32-byte url-safe base64-encoded Fernet key."""
#       self._fernet = Fernet(key)
#
#   def encrypt(self, data: dict[str, Any]) -> str:
#       """Encrypt dict to base64 string.
#       >>> svc.encrypt({"webhook_url": "https://..."})
#       'gAAAAAB...'
#       """
#       json_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")
#       token = self._fernet.encrypt(json_bytes)
#       return token.decode("utf-8")
#
#   def decrypt(self, token: str) -> dict[str, Any]:
#       """Decrypt base64 string back to dict.
#       Raises: ValueError if token is invalid or tampered with.
#       """
#       try:
#           json_bytes = self._fernet.decrypt(token.encode("utf-8"))
#           return json.loads(json_bytes)
#       except InvalidToken as e:
#           raise ValueError("Invalid or corrupted encrypted token") from e
#
#   @staticmethod
#   def generate_key() -> bytes:
#       """Generate a new Fernet key."""
#       return Fernet.generate_key()
```

---

**Файл 32:** `src/core/tenant.py` — `TenantManager`

```python
# Импорты:
#   from sqlalchemy.ext.asyncio import AsyncSession
#   from sqlalchemy import select
#   from src.core.models.company import Company
#   from src.core.exceptions import TenantNotFoundError, TenantInactiveError

# Класс TenantManager:
#   """Resolves company (tenant) by slug for multi-tenant isolation."""
#
#   def __init__(self, session: AsyncSession) -> None:
#       self.session = session
#
#   async def get_by_slug(self, slug: str) -> Company:
#       """Find active company by slug. Raises TenantNotFoundError if not found,
#       TenantInactiveError if is_active=False."""
#       result = await self.session.execute(
#           select(Company).where(Company.slug == slug)
#       )
#       company = result.scalar_one_or_none()
#       if company is None:
#           raise TenantNotFoundError(f"Company with slug '{slug}' not found")
#       if not company.is_active:
#           raise TenantInactiveError(f"Company '{slug}' is deactivated")
#       return company
#
#   async def get_active_companies(self) -> list[Company]:
#       """Return all active companies."""
#       result = await self.session.execute(
#           select(Company).where(Company.is_active == True)
#       )
#       return list(result.scalars().all())
```

---

**Файлы 33–37:** Сервисный слой — `src/core/services/`

#### `src/core/services/__init__.py`

```python
# Re-export:
# from src.core.services.company_service import CompanyService
# from src.core.services.user_service import UserService
# from src.core.services.conversation_service import ConversationService
# from src.core.services.message_service import MessageService
# from src.core.services.integration_service import IntegrationService
```

#### `src/core/services/company_service.py` — `CompanyService`

```python
# Импорты: AsyncSession, select, Company
# Класс CompanyService:
#   def __init__(self, session: AsyncSession) -> None
#
#   async def create(self, name: str, slug: str, settings: dict | None = None) -> Company
#   async def get_by_id(self, company_id: uuid.UUID) -> Company | None
#   async def get_by_slug(self, slug: str) -> Company | None
#   async def list_active(self) -> list[Company]
#   async def update_settings(self, company_id: uuid.UUID, settings: dict) -> Company
#   async def deactivate(self, company_id: uuid.UUID) -> None
```

#### `src/core/services/user_service.py` — `UserService`

```python
# Импорты: AsyncSession, select, User
# Класс UserService:
#   def __init__(self, session: AsyncSession) -> None
#
#   async def get_or_create(
#       self,
#       company_id: uuid.UUID,
#       messenger: str,
#       messenger_user_id: str,
#       extra: dict | None = None,  # first_name, last_name, username
#   ) -> User:
#       """Find existing user or create new one. Thread-safe via unique constraint."""
#       # Пытается найти → если нет, создаёт с обработкой IntegrityError (race condition)
#
#   async def get_by_id(self, user_id: uuid.UUID) -> User | None
#   async def list_by_company(self, company_id: uuid.UUID) -> list[User]
```

#### `src/core/services/conversation_service.py` — `ConversationService`

```python
# Импорты: AsyncSession, select, Conversation
# Класс ConversationService:
#   def __init__(self, session: AsyncSession) -> None
#
#   async def get_or_create_active(
#       self,
#       company_id: uuid.UUID,
#       user_id: uuid.UUID,
#       messenger: str,
#       messenger_chat_id: str,
#   ) -> Conversation:
#       """Find active conversation or create new one."""
#
#   async def get_by_id(self, conv_id: uuid.UUID) -> Conversation | None
#   async def update_previous_response_id(self, conv_id: uuid.UUID, response_id: str) -> None
#   async def touch_last_message(self, conv_id: uuid.UUID) -> None  # обновить last_message_at
#   async def close_conversation(self, conv_id: uuid.UUID) -> None
```

#### `src/core/services/message_service.py` — `MessageService`

```python
# Импорты: AsyncSession, select, Message
# Класс MessageService:
#   def __init__(self, session: AsyncSession) -> None
#
#   async def create(
#       self,
#       conversation_id: uuid.UUID,
#       role: str,                     # user|assistant|tool|system
#       content: str | None = None,
#       tool_calls: list[dict] | None = None,
#       tool_call_id: str | None = None,
#       metadata: dict | None = None,
#   ) -> Message
#
#   async def get_conversation_history(
#       self,
#       conversation_id: uuid.UUID,
#       limit: int = 20,
#   ) -> list[Message]:
#       """Last N messages, ordered by created_at ASC."""
#
#   async def get_last_messages(
#       self,
#       conversation_id: uuid.UUID,
#       limit: int = 20,
#   ) -> list[Message]:
#       """Get last N messages for AI context."""
```

#### `src/core/services/integration_service.py` — `IntegrationService`

```python
# Импорты: AsyncSession, select, Integration, EncryptionService
# Класс IntegrationService:
#   def __init__(self, session: AsyncSession, encryption: EncryptionService) -> None
#
#   async def save_config(
#       self, company_id: uuid.UUID, plugin_name: str, config: dict, enabled: bool = True
#   ) -> Integration:
#       """Encrypt config dict and upsert integration record."""
#
#   async def get_config(self, company_id: uuid.UUID, plugin_name: str) -> dict | None:
#       """Decrypt and return config dict. None if not found or disabled."""
#
#   async def get_raw_config(self, company_id: uuid.UUID, plugin_name: str) -> dict | None:
#       """Return config for enabled integration or None."""
#
#   async def disable(self, company_id: uuid.UUID, plugin_name: str) -> None
#   async def enable(self, company_id: uuid.UUID, plugin_name: str) -> None
#   async def delete(self, company_id: uuid.UUID, plugin_name: str) -> None
```

---

**Файл 38:** `alembic/versions/001_initial_schema.py` — Миграция (генерируется автогенерацией)

Команда: `alembic revision --autogenerate -m "initial_schema"`

Создаёт таблицы: `companies`, `users`, `conversations`, `messages`, `integrations` со всеми индексами и внешними ключами.

---

**Файл 39:** `scripts/generate_key.py`

```python
"""Генерация Fernet ключа для MULTIBOT_ENCRYPTION_KEY."""
from cryptography.fernet import Fernet

def main() -> None:
    key = Fernet.generate_key()
    print(f"MULTIBOT_ENCRYPTION_KEY={key.decode()}")

if __name__ == "__main__":
    main()
```

---

**Файл 40:** `scripts/init_db.sh`

```bash
#!/bin/bash
set -e
echo "Creating database..."
docker compose -f docker/docker-compose.yml up -d db
echo "Waiting for PostgreSQL..."
sleep 3
echo "Running migrations..."
cd "$(dirname "$0")/.."
alembic upgrade head
echo "Done. Database is ready."
```

---

### TASK 3: YAIS AI Provider

**Цель:** Полноценный AI-клиент для Yandex AI Studio Responses API с поддержкой function calling и multi-turn диалогов.

**Время:** ~5–6 часов

**Проверка:** Юнит-тесты с замоканным HTTP: `chat("Привет")` → `AIResponse`, `chat("Создай лида", tools=[...])` → `AIResponse` с `function_calls`.

#### Файлы

---

**Файл 41:** `src/ai/__init__.py`

```python
"""AI provider abstraction layer."""
```

---

**Файл 42:** `src/ai/base.py` — Абстрактный `AIProvider`

```python
# Импорты:
#   from abc import ABC, abstractmethod
#   from src.ai.schemas import AIResponse, MessageRecord

# Класс AIProvider(ABC):
#   """Abstract AI provider interface.
#   Все AI-провайдеры (YAIS, OpenAI, локальные) реализуют этот интерфейс.
#   """
#
#   @abstractmethod
#   async def chat(
#       self,
#       messages: list[MessageRecord],
#       tools: list[dict] | None = None,
#       system_prompt: str | None = None,
#       previous_response_id: str | None = None,
#       model: str | None = None,
#   ) -> AIResponse:
#       """Send conversation to AI, get response.
#
#       Args:
#           messages: Conversation history (user/assistant/tool messages).
#           tools: Function definitions for function calling (YAIS format).
#           system_prompt: System instructions (mapped to YAIS 'instructions').
#           previous_response_id: For multi-turn with YAIS Responses API.
#           model: Override default model.
#
#       Returns:
#           AIResponse with text messages and/or function calls.
#       """
#       ...
#
#   @abstractmethod
#   async def submit_tool_result(
#       self,
#       previous_response_id: str,
#       call_id: str,
#       tool_output: str,
#       tools: list[dict] | None = None,
#       model: str | None = None,
#   ) -> AIResponse:
#       """Submit tool execution result back to AI for continuation.
#
#       Args:
#           previous_response_id: Response ID from the last AI response.
#           call_id: The call_id from the function_call output.
#           tool_output: JSON string with tool execution result.
#           tools: Same tools (may differ after execution context).
#           model: Override default model.
#
#       Returns:
#           AIResponse with next text or function_call.
#       """
#       ...
#
#   @abstractmethod
#   async def embed(self, texts: list[str], model: str | None = None) -> list[list[float]]:
#       """Generate embeddings for texts. Used by RAG (Week 3)."""
#       ...
```

---

**Файл 43:** `src/ai/schemas.py` — Pydantic модели AI

```python
# Импорты:
#   from pydantic import BaseModel, Field
#   from typing import Literal, Any
#   from datetime import datetime

# ============================================================
# Внутренние (нормализованные) модели
# ============================================================

# Класс MessageRecord(BaseModel):
#   """Internal normalized message for conversation history."""
#   role: str                                    # user | assistant | tool | system
#   content: str | None = None
#   tool_calls: list[dict] | None = None        # For assistant messages with function calls
#   tool_call_id: str | None = None             # For tool messages
#   name: str | None = None                     # For tool messages (function name)

# Класс AIResponse(BaseModel):
#   """Normalized AI response — what the router works with."""
#   response_id: str                            # YAIS response ID (for multi-turn)
#   messages: list[str] | None = None           # Text messages to show user
#   function_calls: list[FunctionCall] | None = None  # Tool calls
#   finish_reason: str | None = None            # "stop" | "tool_calls" | "length" | "error"
#   usage: UsageStats | None = None

# Класс FunctionCall(BaseModel):
#   """A single function call from the AI."""
#   call_id: str                                # Unique call ID (for tool result submission)
#   name: str                                   # Function name, e.g. "crm.lead.add"
#   arguments: dict[str, Any]                   # Parsed JSON arguments

# Класс UsageStats(BaseModel):
#   input_tokens: int
#   output_tokens: int
#   total_tokens: int

# ============================================================
# YAIS Responses API модели (request/response)
# ============================================================

# Класс YaisToolParameter(BaseModel):
#   """JSON Schema for tool parameters."""
#   type: str = "object"
#   properties: dict[str, Any]
#   required: list[str] | None = None

# Класс YaisTool(BaseModel):
#   """YAIS tool definition."""
#   type: str = "function"
#   name: str
#   description: str
#   parameters: YaisToolParameter

# Класс YaisResponsesRequest(BaseModel):
#   """POST /v1/responses request body."""
#   model: str
#   instructions: str | None = None            # System prompt
#   input: str | list[dict] | None = None      # User message (str) or tool results (list)
#   tools: list[YaisTool] | None = None
#   previous_response_id: str | None = None
#   temperature: float | None = None
#   max_output_tokens: int | None = None

# Класс YaisOutputMessageContent(BaseModel):
#   type: str  # "output_text"
#   text: str

# Класс YaisOutputMessage(BaseModel):
#   type: Literal["message"]
#   content: list[YaisOutputMessageContent]

# Класс YaisOutputFunctionCall(BaseModel):
#   type: Literal["function_call"]
#   name: str
#   arguments: str                              # JSON string!
#   call_id: str

# Класс YaisOutputReasoning(BaseModel):
#   type: Literal["reasoning"]
#   content: list[dict]

# YaisOutputItem = YaisOutputMessage | YaisOutputFunctionCall | YaisOutputReasoning

# Класс YaisUsageInfo(BaseModel):
#   input_tokens: int
#   output_tokens: int
#   total_tokens: int

# Класс YaisResponsesResponse(BaseModel):
#   """YAIS /v1/responses response."""
#   id: str
#   object: str = Field(alias="object", default="response")
#   model: str
#   output: list[dict]                          # Raw list, parsed manually to handle union
#   usage: YaisUsageInfo | None = None
```

---

**Файл 44:** `src/ai/yais.py` — `YAISResponsesProvider`

```python
# Импорты:
#   import json
#   import httpx
#   import structlog
#   from src.ai.base import AIProvider
#   from src.ai.schemas import *
#   from src.core.exceptions import AITimeoutError, AIRateLimitError, AIAuthError, AIProviderError

# Класс YAISResponsesProvider(AIProvider):
#   """Yandex AI Studio Responses API provider.
#
#   Primary model: GPT OSS 20B via /v1/responses (function calling).
#   Fallback model: YandexGPT-5-lite via /v1/chat/completions (Week 4: fallback logic).
#   Embeddings: text-embeddings-v2 via /v1/embeddings.
#
#   Multi-turn: previous_response_id in request.
#   """
#
#   def __init__(
#       self,
#       api_key: str,
#       folder_id: str,
#       base_url: str = "https://ai.api.yandexcloud.net",
#       primary_model: str = "",
#       fallback_model: str = "yandexgpt-5-lite",
#       embedding_model: str = "text-embeddings-v2",
#       timeout: int = 30,
#       httpx_client: httpx.AsyncClient | None = None,
#   ) -> None:
#       self.api_key = api_key
#       self.folder_id = folder_id
#       self.base_url = base_url.rstrip("/")
#       self.primary_model = primary_model or f"gpt://{folder_id}/gpt-oss-20b/latest"
#       self.fallback_model = fallback_model
#       self.embedding_model = embedding_model
#       self.timeout = timeout
#       self._client = httpx_client or httpx.AsyncClient(timeout=httpx.Timeout(timeout))
#       self._logger = structlog.get_logger(__name__)
#
#   # ======== Public API ========
#
#   async def chat(
#       self,
#       messages: list[MessageRecord],
#       tools: list[dict] | None = None,
#       system_prompt: str | None = None,
#       previous_response_id: str | None = None,
#       model: str | None = None,
#   ) -> AIResponse:
#       """Main chat method. Sends conversation + tools → YAIS → normalized response."""
#       # 1. Build user input from the LAST user message in messages
#       # 2. Convert tools list to YaisTool[]
#       # 3. Build YaisResponsesRequest
#       # 4. POST /v1/responses
#       # 5. Handle errors (timeout, rate limit, auth, model error)
#       # 6. Parse YaisResponsesResponse → AIResponse
#       # 7. Return
#
#   async def submit_tool_result(
#       self,
#       previous_response_id: str,
#       call_id: str,
#       tool_output: str,
#       tools: list[dict] | None = None,
#       model: str | None = None,
#   ) -> AIResponse:
#       """Submit function call result back to YAIS."""
#       # POST /v1/responses with:
#       # {
#       #   model: ...,
#       #   previous_response_id: ...,
#       #   input: [{"type": "function_call_output", "call_id": call_id, "output": tool_output}],
#       #   tools: ...
#       # }
#
#   async def embed(self, texts: list[str], model: str | None = None) -> list[list[float]]:
#       """Generate embeddings via YAIS Embeddings API."""
#       # POST /v1/embeddings
#       # { model: "emb://{folder_id}/text-embeddings-v2/latest", input: texts }
#       # Return: list of embedding vectors
#
#   # ======== Private methods ========
#
#   def _extract_last_user_input(self, messages: list[MessageRecord]) -> str:
#       """Extract the last user message text for YAIS 'input' field."""
#
#   def _build_tools(self, tools: list[dict] | None) -> list[YaisTool] | None:
#       """Convert internal tool dicts to YaisTool list."""
#
#   def _build_request(
#       self,
#       model: str,
#       input_text: str | list[dict],
#       instructions: str | None,
#       tools: list[YaisTool] | None,
#       previous_response_id: str | None,
#   ) -> dict:
#       """Build YAIS-compatible request dict."""
#
#   async def _make_request(self, path: str, body: dict) -> dict:
#       """Send HTTP request to YAIS with auth headers and error handling."""
#       # Headers: Authorization: Api-Key {api_key}
#       # On error: parse status code → raise appropriate error
#
#   def _parse_response(self, data: dict) -> AIResponse:
#       """Parse YAIS JSON response → normalized AIResponse."""
#       # Iterate data["output"]:
#       #   - type="message" → extract text
#       #   - type="function_call" → parse arguments JSON → FunctionCall
#       #   - type="reasoning" → ignore (or log)
#       # Return AIResponse with response_id, messages, function_calls

#   def _handle_http_error(self, status_code: int, body: dict) -> None:
#       """Map HTTP errors to our exceptions:
#       401/403 → AIAuthError
#       429 → AIRateLimitError
#       408/504 → AITimeoutError
#       5xx → AIProviderError
#       """
```

Подробно: метод `chat()`:

```python
async def chat(self, messages, tools=None, system_prompt=None, previous_response_id=None, model=None):
    # 1. Определить модель
    model = model or self.primary_model

    # 2. Извлечь последнее сообщение пользователя как 'input'
    #    Для первого сообщения: просто текст.
    #    Для multi-turn: текст последнего сообщения пользователя.
    user_messages = [m for m in messages if m.role == "user"]
    if not user_messages:
        raise AIProviderError("No user message in conversation")
    input_text = user_messages[-1].content or ""

    # 3. Конвертировать tools
    yais_tools = self._build_tools(tools)

    # 4. Построить запрос
    body = {
        "model": model,
        "instructions": system_prompt or "",
        "input": input_text,
        "tools": [t.model_dump(exclude_none=True) for t in yais_tools] if yais_tools else None,
    }
    if previous_response_id:
        body["previous_response_id"] = previous_response_id

    # 5. Отправить
    response_data = await self._make_request("/v1/responses", body)

    # 6. Распарсить
    return self._parse_response(response_data)
```

Метод `submit_tool_result()`:

```python
async def submit_tool_result(self, previous_response_id, call_id, tool_output, tools=None, model=None):
    model = model or self.primary_model
    yais_tools = self._build_tools(tools)

    body = {
        "model": model,
        "previous_response_id": previous_response_id,
        "input": [{
            "type": "function_call_output",
            "call_id": call_id,
            "output": tool_output,
        }],
        "tools": [t.model_dump(exclude_none=True) for t in yais_tools] if yais_tools else None,
    }

    response_data = await self._make_request("/v1/responses", body)
    return self._parse_response(response_data)
```

Метод `_parse_response()`:

```python
def _parse_response(self, data: dict) -> AIResponse:
    response_id = data["id"]
    messages = []
    function_calls = []

    for item in data.get("output", []):
        if item["type"] == "message":
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    messages.append(content["text"])
        elif item["type"] == "function_call":
            try:
                arguments = json.loads(item["arguments"])
            except json.JSONDecodeError:
                arguments = {}
            function_calls.append(FunctionCall(
                call_id=item["call_id"],
                name=item["name"],
                arguments=arguments,
            ))
        # type="reasoning" — skip (logging only)

    usage = None
    if "usage" in data:
        usage = UsageStats(
            input_tokens=data["usage"]["input_tokens"],
            output_tokens=data["usage"]["output_tokens"],
            total_tokens=data["usage"]["total_tokens"],
        )

    finish_reason = "stop"
    if function_calls:
        finish_reason = "tool_calls"

    return AIResponse(
        response_id=response_id,
        messages=messages if messages else None,
        function_calls=function_calls if function_calls else None,
        finish_reason=finish_reason,
        usage=usage,
    )
```

---

### TASK 4: MAX Adapter

**Цель:** Полноценный REST-клиент для `platform-api.max.ru`, обработка вебхуков, отправка сообщений с Markdown-форматированием.

**Время:** ~5–6 часов

**Проверка:** Юнит-тесты с замоканным HTTP: парсинг вебхука, отправка сообщения, форматирование Markdown.

#### Файлы

---

**Файл 45:** `src/adapters/__init__.py`

```python
"""Messenger adapter layer. Each messenger has its own subpackage."""
```

---

**Файл 46:** `src/adapters/base.py` — `MessengerAdapter`

```python
# Импорты:
#   from abc import ABC, abstractmethod
#   from pydantic import BaseModel

# Класс IncomingMessage(BaseModel):
#   """Normalized incoming message from any messenger."""
#   messenger: str                                  # "maxx" | "telegram" | "vk"
#   messenger_user_id: str                          # ID пользователя в мессенджере
#   messenger_chat_id: str                          # ID чата
#   text: str | None = None                         # Текст сообщения
#   company_slug: str = ""                          # Slug компании (из URL вебхука)
#   raw_payload: dict = {}                          # Оригинальный payload

# Класс OutgoingMessage(BaseModel):
#   """Message to be sent back to user."""
#   text: str
#   parse_mode: str = "markdown"                    # markdown | html | text
#   reply_markup: dict | None = None                # Inline keyboard

# Класс MessengerAdapter(ABC):
#   """Abstract messenger adapter. Реализуется для каждого мессенджера."""
#
#   @abstractmethod
#   async def parse_incoming(self, payload: dict) -> IncomingMessage:
#       """Parse raw webhook payload → IncomingMessage."""
#
#   @abstractmethod
#   async def send_message(
#       self,
#       chat_id: str,
#       text: str,
#       parse_mode: str = "markdown",
#       reply_markup: dict | None = None,
#   ) -> dict:
#       """Send message to user. Returns messenger response."""
#
#   @abstractmethod
#   async def register_webhook(self, webhook_url: str) -> dict:
#       """Register webhook URL with messenger."""
#
#   @abstractmethod
#   async def unregister_webhook(self) -> bool:
#       """Remove webhook registration."""
#
#   @abstractmethod
#   async def verify_webhook_signature(self, payload: dict, headers: dict) -> bool:
#       """Verify webhook request authenticity. (Optional, depends on messenger.)"""
```

---

**Файл 47:** `src/adapters/maxx/__init__.py`

```python
"""MAX Messenger adapter for platform-api.max.ru."""
```

---

**Файл 48:** `src/adapters/maxx/schemas.py` — MAX-specific модели

```python
# Импорты: BaseModel, Optional, Any

# ============================================================
# MAX Webhook Payload (входящее сообщение)
# ============================================================

# Класс MaxWebhookUser(BaseModel):
#   id: str                                        # MAX user ID
#   first_name: str | None = None
#   last_name: str | None = None
#   username: str | None = None

# Класс MaxWebhookChat(BaseModel):
#   id: str                                        # MAX chat ID

# Класс MaxWebhookMessage(BaseModel):
#   message_id: str
#   chat: MaxWebhookChat
#   from_: MaxWebhookUser = Field(alias="from")
#   text: str | None = None
#   date: int | None = None                        # Unix timestamp

# Класс MaxWebhookPayload(BaseModel):
#   """Root webhook payload from MAX."""
#   update_id: int
#   message: MaxWebhookMessage | None = None
#   callback_query: dict | None = None             # Inline keyboard callback

# ============================================================
# MAX Send Message API
# ============================================================

# Класс MaxSendMessageRequest(BaseModel):
#   chat_id: str
#   text: str
#   parse_mode: str = "markdown"                   # "markdown" | "html"
#   reply_markup: dict | None = None               # {"inline_keyboard": [[...]]}
#   disable_notification: bool = False

# Класс MaxMessageResponse(BaseModel):
#   message_id: str
#   chat: dict
#   date: int
#   text: str | None = None

# Класс MaxWebhookRegistrationRequest(BaseModel):
#   url: str                                       # HTTPS URL for webhook

# Класс MaxWebhookRegistrationResponse(BaseModel):
#   ok: bool
#   result: dict | None = None
#   description: str | None = None
```

---

**Файл 49:** `src/adapters/maxx/client.py` — `MaxRESTClient`

```python
# Импорты:
#   import httpx
#   import structlog
#   from src.adapters.maxx.schemas import *
#   from src.core.exceptions import MessengerError, MessengerSendError

# Класс MaxRESTClient:
#   """REST client for MAX Bot API (platform-api.max.ru).
#
#   Authentication: Authorization: {bot_token} header.
#   Base URL: https://platform-api.max.ru
#   Rate limit: 30 RPS per bot.
#   """
#
#   def __init__(
#       self,
#       bot_token: str,
#       base_url: str = "https://platform-api.max.ru",
#       httpx_client: httpx.AsyncClient | None = None,
#       timeout: int = 10,
#   ) -> None:
#       self.bot_token = bot_token
#       self.base_url = base_url.rstrip("/")
#       self._client = httpx_client or httpx.AsyncClient(timeout=httpx.Timeout(timeout))
#       self._logger = structlog.get_logger(__name__)
#
#   async def send_message(
#       self,
#       chat_id: str,
#       text: str,
#       parse_mode: str = "markdown",
#       reply_markup: dict | None = None,
#   ) -> MaxMessageResponse:
#       """Send message to MAX chat.
#
#       Args:
#           chat_id: MAX chat ID.
#           text: Message text (supports Markdown/HTML).
#           parse_mode: "markdown" or "html".
#           reply_markup: Inline keyboard: {"inline_keyboard": [[{"text":"...", "callback_data":"..."}]]}
#
#       Returns:
#           MaxMessageResponse with message_id.
#       """
#       body = MaxSendMessageRequest(
#           chat_id=chat_id,
#           text=text,
#           parse_mode=parse_mode,
#           reply_markup=reply_markup,
#       )
#       data = await self._request("POST", "/messages", body.model_dump(exclude_none=True))
#       return MaxMessageResponse(**data)
#
#   async def get_me(self) -> dict:
#       """Get bot information."""
#       return await self._request("GET", "/me")
#
#   async def register_webhook(self, url: str) -> MaxWebhookRegistrationResponse:
#       """Register webhook URL. Must be HTTPS."""
#       body = MaxWebhookRegistrationRequest(url=url)
#       data = await self._request("POST", "/subscriptions", body.model_dump())
#       return MaxWebhookRegistrationResponse(**data)
#
#   async def delete_webhook(self) -> bool:
#       """Remove webhook registration."""
#       await self._request("DELETE", "/subscriptions")
#       return True
#
#   async def _request(self, method: str, path: str, json_data: dict | None = None) -> dict:
#       """Send HTTP request to MAX API with auth and error handling.
#
#       Headers:
#           Authorization: {bot_token}  (не Bearer! plain token)
#           Content-Type: application/json
#
#       Error handling:
#           400 → MessengerError (bad request)
#           401/403 → MessengerError (invalid token)
#           429 → MessengerError (rate limit)
#           5xx → MessengerSendError (server error)
#       """
#       url = f"{self.base_url}{path}"
#       headers = {
#           "Authorization": self.bot_token,
#           "Content-Type": "application/json",
#       }
#       response = await self._client.request(method, url, json=json_data, headers=headers)
#       # ... error handling based on status code
#       return response.json()

#   async def close(self) -> None:
#       """Close HTTP client."""
#       await self._client.aclose()
```

---

**Файл 50:** `src/adapters/maxx/webhook.py` — `MaxWebhookHandler`

```python
# Импорты:
#   from src.adapters.base import IncomingMessage
#   from src.adapters.maxx.schemas import MaxWebhookPayload

# Класс MaxWebhookHandler:
#   """Handles incoming MAX webhook payloads.
#   Нормализует MAX-специфичные payload → IncomingMessage.
#   """
#
#   def __init__(self, client: "MaxRESTClient") -> None:
#       self.client = client
#
#   def parse_incoming(self, payload: dict) -> IncomingMessage:
#       """Parse raw MAX webhook payload → IncomingMessage.
#
#       MAX webhook format:
#       {
#           "update_id": 123,
#           "message": {
#               "message_id": "...",
#               "from": {"id": "...", "first_name": "...", ...},
#               "chat": {"id": "..."},
#               "text": "Привет!",
#               "date": 1234567890
#           }
#       }
#       Or callback_query (inline button click):
#       {
#           "update_id": 123,
#           "callback_query": {
#               "id": "...",
#               "from": {...},
#               "message": {...},
#               "data": "callback_payload"
#           }
#       }
#       """
#       # 1. Проверить тип: message или callback_query
#       # 2. Извлечь user_id, chat_id, text
#       # 3. Вернуть IncomingMessage
#
#   def is_callback(self, payload: dict) -> bool:
#       """Check if payload is a callback query (vs message)."""
```

---

**Файл 51:** `src/adapters/maxx/formatting.py` — `MaxMessageFormatter`

```python
# Класс MaxMessageFormatter:
#   """Format text for MAX messenger Markdown/HTML support.
#
#   MAX supports:
#   - Markdown: **bold**, *italic*, [text](url), `code`, ```code block```
#   - HTML: <b>, <i>, <a href>, <code>, <pre>
#   - inline_keyboard: list of button rows
#   """
#
#   @staticmethod
#   def escape_markdown(text: str) -> str:
#       """Escape special Markdown characters in user text that shouldn't be formatted.
#       Escapes: _ * [ ] ( ) ~ ` > # + - = | { } . !
#       """
#
#   @staticmethod
#   def bold(text: str) -> str:
#       """Wrap text in **bold**."""
#       return f"**{text}**"
#
#   @staticmethod
#   def italic(text: str) -> str:
#       """Wrap text in *italic*."""
#       return f"*{text}*"
#
#   @staticmethod
#   def link(text: str, url: str) -> str:
#       """Create a Markdown link."""
#       return f"[{text}]({url})"
#
#   @staticmethod
#   def code(text: str) -> str:
#       """Wrap text in `code`."""
#       return f"`{text}`"
#
#   @staticmethod
#   def code_block(text: str, language: str = "") -> str:
#       """Wrap text in ```code block```."""
#       return f"```{language}\n{text}\n```"
#
#   @staticmethod
#   def build_inline_keyboard(buttons: list[list[dict]]) -> dict:
#       """Build inline_keyboard markup.
#
#       Args:
#           buttons: [
#               [{"text": "Кнопка 1", "callback_data": "action_1"}],
#               [{"text": "Кнопка 2", "url": "https://..."}],
#           ]
#
#       Returns:
#           {"inline_keyboard": [[...], [...]]}
#       """
#       return {"inline_keyboard": buttons}
```

---

### TASK 5: End-to-end Dialog

**Цель:** MAX вебхук → определение компании → создание диалога → вызов YAIS → ответ в MAX. Полный цикл с сохранением истории.

**Время:** ~6–7 часов

**Проверка:** Интеграционный тест: отправить вебхук → YAIS отвечает текстом → сообщение сохранено в БД → `previous_response_id` обновлён.

#### Файлы

---

**Файл 52:** `src/core/router.py` — `MessageRouter` (ГЛАВНЫЙ ОРКЕСТРАТОР)

```python
# Импорты:
#   import uuid
#   import structlog
#   from sqlalchemy.ext.asyncio import AsyncSession
#   from src.core.tenant import TenantManager
#   from src.core.services import *
#   from src.ai.base import AIProvider
#   from src.ai.schemas import AIResponse, MessageRecord, FunctionCall
#   from src.adapters.base import IncomingMessage, MessengerAdapter
#   from src.plugins.registry import PluginRegistry
#   from src.core.config import Settings
#   from src.core.exceptions import *

# Класс MessageRouter:
#   """Orchestrates full message flow: adapter → AI → response.
#
#   Pipeline:
#   1. Resolve tenant (company_slug)
#   2. Find/create User
#   3. Find/create active Conversation
#   4. Store user message
#   5. Build conversation history
#   6. Get tools for company (from PluginRegistry)
#   7. Call AI provider
#   8. Process response (text → send, function_call → execute → loop)
#   9. Update conversation.previous_response_id
#   """
#
#   def __init__(
#       self,
#       settings: Settings,
#       ai_provider: AIProvider,
#       plugin_registry: "PluginRegistry | None" = None,
#   ) -> None:
#       self.settings = settings
#       self.ai = ai_provider
#       self.plugin_registry = plugin_registry  # None в Week 1 (нет плагинов)
#       self._logger = structlog.get_logger(__name__)
#
#   async def process_message(
#       self,
#       incoming: IncomingMessage,
#       session: AsyncSession,
#       adapter: MessengerAdapter,
#   ) -> None:
#       """Main entry point for processing an incoming message.
#
#       Args:
#           incoming: Normalized incoming message.
#           session: DB session (from FastAPI dependency).
#           adapter: Messenger adapter for sending responses.
#       """
#       # === STEP 1: Resolve tenant ===
#       tenant_mgr = TenantManager(session)
#       company = await tenant_mgr.get_by_slug(incoming.company_slug)
#
#       # === STEP 2: Find or create user ===
#       user_svc = UserService(session)
#       user = await user_svc.get_or_create(
#           company_id=company.id,
#           messenger=incoming.messenger,
#           messenger_user_id=incoming.messenger_user_id,
#       )
#
#       # === STEP 3: Find or create conversation ===
#       conv_svc = ConversationService(session)
#       conversation = await conv_svc.get_or_create_active(
#           company_id=company.id,
#           user_id=user.id,
#           messenger=incoming.messenger,
#           messenger_chat_id=incoming.messenger_chat_id,
#       )
#
#       # === STEP 4: Store user message ===
#       msg_svc = MessageService(session)
#       await msg_svc.create(
#           conversation_id=conversation.id,
#           role="user",
#           content=incoming.text or "",
#       )
#
#       # === STEP 5: Build conversation history ===
#       history = await msg_svc.get_conversation_history(
#           conversation.id,
#           limit=self.settings.conversation_history_limit,
#       )
#       message_records = self._messages_to_records(history)
#
#       # === STEP 6: Load system prompt for company ===
#       system_prompt = self._build_system_prompt(company)
#
#       # === STEP 7: Get tools ===
#       tools = await self._get_tools(company.id)  # Week 1: empty list
#
#       # === STEP 8: Call AI ===
#       try:
#           response = await self.ai.chat(
#               messages=message_records,
#               tools=tools,
#               system_prompt=system_prompt,
#               previous_response_id=conversation.previous_response_id,
#           )
#       except AIProviderError as e:
#           self._logger.error("AI provider error", error=str(e), company=company.slug)
#           await adapter.send_message(
#               incoming.messenger_chat_id,
#               "Извините, произошла ошибка при обработке запроса. Попробуйте позже."
#           )
#           return
#
#       # === STEP 9: Process AI response ===
#       await self._process_ai_response(
#           response=response,
#           conversation=conversation,
#           adapter=adapter,
#           company_id=company.id,
#           user_id=user.id,
#           session=session,
#           tools=tools,
#       )
#
#       # === STEP 10: Commit transaction ===
#       await session.commit()
#
#   async def _process_ai_response(
#       self,
#       response: AIResponse,
#       conversation: Conversation,
#       adapter: MessengerAdapter,
#       company_id: uuid.UUID,
#       user_id: uuid.UUID,
#       session: AsyncSession,
#       tools: list[dict] | None,
#       iteration: int = 0,
#   ) -> None:
#       """Process AI response: send text or execute function calls.
#
#       If function_calls present:
#           1. Store assistant message with tool_calls
#           2. Execute each tool call
#           3. Store tool results as messages
#           4. Submit results back to AI → recurse
#
#       If messages (text) present:
#           1. Store assistant message
#           2. Send to messenger
#           3. Update conversation.previous_response_id
#       """
#       max_iter = self.settings.tool_call_max_iterations
#       conv_svc = ConversationService(session)
#       msg_svc = MessageService(session)
#
#       if response.function_calls and iteration < max_iter:
#           # --- Handle function calls ---
#           self._logger.info(
#               "AI requested function calls",
#               calls=[fc.name for fc in response.function_calls],
#               iteration=iteration,
#           )
#
#           # Store assistant message with tool_calls
#           await msg_svc.create(
#               conversation_id=conversation.id,
#               role="assistant",
#               tool_calls=[fc.model_dump() for fc in response.function_calls],
#               metadata={"response_id": response.response_id},
#           )
#
#           # Execute each tool call
#           for fc in response.function_calls:
#               result = await self._execute_tool(
#                   fc, company_id=company_id, user_id=user_id
#               )
#               # Store tool result
#               await msg_svc.create(
#                   conversation_id=conversation.id,
#                   role="tool",
#                   content=result,
#                   tool_call_id=fc.call_id,
#                   name=fc.name,
#               )
#
#           # Submit all tool results back to AI
#           # (Submit first one to continue; YAIS takes one result per submit)
#           first_call = response.function_calls[0]
#           next_response = await self.ai.submit_tool_result(
#               previous_response_id=response.response_id,
#               call_id=first_call.call_id,
#               tool_output=json.dumps(first_call.arguments),  # TODO: use actual result
#               tools=tools,
#           )
#           # Recurse
#           await self._process_ai_response(
#               response=next_response,
#               conversation=conversation,
#               adapter=adapter,
#               company_id=company_id,
#               user_id=user_id,
#               session=session,
#               tools=tools,
#               iteration=iteration + 1,
#           )
#
#       elif response.messages:
#           # --- Handle text response ---
#           text = "\n\n".join(response.messages)
#
#           # Store assistant message
#           await msg_svc.create(
#               conversation_id=conversation.id,
#               role="assistant",
#               content=text,
#               metadata={
#                   "response_id": response.response_id,
#                   "model": response.usage.model if response.usage else "unknown",
#               },
#           )
#
#           # Update conversation
#           await conv_svc.update_previous_response_id(conversation.id, response.response_id)
#           await conv_svc.touch_last_message(conversation.id)
#
#           # Send to messenger
#           chat_id = conversation.messenger_chat_id
#           try:
#               await adapter.send_message(chat_id, text)
#               await session.commit()
#           except MessengerError as e:
#               self._logger.error("Failed to send message to messenger", error=str(e))
#
#       else:
#           # No text and no function calls → edge case, log and send generic
#           self._logger.warning("AI returned empty response", response_id=response.response_id)
#           await adapter.send_message(
#               conversation.messenger_chat_id,
#               "Я не смог сформулировать ответ. Попробуйте переформулировать запрос."
#           )
#
#   async def _execute_tool(
#       self,
#       function_call: FunctionCall,
#       company_id: uuid.UUID,
#       user_id: uuid.UUID,
#   ) -> str:
#       """Execute a single tool call through the plugin registry.
#       Week 1: registry is None or empty → returns error message.
#       Week 2: dispatches to correct plugin.
#       """
#       if self.plugin_registry is None:
#           return json.dumps({"error": "Plugin system not available"})
#       try:
#           result = await self.plugin_registry.execute_tool(
#               tool_name=function_call.name,
#               arguments=function_call.arguments,
#               context={"company_id": str(company_id), "user_id": str(user_id)},
#           )
#           return json.dumps(result, ensure_ascii=False)
#       except Exception as e:
#           self._logger.error("Tool execution failed", tool=function_call.name, error=str(e))
#           return json.dumps({"error": str(e)})
#
#   def _messages_to_records(self, messages: list[Message]) -> list[MessageRecord]:
#       """Convert DB Message objects to MessageRecord for AI provider."""
#       return [
#           MessageRecord(
#               role=msg.role,
#               content=msg.content,
#               tool_calls=msg.tool_calls,
#               tool_call_id=msg.tool_call_id,
#           )
#           for msg in messages
#       ]
#
#   def _build_system_prompt(self, company: Company) -> str:
#       """Build system prompt for AI from company settings."""
#       default = (
#           "Ты — AI-ассистент компании. "
#           "Отвечай на русском языке. "
#           "Будь вежлив и профессионален. "
#           "Если тебя просят выполнить действие (создать лида, найти сделку), "
#           "используй доступные инструменты."
#       )
#       custom = company.settings.get("system_prompt", "") if company.settings else ""
#       return custom or default
#
#   async def _get_tools(self, company_id: uuid.UUID) -> list[dict] | None:
#       """Get registered tools for the company from PluginRegistry.
#       Week 1: returns empty list (no plugins registered yet).
#       Week 2: returns tools from manifest.yaml files.
#       """
#       if self.plugin_registry is None:
#           return None
#       return await self.plugin_registry.get_tools_for_ai(company_id)
```

---

**Файл 53:** `src/api/routes/webhooks.py` — Вебхук endpoint

```python
# Импорты:
#   from fastapi import APIRouter, Depends, Request, HTTPException
#   from sqlalchemy.ext.asyncio import AsyncSession
#   from src.core.database import get_session
#   from src.core.router import MessageRouter
#   from src.adapters.maxx.client import MaxRESTClient
#   from src.adapters.maxx.webhook import MaxWebhookHandler
#   from src.adapters.maxx.schemas import MaxWebhookPayload
#   import structlog

# router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])
# logger = structlog.get_logger(__name__)

# @router.post("/maxx/{company_slug}")
# async def maxx_webhook(
#     company_slug: str,
#     request: Request,
#     db: AsyncSession = Depends(get_session),
# ) -> dict:
#     """Handle incoming MAX Messenger webhook.
#
#     MAX sends updates to this endpoint.
#     URL: POST /api/v1/webhooks/maxx/{company_slug}
#     """
#     # 1. Read raw payload
#     payload = await request.json()
#
#     # 2. Resolve MAX adapter for this company
#     #    Week 1: use default bot token from settings
#     #    Week 3: lookup token from integrations table per company
#     settings = request.app.state.settings
#     # For Week 1, check integration table for company "maxx"
#     integration_svc = IntegrationService(db, encryption_svc)
#     max_config = await integration_svc.get_raw_config(company_id, "maxx")
#     bot_token = max_config.get("bot_token") if max_config else settings.max_default_bot_token
#
#     if not bot_token:
#         raise HTTPException(status_code=500, detail="MAX bot token not configured")
#
#     max_client = MaxRESTClient(bot_token=bot_token)
#     handler = MaxWebhookHandler(max_client)
#
#     # 3. Parse incoming message
#     try:
#         incoming = handler.parse_incoming(payload)
#         incoming.company_slug = company_slug
#     except Exception as e:
#         logger.error("Failed to parse MAX webhook", error=str(e), payload=payload)
#         # Return 200 anyway so MAX doesn't retry
#         return {"status": "error", "message": "Invalid payload"}
#
#     # 4. Route to core
#     router = MessageRouter(
#         settings=settings,
#         ai_provider=request.app.state.ai_provider,
#         plugin_registry=request.app.state.plugin_registry,
#     )
#
#     # Create adapter wrapper
#     class MaxAdapter(MessengerAdapter):
#         # ... implements send_message etc. using max_client
#         pass
#
#     adapter = MaxAdapter(client=max_client, handler=handler)
#
#     await router.process_message(incoming, db, adapter)
#
#     return {"status": "ok"}
```

Примечание по MAX Adapter в вебхуке: лушче создать `MaxMessengerAdapter`, который реализует `MessengerAdapter` и использует `MaxRESTClient` + `MaxWebhookHandler`. Его нужно зарегистрировать в DI-контейнере приложения при старте. Переработаем:

---

**Уточнение к Task 5:** `src/adapters/maxx/adapter.py` — полный адаптер

```python
# Файл: src/adapters/maxx/adapter.py
# Класс MaxMessengerAdapter(MessengerAdapter):
#   """Полная реализация MessengerAdapter для MAX."""
#
#   def __init__(self, client: MaxRESTClient, handler: MaxWebhookHandler) -> None:
#       self.client = client
#       self.handler = handler
#
#   async def parse_incoming(self, payload: dict) -> IncomingMessage:
#       return self.handler.parse_incoming(payload)
#
#   async def send_message(self, chat_id, text, parse_mode="markdown", reply_markup=None) -> dict:
#       response = await self.client.send_message(chat_id, text, parse_mode, reply_markup)
#       return response.model_dump()
#
#   async def register_webhook(self, webhook_url: str) -> dict:
#       response = await self.client.register_webhook(webhook_url)
#       return response.model_dump()
#
#   async def unregister_webhook(self) -> bool:
#       return await self.client.delete_webhook()
#
#   async def verify_webhook_signature(self, payload, headers) -> bool:
#       # MAX doesn't have webhook signatures (MVP)
#       return True
```

---

**Файл 54:** Обновлённый `src/api/app.py` — с инициализацией компонентов

```python
# def create_app(settings: Settings) → FastAPI:
#   app = FastAPI(...)
#
#   # Инициализация AI провайдера
#   ai_provider = YAISResponsesProvider(
#       api_key=settings.yais_api_key,
#       folder_id=settings.yais_folder_id,
#       base_url=settings.yais_base_url,
#       primary_model=settings.get_yais_model_url(),
#   )
#   app.state.ai_provider = ai_provider
#
#   # Инициализация Plugin Registry (Week 1: пустой)
#   plugin_registry = PluginRegistry()
#   app.state.plugin_registry = plugin_registry
#
#   # Инициализация Encryption Service
#   encryption_svc = EncryptionService(settings.get_encryption_key())
#   app.state.encryption = encryption_svc
#
#   # Register routes
#   app.include_router(health_router)
#   app.include_router(webhooks_router)
#
#   # Store settings (for DI in routes)
#   app.state.settings = settings
#
#   return app
```

---

**Файл 55:** Пустой PluginRegistry для Week 1 — `src/plugins/registry.py`

```python
# Импорты:
#   import structlog

# Класс PluginRegistry:
#   """Plugin registry — loads and manages integration plugins.
#   Week 1: stub implementation (returns empty tools).
#   Week 2: loads manifest.yaml, registers tools, dispatches function calls.
#   """
#
#   def __init__(self) -> None:
#       self._plugins: dict[str, "Plugin"] = {}
#       self._tools: dict[str, "Plugin"] = {}  # tool_name → plugin
#       self._logger = structlog.get_logger(__name__)
#
#   async def load_plugins(self, plugins_dir: str) -> None:
#       """Scan plugins_dir for manifest.yaml files and load them.
#       Week 2 implementation.
#       """
#       pass
#
#   async def get_tools_for_ai(self, company_id: uuid.UUID) -> list[dict]:
#       """Return all registered tools in YAIS-compatible format.
#       Week 1: returns empty list.
#       Week 2: returns converted manifest tools.
#       """
#       return []
#
#   async def execute_tool(
#       self,
#       tool_name: str,
#       arguments: dict,
#       context: dict,
#   ) -> dict:
#       """Execute a registered tool.
#       Week 1: raises ToolNotFoundError.
#       Week 2: dispatches to correct plugin.
#       """
#       raise ToolExecutionError(f"Tool '{tool_name}' not found (plugin system not yet active)")
```

---

**Файл 56:** `src/plugins/base.py` — Абстрактный Plugin (скелет для Week 2)

```python
# from abc import ABC, abstractmethod

# class Plugin(ABC):
#   """Abstract integration plugin."""
#
#   @property
#   @abstractmethod
#   def name(self) -> str: ...
#
#   @property
#   @abstractmethod
#   def version(self) -> str: ...
#
#   @abstractmethod
#   async def initialize(self, config: dict) -> None: ...
#
#   @abstractmethod
#   async def execute_tool(self, tool_name: str, arguments: dict, context: dict) -> dict: ...
#
#   @abstractmethod
#   async def get_tools(self) -> list[dict]: ...
```

---

**Файл 57:** Обновлённый `src/core/exceptions.py` — добавить `ToolNotFoundError`

```python
# class ToolExecutionError(PluginError):
#     code = "TOOL_EXECUTION_ERROR"

# class ToolNotFoundError(PluginError):
#     code = "TOOL_NOT_FOUND"
```

---

### Сводная таблица: 57 файлов Week 1

| # | Задача | Файлов |
|---|--------|--------|
| 1 | Project Init | 24 (1–24) |
| 2 | Multi-tenant | 16 (25–40) |
| 3 | YAIS Provider | 4 (41–44) |
| 4 | MAX Adapter | 7 (45–51) |
| 5 | E2E Dialog | 6 (52–57) |
| **Итого** | | **57** |

---

## 5. Data Flow Diagrams

### 5.1. Основной поток: MAX → Router → YAIS → MAX

```
┌──────────┐     HTTPS POST       ┌────────────────────┐
│  MAX     │  /webhooks/maxx/     │   FastAPI Server    │
│ Messenger│  {company_slug}      │                     │
│  Server  │ ──────────────────► │ api/routes/         │
│          │                      │   webhooks.py       │
└──────────┘                      │                     │
                                  │ 1. Извлечь payload   │
                                  │ 2. Определить        │
                                  │    company_slug      │
                                  └─────────┬───────────┘
                                            │
                                  ┌─────────▼───────────┐
                                  │ MaxWebhookHandler   │
                                  │  .parse_incoming()  │
                                  │                     │
                                  │ {messenger: "maxx", │
                                  │  user_id: "123",     │
                                  │  chat_id: "456",     │
                                  │  text: "Привет!"}   │
                                  └─────────┬───────────┘
                                            │ IncomingMessage
                                  ┌─────────▼───────────┐
                                  │   MessageRouter      │
                                  │                     │
                                  │ 1. TenantManager     │
                                  │    .get_by_slug()   │
                                  │    → Company("amiri")│
                                  │                     │
                                  │ 2. UserService       │
                                  │    .get_or_create() │
                                  │    → User(id=...)    │
                                  │                     │
                                  │ 3. ConversationSvc   │
                                  │    .get_or_create() │
                                  │    → Conv(id=...)    │
                                  │                     │
                                  │ 4. MessageService    │
                                  │    .create(role=     │
                                  │     "user", ...)     │
                                  │                     │
                                  │ 5. Build history     │
                                  │    (last 20 msgs)    │
                                  │                     │
                                  │ 6. Get tools         │
                                  │    (Week 1: [])     │
                                  └─────────┬───────────┘
                                            │ messages[], tools[], prev_response_id
                                  ┌─────────▼───────────┐
                                  │ YAISResponsesProvider│
                                  │                     │
                                  │ POST /v1/responses   │
                                  │ {model, instructions,│
                                  │  input, tools,       │
                                  │  prev_response_id}   │
                                  └─────────┬───────────┘
                                            │
                              ┌─────────────┴─────────────┐
                              │                            │
                    ┌─────────▼────────┐    ┌─────────────▼──────────┐
                    │ output: message  │    │ output: function_call  │
                    │ "Привет! Чем..." │    │ name: "crm.lead.add"   │
                    └─────────┬────────┘    └─────────────┬──────────┘
                              │                            │
                              │                  ┌─────────▼──────────┐
                              │                  │ PluginRegistry     │
                              │                  │ .execute_tool()    │
                              │                  │ → Bitrix24 REST    │
                              │                  └─────────┬──────────┘
                              │                            │ tool result
                              │                  ┌─────────▼──────────┐
                              │                  │ YAIS .submit_tool  │
                              │                  │ _result()          │
                              │                  │ → output: message  │
                              │                  │ "Лид Иванов        │
                              │                  │  создан!"          │
                              │                  └─────────┬──────────┘
                              │                            │
                              └────────────┬───────────────┘
                                           │ text
                               ┌───────────▼──────────┐
                               │ MessageService       │
                               │ .create(role=        │
                               │  "assistant", ...)    │
                               │                      │
                               │ ConversationService  │
                               │ .update_prev_resp_id │
                               └───────────┬──────────┘
                                           │
                               ┌───────────▼──────────┐
                               │ MaxRESTClient        │
                               │ .send_message(       │
                               │   chat_id="456",     │
                               │   text="Привет!")    │
                               └───────────┬──────────┘
                                           │
                               ┌───────────▼──────────┐
                               │ Commit DB transaction │
                               └──────────────────────┘
```

### 5.2. Multi-turn диалог с previous_response_id

```
Turn 1:                          Turn 2:
POST /v1/responses              POST /v1/responses
{                               {
  instructions: "...",            instructions: "...",
  input: "Привет",               input: "Как дела?",
  tools: [...]                    tools: [...],
  // no previous_response_id      previous_response_id: "resp_1"
}                               }
        │                               │
        ▼                               ▼
Response:                        Response:
{                               {
  id: "resp_1",                   id: "resp_2",
  output: [{                      output: [{
    type: "message",                type: "message",
    text: "Здравствуйте!"          text: "Всё отлично!"
  }]                              }]
}                               }
        │                               │
        ▼                               ▼
prev_response_id = "resp_1"     prev_response_id = "resp_2"
(сохраняется в conversations)
```

### 5.3. Function call loop

```
Turn: "Создай лида Иванов Иван, телефон +79161234567"

     ┌─────────────────────────────────────────────┐
     │  1. YAIS: function_call                     │
     │  name: "crm.lead.add"                       │
     │  arguments: {"name":"Иванов Иван",          │
     │       "phone":"+79161234567"}               │
     │  call_id: "call_1"                          │
     │  response_id: "resp_3"                      │
     └──────────────┬──────────────────────────────┘
                    │
     ┌──────────────▼──────────────────────────────┐
     │  2. PluginRegistry.execute_tool()           │
     │  → Bitrix24Plugin.crm_lead_add()            │
     │  → REST POST to Bitrix24 webhook            │
     │  → Result: {"lead_id": 12345, "url": "..."} │
     └──────────────┬──────────────────────────────┘
                    │
     ┌──────────────▼──────────────────────────────┐
     │  3. Store tool result as Message            │
     │  role: "tool"                               │
     │  content: '{"lead_id": 12345, "url": "..."}'│
     │  tool_call_id: "call_1"                     │
     └──────────────┬──────────────────────────────┘
                    │
     ┌──────────────▼──────────────────────────────┐
     │  4. YAIS: submit_tool_result()              │
     │  previous_response_id: "resp_3"             │
     │  call_id: "call_1"                          │
     │  output: '{"lead_id": 12345, "url": "..."}' │
     └──────────────┬──────────────────────────────┘
                    │
     ┌──────────────▼──────────────────────────────┐
     │  5. YAIS response: message                  │
     │  text: "Лид Иванов Иван создан! ✅          │
     │   Ссылка: https://bitrix24/lead/12345"      │
     │  response_id: "resp_4"                      │
     └──────────────┬──────────────────────────────┘
                    │
     ┌──────────────▼──────────────────────────────┐
     │  6. Send text to MAX + store in DB          │
     └─────────────────────────────────────────────┘
```

### 5.4. MAX Webhook → Internal Router Mapping

```
MAX Server                          MultiBot Server
──────────                          ───────────────

POST /subscriptions
{ url: "https://multibot.example.com/api/v1/webhooks/maxx/amiri" }
                                                │
                                                ▼
                                        FastAPI Route:
                                        POST /api/v1/webhooks/maxx/amiri
                                                │
                                                ▼
                                        Извлечение company_slug="amiri"
                                                │
                                                ▼
                                        TenantManager.get_by_slug("amiri")
                                                │
                                                ▼
                                        Company(name="Amiri", slug="amiri", ...)
                                                │
                                                ▼
                                        MaxWebhookHandler.parse_incoming(payload)
                                                │
                                                ▼
                                        IncomingMessage(
                                            messenger="maxx",
                                            messenger_user_id="user_123",
                                            messenger_chat_id="chat_456",
                                            text="Привет!",
                                            company_slug="amiri"
                                        )
                                                │
                                                ▼
                                        MessageRouter.process_message(...)
```

### 5.5. Упрощённая диаграмма компонентов (Week 1)

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                   │
│                                                         │
│  ┌──────────────────────┐   ┌──────────────────────┐   │
│  │   Webhook Routes     │   │   Health Routes       │   │
│  │   POST /webhooks/    │   │   GET /health          │   │
│  │        maxx/{slug}   │   │   GET /health/ready    │   │
│  └──────────┬───────────┘   └──────────────────────┘   │
│             │                                           │
│  ┌──────────▼───────────┐                               │
│  │   MessageRouter      │  ← core/router.py            │
│  │                      │                               │
│  │  process_message()   │                               │
│  │  _process_ai_resp()  │                               │
│  └────┬────────────┬────┘                               │
│       │            │                                     │
│  ┌────▼────┐  ┌───▼──────────┐                          │
│  │  YAIS   │  │  Plugin       │  (Week 2: Bitrix24)    │
│  │ Provider│  │  Registry     │                          │
│  │ (ai/)   │  │  (plugins/)   │                          │
│  └─────────┘  └──────────────┘                          │
│       │                                                  │
│  ┌────▼────────────────────────────┐                    │
│  │  Service Layer                  │                    │
│  │  TenantManager, UserService,    │                    │
│  │  ConversationService,           │                    │
│  │  MessageService,                │                    │
│  │  IntegrationService             │                    │
│  └────┬────────────────────────────┘                    │
│       │                                                  │
│  ┌────▼────────────────────────────┐                    │
│  │  Database (async SQLAlchemy)    │                    │
│  │  PostgreSQL 16 + pgvector       │                    │
│  └─────────────────────────────────┘                    │
│                                                         │
│  ┌──────────────────────────────────┐                   │
│  │  Adapters                         │                   │
│  │  MaxMessengerAdapter              │                   │
│  │  ├── MaxRESTClient (HTTP)         │                   │
│  │  ├── MaxWebhookHandler (parse)    │                   │
│  │  └── MaxMessageFormatter (fmt)    │                   │
│  └──────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

---

## 6. Error Handling Strategy

### 6.1. Слои обработки ошибок

```
 Layer              Error Type            Strategy
 ─────────────────────────────────────────────────────────────
 HTTP (FastAPI)     Unhandled Exception   500 + log + trace_id
 Middleware         Request validation    422 + detail
 Routes             Tenant not found      404 + "Компания не найдена"
 Router             AI timeout            Retry 3x → friendly msg
 Router             Function call fail    Log + "Не удалось выполнить"
 Adapter (MAX)      Send fail             Retry 3x → log + skip
 Adapter (MAX)      Rate limit (30rps)    Throttle → queue
 AI Provider        HTTP 401/403          AIAuthError → log → admin
 AI Provider        HTTP 429              AIRateLimitError → retry 3x
 AI Provider        HTTP 5xx              AIProviderError → retry 2x
 AI Provider        Timeout (30s)         AITimeoutError → retry 1x
 Plugin (Week 2)    Bitrix24 down         ToolExecutionError → friendly
 Database           Connection lost       Pool retry → 500
```

### 6.2. Retry Policy

```python
# Общая retry-функция (может быть декоратором):
# async def retry_with_backoff(
#     func: Callable,
#     max_retries: int = 3,
#     base_delay: float = 1.0,
#     backoff_factor: float = 2.0,
#     retryable_exceptions: tuple = (AITimeoutError, AIRateLimitError, MessengerSendError),
# ) -> Any:
#     for attempt in range(max_retries):
#         try:
#             return await func()
#         except retryable_exceptions as e:
#             if attempt == max_retries - 1:
#                 raise
#             delay = base_delay * (backoff_factor ** attempt)
#             logger.warning(f"Retry {attempt+1}/{max_retries} after {delay:.1f}s", error=str(e))
#             await asyncio.sleep(delay)
```

### 6.3. User-Facing Error Messages

Все сообщения пользователю на русском, никогда не раскрывают внутренние детали:

| Ситуация | Сообщение |
|---------|----------|
| AI timeout / ошибка | "Извините, произошла ошибка при обработке запроса. Попробуйте позже." |
| AI rate limit | "Слишком много запросов. Пожалуйста, подождите несколько секунд." |
| Plugin error | "Не удалось выполнить операцию. Проверьте настройки интеграции." |
| Messenger send fail | (silent retry, если не удалось — логировать) |
| Tenant not found | HTTP 404, не возвращать тело (бот не переспрашивает) |
| Invalid payload | HTTP 200 + `{"status": "error"}` (MAX не должен ретраить) |

### 6.4. Логирование ошибок

Все ошибки логируются через structlog с контекстом:

```python
logger.error(
    "AI request failed",
    error=str(e),
    error_type=type(e).__name__,
    company_slug=company_slug,
    conversation_id=str(conv_id),
    attempt=attempt,
    request_id=request_id,  # из контекста (RequestIDMiddleware)
)
```

### 6.5. Circuit Breaker (опционально, Week 4)

Для Week 1 — простой retry. Week 4 — circuit breaker на AI провайдера и плагины.

---

## 7. Testing Strategy for Week 1

### 7.1. Тестовая пирамида (Week 1)

```
           ┌──────┐
           │ E2E  │  1 test: webhook → response
           │      │  (с тестовой БД + mock YAIS)
           ├──────┤
           │ Int. │  5 tests: роутер + БД, модели, сервисы
           │      │
           ├──────┤
           │ Unit │  25+ tests: YAIS client, MAX client, форматтеры,
           │      │  шифрование, tenant resolver, config, schemas
           └──────┘
```

### 7.2. Файлы тестов и что тестировать

| Файл | Тип | Что тестировать |
|------|-----|----------------|
| `tests/conftest.py` | — | Фикстуры: `test_db` (async session на тестовой БД), `mock_httpx`, `test_settings`, `sample_company` |
| `tests/test_core/test_config.py` | Unit | Загрузка Settings из `.env`, приоритет env vars, автогенерация encryption_key, подстановка folder_id в модель |
| `tests/test_core/test_security.py` | Unit | `EncryptionService.encrypt()` → `decrypt()` roundtrip, повреждённый токен → `ValueError`, пустой словарь |
| `tests/test_core/test_tenant.py` | Unit | `TenantManager.get_by_slug()`: успех, `TenantNotFoundError`, `TenantInactiveError` |
| `tests/test_core/test_models.py` | Unit | Создание моделей, relationships, unique constraints, каскадное удаление |
| `tests/test_core/test_services.py` | Int | `UserService.get_or_create()` (race condition через duplicate key), `ConversationService.get_or_create_active()`, `IntegrationService.save_config()` + `get_config()` с шифрованием |
| `tests/test_core/test_router.py` | Unit | `MessageRouter._messages_to_records()`, `_build_system_prompt()`, `_process_ai_response()` с mock AI, mock adapter |
| `tests/test_ai/test_yais_schemas.py` | Unit | Pydantic валидация: парсинг реального YAIS ответа (с function_call и message), невалидный JSON в arguments, пустой output[] |
| `tests/test_ai/test_yais_client.py` | Unit | `chat()` с mock HTTP: простой ответ, ответ с function_call, multi-turn с previous_response_id, ошибка 401, ошибка 429, таймаут |
| `tests/test_adapters/test_maxx_schemas.py` | Unit | Pydantic валидация MAX вебхук payload, callback_query |
| `tests/test_adapters/test_maxx_client.py` | Unit | `send_message()` с mock HTTP, `register_webhook()`, ошибка 403, ошибка 429 |
| `tests/test_adapters/test_maxx_webhook.py` | Unit | `MaxWebhookHandler.parse_incoming()`: обычное сообщение, callback_query, пустой текст |
| `tests/test_adapters/test_maxx_formatting.py` | Unit | `escape_markdown()`: спецсимволы, `build_inline_keyboard()`: структура |
| `tests/test_api/test_health.py` | Unit | `GET /health` → 200, `GET /health/ready` → 200/503 |
| `tests/test_api/test_webhooks.py` | Int | `POST /webhooks/maxx/test` с mock YAIS → 200, сообщение сохранено в БД, проверка `previous_response_id` |

### 7.3. Тестовая инфраструктура

**`tests/conftest.py`**:

```python
# Фикстуры:
#   - event_loop (session-scoped для всей тестовой сессии)
#   - test_settings → Settings() с тестовыми значениями
#   - test_engine → create_async_engine("postgresql+asyncpg://.../multibot_test")
#   - test_db_session → async session с транзакцией (rollback после каждого теста)
#   - mock_httpx_client → httpx.AsyncClient(transport=httpx.MockTransport(handler))
#   - yais_provider → YAISResponsesProvider с mock_httpx_client
#   - sample_company → создать Company в тестовой БД
#   - sample_user → создать User в тестовой БД
#   - test_app → FastAPI TestClient с переопределёнными зависимостями

# Для изоляции тестов БД: каждый тест в транзакции с rollback.
# Альтернатива: testcontainers с PostgreSQL (тяжелее, но реалистичнее).
```

### 7.4. Что НЕ тестировать в Week 1

- Реальные запросы к YAIS API (нужен API ключ, сеть)
- Реальные запросы к MAX API (нужен токен бота, сеть)
- PluginRegistry (пустой в Week 1)
- Bitrix24 plugin (Week 2)
- RAG engine (Week 3)
- Админ-панель (Week 3)
- Конкурентные запросы / нагрузочное тестирование (Week 4)

### 7.5. Coverage Target (Week 1)

| Слой | Цель |
|------|------|
| `src/core/config.py` | 90% |
| `src/core/security.py` | 95% |
| `src/core/tenant.py` | 90% |
| `src/core/models/` | 80% |
| `src/core/services/` | 85% |
| `src/core/router.py` | 70% (unit, integration в Week 4) |
| `src/ai/yais.py` | 80% (mocked HTTP) |
| `src/adapters/maxx/` | 85% (mocked HTTP) |
| `src/api/` | 80% |

---

## 8. Architectural Decisions Log

### AD-001: Один AI-провайдер (YAIS)

**Решение:** В MVP используется только Yandex AI Studio (YAIS). Никаких других AI-провайдеров.

**Обоснование:**
- GPT OSS 20B через Responses API поддерживает function calling на русском — все requirements закрыты
- YandexGPT-5-lite — fallback для простых ответов
- text-embeddings-v2 — для RAG (Week 3)
- Всё через один API-ключ и одну платформу
- Снижает сложность v0.1 на 30% по сравнению с мульти-провайдерной архитектурой

**Альтернатива отклонена:** OpenAI + DeepSeek + Yandex. Слишком сложно для MVP.

---

### AD-002: Responses API, не Chat Completions

**Решение:** Используем YAIS `/v1/responses` (Responses API), не `/v1/chat/completions`.

**Обоснование:**
- Нативный формат YAIS для GPT OSS 20B
- Встроенная поддержка function calling на русском
- Multi-turn через `previous_response_id` (сервер-side хранение контекста)
- Не нужно самостоятельно собирать conversation history в OpenAI-формате для каждого запроса
- YAIS сам управляет контекстом между ходами

**Риск:** API может измениться (бета). Митигация: абстракция AIProvider позволяет переключиться на Chat Completions без изменений в ядре.

---

### AD-003: MAX Messenger первым

**Решение:** Первый адаптер — MAX, не Telegram.

**Обоснование:**
- Полноценный Bot API: REST, вебхуки, Markdown/HTML, inline-клавиатуры, 30 rps
- Целевой рынок — РФ, где MAX активно используется
- API стабильный и документированный

**Альтернативы:** Telegram (v0.2), VK (v0.3).

---

### AD-004: Multi-tenant изоляция через company_slug в URL

**Решение:** Компания определяется по `company_slug` в URL вебхука: `POST /webhooks/maxx/{company_slug}`.

**Обоснование:**
- Каждая компания регистрирует свой вебхук в MAX со своим slug
- Не нужен API-ключ в заголовках для идентификации
- Простой и надёжный механизм
- Все последующие запросы к БД фильтруются по `company_id`

**Альтернатива отклонена:** JWT токены в заголовках. Слишком сложно для вебхуков (MAX не поддерживает кастомные заголовки).

---

### AD-005: Fernet для шифрования API-ключей

**Решение:** Используем `cryptography.fernet.Fernet` (AES-128-CBC + HMAC) для шифрования API-ключей в БД.

**Обоснование:**
- Простой API: `encrypt(bytes)` → `token`, `decrypt(token)` → `bytes`
- Встроенная проверка целостности (HMAC)
- Стандартная библиотека Python (`cryptography` — зависимость FastAPI/uvicorn)
- Достаточно для хранения API-ключей (не банковские данные)

**Альтернативы:** AES-256-GCM вручную. Больше кода, больше шансов ошибиться.

---

### AD-006: SQLAlchemy async + asyncpg

**Решение:** Асинхронный доступ к БД через `sqlalchemy[asyncio]` + `asyncpg`.

**Обоснование:**
- Неблокирующие запросы к БД в асинхронном FastAPI
- `asyncpg` — самый быстрый драйвер PostgreSQL для Python
- Поддержка `pgvector` через SQLAlchemy
- Совместимость с Alembic (асинхронный `env.py`)

---

### AD-007: PluginRegistry — ленивая загрузка

**Решение:** Плагины загружаются при старте приложения, tools регистрируются в памяти. Конфигурация компании (API-ключи для плагина) загружается лениво при первом вызове.

**Обоснование:**
- Не нужно на каждый запрос парсить `manifest.yaml`
- Конфигурация per-company может быть разной
- При добавлении нового плагина достаточно рестарта (или hot-reload в будущем)

**Процесс загрузки (Week 2):**
1. `PluginRegistry.load_plugins("src/plugins/")` — сканирует поддиректории
2. Для каждой: читает `manifest.yaml` → валидирует → создаёт экземпляр плагина
3. `get_tools_for_ai(company_id)` — собирает tools со всех активных плагинов компании

---

### AD-008: Структура БД — отдельная таблица messages, не JSONB в conversations

**Решение:** Сообщения хранятся в отдельной таблице `messages`, не в JSONB-поле внутри `conversations`.

**Обоснование:**
- Индексация по `conversation_id` + `created_at` для быстрого получения истории
- Возможность аналитики: подсчёт токенов, поиск по сообщениям
- Поддержка пагинации для длинных диалогов
- Совместимость с RAG (поиск по content)

**Альтернатива отклонена:** JSONB поле `history` в `conversations`. Меньше joins, но плохо для аналитики и поиска.

---

### AD-009: Empty PluginRegistry для Week 1

**Решение:** В Week 1 `PluginRegistry` — stub, возвращает пустой список tools. Полная реализация — Week 2.

**Обоснование:**
- End-to-end диалог работает без плагинов (текстовые ответы)
- Не блокирует демонстрацию работы MAX + YAIS
- Week 2 добавляет function calling без изменения архитектуры ядра

---

### AD-010: System prompt из Company.settings

**Решение:** Системный промпт для AI хранится в `companies.settings` (JSONB), а не в отдельной таблице.

**Обоснование:**
- Один промпт на компанию — не нужна отдельная таблица
- JSONB позволяет добавлять поля без миграций
- В будущем: разные промпты для разных сценариев можно добавить как ключи в `settings`

**Формат:** `settings.system_prompt` — строка. Если отсутствует — используется дефолтный промпт.

---

## Итоговая проверка Week 1

### Definition of Done (Week 1)

- [ ] `docker compose up -d` поднимает PostgreSQL и Redis
- [ ] `alembic upgrade head` создаёт все 5 таблиц
- [ ] `python -m src.main` запускает FastAPI на :8000
- [ ] `GET /health` возвращает `{"status": "ok"}`
- [ ] `GET /health/ready` проверяет БД
- [ ] `POST /api/v1/webhooks/maxx/test` обрабатывает тестовый вебхук
- [ ] Сообщение пользователя сохраняется в БД
- [ ] AI (YAIS) вызывается и возвращает ответ
- [ ] Ответ сохраняется в БД и отправляется в MAX
- [ ] `previous_response_id` обновляется для multi-turn
- [ ] API-ключ в `integrations.config` зашифрован Fernet
- [ ] Все юнит-тесты проходят (pytest, >25 тестов)
- [ ] Логи структурированные (JSON) с trace_id

### Что НЕ входит в Week 1 (но готово для Week 2)

- Plugin system (скелет есть, нет загрузки manifest.yaml)
- Bitrix24 REST клиент (скелет есть, нет реальных вызовов)
- Function calling dispatch (логика в роутере готова, нет плагинов)
- Admin panel (роуты заготовлены, пустые)
- RAG engine
- Fallback на YandexGPT-5-lite
- Интеграция с Redis
- Prometheus метрики

---

**Конец ARCHITECT_PLAN.md**
