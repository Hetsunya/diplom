package auth

import (
	"errors"
	"strings"
	"time"
)

type LoginResponse struct {
	AuthUserID   int     `json:"authUserId"`
	Email        string  `json:"email"`
	IsActive     bool    `json:"isActive"`
	CreatedAt    string  `json:"createdAt"`
	LastLogin    string  `json:"lastLogin"`
	PasswordHash string  `json:"passwordHash"`
}

type service struct{}

func NewService() Service {
	return &service{}
}

func (s *service) Authenticate(email, password string) (*LoginResponse, error) {
	if strings.TrimSpace(email) == "" || strings.TrimSpace(password) == "" {
		return nil, errors.New("email and password are required")
	}

	now := time.Now().UTC().Format(time.RFC3339)
	return &LoginResponse{
		AuthUserID:   1,
		Email:        email,
		IsActive:     true,
		CreatedAt:    now,
		LastLogin:    now,
		PasswordHash: "",
	}, nil
}
