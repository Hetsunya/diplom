package session

import (
	"bytes"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/gin-gonic/gin"

	"emeeting/internal/models"
)

type fakeRepo struct {
	nextID   int
	sessions map[int]models.Session
}

func newFakeRepo() *fakeRepo {
	start := time.Date(2026, 3, 20, 12, 0, 0, 0, time.UTC)
	return &fakeRepo{
		nextID: 2,
		sessions: map[int]models.Session{
			1: {
				SessionID:     1,
				Title:         "Seed Session",
				SessionType:   models.SessionMeeting,
				StartDatetime: &start,
			},
		},
	}
}

func (r *fakeRepo) Create(input models.Session) (int, error) {
	id := r.nextID
	r.nextID++
	input.SessionID = id
	r.sessions[id] = input
	return id, nil
}

func (r *fakeRepo) List() ([]models.Session, error) {
	result := make([]models.Session, 0, len(r.sessions))
	for _, s := range r.sessions {
		result = append(result, s)
	}
	return result, nil
}

func (r *fakeRepo) Get(id int) (*models.Session, error) {
	s, ok := r.sessions[id]
	if !ok {
		return nil, errors.New("not found")
	}
	return &s, nil
}

func setupRouterForSessionTests(repo Repository) *gin.Engine {
	gin.SetMode(gin.TestMode)
	svc := NewService(repo)
	handler := NewHandler(svc, NewSessionHub(), nil, nil)
	r := gin.New()
	r.GET("/sessions", handler.List)
	r.POST("/sessions", handler.Create)
	r.GET("/sessions/:id", handler.Get)
	return r
}

func TestSessionsListSmoke(t *testing.T) {
	router := setupRouterForSessionTests(newFakeRepo())
	req := httptest.NewRequest(http.MethodGet, "/sessions", nil)
	w := httptest.NewRecorder()

	router.ServeHTTP(w, req)
	if w.Code != http.StatusOK {
		t.Fatalf("expected status 200, got %d", w.Code)
	}
}

func TestSessionsCreateSmoke(t *testing.T) {
	router := setupRouterForSessionTests(newFakeRepo())
	payload := map[string]any{
		"title":         "Interview A",
		"sessionType":   "interview",
		"startDatetime": "2026-03-20T13:00",
	}
	body, _ := json.Marshal(payload)

	req := httptest.NewRequest(http.MethodPost, "/sessions", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	router.ServeHTTP(w, req)
	if w.Code != http.StatusCreated {
		t.Fatalf("expected status 201, got %d, body=%s", w.Code, w.Body.String())
	}
}

func TestSessionsGetByIDSmoke(t *testing.T) {
	router := setupRouterForSessionTests(newFakeRepo())
	req := httptest.NewRequest(http.MethodGet, "/sessions/1", nil)
	w := httptest.NewRecorder()

	router.ServeHTTP(w, req)
	if w.Code != http.StatusOK {
		t.Fatalf("expected status 200, got %d", w.Code)
	}
}

