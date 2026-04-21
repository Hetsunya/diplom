package meeting

import (
	"encoding/json"
	"errors"
	"fmt"
	"time"
)

var (
	ErrInvalidTransition = errors.New("invalid meeting status transition")
)

type service struct {
	repo Repository
}

func NewService(repo Repository) Service {
	return &service{repo: repo}
}

func (s *service) StartMeeting(sessionID int, at time.Time) error {
	current, err := s.repo.GetStatus(sessionID)
	if err != nil {
		return fmt.Errorf("get meeting status: %w", err)
	}

	if current != StatusCreated && current != StatusPaused {
		return fmt.Errorf("%w: %s -> %s", ErrInvalidTransition, current, StatusActive)
	}

	if err := s.repo.SetStatusActive(sessionID, at.UTC()); err != nil {
		return fmt.Errorf("set meeting active: %w", err)
	}

	payload, _ := json.Marshal(map[string]any{
		"from": string(current),
		"to":   string(StatusActive),
	})
	_ = s.repo.AppendEvent(Event{
		SessionID:  sessionID,
		Type:       "meeting_status_changed",
		Payload:    payload,
		OccurredAt: at.UTC(),
	})

	return nil
}

func (s *service) EndMeeting(sessionID int, at time.Time) error {
	current, err := s.repo.GetStatus(sessionID)
	if err != nil {
		return fmt.Errorf("get meeting status: %w", err)
	}

	if current != StatusActive && current != StatusPaused && current != StatusCreated {
		return fmt.Errorf("%w: %s -> %s", ErrInvalidTransition, current, StatusEnded)
	}

	if err := s.repo.SetStatusEnded(sessionID, at.UTC()); err != nil {
		return fmt.Errorf("set meeting ended: %w", err)
	}

	payload, _ := json.Marshal(map[string]any{
		"from": string(current),
		"to":   string(StatusEnded),
	})
	_ = s.repo.AppendEvent(Event{
		SessionID:  sessionID,
		Type:       "meeting_status_changed",
		Payload:    payload,
		OccurredAt: at.UTC(),
	})

	return nil
}

