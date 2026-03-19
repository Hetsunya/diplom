package auth

import (
	"bytes"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
)

type authServiceMock struct {
	authenticateFn func(email, password string) (*LoginResponse, error)
}

func (m *authServiceMock) Authenticate(email, password string) (*LoginResponse, error) {
	return m.authenticateFn(email, password)
}

func TestLoginHandlerUsesServicePort(t *testing.T) {
	gin.SetMode(gin.TestMode)

	mock := &authServiceMock{
		authenticateFn: func(email, password string) (*LoginResponse, error) {
			if email != "u@example.com" || password != "secret" {
				return nil, errors.New("bad credentials")
			}
			return &LoginResponse{AuthUserID: 1, Email: email}, nil
		},
	}
	h := NewHandler(mock)
	r := gin.New()
	r.POST("/auth/login", h.Login)

	body, _ := json.Marshal(map[string]string{
		"email":    "u@example.com",
		"password": "secret",
	})
	req := httptest.NewRequest(http.MethodPost, "/auth/login", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	r.ServeHTTP(w, req)
	if w.Code != http.StatusOK {
		t.Fatalf("expected status 200, got %d, body=%s", w.Code, w.Body.String())
	}
}

