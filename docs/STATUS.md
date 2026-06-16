# MultiBot — Статус Этапа 1 (Week 1)

**Дата:** 17 июня 2026  
**Версия:** 0.1.0-dev  
**Репозиторий:** github.com/dimanimda/xambot

---

## Резюме

За 1 сессию (≈2 часа) 7 AI-агентов спроектировали и реализовали ядро
мультимессенджерной AI-платформы: FastAPI, PostgreSQL, YAIS (Yandex AI Studio),
MAX Messenger adapter, multi-tenant изоляция, function calling.

---

## Конвейер агентов

| # | Агент | Роль | Результат |
|---|-------|------|-----------|
| 1 | **Architect** (Pi) | Проектирование | `ARCHITECT_PLAN.md` — 3409 строк, 10 ADR, 5 диаграмм |
| 2 | **Builder** (Pi) | Инициализация | 45 файлов: pyproject, Docker, конфиги, Alembic |
| 3 | **Builder** (Pi) | Модели + сервисы | 5 таблиц PostgreSQL, CRUD-сервисы, шифрование |
| 4 | **Builder** (Pi) | YAIS Provider | Responses API, function calling, fallback (459 строк) |
| 5 | **Builder** (Pi) | MAX Adapter | REST client, webhook, Markdown/HTML, клавиатуры |
| 6 | **Builder** (Pi) | End-to-end | MessageRouter, webhook endpoint, multi-turn |
| 7 | **Reviewer** (Pi) | Код-ревью | 26 находок (P0:3, P0.5:2, P1:4, P2:6...) |
| 8 | **Security Rev.** (Pi) | Сканирование | 11 находок (2 CRITICAL, 2 HIGH) |
| 9 | **Fixer** (Pi) | Исправления | P0/P0.5 закрыты (engine leak, CORS, webhook auth) |
| 10 | **TODO Finder** (Pi) | Зачистка | 7 плановых заглушек (Week 2) |

---

## Проект

| Метрика | Значение |
|---------|----------|
| Файлов `.py` | 60+ |
| Строк кода | ~4000 |
| Таблиц БД | 5 |
| API роутов | 7 |
| Моделей Pydantic | 15+ |
| Env vars | 20+ |

---

## Архитектура

```
MAX Messenger ← webhook → FastAPI Core
                            ├── YAIS AI Provider (GPT OSS 20B, function calling)
                            ├── Plugin Registry (Bitrix24 — Week 2)
                            └── PostgreSQL + pgvector
```

- **Multi-tenant:** изоляция через `company_slug` в URL вебхука
- **AI:** единый провайдер (YAIS Responses API), fallback YandexGPT-5-lite
- **Шифрование:** Fernet (AES-128-CBC + HMAC) для API-ключей в БД
- **Логирование:** structlog JSON с request_id

---

## Definition of Done (Week 1)

- [x] 5 таблиц PostgreSQL (Alembic: 001_initial_schema)
- [x] `GET /health` → `{"status":"ok","version":"0.1.0"}`
- [x] `GET /health/ready` → проверка БД
- [x] `POST /api/v1/webhooks/maxx/{slug}` → YAIS → ответ
- [x] Multi-turn диалоги через `previous_response_id`
- [x] Fernet-шифрование API-ключей
- [x] JSON-логи с request_id
- [x] Webhook signature verification
- [x] CORS настроен
- [ ] 25+ тестов → Week 2

---

## План на Week 2

1. **Тесты** — pytest, покрытие ядра и адаптеров
2. **Plugin Registry** — загрузка manifest.yaml, валидация tools
3. **Bitrix24 Plugin** — REST-клиент, crm.lead.add, crm.deal.list
4. **Function calling → плагины** — связка YAIS tool_call → plugin.execute
5. **Интеграционный тест** — с реальным MAX-токеном (ждём)
