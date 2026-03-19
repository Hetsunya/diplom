package session

import (
	"time"

	"emeeting/internal/models"
	"github.com/gorilla/websocket"
)

type Repository interface {
	Create(input models.Session) (int, error)
	List() ([]models.Session, error)
	Get(id int) (*models.Session, error)
}

type Service interface {
	Create(input models.Session) (int, error)
	List() ([]models.Session, error)
	Get(id int) (*models.Session, error)
}

type Bus interface {
	Add(sessionID int, conn *websocket.Conn)
	Remove(sessionID int, conn *websocket.Conn)
	Broadcast(sessionID int, message any)
}

type WSMessageHandler func(sessionID int, msg WSMessage)

type WSMessage struct {
	Type        string    `json:"type"`
	SessionID   int       `json:"session_id"`
	Participant string    `json:"participant_id,omitempty"`
	Payload     any       `json:"payload,omitempty"`
	Timestamp   time.Time `json:"timestamp"`
}
