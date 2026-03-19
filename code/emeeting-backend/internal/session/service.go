package session

import "emeeting/internal/models"

type service struct {
	repo Repository
}

func NewService(repo Repository) Service {
	return &service{repo: repo}
}

func (s *service) Create(input models.Session) (int, error) {
	return s.repo.Create(input)
}

func (s *service) List() ([]models.Session, error) {
	return s.repo.List()
}

func (s *service) Get(id int) (*models.Session, error) {
	return s.repo.Get(id)
}
