# Материалы для отчёта по практике: система EMeeting

Документ сжимает **техническую базу**, **алгоритмы**, **схему взаимодействия сервисов** и **ориентиры по коду** монорепозитория. **Корень репозитория:** `diplom/` (этот файл — `diplom/practice.md`); **исходный код** — в `diplom/code/`. Пути к файлам в таблицах ниже — **от `code/`**, если не указано иначе. Полные контракты и планы — в `code/docs/`, runbook — в `diplom/README.md`.

Ранний прототип интерфейса (до текущей реализации) можно сопоставить с материалами в каталоге **`вкр/`** (например, `вкр/ui/схема ui.drawio`). Нижеследующие схемы отражают **актуальную** архитектуру стека EMeeting.

---

## 1. Цель и предмет разработки

**EMeeting** — программный комплекс для планирования онлайн-сессий, проведения видеовстречи в браузере, сбора аналитики по речи/лицу (через отдельный AI-шлюз) и просмотра отчётов. Практика охватывает полный цикл: UI, REST API, WebSocket, БД, опциональный стек ASR + gateway.

---

## 2. Состав системы (монорепозиторий)

| Компонент | Каталог | Роль |
|-----------|---------|------|
| **Frontend** | `emeeting-ui/` | SPA: React 19, TypeScript, Vite; маршруты, встреча, авторизация |
| **Backend** | `emeeting-backend/` | Go (Gin), JWT, PostgreSQL, REST + WS комнаты сессии |
| **AI Gateway** | `ai-gateway/` | Python: подключение к backend по WS, плагины анализа, вызов `speech-service` |
| **Speech service** | `speech-service/` | FastAPI: HTTP `/v1/transcribe` (stub или faster-whisper) |
| **Документация** | `docs/` | API, контракты WS аналитики, наблюдаемость, дорожные карты AI |

**Оркестрация:** `docker-compose.yml` в корне `diplom/` (сервисы `db`, `backend`, `ui`; профиль `ai` — `speech-service`, `ai-gateway`).

**Схема потоков (упрощённо):**

```
[Браузер UI] --REST/JWT--> [emeeting-backend] <--SQL--> [PostgreSQL]
      |                           ^
      | WS /ws/sessions/:id       | WS (ai-gateway подписан как клиент)
      v                           |
[Та же комната WS] <------------+ [ai-gateway] --HTTP--> [speech-service]
```

Клиент встречи шлёт по WS: `join`, `frame` (кадр для эмоций), `audio` (чанки), `chat_message`, `leave` / `end_meeting`. Backend рассылает события участникам и при необходимости пишет аналитику в БД. `ai-gateway` подписан на тот же канал (или multiplex), обрабатывает медиа и может эмитить обогащённые сообщения обратно в комнату (см. `docs/ANALYSIS_WS_CONTRACTS.md`).

---

## 3. Технологический стек

### 3.1. Frontend (`emeeting-ui`)

- **React** 19, **TypeScript**, **Vite** 7  
- **react-router-dom** — маршрутизация, **TanStack Query** — серверное состояние  
- **Zustand** — локальное состояние встречи (участники, тосты)  
- **Vitest** + Testing Library — unit-тесты  
- Ключевые страницы: `src/pages/Dashboard.tsx`, `Sessions.tsx`, `NewSession.tsx`, `VideoMeet.tsx`, `Login.tsx`, `Report.tsx`

### 3.2. Backend (`emeeting-backend`)

- **Go** 1.23+, модуль `emeeting`  
- **Gin** — HTTP, **gorilla/websocket** — WS  
- **golang.org/x/crypto/bcrypt** — пароли  
- **github.com/golang-jwt/jwt/v5** — access/refresh  
- **lib/pq** — драйвер PostgreSQL  
- Точка входа: `cmd/server/main.go` — подключение БД, CORS, middleware, регистрация модулей маршрутов

### 3.3. AI и речь

- **ai-gateway:** Python 3.11, конфиг модулей JSON, плагины в `plugins/`  
- **speech-service:** FastAPI, режимы `SPEECH_ASR_ENGINE=stub|whisper` (см. `speech-service/README.md`)

---

## 4. Backend: модули и порядок middleware

Из `cmd/server/main.go`:

