package auth

type Service interface {
	Authenticate(email, password string) (*LoginResponse, error)
}
