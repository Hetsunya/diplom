# Implementation Plan (2 спринта)

Цель: быстро довести AI-контур до рабочего hybrid-сценария без перегруза архитектуры.

## Спринт A — Production baseline (ASR + стабильные события)

### A1. Подключить внешний ASR сервис
- Поднять и проверить `whisperX-FastAPI` как `speech-service`.
- Настроить `ai-gateway/modules.default.json`:
  - `modules.text.enabled=true`
  - `modules.text.params.speech_service_url=<url>`
- Файлы проекта:
  - `ai-gateway/adapters/speech_service.py`
  - `ai-gateway/modules.default.json`
  - `ai-gateway/plugins/audio.py`

**Результат:** стабильные `text_analysis` partial/final события в WS.

### A2. Укрепить контракт и fault tolerance
- Жестко валидировать наличие `trace_id/stage/version/module` в исходящих событиях.
- Добавить retry + timeout + backoff на вызов ASR (без падения цикла).
- Файлы проекта:
  - `ai-gateway/contracts.py`
  - `ai-gateway/plugins/audio.py`
  - `emeeting-backend/internal/analysis/validate.go`

**Результат:** при проблемах ASR остальные модули продолжают работу.

### A3. Улучшить face-модуль по качеству/производительности
- Добавить frame throttling (например, анализ каждого N-го кадра).
- Добавить quality guards (`face_detected=false`, confidence threshold).
- Файлы проекта:
  - `ai-gateway/plugins/frame.py`
  - `ai-gateway/modules.default.json`

**Результат:** меньше ложных срабатываний, ниже нагрузка CPU/GPU.

### A4. Проверка backend read-path
- Проверить сохранение/чтение analytics:
  - `GET /sessions/:id/analysis/events?limit=`
  - `GET /sessions/:id/analysis/report`
- Файлы проекта:
  - `emeeting-backend/internal/analysis/http_handlers.go`
  - `emeeting-backend/internal/analysis/repository.go`

**Результат:** аналитика доступна для UI/отладки через REST.

---

## Спринт B — Multimodal baseline (audio + partial reports)

### B1. Реальный baseline для audio_analysis
- Реализовать базовые аудио-фичи вместо stub:
  - energy, pause_ratio, tempo (минимум).
- Использовать идеи из `AI/solutions/emotion-recognition-using-speech`.
- Файлы проекта:
  - `ai-gateway/plugins/audio.py`
  - `docs/ANALYSIS_WS_CONTRACTS.md`

**Результат:** осмысленные `audio_analysis` partial события.

### B2. Усилить report orchestrator
- В `report_loop` добавить window join по:
  - `trace_id`
  - `participant_id`
  - time bucket
- Встроить маркер неполноты данных (если модуль недоступен).
- Файлы проекта:
  - `ai-gateway/report_loop.py`
  - `ai-gateway/feature_store.py`
  - `ai-gateway/own_nn_client.py`

**Результат:** полезные `analysis_report_partial`, даже при деградации одного модуля.

### B3. Наблюдаемость и SLO
- Зафиксировать метрики:
  - module latency p95,
  - error-rate per module,
  - report lag.
- Добавить лог-корреляцию по `trace_id` в каждом модуле.
- Файлы проекта:
  - `ai-gateway/observability.py`
  - `docs/ANALYSIS_OBSERVABILITY.md`

**Результат:** понятная диагностика и управляемая эксплуатация.

### B4. Сквозной smoke pipeline
- Расширить smoke-тесты:
  - frame -> face_analysis (+ emotion alias)
  - audio -> text_analysis + audio_analysis
  - report_loop -> analysis_report_partial
- Файлы проекта:
  - `ai-gateway/smoke_ws_emotion_test.py`
  - новые `ai-gateway/tests/*`

**Результат:** быстрый регрессионный прогон перед релизом.

---

## Ready-to-start Task List

1. Включить `modules.text.enabled=true` и подключить реальный `speech_service_url`.
2. Добавить retry/backoff в `adapters/speech_service.py`.
3. Добавить throttling/thresholds в `plugins/frame.py`.
4. Реализовать baseline audio features в `plugins/audio.py`.
5. Обновить smoke-тест под hybrid цепочку.

## Definition of Done (для 2 спринтов)

- В live сессии стабильно идут `face_analysis`, `audio_analysis`, `text_analysis`.
- Регулярно формируется `analysis_report_partial`.
- Backend сохраняет события/отчеты и отдает их через `/sessions/:id/analysis/*`.
- Модули переключаются только конфигом, без code changes.

---

**Примечание (2026-05):** большая часть пунктов спринтов A/B закрыта в репозитории (карточки **BL-030…BL-037** в `cursor backlog.md`). Дальнейшая **замена заглушек на прод-модели** ведётся по **`docs/AI_STUB_TO_PRODUCTION_ROADMAP.md`** и беклогу **BL-AI-101…109**.
