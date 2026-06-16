# Техническое задание: MultiBot — мультимессенджерная AI-платформа для бизнеса

**Версия:** 0.1 (драфт)  
**Дата:** 16.06.2026  
**Статус:** На аппруве

---

## 1. Видение продукта

**MultiBot** — это on-premise платформа для создания AI-ассистентов в популярных мессенджерах (Telegram, MAX, VK), подключаемая к CRM, календарям и таблицам российских и международных сервисов.

**Ценность для клиента:** сотрудники общаются с ботом в привычном мессенджере, а бот:
- Отвечает на вопросы, используя RAG на документах компании
- Создаёт лиды / сделки в CRM голосом или текстом
- Записывает в календарь, ищет данные в таблицах
- Работает через российские AI (YandexGPT) или локальные модели (OpenAI-совместимые)

**Модель распространения:** клиент получает Docker-образ, разворачивает на своём сервере, подключает свои API-ключи и интеграции. SaaS-версия — опционально, для тех, кто не хочет возиться с сервером.

---

## 2. Целевая аудитория

**Первичная:** компании малого и среднего бизнеса РФ, уже использующие:
- Bitrix24 или amoCRM как CRM
- Telegram / VK / MAX для общения с клиентами
- Yandex Cloud для инфраструктуры

**Вторичная:** компании с собственным IT-отделом, желающие хостить AI-ассистента локально (через OpenAI-совместимые модели).

---

## 3. Функциональные требования

### 3.1. Ядро (MVP — v0.1)

| ID | Требование | Приоритет |
|----|-----------|-----------|
| C1 | Приём сообщений из мессенджера, маршрутизация к AI | P0 |
| C2 | Диалоговый контекст (история сообщений, state machine) | P0 |
| C3 | AI-ответ через YandexGPT (Yandex AI Studio) с function calling | P0 |
| C4 | Регистрация компании-клиента (multi-tenant), изоляция данных | P0 |
| C5 | Подключение API-ключей клиента (Yandex, CRM, мессенджеры) | P0 |
| C6 | Базовая веб-админка: настройки бота, статус интеграций | P1 |
| C7 | Логирование диалогов для аудита (по компании) | P1 |

### 3.2. Мессенджеры (очередь реализации)

| ID | Мессенджер | MVP |
|----|-----------|-----|
| M1 | MAX Messenger | ✅ v0.1 |
| M2 | Telegram Bot API | v0.2 |
| M3 | VK Messenger | v0.3 |

**Обоснование:** MAX API подтверждён — `platform-api.max.ru`, REST, вебхуки,
Markdown/HTML, inline-клавиатуры, file upload, 30 rps. Полноценный Bot API.

**Архитектурное требование:** каждый мессенджер — отдельный adapter, реализующий интерфейс `MessengerAdapter`. Добавление нового мессенджера не требует изменений в ядре.

### 3.3. AI-провайдеры

| ID | Провайдер | MVP |
|----|----------|-----|
| A1 | Yandex AI Studio (GPT OSS 20B) — Responses API, function calling | ✅ v0.1 |
| A2 | Yandex AI Studio (YandexGPT-5-lite) — Chat Completions, fallback | ✅ v0.1 |
| A3 | OpenAI-совместимый локальный (vLLM, llama.cpp) | v0.3 |

**Требования к AI-слою:**
- Единый интерфейс `AIProvider.chat(messages, tools)` → ответ
- Primary: GPT OSS 20B через Responses API (`/v1/responses`) — function calling на русском
- Fallback: YandexGPT-5-lite через Chat Completions (`/v1/chat/completions`) — дешёвый
- Embeddings: `text-embeddings-v2` через `emb://` (Yandex)
- Multi-turn: через `previous_response_id` в Responses API
- **Один API-ключ, одна платформа** — YAIS закрывает всё

### 3.4. Интеграции (Tools)

| ID | Интеграция | MVP | Что умеет |
|----|-----------|-----|-----------|
| T1 | Bitrix24 REST | ✅ v0.1 | Создание лида, поиск сделок, статусы |
| T2 | amoCRM | v0.2 | Аналогично Bitrix24 |
| T3 | Yandex Calendar | v0.2 | Создание встреч, проверка занятости |
| T4 | Google Calendar | v0.3 | Аналогично Yandex |
| T5 | Google Sheets | v0.3 | Чтение/запись данных |
| T6 | Yandex Sheets (Яндекс.Документы) | v0.3 | Аналогично Google |
| T7 | Вебхуки (generic) | v0.2 | Клиент настраивает URL → бот дёргает при событии |

**Архитектурное требование:** каждая интеграция — отдельный Python-пакет в `plugins/` с манифестом `manifest.yaml`. Ядро регистрирует инструменты плагина и передаёт их AI как `tools`.

### 3.5. RAG (Retrieval-Augmented Generation)

| ID | Требование | Приоритет |
|----|-----------|-----------|
| R1 | Загрузка документов компании (PDF, DOCX, TXT, Markdown) | P1 |
| R2 | Эмбеддинги через YandexGPT Embeddings API | P1 |
| R3 | Поиск по документам при ответе на вопрос пользователя | P1 |
| R4 | Указание источника в ответе («Согласно документу X...») | P2 |

