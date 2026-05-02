package session

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strconv"
	"strings"
	"time"

	"emeeting/internal/analysis"

	"github.com/gin-gonic/gin"
	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		return true // для разработки
	},
}

func (h *Handler) RegisterWSHandler(messageType string, handler WSMessageHandler) {
	h.wsMu.Lock()
	defer h.wsMu.Unlock()
	h.wsMap[messageType] = handler
}

func (h *Handler) registerDefaultWSHandlers() {
	// Default behavior for known command types is broadcast.
	broadcastHandler := func(sessionID int, _ *websocket.Conn, msg WSMessage) {
		h.hub.Broadcast(sessionID, msg)
	}

	persistBroadcast := func(sessionID int, _ *websocket.Conn, msg WSMessage) {
		if h.analysisSvc != nil {
			_ = h.analysisSvc.RecordInbound(context.Background(), analysis.InboundWSMessage{
				Type:        msg.Type,
				SessionID:   sessionID,
				Participant: msg.Participant,
				Payload:     msg.Payload,
				Timestamp:   msg.Timestamp,
			})
		}
		h.hub.Broadcast(sessionID, msg)
	}
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

		// Keep backwards compatibility: still broadcast "join" WSMessage.
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

		// Полный список уже подключённых — чтобы поздние вкладки видели ранних без перезагрузки.
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
	leaveHandler := func(sessionID int, conn *websocket.Conn, msg WSMessage) {
		h.hub.RemoveConnJoinMeta(sessionID, conn)

		// Keep backwards compatibility: still broadcast "leave" WSMessage.
		h.hub.Broadcast(sessionID, msg)

		var name string
		if msg.Payload != nil {
			if m, ok := msg.Payload.(map[string]any); ok {
				if v, ok := m["name"].(string); ok {
					name = v
				}
			}
		}

		payload, _ := json.Marshal(map[string]any{
			"participant_id": msg.Participant,
			"name":           name,
			"left_at":        msg.Timestamp.UTC(),
		})
		h.hub.Broadcast(sessionID, WSEvent{
			Type:      "user_left",
			Payload:   payload,
			Timestamp: time.Now().UTC(),
		})
	}
	endMeetingHandler := func(sessionID int, _ *websocket.Conn, msg WSMessage) {
		// Only host should be allowed to end meeting. We accept role passed in payload
		// (server also tracks roles per connection for disconnect rules).
		role := ""
		if msg.Payload != nil {
			if m, ok := msg.Payload.(map[string]any); ok {
				if v, ok := m["role"].(string); ok {
					role = v
				}
			}
		}
		if role != "host" {
			return
		}
		now := time.Now().UTC()
		endPayload, _ := json.Marshal(map[string]any{
			"ended_at": now,
			"reason":   "host_ended",
		})
		h.hub.Broadcast(sessionID, WSEvent{
			Type:      "meeting_ended",
			Payload:   endPayload,
			Timestamp: now,
		})
	}
	h.RegisterWSHandler("broadcast", broadcastHandler)
	h.RegisterWSHandler("frame", broadcastHandler)
	h.RegisterWSHandler("audio", broadcastHandler)
	h.RegisterWSHandler("analytics", broadcastHandler)
	h.RegisterWSHandler("face_debug", broadcastHandler)
	// AI analytics inbound (from ai-gateway or future clients): persist + broadcast.
	h.RegisterWSHandler(analysis.TypeTextAnalysis, persistBroadcast)
	h.RegisterWSHandler(analysis.TypeAudioAnalysis, persistBroadcast)
	h.RegisterWSHandler(analysis.TypeFaceAnalysis, persistBroadcast)
	h.RegisterWSHandler(analysis.TypeAnalysisReport, persistBroadcast)
	h.RegisterWSHandler(analysis.TypeAnalysisReportPartial, persistBroadcast)
	h.RegisterWSHandler(analysis.TypeEmotionLegacy, persistBroadcast)
	h.RegisterWSHandler("join", joinHandler)
	h.RegisterWSHandler("leave", leaveHandler)
	h.RegisterWSHandler("end_meeting", endMeetingHandler)
	h.RegisterWSHandler("chat_message", h.chatMessageHandler())
}

func wsPayloadString(m map[string]any, key string) string {
	v, ok := m[key]
	if !ok || v == nil {
		return ""
	}
	switch t := v.(type) {
	case string:
		return strings.TrimSpace(t)
	case float64:
		return strconv.FormatInt(int64(t), 10)
	default:
		return strings.TrimSpace(fmt.Sprintf("%v", v))
	}
}

func parseChatInbound(payload any) (text, name, clientID string, ok bool) {
	m, ok := payload.(map[string]any)
	if !ok {
		return "", "", "", false
	}
	text = wsPayloadString(m, "text")
	if text == "" {
		return "", "", "", false
	}
	name = wsPayloadString(m, "name")
	clientID = wsPayloadString(m, "client_id")
	return text, name, clientID, true
}

