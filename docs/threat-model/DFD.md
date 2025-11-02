# Data Flow Diagram (DFD)

## Обзор
Данная диаграмма показывает основные потоки данных в SecDev Course App и границы доверия.

## Границы доверия
- **Client Zone** (Untrusted): Браузер пользователя, внешние клиенты
- **Edge Zone** (DMZ): API Gateway, Load Balancer
- **Core Zone** (Trusted): Application Server, Business Logic
- **Data Zone** (Highly Trusted): Database, Secrets Storage

## DFD Schema
```mermaidgraph TB
subgraph "Client Zone (Untrusted)"
User[User/Browser]
endsubgraph "Edge Zone (DMZ)"
    API[API Gateway/FastAPI]
endsubgraph "Core Zone (Trusted)"
    App[Application Logic]
    Valid[Input Validator]
    Auth[Auth Service]
endsubgraph "Data Zone (Highly Trusted)"
    DB[(Database)]
    Logs[(Security Logs)]
endUser -->|F1: HTTPS POST /items| API
User -->|F2: HTTPS GET /items/{id}| API
User -->|F3: HTTPS GET /health| APIAPI -->|F4: Validate Input| Valid
Valid -->|F5: Pass to Logic| AppAPI -->|F6: Auth Check| Auth
Auth -->|F7: Token Validation| AuthApp -->|F8: Store Item| DB
App -->|F9: Query Item| DBApp -->|F10: Log Events| Logs
Valid -->|F11: Log Validation Errors| Logs

## Описание потоков данных

### Клиентские потоки (Client → Edge)

**F1: HTTPS POST /items**
- **Источник:** User/Browser (Untrusted)
- **Назначение:** API Gateway (DMZ)
- **Протокол:** HTTPS
- **Данные:** JSON {name: string}
- **Угрозы:** Spoofing, Tampering, Injection
- **Контроли:** TLS, Input Validation, Rate Limiting

**F2: HTTPS GET /items/{id}**
- **Источник:** User/Browser (Untrusted)
- **Назначение:** API Gateway (DMZ)
- **Протокол:** HTTPS
- **Данные:** item_id (integer)
- **Угрозы:** Information Disclosure, DoS
- **Контроли:** TLS, Authorization, Rate Limiting

**F3: HTTPS GET /health**
- **Источник:** Monitoring System (Trusted)
- **Назначение:** API Gateway (DMZ)
- **Протокол:** HTTPS
- **Данные:** None
- **Угрозы:** Information Disclosure
- **Контроли:** Minimal data exposure

### Внутренние потоки (Edge → Core)

**F4: Validate Input**
- **Источник:** API Gateway (DMZ)
- **Назначение:** Input Validator (Core)
- **Протокол:** Internal
- **Данные:** User input
- **Угрозы:** Injection, Tampering
- **Контроли:** NFR-004 (100% validation)

**F5: Pass to Logic**
- **Источник:** Input Validator (Core)
- **Назначение:** Application Logic (Core)
- **Протокол:** Internal
- **Данные:** Validated input
- **Угрозы:** Logic bugs
- **Контроли:** Unit tests, Type checking

**F6-F7: Auth Check & Token Validation**
- **Источник:** API Gateway (DMZ)
- **Назначение:** Auth Service (Core)
- **Протокол:** Internal
- **Данные:** JWT token
- **Угрозы:** Spoofing, Elevation of Privilege
- **Контроли:** NFR-006 (TTL ≤ 1 hour)

### Потоки данных (Core → Data)

**F8: Store Item**
- **Источник:** Application Logic (Core)
- **Назначение:** Database (Data)
- **Протокол:** Internal/DB Protocol
- **Данные:** Item record
- **Угрозы:** Tampering, Information Disclosure
- **Контроли:** Encryption at rest, Access control

**F9: Query Item**
- **Источник:** Application Logic (Core)
- **Назначение:** Database (Data)
- **Протокол:** Internal/DB Protocol
- **Данные:** SQL query
- **Угрозы:** SQL Injection, Information Disclosure
- **Контроли:** Parameterized queries, ORM

**F10-F11: Log Events**
- **Источник:** App/Validator (Core)
- **Назначение:** Security Logs (Data)
- **Протокол:** Internal
- **Данные:** Log entries
- **Угрозы:** Tampering, Repudiation
- **Контроли:** NFR-007 (100% security events logged)

## Элементы системы

### Внешние сущности (External Entities)
1. **User/Browser** - Конечный пользователь (Untrusted)
2. **Monitoring System** - Система мониторинга (Trusted)

### Процессы (Processes)
1. **API Gateway** - Точка входа (Edge)
2. **Input Validator** - Валидация данных (Core)
3. **Application Logic** - Бизнес-логика (Core)
4. **Auth Service** - Аутентификация (Core)

### Хранилища данных (Data Stores)
1. **Database** - Основное хранилище (Data)
2. **Security Logs** - Логи безопасности (Data)

## Альтернативный сценарий: Ошибка валидации
```mermaidgraph TB
User[User] -->|F1: Invalid Input| API[API Gateway]
API -->|F4: Validate| Valid[Validator]
Valid -->|F11: Log Error| Logs[(Logs)]
Valid -->|F12: Return 422| API
API -->|F13: Error Response| User

**Описание:**
- Пользователь отправляет некорректные данные
- Валидатор отклоняет запрос
- Ошибка логируется (NFR-007)
- Пользователь получает понятное сообщение об ошибке (NFR-003)

## Метаданные

- **Версия DFD:** 1.0
- **Дата:** 2024-10-14
- **Автор:** Student
- **Статус:** Draft для P04