---

## 4. Нефункциональные требования

| ID | Требование | Детали |
|----|-----------|--------|
| N1 | **On-premise деплой** | Единый `docker-compose.yml`, поднимается за 5 минут |
| N2 | **Multi-tenant изоляция** | Данные компании A не видны компании B. Отдельные API-ключи, контексты, документы |
| N3 | **Безопасность** | API-ключи в БД зашифрованы (AES-256). Бекап БД — одной командой |
| N4 | **Отказоустойчивость** | Если YandexGPT недоступен → очередь с retry, уведомление админа |
| N5 | **Производительность** | Ответ бота < 5 секунд для типового вопроса (без учёта AI-задержки) |
| N6 | **Масштабируемость** | От 1 до ~50 компаний на одном инстансе (4 vCPU, 8 GB RAM) |
| N7 | **Локализация** | Интерфейс админки и промпты — русский. База знаний клиента — любой язык |

---

## 5. Архитектура

### 5.1. Слои

```
┌─────────────────────────────────────────────────────┐
│                   Web Admin UI                       │
│           (FastAPI + Jinja2 / React)                │
├─────────────────────────────────────────────────────┤
│                  Core Engine                         │
│                                                      │
│  ┌──────────┐  ┌───────────┐  ┌──────────────────┐ │
│  │ Router   │  │ State     │  │ Plugin Registry  │ │
│  │ (intent) │  │ Machine   │  │ (hot-plug tools) │ │
│  └──────────┘  └───────────┘  └──────────────────┘ │
│                                                      │
│  ┌──────────┐  ┌───────────┐  ┌──────────────────┐ │
│  │ Tenant   │  │ AI        │  │ RAG Engine       │ │
│  │ Manager  │  │ Dispatcher│  │ (embed + search) │ │
│  └──────────┘  └───────────┘  └──────────────────┘ │
├─────────────────────────────────────────────────────┤
│                 Adapter Layer                        │
│  ┌──────────┐  ┌───────────┐  ┌──────────────────┐ │
│  │ Telegram │  │ YandexGPT │  │ Bitrix24 Plugin  │ │
│  │ Adapter  │  │ Provider  │  │ (REST + webhooks) │ │
│  └──────────┘  └───────────┘  └──────────────────┘ │
│  ┌──────────┐  ┌───────────┐  ┌──────────────────┐ │
│  │ MAX      │  │ OpenAI    │  │ amoCRM Plugin    │ │
│  │ Adapter  │  │ compat.   │  │ (HTTP API)       │ │
│  └──────────┘  └───────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### 5.2. Поток сообщения

```
1. User → Telegram → Webhook → Core Router
2. Router → Tenant Manager (определяет компанию)
3. Router → AI Dispatcher → YandexGPT.chat(messages, tools)
4. Два исхода:
   a) AI возвращает text → Router → Telegram → User
   b) AI возвращает tool_call → Plugin Registry → Bitrix24.add_lead()
      → результат → Router → AI (продолжение диалога) → ответ → User
```

### 5.3. Плагин-система

Формат плагина:

```
plugins/bitrix24/
  manifest.yaml    ← метаданные и список tools
  __init__.py      ← класс Bitrix24Plugin
  client.py        ← REST-клиент
  models.py        ← pydantic-модели
```

`manifest.yaml`:
```yaml
name: bitrix24
version: 1.0.0
description: "Bitrix24 REST API integration"
config_fields:
  - name: webhook_url
    label: "URL вебхука Bitrix24"
    type: string
    required: true
  - name: client_id
    label: "Client ID (если OAuth)"
    type: string
    required: false
tools:
  - name: crm.lead.add
    description: "Создать нового лида в CRM"
    parameters:
      name: { type: string, description: "Имя контакта", required: true }
      phone: { type: string, description: "Телефон", required: false }
      email: { type: string, description: "Email", required: false }
      source: { type: string, description: "Источник лида" }
  - name: crm.deal.list
    description: "Найти сделки по фильтру"
    parameters:
      stage: { type: string, description: "Стадия сделки" }
      assigned: { type: string, description: "ID ответственного" }
```

---

## 6. Технологический стек

| Слой | Технология | Обоснование |
|------|-----------|------------|
| **Язык** | Python 3.12+ | Быстрая разработка, асинхронность, ML-экосистема |
| **Фреймворк** | FastAPI | Webhook'и + админка в одном, авто-docs |
| **Асинхронность** | asyncio + httpx | Неблокирующие вызовы API |
| **База данных** | PostgreSQL 16 + pgvector | Реляционные данные + эмбеддинги для RAG |
| **ORM** | SQLAlchemy 2.0 (async) | Зрелая, асинхронная |
| **Кеш/очереди** | Redis | Сессии диалогов, фоновая очередь |
| **Мессенджеры** | aiogram 3.x (Telegram), кастомные адаптеры | aiogram — зрелый |
| **AI SDK** | openai Python SDK (для YandexGPT через OpenAI-совместимый эндпоинт) | Единый клиент |
| **RAG** | langchain (только embeddings + retrievers, без агентов) | Зрелый |
| **Деплой** | Docker + docker-compose | On-premise — единая команда |
| **Админка** | Jinja2 + htmx (MVP), React (позже) | Минимум JS для v0.1 |
| **Мониторинг** | Prometheus + Grafana (опционально в compose) | Для клиентов с IT |

---

## 7. База данных (концептуальная схема)

```sql
-- Компании (tenants)
companies: id, name, slug, created_at, settings (JSONB)

