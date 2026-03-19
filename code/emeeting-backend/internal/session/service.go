package session

import "emeeting/internal/models"

type Service struct {
	repo *Repository
}

func NewService(repo *Repository) *Service {
	return &Service{repo: repo}
}

func (s *Service) Create(input models.Session) (int, error) {
	return s.repo.Create(input)
}

func (s *Service) List() ([]models.Session, error) {
	return s.repo.List()
}

func (s *Service) Get(id int) (*models.Session, error) {
	return s.repo.Get(id)
}