1. `gin.Recovery()`, `RequestID`, `AccessLog`  
2. **CORS** (origins из `CORS_ALLOW_ORIGIN`)  
3. `RateLimitLogin()` — ограничение попыток входа  
4. `RequireAuth()` — для защищённых маршрутов (публичные исключения заданы в middleware)  
5. Модули: `health`, `auth`, `session`, `analysis`, `reports`, `ws`

**Сессии и WebSocket:** `internal/session/` — хаб соединений, обработчики типов сообщений (`join`, `leave`, `frame`, `audio`, …), upgrade WS, лимит размера сообщения (`wsMaxMessageBytes`).

**Аналитика:** `internal/analysis/` — запись входящих WS-сообщений аналитики, выдача по REST с правилами доступа (организатор vs участник с `participant_id`).

---

## 5. Алгоритмы и логика (для текста отчёта)

### 5.1. Авторизация

1. Клиент отправляет `POST /auth/login` с email и паролем.  
2. Сервер проверяет пользователя в БД, сравнивает пароль с **bcrypt**-хешем.  
3. Выдаётся пара **access** (короткий TTL) и **refresh** токенов; refresh хранится в БД с возможностью ротации.  
4. Последующие запросы: заголовок `Authorization: Bearer <access>` или cookie (в зависимости от реализации UI).  
5. Обновление сессии: `POST /auth/refresh` с телом, содержащим refresh-токен.

*Детали контрактов:* `docs/api-contract.md`, код `internal/auth/`.

### 5.2. Подключение к встрече по WebSocket

1. Клиент открывает `WebSocket` на URL вида `…/ws/sessions/:sessionId` (в dev — `ws://localhost:8080/ws/sessions/:id`; за прокси — относительный префикс из `VITE_WS_URL`).  
2. После `onopen` клиент шлёт сообщение **`join`** с `participant_id`, в `payload` — имя и роль (`host` / `participant`).  
3. **Backend** (`joinHandler` в `ws_handler.go`): сохраняет метаданные соединения, рассылает legacy `join`, затем событие **`user_joined`**, новому клиенту — **`participants_snapshot`** со списком уже подключённых.  
4. Дальнейшие сообщения (`chat_message`, `frame`, `audio`, …) обрабатываются зарегистрированными обработчиками: часть только **broadcast** в комнату, часть ещё **персистит** аналитику через `analysisSvc.RecordInbound`.

### 5.3. Список участников и завершение встречи

- Состояние участников на клиенте обновляется обработчиком **`handleMeetingEvent`** по типам `user_joined`, `user_left`, `participants_snapshot`, а также legacy `join`/`leave`.  
- При **`meeting_ended`** UI переходит к списку сессий (колбэк в `VideoMeet`).

### 5.4. Захват аудио для ASR (браузер)

Реализовано в `useMeetingAudioChunks.ts`:

1. Берётся **только аудиодорожка** микрофона (`MediaStream` с audio tracks).  
2. Создаётся **`MediaRecorder`** с подбором поддерживаемого MIME (webm/opus и др.).  
3. По тайм-слайсу накапливаются куски **в один непрерывный буфер** (важно для корректного WebM: init-сегмент + кластеры).  
4. Периодически или по лимиту времени/размера буфер кодируется в **Base64** и отправляется по WS типом **`audio`** (поля согласованы с gateway).  
5. При остановке/смене потока — корректная отмена и освобождение recorder.

### 5.5. Захват видеокадров для анализа лица

- В `VideoMeet.tsx` по интервалу (например ~320 ms) вызывается захват кадра с `<video>` и отправка **`frame`** с полезной нагрузкой (например JPEG base64).  
- Ответы/события аналитики приходят тем же WS: `face_analysis`, legacy `emotion`, опционально `face_debug`.

### 5.6. Транскрипт в UI

- События **`text_analysis`** содержат `transcript_partial` / `transcript_final`, `stage`, `trace_id`.  
- В UI для одного спикера поддерживается **один «черновик»** на `participant_id` (стабильный `traceId` вида `asr-draft:<pid>`), финальная реплика добавляется отдельной строкой.  
- Отображение: хронологическая лента в правой панели (`MeetingTranscriptRail.tsx`).

### 5.7. Speech-service

1. **POST** `/v1/transcribe` с JSON: `session_id`, `participant_id`, `trace_id`, `audio` (base64, mime, язык).  
2. Режим **stub** — детерминированный ответ без распознавания.  
3. Режим **whisper** — декодирование base64, вызов faster-whisper через `asr_whisper.py`, возврат partial/final и `text_features`.

