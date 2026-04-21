package meeting

import (
	"encoding/json"
	"time"
)

type Status string

const (
	StatusCreated   Status = "created"
	StatusActive    Status = "active"
	StatusPaused    Status = "paused"
	StatusEnded     Status = "ended"
	StatusCancelled Status = "cancelled"
)

type Event struct {
	SessionID  int             `json:"sessionId"`
	Type       string          `json:"type"`
	Payload    json.RawMessage `json:"payload,omitempty"`
	OccurredAt time.Time       `json:"occurredAt"`
}

type Repository interface {
	GetStatus(sessionID int) (Status, error)
	SetStatusActive(sessionID int, startedAt time.Time) error
	SetStatusEnded(sessionID int, endedAt time.Time) error
	AppendEvent(e Event) error
}

type Service interface {
	StartMeeting(sessionID int, at time.Time) error
	EndMeeting(sessionID int, at time.Time) error
}

