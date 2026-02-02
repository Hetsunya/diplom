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

// Это страрое и уехало в contracts.go
// type WSMessage struct {
// 	Type      string    `json:"type"`
// 	SessionID int       `json:"session_id"`
// 	Payload   any       `json:"payload"`
// 	Timestamp time.Time `json:"timestamp"`
// }

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

		//todo
		switch msg.Type {
		// case "frame":
		// 	h.handleFrame(sessionID, msg)

		// case "analytics":
		// 	h.handleAnalytics(sessionID, msg)

		default:
			h.hub.Broadcast(sessionID, msg)
		}
	}

}
