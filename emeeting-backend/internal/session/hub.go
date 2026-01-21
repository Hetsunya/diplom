package session

import (
	"log"
	"sync"

	"github.com/gorilla/websocket"
)

type SessionHub struct {
	mu       sync.RWMutex
	sessions map[int]map[*websocket.Conn]bool
}

func NewSessionHub() *SessionHub {
	return &SessionHub{
		sessions: make(map[int]map[*websocket.Conn]bool),
	}
}

func (h *SessionHub) Add(sessionID int, conn *websocket.Conn) {
	h.mu.Lock()
	defer h.mu.Unlock()

	if _, ok := h.sessions[sessionID]; !ok {
		h.sessions[sessionID] = make(map[*websocket.Conn]bool)
	}

	h.sessions[sessionID][conn] = true
	log.Printf("[HUB] client joined session=%d total=%d",
		sessionID, len(h.sessions[sessionID]))
}

func (h *SessionHub) Remove(sessionID int, conn *websocket.Conn) {
	h.mu.Lock()
	defer h.mu.Unlock()

	if clients, ok := h.sessions[sessionID]; ok {
		delete(clients, conn)
		log.Printf("[HUB] client left session=%d remaining=%d",
			sessionID, len(clients))

		if len(clients) == 0 {
			delete(h.sessions, sessionID)
			log.Printf("[HUB] session=%d closed", sessionID)
		}
	}
}

func (h *SessionHub) Broadcast(sessionID int, message any) {
	h.mu.RLock()
	defer h.mu.RUnlock()

	for conn := range h.sessions[sessionID] {
		_ = conn.WriteJSON(message)
	}
}
