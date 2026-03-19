# eMeeting Monorepo

## Quick start (Docker Compose)

Requirements:
- Docker
- Docker Compose plugin

Run full stack:

```bash
docker compose up --build
```

Services:
- UI: `http://localhost:5173`
- Backend API: `http://localhost:8080`
- Postgres: `localhost:5432`

Stop and remove containers:

```bash
docker compose down
```

Reset DB volume:

```bash
docker compose down -v
```

## Database migrations

- Versioned SQL migrations live in:
  - `code/emeeting-backend/migrations/up`
  - `code/emeeting-backend/migrations/down`
- On fresh startup, `docker compose` auto-applies only `up` scripts via `/docker-entrypoint-initdb.d`.
- Rollback instructions are documented in `code/emeeting-backend/migrations/README.md`.

## Environment notes

- Backend config in compose:
  - `POSTGRES_DSN`
  - `SERVER_PORT`
  - `CORS_ALLOW_ORIGIN`
- UI config in compose:
  - `VITE_API_URL`
  - `VITE_WS_URL`
- AI gateway config in compose:
  - `BACKEND_WS_BASE_URL`
  - `SESSION_ID`