### 5.8. AI Gateway (концептуально)

- Читает конфиг модулей (`modules.default.json` / `modules.docker.json`).  
- Поддерживает цепочки: аудио → HTTP в speech-service → нормализация в события `text_analysis`; видеокадры → модуль лица; агрегация → `analysis_report` / partial.  
- Подробности: `ai-gateway/MEMO.md`, `docs/ANALYSIS_WS_CONTRACTS.md`.

---

## 6. База данных

- Миграции: `emeeting-backend/migrations/up/*.sql` и `down/`.  
- Сущности (по именам файлов миграций): пользователи и auth, сессии, участники встречи, состояние митинга, refresh-токены, события auth, аналитика (`analysis`), чат сессии и т.д.  
- Описание порядка применения: `emeeting-backend/migrations/README.md`.

---

## 7. Контракты REST и WS (где искать)

| Тема | Файл |
|------|------|
| REST v1 (логин, сессии, чат, аналитика) | `docs/api-contract.md` |
| WS-типы аналитики (`text_analysis`, `face_analysis`, отчёты) | `docs/ANALYSIS_WS_CONTRACTS.md` |
| Метрики и логирование | `docs/ANALYSIS_OBSERVABILITY.md` |
| План развития AI | `docs/AI_STUB_TO_PRODUCTION_ROADMAP.md` |

---

## 8. Листинги и опорные фрагменты кода

Ниже — **сокращённые** фрагменты; полный код в указанных файлах.

### 8.1. Регистрация сервера и модулей (Go)

```24:65:emeeting-backend/cmd/server/main.go
func main() {
	postgresDSN := getEnv("POSTGRES_DSN", "postgres://postgres:1040@localhost:5432/emeeting?sslmode=disable")
	serverPort := getEnv("SERVER_PORT", "8080")
	corsOrigin := getEnv("CORS_ALLOW_ORIGIN", "http://localhost:5173,http://127.0.0.1:5173")

	// DB
	database, err := db.NewPostgres(postgresDSN)
	if err != nil {
		log.Fatal("DB connection failed:", err)
	}

	// gin
	r := gin.New()
	r.Use(gin.Recovery())
	r.Use(middleware.RequestID())
	r.Use(middleware.AccessLog())

	allowedOrigins := splitCSV(corsOrigin)
	r.Use(cors.New(cors.Config{
		AllowOrigins:     allowedOrigins,
		AllowOriginFunc:  isAllowedDevOrigin(allowedOrigins),
		AllowMethods:     []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowHeaders:     []string{"Origin", "Content-Type", "Accept", "Authorization", "X-Request-ID"},
		AllowCredentials: true,
		MaxAge:           12 * 60 * 60,
	}))

	r.Use(middleware.RateLimitLogin())
	r.Use(middleware.RequireAuth())

	modules := []server.RouteModule{
		health.NewModule(database),
		auth.NewModule(database),
		session.NewModule(database),
		analysis.NewModule(database),
		reports.NewModule(),
		ws.NewModule(),
	}
	for _, module := range modules {
		module.RegisterRoutes(r)
	}
	// ...
}
```

### 8.2. Обработка `join` на backend: user_joined + snapshot

```59:96:emeeting-backend/internal/session/ws_handler.go
	joinHandler := func(sessionID int, conn *websocket.Conn, msg WSMessage) {
		var name string
		if msg.Payload != nil {
			if m, ok := msg.Payload.(map[string]any); ok {
				if v, ok := m["name"].(string); ok {
					name = v
				}
			}
		}
		pid := strings.TrimSpace(msg.Participant)
		if pid != "" && conn != nil {
			h.hub.SetJoinMeta(sessionID, conn, pid, name)
		}

		h.hub.Broadcast(sessionID, msg)

		payload, _ := json.Marshal(map[string]any{
			"participant_id": msg.Participant,
			"name":           name,
			"joined_at":      msg.Timestamp.UTC(),
		})
		h.hub.Broadcast(sessionID, WSEvent{
			Type:      "user_joined",
			Payload:   payload,
			Timestamp: time.Now().UTC(),
		})

		if conn != nil {
			snap := h.hub.ParticipantSnapshot(sessionID)
			snapBody, _ := json.Marshal(map[string]any{"participants": snap})
			h.hub.SendJSON(conn, WSEvent{
				Type:      "participants_snapshot",
				Payload:   snapBody,
				Timestamp: time.Now().UTC(),
			})
		}
	}
```

