Отлично — вот готовый технический backlog с приоритетом, оценкой и привязкой к файлам, чтобы можно было сразу заносить в трекер.

Backlog (приоритетный)
P0 — Стабильный базовый контур (блокеры)
BL-001 [x]: Зафиксировать API-контракт v1 (UI ↔ Backend)

Цель: убрать рассинхрон эндпоинтов и payload.
Файлы: emeeting-ui/src/api/auth.ts, emeeting-ui/src/api/reports.ts, emeeting-ui/src/api/sessions.ts, emeeting-backend/cmd/server/main.go
Результат: документ docs/api-contract.md + backend маршруты соответствуют UI.
Оценка: 4–6 ч
DoD: UI не получает 404 на основных сценариях (login/sessions/reports).
BL-002 [x]: Убрать хардкод конфигов во всех сервисах

Цель: переносимость между окружениями.
Файлы: emeeting-backend/internal/db/postgres.go, emeeting-backend/cmd/server/main.go, emeeting-ui/src/api/http.ts, emeeting-ui/src/hooks/useSessionWS.ts, ai-gateway/main.py
Результат: env-переменные + .env.example в emeeting-backend, emeeting-ui, ai-gateway.
Оценка: 4–8 ч
DoD: запуск на новой машине без правки исходников.
BL-003 [x]: Минимально закрыть пустые backend-заготовки

Цель: убрать технические “дыры” в критическом пути.
Файлы: emeeting-backend/internal/auth/handler.go, emeeting-backend/internal/auth/service.go, emeeting-backend/internal/session/service.go, emeeting-backend/internal/ws/handler.go
Результат: рабочие заглушки/реализации без пустых файлов.
Оценка: 1–2 дн
DoD: проект билдится, маршруты отвечают предсказуемо (не “пустые” обработчики).
BL-004 [x]: Базовые автотесты backend

Цель: ловить регрессии по сессиям и WS.
Файлы: emeeting-backend/internal/session/*, новые *_test.go
Результат: unit + интеграционные smoke-тесты для /sessions и WS-подключения.
Оценка: 1–2 дн
DoD: go test ./... зеленый локально и в CI.
P1 — Предсказуемая разработка и релиз
BL-005 [x]: Настроить CI (lint + test + build)

Цель: автоматическая проверка каждого PR/коммита.
Файлы: .github/workflows/ci.yml (новый), конфиги линта/тестов
Результат: пайплайн для emeeting-ui, emeeting-backend, ai-gateway.
Оценка: 6–10 ч
DoD: CI падает при поломке тестов/линта.
BL-006 [x]: Воспроизводимый локальный запуск (docker-compose)

Цель: запуск всего стека одной командой.
Файлы: docker-compose.yml (новый), Dockerfile для сервисов, README.md (корень)
Результат: db + backend + gateway + ui в одном compose.
Оценка: 1–2 дн
DoD: docker compose up поднимает систему и health-check проходит.
BL-007 [x]: Миграции БД

Цель: управляемая эволюция схемы.
Файлы: emeeting-backend/migrations/* (новые), скрипты запуска миграций
Результат: versioned SQL миграции и инструкция отката.
Оценка: 6–12 ч
DoD: новая БД поднимается из нуля до актуальной схемы автоматически.
BL-008 [x]: Нормальная проектная документация

Цель: снизить bus factor и onboarding time.
Файлы: README.md (корень), emeeting-ui/README.md
Результат: runbook “как поднять/проверить/дебажить”.
Оценка: 3–5 ч
DoD: новый разработчик поднимает проект по инструкции без помощи.
P2 — Расширяемость инструментария (архитектурно)
BL-009 [x]: Backend модульная регистрация роутов

Цель: масштабировать новые домены без разрастания main.go.
Файлы: emeeting-backend/cmd/server/main.go, emeeting-backend/internal/*/module.go (новые)
Результат: интерфейс модуля (RegisterRoutes) и сборка через список модулей.
Оценка: 1–2 дн
DoD: добавление нового модуля не требует большого рефакторинга main.go.
BL-010 [x]: Интерфейсы портов в session/auth

Цель: тестируемость и замена реализаций.
Файлы: emeeting-backend/internal/session/contracts.go, handler.go, repository.go, hub.go
Результат: Repository/Service/Bus как интерфейсы, handler зависит от абстракций.
Оценка: 1–2 дн
DoD: можно подменить репозиторий моками в unit-тестах.
BL-011 [x]: Registry-based WS dispatch

