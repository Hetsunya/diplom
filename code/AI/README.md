## AI Gateway: эмоции из видео (MVP)

Этот раздел описывает то, как сейчас в проекте запускается распознавание эмоций и как UI “сшивается” с `ai-gateway` через WebSocket.

### Что уже работает (в проекте)
1. UI периодически отправляет в backend WS-сессию сообщения `type: "frame"`.
2. `ai-gateway` принимает `frame`, делает inference по лицу (в MVP — только эмоции) через `DeepFace`.
3. `ai-gateway` отправляет обратно в backend событие `type: "emotion"`.
4. UI использует `emotion` для отображения эмоций на плитках и для агрегации статистики в отчёте.

### Contract сообщений (ключевое)
1. От UI к backend:
   - `type`: `"frame"`
   - `payload.frame`: строка вида `"data:image/jpeg;base64,..."`.
2. От `ai-gateway` к backend (и далее к UI):
   - `type`: `"emotion"`
   - `payload`:
     - `emotion`: доминирующая эмоция (строка DeepFace, напр. `happy`, `neutral`)
     - `confidence`: оценка уверенности (значение от модели)
     - `probs`: словарь вероятностей/оценок по классам (если модель вернула)

### Почему выбран DeepFace
DeepFace даёт готовую интеграцию “из коробки”: inference по выражению лица с возвращением `dominant_emotion` и распределения по классам, без необходимости отдельно хранить веса внутри репозитория.

### Установка зависимостей `ai-gateway`
Для локального запуска:
```bash
pip install -r requirements.txt
```

Для Docker:
- Dockerfile для `ai-gateway` устанавливает зависимости из `requirements.txt`, поэтому для контейнера также нужен `pip install -r requirements.txt`.

### Аудио и модульная аналитика (обновление)

См. также:

- Контракты v1: [`../docs/ANALYSIS_WS_CONTRACTS.md`](../docs/ANALYSIS_WS_CONTRACTS.md)
- Наблюдаемость / SLO: [`../docs/ANALYSIS_OBSERVABILITY.md`](../docs/ANALYSIS_OBSERVABILITY.md)
- Конфиг модулей: `ai-gateway/modules.default.json`, памятка `ai-gateway/MEMO.md`
- Отдельный ASR: каталог `speech-service/` (HTTP stub + контракт для `ai-gateway/adapters/speech_service.py`)

Поведение `frame`: помимо legacy `emotion` шлюз шлёт `face_analysis` с полями `module`, `stage`, `trace_id`, `version` в `payload`.