func (h *Handler) chatMessageHandler() WSMessageHandler {
	return func(sessionID int, _ *websocket.Conn, msg WSMessage) {
		if h.chatRepo == nil {
			return
		}
		text, name, clientID, ok := parseChatInbound(msg.Payload)
		if !ok {
			return
		}
		pid := strings.TrimSpace(msg.Participant)
		if pid == "" {
			return
		}
		res, err := h.chatRepo.AppendMessage(context.Background(), sessionID, pid, clientID, name, text)
		if err != nil {
			log.Printf("[WS] chat_message persist session=%d err=%v", sessionID, err)
			return
		}
		if !res.Inserted {
			return
		}
		out := map[string]any{
			"text":            text,
			"name":            name,
			"chat_message_id": res.ChatMessageID,
		}
		if clientID != "" {
			out["client_id"] = clientID
		}
		msg.Payload = out
		h.hub.Broadcast(sessionID, msg)
	}
}

func (h *Handler) dispatchWSMessage(sessionID int, conn *websocket.Conn, msg WSMessage) {
	h.wsMu.RLock()
	handler, ok := h.wsMap[msg.Type]
	h.wsMu.RUnlock()
	if !ok {
		// Fallback for yet-unregistered types.
		h.hub.Broadcast(sessionID, msg)
		return
	}
	handler(sessionID, conn, msg)
}

func (h *Handler) WS(c *gin.Context) {
	sessionIDStr := c.Param("id")
	sessionID, err := strconv.Atoi(sessionIDStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid session id"})
		return
	}

	log.Printf("[WS] incoming connection for session=%d", sessionID)

	conn, err := upgrader.Upgrade(c.Writer, c.Request, nil)
	if err != nil {
		log.Println("[WS] upgrade failed:", err)
		return
	}
	defer conn.Close()

	log.Printf("[WS] CONNECTED session=%d remote=%s", sessionID, conn.RemoteAddr())
	done := make(chan struct{})

	// регистрируем в хабе
	h.hub.Add(sessionID, conn)
	participantID := ""
	participantName := ""
	participantRole := ""

	h.roleMu.Lock()
	if _, ok := h.connRoles[sessionID]; !ok {
		h.connRoles[sessionID] = make(map[*websocket.Conn]string)
	}
	h.connRoles[sessionID][conn] = participantRole
	h.roleMu.Unlock()

	defer func() {
		close(done)
		leaveAt := time.Now().UTC()
		endAt := leaveAt
		h.roleMu.Lock()
		delete(h.connRoles[sessionID], conn)
		remainingRoles := make([]string, 0, len(h.connRoles[sessionID]))
		for _, r := range h.connRoles[sessionID] {
			if r != "" {
				remainingRoles = append(remainingRoles, r)
			}
		}
		if len(h.connRoles[sessionID]) == 0 {
			delete(h.connRoles, sessionID)
		}
		h.roleMu.Unlock()

		if participantID != "" {
			// Broadcast leave so that clients can remove the participant tile.
			leaveMsg := WSMessage{
				Type:        "leave",
				SessionID:   sessionID,
				Participant: participantID,
				Payload: map[string]any{
					"name": participantName,
					"role": participantRole,
				},
				Timestamp: leaveAt,
			}
			h.hub.Broadcast(sessionID, leaveMsg)

			// Also emit server event envelope.
			payload, _ := json.Marshal(map[string]any{
				"participant_id": participantID,
				"name":           participantName,
				"role":           participantRole,
				"left_at":        leaveAt,
			})
			h.hub.Broadcast(sessionID, WSEvent{
				Type:      "user_left",
				Payload:   payload,
				Timestamp: leaveAt,
			})

			// If host left and there is no co-host, end the meeting.
			if participantRole == "host" {
				hasCoHost := false
				for _, r := range remainingRoles {
					if r == "co-host" {
						hasCoHost = true
						break
					}
				}
				if !hasCoHost {
					endPayload, _ := json.Marshal(map[string]any{
						"ended_at": endAt,
						"reason":   "host_left",
					})
					h.hub.Broadcast(sessionID, WSEvent{
						Type:      "meeting_ended",
						Payload:   endPayload,
						Timestamp: endAt,
					})
				}
			}
		}
		h.hub.Remove(sessionID, conn)
	}()

	// ping loop
	go func() {
		ticker := time.NewTicker(10 * time.Second)
		defer ticker.Stop()

		for {
			select {
			case <-done:
				return
			case <-ticker.C:
				msg := WSMessage{
					Type:      "ping",
					SessionID: sessionID,
					Timestamp: time.Now().UTC(),
				}
				h.hub.Broadcast(sessionID, msg)
				log.Printf("[WS] ping sent session=%d", sessionID)
			}
		}
	}()

	// read loop
	for {
		var msg WSMessage
		if err := conn.ReadJSON(&msg); err != nil {
			log.Printf("[WS] DISCONNECT session=%d err=%v", sessionID, err)
			break
		}

		// Track last known participant to emit `leave` on disconnect.
		if msg.Participant != "" {
			participantID = msg.Participant
		}
		if msg.Type == "join" && msg.Payload != nil {
			if m, ok := msg.Payload.(map[string]any); ok {
				if name, ok := m["name"].(string); ok {
					participantName = name
				}
				if role, ok := m["role"].(string); ok {
					participantRole = role
					h.roleMu.Lock()
					if _, ok := h.connRoles[sessionID]; !ok {
						h.connRoles[sessionID] = make(map[*websocket.Conn]string)
					}
					h.connRoles[sessionID][conn] = participantRole
					h.roleMu.Unlock()
				}
			}
		}
		if msg.Type == "leave" {
			// Explicit leave: avoid duplicate leave on deferred disconnect.
			participantID = ""
			participantName = ""
		}

		h.dispatchWSMessage(sessionID, conn, msg)
	}

}
