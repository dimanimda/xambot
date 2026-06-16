# План реализации MultiBot MVP v0.1

**Статус:** НА АППРУВЕ (v2 — упрощён после тестирования YAIS)
**Режим работы:** План → Аппрув → Выполнение (L7-стиль)

---

## Этап 0: Подготовка

- [x] ТЗ утверждено
- [x] MAX API подтверждён (`platform-api.max.ru`, REST, вебхуки, кнопки, 30 rps)
- [x] Yandex AI Studio: API-ключ работает, GPT OSS 20B → function calling на русском ✅
- [x] YAIS function calling протестирован: Responses API, `tools` → `function_call` output
- [ ] MAX: дождаться токена бота (~24h)

**Ключевое открытие:** YAIS GPT OSS 20B через Responses API поддерживает
function calling на русском. DeepSeek v4-pro для tool calls НЕ НУЖЕН.
Весь AI-слой — один провайдер (YAIS), один API-ключ.

---

## Архитектура (финальная)

```
MAX Messenger ← REST webhook → FastAPI Core
                                  ├── YAIS AI Provider (единственный)
                                  │   ├── chat: GPT OSS 20B (Responses API, function calling)
                                  │   ├── fallback: YandexGPT-5-lite (Chat Completions)
                                  │   └── embeddings: text-embeddings-v2 (RAG)
                                  ├── Plugin Registry
                                  │   └── Bitrix24 REST Plugin
                                  └── Multi-tenant DB (PostgreSQL + pgvector)
```

**Формат Responses API (YAIS):**
```python
POST /v1/responses
{
  "model": "gpt://{folder}/gpt-oss-20b/latest",
  "instructions": "Ты CRM-ассистент...",   # system prompt
  "input": "Создай лида...",                # user message
  "tools": [{                               # function definitions
    "type": "function",
    "name": "create_lead",
    "description": "Создать лида в CRM",
    "parameters": { ... }                   # JSON Schema
  }]
}
→ output[]: function_call | message | reasoning
→ multi-turn: previous_response_id
```

---

## План работ (4 недели)

### Неделя 1: Ядро + MAX + Базовый AI

| # | Задача | Детали |
|---|--------|--------|
| 1 | Инициализация проекта | FastAPI, SQLAlchemy async, Docker, структура `core/`, `adapters/`, `plugins/` |
| 2 | Multi-tenant модель | Company, User, Integration — миграции, CRUD, шифрование ключей |
| 3 | YAIS AI Provider | `ai/provider.py`: класс `YAISProvider` → `chat()`, `embed()` через Responses API |
| 4 | MAX Adapter | REST-клиент `platform-api.max.ru`, webhook handler, send message (Markdown), callback buttons |
| 5 | End-to-end диалог | MAX webhook → Router → YAIS → ответ в MAX |

### Неделя 2: Plugin System + Bitrix24 + Function Calling

| # | Задача | Детали |
|---|--------|--------|
| 6 | Plugin Registry | Загрузка `manifest.yaml`, валидация, регистрация tools в рантайме |
| 7 | Function Calling Dispatcher | YAIS → `function_call` → найти плагин → выполнить → результат → YAIS → ответ |
| 8 | Bitrix24 Plugin | REST-клиент, tools: `crm.lead.add`, `crm.deal.list`, `crm.deal.get` |
| 9 | End-to-end CRM | «Создай лида Иванов» → tool_call → Bitrix24 → лид создан → ссылка пользователю |

### Неделя 3: RAG + Админка

| # | Задача | Детали |
|---|--------|--------|
| 10 | RAG Engine | Загрузка PDF/DOCX/TXT, чанкинг, эмбеддинги через YAIS, pgvector |
| 11 | RAG Retrieval | Поиск по документам → инжект в `instructions` → ответ с источником |
| 12 | Web-админка | FastAPI + Jinja2: компании, интеграции, документы, статус, логи |
| 13 | Документация | README, docker-compose.yml, инструкция по деплою on-premise |

### Неделя 4: Тесты + Безопасность + 7-агентный ревью

| # | Задача | Детали |
|---|--------|--------|
| 14 | Безопасность | AES-256 шифрование ключей в БД, audit log, HTTPS enforce |
| 15 | Тесты | pytest (core, adapters, plugins), CI через GitHub Actions |
| 16 | 7-агентный код-ревью | Architect→Reviewer→Fixer→Security→Design→TODO Finder |
| 17 | Демо | Инстанс для beta-тестеров, приглашение |

---

## Ключевые решения

| Решение | Причина |
|---------|---------|
| **Один AI-провайдер** (YAIS) | GPT OSS 20B закрывает chat + function calling + embeddings |
| **Responses API, не Chat Completions** | Нативный формат YAIS, поддерживает function calling на русском |
| **MAX первым** | API полноценное, целевой рынок — РФ |
| **Bitrix24 первой интеграцией** | Твоя экспертиза, готовый MCP |
| **On-premise деплой** | Клиенты ставят Docker у себя |

---

## Метрики MVP

| Метрика | Цель |
|---------|------|
| Ответ бота | < 5 сек (без учёта AI) |
| Компаний на инстансе | до 50 (4 vCPU, 8 GB RAM) |
| Деплой | `docker compose up -d` (5 минут) |
| Точность function calling | > 90% на типовых CRM-сценариях |

---

## Что НЕ входит в MVP

- Telegram, VK адаптеры → v0.2–v0.3
- amoCRM → v0.2
- Голос / SpeechKit → v0.4
- Календари / Таблицы → v0.2–v0.3
- SaaS-хостинг → v0.5
- Биллинг → v0.5
