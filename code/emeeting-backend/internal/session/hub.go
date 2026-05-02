package session

import (
	"log"
	"sort"
	"sync"

	"github.com/gorilla/websocket"
)

type connJoinMeta struct {
	ParticipantID string
	Name            string
}

type SessionHub struct {
	mu        sync.RWMutex
	sessions  map[int]map[*websocket.Conn]bool
	connLocks map[*websocket.Conn]*sync.Mutex
	joinMeta  map[int]map[*websocket.Conn]connJoinMeta
}

func NewSessionHub() *SessionHub {
	return &SessionHub{
		sessions:  make(map[int]map[*websocket.Conn]bool),
		connLocks: make(map[*websocket.Conn]*sync.Mutex),
		joinMeta:  make(map[int]map[*websocket.Conn]connJoinMeta),
	}
}

func (h *SessionHub) Add(sessionID int, conn *websocket.Conn) {
	h.mu.Lock()
	defer h.mu.Unlock()

	if _, ok := h.sessions[sessionID]; !ok {
		h.sessions[sessionID] = make(map[*websocket.Conn]bool)
	}

	h.sessions[sessionID][conn] = true
	if _, ok := h.connLocks[conn]; !ok {
		h.connLocks[conn] = &sync.Mutex{}
	}
	log.Printf("[HUB] client joined session=%d total=%d",
		sessionID, len(h.sessions[sessionID]))
}

// SetJoinMeta запоминает участника для WS-соединения (после сообщения join).
func (h *SessionHub) SetJoinMeta(sessionID int, conn *websocket.Conn, participantID, name string) {
	if conn == nil {
		return
	}
	h.mu.Lock()
	defer h.mu.Unlock()
	if _, ok := h.joinMeta[sessionID]; !ok {
		h.joinMeta[sessionID] = make(map[*websocket.Conn]connJoinMeta)
	}
	h.joinMeta[sessionID][conn] = connJoinMeta{ParticipantID: participantID, Name: name}
}

// RemoveConnJoinMeta убирает участника с этой вкладки при явном leave (до disconnect).
func (h *SessionHub) RemoveConnJoinMeta(sessionID int, conn *websocket.Conn) {
	if conn == nil {
		return
	}
	h.mu.Lock()
	defer h.mu.Unlock()
	if jm, ok := h.joinMeta[sessionID]; ok {
		delete(jm, conn)
		if len(jm) == 0 {
			delete(h.joinMeta, sessionID)
		}
	}
}

// ParticipantSnapshot возвращает уникальных участников по последнему известному имени (для нового клиента).
func (h *SessionHub) ParticipantSnapshot(sessionID int) []map[string]any {
	h.mu.RLock()
	defer h.mu.RUnlock()
	metaMap := h.joinMeta[sessionID]
	if len(metaMap) == 0 {
		return nil
	}
	seen := make(map[string]bool)
	var out []map[string]any
	for _, meta := range metaMap {
		pid := meta.ParticipantID
		if pid == "" {
			continue
		}
		if seen[pid] {
			continue
		}
		seen[pid] = true
		name := meta.Name
		if name == "" {
			name = "Participant " + pid
		}
		out = append(out, map[string]any{
			"participant_id": pid,
			"name":           name,
		})
	}
	sort.Slice(out, func(i, j int) bool {
		a, _ := out[i]["participant_id"].(string)
		b, _ := out[j]["participant_id"].(string)
		return a < b
	})
	return out
}

func (h *SessionHub) Remove(sessionID int, conn *websocket.Conn) {
	h.mu.Lock()
	defer h.mu.Unlock()

	if jm, ok := h.joinMeta[sessionID]; ok {
		delete(jm, conn)
		if len(jm) == 0 {
			delete(h.joinMeta, sessionID)
		}
	}

	if clients, ok := h.sessions[sessionID]; ok {
		delete(clients, conn)
		log.Printf("[HUB] client left session=%d remaining=%d",
			sessionID, len(clients))

		if len(clients) == 0 {
			delete(h.sessions, sessionID)
			log.Printf("[HUB] session=%d closed", sessionID)
		}
	}
	delete(h.connLocks, conn)
}

func (h *SessionHub) Broadcast(sessionID int, message any) {
	h.mu.RLock()
	conns := make([]*websocket.Conn, 0, len(h.sessions[sessionID]))
	for conn := range h.sessions[sessionID] {
		conns = append(conns, conn)
	}
	h.mu.RUnlock()

	for _, conn := range conns {
		h.writeJSON(conn, message)
	}
}

// SendJSON отправляет одному соединению (например снимок участников после join).
func (h *SessionHub) SendJSON(conn *websocket.Conn, message any) {
	h.writeJSON(conn, message)
}

func (h *SessionHub) writeJSON(conn *websocket.Conn, message any) {
	h.mu.RLock()
	lock := h.connLocks[conn]
	h.mu.RUnlock()
	if lock == nil {
		return
	}
	lock.Lock()
	defer lock.Unlock()
	_ = conn.WriteJSON(message)
}
