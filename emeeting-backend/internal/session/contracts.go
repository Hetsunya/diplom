package session

import "time"

type WSMessage struct {
	Type        string    `json:"type"`
	SessionID   int       `json:"session_id"`
	Participant string    `json:"participant_id,omitempty"`
	Payload     any       `json:"payload,omitempty"`
	Timestamp   time.Time `json:"timestamp"`
}
