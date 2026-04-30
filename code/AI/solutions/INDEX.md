# AI Solutions Base

Собранные репозитории для отбора под ваш pipeline.

## ASR / Text

- `whisperX-FastAPI`  
  FastAPI сервис для транскрибации/align/diarization (хороший кандидат для `speech-service`).

## Audio Emotion (SER)

- `emotion-recognition-using-speech`  
  Классические признаки + модели (быстрый baseline для `audio_analysis`).
- `speech-emotion-realtime-lstm`  
  Realtime SER на LSTM; полезно как reference для live-пайплайна.

## Face Emotion

- `realtime-deepface-mediapipe`  
  DeepFace + MediaPipe, можно взять quality guards и frame-throttling.
- `emotion-tracker`  
  Локальная аналитика эмоций, полезные идеи для persistence/агрегации.

## Multimodal Fusion

- `multimodal-emotion-recognition-zrr1999`  
  T/A/V модульная архитектура с конфигами и fusion (reference для `report_orchestrator`).
- `meld-cross-modal-transformers`  
  Cross-modal Transformer (исследовательский baseline для финальной нейросетки отчета).

## Рекомендация по интеграции

1. Быстрый production контур: `whisperX-FastAPI` + ваш `ai-gateway`.
2. Face улучшать через техники из `realtime-deepface-mediapipe`.
3. Audio начать с baseline из `emotion-recognition-using-speech`.
4. Для итоговой мультимодальной нейросети использовать идеи/структуру из двух fusion-реп.
