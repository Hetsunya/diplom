package middleware

import (
	"net/http"
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"
)

func RequireAuth() gin.HandlerFunc {
	return func(c *gin.Context) {
		path := c.Request.URL.Path
		if path == "/auth/login" || path == "/auth/refresh" || path == "/ws/health" || path == "/health" {
			c.Next()
			return
		}

		token, err := c.Cookie("access_token")
		if err != nil || strings.TrimSpace(token) == "" {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
			return
		}

		claims, err := ParseAccessToken(token)
		if err != nil || claims.Subject == "" {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
			return
		}
		userID, err := strconv.Atoi(claims.Subject)
		if err != nil {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
			return
		}
		c.Set("authUserID", userID)
		c.Set("roles", claims.Roles)
		c.Next()
	}
}

func RequireRole(allowed ...string) gin.HandlerFunc {
	allow := make(map[string]bool, len(allowed))
	for _, r := range allowed {
		allow[r] = true
	}
	return func(c *gin.Context) {
		raw, ok := c.Get("roles")
		if !ok {
			c.AbortWithStatusJSON(http.StatusForbidden, gin.H{"error": "forbidden"})
			return
		}
		roles, _ := raw.([]string)
		for _, r := range roles {
			if allow[r] {
				c.Next()
				return
			}
		}
		c.AbortWithStatusJSON(http.StatusForbidden, gin.H{"error": "forbidden"})
	}
}

