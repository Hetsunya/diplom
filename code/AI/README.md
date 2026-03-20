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

### Аудио (следующий шаг)
В этом MVP аудио ещё не отправляется в `ai-gateway` и не анализируется.
Дальше можно подключить:
- ASR: `Whisper` (speech-to-text)
- эмоции голоса: `openSMILE` или `SpeechBrain`
- фьюжн: простая агрегация по времени (moving average / majority vote) до перехода к более сложным моделям.

