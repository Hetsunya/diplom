# Speech service (ASR)

HTTP сервис для `ai-gateway` (`adapters/speech_service.py`). Принимает фрагмент аудио в JSON и возвращает поля транскрипта.

## API

`POST /v1/transcribe`

Request JSON:

```json
{
  "session_id": 1,
  "participant_id": "p1",
  "trace_id": "uuid",
  "audio": {
    "chunk_base64": "<base64>",
    "mime": "audio/webm;codecs=opus",
    "encoding": "base64",
    "language": "ru"
  }
}
```

`language` в `audio` опционален: если не указан, Whisper может автоопределить язык.

Response JSON (пример):

```json
{
  "transcript_partial": "…",
  "transcript_final": null,
  "language": "ru",
  "text_features": { "confidence": 0.5 }
}
```

## Режимы

| Переменная | Значение | Описание |
|------------|----------|----------|
| `SPEECH_ASR_ENGINE` | `stub` (по умолчанию) | Мгновенный ответ без распознавания |
| `SPEECH_ASR_ENGINE` | `whisper` | Распознавание через **faster-whisper** (нужен **ffmpeg**) |
| `WHISPER_MODEL_SIZE` | `tiny`, `base`, `small`, … | Размер модели (по умолчанию `base`) |
| `WHISPER_DEVICE` | `cpu` / `cuda` | Устройство |
| `WHISPER_COMPUTE_TYPE` | `int8`, `float16`, … | Тип вычислений |
| `WHISPER_LANGUAGE` | ISO-код или пусто | Фиксированный язык; если пусто — авто |

Локально без Docker чаще удобно `SPEECH_ASR_ENGINE=stub` для быстрых проверок контракта; для реального текста — `whisper`.

## Запуск локально

```bash
pip install -r requirements.txt
# опционально: export SPEECH_ASR_ENGINE=whisper
uvicorn main:app --host 0.0.0.0 --port 8090
```

В `ai-gateway` укажите `modules.text.params.speech_service_url` (например `http://127.0.0.1:8090`).

## Docker

```bash
docker build -t emeeting-speech-service .
docker run --rm -p 8090:8090 -e SPEECH_ASR_ENGINE=whisper emeeting-speech-service
```

Образ включает `ffmpeg`, нужный faster-whisper для декодирования контейнеров вроде WebM.

## Поток данных

Клиент UI шлёт по WebSocket сообщения `type: "audio"` с `payload.chunk_base64` и `payload.mime` → backend транслирует в комнату → `ai-gateway` вызывает этот сервис → в комнату уходит `text_analysis`.
