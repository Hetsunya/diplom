package session

import "emeeting/internal/models"

type RepositoryContract interface {
	Create(input models.Session) (int, error)
	List() ([]models.Session, error)
	Get(id int) (*models.Session, error)
}

type Service struct {
	repo RepositoryContract
}

func NewService(repo RepositoryContract) *Service {
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
