package service

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"emotions-backend/internal/models"
	"emotions-backend/internal/repository"
)

type Service struct {
	repo      *repository.Repository
	pythonAPI string
}

func NewService(repo *repository.Repository, pythonAPI string) *Service {
	return &Service{repo: repo, pythonAPI: pythonAPI}
}

func (s *Service) UploadSession(videoPath, audioPath string, idCandidate, idHRManager int) (int, error) {
	session := &models.Session{
		IDCandidate: idCandidate,
		IDHRManager: idHRManager,
		DateTime:    time.Now(),
		Video:       videoPath,
		Audio:       audioPath,
	}
	if err := s.repo.CreateSession(session); err != nil {
		return 0, err
	}

	// Вызов Python для анализа
	emotions, err := s.callPythonAnalyzer(videoPath)
	if err != nil {
		return session.IDSession, err
	}

	// Сохранение эмоций
	for emotion, prob := range emotions {
		e := &models.Emotion{
			IDSession:   session.IDSession,
			Emotion:     emotion,
			Probability: prob,
		}
		if err := s.repo.SaveEmotion(e); err != nil {
			return session.IDSession, err
		}
	}

	return session.IDSession, nil
}

func (s *Service) callPythonAnalyzer(videoPath string) (map[string]float64, error) {
	payload := map[string]string{"video": videoPath}
	payloadBytes, err := json.Marshal(payload)
	if err != nil {
		return nil, err
	}

	resp, err := http.Post(s.pythonAPI, "application/json", bytes.NewBuffer(payloadBytes))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("Python API returned status: %d", resp.StatusCode)
	}

	var emotions map[string]float64
	if err := json.NewDecoder(resp.Body).Decode(&emotions); err != nil {
		return nil, err
	}
	return emotions, nil
}

func (s *Service) GenerateReport(idSession int) (*models.Report, error) {
	emotions, err := s.repo.GetEmotionsBySession(idSession)
	if err != nil {
		return nil, err
	}

	metrics, _ := json.Marshal(emotions)
	report := &models.Report{
		IDSession:   idSession,
		IDHRManager: 1, // Заглушка
		Metrics:     string(metrics),
		Summary:     "Эмоциональное состояние проанализировано",
	}
	if err := s.repo.CreateReport(report); err != nil {
		return nil, err
	}
	return report, nil
}
