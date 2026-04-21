package auth

import (
	"crypto/sha256"
	"crypto/subtle"
	"encoding/hex"
	"errors"
	"strings"
	"time"

	"golang.org/x/crypto/bcrypt"
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

	// Support legacy SHA-256 hex hashes, but upgrade to bcrypt on successful login.
	if strings.HasPrefix(user.PasswordHash, "$2") {
		if err := bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(password)); err != nil {
			return nil, errors.New("invalid credentials")
		}
	} else {
		sum := sha256.Sum256([]byte(password))
		calculatedHash := hex.EncodeToString(sum[:])
		if subtle.ConstantTimeCompare([]byte(calculatedHash), []byte(user.PasswordHash)) != 1 {
			return nil, errors.New("invalid credentials")
		}
		if newHash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost); err == nil {
			_ = s.repo.UpdatePasswordHash(user.AuthUserID, string(newHash))
		}
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
