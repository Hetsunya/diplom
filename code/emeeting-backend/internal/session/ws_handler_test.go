package session

import (
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/gorilla/websocket"
)

func TestWSSessionConnectionSmoke(t *testing.T) {
	gin.SetMode(gin.TestMode)

	handler := NewHandler(NewService(newFakeRepo()), NewSessionHub())
	r := gin.New()
	r.GET("/ws/sessions/:id", handler.WS)

	server := httptest.NewServer(r)
	defer server.Close()

	wsURL := "ws" + strings.TrimPrefix(server.URL, "http") + "/ws/sessions/1"
	conn, _, err := websocket.DefaultDialer.Dial(wsURL, nil)
	if err != nil {
		t.Fatalf("failed to connect websocket: %v", err)
	}
	defer conn.Close()

	msg := WSMessage{
		Type:        "test",
		SessionID:   1,
		Participant: "p1",
		Payload:     map[string]any{"ok": true},
		Timestamp:   time.Now(),
	}
	if err := conn.WriteJSON(msg); err != nil {
		t.Fatalf("failed to write websocket message: %v", err)
	}

	_ = conn.SetReadDeadline(time.Now().Add(2 * time.Second))
	var got WSMessage
	if err := conn.ReadJSON(&got); err != nil {
		t.Fatalf("failed to read websocket message: %v", err)
	}
	if got.Type != msg.Type {
		t.Fatalf("expected type %q, got %q", msg.Type, got.Type)
	}
}

