package auth

type Service interface {
	Authenticate(email, password string) (*LoginResponse, error)
	Refresh(refreshToken string) (*TokenPair, error)
	IssueTokens(userID int) (*TokenPair, error)
}

type TokenPair struct {
	AccessToken  string `json:"accessToken"`
	RefreshToken string `json:"refreshToken"`
	ExpiresInSec int    `json:"expiresInSec"`
}
