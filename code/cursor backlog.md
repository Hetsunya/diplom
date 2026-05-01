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
BL-014 [x]: State machine митинга + аудит событий в БД

Цель: формализовать жизненный цикл и историю изменений.
Файлы: emeeting-backend/internal/meeting/**, emeeting-backend/migrations/up/*, emeeting-backend/migrations/down/*
Результат:
- статусы: created|active|paused|ended|cancelled
- сервис-методы переходов: StartMeeting(), EndMeeting() (+ валидация)
- таблица audit: meeting_events (append-only)
Оценка: 1–2 дн
DoD: unit-тесты на переходы (`TestMeeting_Transitions`) + миграция поднимается с нуля.

BL-015 [x]: Участники и роли (host/co-host/participant/guest)

Цель: управляемые join/leave и права на действия.
Файлы: emeeting-backend/internal/meeting/**, emeeting-backend/migrations/*
Результат:
- модель participants с ролями и флагом активности (soft leave: is_active=false)
- проверки доступа: user_id из токена ↔ participant.user_id
Оценка: 1–2 дн
DoD: тесты сервис-слоя на join/leave и проверки ролей.

BL-016 [x]: WS события join/leave/start/end + broadcast hub

Цель: синхронизация состояния в реальном времени.
Файлы: emeeting-backend/internal/session/**, emeeting-backend/internal/meeting/**, emeeting-ui/src/**
Результат:
- WSEvent (type/payload/ts)
- события: user_joined, user_left, host_started, meeting_ended (+ user_removed опционально)
- broadcast всем активным соединениям сессии
Оценка: 1–2 дн
DoD: интеграционный тест потока (`TestE2E_MeetingFlow`) + UI обновляет список участников.

BL-017 [x]: Реконнект: восстановление участника по session_id + token

Цель: устойчивость к обрывам сети.
Файлы: code/emeeting-backend/internal/ws/**, code/emeeting-backend/internal/meeting/**, code/emeeting-ui/src/features/meeting/**
Результат:
- server-side: rejoin без дубликатов participant, корректная повторная подписка
- client-side: авто-reconnect с backoff, resync состояния (fetch + cache update)
Оценка: 1–2 дн
DoD: тест на реконнект (backend) + unit-тесты обработчика событий (frontend).

BL-018 [x]: Обработка onClose (user_left) + правило “host ушёл”

Цель: консистентная очистка participants и корректное завершение митинга.
Файлы: code/emeeting-backend/internal/ws/handler.go, code/emeeting-backend/internal/meeting/service.go, code/emeeting-ui/src/features/meeting/**
Результат:
- onClose: is_active=false + broadcast user_left {user_id,left_at}
- если ушёл host и нет co-host: meeting → ended (+ meeting_ended)
Оценка: 6–12 ч
DoD: `TestMeeting_UserDisconnect_WithCoHost`, `TestMeeting_UserDisconnect_HostOnly` + UI корректно реагирует.

P1 — Frontend Meeting UX (чтобы митинг ощущался “живым”)
BL-019 [x]: Meeting feature-store (React Query + Zustand) + WS hook

Цель: разделить server-state и UI-state и стандартизировать WS подписку.
Файлы: code/emeeting-ui/src/features/meeting/**, (опц.) src/lib/ws
Результат:
- `useMeetingStore` (UI флаги/модалки)
- `useMeetingWebSocket`/`useWebSocket` с `onEvent(handleMeetingEvent)`
Оценка: 6–12 ч
DoD: тесты на обработку событий (Vitest) + отсутствие “ручных” setState по всему UI.

BL-020 [x]: UI реакции на WS события (participants cache + toasts + redirect)

Цель: завершить пользовательский цикл “вошёл/вышел/кикнули”.
Файлы: code/emeeting-ui/src/features/meeting/** (participants list, toast, routing)
Результат:
- user_left/user_joined обновляют кэш React Query
- если текущего кикнули: redirect на /meetings + сообщение
Оценка: 4–8 ч
DoD: RTL тесты на редирект/тост и корректное обновление списка.

P0 — Auth System (безопасный базовый контур)
BL-021 [x]: bcrypt для password_hash + миграция/переезд

Цель: убрать SHA-256 и подготовиться к прод-уровню.
Файлы: code/emeeting-backend/internal/auth/**, code/emeeting-backend/migrations/*
Результат:
- хранение bcrypt hash
- сценарий миграции: на логине “rehash” (или массовое обновление для демо-юзеров)
Оценка: 1 дн
DoD: `TestAuth_LoginFlow` покрывает корректные/некорректные пароли.

BL-022 [x]: Access/Refresh tokens + rotation + хранение refresh в БД

Цель: короткий access + безопасный refresh с одноразовостью.
Файлы: code/emeeting-backend/internal/auth/**, code/emeeting-backend/migrations/*
Результат:
- refresh_tokens (token_hash, user_id, expires_at, revoked) + индексы
- refresh rotation: при использовании выдаём новый, старый revoke
Оценка: 1–2 дн
DoD: `TestAuth_TokenRefresh_Invalidated` (старый refresh не работает).

BL-023 [x]: HttpOnly cookie с session token + фронтенд без localStorage

Цель: минимизировать XSS-риски и убрать хранение токенов на клиенте.
Файлы: code/emeeting-backend/internal/auth/**, code/emeeting-ui/src/features/auth/**, UI http client
Результат:
- backend выставляет cookie `session_token` (Secure только prod)
- frontend: AuthContext, retry при 401, auto refresh
Оценка: 1–2 дн
DoD: ручной сценарий “обновил страницу — остаюсь залогинен” (если предусмотрено) + автоповтор запроса после refresh.

BL-024 [x]: Middleware: RequireAuth / RequireRole / RateLimit + audit auth_events

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

---

P0 — Release/VDS (единое решение для Linux/Windows + прод)
BL-025 [ ]: Продовый reverse-proxy + HTTPS (чтобы работал getUserMedia везде)

Цель: камера/микрофон работают не только на localhost, без “secure context” проблем.
Результат:
- домен + TLS (например Caddy или Nginx+certbot)
- единый origin: `https://<domain>` проксирует `/api` и `/ws` на backend
Оценка: 1 дн
DoD: `navigator.mediaDevices.getUserMedia` доступен на VDS, UI/WS/API работают через один домен.

BL-026 [ ]: Prod docker-compose (secrets/env/volumes) + .env.prod.example

Цель: воспроизводимый деплой на VDS без ручных правок.
Результат:
- `docker-compose.prod.yml`
- env: `POSTGRES_DSN`, `JWT_SECRET`, `CORS_ALLOW_ORIGIN`, etc
- persist volumes для Postgres, бэкапы
Оценка: 6–12 ч
DoD: поднятие на чистой VDS одной командой, после рестарта данные на месте.

BL-027 [ ]: Auth hardening для prod (cookie Secure + SameSite + rotation)

Цель: убрать “иногда надо перезапуск” и сделать поведение токенов предсказуемым.
Результат:
- cookie `Secure=true` на HTTPS
- чёткая политика SameSite (обычно Lax при одном origin)
- refresh flow стабилен
Оценка: 4–8 ч
DoD: логин сохраняется после F5, `/sessions` не ловит 401 без причины.

BL-028 [x]: ai-gateway: сервис‑аккаунт/токен для WS или отдельный internal-канал

Цель: gateway не получает 401 на WS.
Результат (варианты):
- A) gateway получает сервисный access token и подключается с ним
- B) отдельный endpoint для internal клиентов в одной сети (с ограничениями)
Оценка: 1–2 дн
DoD: ai-gateway стабильно подключается и не падает.

Статус:
- Реализовано: `/auth/token` (выдаёт TokenPair JSON для сервисов), поддержка `Authorization: Bearer <JWT>` в `RequireAuth`, настройки env для ai-gateway.
- Проверено: gateway подключается к `/ws/sessions/:id` без 401 в docker-compose.

BL-029 [ ]: Observability для релиза (логирование/health/метрики)

Цель: быстро понимать “почему не работает” без дебага в браузере.
Результат:
- структурные логи, request-id
- health endpoints и понятные статусы
Оценка: 6–12 ч
DoD: по логам видно origin/cookies/auth path и причины отказа.

Статус (частично):
- Реализовано: `X-Request-ID` middleware + access log с rid/origin/host/xfp/uid.
- Реализовано: `GET /health` и `GET /ready` (ready проверяет Ping к Postgres).
- Не закрыто по DoD BL-029: метрики/алерты/SLO для прод-наблюдаемости (отдельный трек).

---

P0 — AI modules implementation (единая папка модулей)

**Синхронизация статусов BL-030…BL-037 (2026-05):** часть работы уже в коде, но DoD карточек ниже формулировался шире — не удаляем карточки, фиксируем фактический прогресс.

| ID | Фактический статус | Куда смотреть в репо |
|----|--------------------|----------------------|
| BL-030 | не сделано | Плагины всё ещё в `ai-gateway/plugins/`, папки `ai-gateway/modules/` нет |
| BL-031 | **частично** | `ai-gateway/adapters/speech_service.py` (retry), `plugins/audio.py` → `text_analysis`; полный вынос в `modules/text` + circuit-breaker — впереди |
| BL-032 | не сделано | `audio_analysis` пока baseline stub в `plugins/audio.py` |
| BL-033 | **частично** | `plugins/frame.py`: `face_analysis` + legacy `emotion`, throttling `min_interval_sec`, порог `min_confidence`; вынос в `modules/face` — впереди |
| BL-034 | **частично** | `ai-gateway/report_loop.py` + `feature_store.py`; полноценный fusion/windowing — впереди |
| BL-035 | не сделано | REST есть, RBAC/фильтры `from/to/module` — нет |
| BL-036 | **частично** | `smoke_ws_emotion_test.py` (face+emotion), `e2e_analysis_readpath_check.py`; полный hybrid smoke — впереди |
| BL-037 | не сделано | prod readiness AI |

BL-030 [ ]: Единый layout для AI-модулей в одной папке

Цель: стандартизовать структуру и убрать размазывание логики по разным местам.
Файлы: `ai-gateway/modules/**` (новые), `ai-gateway/handlers.py`, `ai-gateway/gateway_config.py`, `ai-gateway/MEMO.md`
Результат:
- единая папка: `ai-gateway/modules/`
- подпапки: `text/`, `audio/`, `face/`, `report/`, `shared/`
- общий интерфейс модуля (`can_handle/process` + metadata: module/provider/model/version)
Оценка: 1 дн
DoD: все активные анализаторы грузятся из `ai-gateway/modules/**`, старые `plugins/*` либо проксируют, либо удалены без потери функционала.

BL-031 [ ]: Text module v1 (ASR + NLP поверх транскрибации)

Цель: получить стабильный поток `text_analysis` partial/final из отдельного speech-service.
Файлы: `ai-gateway/modules/text/**`, `ai-gateway/adapters/speech_service.py`, `speech-service/**`, `docs/ANALYSIS_WS_CONTRACTS.md`
Результат:
- адаптер к speech-service с timeout/retry/circuit-breaker
- нормализация ответа ASR в контракт `text_analysis`
- базовые `text_features` (sentiment/topics/keyphrases/confidence) как отдельный шаг
Оценка: 1–2 дн
DoD: в live-сессии приходят `text_analysis` события с `trace_id`, `stage`, `version`; при ошибке speech-service gateway не падает.

BL-032 [ ]: Audio module v1 (voice/signal features)

Цель: заменить текущий stub на реальный анализ аудио-сигнала.
Файлы: `ai-gateway/modules/audio/**`, `docs/ANALYSIS_WS_CONTRACTS.md`, `docs/ANALYSIS_OBSERVABILITY.md`
Результат:
- извлечение признаков: energy, pause_ratio, tempo, (опц.) jitter/shimmer
- публикация `audio_analysis` partial событий
- конфигурируемые пороги/окна (`modules.audio.params`)
Оценка: 1–2 дн
DoD: `audio_analysis` стабильно публикуется, latency в целевом диапазоне p95, есть fallback при невалидном чанке.

BL-033 [ ]: Face module v2 (emotion alias + quality guards)

Цель: стабилизировать модуль лица и подготовить к прод-режиму.
Файлы: `ai-gateway/modules/face/**`, `ai-gateway/contracts.py`, `emeeting-backend/internal/analysis/**`
Результат:
- основной тип `face_analysis`, legacy `emotion` как alias
- quality guards: face_detected=false, confidence thresholds, skip noisy frames
- вынесенные настройки провайдера/модели (`modules.face.*`)
Оценка: 1 дн
DoD: UI совместим с legacy `emotion`, а новый канал `face_analysis` используется для агрегаторов/отчетов.

BL-034 [ ]: Report orchestrator v1 (fusion text+audio+face -> own NN)

Цель: собрать 3 канала в единый отчетный пайплайн.
Файлы: `ai-gateway/modules/report/**`, `ai-gateway/feature_store.py`, `ai-gateway/own_nn_client.py`, `docs/ANALYSIS_WS_CONTRACTS.md`
Результат:
- windowing/join по `trace_id` + `participant_id` + time bucket
- `analysis_report_partial` (инкрементально) и `analysis_report` (финал)
- вызов собственной нейронки (`own_nn_url`) + fallback stub
Оценка: 2–3 дн
DoD: по завершении сессии есть финальный `analysis_report`, структура совпадает с контрактом, конфиг-снимок сохранен.

BL-035 [ ]: Backend RBAC + API фильтры для аналитики

Цель: безопасный доступ к аналитике и удобная выборка.
Файлы: `emeeting-backend/internal/analysis/http_handlers.go`, `emeeting-backend/internal/analysis/repository.go`, `middleware/auth.go`
Результат:
- role-aware доступ к `/sessions/:id/analysis/*`
- фильтры для events: `module`, `participant_id`, `from`, `to`, `limit`
- audit лог доступа к participant-level данным
Оценка: 1–2 дн
DoD: host/co-host видят полный отчет, participant — только разрешенный уровень детализации.

BL-036 [ ]: E2E тест-контур AI pipeline (hybrid)

Цель: поймать регрессии на сквозном потоке до релиза.
Файлы: `ai-gateway/smoke_ws_emotion_test.py` (расширить), новые `ai-gateway/tests/*`, `emeeting-backend/internal/session/ws_handler_test.go`
Результат:
- smoke: frame -> face_analysis/emotion
- smoke: audio -> text_analysis + audio_analysis
- smoke: partial report -> final report
Оценка: 1–2 дн
DoD: один сценарий запуска проверяет полный hybrid pipeline и валидирует обязательные поля контракта.

BL-037 [ ]: Prod readiness AI (ресурсы, деградация, алерты)

Цель: контролируемое поведение под нагрузкой и при деградации внешних сервисов.
Файлы: `ai-gateway/observability.py`, `docs/ANALYSIS_OBSERVABILITY.md`, `docker-compose.prod.yml` (или эквивалент)
Результат:
- лимиты/очереди на тяжелые модули
- graceful degradation (отключение модуля через конфиг без перезапуска backend)
- метрики и алерты: error-rate, module latency, report generation lag
Оценка: 1–2 дн
DoD: при падении speech-service или face-провайдера остальные модули продолжают работу, отчет формируется с пометкой неполных данных.

Рекомендуемый порядок внедрения (AI спринты)
Спринт 7 (структура + контракты): BL-030 → BL-031
Спринт 8 (мультимодальность): BL-032 → BL-033
Спринт 9 (агрегация/отчеты): BL-034 → BL-035
Спринт 10 (стабилизация): BL-036 → BL-037

---

P1 — UI: транскрипт, чат, вердикт AI (план в `docs/UI_AI_ANALYSIS_PLAN.md`)

BL-038 [ ]: Правый рейл «Live транскрипт» (не чат)

Цель: отображать поток `text_analysis` (partial/final) по спикерам, без смешивания с пользовательским чатом.
Файлы: `emeeting-ui/src/pages/VideoMeet.tsx`, новый компонент `emeeting-ui/src/features/meeting/TranscriptRail.tsx` (или аналог)
Оценка: 1–2 дн
DoD: при live-сессии видны строки транскрипта; состояния не «вечный analyzing».

BL-039 [ ]: Отдельная панель «Чат»

Цель: явное UI-разделение чата и транскрипта (макет + роутинг/состояние при необходимости).
Файлы: `emeeting-ui/src/pages/VideoMeet.tsx`, layout/meeting shell
Оценка: 1 дн
DoD: пользователь не путает ASR-текст с сообщениями чата.

BL-040 [ ]: Плашка / блок «Вердикт» по `analysis_report_partial`

Цель: краткий вывод нейросети + раскрытие деталей (drawer/modal).
Файлы: `emeeting-ui/src/pages/VideoMeet.tsx`, `emeeting-ui/src/api/sessions.ts` (опц. REST fallback)
Оценка: 1 дн
DoD: клик открывает подробности; пустое состояние без вводящего в заблуждение текста.

BL-041 [ ]: Убрать или переработать «AI analyzing…»

Цель: заменить на состояния пайплайна (listening / transcribing / verdict) или убрать дублирование с индикаторами рейла.
Файлы: `emeeting-ui/src/pages/VideoMeet.tsx`
Оценка: 0.5–1 дн
DoD: нет «вечного» analyzing при отсутствии событий; согласовано с BL-038.

Опционально позже (фаза D в плане): bubble под активным спикером — отдельная карточка после diarization/VAD в данных.