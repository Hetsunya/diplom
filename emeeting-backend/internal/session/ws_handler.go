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
		return true // для dev
	},
}

type WSMessage struct {
	Type      string      `json:"type"`
	SessionID int         `json:"session_id"`
	Payload   interface{} `json:"payload"`
	Timestamp time.Time   `json:"timestamp"`
}

func (h *Handler) WS(c *gin.Context) {
	sessionIDStr := c.Param("id")
	sessionID, err := strconv.Atoi(sessionIDStr)
	if err != nil {
		log.Println("[WS] invalid session id:", sessionIDStr)
		c.AbortWithStatus(http.StatusBadRequest)
		return
	}

	log.Printf("[WS] incoming connection for session=%d\n", sessionID)

	conn, err := upgrader.Upgrade(c.Writer, c.Request, nil)
	if err != nil {
		log.Println("[WS] upgrade failed:", err)
		return
	}
	defer func() {
		log.Printf("[WS] connection closed session=%d\n", sessionID)
		conn.Close()
	}()

	log.Printf("[WS] CONNECTED session=%d remote=%s\n",
		sessionID,
		conn.RemoteAddr(),
	)

	// ping loop (чтобы видеть что соединение живо)
	go func() {
		ticker := time.NewTicker(10 * time.Second)
		defer ticker.Stop()

		for range ticker.C {
			msg := WSMessage{
				Type:      "ping",
				SessionID: sessionID,
				Timestamp: time.Now(),
			}

			if err := conn.WriteJSON(msg); err != nil {
				log.Println("[WS] ping failed:", err)
				return
			}

			log.Printf("[WS] ping sent session=%d\n", sessionID)
		}
	}()

	// read loop
	for {
		var incoming map[string]interface{}
		err := conn.ReadJSON(&incoming)
		if err != nil {
			log.Println("[WS] read error:", err)
			return
		}

		log.Printf("[WS] RECEIVED session=%d payload=%v\n", sessionID, incoming)

		resp := WSMessage{
			Type:      "echo",
			SessionID: sessionID,
			Payload:   incoming,
			Timestamp: time.Now(),
		}

		if err := conn.WriteJSON(resp); err != nil {
			log.Println("[WS] write error:", err)
			return
		}

		log.Printf("[WS] SENT session=%d\n", sessionID)
	}
}
