# API Contract v1 (UI <-> Backend)

Base URL: `http://localhost:8080`

## Auth

### `POST /auth/login`
Request:

```json
{
  "email": "user@example.com",
  "password": "secret"
}
```

Response `200`:

```json
{
  "authUserId": 1,
  "email": "user@example.com",
  "isActive": true,
  "createdAt": "2026-03-20T12:00:00Z",
  "lastLogin": "2026-03-20T12:00:00Z",
  "passwordHash": ""
}
```

### `POST /auth/logout`
Response: `204 No Content`

## Sessions

### `GET /sessions`
Response `200`: массив сессий **только созданных текущим пользователем** (`created_by = sub` из JWT). Участники, переходящие по прямой ссылке на `/meet/:id`, список чужих созвонов не видят — только организатор планирует и делится ссылкой.

### `POST /sessions`
Request:

```json
{
  "title": "Interview with candidate",
  "sessionType": "interview",
  "startDatetime": "2026-03-20T12:30",
  "endDatetime": "2026-03-20T13:30",
  "description": "Technical round",
  "locationType": "online",
  "physicalLocation": ""
}
```

Response `201`: created session object.

### `GET /sessions/:id`
Response `200`: объект сессии по id (любой аутентифицированный пользователь может открыть по ссылке для входа на звонок).

### `GET /sessions/:id/chat/messages`
Query: `limit` (optional, default 100, max 200).

Response `200`:

```json
{
  "messages": [
    {
      "chat_message_id": 1,
      "session_id": 2,
      "participant_id": "p_abc",
      "client_message_id": "uuid-from-client",
      "sender_name": "You",
      "body": "hello",
      "created_at": "2026-05-01T12:00:00.000Z"
    }
  ]
}
```

Auth: same as other session routes (cookie / Bearer). Live delivery uses WebSocket `chat_message`; successful inserts include `chat_message_id` in the broadcast payload.

### Session analysis (persisted WS analytics)

#### `GET /sessions/:id/analysis/report`

- Доступен только **организатору** сессии (`session.created_by` = текущий пользователь). Агрегированный ответ содержит данные всех участников — гостям по ссылке недоступен (`403`).
- Устаревшие строки без `created_by`: отчёт читают все аутентифицированные пользователи (обратная совместимость).

#### `GET /sessions/:id/analysis/events`

Query-параметры:

| Параметр | Описание |
|----------|----------|
| `limit` | По умолчанию `100`, максимум `500` |
| `module` | Фильтр по колонке `module` (например `text`, `face`) |
| `participant_id` | Для **организатора** — необязательное сужение по участнику; для **остальных** — **обязательно**, только события этого участника |
| `from`, `to` | Границы по `created_at`, формат **RFC3339** (например `2026-05-01T12:00:00Z`) |

Правило доступа: организатор видит все события (плюс фильтры); участник, зашедший по ссылке, обязан указать свой `participant_id` с клиента (идентификатор вкладки из UI).

Успешные и отклонённые обращения пишутся в серверный лог с префиксом `[ANALYSIS_ACCESS]`.

## Reports

### `GET /reports/:id`
Response `200`:

```json
{
  "reportId": "12",
  "sessionId": "12",
  "version": 1,
  "createdAt": "2026-03-20T12:00:00Z",
  "updatedAt": "2026-03-20T12:00:00Z",
  "summaryJson": {
    "status": "stub",
    "note": "Report 12 is not generated yet"
  }
}
```