### 8.3. Связка WS встречи на клиенте

```1:31:emeeting-ui/src/features/meeting/useMeetingWebSocket.ts
import { useMeetingStore } from "./useMeetingStore";
import { handleMeetingEvent } from "./handleMeetingEvent";
import { useSessionWS } from "../../hooks/useSessionWS";

export function useMeetingWebSocket(
  sessionId: string,
  participantId: string,
  onMessage?: (msg: unknown) => void,
  onMeetingEnded?: (payload: unknown) => void
) {
  const upsertParticipant = useMeetingStore((s) => s.upsertParticipant);
  const removeParticipant = useMeetingStore((s) => s.removeParticipant);
  const replaceParticipantsFromSnapshot = useMeetingStore((s) => s.replaceParticipantsFromSnapshot);
  const pushToast = useMeetingStore((s) => s.pushToast);

  return useSessionWS(
    sessionId,
    participantId,
    (msg) => {
      handleMeetingEvent(msg, {
        upsertParticipant,
        removeParticipant,
        replaceParticipantsFromSnapshot,
        pushToast,
        onMeetingEnded,
      });
      onMessage?.(msg);
    },
    { reconnect: true }
  );
}
```

### 8.4. Разбор доменных событий встречи (фрагмент)

```20:50:emeeting-ui/src/features/meeting/handleMeetingEvent.ts
export function handleMeetingEvent(msg: unknown, ops: Ops) {
  if (!isRecord(msg)) return;
  const type = typeof msg.type === "string" ? msg.type : undefined;
  if (!type) return;

  const event = msg as WSEvent;
  const payload = event.payload;

  if (type === "user_joined" && isRecord(payload)) {
    const p = payload as unknown as UserJoinedPayload & Record<string, unknown>;
    const id = typeof p.participant_id === "string" ? p.participant_id : undefined;
    if (!id) return;
    const name = typeof p.name === "string" && p.name.length > 0 ? p.name : `Participant ${id}`;
    ops.upsertParticipant({ id, name });
    ops.pushToast?.(`${name} подключился(лась)`);
    return;
  }

  if (type === "user_left" && isRecord(payload)) {
    // ...
  }

  if (type === "meeting_ended") {
    ops.onMeetingEnded?.(payload);
    return;
  }
  // participants_snapshot, legacy join/leave …
}
```

### 8.5. Построение URL WebSocket на клиенте

```17:31:emeeting-ui/src/hooks/useSessionWS.ts
  const buildSocketUrl = (sid: string) => {
    const raw = (WS_URL || "").trim().replace(/\/+$/, "");
    if (raw.startsWith("ws://") || raw.startsWith("wss://")) {
      return `${raw}/ws/sessions/${sid}`;
    }
    if (raw.startsWith("http://") || raw.startsWith("https://")) {
      const wsBase = raw.replace(/^http/i, "ws");
      return `${wsBase}/ws/sessions/${sid}`;
    }
    if (raw.startsWith("/")) {
      return `${raw}/sessions/${sid}`;
    }
    return `${DEFAULT_WS_URL}/ws/sessions/${sid}`;
  };
```

### 8.6. Идея useMeetingAudioChunks (заголовок и контракт)

```57:68:emeeting-ui/src/features/meeting/useMeetingAudioChunks.ts
/**
 * Sends periodic mic chunks over WS as `type: "audio"` for ai-gateway speech pipeline.
 *
 * MediaRecorder timeslice blobs are often **not** standalone WebM files; ffmpeg/Whisper needs
 * the initialization segment plus subsequent clusters. We concatenate all blobs since the last
 * segment boundary and POST that cumulative buffer so decoding stays stable.
 */
export function useMeetingAudioChunks(
  streamRef: React.RefObject<MediaStream | null>,
  send: (type: string, payload?: unknown) => void,
  opts: { enabled: boolean; mediaReady: boolean; streamEpoch?: number; timesliceMs?: number }
) {
```

### 8.7. Speech-service: модель запроса и stub