-- Пользователи (сотрудники компании, общающиеся с ботом)
users: id, company_id, messenger, messenger_user_id, name, phone, role

-- Диалоги
conversations: id, company_id, user_id, messenger, status, started_at, last_message_at

-- Сообщения
messages: id, conversation_id, role (user/assistant/tool), content, 
          tool_calls (JSONB), created_at

-- Настройки интеграций (API-ключи и т.д.)
integrations: id, company_id, plugin_name, config (JSONB, encrypted), enabled

-- Документы для RAG
documents: id, company_id, filename, content, chunks (JSONB), 
           embedding MODEL, created_at

-- Embedding-чанки
document_chunks: id, document_id, chunk_text, embedding (vector(1536)), 
                 metadata (JSONB)
```

---

## 8. План реализации (MVP v0.1)

### Этап 0: Подготовка (сегодня)
- [x] Утверждение ТЗ
- [x] Подтверждён MAX API (`platform-api.max.ru`, REST, вебхуки)
- [ ] Регистрация бота в MAX, получение токена
- [ ] Регистрация в Yandex AI Studio, получение тестового ключа

### Этап 1: Ядро + MAX + YandexGPT (неделя 1)
- [ ] Шаблон проекта (FastAPI + SQLAlchemy + Docker)
- [ ] Multi-tenant модель (Company, User)
- [ ] **MAX adapter** (REST client, webhook handler, message send/receive)
- [ ] YandexGPT provider (через OpenAI-compatible API)
- [ ] Базовый диалог: сообщение → AI → ответ

### Этап 2: Plugin System + Bitrix24 (неделя 2)
- [ ] Plugin registry (загрузка manifest.yaml, валидация)
- [ ] Function calling: ядро передаёт tools в AI, обрабатывает tool_call
- [ ] Bitrix24 REST plugin (crm.lead.add, crm.deal.list)
- [ ] Webhook-сервер для Bitrix24 (обратные вызовы)

### Этап 3: Админка + RAG (неделя 3)
- [ ] Web-админка (FastAPI + Jinja2): компании, интеграции, статус
- [ ] RAG: загрузка документов, эмбеддинги, поиск
- [ ] Документация по развёртыванию (README, docker-compose)

### Этап 4: Полировка (неделя 4)
- [ ] Логирование + аудит
- [ ] Шифрование API-ключей
- [ ] Тесты (pytest)
- [ ] Демо-инстанс для beta-тестеров

---

## 9. Что НЕ входит в MVP (но запланировано)

- ❌ Telegram, VK адаптеры → v0.2–v0.3
- ❌ amoCRM → v0.2
- ❌ Голосовые сообщения (SpeechKit) → v0.4
- ❌ Календари / Таблицы → v0.2–v0.3
- ❌ SaaS-версия (multi-tenant хостинг) → v0.5
- ❌ Биллинг / подписки → v0.5
- ❌ Мобильное приложение → не планируется
- ❌ Визуальный конструктор диалогов → не планируется (бот управляется AI, а не скриптами)

---

## 10. Бизнес-модель (контур)

| Тариф | Цена | Что входит |
|-------|------|-----------|
| **Free** | 0 ₽ | 1 компания, 1 мессенджер, 1 AI, без RAG, community support |
| **Pro** | 15 000 ₽/мес | До 3 мессенджеров, RAG, приоритетная поддержка |
| **Enterprise** | Кастом | Исходники, on-premise без ограничений, доработки |

**Старт:** первые 3–5 клиентов бесплатно (beta), взамен — обратная связь и кейсы для портфолио.

---

## 11. Риски

| Риск | Вероятность | Митигация |
|------|------------|-----------|
| MAX API непубличный / ограниченный | Средняя | Начать с Telegram, MAX — когда будет API |
| YandexGPT function calling нестабилен | Средняя | Fallback на локальную OpenAI-совместимую модель |
| Клиенты не хотят on-premise | Низкая | Добавить SaaS-опцию (v0.5) |
| Низкое качество RAG на русском | Средняя | YandexGPT Embeddings специфичны для русского |

---

## 12. Вопросы, требующие уточнения

1. **MAX Messenger API** — есть ли документация? Контакты в VK?
2. **Yandex AI Studio** — какой именно Plan (тестовый / платный)? Есть ли ограничения на function calling?
3. **Bitrix24** — REST или вебхуки? OAuth или входящие вебхуки?
4. **amoCRM** — какой способ интеграции предпочтительнее (OAuth / API-ключ)?
5. **Хранение документов** — клиенты грузят через админку, или бот принимает файлы прямо в чате?
