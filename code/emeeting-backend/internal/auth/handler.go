package auth

import (
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
)

type Handler struct {
	service Service
}

func NewHandler(service Service) *Handler {
	return &Handler{service: service}
}

type loginRequest struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

type refreshRequest struct {
	RefreshToken string `json:"refreshToken"`
}

func (h *Handler) Login(c *gin.Context) {
	var input loginRequest
	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid login payload"})
		return
	}

	user, err := h.service.Authenticate(input.Email, input.Password)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	pair, err := h.service.IssueTokens(user.AuthUserID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to issue tokens"})
		return
	}

	setTokenCookies(c, pair)
	c.JSON(http.StatusOK, user)
}

func (h *Handler) Refresh(c *gin.Context) {
	var input refreshRequest
	_ = c.ShouldBindJSON(&input)
	if input.RefreshToken == "" {
		if cookie, err := c.Cookie("refresh_token"); err == nil {
			input.RefreshToken = cookie
		}
	}
	if input.RefreshToken == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid refresh payload"})
		return
	}

	pair, err := h.service.Refresh(input.RefreshToken)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	setTokenCookies(c, pair)
	c.JSON(http.StatusOK, pair)
}

func (h *Handler) Logout(c *gin.Context) {
	clearTokenCookies(c)
	c.Status(http.StatusNoContent)
}

func setTokenCookies(c *gin.Context, pair *TokenPair) {
	secure := c.Request.TLS != nil
	httpOnly := true
	sameSite := http.SameSiteLaxMode

	c.SetSameSite(sameSite)
	c.SetCookie("access_token", pair.AccessToken, pair.ExpiresInSec, "/", "", secure, httpOnly)
	// refresh: 7 days
	http.SetCookie(c.Writer, &http.Cookie{
		Name:     "refresh_token",
		Value:    pair.RefreshToken,
		Path:     "/",
		HttpOnly: httpOnly,
		Secure:   secure,
		SameSite: sameSite,
		MaxAge:   int((7 * 24 * time.Hour).Seconds()),
	})
}

func clearTokenCookies(c *gin.Context) {
	secure := c.Request.TLS != nil
	httpOnly := true
	sameSite := http.SameSiteLaxMode
	c.SetSameSite(sameSite)
	http.SetCookie(c.Writer, &http.Cookie{
		Name:     "access_token",
		Value:    "",
		Path:     "/",
		HttpOnly: httpOnly,
		Secure:   secure,
		SameSite: sameSite,
		MaxAge:   -1,
	})
	http.SetCookie(c.Writer, &http.Cookie{
		Name:     "refresh_token",
		Value:    "",
		Path:     "/",
		HttpOnly: httpOnly,
		Secure:   secure,
		SameSite: sameSite,
		MaxAge:   -1,
	})
}