```44:57:speech-service/main.py
class TranscribeRequest(BaseModel):
    session_id: int
    participant_id: str
    trace_id: str
    audio: dict[str, Any] = {}


def _stub_response(req: TranscribeRequest) -> dict[str, Any]:
    return {
        "transcript_partial": f"[stub] session={req.session_id} participant={req.participant_id}",
        "transcript_final": None,
        "language": "ru",
        "text_features": {"confidence": 0.42, "sentiment": "neutral"},
    }
```

---

## 9. Тестирование и CI

- **Frontend:** `npm run lint`, `npm run test` (Vitest), `npm run build` — см. `.github/workflows/ci.yml` в корне `diplom/`.  
- **Backend:** `go vet ./...`, `go test ./...`, `go build ./...`.  
- **ai-gateway:** `python -m compileall .` в CI.

Примеры тестов UI: `emeeting-ui/src/features/meeting/handleMeetingEvent.test.ts`, `emeeting-ui/src/hooks/useSessionWS.test.tsx`.

---

## 10. Чек-лист формулировок для отчёта по практике

Можно напрямую разворачивать в разделы отчёта:

1. **Постановка задачи:** веб-платформа сессий и видеовстреч с аналитикой и отчётностью.  
2. **Проектирование:** клиент–сервер, REST + WebSocket, выделение ASR и AI в отдельные сервисы.  
3. **Реализация:** стек по табл. §3; модульность backend; компонентный UI; хуки для медиа и WS.  
4. **Безопасность:** HTTPS/wss в проде; bcrypt; JWT; rate limit на логин; разграничение доступа к аналитике (организатор / участник).  
5. **Проверка:** unit-тесты, CI, ручной сценарий Docker Compose.  
6. **Заключение:** достигнутые результаты, ограничения (stub-режимы, зависимость от профиля `ai`, размер WS-сообщений).

---

## 11. Индекс файлов «для вставки в приложение к отчёту»

| Назначение | Путь |
|------------|------|
| Точка входа backend | `emeeting-backend/cmd/server/main.go` |
| WS сессии, join/leave/audio | `emeeting-backend/internal/session/ws_handler.go`, `hub.go` |
| Авторизация | `emeeting-backend/internal/auth/` |
| Страница встречи | `emeeting-ui/src/pages/VideoMeet.tsx` |
| Правая панель (транскрипт, чат, люди) | `emeeting-ui/src/features/meeting/MeetingTranscriptRail.tsx` |
| События встречи в state | `emeeting-ui/src/features/meeting/handleMeetingEvent.ts` |
| WS hook | `emeeting-ui/src/hooks/useSessionWS.ts` |
| Аудио-чанки | `emeeting-ui/src/features/meeting/useMeetingAudioChunks.ts` |
| ASR HTTP | `speech-service/main.py`, `speech-service/asr_whisper.py` |
| Конфиг gateway | `ai-gateway/modules.default.json`, `ai-gateway/gateway_config.py` |

---

## 12. Схемы моделирования (BPMN, IDEF0, DFD, ER, логическая БД)

Диаграммы ниже в формате **Mermaid** (рендер в GitHub, GitLab, VS Code / Cursor с предпросмотром Markdown) и **ASCII** для IDEF0. При требовании кафедры к «родным» BPMN/DFD в **draw.io / Visio** — импортируйте как подложку или перерисуйте по этим моделям.

### 12.1. BPMN (основной сценарий: от входа до встречи и аналитики)

Упрощённая модель с дорожками **Участник**, **emeeting-backend**, **Внешние сервисы** (профиль `ai`). Шлюз XOR: опциональное подключение ASR/gateway.

```mermaid
flowchart TB
  subgraph LaneU["Дорожка: Участник / организатор"]
    A([Старт]) --> B[Открыть приложение]
    B --> C{Есть валидный JWT?}
    C -->|Нет| D[POST /auth/login]
    D --> E[Получить access + refresh]
    E --> C
    C -->|Да| F[REST: сессии / открыть встречу]
    F --> G[WebSocket /ws/sessions/:id]
    G --> H[join + медиа / чат]
    H --> I[leave или end_meeting]
    I --> K([Конец])
  end

  subgraph LaneB["Дорожка: emeeting-backend"]
    HB[join → user_joined +\nparticipants_snapshot]
    IB[broadcast + опционально\nзапись analysis_event]
    JB[meeting_ended / disconnect]
  end

  subgraph LaneX["Дорожка: ai-gateway + speech-service\n(compose profile ai)"]
    IX[Приём audio / frame]
    IY[ASR HTTP + плагины]
  end

  H -.-> HB
  H -.-> IB
  H -.-> IX
  IX --> IY
  IY -.->|события аналитики в комнату| IB
  I -.-> JB
```