Цель: легко добавлять новые WS-команды.
Файлы: emeeting-backend/internal/session/ws_handler.go
Результат: map[type]handler вместо giant switch.
Оценка: 6–10 ч
DoD: новая команда добавляется через регистрацию обработчика.
BL-012 [x]: Плагинный AI-pipeline в gateway

Цель: расширять AI-инструментарий без переписывания центра.
Файлы: ai-gateway/handlers.py, ai-gateway/main.py, ai-gateway/plugins/* (новые)
Результат: контракт анализатора (can_handle/process) + реестр плагинов.
Оценка: 1–2 дн
DoD: новый анализатор подключается отдельным модулем.
BL-013 [x]: Декларативный feature-config на UI

Цель: включать новые инструменты/страницы конфигом.
Файлы: emeeting-ui/src/router.tsx, emeeting-ui/src/components/Navbar.tsx, emeeting-ui/src/config/features.ts (новый)
Результат: маршруты/пункты меню генерируются из конфигурации.
Оценка: 6–12 ч
DoD: новая фича добавляется в одном месте, без ручной правки нескольких файлов.
Рекомендуемый порядок внедрения (спринты)
Спринт 1 (стабильность): BL-001 → BL-002 → BL-003 → BL-004
Спринт 2 (инженерная надежность): BL-005 → BL-006 → BL-007 → BL-008
Спринт 3 (расширяемость): BL-009 → BL-010 → BL-011 → BL-012 → BL-013
KPI, чтобы видеть прогресс
0 критичных 404 на основных user flow.
>=70% покрытие для критичного backend-пути сессий/WS (минимум smoke + ключевая логика).
Время поднятия проекта “с нуля” ≤ 15 минут по README.
Добавление новой WS-команды/AI-инструмента ≤ 1 файл + регистрация (без правки центральных switch-цепочек).
Если хочешь, следующим шагом разложу это в формат GitHub Issues (title, description, acceptance criteria, labels, estimate) — готовыми карточками.

---

Новый backlog (по `@instructions.md`, meeting/auth)

P0 — Meeting Service (MVP real-time, блокеры продукта)
BL-014 [ ]: State machine митинга + аудит событий в БД

Цель: формализовать жизненный цикл и историю изменений.
Файлы: code/emeeting-backend/internal/meeting/**, code/emeeting-backend/migrations/up/*, migrations/down/*
Результат:
- статусы: created|active|paused|ended|cancelled
- сервис-методы переходов: StartMeeting(), EndMeeting() (+ валидация)
- таблица audit: meeting_events (append-only)
Оценка: 1–2 дн
DoD: unit-тесты на переходы (`TestMeeting_Transitions`) + миграция поднимается с нуля.

BL-015 [ ]: Участники и роли (host/co-host/participant/guest)

Цель: управляемые join/leave и права на действия.
Файлы: code/emeeting-backend/internal/meeting/**, code/emeeting-backend/migrations/*
Результат:
- модель participants с ролями и флагом активности (soft leave: is_active=false)
- проверки доступа: user_id из токена ↔ participant.user_id
Оценка: 1–2 дн
DoD: тесты сервис-слоя на join/leave и проверки ролей.

BL-016 [ ]: WS события join/leave/start/end + broadcast hub

Цель: синхронизация состояния в реальном времени.
Файлы: code/emeeting-backend/internal/ws/**, code/emeeting-backend/internal/meeting/**, code/emeeting-ui/src/features/meeting/**
Результат:
- WSEvent (type/payload/ts)
- события: user_joined, user_left, host_started, meeting_ended (+ user_removed опционально)
- broadcast всем активным соединениям сессии
Оценка: 1–2 дн
DoD: интеграционный тест потока (`TestE2E_MeetingFlow`) + UI обновляет список участников.

BL-017 [ ]: Реконнект: восстановление участника по session_id + token

Цель: устойчивость к обрывам сети.
Файлы: code/emeeting-backend/internal/ws/**, code/emeeting-backend/internal/meeting/**, code/emeeting-ui/src/features/meeting/**
Результат:
- server-side: rejoin без дубликатов participant, корректная повторная подписка
- client-side: авто-reconnect с backoff, resync состояния (fetch + cache update)
Оценка: 1–2 дн
DoD: тест на реконнект (backend) + unit-тесты обработчика событий (frontend).

BL-018 [ ]: Обработка onClose (user_left) + правило “host ушёл”

Цель: консистентная очистка participants и корректное завершение митинга.
Файлы: code/emeeting-backend/internal/ws/handler.go, code/emeeting-backend/internal/meeting/service.go, code/emeeting-ui/src/features/meeting/**
Результат:
- onClose: is_active=false + broadcast user_left {user_id,left_at}
- если ушёл host и нет co-host: meeting → ended (+ meeting_ended)
Оценка: 6–12 ч
DoD: `TestMeeting_UserDisconnect_WithCoHost`, `TestMeeting_UserDisconnect_HostOnly` + UI корректно реагирует.

P1 — Frontend Meeting UX (чтобы митинг ощущался “живым”)
BL-019 [ ]: Meeting feature-store (React Query + Zustand) + WS hook

Цель: разделить server-state и UI-state и стандартизировать WS подписку.
Файлы: code/emeeting-ui/src/features/meeting/**, (опц.) src/lib/ws
Результат:
- `useMeetingStore` (UI флаги/модалки)
- `useMeetingWebSocket`/`useWebSocket` с `onEvent(handleMeetingEvent)`
Оценка: 6–12 ч
DoD: тесты на обработку событий (Vitest) + отсутствие “ручных” setState по всему UI.

BL-020 [ ]: UI реакции на WS события (participants cache + toasts + redirect)

Цель: завершить пользовательский цикл “вошёл/вышел/кикнули”.
Файлы: code/emeeting-ui/src/features/meeting/** (participants list, toast, routing)
Результат:
- user_left/user_joined обновляют кэш React Query
- если текущего кикнули: redirect на /meetings + сообщение
Оценка: 4–8 ч
DoD: RTL тесты на редирект/тост и корректное обновление списка.

P0 — Auth System (безопасный базовый контур)
BL-021 [ ]: bcrypt для password_hash + миграция/переезд

Цель: убрать SHA-256 и подготовиться к прод-уровню.
Файлы: code/emeeting-backend/internal/auth/**, code/emeeting-backend/migrations/*
Результат:
- хранение bcrypt hash
- сценарий миграции: на логине “rehash” (или массовое обновление для демо-юзеров)
Оценка: 1 дн
DoD: `TestAuth_LoginFlow` покрывает корректные/некорректные пароли.

BL-022 [ ]: Access/Refresh tokens + rotation + хранение refresh в БД

Цель: короткий access + безопасный refresh с одноразовостью.
Файлы: code/emeeting-backend/internal/auth/**, code/emeeting-backend/migrations/*
Результат:
- refresh_tokens (token_hash, user_id, expires_at, revoked) + индексы
- refresh rotation: при использовании выдаём новый, старый revoke
Оценка: 1–2 дн
DoD: `TestAuth_TokenRefresh_Invalidated` (старый refresh не работает).

BL-023 [ ]: HttpOnly cookie с session token + фронтенд без localStorage

Цель: минимизировать XSS-риски и убрать хранение токенов на клиенте.
Файлы: code/emeeting-backend/internal/auth/**, code/emeeting-ui/src/features/auth/**, UI http client
Результат:
- backend выставляет cookie `session_token` (Secure только prod)
- frontend: AuthContext, retry при 401, auto refresh
Оценка: 1–2 дн
DoD: ручной сценарий “обновил страницу — остаюсь залогинен” (если предусмотрено) + автоповтор запроса после refresh.

BL-024 [ ]: Middleware: RequireAuth / RequireRole / RateLimit + audit auth_events

Цель: централизованная защита эндпоинтов и защита от brute-force.
Файлы: code/emeeting-backend/middleware/**, code/emeeting-backend/internal/auth/**, migrations/*
Результат:
- порядок middleware: Recover → Logger → CORS → RateLimit → Auth → Handler
- rate-limit логина: 5/мин IP + lock после 10 попыток (locked_until)
- аудит: auth_events (login_attempt, token_refresh, logout)
Оценка: 1–2 дн
DoD: `TestMiddleware_RequireRole` + тест на блокировку brute-force.

Рекомендуемый порядок внедрения (следующие спринты)
Спринт 4 (meeting MVP): BL-014 → BL-015 → BL-016 → BL-018 → BL-020
Спринт 5 (meeting resilience): BL-017 → BL-019
Спринт 6 (auth secure): BL-021 → BL-022 → BL-023 → BL-024