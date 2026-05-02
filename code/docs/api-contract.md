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
Response `200`: array of sessions.

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
Response `200`: single session object.

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