**События и артефакты:** JWT; сообщения WS (`join`, `frame`, `audio`, `chat_message`); при включённом AI — HTTP в `speech-service`, обратные WS-сообщения по контракту `docs/ANALYSIS_WS_CONTRACTS.md`.

---

### 12.2. IDEF0, контекстная диаграмма A-0 (без декомпозиции)

Одна функция верхнего уровня — **«Обеспечить проведение веб-конференции и сбор аналитики в системе EMeeting»**. Стрелки ICOM:

| Тип | Содержание (по смыслу реализации) |
|-----|-----------------------------------|
| **Входы (Input)** | Учётные данные пользователя; команды и медиаданные (кадры, аудиочанки, текст чата); параметры сессии (название, время, тип). |
| **Выходы (Output)** | Отображение встречи и списков в UI; сохранённые записи аналитики и чата; агрегированные отчёты; уведомления участникам по WS. |
| **Управление (Control)** | Политики безопасности (JWT, rate limit логина); контракты REST/WS; настройки CORS и окружения Docker. |
| **Механизмы (Mechanism)** | Браузер (React); сервер `emeeting-backend` (Go); СУБД PostgreSQL; при включении — `ai-gateway` (Python), `speech-service` (FastAPI). |

ASCII-вид (для вставки в отчёт, если Markdown не рендерится):

```
                    ┌── Управление (Control) ──────────────────────────────┐
                    │ JWT, rate limit, контракты API/WS, CORS, compose    │
                    └──────────────────────────┬──────────────────────────┘
                                               │
  Входы (Input)                                ▼
  креды, медиа,          ┌─────────────────────────────────────────┐
  команды WS,      ───►  │  A-0: EMeeting — веб-конференция       │
  данные сессии          │      и аналитика                        │
                         └─────────────────┬───────────────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ▼                                             ▼
           Выходы (Output)                               Механизмы (Mechanism)
           UI, отчёты, записи БД, WS-события              React, Gin, PostgreSQL,
                                                          ai-gateway, speech-service
```

---

### 12.3. DFD (потоки данных)

#### Уровень 0 (контекст)

```mermaid
flowchart LR
  U([Пользователь\nбраузер])
  SYS[[П0: Система\nEMeeting]]
  DB[(D1: PostgreSQL)]
  AI[[Внешний контур AI\n gateway + ASR]]

  U -->|запросы REST, WS,\nмедиа| SYS
  SYS -->|ответы, события WS| U
  SYS <-->|SQL| DB
  SYS <-->|опционально:\nHTTP / WS события| AI
```

#### Уровень 1 (основные процессы и хранилища)

```mermaid
flowchart TB
  U([Пользователь])

  subgraph Stores["Хранилища данных"]
    D_AUTH[(D2: auth_user,\nrefresh_tokens,\nauth_events)]
    D_SESS[(D3: session,\nmeeting_events,\nmeeting_participant)]
    D_ANA[(D4: analysis_event,\nanalysis_report)]
    D_CHAT[(D5: session_chat_message)]
  end

  P1[[P1:\nАутентификация]]
  P2[[P2:\nУправление сессиями]]
  P3[[P3:\nКомната встречи WS]]
  P4[[P4:\nПерсистенция аналитики]]
  P5[[P5:\nЧат сессии]]
  P6[[P6:\nОтчёты / выдача]]

  U -->|логин| P1
  P1 <-->|чтение/запись| D_AUTH
  U -->|CRUD сессий| P2
  P2 <-->|SQL| D_SESS
  U -->|WS медиа/чат| P3
  P3 <-->|участники, статус| D_SESS
  P3 -->|сохранить события| P4
  P4 <-->|вставка/выборка| D_ANA
  P3 -->|сообщения чата| P5
  P5 <-->|SQL| D_CHAT
  U -->|запрос отчёта| P6
  P6 <-->|SQL| D_ANA
  P6 -->|JSON отчёта| U
```

