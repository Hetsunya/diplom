package auth

import (
	"crypto/sha256"
	"crypto/subtle"
	"encoding/hex"
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

type service struct {
	repo Repository
}

func NewService(repo Repository) Service {
	return &service{repo: repo}
}

func (s *service) Authenticate(email, password string) (*LoginResponse, error) {
	if strings.TrimSpace(email) == "" || strings.TrimSpace(password) == "" {
		return nil, errors.New("email and password are required")
	}

	user, err := s.repo.GetByEmail(email)
	if err != nil {
		// Avoid leaking whether the user exists.
		return nil, errors.New("invalid credentials")
	}
	if !user.IsActive {
		return nil, errors.New("invalid credentials")
	}

	sum := sha256.Sum256([]byte(password))
	calculatedHash := hex.EncodeToString(sum[:])

	if subtle.ConstantTimeCompare([]byte(calculatedHash), []byte(user.PasswordHash)) != 1 {
		return nil, errors.New("invalid credentials")
	}

	now := time.Now().UTC()
	_ = s.repo.UpdateLastLogin(user.AuthUserID, now)

	return &LoginResponse{
		AuthUserID:   user.AuthUserID,
		Email:        user.Email,
		IsActive:     user.IsActive,
		CreatedAt:    user.CreatedAt.Format(time.RFC3339),
		LastLogin:    now.Format(time.RFC3339),
		PasswordHash: user.PasswordHash,
	}, nil
}
