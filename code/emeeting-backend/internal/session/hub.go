package session

import (
	"log"
	"sync"

	"github.com/gorilla/websocket"
)

type SessionHub struct {
	mu        sync.RWMutex
	sessions  map[int]map[*websocket.Conn]bool
	connLocks map[*websocket.Conn]*sync.Mutex
}

func NewSessionHub() *SessionHub {
	return &SessionHub{
		sessions:  make(map[int]map[*websocket.Conn]bool),
		connLocks: make(map[*websocket.Conn]*sync.Mutex),
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
