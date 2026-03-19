package session

import (
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/gorilla/websocket"
)

type busSpy struct {
	lastSessionID int
	lastMessage   WSMessage
}

func (b *busSpy) Add(sessionID int, conn *websocket.Conn)    {}
func (b *busSpy) Remove(sessionID int, conn *websocket.Conn) {}
func (b *busSpy) Broadcast(sessionID int, message any) {
	b.lastSessionID = sessionID
	if typed, ok := message.(WSMessage); ok {
		b.lastMessage = typed
	}
}

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

func TestWSDispatchUsesRegisteredHandler(t *testing.T) {
	spy := &busSpy{}
	handler := NewHandler(NewService(newFakeRepo()), spy)

	handler.RegisterWSHandler("custom", func(sessionID int, msg WSMessage) {
		msg.Type = "custom_processed"
		handler.hub.Broadcast(sessionID, msg)
	})

	handler.dispatchWSMessage(7, WSMessage{Type: "custom"})
	if spy.lastSessionID != 7 {
		t.Fatalf("expected session 7, got %d", spy.lastSessionID)
	}
	if spy.lastMessage.Type != "custom_processed" {
		t.Fatalf("expected transformed type, got %q", spy.lastMessage.Type)
	}
}

