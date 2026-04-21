package auth

import (
	"database/sql"
	"time"

	"emeeting/internal/models"
)

type Repository interface {
	GetByEmail(email string) (*models.AuthUser, error)
	UpdateLastLogin(authUserID int, at time.Time) error
	UpdatePasswordHash(authUserID int, passwordHash string) error
}

type repo struct {
	db *sql.DB
}

func NewRepository(db *sql.DB) Repository {
	return &repo{db: db}
}

func (r *repo) GetByEmail(email string) (*models.AuthUser, error) {
	var (
		authUserID   int
		fetchedEmail  string
		passwordHash string
		isActive     bool
		createdAt    time.Time
		lastLogin    sql.NullTime
	)

	err := r.db.QueryRow(`
		SELECT auth_user_id, email, password_hash, is_active, created_at, last_login
		FROM auth_user
		WHERE email = $1
	`, email).Scan(&authUserID, &fetchedEmail, &passwordHash, &isActive, &createdAt, &lastLogin)

	if err != nil {
		return nil, err
	}

	userEmail := fetchedEmail

	var lastLoginPtr *time.Time
	if lastLogin.Valid {
		t := lastLogin.Time.UTC()
		lastLoginPtr = &t
	}

	return &models.AuthUser{
		AuthUserID:   authUserID,
		Email:        userEmail,
		PasswordHash: passwordHash,
		IsActive:     isActive,
		CreatedAt:    createdAt.UTC(),
		LastLogin:    lastLoginPtr,
	}, nil
}

func (r *repo) UpdateLastLogin(authUserID int, at time.Time) error {
	_, err := r.db.Exec(`
		UPDATE auth_user
		SET last_login = $1
		WHERE auth_user_id = $2
	`, at, authUserID)
	return err
}

func (r *repo) UpdatePasswordHash(authUserID int, passwordHash string) error {
	_, err := r.db.Exec(`
		UPDATE auth_user
		SET password_hash = $1
		WHERE auth_user_id = $2
	`, passwordHash, authUserID)
	return err
}

