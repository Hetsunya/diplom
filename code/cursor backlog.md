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
BL-007: Миграции БД

Цель: управляемая эволюция схемы.
Файлы: emeeting-backend/migrations/* (новые), скрипты запуска миграций
Результат: versioned SQL миграции и инструкция отката.
Оценка: 6–12 ч
DoD: новая БД поднимается из нуля до актуальной схемы автоматически.
BL-008: Нормальная проектная документация

Цель: снизить bus factor и onboarding time.
Файлы: README.md (корень), emeeting-ui/README.md
Результат: runbook “как поднять/проверить/дебажить”.
Оценка: 3–5 ч
DoD: новый разработчик поднимает проект по инструкции без помощи.
P2 — Расширяемость инструментария (архитектурно)
BL-009: Backend модульная регистрация роутов

Цель: масштабировать новые домены без разрастания main.go.
Файлы: emeeting-backend/cmd/server/main.go, emeeting-backend/internal/*/module.go (новые)
Результат: интерфейс модуля (RegisterRoutes) и сборка через список модулей.
Оценка: 1–2 дн
DoD: добавление нового модуля не требует большого рефакторинга main.go.
BL-010: Интерфейсы портов в session/auth

Цель: тестируемость и замена реализаций.
Файлы: emeeting-backend/internal/session/contracts.go, handler.go, repository.go, hub.go
Результат: Repository/Service/Bus как интерфейсы, handler зависит от абстракций.
Оценка: 1–2 дн
DoD: можно подменить репозиторий моками в unit-тестах.
BL-011: Registry-based WS dispatch

Цель: легко добавлять новые WS-команды.
Файлы: emeeting-backend/internal/session/ws_handler.go
Результат: map[type]handler вместо giant switch.
Оценка: 6–10 ч
DoD: новая команда добавляется через регистрацию обработчика.
BL-012: Плагинный AI-pipeline в gateway

Цель: расширять AI-инструментарий без переписывания центра.
Файлы: ai-gateway/handlers.py, ai-gateway/main.py, ai-gateway/plugins/* (новые)
Результат: контракт анализатора (can_handle/process) + реестр плагинов.
Оценка: 1–2 дн
DoD: новый анализатор подключается отдельным модулем.
BL-013: Декларативный feature-config на UI

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