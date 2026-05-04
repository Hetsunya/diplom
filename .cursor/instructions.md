# eMeeting Monorepo — контекст для агентов

Рабочая область Cursor часто открыта на каталоге **`code/`** внутри репозитория; пути ниже указаны **от корня монорепозитория** (`diplom/`), как в CI и Docker.

## Архитектура

| Компонент | Путь | Стек |
|-----------|------|------|
| Frontend | `code/emeeting-ui` | React 19, TypeScript, Vite, TanStack Query, Zustand |
| Backend | `code/emeeting-backend` | Go, Gin, gorilla/websocket, PostgreSQL |
| AI Gateway | `code/ai-gateway` | Python 3.11, WebSocket-пайплайн аналитики (face, audio, text, отчёты) |
| ASR | `code/speech-service` | HTTP `/v1/transcribe`: режимы `stub` и `whisper` (faster-whisper) |

Оркестрация: `docker-compose.yml` / `docker-compose.prod.yml` в корне репозитория.

## Текущее состояние (актуально)

- **Аутентификация:** bcrypt для паролей, JWT access + refresh, ротация refresh-токенов, часть эндпоинтов публичная (`/auth/login`, `/auth/refresh`, health). Подробности — код в `code/emeeting-backend/internal/auth/`.
- **Встречи / сессии:** WebSocket по сессиям, состояние митинга и участники — см. `code/emeeting-backend/internal/session/`, UI — `code/emeeting-ui/src/features/meeting/`.
- **Документация:** индекс — `code/docs/README.md`; контракты WS — `code/docs/ANALYSIS_WS_CONTRACTS.md`. Каталог **`code/AI/`** (черновики исследований) **не входит в репозиторий** — удалён для уменьшения размера клона.
- **Правила по подсистемам:** `.cursor/rules/meeting-service.mdc`, `.cursor/rules/auth-system.mdc` (globs относительно корня workspace — при открытом `code/` без префикса `code/`).

## Команды

```bash
# Корень репозитория (diplom/)
docker compose up --build

# Backend
cd code/emeeting-backend && go test ./... && go vet ./... && go build ./...

# Frontend
cd code/emeeting-ui && npm ci && npm run lint && npm run test && npm run build
```

## Соглашения

- Миграции БД: SQL в `code/emeeting-backend/migrations/up` и `down`.
- Новые документы продуктового уровня — в `code/docs/`, ссылка из `docs/README.md`.
- Не добавлять в git тяжёлые бинарники и полные клоны сторонних ML-проектов; достаточно ссылок и описания в документации.
