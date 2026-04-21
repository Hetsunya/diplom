# eMeeting Monorepo — Project Context

## Architecture
- Monorepo с 3 сервисами:
  - `code/emeeting-ui`: React 18 + TypeScript + Vite, frontend
  - `code/emeeting-backend`: Go 1.21 + Gin + gorilla/websocket, REST API + WS
  - `code/ai-gateway`: Python 3.11, прокси для AI/WS обработчиков
- Оркестрация: Docker Compose (Postgres 15, все сервисы в одной сети)
- Auth: пока демо-пользователи в БД (password_hash = SHA-256 hex), планируется cookie-based auth с HttpOnly сессиями

## Ключевые эндпоинты
- Backend: `GET /ws/health`, `POST /auth/login`, `GET /sessions`, `GET /reports/:id`
- WebSocket: `/ws/sessions/:id` (upgrade, JWT в query-параметре пока)
- UI: Vite dev server на 5173, проксирует API на 8080

## Текущее состояние
✅ Базовая инфраструктура: Docker Compose, миграции SQL, health checks
⚠️ Meeting service: минимальная реализация, нет:
  - управления участниками (join/leave, роли: host/participant)
  - real-time синхронизации состояния митинга
  - обработки отключений/реконнектов
⚠️ Auth system:
  - пароли хранятся как SHA-256 (небезопасно для prod)
  - нет refresh tokens, rate limiting, validation middleware
  - frontend хранит isAuthenticated в state (уязвимо)

## Цели доработки (приоритет)
1. **Meeting Service**:
   - Реализовать состояние митинга: `created` → `active` → `ended`
   - Добавить роли участников: `host`, `co-host`, `participant`, `guest`
   - WebSocket события: `user_joined`, `user_left`, `host_started`, `meeting_ended`
   - Обработка реконнекта: восстановление сессии по session_id + token
   - Хранение метаданных митинга в БД: participants[], start_time, duration, settings

2. **Auth System**:
   - Перейти на bcrypt для хеширования паролей
   - Реализовать JWT access + refresh tokens (access: 15min, refresh: 7d)
   - Добавить middleware: `RequireAuth`, `RequireRole`, `RateLimit`
   - Backend: HttpOnly secure cookie с session token (не localStorage!)
   - Frontend: AuthContext с retry-логикой при 401, автоматический рефреш токена

## Технические требования
- Go: использовать context для отмены, graceful shutdown для WS
- React: TypeScript strict mode, React Query для server state, Zod для валидации форм
- БД: миграции только через SQL в `migrations/up`, rollback в `migrations/down`
- Безопасность: CSP headers, CORS только с `CORS_ALLOW_ORIGIN`, sanitization входных данных
- Тесты:
  - Backend: `go test ./...` с coverage >80%, тесты на конкурентность через `t.Parallel()`
  - Frontend: Vitest + React Testing Library, e2e через Playwright (опционально)

## Конвенции кода
- Go: effective go, golint, имена в camelCase для экспортируемых, snake_case для БД
- React: functional components + hooks, file-per-component, `*.test.tsx` рядом с компонентом
- Ошибки: Go — wrap с `%w`, React — ErrorBoundary + user-friendly messages
- Логирование: structured logging (zap в Go, pino в Node если понадобится)

## Команды разработки
```bash
# Запуск всего стека
docker compose up --build

# Backend dev
cd code/emeeting-backend && go run ./cmd/server

# Frontend dev
cd code/emeeting-ui && npm run dev

# Тесты
cd code/emeeting-backend && go test ./... -cover
cd code/emeeting-ui && npm run test && npm run lint
```

