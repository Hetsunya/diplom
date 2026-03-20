package session

import (
	"database/sql"
	"log"

	"emeeting/internal/models"
)

type PostgresRepository struct {
	db *sql.DB
}

func NewRepository(db *sql.DB) *PostgresRepository {
	return &PostgresRepository{db: db}
}

// Create создает новую сессию и возвращает ее ID
func (r *PostgresRepository) Create(s models.Session) (int, error) {
	var id int

	// sql.Null* для nullable полей
	var locationType sql.NullString
	if s.LocationType != nil {
		locationType = sql.NullString{String: string(*s.LocationType), Valid: true}
	}

	var physicalLocation sql.NullString
	if s.PhysicalLocation != nil {
		physicalLocation = sql.NullString{String: *s.PhysicalLocation, Valid: true}
	}

	var description sql.NullString
	if s.Description != nil {
		description = sql.NullString{String: *s.Description, Valid: true}
	}

	var endDatetime sql.NullTime
	if s.EndDatetime != nil {
		endDatetime = sql.NullTime{Time: *s.EndDatetime, Valid: true}
	}

	var createdBy sql.NullInt32
	if s.CreatedBy != nil {
		createdBy = sql.NullInt32{Int32: int32(*s.CreatedBy), Valid: true}
	}

	log.Printf("DEBUG: inserting session: %+v", s)

	err := r.db.QueryRow(`
		INSERT INTO session
		(title, session_type, start_datetime, end_datetime, description, location_type, physical_location, created_by)
		VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
		RETURNING session_id
	`, s.Title, s.SessionType, s.StartDatetime, endDatetime, description, locationType, physicalLocation, createdBy).Scan(&id)

	if err != nil {
		log.Printf("ERROR: failed to insert session: %v", err)
		return 0, err
	}

	return id, nil
}

// List возвращает все сессии
func (r *PostgresRepository) List() ([]models.Session, error) {
	rows, err := r.db.Query(`
		SELECT session_id, title, description, session_type, start_datetime, end_datetime, location_type, physical_location, created_by
		FROM session
		ORDER BY start_datetime DESC
	`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	// Return empty array ([]) instead of null, so UI doesn't crash on `sessions.length`.
	sessions := make([]models.Session, 0)
	for rows.Next() {
		var s models.Session
		err := rows.Scan(
			&s.SessionID,
			&s.Title,
			&s.Description,
			&s.SessionType,
			&s.StartDatetime,
			&s.EndDatetime,
			&s.LocationType,
			&s.PhysicalLocation,
			&s.CreatedBy,
		)
		if err != nil {
			return nil, err
		}
		sessions = append(sessions, s)
	}
	return sessions, nil
}

// Get возвращает одну сессию по ID
func (r *PostgresRepository) Get(id int) (*models.Session, error) {
	var s models.Session
	err := r.db.QueryRow(`
		SELECT session_id, title, description, session_type, start_datetime, end_datetime, location_type, physical_location, created_by
		FROM session
		WHERE session_id = $1
	`, id).Scan(
		&s.SessionID,
		&s.Title,
		&s.Description,
		&s.SessionType,
		&s.StartDatetime,
		&s.EndDatetime,
		&s.LocationType,
		&s.PhysicalLocation,
		&s.CreatedBy,
	)
	if err != nil {
		return nil, err
	}
	return &s, nil
}
