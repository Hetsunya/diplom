package session

import (
	"log"
	"net/http"
	"strconv"
	"time"

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
	broadcastHandler := func(sessionID int, msg WSMessage) {
		h.hub.Broadcast(sessionID, msg)
	}
	h.RegisterWSHandler("broadcast", broadcastHandler)
	h.RegisterWSHandler("frame", broadcastHandler)
	h.RegisterWSHandler("analytics", broadcastHandler)
}

func (h *Handler) dispatchWSMessage(sessionID int, msg WSMessage) {
	h.wsMu.RLock()
	handler, ok := h.wsMap[msg.Type]
	h.wsMu.RUnlock()
	if !ok {
		// Fallback for yet-unregistered types.
		h.hub.Broadcast(sessionID, msg)
		return
	}
	handler(sessionID, msg)
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

	// регистрируем в хабе
	h.hub.Add(sessionID, conn)
	defer h.hub.Remove(sessionID, conn)

	// ping loop
	go func() {
		ticker := time.NewTicker(10 * time.Second)
		defer ticker.Stop()

		for range ticker.C {
			msg := WSMessage{
				Type:      "ping",
				SessionID: sessionID,
				Timestamp: time.Now(),
			}
			h.hub.Broadcast(sessionID, msg)
			log.Printf("[WS] ping sent session=%d", sessionID)
		}
	}()

	// read loop
	for {
		var msg WSMessage
		if err := conn.ReadJSON(&msg); err != nil {
			log.Printf("[WS] DISCONNECT session=%d err=%v", sessionID, err)
			break
		}

		log.Printf(
			"[WS] RECEIVED type=%s session=%d participant=%s",
			msg.Type, msg.SessionID, msg.Participant,
		)

		h.dispatchWSMessage(sessionID, msg)
	}

}