*Примечание:* внешний контур `ai-gateway` на DFD уровня 1 можно показать отдельным процессом **P7 «Обогащение аналитики»** между P3 и P4; здесь он свёрнут в поток «WS → gateway → обратно в комнату» для краткости.

---

### 12.4. ER-диаграмма (сущности и связи по миграциям)

```mermaid
erDiagram
  auth_user {
    int auth_user_id PK
    string email UK
    string password_hash
    boolean is_active
    timestamptz created_at
    int failed_login_attempts
    timestamptz locked_until
  }
  refresh_tokens {
    bigint refresh_token_id PK
    string token_hash UK
    int user_id FK
    timestamptz expires_at
    timestamptz revoked_at
  }
  auth_events {
    bigint auth_event_id PK
    int auth_user_id FK
    string event_type
    timestamptz created_at
  }
  session {
    int session_id PK
    string title
    string session_type
    timestamp start_datetime
    int created_by FK
    string meeting_status
  }
  meeting_events {
    bigint meeting_event_id PK
    int session_id FK
    string event_type
    jsonb payload
  }
  meeting_participant {
    int meeting_participant_id PK
    int session_id FK
    int auth_user_id FK
    string role_code
    boolean is_active
  }
  analysis_event {
    bigint analysis_event_id PK
    int session_id FK
    string event_type
    string participant_id
    jsonb payload
  }
  analysis_report {
    bigint analysis_report_id PK
    int session_id FK
    string stage
    jsonb report
  }
  session_chat_message {
    bigint chat_message_id PK
    int session_id FK
    string participant_id
    text body
  }

  auth_user ||--o{ refresh_tokens : "user_id"
  auth_user ||--o{ auth_events : "auth_user_id"
  auth_user ||--o{ session : "created_by"
  session ||--o{ meeting_events : "session_id"
  session ||--o{ meeting_participant : "session_id"
  auth_user |o--o{ meeting_participant : "auth_user_id"
  session ||--o{ analysis_event : "session_id"
  session ||--o{ analysis_report : "session_id"
  session ||--o{ session_chat_message : "session_id"
```

---

### 12.5. Логическая модель данных (атрибуты по таблицам)

Краткое описание таблиц PostgreSQL (логический уровень «сущность — атрибуты — ключи»). Источник истины — файлы `code/emeeting-backend/migrations/up/*.sql`.

| Таблица | Назначение | Ключ / важные атрибуты |
|---------|------------|-------------------------|
| **schema_migrations** | учёт применённых миграций | `version` PK |
| **auth_user** | пользователь | `auth_user_id` PK; `email` UK; `password_hash`; `is_active`; защита: `failed_login_attempts`, `locked_until` |
| **refresh_tokens** | refresh JWT | `refresh_token_id` PK; `token_hash` UK; `user_id` → auth_user; `expires_at`, `revoked_at`, ротация `replaced_by_token_hash` |
| **auth_events** | аудит auth | `auth_event_id` PK; `event_type`; `auth_user_id` FK nullable; `ip`, `payload` JSONB |
| **session** | планируемая сессия / встреча | `session_id` PK; `title`, `session_type`, `start_datetime`, `end_datetime`; `created_by` → auth_user; `meeting_status`, `meeting_started_at`, `meeting_ended_at` |
| **meeting_events** | журнал событий митинга | PK; `session_id` FK; `event_type`; `payload` JSONB |
| **meeting_participant** | роль в сессии | PK; `session_id` FK; `auth_user_id` FK nullable (гость); `role_code`; `joined_at`, `left_at`, `is_active` |
| **analysis_event** | событие аналитики (WS) | PK; `session_id` FK; `event_type`, `participant_id`, `trace_id`, `module`, `stage`, `payload` JSONB |
| **analysis_report** | снимок отчёта | PK; `session_id` FK; `stage`, `trace_id`, `report` JSONB, `config_snapshot` JSONB |
| **session_chat_message** | чат встречи | PK; `session_id` FK; `participant_id`, `client_message_id`, `sender_name`, `body` (1…2000 символов) |

**Целостность:** каскадное удаление дочерних записей при удалении `session` для событий митинга, аналитики и чата; `refresh_tokens` и связанные данные — при удалении пользователя (см. `ON DELETE` в SQL).

---

*Файл подготовлен как консолидированная шпаргалка; при изменении кода обновляйте разделы 5–8 и §12 по актуальным коммитам и миграциям.*
