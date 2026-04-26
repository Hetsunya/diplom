# eMeeting Monorepo

## What is inside

- `code/emeeting-ui` - React + TypeScript frontend
- `code/emeeting-backend` - Go (Gin) backend API + WebSocket
- `code/ai-gateway` - Python gateway for WS/AI handlers
- `docker-compose.yml` - local stack orchestration

## Runbook: quick start (Docker Compose)

Requirements:
- Docker Desktop (or Docker Engine)
- Docker Compose plugin

1) Start full stack:

```bash
docker compose up --build
```

2) Open services:
- UI: `http://localhost:5173`
- Backend API: `http://localhost:8080`
- Backend health: `http://localhost:8080/ws/health`
- Postgres: `localhost:5432`

3) Stop stack:

```bash
docker compose down
```

4) Reset DB data (fresh bootstrap):

```bash
docker compose down -v
```

## Runbook: local development (without Docker)

### Backend

```bash
cd code/emeeting-backend
go test ./...
go run ./cmd/server
```

Default backend URL: `http://localhost:8080`

### UI

```bash
cd code/emeeting-ui
npm install
npm run lint
npm run build
npm run dev
```

Default UI URL: `http://localhost:5173`

### AI gateway

```bash
cd code/ai-gateway
python -m pip install -r requirements.txt
python main.py
```

## Database migrations

- Versioned SQL migrations live in:
  - `code/emeeting-backend/migrations/up`
  - `code/emeeting-backend/migrations/down`
- On fresh startup, `docker compose` auto-applies only `up` scripts via `/docker-entrypoint-initdb.d`.
- Rollback instructions are documented in `code/emeeting-backend/migrations/README.md`.

## Verify checklist

- `docker compose up --build` starts all services without crash loops.
- `GET http://localhost:8080/ws/health` returns status `ok`.
- UI opens and can call backend endpoints (`/sessions`, `/auth/login`, `/reports/:id`).
- Backend tests pass locally: `go test ./...`.
- UI quality checks pass locally: `npm run lint && npm run build`.

## Debug guide

- **Backend fails to connect DB**
  - Check `POSTGRES_DSN` in compose/env.
  - Ensure DB container is healthy before backend start.
- **UI cannot reach API or WS**
  - Check `VITE_API_URL` and `VITE_WS_URL`.
  - Verify backend exposed on port `8080`.
- **WS closes immediately**
  - Confirm `GET /ws/sessions/:id` is reachable.
  - Check backend logs for upgrade errors.
- **DB schema missing**
  - Reset volumes (`docker compose down -v`) and start again.
  - Verify scripts exist in `migrations/up`.

## Environment variables

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

## Seed users (demo auth)

Демо пользователи хранятся в таблице `auth_user` (пароль в `password_hash` хранится как SHA-256 hex).

1. `demo1@example.com` / `demo1pass`
2. `demo2@example.com` / `demo2pass`

В UI поля логина/пароля по умолчанию заполнены для пользователя `demo1`.

TODO: будет cookie-based auth (HttpOnly cookie / session token) вместо хранения только `isAuthenticated` в frontend state.

---

## Production (VDS) deploy

### Requirements
- A VDS with Docker Engine + Docker Compose plugin
- A domain name pointing to your VDS IP (A/AAAA records)
- Open ports **80** and **443** in firewall/security group

### Files
- `docker-compose.prod.yml` – production stack (db + backend + ui + caddy)
- `Caddyfile` – HTTPS + reverse proxy
- `.env.prod.example` – example environment file

### Deploy steps

1) Copy `.env.prod.example` to `.env.prod` and fill values:
- `DOMAIN` (your domain)
- `JWT_SECRET` (generate a long random string)
- `POSTGRES_PASSWORD`

2) Start the stack:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

3) Open the app:
- `https://<DOMAIN>/`

### Notes
- **Camera/mic**: `getUserMedia` works on `https://<DOMAIN>` and on `http://localhost` (browser secure-context rules).
- **Caddy TLS**: certificates are stored in `caddy_data` volume.
