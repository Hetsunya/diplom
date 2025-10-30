package repository

import (
	"database/sql"
	"emotions-backend/internal/models"

	_ "github.com/lib/pq"
)

type Repository struct {
	db *sql.DB
}

func NewRepository(db *sql.DB) *Repository {
	return &Repository{db: db}
}

func (r *Repository) CreateSession(session *models.Session) error {
	query := `
        INSERT INTO Session (id_candidate, id_hr_manager, date_time, video, audio)
        VALUES ($1, $2, $3, $4, $5) RETURNING id_session`
	return r.db.QueryRow(query, session.IDCandidate, session.IDHRManager, session.DateTime, session.Video, session.Audio).
		Scan(&session.IDSession)
}

func (r *Repository) SaveEmotion(emotion *models.Emotion) error {
	query := `
        INSERT INTO Emotions (id_session, emotion, probability)
        VALUES ($1, $2, $3) RETURNING id_emotion`
	return r.db.QueryRow(query, emotion.IDSession, emotion.Emotion, emotion.Probability).
		Scan(&emotion.IDEmotion)
}

func (r *Repository) SaveFeature(feature *models.Feature) error {
	query := `
        INSERT INTO Features (id_session, facial_features, mfcc)
        VALUES ($1, $2, $3) RETURNING id_feature`
	return r.db.QueryRow(query, feature.IDSession, feature.FacialFeatures, feature.MFCC).
		Scan(&feature.IDFeature)
}

func (r *Repository) CreateReport(report *models.Report) error {
	query := `
        INSERT INTO Report (id_session, id_hr_manager, metrics, summary)
        VALUES ($1, $2, $3, $4) RETURNING id_report`
	return r.db.QueryRow(query, report.IDSession, report.IDHRManager, report.Metrics, report.Summary).
		Scan(&report.IDReport)
}

func (r *Repository) GetEmotionsBySession(idSession int) ([]models.Emotion, error) {
	query := `SELECT id_emotion, id_session, emotion, probability FROM Emotions WHERE id_session = $1`
	rows, err := r.db.Query(query, idSession)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var emotions []models.Emotion
	for rows.Next() {
		var e models.Emotion
		if err := rows.Scan(&e.IDEmotion, &e.IDSession, &e.Emotion, &e.Probability); err != nil {
			return nil, err
		}
		emotions = append(emotions, e)
	}
	return emotions, nil
}
