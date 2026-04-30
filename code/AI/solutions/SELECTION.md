# AI Solutions Selection

Цель: выбрать, что интегрируем в текущий стек (`ai-gateway` + `emeeting-backend`) без лишнего риска.

## Краткий вердикт

- **Берем сейчас (MVP/production path):**
  - `whisperX-FastAPI`
  - `realtime-deepface-mediapipe` (частично, как source идей)
  - `emotion-recognition-using-speech` (частично, baseline фичей)
- **Берем позже (R&D/next iterations):**
  - `speech-emotion-realtime-lstm`
  - `multimodal-emotion-recognition-zrr1999`
  - `meld-cross-modal-transformers`
  - `emotion-tracker` (только аналитические идеи)

## Матрица отбора

| Repo | Роль в проекте | Интеграция | Лицензия | Решение |
|---|---|---|---|---|
| `whisperX-FastAPI` | Отдельный ASR сервис (`text_analysis`) | Низкая/средняя | MIT | Берем сейчас |
| `realtime-deepface-mediapipe` | Улучшение face-модуля (качество/оптимизация) | Низкая | MIT | Берем сейчас (частично) |
| `emotion-recognition-using-speech` | Baseline для `audio_analysis` | Средняя | MIT | Берем сейчас (частично) |
| `speech-emotion-realtime-lstm` | Альтернативный realtime SER | Средняя/высокая | Проверить в репо | Позже |
| `multimodal-emotion-recognition-zrr1999` | Архитектура fusion T/A/V | Высокая | MIT | Позже |
| `meld-cross-modal-transformers` | Исследовательский fusion baseline | Высокая | MIT | Позже |
| `emotion-tracker` | UX/метрики/логирование эмоций | Низкая | MIT | Позже (идеи) |

## Что использовать прямо сейчас

### 1) ASR/Text
- Внедрить `whisperX-FastAPI` как внешний `speech-service`.
- Подключение через ваш адаптер: `ai-gateway/adapters/speech_service.py`.
- Маппинг в ваш контракт: `type="text_analysis"`, `payload.module/stage/trace_id/version`.

### 2) Face Emotion
- Оставить текущий DeepFace путь как основной.
- Из `realtime-deepface-mediapipe` взять:
  - frame throttling (не анализировать каждый кадр),
  - quality guards (`face_detected`, confidence threshold),
  - базовые performance-практики.

### 3) Audio Emotion
- В `audio` модуль добавить baseline фичи и классификатор из идей `emotion-recognition-using-speech`.
- Начать с chunk-level `audio_analysis` partial, без усложнения end-to-end моделей.

## Что не тащить в основной контур пока

- Полные обучающие пайплайны multimodal fusion (`zrr1999`, `meld-cross-modal-transformers`) в production сейчас не нужны:
  - много зависимостей,
  - большие требования к данным/GPU,
  - высокий риск затянуть сроки.
- Использовать их как reference для вашей будущей собственной нейросети отчетов.

## Рекомендуемая последовательность (практично)

1. Поднять `whisperX-FastAPI` локально/в docker, связать с gateway.
2. Стабилизировать `text_analysis` контракт и обработку ошибок.
3. Усилить `face_analysis` quality/performance.
4. Добавить baseline `audio_analysis`.
5. После стабилизации событий перейти к fusion-модели итогового отчета.

## Критерии “готово к использованию”

- Модуль включается/выключается только конфигом.
- При падении внешнего ASR остальные модули продолжают работу.
- Все события проходят через единый контракт `ANALYSIS_WS_CONTRACTS`.
- В backend сохраняются и читаются `analysis_event`/`analysis_report`.
