package meeting

import (
	"errors"
	"testing"
	"time"
)

type repoStub struct {
	status Status

	setActiveCalls int
	setEndedCalls  int
	appendCalls    int
}

func (r *repoStub) GetStatus(sessionID int) (Status, error) { return r.status, nil }
func (r *repoStub) SetStatusActive(sessionID int, startedAt time.Time) error {
	r.setActiveCalls++
	r.status = StatusActive
	return nil
}
func (r *repoStub) SetStatusEnded(sessionID int, endedAt time.Time) error {
	r.setEndedCalls++
	r.status = StatusEnded
	return nil
}
func (r *repoStub) AppendEvent(e Event) error {
	r.appendCalls++
	return nil
}

func TestMeeting_Transitions(t *testing.T) {
	now := time.Date(2026, 4, 21, 12, 0, 0, 0, time.UTC)

	t.Run("StartMeeting allowed from created", func(t *testing.T) {
		t.Parallel()
		repo := &repoStub{status: StatusCreated}
		svc := NewService(repo)

		if err := svc.StartMeeting(1, now); err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if repo.setActiveCalls != 1 {
			t.Fatalf("expected SetStatusActive called once, got %d", repo.setActiveCalls)
		}
	})

	t.Run("StartMeeting forbidden from ended", func(t *testing.T) {
		t.Parallel()
		repo := &repoStub{status: StatusEnded}
		svc := NewService(repo)

		err := svc.StartMeeting(1, now)
		if err == nil {
			t.Fatal("expected error, got nil")
		}
		if !errors.Is(err, ErrInvalidTransition) {
			t.Fatalf("expected ErrInvalidTransition, got %v", err)
		}
		if repo.setActiveCalls != 0 {
			t.Fatalf("expected SetStatusActive not called, got %d", repo.setActiveCalls)
		}
	})

	t.Run("EndMeeting allowed from active", func(t *testing.T) {
		t.Parallel()
		repo := &repoStub{status: StatusActive}
		svc := NewService(repo)

		if err := svc.EndMeeting(1, now); err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if repo.setEndedCalls != 1 {
			t.Fatalf("expected SetStatusEnded called once, got %d", repo.setEndedCalls)
		}
	})

	t.Run("EndMeeting forbidden from cancelled", func(t *testing.T) {
		t.Parallel()
		repo := &repoStub{status: StatusCancelled}
		svc := NewService(repo)

		err := svc.EndMeeting(1, now)
		if err == nil {
			t.Fatal("expected error, got nil")
		}
		if !errors.Is(err, ErrInvalidTransition) {
			t.Fatalf("expected ErrInvalidTransition, got %v", err)
		}
		if repo.setEndedCalls != 0 {
			t.Fatalf("expected SetStatusEnded not called, got %d", repo.setEndedCalls)
		}
	})
}

