package analysis

import (
	"context"
	"database/sql"
	"fmt"
	"log"
)

type Service struct {
	repo *Repository
}

func NewService(db *sql.DB) *Service {
	return &Service{repo: NewRepository(db)}
}

// RecordInbound validates (for v1 types) and persists supported analytics WS messages.
func (s *Service) RecordInbound(ctx context.Context, msg InboundWSMessage) error {
	if s == nil || s.repo == nil {
		return nil
	}
	if !ShouldPersist(msg.Type) {
		return nil
	}
	if err := ValidatePayload(msg.Type, msg.Payload); err != nil {
		log.Printf("[ANALYSIS] validate skipped store: %v (type=%s)", err, msg.Type)
		return nil
	}
	if msg.Type == TypeAnalysisReport || msg.Type == TypeAnalysisReportPartial {
		stage := "partial"
		if msg.Type == TypeAnalysisReport {
			stage = "final"
		}
		if pl, ok := msg.Payload.(map[string]any); ok {
			if st, ok := pl["stage"].(string); ok && st != "" {
				stage = st
			}
		}
		return s.repo.InsertReport(ctx, msg.SessionID, stage, msg.Payload)
	}
	return s.repo.InsertEvent(ctx, msg)
}

func (s *Service) GetLatestReportJSON(ctx context.Context, sessionID int) ([]byte, error) {
	if s == nil || s.repo == nil {
		return nil, fmt.Errorf("analysis service unavailable")
	}
	return s.repo.LatestReport(ctx, sessionID)
}

func (s *Service) ListEventsJSON(ctx context.Context, sessionID int, limit int) ([]byte, error) {
	if s == nil || s.repo == nil {
		return nil, fmt.Errorf("analysis service unavailable")
	}
	return s.repo.ListEvents(ctx, sessionID, limit)
}
